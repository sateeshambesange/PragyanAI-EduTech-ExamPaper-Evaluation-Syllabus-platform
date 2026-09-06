import streamlit as st
from database import SessionLocal, KnowledgeRecord
from agentic_workflow import agent_app

st.set_page_config(page_title="Concept Extraction & Weightage", page_icon="⚙️", layout="wide")

if st.session_state.get("role") != "Faculty":
    st.error("Access Denied. Faculty members only.")
    st.stop()

st.title("⚙️ Module & Concept Extraction & Weightage Engine")
st.markdown("Automatically decompose your uploaded syllabus into modules and key concepts, and assign analytical weightages using agentic AI.")

db = SessionLocal()
records = db.query(KnowledgeRecord).all()
db.close()

if not records:
    st.warning("⚠️ **Prerequisite Missing:** No Knowledge Bank records found.")
    st.info("👉 **What to execute first:** Please go to **1_Knowledge_Bank** in the sidebar to upload or quick-load a course syllabus before running concept extraction.")
    st.stop()

subject_options = [f"{r.subject_info} (ID: {r.id})" for r in records]
selected_sub_str = st.selectbox("Select Course / Subject Record", subject_options)

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
            for m in result.get("modules", []):
                st.markdown(f"- {m}")
        with col2:
            st.subheader("🔑 Concept-wise Weightage (%)")
            for concept, weight in result.get("concept_weights", {}).items():
                st.metric(label=concept, value=f"{weight}%")
