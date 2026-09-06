import streamlit as st
from database import SessionLocal, KnowledgeRecord
from agentic_workflow import agent_app

st.set_page_config(page_title="Concept Extraction & Weightage", page_icon="⚙️", layout="wide")

if st.session_state.get("role") != "Faculty":
    st.error("Access Denied. Faculty members only.")
    st.stop()

st.title("⚙️ Module & Concept Extraction & Weightage Engine")
st.markdown("Automatically decompose your uploaded syllabus into modules and key concepts, and assign analytical weightages using agentic AI.")

# Fetch stored syllabus records for the logged-in faculty
db = SessionLocal()
records = db.query(KnowledgeRecord).filter(KnowledgeRecord.faculty_username == st.session_state.get("username", "faculty1")).all()
db.close()

if not records:
    st.warning("No Knowledge Bank records found. Please complete **1_Knowledge_Bank.py** first.")
else:
    subject_options = [f"{r.subject_info} (ID: {r.id})" for r in records]
    selected_sub_str = st.selectbox("Select Course / Subject Record", subject_options)
    
    # Extract ID from selection string
    selected_id = int(selected_sub_str.split("ID: ")[1].split(")")[0])
    selected_record = next(r for r in records if r.id == selected_id)

    st.text_area("Loaded Syllabus Preview", selected_record.syllabus_text, height=150, disabled=True)

    if st.button("Run Agentic Extraction & Weightage Analysis"):
        with st.spinner("Executing LangGraph syllabus decomposition agent..."):
            initial_state = {"syllabus_text": selected_record.syllabus_text}
            result = agent_app.invoke(initial_state)
            
            st.success("Extraction and weightage analysis completed successfully!")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📦 Extracted Modules")
                modules = result.get("modules", [])
                for m in modules:
                    st.markdown(f"- {m}")
            
            with col2:
                st.subheader("🔑 Concept-wise Weightage (%)")
                weights = result.get("concept_weights", {})
                for concept, weight in weights.items():
                    st.metric(label=concept, value=f"{weight}%")
