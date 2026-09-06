import streamlit as st
from database import init_db, SessionLocal, UserModel, QuestionBankItem, ExamPaper, SubmissionRecord, KnowledgeRecord

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
    st.title("🔐 PragyanAI - EduPilot AI & PragyanAI Enterprise Authentication")
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
st.sidebar.markdown("📖 **Use the sidebar above to navigate across specific modules & tools.**")

# --- 3. Role-Based Master Dashboard with Tab Views ---
role = st.session_state.role
db = SessionLocal()
current_user = db.query(UserModel).filter(UserModel.username == st.session_state.username).first()

st.title(f"🎓 EduPilot AI Portal — {role} Dashboard")

# Define Tab View for the Dashboard
dash_tabs = st.tabs(["📊 Overview & Live Metrics", "👤 Create / Edit Profile", "🚀 Quick Operations Launchpad"])

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
        
        st.info("Tip: Use the sidebar to take exams, practice questions, or generate custom study plans.")

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

# --- TAB 3: QUICK OPERATIONS LAUNCHPAD ---
with dash_tabs[2]:
    st.subheader("🚀 Quick Action Launchpad")
    st.markdown("Jump directly into frequent workflows using the shortcuts below or via the sidebar menu.")
    
    if role == "PragyanAI Admin":
        st.markdown("""
        * 🛡️ **Admin Dashboard:** Monitor global statistics.
        * 👥 **Manage Users:** Edit user roles and passwords.
        * 📊 **System Analytics:** View platform audit logs.
        """)
    elif role == "Faculty":
        st.markdown("""
        * 📚 **Knowledge Bank:** Upload or quick-load syllabi.
        * ⚙️ **Concept Extraction:** Deconstruct modules with AI.
        * 📝 **Question Generator:** Build multi-tier question banks.
        * 📑 **Paper Creation:** Compile custom exam papers.
        * 💡 **Ideal Answers:** Review reference grading keys.
        * 📈 **Faculty RAG Studio:** Analyze student performance gaps.
        """)
    elif role == "Student":
        st.markdown("""
        * 📑 **Take Exam:** Complete faculty-compiled exam papers.
        * 🎯 **Practice & Evaluate:** Text, OCR, and voice submissions.
        * 📊 **Deep Analytics:** Review concept-wise proficiency.
        * 🏆 **Leaderboard:** Check global academic rankings.
        * 💡 **Interactive RAG:** Diagnostic AI tutor for mistakes.
        * 📚 **Study Plan:** Generate custom remedial blueprints.
        """)

db.close()
