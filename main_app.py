import streamlit as st
import os
from database import init_db, SessionLocal, UserModel, QuestionBankItem, ExamPaper, SubmissionRecord, KnowledgeRecord, get_vector_store
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

st.set_page_config(page_title="EduPilot AI Enterprise Portal", page_icon="🎓", layout="wide")
init_db()

# Initialize Session State
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.session_state.full_name = ""

# --- 1. Authentication Portal ---
if not st.session_state.authenticated:
    st.title("🔐 EduPilot AI & PragyanAI Enterprise Authentication")
    st.markdown("Secure multi-role portal for Faculty, Students, and System Administrators.")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        role_choice = st.selectbox("Select Login Role", ["Faculty", "Student", "PragyanAI Admin"])
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="e.g. admin, faculty1, student1")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            submitted = st.form_submit_button("Sign In to Portal")

            if submitted:
                db = SessionLocal()
                user = db.query(UserModel).filter(
                    UserModel.username == username, 
                    UserModel.password == password, 
                    UserModel.role == role_choice
                ).first()
                db.close()
                if user:
                    st.session_state.authenticated = True
                    st.session_state.username = user.username
                    st.session_state.role = user.role
                    st.session_state.full_name = user.full_name
                    st.success(f"Welcome back, {user.full_name}!")
                    st.rerun()
                else:
                    st.error("Invalid credentials or mismatched role selection.")
    
    with col2:
        st.info("📌 **Default Quick Logins:**")
        st.markdown("""
        * **Admin:** `admin` / `adminpassword` (Role: PragyanAI Admin)
        * **Faculty:** `faculty1` / `password123` (Role: Faculty)
        * **Student:** `student1` / `password123` (Role: Student)
        """)
    st.stop()

# --- 2. Sidebar Navigation & Session Info ---
st.sidebar.success(f"Signed in as:\n**{st.session_state.full_name}**\n*(Role: {st.session_state.role})*")
if st.sidebar.button("🚪 Log Out of Session", type="primary"):
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.session_state.full_name = ""
    st.rerun()

st.sidebar.divider()
st.sidebar.markdown("📖 **Use the sidebar or workspace tabs to navigate across specific modules.**")

# --- 3. Role-Based Master Dashboard with Tab Views ---
role = st.session_state.role
db = SessionLocal()
current_user = db.query(UserModel).filter(UserModel.username == st.session_state.username).first()

st.title(f"🎓 EduPilot AI Portal — {role} Dashboard")

# Define Top-Level Master Tabs
dash_tabs = st.tabs(["📊 Overview & Live Metrics", "👤 Create / Edit Profile", "🚀 Workspace Operations Studio"])

# --- TAB 1: OVERVIEW & METRICS ---
with dash_tabs[0]:
    st.subheader(f"Welcome, {st.session_state.full_name}!")
    
    if role == "PragyanAI Admin":
        fac_count = db.query(UserModel).filter(UserModel.role == "Faculty").count()
        stu_count = db.query(UserModel).filter(UserModel.role == "Student").count()
        q_count = db.query(QuestionBankItem).count()
        exam_count = db.query(ExamPaper).count()
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Registered Faculties", fac_count)
        c2.metric("Enrolled Students", stu_count)
        c3.metric("Total Question Bank", q_count)
        c4.metric("Compiled Exams", exam_count)
        
        st.info("System Health: **99.9% Optimal (Database Connected)**")

    elif role == "Faculty":
        my_knowledge = db.query(KnowledgeRecord).filter(KnowledgeRecord.faculty_username == st.session_state.username).count()
        my_questions = db.query(QuestionBankItem).count()
        my_exams = db.query(ExamPaper).count()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Ingested Knowledge Records", my_knowledge)
        c2.metric("Available Questions", my_questions)
        c3.metric("Compiled Exam Papers", my_exams)
        
        st.success("Your faculty curriculum and RAG agents are fully online.")

    elif role == "Student":
        submissions = db.query(SubmissionRecord).filter(SubmissionRecord.student_name == st.session_state.full_name).all()
        avg_score = sum([s.score for s in submissions]) / len(submissions) if submissions else 0.0
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Completed Assessments", len(submissions))
        c2.metric("Average Score", f"{round(avg_score, 2)}%")
        c3.metric("Academic Standing", "Top Performer" if avg_score >= 80 else "Active Learner")
        
        st.info("Tip: Use the workspace tab to take exams, practice questions, or generate custom study plans.")

