import os
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

DB_URL = "sqlite:///edupilot_enterprise.db"
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 1. Relational Database Tables ---

class UserModel(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String)  # "Faculty", "Student", "PragyanAI Admin"
    full_name = Column(String, default="")
    college = Column(String, default="Pragyan Institute of Technology, Bengaluru")
    department = Column(String, default="")
    bio_or_topics = Column(Text, default="")

class KnowledgeRecord(Base):
    __tablename__ = "knowledge_records"
    id = Column(Integer, primary_key=True, index=True)
    faculty_username = Column(String)
    college_info = Column(String)
    dept_info = Column(String)
    subject_info = Column(String)
    subject_topics = Column(Text)
    syllabus_text = Column(Text)
    
    modules = relationship("SyllabusModuleModel", back_populates="knowledge_record", cascade="all, delete-orphan")

class SyllabusModuleModel(Base):
    __tablename__ = "syllabus_modules"
    id = Column(Integer, primary_key=True, index=True)
    knowledge_record_id = Column(Integer, ForeignKey("knowledge_records.id"))
    module_code = Column(String)
    module_title = Column(String)
    module_weight = Column(Float, default=20.0)
    
    knowledge_record = relationship("KnowledgeRecord", back_populates="modules")
    topics = relationship("SyllabusTopicModel", back_populates="module", cascade="all, delete-orphan")

class SyllabusTopicModel(Base):
    __tablename__ = "syllabus_topics"
    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey("syllabus_modules.id"))
    topic_name = Column(String)
    topic_weight = Column(Float, default=5.0)

    module = relationship("SyllabusModuleModel", back_populates="topics")

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


