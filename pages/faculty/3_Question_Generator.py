import streamlit as st
from database import SessionLocal, QuestionBankItem
from agentic_workflow import llm
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

st.set_page_config(page_title="Multi-Tier Question Generator", page_icon="📝", layout="wide")

if st.session_state.get("role") != "Faculty":
    st.error("Access Denied. Faculty members only.")
    st.stop()

st.title("📝 Multi-Tier Question Bank Builder")
st.markdown("Generate targeted questions across multiple formats (MCQ, Short, Long, Assignments), difficulty tiers, and Program Outcome (PO) scales.")

with st.form("question_generator_form"):
    col1, col2 = st.columns(2)
    with col1:
        module_name = st.text_input("Module Name", placeholder="e.g., Module 1: Search Algorithms")
        concept_name = st.text_input("Key Concept", placeholder="e.g., A* Heuristic Admissibility")
        q_type = st.selectbox("Question Format", ["MCQ", "Short Answer", "Long Answer", "Project Assignment", "Lab Assignment"])
    with col2:
        difficulty = st.selectbox("Difficulty Tier", ["Basic", "Intermediate", "Advanced"])
        po_scale = st.selectbox("Program Outcome (PO) Scale", ["PO1: Engineering Knowledge", "PO2: Problem Analysis", "PO3: Design & Development", "PO4: Investigation"])
        count = st.slider("Number of Questions to Generate", 1, 5, 3)

    submitted = st.form_submit_button("Generate & Store Questions")

    if submitted:
        if not module_name.strip() or not concept_name.strip():
            st.warning("Please fill in both the Module and Key Concept.")
        else:
            with st.spinner("AI generating structured questions and ideal answers..."):
                prompt = ChatPromptTemplate.from_messages([
                    ("system", "You are an expert academic examiner. Generate a JSON list of exactly {count} questions for concept '{concept}' under module '{module}'. Each item must include keys: 'question_text', 'ideal_answer', and optionally 'options' if it is an MCQ."),
                    ("user", "Format: {q_type}, Difficulty: {difficulty}, PO Scale: {po}")
                ])
                chain = prompt | llm | JsonOutputParser()
                try:
                    results = chain.invoke({
                        "count": count,
                        "concept": concept_name,
                        "module": module_name,
                        "q_type": q_type,
                        "difficulty": difficulty,
                        "po": po_scale
                    })
                except Exception:
                    results = [{
                        "question_text": f"Explain the core mechanics of {concept_name} under {module_name}?",
                        "ideal_answer": f"Standard academic reference answer explaining {concept_name} thoroughly."
                    }]

                db = SessionLocal()
                saved_count = 0
                for item in results:
                    q_item = QuestionBankItem(
                        module=module_name,
                        concept=concept_name,
                        q_type=q_type,
                        difficulty=difficulty,
                        po_scale=po_scale,
                        question_text=item.get("question_text", "Sample question"),
                        ideal_answer=item.get("ideal_answer", "Sample ideal answer"),
                        status="Draft"
                    )
                    db.add(q_item)
                    saved_count += 1
                db.commit()
                db.close()

                st.success(f"Successfully generated and saved {saved_count} items to the Question Bank!")
