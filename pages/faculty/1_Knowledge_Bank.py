import streamlit as st
from database import SessionLocal, KnowledgeRecord, save_document_vector

st.set_page_config(page_title="Knowledge Bank Ingestion", page_icon="📚", layout="wide")

if st.session_state.get("role") != "Faculty":
    st.error("Access Denied. Faculty members only.")
    st.stop()

st.title("📚 Faculty Knowledge Bank & Syllabus Ingestion Studio")
st.markdown("Upload departmental course metadata and syllabi via file upload (.txt, .md), select from pre-loaded engineering courses, or paste curriculum text to initialize your vector store.")

# Quick Load Option for Pre-configured Detailed Courses
db = SessionLocal()
existing_records = db.query(KnowledgeRecord).all()
db.close()

with st.expander("⚡ Quick-Load Pre-Configured College Syllabi"):
    quick_choice = st.selectbox("Select a Pre-configured Course", [r.subject_info for r in existing_records])
    if st.button("Load Selected Course into Active Form"):
        target_rec = next(r for r in existing_records if r.subject_info == quick_choice)
        st.session_state["q_dept"] = target_rec.dept_info
        st.session_state["q_subj"] = target_rec.subject_info
        st.session_state["q_topics"] = target_rec.subject_topics
        st.session_state["q_text"] = target_rec.syllabus_text
        st.success(f"Loaded '{quick_choice}' successfully! Review below and click Ingest.")

st.divider()

# Syllabus File Upload and Form
with st.form("knowledge_bank_form"):
    st.subheader("📁 Upload Syllabus Document or Enter Details")
    
    uploaded_file = st.file_uploader("Upload Syllabus File (.txt, .md)", type=["txt", "md"])
    file_syllabus_text = ""
    if uploaded_file:
        file_syllabus_text = uploaded_file.read().decode("utf-8", errors="ignore")
        st.success("Syllabus file loaded successfully!")

    dept_info = st.text_input("Department Information", value=st.session_state.get("q_dept", "Department of Computer Science & Engineering"))
    subject_info = st.text_input("Subject Information & Course Code", value=st.session_state.get("q_subj", ""))
    subject_topics = st.text_area("Subject Key Topics (Comma separated)", value=st.session_state.get("q_topics", ""))
    
    default_text = file_syllabus_text if file_syllabus_text else st.session_state.get("q_text", "")
    syllabus_text = st.text_area("Comprehensive Module-wise Syllabus Text", value=default_text, height=250)
    
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
            
            st.success(f"Knowledge Bank for '{subject_info}' successfully ingested and vectorized for RAG retrieval!")
