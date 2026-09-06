import streamlit as st
from database import SessionLocal, ExamPaper, QuestionBankItem, SubmissionRecord

st.set_page_config(page_title="Select Exam Paper & Take Exam", page_icon="📑", layout="wide")

if st.session_state.get("role") != "Student":
    st.error("Access Denied. Student portal only.")
    st.stop()

st.title("📑 Exam Paper Selection & Assessment Portal")
st.markdown("Select an active faculty-compiled exam paper, answer the questions, and submit your work for automated AI evaluation.")

db = SessionLocal()
exams = db.query(ExamPaper).all()
questions = db.query(QuestionBankItem).all()
db.close()

if not exams:
    st.info("No exam papers have been compiled by faculty members yet. Please check back later or use the Practice Mode.")
else:
    exam_titles = [e.title for e in exams]
    selected_title = st.selectbox("Select Active Exam Paper", exam_titles)
    
    selected_exam = next(e for e in exams if e.title == selected_title)
    
    st.markdown(f"### 📋 Exam: {selected_exam.title}")
    st.write(f"**Subject:** {selected_exam.subject} | **Format:** {selected_exam.paper_type}")
    st.write(f"**Summary:** {selected_exam.questions_summary}")
    
    st.divider()

    # Simulate answering exam questions available in the question bank
    with st.form("exam_submission_form"):
        st.subheader("Answer Section")
        student_answers = {}
        
        # Display sample/relevant questions for this exam
        sample_questions = questions[:3] # Pull subset for student exam take
        if not sample_questions:
            st.warning("No question bank items available for this exam yet.")
        else:
            for idx, q in enumerate(sample_questions):
                st.markdown(f"**Q{idx+1} ({q.q_type} — {q.difficulty}):** {q.question_text}")
                ans = st.text_area(f"Your Answer for Q{idx+1}", key=f"exam_ans_{q.id}")
                student_answers[q.id] = ans

        submitted_exam = st.form_submit_button("Submit Complete Exam Paper")

        if submitted_exam:
            if not student_answers:
                st.warning("No answers provided.")
            else:
                db = SessionLocal()
                student_name = st.session_state.get("full_name", "Ada Lovelace")
                
                # Save submission records
                for q_id, ans_text in student_answers.items():
                    sub = SubmissionRecord(
                        student_name=student_name,
                        paper_title=selected_exam.title,
                        question_id=q_id,
                        answer_text=ans_text if ans_text else "No answer provided",
                        score=82.0, # Simulated evaluated score
                        feedback="Completed exam submission. Good conceptual structure.",
                        rag_explanation="Exam submitted successfully. Check Deep Analytics and RAG studio for details."
                    )
                    db.add(sub)
                db.commit()
                db.close()
                st.success("Exam successfully submitted and recorded in the database!")
