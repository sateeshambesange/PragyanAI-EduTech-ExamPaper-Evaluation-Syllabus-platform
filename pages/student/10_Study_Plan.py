import os
import streamlit as st
from database import SessionLocal, SubmissionRecord, QuestionBankItem
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

st.set_page_config(page_title="Personalized Study Plan", page_icon="📚", layout="wide")

if st.session_state.get("role") != "Student":
    st.error("Access Denied. Student portal only.")
    st.stop()

st.title("📚 Personalized Remediation & Study Plan Generator")
st.markdown("Generate custom study blueprints containing high-importance questions, model answers, and targeted practice tasks based on your recent evaluation history.")

GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY", "your-groq-api-key"))
llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.4, api_key=GROQ_API_KEY)

# Fetch student historical weak areas
db = SessionLocal()
student_name = st.session_state.get("full_name", "Ada Lovelace")
user_subs = db.query(SubmissionRecord).filter(SubmissionRecord.student_name == student_name).all()
all_questions = {q.id: q for q in db.query(QuestionBankItem).all()}
db.close()

# Identify weak concepts if any
weak_concepts = []
for sub in user_subs:
    if sub.score < 75.0:
        q = all_questions.get(sub.question_id)
        if q and q.concept not in weak_concepts:
        
            weak_concepts.append(q.concept)

target_focus = st.text_input(
    "Enter focus subjects or concepts for your study plan:",
    value=", ".join(weak_concepts) if weak_concepts else "Core Algorithms, Heuristics, Problem Solving"
)

if st.button("Generate Tailored Study Plan & Important Questions"):
    if not target_focus.strip():
        st.warning("Please specify focus concepts.")
    else:
        with st.spinner("Compiling custom study plan, important Q&A, and practice prompts using AI agent..."):
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are an expert AI academic mentor. Create a structured, comprehensive remedial study plan for a student focusing on the provided topics. Include: 1. Core Summary, 2. Three Important Questions with detailed Ideal Answers, and 3. Two Practice Exercises."),
                ("user", "Student Focus Concepts/Weak Areas: {focus}")
            ])
            
            chain = prompt | llm
            response = chain.invoke({"focus": target_focus})

            st.success("Study Plan Generated Successfully!")
            st.markdown("### 📋 Your Customized Study Roadmap")
            st.markdown(response.content)
