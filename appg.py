import streamlit as st
from pypdf import PdfReader
from dotenv import load_dotenv

from services.question_generator_gemini import generate_questions

import html
import io
import zipfile


# =========================================================
# BRANDING  (edit the text here and it updates everywhere)
# =========================================================

APP_TITLE = "UMAYAL 98 : Brainbox AI"
APP_TAGLINE = "Smart Quiz, Sharp Mind"
CREATED_BY = "Created by student K. Hamsika Felicia"
BIRTHDAY_BADGE = "🎂 Celebrating the 98th Birthday of Umayal Achi"
FOOTER_LINE = "With love and blessings, on Umayal Achi's 98th Birthday"

# Umayal Achi's photo is embedded, so no extra files are needed and
# it appears inside every downloaded quiz HTML (works offline / WhatsApp).
UMAYAL_PHOTO_B64 = (
    "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"
)

UMAYAL_PHOTO_URI = "data:image/jpeg;base64," + UMAYAL_PHOTO_B64


HEADER_FOOTER_CSS = """
.bb-hero{position:relative;text-align:center;padding:30px 18px 26px;border-radius:24px;background:radial-gradient(circle at 50% -10%,#b3303a 0%,#7a1220 42%,#3b0a14 100%);color:#ffffff;border:2px solid #d4a017;box-shadow:0 12px 32px rgba(59,10,20,0.35),inset 0 0 0 5px rgba(255,213,79,0.12);margin:0 0 26px 0;font-family:'Segoe UI',Arial,sans-serif;overflow:hidden;}
.bb-hero:before,.bb-hero:after{content:"❖";position:absolute;top:14px;font-size:22px;color:#ffd54f;opacity:0.75;}
.bb-hero:before{left:20px;}
.bb-hero:after{right:20px;}
.bb-badge{display:inline-block;padding:7px 18px;border-radius:999px;background:linear-gradient(90deg,#ffe082,#ffc107);color:#5a0e18;font-size:14px;font-weight:800;letter-spacing:0.4px;box-shadow:0 3px 8px rgba(0,0,0,0.25);}
.bb-photo-ring{width:176px;height:176px;margin:20px auto 14px auto;padding:6px;border-radius:50%;background:conic-gradient(#ffe082,#c8921a,#fff3c4,#b8860b,#ffe082);box-shadow:0 0 0 7px rgba(255,224,130,0.18),0 10px 24px rgba(0,0,0,0.45);box-sizing:border-box;}
.bb-photo-ring img{width:100%;height:100%;border-radius:50%;object-fit:cover;object-position:center top;border:4px solid #ffffff;background:#ffffff;display:block;box-sizing:border-box;margin:0;}
.bb-name{font-size:14px;letter-spacing:4px;text-transform:uppercase;color:#ffe9a8;font-weight:700;}
.bb-title{font-size:42px;font-weight:800;letter-spacing:1px;line-height:1.15;margin:8px 0 0 0;color:#ffd54f;background:linear-gradient(90deg,#fff3c4,#ffd54f 50%,#fff3c4);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;}
.bb-divider{width:140px;height:3px;margin:14px auto 12px auto;background:linear-gradient(90deg,transparent,#ffd54f,transparent);}
.bb-tagline{font-size:21px;font-style:italic;color:#ffe9a8;letter-spacing:0.6px;}
.bb-footer{margin:34px 0 6px 0;padding:22px 18px;border-radius:20px;background:linear-gradient(135deg,#3b0a14,#7a1220);border-top:4px solid #d4a017;color:#ffffff;text-align:center;box-shadow:0 8px 22px rgba(59,10,20,0.3);font-family:'Segoe UI',Arial,sans-serif;}
.bb-f-title{font-size:20px;font-weight:800;letter-spacing:1px;color:#ffd54f;}
.bb-f-tag{font-size:15px;font-style:italic;color:#ffe9a8;margin-top:4px;}
.bb-f-sep{width:90px;height:2px;margin:12px auto;background:linear-gradient(90deg,transparent,#ffd54f,transparent);}
.bb-f-line{font-size:14px;color:#f7e6ea;}
.bb-f-credit{font-size:14px;font-weight:700;margin-top:8px;color:#ffffff;}
@media (max-width:640px){.bb-title{font-size:28px;}.bb-tagline{font-size:17px;}.bb-photo-ring{width:150px;height:150px;}.bb-badge{font-size:12px;}}
"""


