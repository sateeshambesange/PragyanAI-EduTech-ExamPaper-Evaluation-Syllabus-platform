import streamlit as st
from database import SessionLocal, QuestionBankItem

st.set_page_config(page_title="Ideal Answers Manager", page_icon="💡", layout="wide")

if st.session_state.get("role") != "Faculty":
    st.error("Access Denied. Faculty members only.")
    st.stop()

st.title("💡 Faculty Ideal Answer Manager & Enhancer")
st.markdown("Review model-generated ideal reference answers, edit technical explanations, and enhance grading rubrics for questions stored in the question bank.")

db = SessionLocal()
questions = db.query(QuestionBankItem).all()
db.close()

if not questions:
    st.warning("No questions found in the Question Bank. Please generate questions using **3_Question_Generator.py** first.")
else:
    concept_filter = st.selectbox("Filter by Concept", ["All"] + list(set([q.concept for q in questions])))

    for q in questions:
        if concept_filter != "All" and q.concept != concept_filter:
            continue
        
        with st.expander(f"[{q.id}] {q.concept} ({q.q_type} — {q.difficulty})"):
            with st.form(f"ideal_form_{q.id}"):
                st.markdown(f"**Question Text:** {q.question_text}")
                updated_ideal = st.text_area("Ideal Reference Answer", value=q.ideal_answer, height=120)
                
                status_options = ["Draft", "Verified/Enhanced"]
                current_status_idx = status_options.index(q.status) if q.status in status_options else 0
                new_status = st.selectbox("Question Verification Status", status_options, index=current_status_idx)
                
                submitted = st.form_submit_button(f"Save & Enhance Ideal Answer #{q.id}")
                if submitted:
                    db = SessionLocal()
                    target_q = db.query(QuestionBankItem).filter(QuestionBankItem.id == q.id).first()
                    if target_q:
                        target_q.ideal_answer = updated_ideal
                        target_q.status = new_status
                        db.commit()
                        st.success(f"Ideal answer for Question #{q.id} updated successfully!")
                    db.close()
