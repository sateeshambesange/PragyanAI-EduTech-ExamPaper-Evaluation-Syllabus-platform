import streamlit as st
from database import SessionLocal, SubmissionRecord, QuestionBankItem

st.set_page_config(page_title="Deep Analytics & Recommendations", page_icon="📊", layout="wide")

if not st.session_state.get("authenticated"):
    st.error("Please log in first.")
    st.stop()

st.title("📊 Deep Student Analytics & Personalized Recommendations")
st.markdown("Analyze your historical assessment performance, concept-wise proficiency, and AI-driven study recommendations.")

db = SessionLocal()
submissions = db.query(SubmissionRecord).all()
questions = {q.id: q for q in db.query(QuestionBankItem).all()}
db.close()

role = st.session_state.get("role")
username = st.session_state.get("full_name", "Ada Lovelace")

if role == "Student":
    user_subs = [s for s in submissions if s.student_name == username]
else:
    user_subs = submissions

if not user_subs:
    st.info("No submission performance records found yet. Complete some practice questions or exams to generate analytics.")
else:
    scores = [s.score for s in user_subs]
    avg_score = sum(scores) / len(scores) if scores else 0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Submissions", len(user_subs))
    col2.metric("Average Score", f"{round(avg_score, 2)}%")
    col3.metric("Performance Status", "Excellent" if avg_score >= 80 else "Needs Improvement" if avg_score < 60 else "Good Standing")

    st.divider()

    st.subheader("📈 Concept-wise Proficiency Breakdown")
    concept_scores = {}
    for sub in user_subs:
        q = questions.get(sub.question_id)
        c_name = q.concept if q else "General Practice"
        if c_name not in concept_scores:
            concept_scores[c_name] = []
        concept_scores[c_name].append(sub.score)
    
    avg_concept_scores = {c: sum(sc)/len(sc) for c, sc in concept_scores.items()}
    st.bar_chart(avg_concept_scores)

    st.subheader("💡 AI Recommendations & Focus Areas")
    weak_concepts = [c for c, sc in avg_concept_scores.items() if sc < 75.0]
    if weak_concepts:
        st.warning(f"**Identified Weak Concepts Requiring Attention:** {', '.join(weak_concepts)}")
        st.markdown("""
        * **Action Plan:**
          1. Review syllabus sections corresponding to your weak concepts.
          2. Use the **Interactive RAG Studio** to ask diagnostic questions about where your answers fell short.
          3. Generate custom practice questions via the Practice Module.
        """)
    else:
        st.success("Great job! You are maintaining strong performance across all evaluated concepts.")

    st.subheader("📋 Detailed Submission History")
    history_data = []
    for s in user_subs:
        q = questions.get(s.question_id)
        history_data.append({
            "Paper/Session": s.paper_title,
            "Concept": q.concept if q else "N/A",
            "Score (%)": s.score,
            "Feedback": s.feedback
        })
    st.table(history_data)