QUIZ_THEME_CSS = """
body{background:#fbf3e8 !important;}
.container{box-shadow:0 8px 28px rgba(122,18,32,0.15);border:1px solid #ecd9b8;}
h2{color:#7a1220;}
.question{background:#fffdf9;border:1px solid #ecd9b8;border-left:6px solid #d4a017;box-shadow:0 2px 8px rgba(0,0,0,0.05);}
.option{cursor:pointer;background:#ffffff;}
.option:hover{background:#fff4d6;border-color:#d4a017;}
button.submit{background:linear-gradient(90deg,#7a1220,#b3303a);color:#ffffff;font-weight:700;box-shadow:0 5px 14px rgba(122,18,32,0.35);}
button.submit:hover{filter:brightness(1.1);}
.result{color:#7a1220;}
th{background:#f7e6b8 !important;color:#5a0e18;}
"""


def build_header_html():
    """Same header in the Streamlit app and every generated HTML."""

    return (
        '<div class="bb-hero">'
        f'<div class="bb-badge">{html.escape(BIRTHDAY_BADGE)}</div>'
        '<div class="bb-photo-ring">'
        f'<img src="{UMAYAL_PHOTO_URI}" alt="Umayal Achi">'
        '</div>'
        '<div class="bb-name">Umayal Achi</div>'
        f'<div class="bb-title">{html.escape(APP_TITLE)}</div>'
        '<div class="bb-divider"></div>'
        f'<div class="bb-tagline">{html.escape(APP_TAGLINE)}</div>'
        '</div>'
    )


def build_footer_html():
    """Same footer in the Streamlit app and every generated HTML."""

    return (
        '<div class="bb-footer">'
        f'<div class="bb-f-title">{html.escape(APP_TITLE)}</div>'
        f'<div class="bb-f-tag">{html.escape(APP_TAGLINE)}</div>'
        '<div class="bb-f-sep"></div>'
        f'<div class="bb-f-line">{html.escape(FOOTER_LINE)}</div>'
        f'<div class="bb-f-credit">{html.escape(CREATED_BY)}</div>'
        '</div>'
    )


# =========================================================
# HTML QUIZ GENERATOR FUNCTION
# =========================================================

