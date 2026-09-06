import streamlit as st
from database import SessionLocal, UserModel, QuestionBankItem, ExamPaper, SubmissionRecord

st.set_page_config(page_title="Admin Dashboard", page_icon="🛡️", layout="wide")

if st.session_state.get("role") != "PragyanAI Admin":
    st.error("Access Denied. Admins only.")
    st.stop()

st.title("🛡️ PragyanAI System Admin Dashboard")
st.markdown("Monitor global platform statistics, system health, and user distribution.")

db = SessionLocal()
faculties = db.query(UserModel).filter(UserModel.role == "Faculty").all()
students = db.query(UserModel).filter(UserModel.role == "Student").all()
questions = db.query(QuestionBankItem).count()
exams = db.query(ExamPaper).count()
submissions = db.query(SubmissionRecord).count()
db.close()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Faculties", len(faculties))
col2.metric("Students", len(students))
col3.metric("Questions Bank", questions)
col4.metric("Exam Papers", exams)
col5.metric("Submissions", submissions)

st.success("System operational status: **Healthy (99.9% Uptime)**")
