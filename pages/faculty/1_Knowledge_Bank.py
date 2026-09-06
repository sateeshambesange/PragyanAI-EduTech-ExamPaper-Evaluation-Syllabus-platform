import streamlit as st
from database import SessionLocal, KnowledgeRecord, save_document_vector

st.set_page_config(page_title="Knowledge Bank Ingestion", page_icon="📚", layout="wide")

if st.session_state.get("role") != "Faculty":
    st.error("Access Denied. Faculty members only.")
    st.stop()

st.title("📚 Faculty Knowledge Bank & Syllabus Ingestion")
st.markdown("Upload college department metadata, subject information, specialized topics, and comprehensive syllabus text to initialize your course repository and vector index.")

with st.form("knowledge_bank_form"):
    dept_info = st.text_input("Department Information", placeholder="e.g., Computer Science & Engineering")
    subject_info = st.text_input("Subject Information", placeholder="e.g., Artificial Intelligence & Neural Networks")
    subject_topics = st.text_area("Subject Key Topics (Comma separated)", placeholder="e.g., Heuristic Search, A* Algorithm, Propositional Logic, Neural Layers")
    syllabus_text = st.text_area("Upload / Paste Full Syllabus Text", placeholder="Module 1: Search algorithms...\nModule 2: Knowledge representation...")
    
    submitted = st.form_submit_button("Ingest Knowledge Base & Vectorize")
    
    if submitted:
        if not dept_info.strip() or not subject_info.strip() or not syllabus_text.strip():
            st.warning("Please fill in all mandatory fields (Department, Subject, Syllabus).")
        else:
            db = SessionLocal()
            record = KnowledgeRecord(
                faculty_username=st.session_state.get("username", "faculty1"),
                dept_info=dept_info,
                subject_info=subject_info,
                subject_topics=subject_topics,
                syllabus_text=syllabus_text
            )
            db.add(record)
            db.commit()
            db.close()
            
            # Index document into ChromaDB Vector Store
            save_document_vector(
                syllabus_text, 
                {
                    "faculty": st.session_state.get("username", "faculty1"),
                    "department": dept_info,
                    "subject": subject_info,
                    "type": "syllabus"
                }
            )
            
            st.success("Knowledge Bank successfully ingested into relational database and vectorized for RAG retrieval!")