def create_quiz_html(
    title,
    set_name,
    questions
):

    questions_json = []

    for index, question in enumerate(
        questions
    ):

        questions_json.append(
            {
                "number": index + 1,
                "question": question.get(
                    "question",
                    ""
                ),
                "type": question.get(
                    "type",
                    ""
                ),
                "options": question.get(
                    "options",
                    []
                ),
                "answer": question.get(
                    "correct_answer",
                    ""
                )
            }
        )


    questions_json_text = repr(
        questions_json
    )

    header_html = build_header_html()

    footer_html = build_footer_html()


    html_content = f"""
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>{html.escape(APP_TITLE)} - {html.escape(set_name)}</title>

<style>

body {{
    font-family: Arial, sans-serif;
    background: #f5f7fb;
    margin: 0;
    padding: 20px;
}}

.container {{
    max-width: 850px;
    margin: auto;
    background: white;
    padding: 30px;
    border-radius: 15px;
}}

h1 {{
    text-align: center;
}}

.subtitle {{
    text-align: center;
    color: #666;
}}

.question {{
    margin-top: 25px;
    padding: 20px;
    border: 1px solid #ddd;
    border-radius: 12px;
}}

.option {{
    display: block;
    padding: 10px;
    margin: 8px 0;
    border: 1px solid #ddd;
    border-radius: 8px;
}}

button {{
    padding: 14px 25px;
    font-size: 17px;
    border: none;
    border-radius: 8px;
    cursor: pointer;
}}

.submit {{
    display: block;
    margin: 30px auto;
}}

.result {{
    text-align: center;
    font-size: 25px;
    font-weight: bold;
}}

.correct {{
    background: #d4edda;
    padding: 10px;
    border-radius: 8px;
}}

.incorrect {{
    background: #f8d7da;
    padding: 10px;
    border-radius: 8px;
}}

{HEADER_FOOTER_CSS}

{QUIZ_THEME_CSS}

</style>

</head>


<body>

<div class="container">

{header_html}

<div class="subtitle">
{html.escape(title)}
</div>

<h2 style="text-align:center;">
{html.escape(set_name)}
</h2>

<form id="quizForm">

<div id="quiz"></div>

<button
type="button"
class="submit"
onclick="submitQuiz()">

✅ SUBMIT QUIZ

</button>

</form>

<div id="result"></div>

{footer_html}

</div>


<script>

const questions = {questions_json_text};

function renderQuiz() {{

    const quiz =
        document.getElementById("quiz");

    questions.forEach((q, index) => {{

        const div =
            document.createElement("div");

        div.className = "question";

        let content =
            "<h3>Q"
            + q.number
            + ". "
            + escapeHtml(q.question)
            + "</h3>";

        if (
            q.type === "Multiple Choice"
        ) {{

            q.options.forEach(
                (option, optionIndex) => {{

                    content += `
                    <label class="option">
                    <input
                        type="radio"
                        name="q${{index}}"
                        value="${{escapeAttribute(option)}}"
                    >
                    ${{escapeHtml(option)}}
                    </label>
                    `;
                }}
            );

        }}

        else if (
            q.type === "True / False"
        ) {{

            content += `
            <label class="option">
            <input
                type="radio"
                name="q${{index}}"
                value="True"
            >
            True
            </label>

            <label class="option">
            <input
                type="radio"
                name="q${{index}}"
                value="False"
            >
            False
            </label>
            `;

        }}

        else if (
            q.type === "Fill in the Blanks"
        ) {{

            content += `
            <input
                type="text"
                name="q${{index}}"
                style="width:95%;padding:10px;"
            >
            `;

        }}

        else {{

            content += `
            <textarea
                name="q${{index}}"
                rows="4"
                style="width:95%;padding:10px;"
            ></textarea>
            `;

        }}

        div.innerHTML = content;

        quiz.appendChild(div);

    }});

}}


function submitQuiz() {{

    let score = 0;

    let answered = 0;

    let review = "";

    questions.forEach(
        (q, index) => {{

            let answer = "";

            const elements =
                document.getElementsByName(
                    "q" + index
                );

            elements.forEach(
                element => {{

                    if (
                        (
                            element.type === "radio"
                            && element.checked
                        )
                        ||
                        (
                            element.type !== "radio"
                        )
                    ) {{

                        answer =
                            element.value;

                    }}

                }}
            );


            answer =
                answer.trim();


            if (answer !== "") {{

                answered++;

            }}


            const correct =
                String(q.answer)
                .trim()
                .toLowerCase();

            const user =
                answer
                .toLowerCase();


            if (
                user !== ""
                &&
                user === correct
            ) {{

                score++;

                review +=
                    "<div class='correct'>"
                    + "Q"
                    + q.number
                    + " ✅ Correct"
                    + "</div>";

            }}

            else {{

                review +=
                    "<div class='incorrect'>"
                    + "Q"
                    + q.number
                    + " ❌ Incorrect"
                    + "<br>"
                    + "Correct answer: "
                    + escapeHtml(q.answer)
                    + "</div>";

            }}

        }}
    );


    const percentage =
        questions.length > 0
        ? Math.round(
            score / questions.length * 100
        )
        : 0;


    document.getElementById(
        "result"
    ).innerHTML =

        "<div class='result'>"
        + "🎉 Quiz Completed!"
        + "<br>"
        + score
        + " / "
        + questions.length
        + " ("
        + percentage
        + "%)"
        + "</div>"
        + "<br>"
        + "<p>Answered: "
        + answered
        + " / "
        + questions.length
        + "</p>"
        + review;

}}


function escapeHtml(text) {{

    return String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");

}}


function escapeAttribute(text) {{

    return escapeHtml(text);

}}


renderQuiz();

</script>

</body>

</html>
"""


    return html_content


# =========================================================
# ANSWER KEY GENERATOR
# =========================================================

