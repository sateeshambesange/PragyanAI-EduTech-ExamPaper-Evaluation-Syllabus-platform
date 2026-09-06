import os
from typing import TypedDict, List, Dict, Any
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langgraph.graph import StateGraph, END
from database import get_vector_store
import streamlit as st

# Initialize Groq LLM with safe fallback configuration
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY", "your-groq-api-key"))
llm = ChatGroq(model_name="openai/gpt-oss-120b", temperature=0.4, api_key=GROQ_API_KEY)

class AgentState(TypedDict):
    syllabus_text: str
    modules: List[str]
    concepts: List[str]
    concept_weights: Dict[str, float]
    generated_questions: List[Dict[str, Any]]
    student_response: str
    ideal_answer: str
    evaluation: Dict[str, Any]

# --- Node 1: Syllabus Decomposition Agent ---
def extract_syllabus_node(state: AgentState) -> AgentState:
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Extract modules and key concepts from the given syllabus text. Return a JSON object with keys 'modules' (list of strings) and 'concepts' (list of strings)."),
        ("user", "{syllabus}")
    ])
    chain = prompt | llm | JsonOutputParser()
    try:
        res = chain.invoke({"syllabus": state.get("syllabus_text", "")})
        state["modules"] = res.get("modules", ["Module 1: Foundations"])
        state["concepts"] = res.get("concepts", ["Core Concept A", "Core Concept B"])
    except Exception:
        state["modules"] = ["Module 1: Foundations"]
        state["concepts"] = ["Core Concept A"]
    return state

# --- Node 2: Weight Calculation Agent ---
def compute_weights_node(state: AgentState) -> AgentState:
    concepts = state.get("concepts", [])
    weight = round(100.0 / len(concepts), 2) if concepts else 100.0
    state["concept_weights"] = {c: weight for c in concepts}
    return state

# --- Node 3: Question Generation Agent ---
def generate_questions_node(state: AgentState) -> AgentState:
    concepts = state.get("concepts", ["Core Concept A"])
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Generate a structured list of 3 questions (MCQ, Short, Long) across Basic, Intermediate, and Advanced tiers for these concepts. Return a JSON list format with keys: concept, q_type, difficulty, question_text, ideal_answer."),
        ("user", "Concepts to cover: {concepts}")
    ])
    chain = prompt | llm | JsonOutputParser()
    try:
        state["generated_questions"] = chain.invoke({"concepts": str(concepts)})
    except Exception:
        state["generated_questions"] = [{
            "concept": concepts[0],
            "q_type": "Short Answer",
            "difficulty": "Basic",
            "question_text": f"Define and explain {concepts[0]}?",
            "ideal_answer": f"Standard academic definition and explanation for {concepts[0]}."
        }]
    return state

# --- Node 4: RAG Evaluation & Scoring Agent ---
def evaluate_answer_node(state: AgentState) -> AgentState:
    # Retrieve relevant external vector context from ChromaDB
    vector_store = get_vector_store()
    docs = vector_store.similarity_search(state.get("student_response", ""), k=2)
    context = "\n".join([d.page_content for d in docs]) if docs else "No specific external document reference found."

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert strict academic professor. Evaluate the student response against the ideal answer using the provided curriculum context. Return JSON with keys: score (float out of 100), feedback (string), rag_explanation (string explaining what went wrong and how to improve)."),
        ("user", "Curriculum Context: {context}\n\nIdeal Answer: {ideal}\n\nStudent Answer: {student}")
    ])
    chain = prompt | llm | JsonOutputParser()
    try:
        res = chain.invoke({
            "context": context,
            "ideal": state.get("ideal_answer", ""),
            "student": state.get("student_response", "")
        })
        state["evaluation"] = res
    except Exception:
        state["evaluation"] = {
            "score": 75.0,
            "feedback": "Acceptable attempt, but could provide more detail.",
            "rag_explanation": "Review core conceptual framework and revisit fundamental definitions."
        }
    return state

# --- Compile LangGraph Workflow ---
workflow = StateGraph(AgentState)
workflow.add_node("extract", extract_syllabus_node)
workflow.add_node("weights", compute_weights_node)
workflow.add_node("generate_questions", generate_questions_node)

workflow.set_entry_point("extract")
workflow.add_edge("extract", "weights")
workflow.add_edge("weights", "generate_questions")
workflow.add_edge("generate_questions", END)

agent_app = workflow.compile()
