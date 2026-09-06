import streamlit as st
from database import SessionLocal, QuestionBankItem, SubmissionRecord
from agentic_workflow import evaluate_answer_node

st.set_page_config(page_title="Practice & Answer Evaluation", page_icon="🎯", layout="wide")

if st.session_state.get("role") != "Student":
    st.error("Access Denied. Student portal only.")
    st.stop()

st.title("🎯 Self-Paced Practice & AI Answer Evaluation")
st.markdown("Practice concept questions one by one. Choose your submission method (Text Answer, Document Upload, Simulated OCR Handwritten, or Voice Log), and get instant AI evaluation against ideal answers.")

db = SessionLocal()
questions = db.query(QuestionBankItem).all()
db.close()

if not questions:
    st.info("No questions found in the Question Bank yet.")
else:
    q_options = {f"[{q.id}] {q.concept} ({q.q_type})": q for q in questions}
    selected_key = st.selectbox("Select Question for Practice", list(q_options.keys()))
    target_q = q_options[selected_key]

    st.markdown(f"### Question Details")
    st.info(f"**Question:** {target_q.question_text}")
    st.write(f"**Module:** {target_q.module} | **Difficulty:** {target_q.difficulty}")

    sub_mode = st.radio("Choose Answer Submission Method", ["Text Input", "Document Upload (PDF/Doc)", "Handwritten Answer (OCR)", "Voice Log Transcript"])

    student_answer_input = ""
    if sub_mode == "Text Input":
        student_answer_input = st.text_area("Type your detailed answer here:", placeholder="Explain your reasoning...")
    elif sub_mode == "Document Upload":
        uploaded_doc = st.file_uploader("Upload assignment document (.pdf, .docx)", type=["pdf", "docx", "txt"])
        if uploaded_doc:
            student_answer_input = uploaded_doc.read().decode("utf-8", errors="ignore")
            st.success("Document uploaded and parsed successfully!")
    elif sub_mode == "Handwritten Answer (OCR)":
        handwritten_file = st.file_uploader("Upload image of handwritten answer (.png, .jpg)", type=["png", "jpg", "jpeg"])
        if handwritten_file:
            st.image(handwritten_file, caption="Uploaded Handwritten Paper", width=300)
            student_answer_input = st.text_area("Simulated OCR Extracted Text", value=f"OCR extracted text for concept {target_q.concept}: Student explained core equations accurately.")
    elif sub_mode == "Voice Log Transcript":
        audio_file = st.file_uploader("Upload voice recording (.wav, .mp3)", type=["wav", "mp3", "m4a"])
        if audio_file:
            st.audio(audio_file)
            student_answer_input = st.text_area("Voice-to-Text Transcription", value=f"Verbal explanation provided for {target_q.concept} with clear logical steps.")

    if st.button("Evaluate Answer with AI RAG Agent"):
        if not student_answer_input.strip():
            st.warning("Please provide an answer submission before evaluating.")
        else:
            with st.spinner("Evaluating response against ideal answer using AI agent..."):
                eval_state = {
                    "student_response": student_answer_input,
                    "ideal_answer": target_q.ideal_answer
                }
                result_state = evaluate_answer_node(eval_state)
                eval_res = result_state.get("evaluation", {})

                st.success("Evaluation Complete!")
                st.metric("Awarded Score", f"{eval_res.get('score', 0)} / 100")
                st.info(f"**Evaluator Feedback:** {eval_res.get('feedback', 'No feedback provided.')}")
                st.error(f"**RAG Remediation Explainer:** {eval_res.get('rag_explanation', 'Review foundational concepts.')}")

                # Save record to database
                db = SessionLocal()
                sub = SubmissionRecord(
                    student_name=st.session_state.get("full_name", "Ada Lovelace"),
                    paper_title="Practice Mode Session",
                    question_id=target_q.id,
                    answer_text=student_answer_input,
                    score=eval_res.get('score', 0.0),
                    feedback=eval_res.get('feedback', ''),
                    rag_explanation=eval_res.get('rag_explanation', '')
                )
                db.add(sub)
                db.commit()
                db.close()