# --- 2. Database Initialization & Enterprise Seeding ---

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # 1. Seed System Admin
        if not db.query(UserModel).filter(UserModel.username == "admin").first():
            db.add(UserModel(username="admin", password="adminpassword", role="PragyanAI Admin", full_name="Sateesh Ambesange (Founder & CEO)", department="Platform Administration", bio_or_topics="Global enterprise supervision."))

        # 2. Seed 25+ Faculty Members across Multiple Departments & Colleges
        faculties = [
            ("faculty1", "password123", "Dr. Alan Turing", "Department of Computer Science & Engineering", "Pragyan Institute of Technology, Bengaluru", "AI & Machine Learning"),
            ("faculty2", "password123", "Dr. Grace Hopper", "Department of Information Technology", "Pragyan Institute of Technology, Bengaluru", "Cloud Computing & Distributed Systems"),
            ("faculty3", "password123", "Dr. John von Neumann", "Department of Artificial Intelligence & Data Science", "Pragyan Institute of Technology, Bengaluru", "Deep Learning & LLMs"),
            ("faculty4", "password123", "Dr. Margaret Hamilton", "Department of Computer Science & Engineering", "Karnataka School of Engineering, Mysuru", "Software Architecture & Embedded Systems"),
            ("faculty5", "password123", "Dr. Donald Knuth", "Department of Information Technology", "Karnataka School of Engineering, Mysuru", "Advanced Data Structures & Algorithms"),
            ("faculty6", "password123", "Dr. Claude Shannon", "Department of Electronics & Communication Engineering", "Pragyan Institute of Technology, Bengaluru", "Digital Signal Processing & Information Theory"),
            ("faculty7", "password123", "Dr. Barbara Liskov", "Department of Computer Science & Engineering", "Silicon Valley Tech University, Hubli", "Distributed Systems & Object-Oriented Design"),
            ("faculty8", "password123", "Dr. Vint Cerf", "Department of Cybersecurity & Defense", "Pragyan Institute of Technology, Bengaluru", "Cyber Security & Network Protocols"),
            ("faculty9", "password123", "Dr. Tim Berners-Lee", "Department of Information Technology", "Silicon Valley Tech University, Hubli", "Web Engineering & Semantic Web"),
            ("faculty10", "password123", "Dr. Hedy Lamarr", "Department of Electronics & Communication Engineering", "Karnataka School of Engineering, Mysuru", "Wireless Communications & VLSI")
        ]

        for uname, pwd, fname, dept, college, bio in faculties:
            if not db.query(UserModel).filter(UserModel.username == uname).first():
                db.add(UserModel(username=uname, password=pwd, role="Faculty", full_name=fname, department=dept, college=college, bio_or_topics=bio))

        # 3. Seed Sample Students (Representing 1,000+ enrolled students across departments)
        students = [
            ("student1", "password123", "Ada Lovelace", "Department of Computer Science & Engineering", "Pragyan Institute of Technology, Bengaluru"),
            ("student2", "password123", "Linus Torvalds", "Department of Computer Science & Engineering", "Pragyan Institute of Technology, Bengaluru"),
            ("student3", "password123", "Radia Perlman", "Department of Information Technology", "Pragyan Institute of Technology, Bengaluru"),
            ("student4", "password123", "Guido van Rossum", "Department of Artificial Intelligence & Data Science", "Pragyan Institute of Technology, Bengaluru"),
            ("student5", "password123", "Satya Nadella", "Department of Cybersecurity & Defense", "Pragyan Institute of Technology, Bengaluru"),
            ("student6", "password123", "Sundar Pichai", "Department of Electronics & Communication Engineering", "Karnataka School of Engineering, Mysuru")
        ]

        for uname, pwd, fname, dept, college in students:
            if not db.query(UserModel).filter(UserModel.username == uname).first():
                db.add(UserModel(username=uname, password=pwd, role="Student", full_name=fname, department=dept, college=college, bio_or_topics="Semester 4 Enrolled Student"))

        # 4. Seed 10 Detailed Technical Subjects
        subjects_data = [
            ("faculty1", "Pragyan Institute of Technology, Bengaluru", "Department of Computer Science & Engineering", 
             "CS301: Artificial Intelligence & Machine Learning", 
             "Uninformed Search, Informed Search, Propositional Logic, Supervised ML, Unsupervised Learning, Neural Networks, Deep Learning",
             "Module 1: Foundations of AI & Search\n- History, Turing test, intelligent agents\n- BFS, DFS, Uniform Cost Search\n- A* search, heuristic functions, admissibility\n- Minimax & Alpha-Beta pruning\n\nModule 2: Knowledge & Logic\n- Propositional & predicate logic\n- Semantic networks & frames\n- Bayesian networks\n\nModule 3: Supervised ML\n- Regression & Polynomial fitting\n- Logistic regression, KNN, SVM\n- Decision Trees & Random Forests\n\nModule 4: Unsupervised & ANNs\n- K-Means, DBSCAN, PCA\n- Perceptrons & Backpropagation\n\nModule 5: Deep Learning\n- CNNs, RNNs, Transformers"),

            ("faculty2", "Pragyan Institute of Technology, Bengaluru", "Department of Information Technology", 
             "IT405: Cloud Computing & Distributed Systems", 
             "RPC, Time Synchronization, Cloud Architecture, Virtualization, Kubernetes, Distributed Storage, NoSQL, DevOps",
             "Module 1: Distributed Fundamentals\n- Architecture models, RPC, RMI\n- Clock drift, NTP, Lamport logical clocks\n\nModule 2: Cloud Architecture\n- Public, Private, Hybrid models\n- IaaS, PaaS, SaaS, CAP Theorem\n\nModule 3: Virtualization & Containers\n- Type 1 & 2 Hypervisors\n- Docker & Kubernetes orchestration\n\nModule 4: Distributed Storage\n- GFS, HDFS, NoSQL databases (MongoDB, Cassandra)\n- Paxos & Raft consensus\n\nModule 5: Cloud Security & DevOps\n- IAM, Terraform, CI/CD pipelines"),

            ("faculty3", "Pragyan Institute of Technology, Bengaluru", "Department of Artificial Intelligence & Data Science", 
             "AIDS501: Generative AI & Large Language Models", 
             "Transformers, Attention Mechanism, RAG, Fine-tuning, RLHF, Prompt Engineering, Agentic AI",
             "Module 1: Transformer Architecture\n- Self-attention, Multi-head attention, Positional encoding\n\nModule 2: Pre-training & Foundation Models\n- GPT, LLaMA, BERT architectures\n\nModule 3: RAG & Vector Databases\n- Chunking, Embeddings, ChromaDB, FAISS\n\nModule 4: Fine-Tuning & Alignment\n- LoRA, QLoRA, RLHF, DPO\n\nModule 5: Agentic AI Systems\n- LangChain, LlamaIndex, Multi-Agent Orchestration"),

            ("faculty5", "Karnataka School of Engineering, Mysuru", "Department of Information Technology", 
             "CS202: Advanced Data Structures & Algorithms", 
             "Red-Black Trees, B-Trees, Graph Algorithms, String Matching, Dynamic Programming, NP-Completeness",
             "Module 1: Advanced Trees\n- Red-Black trees, B-Trees, Fibonacci Heaps\n\nModule 2: Advanced Graph Algorithms\n- Kruskal, Prim, Dijkstra, Bellman-Ford, Max Flow\n\nModule 3: String Matching\n- KMP, Rabin-Karp, Boyer-Moore, Bloom Filters\n\nModule 4: Algorithmic Paradigms\n- Greedy, Divide & Conquer, Dynamic Programming\n\nModule 5: Intractability\n- P, NP, NP-Complete, NP-Hard, Approximations"),

            ("faculty8", "Pragyan Institute of Technology, Bengaluru", "Department of Cybersecurity & Defense", 
             "CY310: Cyber Security & Ethical Hacking", 
             "CIA Triad, Reconnaissance, OSINT, OWASP Top 10, SQL Injection, XSS, System Hacking, Cryptography",
             "Module 1: Sec Foundations\n- CIA Triad, Access controls, ISO 27001\n\nModule 2: Reconnaissance\n- Footprinting, Nmap scanning, Vulnerability assessment\n\nModule 3: Web Vulnerabilities\n- OWASP Top 10, SQLi, XSS, CSRF\n\nModule 4: System Hacking\n- Password cracking, Privilege escalation, Malware analysis\n\nModule 5: Cryptography\n- AES, RSA, PKI, SSL/TLS, SOC operations"),

            ("faculty6", "Pragyan Institute of Technology, Bengaluru", "Department of Electronics & Communication Engineering", 
             "ECE401: Digital Signal Processing & Computer Vision", 
             "Fourier Transforms, Digital Filters, Image Processing, Edge Detection, Feature Extraction, OpenCV",
             "Module 1: Signals & Systems\n- Discrete-time signals, Z-Transforms\n\nModule 2: Digital Filters\n- FIR and IIR filter design\n\nModule 3: Image Processing Basics\n- Grayscaling, histogram equalization, filtering\n\nModule 4: Edge Detection & Segmentation\n- Canny edge detector, Watershed segmentation\n\nModule 5: Computer Vision Applications\n- Object tracking, Face recognition, OpenCV pipelines"),

            ("faculty4", "Karnataka School of Engineering, Mysuru", "Department of Computer Science & Engineering", 
             "CSE403: Internet of Things & Embedded Systems", 
             "Microcontrollers, RTOS, MQTT, Sensor Networks, Edge Computing, IoT Security",
             "Module 1: Embedded Architectures\n- ARM Cortex, Microcontrollers, GPIO\n\nModule 2: Real-Time Operating Systems\n- Task scheduling, concurrency, semaphores\n\nModule 3: IoT Protocols\n- MQTT, CoAP, HTTP/REST for constrained devices\n\nModule 4: Sensor Interfacing\n- ADC, PWM, I2C, SPI communication protocols\n\nModule 5: Edge Computing & IoT Security\n- Local inference, device authentication, TLS for IoT"),

            ("faculty9", "Silicon Valley Tech University, Hubli", "Department of Information Technology", 
             "IT304: Big Data Analytics & NoSQL Databases", 
             "Hadoop, MapReduce, Spark, Kafka, Cassandra, Data Warehousing, ETL Pipelines",
             "Module 1: Big Data Ecosystem\n- 4 Vs of Big Data, Distributed processing\n\nModule 2: Hadoop & MapReduce\n- HDFS architecture, MapReduce paradigms\n\nModule 3: Apache Spark\n- RDDs, Spark SQL, Spark Streaming\n\nModule 4: NoSQL & Distributed DBs\n- Document stores, Wide-column stores (Cassandra)\n\nModule 5: Real-time Streaming\n- Kafka topics, event-driven architectures"),

            ("faculty7", "Silicon Valley Tech University, Hubli", "Department of Computer Science & Engineering", 
             "CSE502: Distributed Ledger & Blockchain Technology", 
             "Cryptographic Hash Functions, Consensus Mechanisms, Smart Contracts, Ethereum, Hyperledger",
             "Module 1: Cryptographic Foundations\n- SHA-256, public-key cryptography, digital signatures\n\nModule 2: Blockchain Architecture\n- Decentralization, consensus (PoW, PoS)\n\nModule 3: Smart Contracts\n- Solidity, EVM, deployment on testnets\n\nModule 4: Enterprise Blockchains\n- Hyperledger Fabric, permissioned ledgers\n\nModule 5: Web3 & Decentralized Apps\n- DApps, tokenomics, security audits"),

            ("faculty10", "Karnataka School of Engineering, Mysuru", "Department of Electronics & Communication Engineering", 
             "ECE302: VLSI Design & Microelectronics", 
             "MOSFETs, CMOS Inverters, Verilog HDL, FPGA Prototyping, Static Timing Analysis",
             "Module 1: MOS Transistor Theory\n- IV characteristics, threshold voltage, scaling\n\nModule 2: CMOS Logic Design\n- Inverter sizing, delay calculation, power dissipation\n\nModule 3: HDL & RTL Design\n- Verilog syntax, behavioral modeling, finite state machines\n\nModule 4: FPGA & ASIC Synthesis\n- Place and route, synthesis constraints\n\nModule 5: Testing & Verification\n- Fault models, ATPG, static timing analysis")
        ]

        for fac_uname, college, dept, subj_info, topics, syl_text in subjects_data:
            existing = db.query(KnowledgeRecord).filter(KnowledgeRecord.subject_info == subj_info).first()
            if not existing:
                rec = KnowledgeRecord(
                    faculty_username=fac_uname,
                    college_info=college,
                    dept_info=dept,
                    subject_info=subj_info,
                    subject_topics=topics,
                    syllabus_text=syl_text
                )
                db.add(rec)

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Enterprise DB init notice: {e}")
    finally:
        db.close()


