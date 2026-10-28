import os
import json
import re
from datetime import date, datetime, timedelta

import streamlit as st
import fitz  # PyMuPDF
from google import genai
from google.genai import types

st.set_page_config(page_title="AI Study Assistant", page_icon="📚", layout="wide")

DEFAULT_MODEL = "gemini-2.5-flash"
MAX_TEXT_CHARS = 80000

st.title("📚 AI Study Assistant")
st.caption("Turn lecture notes into revision material and a realistic exam plan.")

with st.sidebar:
    st.header("⚙️ Settings")
    api_key_input = st.text_input(
        "Gemini API key",
        type="password",
        help="Alternatively, set GEMINI_API_KEY in your environment or Streamlit secrets.",
    )
    model_name = st.text_input("Gemini model", value=DEFAULT_MODEL)
    st.caption("Get an API key from Google AI Studio. Keep it private.")

api_key = api_key_input.strip() or os.getenv("GEMINI_API_KEY", "")
if not api_key:
    try:
        api_key = str(st.secrets.get("GEMINI_API_KEY", "")).strip()
    except Exception:
        api_key = ""

def get_client():
    if not api_key:
        raise ValueError("Add your Gemini API key in the sidebar or configure GEMINI_API_KEY.")
    return genai.Client(api_key=api_key)

def extract_text(uploaded_file):
    """Extract text from PDF, TXT, or Markdown uploads."""
    filename = uploaded_file.name.lower()
    raw = uploaded_file.getvalue()
    if filename.endswith(".pdf"):
        pieces = []
        with fitz.open(stream=raw, filetype="pdf") as pdf:
            for page in pdf:
                pieces.append(page.get_text("text"))
        text = "\n\n".join(pieces)
    elif filename.endswith((".txt", ".md")):
        text = raw.decode("utf-8", errors="replace")
    else:
        raise ValueError("Unsupported file type. Upload a PDF, TXT, or Markdown file.")
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        raise ValueError(
            "No readable text was found. If this is a scanned PDF, run OCR on it first and upload the searchable PDF."
        )
    return text[:MAX_TEXT_CHARS]

def ask_gemini(prompt, source_text):
    client = get_client()
    response = client.models.generate_content(
        model=model_name.strip() or DEFAULT_MODEL,
        contents=[
            types.Part.from_text(text=(
                "You are a careful, student-friendly study assistant. Use the supplied notes as the main source. "
                "Do not invent facts. If something is not covered, say so. Format the answer in clear Markdown.\n\n"
                f"TASK:\n{prompt}\n\nLECTURE NOTES:\n{source_text}"
            ))
        ],
        config=types.GenerateContentConfig(temperature=0.3),
    )
    result = (response.text or "").strip()
    if not result:
        raise RuntimeError("Gemini returned an empty response. Please try again.")
    return result

def run_ai(task_label, prompt, source_text):
    if not source_text:
        st.warning("Upload a file and extract its text first.")
        return
    with st.spinner(f"Generating {task_label.lower()}…"):
        try:
            result = ask_gemini(prompt, source_text)
            st.session_state["result_" + task_label] = result
        except Exception as exc:
            st.error(f"Could not generate {task_label.lower()}: {exc}")

uploaded = st.file_uploader(
    "Upload lecture notes",
    type=["pdf", "txt", "md"],
    help="PDF, plain text, or Markdown. Text-based PDFs work best.",
)

if uploaded:
    try:
        extracted_text = extract_text(uploaded)
        st.success(f"Extracted {len(extracted_text):,} characters from **{uploaded.name}**.")
        with st.expander("Preview extracted text"):
            st.text(extracted_text[:6000] + ("\n\n[Preview shortened]" if len(extracted_text) > 6000 else ""))
        st.session_state["source_text"] = extracted_text
        st.session_state["source_name"] = uploaded.name
    except Exception as exc:
        st.error(str(exc))

source_text = st.session_state.get("source_text", "")

tab_summary, tab_mcq, tab_short, tab_cards, tab_plan = st.tabs(
    ["📝 Summary", "✅ MCQs", "✍️ Short questions", "🃏 Flashcards", "🗓️ Exam plan"]
)

