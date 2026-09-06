import streamlit as st
from database import SessionLocal, QuestionBankItem, ExamPaper

st.set_page_config(page_title="Exam Paper Creation", page_icon="📑", layout="wide")

if st.session_state.get("role") != "Faculty":
    st.error("Access Denied. Faculty members only.")
    st.stop()

st.title("📑 Exam Paper Compilation Studio")
st.markdown("Compile customized exam papers by selecting modules, concepts, difficulty tiers, and question formats (MCQ, Short Answer, Long Answer, or Mix) mapped to PO scales.")

db = SessionLocal()
bank_items = db.query(QuestionBankItem).all()
db.close()

if not bank_items:
    st.warning("No questions found in the Question Bank. Please generate questions using **3_Question_Generator.py** first.")
else:
    with st.form("exam_paper_form"):
        paper_title = st.text_input("Exam Paper Title", placeholder="e.g., Mid-Term AI Assessment - Semester 4")
        subject_name = st.text_input("Subject Name", placeholder="e.g., Artificial Intelligence")
        paper_type = st.selectbox("Exam Format", ["MCQ Only", "Short Answer Only", "Long Answer Only", "Comprehensive Mix"])
        
        st.subheader("Select Questions from Question Bank")
        selected_q_ids = []
        for q in bank_items:
            checked = st.checkbox(f"[{q.id}] ({q.q_type} | {q.difficulty}) {q.question_text[:80]}...", key=f"q_select_{q.id}")
            if checked:
                selected_q_ids.append(q.id)

        submitted = st.form_submit_button("Compile & Save Exam Paper")

        if submitted:
            if not paper_title.strip() or not subject_name.strip():
                st.warning("Please provide an Exam Title and Subject Name.")
            elif not selected_q_ids:
                st.warning("Please select at least one question to compile the exam paper.")
            else:
                db = SessionLocal()
                summary_text = f"Compiled {len(selected_q_ids)} questions for format: {paper_type}."
                exam = ExamPaper(
                    title=paper_title,
                    subject=subject_name,
                    paper_type=paper_type,
                    questions_summary=summary_text
                )
                db.add(exam)
                db.commit()
                db.close()
                st.success(f"Exam Paper '{paper_title}' successfully compiled and saved!")

    st.divider()
    st.subheader("🗂️ Previously Compiled Exam Papers")
    db = SessionLocal()
    existing_exams = db.query(ExamPaper).all()
    db.close()
    
    if existing_exams:
        for exam in existing_exams:
            with st.expander(f"{exam.title} ({exam.subject}) — Format: {exam.paper_type}"):
                st.write(f"**Summary:** {exam.questions_summary}")
    else:
        st.info("No exam papers compiled yet.")
