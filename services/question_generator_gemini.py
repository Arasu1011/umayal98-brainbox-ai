import os
import re
import time
from typing import List, Literal, Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field, ValidationError

load_dotenv()

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

# Keep generation fast and predictable: ONE primary model only.
# You can override it in .env with GEMINI_MODEL=...
REQUEST_TIMEOUT_MS = int(os.getenv("GEMINI_TIMEOUT_MS", "45000"))
RETRY_DELAY_SECONDS = float(os.getenv("GEMINI_RETRY_DELAY_SECONDS", "2"))


def _is_503_error(error):
    text = str(error).upper()
    return "503" in text or "UNAVAILABLE" in text or "HIGH DEMAND" in text


QuestionType = Literal[
    "Multiple Choice",
    "Fill in the Blanks",
    "True / False",
    "Short Answer",
]

DifficultyType = Literal["Easy", "Medium", "Hard"]


class Question(BaseModel):
    question: str
    type: QuestionType
    options: List[str] = Field(default_factory=list)
    correct_answer: str
    difficulty: DifficultyType
    source_page: Optional[int] = None


class QuestionSet(BaseModel):
    set_name: str
    questions: List[Question]


class QuizOutput(BaseModel):
    sets: List[QuestionSet]


def _get_api_key():
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. Add it to your .env file."
        )
    return key


def _extract_page_numbers(source_text):
    pages = re.findall(
        r"---\s*PAGE\s+(\d+)\s*---",
        source_text,
        flags=re.IGNORECASE,
    )
    return sorted({int(p) for p in pages})


def _type_sequence(question_types, questions_per_set):
    if not question_types:
        raise ValueError("At least one question type is required.")

    allowed = {
        "Multiple Choice",
        "Fill in the Blanks",
        "True / False",
        "Short Answer",
    }

    bad = [x for x in question_types if x not in allowed]
    if bad:
        raise ValueError(f"Unsupported question type(s): {bad}")

    if questions_per_set < len(question_types):
        raise ValueError(
            "questions_per_set must be at least the number of selected "
            "question types."
        )

    return [
        question_types[i % len(question_types)]
        for i in range(questions_per_set)
    ]


def _validate(result, number_of_sets, questions_per_set,
              question_types, valid_pages):

    if len(result.sets) != number_of_sets:
        raise ValueError(
            f"Gemini returned {len(result.sets)} sets; "
            f"{number_of_sets} were requested."
        )

    expected_types = _type_sequence(
        question_types, questions_per_set
    )

    for set_index, qset in enumerate(result.sets, start=1):

        if len(qset.questions) != questions_per_set:
            raise ValueError(
                f"{qset.set_name} contains {len(qset.questions)} questions; "
                f"{questions_per_set} were requested."
            )

        seen = set()

        for q_index, q in enumerate(qset.questions):

            if q.type != expected_types[q_index]:
                raise ValueError(
                    f"{qset.set_name}, Question {q_index + 1}: "
                    f"expected '{expected_types[q_index]}' but received "
                    f"'{q.type}'."
                )

            text = q.question.strip()
            if not text:
                raise ValueError(
                    f"Empty question in {qset.set_name}, "
                    f"Question {q_index + 1}."
                )

            normalized = text.lower()
            if normalized in seen:
                raise ValueError(
                    f"Duplicate question in {qset.set_name}."
                )
            seen.add(normalized)

            if q.type == "Multiple Choice":
                if len(q.options) != 4:
                    raise ValueError(
                        f"{qset.set_name}, Question {q_index + 1}: "
                        "MCQ must have exactly 4 options."
                    )

                options = [x.strip() for x in q.options]

                if any(not x for x in options):
                    raise ValueError(
                        f"{qset.set_name}, Question {q_index + 1}: "
                        "MCQ contains an empty option."
                    )

                if q.correct_answer.strip() not in options:
                    raise ValueError(
                        f"{qset.set_name}, Question {q_index + 1}: "
                        "correct_answer does not match an MCQ option."
                    )

            else:
                q.options = []

            if valid_pages and q.source_page is not None:
                if q.source_page not in valid_pages:
                    raise ValueError(
                        f"{qset.set_name}, Question {q_index + 1}: "
                        f"invalid source_page {q.source_page}."
                    )


def _to_dict(result):
    return {
        "sets": [
            {
                "set_name": qset.set_name,
                "questions": [
                    {
                        "question": q.question.strip(),
                        "type": q.type,
                        "options": [x.strip() for x in q.options],
                        "correct_answer": q.correct_answer.strip(),
                        "difficulty": q.difficulty,
                        "source_page": q.source_page,
                    }
                    for q in qset.questions
                ],
            }
            for qset in result.sets
        ]
    }