with tab_summary:
    st.subheader("Lecture summary")
    summary_style = st.selectbox("Summary style", ["Exam-friendly bullet notes", "Detailed section-by-section summary", "Quick revision sheet"])
    if st.button("Generate summary", type="primary", key="make_summary"):
        run_ai("summary", f"Summarize these notes as {summary_style.lower()}. Include key terms, important explanations, and a concise final revision checklist.", source_text)
    if st.session_state.get("result_summary"):
        st.markdown(st.session_state["result_summary"])
        st.download_button("Download summary (.md)", st.session_state["result_summary"], "lecture_summary.md", "text/markdown")

with tab_mcq:
    st.subheader("Multiple-choice questions")
    mcq_count = st.slider("Number of MCQs", 5, 25, 10)
    difficulty = st.selectbox("Difficulty", ["Mixed", "Easy", "Medium", "Hard"], key="mcq_difficulty")
    if st.button("Generate MCQs", key="make_mcq"):
        run_ai("mcq", f"Create {mcq_count} multiple-choice questions at {difficulty.lower()} difficulty. Give four options (A-D), identify the correct answer, and add a one-sentence explanation for each. Keep questions grounded in the notes.", source_text)
    if st.session_state.get("result_mcq"):
        st.markdown(st.session_state["result_mcq"])
        st.download_button("Download MCQs (.md)", st.session_state["result_mcq"], "mcqs.md", "text/markdown")

with tab_short:
    st.subheader("Short questions with answers")
    short_count = st.slider("Number of short questions", 5, 25, 10)
    answer_length = st.selectbox("Answer length", ["2–3 sentences", "A short paragraph", "Bullet points"])
    if st.button("Generate short questions", key="make_short"):
        run_ai("short_questions", f"Write {short_count} exam-style short questions with accurate answers of {answer_length}. Number each question and make answers easy to revise.", source_text)
    if st.session_state.get("result_short_questions"):
        st.markdown(st.session_state["result_short_questions"])
        st.download_button("Download questions (.md)", st.session_state["result_short_questions"], "short_questions.md", "text/markdown")

with tab_cards:
    st.subheader("Interactive flashcards")
    card_count = st.slider("Number of flashcards", 5, 30, 10)
    if st.button("Create flashcards", key="make_cards"):
        with st.spinner("Creating flashcards…"):
            try:
                raw_cards = ask_gemini(
                    f"""Create exactly {card_count} concise flashcards from the notes. Return ONLY valid JSON, no Markdown fences, in this shape:
{{"cards":[{{"front":"question or term","back":"concise answer"}}]}}
Each front should ask one thing. Keep answers short.""",
                    source_text,
                )
                raw_cards = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_cards.strip(), flags=re.I)
                data = json.loads(raw_cards)
                cards = data.get("cards", [])
                cards = [
                    {"front": str(c.get("front", "")).strip(), "back": str(c.get("back", "")).strip()}
                    for c in cards if c.get("front") and c.get("back")
                ]
                if not cards:
                    raise ValueError("The model did not return usable flashcards. Try again.")
                st.session_state["flashcards"] = cards[:card_count]
                st.session_state["card_index"] = 0
                st.session_state["card_revealed"] = False
            except Exception as exc:
                st.error(f"Could not create flashcards: {exc}")
    cards = st.session_state.get("flashcards", [])
    if cards:
        idx = min(st.session_state.get("card_index", 0), len(cards) - 1)
        st.caption(f"Card {idx + 1} of {len(cards)}")
        st.progress((idx + 1) / len(cards))
        st.markdown("**Front**")
        st.info(cards[idx]["front"])
        if st.button("Reveal answer" if not st.session_state.get("card_revealed") else "Hide answer", key="reveal_card"):
            st.session_state["card_revealed"] = not st.session_state.get("card_revealed", False)
        if st.session_state.get("card_revealed"):
            st.success(cards[idx]["back"])
        c1, c2, c3 = st.columns([1, 1, 2])
        with c1:
            if st.button("← Previous", disabled=idx == 0, key="prev_card"):
                st.session_state["card_index"] = idx - 1
                st.session_state["card_revealed"] = False
                st.rerun()
        with c2:
            if st.button("Next →", disabled=idx >= len(cards) - 1, key="next_card"):
                st.session_state["card_index"] = idx + 1
                st.session_state["card_revealed"] = False
                st.rerun()
        with c3:
            if st.button("Reset deck", key="reset_cards"):
                st.session_state["card_index"] = 0
                st.session_state["card_revealed"] = False
                st.rerun()
        if st.button("Download flashcards (.json)", key="download_cards"):
            st.download_button(
                "Save JSON file",
                json.dumps({"cards": cards}, ensure_ascii=False, indent=2),
                "flashcards.json",
                "application/json",
                key="save_cards_json",
            )