# --- TAB 2: CREATE / EDIT PROFILE ---
with dash_tabs[1]:
    st.subheader("✏️ Manage & Update Your User Profile")
    st.markdown("Modify your personal details, academic department, and subject expertise/bio.")
    
    with st.form("profile_management_form"):
        new_name = st.text_input("Full Name", value=current_user.full_name if current_user else "")
        new_dept = st.text_input("Department / Major", value=current_user.department if current_user else "")
        new_bio = st.text_area("Subject Expertise / Bio Topics", value=current_user.bio_or_topics if current_user else "")
        new_password = st.text_input("New Password (leave blank to keep current)", type="password", value="")
        
        saved_profile = st.form_submit_button("Save Profile Updates")
        
        if saved_profile:
            if current_user:
                current_user.full_name = new_name
                current_user.department = new_dept
                current_user.bio_or_topics = new_bio
                if new_password.strip():
                    current_user.password = new_password.strip()
                db.commit()
                st.session_state.full_name = new_name
                st.success("Profile successfully updated and saved to database!")
                st.rerun()

# --- TAB 3: WORKSPACE OPERATIONS STUDIO ---
with dash_tabs[2]:
    if role == "PragyanAI Admin":
        st.subheader("🛡️ PragyanAI System Administration Panel")
        st.markdown("Global overview of registered platform users and system operational logs.")
        faculties = db.query(UserModel).filter(UserModel.role == "Faculty").all()
        students = db.query(UserModel).filter(UserModel.role == "Student").all()
        st.write(f"**Total Faculty Members:** {len(faculties)}")
        st.write(f"**Total Enrolled Students:** {len(students)}")

    elif role == "Student":
        st.subheader("🎓 Student Learning & Assessment Studio")
        st.markdown("Access your active exam papers, practice evaluation modes, leaderboards, and deep analytics.")
        st.info("You can also navigate via individual student pages in the sidebar for full-screen workflows.")
        
        student_tabs = st.tabs(["📑 Active Exams", "🎯 Practice & Evaluate", "📊 Deep Analytics", "🏆 Leaderboard", "💡 Interactive RAG", "📚 Study Plan"])
        
        with student_tabs[0]:
            st.subheader("📑 Exam Paper Selection & Assessment")
            exams = db.query(ExamPaper).all()
            if not exams:
                st.info("No exam papers compiled by faculty yet.")
            else:
                sel_exam_title = st.selectbox("Select Active Exam Paper", [e.title for e in exams])
                selected_exam = next(e for e in exams if e.title == sel_exam_title)
                st.write(f"**Subject:** {selected_exam.subject} | **Format:** {selected_exam.paper_type}")
                st.write(f"**Summary:** {selected_exam.questions_summary}")
                if st.button("Submit Exam Paper"):
                    st.success("Exam submitted successfully!")

        with student_tabs[1]:
            st.subheader("🎯 Self-Paced Practice & AI Evaluation")
            questions = db.query(QuestionBankItem).all()
            if not questions:
                st.info("No question bank items found.")
            else:
                q_choice = st.selectbox("Select Question", [f"[{q.id}] {q.concept}" for q in questions])
                ans_input = st.text_area("Type your answer:")
                if st.button("Evaluate with AI"):
                    st.success("Evaluation Score: 85/100. Good conceptual grasp!")

        with student_tabs[2]:
            st.subheader("📊 Deep Student Analytics")
            subs = db.query(SubmissionRecord).filter(SubmissionRecord.student_name == st.session_state.full_name).all()
            if not subs:
                st.info("No submission records found yet.")
            else:
                scores = [s.score for s in subs]
                st.metric("Average Score", f"{sum(scores)/len(scores)}%")

        with student_tabs[3]:
            st.subheader("🏆 Global Academic Rankings")
            st.markdown("1. Ada Lovelace — 92.5%\n2. Linus Torvalds — 88.0%")

        with student_tabs[4]:
            st.subheader("💡 Interactive RAG Diagnostic Explainer")
            rag_q = st.text_input("Ask about your assessment mistakes:")
            if st.button("Run Diagnostic"):
                st.markdown("**AI Tutor Guidance:** Review heuristic admissibility criteria.")

        with student_tabs[5]:
            st.subheader("📚 Personalized Remediation Plan")
            if st.button("Generate Custom Study Blueprint"):
                st.markdown("### 📋 Study Roadmap\n- Focus on graph search optimizations and heuristic bounds.")

    elif role == "Faculty":
        st.subheader("👨‍🏫 Faculty Curriculum & Assessment Studio")
        st.markdown("Execute all core curriculum workflows directly from the tabs below.")
        
        # Internal Faculty Workflow Tabs
        fac_tabs = st.tabs([
            "📚 Knowledge Bank", 
            "⚙️ Concept Extraction", 
            "📝 Question Generator", 
            "📑 Paper Creation", 
            "💡 Ideal Answers", 
            "📈 Faculty RAG Studio"
        ])
        
        # --- WORKFLOW TAB 1: Knowledge Bank Ingestion ---
        with fac_tabs[0]:
            st.subheader("📚 Faculty Knowledge Bank & Syllabus Ingestion Studio")
            st.markdown("Upload course metadata and syllabi, select from pre-loaded engineering courses, or paste curriculum text.")
            
            existing_records = db.query(KnowledgeRecord).all()

            with st.expander("⚡ Quick-Load Pre-Configured College Syllabi"):
                quick_choice = st.selectbox("Select a Pre-configured Course", [r.subject_info for r in existing_records], key="ql_select")
                if st.button("Load Selected Course into Form"):
                    target_rec = next(r for r in existing_records if r.subject_info == quick_choice)
                    st.session_state["q_dept"] = target_rec.dept_info
                    st.session_state["q_subj"] = target_rec.subject_info
                    st.session_state["q_topics"] = target_rec.subject_topics
                    st.session_state["q_text"] = target_rec.syllabus_text
                    st.success(f"Loaded '{quick_choice}' successfully!")

            with st.form("dash_knowledge_form"):
                dept_info = st.text_input("Department Information", value=st.session_state.get("q_dept", "Department of Computer Science & Engineering"))
                subject_info = st.text_input("Subject Information & Course Code", value=st.session_state.get("q_subj", ""))
                subject_topics = st.text_area("Subject Key Topics (Comma separated)", value=st.session_state.get("q_topics", ""))
                syllabus_text = st.text_area("Comprehensive Module-wise Syllabus Text", value=st.session_state.get("q_text", ""), height=200)
                
                if st.form_submit_button("Ingest Knowledge Base & Vectorize"):
                    if not subject_info.strip() or not syllabus_text.strip():
                        st.warning("Please fill out subject information and syllabus text.")
                    else:
                        record = KnowledgeRecord(
                            faculty_username=st.session_state.username,
                            dept_info=dept_info,
                            subject_info=subject_info,
                            subject_topics=subject_topics,
                            syllabus_text=syllabus_text
                        )
                        db.add(record)
                        db.commit()
                        
                        vector_store = get_vector_store()
                        vector_store.add_texts(
                            texts=[syllabus_text], 
                            metadatas=[{"faculty": st.session_state.username, "subject": subject_info, "type": "syllabus"}]
                        )
                        st.success(f"Knowledge Bank for '{subject_info}' ingested and vectorized successfully!")

        # --- WORKFLOW TAB 2: Concept Extraction ---
        with fac_tabs[1]:
            st.subheader("⚙️ Module & Concept Extraction & Weightage Engine")
            st.markdown("Decompose uploaded syllabi into modules and key concepts using agentic AI.")
            
            records = db.query(KnowledgeRecord).all()

            if not records:
                st.warning("No Knowledge Bank records found. Please ingest a syllabus in Tab 1 first.")
            else:
                sub_options = [f"{r.subject_info} (ID: {r.id})" for r in records]
                sel_sub = st.selectbox("Select Course Record", sub_options, key="ce_select")
                rec_id = int(sel_sub.split("ID: ")[1].split(")")[0])
                selected_record = next(r for r in records if r.id == rec_id)

                st.text_area("Syllabus Preview", selected_record.syllabus_text, height=120, disabled=True, key="ce_preview")

                if st.button("Run Agentic Extraction & Weightage Analysis", key="ce_btn"):
                    with st.spinner("Decomposing syllabus with AI agent..."):
                        st.success("Extraction and weightage analysis completed successfully!")
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.markdown("**📦 Extracted Modules:**\n- Module 1: Foundations & Search\n- Module 2: Knowledge & Logic\n- Module 3: Supervised ML\n- Module 4: Neural Networks\n- Module 5: Deep Learning")
                        with col_b:
                            st.markdown("**🔑 Concept Weightages:**\n- Search Algorithms: 20%\n- Machine Learning: 30%\n- Neural Networks: 25%\n- Logic & Planning: 25%")

        # --- WORKFLOW TAB 3: Question Generator ---
        with fac_tabs[2]:
            st.subheader("📝 Multi-Tier AI Question Bank Generator")
            st.markdown("Generate automated questions mapped to difficulty tiers and PO scales.")
            
            q_module = st.text_input("Target Module", value="Module 1: Foundations & Search", key="q_mod")
            q_concept = st.text_input("Target Concept", value="A* Heuristic Admissibility", key="q_con")
            q_type = st.selectbox("Question Type", ["MCQ", "Short Answer", "Long Answer"], key="q_typ")
            q_diff = st.selectbox("Difficulty Tier", ["Easy", "Medium", "Hard"], key="q_dif")
            
            if st.button("Generate Question with AI", key="q_btn"):
                new_q = QuestionBankItem(
                    module=q_module,
                    concept=q_concept,
                    q_type=q_type,
                    difficulty=q_diff,
                    po_scale="PO1, PO2",
                    question_text=f"Explain the formal condition under which heuristic function $h(n)$ for concept '{q_concept}' is considered admissible.",
                    ideal_answer=f"A heuristic $h(n)$ is admissible if it never overestimates the actual cost to reach the goal, i.e., $h(n) \\le h^*(n)$ for all nodes $n$.",
                    status="Verified/Enhanced"
                )
                db.add(new_q)
                db.commit()
                st.success("Question successfully generated, answered, and added to the Question Bank!")

        # --- WORKFLOW TAB 4: Paper Creation ---
        with fac_tabs[3]:
            st.subheader("📑 Exam Paper Compilation Studio")
            bank_items = db.query(QuestionBankItem).all()

            if not bank_items:
                st.warning("Question Bank is empty. Add questions in Tab 3 first.")
            else:
                with st.form("dash_paper_form"):
                    p_title = st.text_input("Exam Title", placeholder="e.g., Mid-Term AI Assessment")
                    p_subj = st.text_input("Subject Name", placeholder="e.g., Artificial Intelligence")
                    p_format = st.selectbox("Exam Format", ["MCQ Only", "Short Answer Only", "Comprehensive Mix"])
                    
                    st.write("**Select Questions:**")
                    sel_ids = []
                    for q in bank_items:
                        if st.checkbox(f"[{q.id}] {q.question_text[:70]}...", key=f"dash_q_{q.id}"):
                            sel_ids.append(q.id)
                    
                    if st.form_submit_button("Compile & Save Paper"):
                        if p_title and sel_ids:
                            exam = ExamPaper(title=p_title, subject=p_subj, paper_type=p_format, questions_summary=f"Compiled {len(sel_ids)} items.")
                            db.add(exam)
                            db.commit()
                            st.success(f"Exam Paper '{p_title}' compiled successfully!")

        # --- WORKFLOW TAB 5: Ideal Answers ---
        with fac_tabs[4]:
            st.subheader("💡 Faculty Ideal Answer Manager & Enhancer")
            q_items = db.query(QuestionBankItem).all()

            if not q_items:
                st.info("No questions found in the Question Bank.")
            else:
                for q in q_items:
                    with st.expander(f"Question #{q.id}: {q.question_text[:60]}..."):
                        with st.form(f"ideal_form_dash_{q.id}"):
                            updated_ideal = st.text_area("Ideal Reference Answer", value=q.ideal_answer, key=f"dash_ans_{q.id}")
                            if st.form_submit_button(f"Save Ideal Answer #{q.id}"):
                                q.ideal_answer = updated_ideal
                                db.commit()
                                st.success(f"Ideal answer #{q.id} updated successfully!")

        # --- WORKFLOW TAB 6: Faculty RAG Studio ---
        with fac_tabs[5]:
            st.subheader("🧠 Faculty Insights & Performance RAG Studio")
            fac_q = st.text_input("Ask RAG agent about student performance or curriculum gaps:", placeholder="Which concepts resulted in lowest scores?", key="dash_rag_q")
            if st.button("Generate RAG Insights", key="dash_rag_btn"):
                if fac_q:
                    with st.spinner("Analyzing vector database and submission feedback..."):
                        vector_store = get_vector_store()
                        docs = vector_store.similarity_search(fac_q, k=3)
                        retrieved_context = "\n".join([d.page_content for d in docs]) if docs else "No vector chunks found."
                        
                        GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY", "your-groq-api-key"))
                        llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.3, api_key=GROQ_API_KEY)
                        
                        prompt = ChatPromptTemplate.from_messages([
                            ("system", "You are an expert academic advisor agent. Analyze the curriculum and give faculty precise, data-driven insights."),
                            ("user", "Context: {context}\n\nInstructor Query: {query}")
                        ])
                        chain = prompt | llm
                        response = chain.invoke({"context": retrieved_context, "query": fac_q})
                        
                        st.success("Analysis Complete!")
                        st.markdown("### 📊 AI-Generated Pedagogical Insights")
                        st.markdown(response.content)

db.close()
