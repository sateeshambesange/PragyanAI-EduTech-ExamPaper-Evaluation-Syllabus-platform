import os
from sqlalchemy import create_engine, Column, Integer, String, Text, Float
from sqlalchemy.orm import declarative_base, sessionmaker
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

DB_URL = "sqlite:///edupilot_enterprise.db"
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class UserModel(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String) # "Faculty", "Student", "PragyanAI Admin"
    full_name = Column(String, default="")
    department = Column(String, default="")
    bio_or_topics = Column(Text, default="") # Subject topics for faculty / major for student

class KnowledgeRecord(Base):
    __tablename__ = "knowledge_records"
    id = Column(Integer, primary_key=True, index=True)
    faculty_username = Column(String)
    dept_info = Column(String)
    subject_info = Column(String)
    subject_topics = Column(Text)
    syllabus_text = Column(Text)

class QuestionBankItem(Base):
    __tablename__ = "question_bank"
    id = Column(Integer, primary_key=True, index=True)
    module = Column(String)
    concept = Column(String)
    q_type = Column(String) 
    difficulty = Column(String) 
    po_scale = Column(String)
    question_text = Column(Text)
    ideal_answer = Column(Text)
    status = Column(String, default="Draft")

class ExamPaper(Base):
    __tablename__ = "exam_papers"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    subject = Column(String)
    paper_type = Column(String) # MCQ, Short, Long, Mix
    questions_summary = Column(Text)

class SubmissionRecord(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True, index=True)
    student_name = Column(String)
    paper_title = Column(String)
    question_id = Column(Integer)
    answer_text = Column(Text)
    score = Column(Float)
    feedback = Column(Text)
    rag_explanation = Column(Text)

def init_db():
    # Create tables safely if they don't exist
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Comprehensive sample users and rich profiles
        sample_users = [
            UserModel(
                username="admin", 
                password="adminpassword", 
                role="PragyanAI Admin", 
                full_name="PragyanAI System Admin",
                department="Platform Administration",
                bio_or_topics="Global system management, role governance, and audit logging."
            ),
            UserModel(
                username="faculty1", 
                password="password123", 
                role="Faculty", 
                full_name="Dr. Alan Turing", 
                department="Computer Science & Engineering", 
                bio_or_topics="Artificial Intelligence, Machine Learning, Heuristic Search, Neural Networks"
            ),
            UserModel(
                username="faculty2", 
                password="password123", 
                role="Faculty", 
                full_name="Dr. Grace Hopper", 
                department="Information Technology", 
                bio_or_topics="Software Architecture, Data Structures, Compilers"
            ),
            UserModel(
                username="student1", 
                password="password123", 
                role="Student", 
                full_name="Ada Lovelace", 
                department="Computer Science & Engineering", 
                bio_or_topics="Computer Science Semester 4 — Focused on AI & Algorithms"
            ),
            UserModel(
                username="student2", 
                password="password123", 
                role="Student", 
                full_name="Linus Torvalds", 
                department="Computer Science & Engineering", 
                bio_or_topics="Computer Science Semester 6 — Focused on Systems & Networks"
            )
        ]

        for user in sample_users:
            existing_user = db.query(UserModel).filter(UserModel.username == user.username).first()
            if not existing_user:
                db.add(user)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Database initialization notice: {e}")
    finally:
        db.close()

VECTOR_DB_DIR = "./chroma_vector_store"
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def get_vector_store():
    return Chroma(persist_directory=VECTOR_DB_DIR, embedding_function=embeddings)

def save_document_vector(text: str, metadata: dict):
    store = get_vector_store()
    store.add_texts(texts=[text], metadatas=[metadata])
