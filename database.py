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
    bio_or_topics = Column(Text, default="")

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
    paper_type = Column(String)
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
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # 1. Seed Users
        sample_users = [
            UserModel(username="admin", password="adminpassword", role="PragyanAI Admin", full_name="PragyanAI System Admin", department="Platform Administration", bio_or_topics="Global system management."),
            UserModel(username="faculty1", password="password123", role="Faculty", full_name="Dr. Alan Turing", department="Computer Science & Engineering", bio_or_topics="Artificial Intelligence, Machine Learning"),
            UserModel(username="faculty2", password="password123", role="Faculty", full_name="Dr. Grace Hopper", department="Information Technology", bio_or_topics="Cloud Computing, Distributed Systems"),
            UserModel(username="student1", password="password123", role="Student", full_name="Ada Lovelace", department="Computer Science & Engineering", bio_or_topics="CS Semester 4"),
            UserModel(username="student2", password="password123", role="Student", full_name="Linus Torvalds", department="Computer Science & Engineering", bio_or_topics="CS Semester 6")
        ]
        for user in sample_users:
            if not db.query(UserModel).filter(UserModel.username == user.username).first():
                db.add(user)

        # 2. Seed the 4 Detailed Course Syllabi
        sample_courses = [
            KnowledgeRecord(
                faculty_username="faculty1",
                dept_info="Department of Computer Science & Engineering (Pragyan Institute of Technology)",
                subject_info="CS301: Artificial Intelligence & Machine Learning",
                subject_topics="Uninformed Search, Informed Search, Propositional Logic, Supervised ML, Unsupervised Learning, Neural Networks, Deep Learning",
                syllabus_text="""Module 1: Foundations of AI & Uninformed/Informed Search
- History and scope of AI, Turing test, intelligent agents.
- Uninformed search strategies: BFS, DFS, Uniform Cost Search.
- Informed search strategies: Greedy Best-First Search, A* search, heuristic functions, admissibility.
- Adversarial search: Minimax algorithm, Alpha-Beta pruning.

Module 2: Knowledge Representation, Logic & Planning
- Propositional logic, inference, first-order predicate logic.
- Knowledge representation using rules, semantic networks, and frames.
- Ontologies and probabilistic reasoning (Bayesian networks).
- Classical planning: STRIPS, forward and backward state-space search.

Module 3: Supervised Machine Learning
- Introduction to machine learning pipeline, data preprocessing, feature scaling.
- Linear regression, multiple regression, polynomial regression.
- Classification algorithms: Logistic regression, KNN, SVM.
- Decision trees, random forests, ensemble methods (bagging, boosting).

Module 4: Unsupervised Learning & Neural Networks
- Clustering techniques: K-Means, hierarchical clustering, DBSCAN.
- Dimensionality reduction: PCA and t-SNE.
- Artificial Neural Networks (ANN): Perceptrons, activation functions, backpropagation.
- Optimization techniques: Gradient descent variants (SGD, Adam) and regularization.

Module 5: Deep Learning & Modern Applications
- Convolutional Neural Networks (CNN) for computer vision.
- Recurrent Neural Networks (RNN), LSTMs, sequence-to-sequence models.
- Introduction to Transformers and Large Language Models (LLMs).
- Ethical considerations, bias in AI, and explainable AI (XAI)."""
            ),
            KnowledgeRecord(
                faculty_username="faculty1",
                dept_info="Department of Computer Science & Engineering (Pragyan Institute of Technology)",
                subject_info="CS202: Advanced Data Structures & Algorithms",
                subject_topics="Red-Black Trees, B-Trees, Graph Algorithms, String Matching, Dynamic Programming, NP-Completeness",
                syllabus_text="""Module 1: Advanced Trees & Heaps
- Red-Black Trees: Properties, rotations, insertion, deletion.
- B-Trees and B+ Trees: Operations and database indexing.
- Binomial Heaps and Fibonacci Heaps: Operations and amortized analysis.

Module 2: Advanced Graph Algorithms
- Graph representation and traversal optimizations.
- Minimum Spanning Trees: Kruskal’s and Prim’s algorithms.
- Shortest Path algorithms: Dijkstra, Bellman-Ford, Floyd-Warshall.
- Network flow: Ford-Fulkerson method, Edmonds-Karp algorithm.

Module 3: String Matching & Hashing
- Naive string matching, Rabin-Karp fingerprint algorithm.
- Knuth-Morris-Pratt (KMP) algorithm and Finite Automata.
- Boyer-Moore string search algorithm.
- Advanced Hashing: Universal hashing, perfect hashing, Bloom filters.

Module 4: Algorithmic Paradigm Design
- Greedy algorithms: Fractional knapsack, activity selection, Huffman coding.
- Divide and conquer: Strassen's matrix multiplication, closest pair of points.
- Dynamic programming: Matrix chain multiplication, optimal BST, subset sum.
- Backtracking and Branch-and-Bound (Traveling Salesperson, N-Queens).

Module 5: Intractability & Approximation
- Classes P, NP, NP-Complete, and NP-Hard.
- Polynomial-time reductions and classic NP-complete problems (SAT, Clique).
- Introduction to randomized algorithms and approximation algorithms."""
            ),
            KnowledgeRecord(
                faculty_username="faculty2",
                dept_info="Department of Information Technology (Pragyan Institute of Technology)",
                subject_info="IT405: Cloud Computing & Distributed Systems",
                subject_topics="RPC, Time Synchronization, Cloud Architecture, Virtualization, Kubernetes, Distributed Storage, NoSQL, DevOps",
                syllabus_text="""Module 1: Distributed Systems Fundamentals
- Characteristics of distributed systems, architectural models, inter-process communication.
- Remote Procedure Calls (RPC) and Remote Method Invocation (RMI).
- Time synchronization: Cristian's algorithm, NTP, Lamport logical clocks.
- Mutual exclusion and election algorithms (Bully and Ring algorithms).

Module 2: Cloud Computing Architecture & Models
- Evolution of cloud computing, deployment models (Public, Private, Hybrid).
- Service models: IaaS, PaaS, SaaS.
- Cloud reference architecture, elasticity, multi-tenancy, resource pooling.
- Economics of cloud computing, CAP theorem, eventual consistency.

Module 3: Virtualization & Containerization
- Hardware virtualization: Type 1 & 2 Hypervisors, VM migration.
- OS-level virtualization: Containers vs. Virtual Machines.
- Container orchestration with Docker and Kubernetes (Pods, Services).
- Serverless computing and FaaS models (AWS Lambda).

Module 4: Distributed Storage & Databases
- Distributed file systems: GFS and HDFS.
- NoSQL databases: Key-value, document, wide-column, graph stores (MongoDB, Cassandra).
- Distributed consensus: Paxos and Raft consensus algorithms.
- MapReduce processing model and stream processing.

Module 5: Cloud Security, DevOps & Management
- Cloud security challenges: IAM, encryption at rest and in transit.
- Compliance, data privacy, and multi-tenant isolation.
- DevOps practices: Infrastructure as Code (Terraform), CI/CD pipelines.
- Monitoring, logging, auto-scaling, disaster recovery."""
            ),
            KnowledgeRecord(
                faculty_username="faculty2",
                dept_info="Department of Cybersecurity & Defense (Pragyan Institute of Technology)",
                subject_info="CY310: Cyber Security & Ethical Hacking",
                subject_topics="CIA Triad, Reconnaissance, OSINT, OWASP Top 10, SQL Injection, XSS, System Hacking, Cryptography, PKI",
                syllabus_text="""Module 1: Information Security Foundations
- CIA Triad, threat modeling, and risk assessment.
- Access control models: DAC, MAC, RBAC.
- Legal and ethical frameworks, compliance standards (ISO 27001, GDPR, NIST).
- Phases in ethical hacking (Reconnaissance, Scanning, Gaining Access, Maintaining Access).

Module 2: Reconnaissance & Network Scanning
- Footprinting and OSINT gathering.
- Network scanning techniques: Port scanning (TCP SYN, UDP, FIN).
- Vulnerability assessment tools (Nessus, OpenVAS).
- Fingerprinting operating systems and services (Banner grabbing).

Module 3: Web Application Vulnerabilities (OWASP Top 10)
- Injection flaws (SQL Injection, Command Injection).
- Broken Authentication and Session Management.
- Cross-Site Scripting (XSS) and Cross-Site Request Forgery (CSRF).
- Insecure Direct Object References (IDOR), Security Misconfigurations.

Module 4: System Hacking & Malware Analysis
- Password cracking techniques (Brute-force, dictionary attacks, rainbow tables).
- Privilege escalation mechanisms in Windows and Linux.
- Types of malware: Trojans, viruses, worms, ransomware, rootkits.
- Static and dynamic malware analysis in a sandbox.

Module 5: Cryptography & Security Operations
- Symmetric vs. Asymmetric cryptography (AES, RSA, ECC).
- Hashing algorithms (SHA-256) and digital signatures.
- Public Key Infrastructure (PKI) and SSL/TLS certificate lifecycle.
- SOC, IDS/IPS, and Incident Response Playbooks."""
            )
        ]

        for course in sample_courses:
            existing = db.query(KnowledgeRecord).filter(KnowledgeRecord.subject_info == course.subject_info).first()
            if not existing:
                db.add(course)

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"DB init notice: {e}")
    finally:
        db.close()

VECTOR_DB_DIR = "./chroma_vector_store"
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def get_vector_store():
    return Chroma(persist_directory=VECTOR_DB_DIR, embedding_function=embeddings)

def save_document_vector(text: str, metadata: dict):
    store = get_vector_store()
    store.add_texts(texts=[text], metadatas=[metadata])