# --- 3. CRUD Helpers & Hybrid RAG Retrieval ---

VECTOR_DB_DIR = "./chroma_vector_store"
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def get_vector_store():
    return Chroma(persist_directory=VECTOR_DB_DIR, embedding_function=embeddings)

def save_curriculum_hierarchy(knowledge_id: int, modules_data: dict, weights_data: dict, topics_data: dict):
    db = SessionLocal()
    try:
        db.query(SyllabusModuleModel).filter(SyllabusModuleModel.knowledge_record_id == knowledge_id).delete()
        
        for mod_key, mod_title in modules_data.items():
            mod_wt = float(weights_data.get(mod_key, 20.0))
            db_module = SyllabusModuleModel(
                knowledge_record_id=knowledge_id,
                module_code=mod_key,
                module_title=mod_title,
                module_weight=mod_wt
            )
            db.add(db_module)
            db.flush()
            
            sub_topics = topics_data.get(mod_key, {})
            for topic_name, topic_wt in sub_topics.items():
                db_topic = SyllabusTopicModel(
                    module_id=db_module.id,
                    topic_name=topic_name,
                    topic_weight=float(topic_wt)
                )
                db.add(db_topic)
                
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error saving curriculum hierarchy: {e}")
        return False
    finally:
        db.close()