def create_answer_key_html(
    title,
    sets
):

    header_html = build_header_html()

    footer_html = build_footer_html()

    html_content = f"""
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<title>{html.escape(APP_TITLE)} - Answer Key</title>

<style>

body {{
    font-family: Arial, sans-serif;
    padding: 30px;
}}

table {{
    width: 100%;
    border-collapse: collapse;
}}

th, td {{
    border: 1px solid #ccc;
    padding: 10px;
}}

th {{
    background: #f0f0f0;
}}

body {{
    max-width: 900px;
    margin: auto;
}}

{HEADER_FOOTER_CSS}

{QUIZ_THEME_CSS}

</style>

</head>

<body>

{header_html}

<h2>Answer Key</h2>

<p>{html.escape(title)}</p>
"""


    for question_set in sets:

        set_name = question_set.get(
            "set_name",
            "Question Set"
        )


        html_content += (
            f"<h2>{html.escape(set_name)}</h2>"
        )


        html_content += """
<table>

<tr>
<th>Question</th>
<th>Type</th>
<th>Correct Answer</th>
</tr>
"""


        for index, question in enumerate(
            question_set.get(
                "questions",
                []
            ),
            start=1
        ):

            html_content += f"""
<tr>

<td>Q{index}</td>

<td>
{html.escape(
    str(question.get("type", ""))
)}
</td>

<td>
{html.escape(
    str(question.get("correct_answer", ""))
)}
</td>

</tr>
"""


        html_content += "</table>"


    html_content += f"""

{footer_html}

</body>

</html>
"""


    return html_content


# =========================================================
# LOAD ENVIRONMENT
# =========================================================