def generate_questions(
    source_text: str,
    class_name: str,
    subject: str,
    chapter: str,
    number_of_sets: int,
    questions_per_set: int,
    difficulty: str,
    question_types: List[str],
    language: str,
    image_inputs: Optional[List[dict]] = None,
):
    """
    Generate source-grounded questions from PDF text and/or images.

    image_inputs is a list of dictionaries containing:
      - bytes: image bytes
      - mime_type: image/jpeg, image/png, image/webp, etc.
      - name: optional display name
      - source_number: optional source number
    """

    image_inputs = image_inputs or []

    if not source_text or not source_text.strip():
        if not image_inputs:
            raise ValueError("No learning material was supplied.")

    if not chapter or not chapter.strip():
        raise ValueError("Chapter / Topic is required.")

    if number_of_sets < 1 or questions_per_set < 1:
        raise ValueError("Number of sets and questions must be at least 1.")

    sequence = _type_sequence(question_types, questions_per_set)
    valid_pages = _extract_page_numbers(source_text)

    if image_inputs and not valid_pages:
        valid_pages = list(range(1, len(image_inputs) + 1))

    if not valid_pages:
        raise ValueError(
            "No source-page markers found. Expected markers like "
            "'--- PAGE 1 ---'."
        )

    client = genai.Client(
        api_key=_get_api_key(),
        http_options=types.HttpOptions(
            timeout=REQUEST_TIMEOUT_MS,
            retry_options=types.HttpRetryOptions(
                attempts=1
            ),
        ),
    )

    type_order = "\n".join(
        f"{i + 1}. {qtype}" for i, qtype in enumerate(sequence)
    )

    prompt = f"""
You are the question-generation engine for:
UMAYAL 98 : Brainbox AI
Smart Quiz, Sharp Mind

Create school-level quiz questions from ONLY the supplied learning material.

CLASS/GRADE: {class_name}
SUBJECT: {subject}
CHAPTER/TOPIC: {chapter}
LANGUAGE: {language}
DIFFICULTY REQUEST: {difficulty}
SETS: {number_of_sets}
QUESTIONS PER SET: {questions_per_set}

STRICT SOURCE-GROUNDING RULE:
- Use ONLY information in the supplied learning material and supplied images.
- Do not use outside knowledge.
- Do not invent facts, names, dates, numbers, definitions, examples or answers.
- Every answer must be supported by the source.
- The source contains markers such as --- PAGE 1 ---.
- For PDF sources, source_page means the PDF page containing the evidence.
- For image sources, source_page means the image/source number containing the evidence.

EXACT QUESTION TYPE ORDER FOR EVERY SET:
{type_order}

QUESTION RULES:
- Multiple Choice: exactly 4 options; one correct answer; correct_answer
  must exactly match one option.
- Fill in the Blanks: one clear blank; options must be [].
- True / False: source-based statement; correct_answer exactly "True"
  or "False"; options must be [].
- Short Answer: concise source-based answer; options must be [].
- Do not repeat questions within a set.
- Keep wording appropriate for the selected class.
- Use the requested language.
- Difficulty must be exactly Easy, Medium or Hard.
- For Mixed difficulty, vary Easy/Medium/Hard.
- Do not reveal the answer in the question.

Return ONLY the structured JSON matching the supplied schema.

LEARNING MATERIAL / SOURCE REFERENCES:
{source_text}

IMAGE INPUTS:
- If images are attached, inspect them directly and use their visible text,
  diagrams, tables, labels and other educational content as the source.
- Do not assume information that cannot be seen or read in the supplied image.
"""

    last_error = None

    # Gemini accepts image bytes directly with generate_content. This keeps
    # the structured JSON response while allowing textbook photos, diagrams
    # and tables to be understood directly by the model.
    if image_inputs:
        contents = []
        for image in image_inputs:
            contents.append(
                types.Part.from_bytes(
                    data=image["bytes"],
                    mime_type=image.get("mime_type", "image/jpeg"),
                )
            )
        contents.append(prompt)
    else:
        contents = prompt

    # IMPORTANT: exactly ONE primary model + ONE short retry.
    # The SDK automatic retry is disabled above so a 503 cannot silently
    # trigger several hidden retries and make the Streamlit page wait minutes.
    for attempt in range(2):
        current_prompt = prompt

        if attempt == 1 and last_error:
            current_prompt += f"""

CORRECTION REQUIRED:
The previous response failed validation:
{last_error}

Regenerate the COMPLETE result and follow all rules exactly.
"""

        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=(
                    contents[:-1] + [current_prompt]
                    if image_inputs
                    else current_prompt
                ),
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=QuizOutput,
                    # Gemini 3.x docs recommend leaving temperature at its
                    # default rather than changing it for speed/quality.
                ),
            )

            if not getattr(response, "text", None):
                raise RuntimeError("Gemini returned an empty response.")

            try:
                result = QuizOutput.model_validate_json(response.text)
            except ValidationError as e:
                raise RuntimeError(
                    f"Gemini JSON did not match the quiz schema: {e}"
                ) from e

            _validate(
                result,
                number_of_sets,
                questions_per_set,
                question_types,
                valid_pages,
            )

            return _to_dict(result)

        except Exception as e:
            last_error = str(e)

            if attempt == 0:
                # One short, explicit retry only. This handles a temporary
                # 503 as well as a malformed structured response.
                time.sleep(RETRY_DELAY_SECONDS)
                continue

            if _is_503_error(e):
                raise RuntimeError(
                    f"Gemini is temporarily unavailable (503) after 2 attempts. "
                    f"Model: {GEMINI_MODEL}. "
                    f"Please try again shortly.\n\n{last_error}"
                ) from e

            raise RuntimeError(
                f"Gemini question generation failed after 2 attempts using "
                f"{GEMINI_MODEL}.\n\n{last_error}"
            ) from e

    raise RuntimeError(
        f"Gemini question generation failed after 2 attempts using "
        f"{GEMINI_MODEL}.\n\n{last_error}"
    )


if __name__ == "__main__":
    print("Gemini question generator loaded.")
    print("Model:", GEMINI_MODEL)