def get_curriculum_hierarchy(knowledge_id: int):
    db = SessionLocal()
    try:
        modules = db.query(SyllabusModuleModel).filter(SyllabusModuleModel.knowledge_record_id == knowledge_id).all()
        result = {}
        for m in modules:
            topics_dict = {t.topic_name: t.topic_weight for t in m.topics}
            result[m.module_code] = {
                "title": m.module_title,
                "weight": m.module_weight,
                "topics": topics_dict
            }
        return result
    finally:
        db.close()

def hybrid_rag_llm_query(query: str, knowledge_id: int):
    structured_hierarchy = get_curriculum_hierarchy(knowledge_id)
    structured_context = "Structured Curriculum & Weight Distribution:\n"
    for m_code, data in structured_hierarchy.items():
        structured_context += f"- {m_code}: {data['title']} (Weight: {data['weight']}%)\n"
        for t_name, t_wt in data['topics'].items():
            structured_context += f"   * {t_name} [Weight: {t_wt}%]\n"

    vector_store = get_vector_store()
    docs = vector_store.similarity_search(query, k=3)
    semantic_context = "\n".join([d.page_content for d in docs]) if docs else "No vector chunks found."

    combined_context = f"=== SQL STRUCTURED DATA ===\n{structured_context}\n\n=== VECTOR SEMANTIC CHUNKS ===\n{semantic_context}"
    
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "your-groq-api-key")
    llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.3, api_key=GROQ_API_KEY)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert academic AI assistant. Answer the user's inquiry accurately by combining structured database records and semantic syllabus knowledge provided in the context."),
        ("user", "Context:\n{context}\n\nUser Query: {query}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({"context": combined_context, "query": query})
    return response.content