load_dotenv()


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="📚",
    layout="wide"
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: 800;
    }

    .subtitle {
        font-size: 20px;
        color: #666666;
    }

    .step-box {
        padding: 18px;
        border-radius: 12px;
        border: 1px solid #dddddd;
        margin-bottom: 15px;
    }

    .approved-box {
        padding: 12px;
        border-radius: 10px;
        border: 1px solid #cccccc;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# INITIAL SESSION STATE
# =========================================================

if "generated_questions" not in st.session_state:
    st.session_state.generated_questions = None

if "approved_sets" not in st.session_state:
    st.session_state.approved_sets = {}

if "generation_settings" not in st.session_state:
    st.session_state.generation_settings = {}


# =========================================================
# HEADER
# =========================================================

st.markdown(
    "<style>" + HEADER_FOOTER_CSS.strip() + "</style>",
    unsafe_allow_html=True
)

st.markdown(
    build_header_html(),
    unsafe_allow_html=True
)

st.write(
    "Upload learning material → Generate questions → "
    "Teacher review → Approve → Create interactive HTML quizzes."
)

st.divider()


# =========================================================
# STEP 1 — UPLOAD LEARNING MATERIAL
# Supports PDF, uploaded images, and camera photos.
# PDF text is extracted locally; images are passed directly to Gemini Vision.

st.header("📚 Step 1 — Choose Learning Material")

source_mode = st.radio(
    "Choose source type",
    ["📄 PDF", "🖼️ Upload Image(s)", "📸 Take Photo"],
    horizontal=True,
)

uploaded_files = []
image_inputs = []
extracted_text = ""

if source_mode == "📄 PDF":

    uploaded_file = st.file_uploader(
        "Upload textbook chapter, notes or learning material",
        type=["pdf"],
        key="pdf_source",
    )

    if uploaded_file is not None:
        uploaded_files = [uploaded_file]

elif source_mode == "🖼️ Upload Image(s)":

    uploaded_files = st.file_uploader(
        "Upload one or more textbook pages / learning images",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
        key="image_sources",
    ) or []

else:

    camera_photo = st.camera_input(
        "Take a photo of the textbook page",
        key="camera_source",
    )

    if camera_photo is not None:
        uploaded_files = [camera_photo]


if uploaded_files:

    if source_mode == "📄 PDF":

        uploaded_file = uploaded_files[0]

        st.success(f"✅ Uploaded: {uploaded_file.name}")

        try:

            reader = PdfReader(uploaded_file)
            total_pages = len(reader.pages)

            st.info(f"📖 PDF contains {total_pages} page(s).")

            for page_number, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""
                extracted_text += (
                    f"\n\n--- PAGE {page_number} ---\n\n"
                    f"{text}"
                )

        except Exception as error:

            st.error(f"❌ Unable to read PDF: {error}")
            extracted_text = ""

    else:

        if len(uploaded_files) > 10:
            st.warning("⚠️ Please use a maximum of 10 images at a time.")
            uploaded_files = uploaded_files[:10]

        st.success(
            f"✅ {len(uploaded_files)} image(s) ready for Gemini Vision."
        )

        for image_index, image_file in enumerate(uploaded_files, start=1):

            image_bytes = image_file.getvalue()
            mime_type = getattr(image_file, "type", None) or "image/jpeg"

            image_inputs.append({
                "bytes": image_bytes,
                "mime_type": mime_type,
                "name": image_file.name,
                "source_number": image_index,
            })

            extracted_text += (
                f"\n\n--- PAGE {image_index} ---\n\n"
                f"[Image source {image_index}: {image_file.name}]"
            )

        if image_inputs:
            cols = st.columns(min(len(image_inputs), 4))
            for display_index, image_file in enumerate(uploaded_files):
                with cols[display_index % len(cols)]:
                    st.image(
                        image_file,
                        caption=f"Source {display_index + 1}: {image_file.name}",
                        use_container_width=True,
                    )


    # =====================================================
    # EXTRACTED TEXT
    # =====================================================

    if extracted_text.strip():

        if image_inputs:
            st.success(
                "✅ Image source is ready. Gemini Vision will read the page(s) directly."
            )
        else:
            st.success(
                "✅ Learning material extracted successfully."
            )

        with st.expander(
            "🔍 Preview Source Material"
        ):

            st.text_area(
                "Source Text / References",
                extracted_text,
                height=250
            )


        st.divider()


        # =================================================
        # STEP 3 — SETTINGS
        # =================================================

        st.header(
            "⚙️ Step 3 — Question Settings"
        )

        col1, col2 = st.columns(2)


        with col1:

            class_name = st.selectbox(
                "🎓 Class / Grade",
                [
                    "Grade 1",
                    "Grade 2",
                    "Grade 3",
                    "Grade 4",
                    "Grade 5",
                    "Grade 6",
                    "Grade 7",
                    "Grade 8",
                    "Grade 9",
                    "Grade 10",
                    "Grade 11",
                    "Grade 12"
                ],
                index=4
            )


            subject = st.selectbox(
                "📚 Subject",
                [
                    "Mathematics",
                    "Science",
                    "English",
                    "Tamil",
                    "Hindi",
                    "Social Science",
                    "Computer Science",
                    "General Knowledge",
                    "Other"
                ]
            )


            chapter = st.text_input(
                "📖 Chapter / Topic",
                placeholder="Example: National Emblem"
            )


        with col2:

            number_of_sets = st.number_input(
                "📝 Number of Question Sets",
                min_value=1,
                max_value=10,
                value=1,
                step=1
            )


            questions_per_set = st.number_input(
                "🔢 Questions per Set",
                min_value=1,
                max_value=50,
                value=4,
                step=1
            )


            difficulty = st.selectbox(
                "🎯 Difficulty Level",
                [
                    "Easy",
                    "Medium",
                    "Hard",
                    "Mixed"
                ]
            )


        # =================================================
        # QUESTION TYPES
        # =================================================

        st.write("### 🧩 Question Types")

        c1, c2, c3, c4 = st.columns(4)


        with c1:

            mcq = st.checkbox(
                "Multiple Choice",
                value=True
            )


        with c2:

            fill_blank = st.checkbox(
                "Fill in the Blanks",
                value=False
            )


        with c3:

            true_false = st.checkbox(
                "True / False",
                value=False
            )


        with c4:

            short_answer = st.checkbox(
                "Short Answer",
                value=False
            )


        # =================================================
        # LANGUAGE
        # =================================================

        language = st.selectbox(
            "🌐 Question Language",
            [
                "English",
                "Tamil",
                "Hindi"
            ]
        )


        st.divider()


        # =================================================
        # STEP 4 — AI GENERATION
        # =================================================

        st.header(
            "🤖 Step 4 — AI Question Generation"
        )

        generate_button = st.button(
            "🚀 GENERATE QUESTIONS",
            type="primary",
            use_container_width=True
        )


        if generate_button:

            selected_types = []


            if mcq:
                selected_types.append(
                    "Multiple Choice"
                )

            if fill_blank:
                selected_types.append(
                    "Fill in the Blanks"
                )

            if true_false:
                selected_types.append(
                    "True / False"
                )

            if short_answer:
                selected_types.append(
                    "Short Answer"
                )


            if not chapter.strip():

                st.warning(
                    "⚠️ Please enter the chapter/topic."
                )


            elif not selected_types:

                st.warning(
                    "⚠️ Please select at least one "
                    "question type."
                )


            elif questions_per_set < len(selected_types):

                st.warning(
                    f"⚠️ Please select at least "
                    f"{len(selected_types)} questions "
                    "per set so every selected type "
                    "can be included."
                )


            else:

                with st.spinner(
                    "🤖 SMARTQUIZ AI is generating "
                    "questions..."
                ):

                    try:

                        result = generate_questions(
                            source_text=extracted_text,
                            class_name=class_name,
                            subject=subject,
                            chapter=chapter,
                            number_of_sets=number_of_sets,
                            questions_per_set=questions_per_set,
                            difficulty=difficulty,
                            question_types=selected_types,
                            language=language,
                            image_inputs=image_inputs
                        )


                        st.session_state.generated_questions = result

                        st.session_state.generation_settings = {
                            "class_name": class_name,
                            "subject": subject,
                            "chapter": chapter,
                            "difficulty": difficulty,
                            "language": language,
                            "question_types": selected_types
                        }


                        # Reset approvals
                        st.session_state.approved_sets = {}


                        st.success(
                            "🎉 Questions generated successfully!"
                        )


                    except Exception as error:

                        st.error(
                            "❌ AI generation failed."
                        )

                        st.code(
                            str(error)
                        )


        # =================================================
        # STEP 5 — TEACHER REVIEW
        # =================================================

        if st.session_state.generated_questions:

            st.divider()

            st.header(
                "👩‍🏫 Step 5 — Teacher Review & Approval"
            )

            st.info(
                "Review every AI-generated question before "
                "sharing it with students."
            )


            result = st.session_state.generated_questions

            sets = result.get(
                "sets",
                []
            )


            if sets:

                tab_names = []

                for index, question_set in enumerate(sets):

                    tab_names.append(
                        question_set.get(
                            "set_name",
                            f"Set {index + 1}"
                        )
                    )


                tabs = st.tabs(tab_names)


                for set_index, (
                    tab,
                    question_set
                ) in enumerate(
                    zip(tabs, sets)
                ):

                    with tab:

                        set_name = question_set.get(
                            "set_name",
                            f"Set {set_index + 1}"
                        )


                        questions = question_set.get(
                            "questions",
                            []
                        )


                        st.write(
                            f"### {set_name}"
                        )


                        st.write(
                            f"Questions: "
                            f"**{len(questions)}**"
                        )


                        # =========================================
                        # QUESTIONS
                        # =========================================

                        for q_index in range(
                            len(questions)
                        ):

                            question = questions[q_index]

                            question_number = q_index + 1

                            question_type = question.get(
                                "type",
                                "Multiple Choice"
                            )


                            with st.container(
                                border=True
                            ):

                                st.markdown(
                                    f"### Q{question_number}"
                                )


                                # ---------------------------------
                                # QUESTION TEXT
                                # ---------------------------------

                                edited_question = st.text_area(
                                    "Question",
                                    value=question.get(
                                        "question",
                                        ""
                                    ),
                                    key=(
                                        f"edit_question_"
                                        f"{set_index}_"
                                        f"{q_index}"
                                    )
                                )


                                # ---------------------------------
                                # QUESTION TYPE
                                # ---------------------------------

                                st.write(
                                    f"**Type:** "
                                    f"{question_type}"
                                )


                                # ---------------------------------
                                # MCQ OPTIONS
                                # ---------------------------------

                                edited_options = []


                                if question_type == (
                                    "Multiple Choice"
                                ):

                                    options = question.get(
                                        "options",
                                        []
                                    )


                                    while len(options) < 4:

                                        options.append("")


                                    option_columns = st.columns(2)


                                    for option_index in range(4):

                                        with option_columns[
                                            option_index % 2
                                        ]:

                                            option_value = st.text_input(
                                                f"Option "
                                                f"{chr(65 + option_index)}",
                                                value=options[
                                                    option_index
                                                ],
                                                key=(
                                                    f"edit_option_"
                                                    f"{set_index}_"
                                                    f"{q_index}_"
                                                    f"{option_index}"
                                                )
                                            )

                                            edited_options.append(
                                                option_value
                                            )


                                # ---------------------------------
                                # CORRECT ANSWER
                                # ---------------------------------

                                edited_answer = st.text_input(
                                    "Correct Answer",
                                    value=str(
                                        question.get(
                                            "correct_answer",
                                            ""
                                        )
                                    ),
                                    key=(
                                        f"edit_answer_"
                                        f"{set_index}_"
                                        f"{q_index}"
                                    )
                                )


                                # ---------------------------------
                                # DIFFICULTY
                                # ---------------------------------

                                difficulty_options = [
                                    "Easy",
                                    "Medium",
                                    "Hard"
                                ]


                                current_difficulty = question.get(
                                    "difficulty",
                                    "Easy"
                                )


                                if current_difficulty not in (
                                    difficulty_options
                                ):

                                    current_difficulty = "Easy"


                                edited_difficulty = st.selectbox(
                                    "Difficulty",
                                    difficulty_options,
                                    index=difficulty_options.index(
                                        current_difficulty
                                    ),
                                    key=(
                                        f"edit_difficulty_"
                                        f"{set_index}_"
                                        f"{q_index}"
                                    )
                                )


                                # ---------------------------------
                                # SOURCE
                                # ---------------------------------

                                source_page = question.get(
                                    "source_page"
                                )


                                if source_page:

                                    st.caption(
                                        f"📖 Source Page: "
                                        f"{source_page}"
                                    )


                                # ---------------------------------
                                # ACTION BUTTONS
                                # ---------------------------------

                                b1, b2, b3 = st.columns(3)


                                with b1:

                                    if st.button(
                                        "💾 Save Changes",
                                        key=(
                                            f"save_"
                                            f"{set_index}_"
                                            f"{q_index}"
                                        )
                                    ):

                                        question[
                                            "question"
                                        ] = edited_question


                                        if (
                                            question_type
                                            == "Multiple Choice"
                                        ):

                                            question[
                                                "options"
                                            ] = edited_options


                                        question[
                                            "correct_answer"
                                        ] = edited_answer


                                        question[
                                            "difficulty"
                                        ] = edited_difficulty


                                        st.success(
                                            "✅ Question updated."
                                        )

                                        st.rerun()


                                with b2:

                                    if st.button(
                                        "🔄 Regenerate",
                                        key=(
                                            f"regen_"
                                            f"{set_index}_"
                                            f"{q_index}"
                                        )
                                    ):

                                        try:

                                            settings = (
                                                st.session_state
                                                .generation_settings
                                            )


                                            with st.spinner(
                                                "🤖 Generating "
                                                "replacement question..."
                                            ):

                                                new_result = (
                                                    generate_questions(
                                                        source_text=extracted_text,
                                                        class_name=settings[
                                                            "class_name"
                                                        ],
                                                        subject=settings[
                                                            "subject"
                                                        ],
                                                        chapter=settings[
                                                            "chapter"
                                                        ],
                                                        number_of_sets=1,
                                                        questions_per_set=1,
                                                        difficulty=(
                                                            question.get(
                                                                "difficulty",
                                                                "Easy"
                                                            )
                                                        ),
                                                        question_types=[
                                                            question_type
                                                        ],
                                                        language=settings[
                                                            "language"
                                                        ],
                                                        image_inputs=image_inputs
                                                    )
                                                )


                                            new_sets = new_result.get(
                                                "sets",
                                                []
                                            )


                                            if new_sets:

                                                new_questions = (
                                                    new_sets[0].get(
                                                        "questions",
                                                        []
                                                    )
                                                )


                                                if new_questions:

                                                    questions[
                                                        q_index
                                                    ] = (
                                                        new_questions[0]
                                                    )


                                                    st.success(
                                                        "✅ Question regenerated."
                                                    )

                                                    st.rerun()


                                        except Exception as error:

                                            st.error(
                                                f"❌ Regeneration failed: "
                                                f"{error}"
                                            )


                                with b3:

                                    if st.button(
                                        "🗑️ Delete",
                                        key=(
                                            f"delete_"
                                            f"{set_index}_"
                                            f"{q_index}"
                                        )
                                    ):

                                        questions.pop(
                                            q_index
                                        )

                                        st.warning(
                                            "Question deleted."
                                        )

                                        st.rerun()


                        # =========================================
                        # APPROVAL
                        # =========================================

                        st.divider()


                        if st.session_state.approved_sets.get(
                            set_index,
                            False
                        ):

                            st.success(
                                f"✅ {set_name} is approved."
                            )


                        else:

                            if st.button(
                                f"✅ APPROVE {set_name}",
                                key=f"approve_{set_index}",
                                type="primary",
                                use_container_width=True
                            ):

                                st.session_state.approved_sets[
                                    set_index
                                ] = True


                                st.success(
                                    f"🎉 {set_name} approved!"
                                )

                                st.rerun()


            # =================================================
            # APPROVAL STATUS
            # =================================================

            st.divider()

            st.subheader(
                "📋 Approval Status"
            )


            for set_index, question_set in enumerate(
                sets
            ):

                set_name = question_set.get(
                    "set_name",
                    f"Set {set_index + 1}"
                )


                if st.session_state.approved_sets.get(
                    set_index,
                    False
                ):

                    st.write(
                        f"✅ {set_name} — Approved"
                    )

                else:

                    st.write(
                        f"⏳ {set_name} — Pending"
                    )


            # =================================================
            # CHECK ALL APPROVED
            # =================================================

            all_approved = (
                len(sets) > 0
                and all(
                    st.session_state.approved_sets.get(
                        index,
                        False
                    )
                    for index in range(len(sets))
                )
            )


            if all_approved:

                st.success(
                    "🎉 All question sets have been approved!"
                )


                # =============================================
                # STEP 6 — HTML GENERATION
                # =============================================

                st.divider()

                st.header(
                    "🌐 Step 6 — Create Interactive HTML Quizzes"
                )


                st.write(
                    "All approved questions can now be converted "
                    "into standalone HTML quiz files."
                )


                if st.button(
                    "🌐 CREATE HTML QUIZZES",
                    type="primary",
                    use_container_width=True
                ):

                    st.session_state[
                        "html_ready"
                    ] = True

                    st.success(
                        "🎉 HTML quizzes are ready!"
                    )


                # =============================================
                # STEP 7 — DOWNLOAD
                # =============================================

                if st.session_state.get(
                    "html_ready",
                    False
                ):

                    st.divider()

                    st.header(
                        "📥 Step 7 — Download & Share"
                    )


                    settings = (
                        st.session_state
                        .generation_settings
                    )


                    quiz_title = (
                        f"{settings.get('class_name', 'Quiz')}"
                        f" - "
                        f"{settings.get('subject', 'Subject')}"
                        f" - "
                        f"{settings.get('chapter', 'Chapter')}"
                    )


                    generated_files = []


                    # =========================================
                    # CREATE EACH HTML FILE
                    # =========================================

                    for set_index, question_set in enumerate(
                        sets
                    ):

                        set_name = question_set.get(
                            "set_name",
                            f"Set {set_index + 1}"
                        )


                        questions = question_set.get(
                            "questions",
                            []
                        )


                        html_content = create_quiz_html(
                            title=quiz_title,
                            set_name=set_name,
                            questions=questions
                        )


                        safe_set_name = (
                            set_name
                            .replace(" ", "_")
                            .replace("/", "_")
                        )


                        filename = (
                            f"SMARTQUIZ_"
                            f"{safe_set_name}.html"
                        )


                        generated_files.append(
                            (
                                filename,
                                html_content
                            )
                        )


                        st.download_button(
                            label=(
                                f"📄 Download "
                                f"{set_name}.html"
                            ),
                            data=html_content,
                            file_name=filename,
                            mime="text/html",
                            key=f"download_{set_index}"
                        )


                    # =========================================
                    # ANSWER KEY
                    # =========================================

                    answer_key_html = create_answer_key_html(
                        title=quiz_title,
                        sets=sets
                    )


                    st.download_button(
                        label="🔑 Download Answer Key",
                        data=answer_key_html,
                        file_name="SMARTQUIZ_Answer_Key.html",
                        mime="text/html",
                        key="download_answer_key"
                    )


                    generated_files.append(
                        (
                            "SMARTQUIZ_Answer_Key.html",
                            answer_key_html
                        )
                    )


                    # =========================================
                    # CREATE ZIP
                    # =========================================

                    zip_buffer = io.BytesIO()


                    with zipfile.ZipFile(
                        zip_buffer,
                        "w",
                        zipfile.ZIP_DEFLATED
                    ) as zip_file:

                        for filename, content in (
                            generated_files
                        ):

                            zip_file.writestr(
                                filename,
                                content
                            )


                    zip_buffer.seek(0)


                    st.download_button(
                        label="📦 DOWNLOAD ALL AS ZIP",
                        data=zip_buffer,
                        file_name="SMARTQUIZ_Question_Sets.zip",
                        mime="application/zip",
                        key="download_zip",
                        type="primary",
                        use_container_width=True
                    )


                    st.success(
                        "📚 Your approved SMARTQUIZ question "
                        "papers are ready to share with students."
                    )


    else:

        st.warning(
            "⚠️ No readable text was found in this PDF. "
            "It may be a scanned/image-only PDF."
        )


# =========================================================
# FOOTER
# =========================================================

st.markdown(
    build_footer_html(),
    unsafe_allow_html=True
)
