import os
import streamlit as st
from database import SessionLocal, SubmissionRecord, QuestionBankItem, get_vector_store
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

st.set_page_config(page_title="Faculty Insights RAG Studio", page_icon="📈", layout="wide")

if st.session_state.get("role") != "Faculty":
    st.error("Access Denied. Faculty members only.")
    st.stop()

st.title("🧠 Faculty Insights & Performance RAG Studio")
st.markdown("Query student submission data, review practice gaps, and evaluate question paper alignment using conversational AI grounded in your course vector database.")

GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY", "your-groq-api-key"))
llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.3, api_key=GROQ_API_KEY)

db = SessionLocal()
submissions = db.query(SubmissionRecord).all()
questions = db.query(QuestionBankItem).all()
db.close()

col1, col2, col3 = st.columns(3)
col1.metric("Total Tracked Submissions", len(submissions))
col2.metric("Total Question Bank Items", len(questions))
avg_score = sum([s.score for s in submissions]) / len(submissions) if submissions else 0.0
col3.metric("Class Average Score", f"{round(avg_score, 2)}%")

st.divider()

st.subheader("💬 Ask Faculty Performance RAG Agent")
faculty_query = st.text_input(
    "Enter your query about student performance or paper alignment:",
    placeholder="e.g., Which concepts resulted in the lowest student scores across recent submissions?"
)

if st.button("Generate RAG Insights"):
    if not faculty_query.strip():
        st.warning("Please enter a valid question.")
    else:
        with st.spinner("Analyzing student performance records and vector data..."):
            vector_store = get_vector_store()
            docs = vector_store.similarity_search(faculty_query, k=3)
            retrieved_context = "\n".join([d.page_content for d in docs]) if docs else "No specific vector notes indexed yet."

            summary_context = f"Total Submissions: {len(submissions)}. Average Class Score: {avg_score}%."
            for sub in submissions[-5:]:
                summary_context += f"\n- Student: {sub.student_name}, Score: {sub.score}%, Feedback: {sub.feedback}"

            prompt_template = ChatPromptTemplate.from_messages([
                ("system", "You are an expert academic advisor and educational data analyst agent. Using the provided curriculum vector context and student submission feedback, give the faculty member precise, data-driven insights, highlight weak concept areas, and suggest actionable curriculum adjustments."),
                ("user", "Vector Context: {context}\n\nSubmission Summary: {summary}\n\nInstructor Query: {query}")
            ])
            
            chain = prompt_template | llm
            response = chain.invoke({
                "context": retrieved_context,
                "summary": summary_context,
                "query": faculty_query
            })

            st.success("Analysis Complete!")
            st.markdown("### 📊 AI-Generated Pedagogical Insights")
            st.markdown(response.content)

            with st.expander("🔍 View Raw Vector & Submission Context Retrieved"):
                st.write("**Vector Context:**")
                st.text(retrieved_context)
                st.write("**Submission Overview:**")
                st.text(summary_context)
