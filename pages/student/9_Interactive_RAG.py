import os
import streamlit as st
from database import get_vector_store
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

st.set_page_config(page_title="Interactive RAG Explainer", page_icon="💡", layout="wide")

if st.session_state.get("role") != "Student":
    st.error("Access Denied. Student portal only.")
    st.stop()

st.title("💡 Interactive RAG Diagnostic Explainer")
st.markdown("Ask questions about your assessment mistakes, get personalized explanations on where your reasoning fell short, and learn how to improve.")

GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY", "your-groq-api-key"))
llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.3, api_key=GROQ_API_KEY)

student_query = st.text_input(
    "What concept or assessment feedback would you like to clarify?",
    placeholder="e.g., Why was my explanation of A* heuristic admissibility considered incomplete?"
)

if st.button("Run Diagnostic RAG Analysis"):
    if not student_query.strip():
        st.warning("Please enter a question or topic to analyze.")
    else:
        with st.spinner("Searching curriculum knowledge base and analyzing reasoning gaps..."):
            vector_store = get_vector_store()
            docs = vector_store.similarity_search(student_query, k=3)
            retrieved_context = "\n".join([d.page_content for d in docs]) if docs else "No specific course document chunk found."

            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are an expert, supportive AI academic tutor. Using the provided curriculum context, explain clearly to the student where their conceptual understanding went wrong, what key principles they missed, and provide a step-by-step guide on how to improve."),
                ("user", "Curriculum Context: {context}\n\nStudent Query / Mistake: {query}")
            ])
            
            chain = prompt | llm
            response = chain.invoke({
                "context": retrieved_context,
                "query": student_query
            })

            st.success("Analysis Complete!")
            st.markdown("### 🤖 AI Tutor RAG Remediation Guidance")
            st.markdown(response.content)

            with st.expander("🔍 View Retrieved Course Context"):
                st.text(retrieved_context)
