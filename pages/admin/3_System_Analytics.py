import streamlit as st
from database import SessionLocal, UserModel, QuestionBankItem, ExamPaper, SubmissionRecord

st.set_page_config(page_title="System Analytics", page_icon="📊", layout="wide")

if st.session_state.get("role") != "PragyanAI Admin":
    st.error("Access Denied. Admins only.")
    st.stop()

st.title("📊 PragyanAI Global System Analytics")
st.markdown("Comprehensive audit trail, platform usage trends, and system-wide performance metrics.")

db = SessionLocal()
users_count = db.query(UserModel).count()
faculties_count = db.query(UserModel).filter(UserModel.role == "Faculty").count()
students_count = db.query(UserModel).filter(UserModel.role == "Student").count()
questions_count = db.query(QuestionBankItem).count()
exams_count = db.query(ExamPaper).count()
submissions = db.query(SubmissionRecord).all()
db.close()

# High-level overview metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Users", users_count)
col2.metric("Question Bank Size", questions_count)
col3.metric("Exam Papers Created", exams_count)
col4.metric("Total Submissions Evaluated", len(submissions))

st.divider()

# Platform User Distribution Chart
st.subheader("👥 User Distribution by Role")
st.bar_chart({
    "Faculties": faculties_count,
    "Students": students_count,
    "Admins": users_count - (faculties_count + students_count)
})

# Recent Platform Activity Log
st.subheader("📝 Recent Platform Assessment Submissions")
if not submissions:
    st.info("No submission activity recorded across the platform yet.")
else:
    sub_summary = []
    for s in submissions[-10:]: # Show last 10
        sub_summary.append({
            "Student": s.student_name,
            "Paper": s.paper_title,
            "Score (%)": s.score,
            "Feedback Summary": s.feedback[:60] + "..." if s.feedback and len(s.feedback) > 60 else s.feedback
        })
    st.table(sub_summary)