with tab_plan:
    st.subheader("Personalized exam preparation plan")
    st.write("Enter your exam date, daily study time, and topics. The app creates a day-by-day schedule and reserves the final day for revision.")
    with st.form("plan_form"):
        exam_date = st.date_input("Exam date", min_value=date.today() + timedelta(days=1), value=date.today() + timedelta(days=7))
        study_hours = st.number_input("Available study hours per day", min_value=0.5, max_value=16.0, value=2.0, step=0.5)
        topics_text = st.text_area("Topics (one per line)", placeholder="Database architecture\nER model\nNormalization\nSQL joins", height=150)
        include_practice = st.checkbox("Include practice questions and self-testing", value=True)
        create_plan = st.form_submit_button("Create my study plan", type="primary")
    if create_plan:
        topics = [line.strip(" •-\t") for line in topics_text.splitlines() if line.strip(" •-\t")]
        if not topics:
            st.warning("Enter at least one topic.")
        elif exam_date <= date.today():
            st.warning("Choose an exam date in the future.")
        else:
            days = (exam_date - date.today()).days
            study_days = max(1, days)
            plan_prompt = f"""Create a practical exam plan using ONLY these inputs.
Exam date: {exam_date.isoformat()}
Days available starting today: {study_days}
Available study time per day: {study_hours:g} hours
Topics in priority order: {json.dumps(topics, ensure_ascii=False)}
Include practice/self-testing: {include_practice}
Create a Markdown table with Day/Date, Topics, Study tasks, and Time allocation. Distribute all topics across the available days, avoid unrealistic workloads, include short breaks within each study session, schedule active recall/practice, and use the final day before the exam for light revision if there is enough time. Do not schedule beyond the exam date. Clearly state if the time is tight."""
            with st.spinner("Building your study plan…"):
                try:
                    plan = ask_gemini(plan_prompt, source_text or "No lecture file uploaded. Use only the topic list and planning inputs.")
                    st.session_state["exam_plan"] = plan
                except Exception as exc:
                    # A deterministic fallback keeps planning available even if Gemini is unavailable.
                    schedule = []
                    for i in range(days):
                        day = date.today() + timedelta(days=i)
                        topic = topics[i % len(topics)]
                        task = f"Study {topic}; make brief notes; take a 5–10 minute break each 25–50 minutes."
                        if include_practice:
                            task += " Finish with active recall or practice questions."
                        if i == days - 1:
                            task = "Light revision of key points and weak areas; prepare materials and sleep on time."
                        schedule.append(f"| {i + 1} | {day.isoformat()} | {topic if i < days - 1 else 'All topics (light revision)'} | {task} | {study_hours:g} hours |")
                    fallback = "### Study plan (offline fallback)\n\nGemini could not generate the enhanced plan, so this basic schedule was created instead.\n\n| Day | Date | Focus | Tasks | Time |\n|---:|---|---|---|---:|\n" + "\n".join(schedule) + f"\n\nExam date: **{exam_date.isoformat()}**. Keep sessions manageable and take short breaks.\n\nGemini message: {exc}"
                    st.session_state["exam_plan"] = fallback
            st.markdown(st.session_state["exam_plan"])
    if st.session_state.get("exam_plan"):
        st.download_button("Download study plan (.md)", st.session_state["exam_plan"], "exam_study_plan.md", "text/markdown")

st.divider()
st.caption("Privacy note: uploaded text is sent to Google Gemini only when you click a generation button. Do not upload confidential material.")
