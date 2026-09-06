import streamlit as st
from database import init_db, SessionLocal, UserModel, QuestionBankItem, ExamPaper, SubmissionRecord

st.set_page_config(page_title="EduPilot AI Enterprise Portal", page_icon="🎓", layout="wide")
init_db()

# Initialize Session State
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.session_state.full_name = ""

# --- 1. Authentication Screen ---
if not st.session_state.authenticated:
    st.title("🔐 EduPilot AI & PragyanAI Authentication Portal")
    role_choice = st.selectbox("Select Login Role", ["Faculty", "Student", "PragyanAI Admin"])
    
    with st.form("login_form"):
        username = st.text_input("Username", placeholder="e.g. admin, faculty1, student1")
        password = st.text_input("Password", type="password", placeholder="Enter password")
        submitted = st.form_submit_button("Sign In")

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
                st.success(f"Welcome, {user.full_name}!")
                st.rerun()
            else:
                st.error("Invalid credentials or mismatched role selection.")
    
    st.info("Default Logins: **admin** / **adminpassword** (Admin), **faculty1** / **password123** (Faculty), **student1** / **password123** (Student)")
    st.stop()

# --- 2. Profile Management & Sidebar Logout ---
st.sidebar.success(f"User: **{st.session_state.full_name}**\nRole: **{st.session_state.role}**")
if st.sidebar.button("Log Out"):
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.session_state.full_name = ""
    st.rerun()

with st.expander("✏️ My Profile & Preferences"):
    db = SessionLocal()
    current_user = db.query(UserModel).filter(UserModel.username == st.session_state.username).first()
    with st.form("profile_edit"):
        new_name = st.text_input("Full Name", value=current_user.full_name)
        new_dept = st.text_input("Department / Major", value=current_user.department)
        new_bio = st.text_area("Subject Expertise / Bio Topics", value=current_user.bio_or_topics)
        if st.form_submit_button("Save Profile Changes"):
            current_user.full_name = new_name
            current_user.department = new_dept
            current_user.bio_or_topics = new_bio
            db.commit()
            st.session_state.full_name = new_name
            st.success("Profile successfully updated!")
    db.close()

# --- 3. Role-Based Landing View ---
role = st.session_state.role

if role == "PragyanAI Admin":
    st.title("🛡️ PragyanAI System Admin Portal")
    st.markdown("Use the **sidebar menu** to access the Admin Dashboard, Manage Users, and review System Analytics.")
    
    db = SessionLocal()
    faculties = db.query(UserModel).filter(UserModel.role == "Faculty").all()
    students = db.query(UserModel).filter(UserModel.role == "Student").all()
    db.close()
    
    col1, col2 = st.columns(2)
    col1.metric("Total Registered Faculties", len(faculties))
    col2.metric("Total Enrolled Students", len(students))

elif role == "Faculty":
    st.title("👨‍🏫 Faculty Curriculum & Assessment Studio")
    st.markdown("""
    Welcome to your faculty workspace. Use the **sidebar navigation menu** to:
    1. Ingest Knowledge Banks & Syllabi (`1_Knowledge_Bank`)
    2. Extract Modules & Concepts (`2_Concept_Extraction`)
    3. Generate Question Banks (`3_Question_Generator`)
    4. Compile Exam Papers (`4_Paper_Creation`)
    5. Curate Ideal Answers (`6_Ideal_Answers`)
    6. Analyze Student Insights via RAG (`7_Faculty_Insights_RAG`)
    """)

elif role == "Student":
    st.title("🎓 Student Learning & Assessment Portal")
    st.markdown("""
    Welcome to your student workspace. Use the **sidebar navigation menu** to:
    1. Select and Take Exams (`4_Paper_Selection_and_Exams`)
    2. Practice & Evaluate Answers — Text, OCR, Voice (`5_Answer_Evaluation_Practice`)
    3. View Deep Analytics & Weak Areas (`7_Deep_Analytics`)
    4. Check Leaderboards (`8_Leaderboard`)
    5. Run Interactive RAG Diagnostics (`9_Interactive_RAG`)
    6. Generate Custom Study Plans (`10_Study_Plan`)
    """)
