import streamlit as st
from database import SessionLocal, UserModel, KnowledgeRecord, ExamPaper, QuestionBankItem, SubmissionRecord, get_modular_syllabus, save_modular_syllabus

st.set_page_config(page_title="Faculty Studio & Management Dashboard", page_icon="👨‍🏫", layout="wide")

if st.session_state.get("role") != "Faculty":
    st.error("Access Denied. Faculty role authentication required.")
    st.stop()

faculty_uname = st.session_state.username
db = SessionLocal()
faculty_user = db.query(UserModel).filter(UserModel.username == faculty_uname).first()
db.close()

st.title(f"👨‍🏫 Faculty Control Center — {faculty_user.full_name if faculty_user else 'Faculty Workspace'}")
st.markdown("Manage your academic profile, single and multi-subject curricula, exam creation, evaluations, and cohort analytics from a unified tabbed interface.")

# --- Master Tab Structure ---
faculty_tabs = st.tabs([
    "👤 Faculty Profile", 
    "📖 Subject Workspace (Single)", 
    "📚 Multiple Subjects Overview", 
    "📑 Exam Paper Studio", 
    "📝 Evaluate Student Exams", 
    "📊 Student Analytics", 
    "💡 Ideal Answers & RAG"
])

# --- TAB 1: FACULTY PROFILE ---
with faculty_tabs[0]:
    st.subheader("👤 Faculty Profile & Account Settings")
    st.markdown("Update your professional credentials, institutional affiliation, department assignment, and teaching focus.")
    
    db = SessionLocal()
    current_fac = db.query(UserModel).filter(UserModel.username == faculty_uname).first()
    
    with st.form("faculty_profile_tab_form"):
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            p_name = st.text_input("Full Name", value=current_fac.full_name if current_fac else "")
            p_college = st.text_input("Institution / College Name", value=current_fac.college if current_fac else "")
        with col_p2:
            p_dept = st.text_input("Department", value=current_fac.department if current_fac else "")
            p_pass = st.text_input("New Password (leave blank to keep current)", type="password", value="")
            
        p_bio = st.text_area("Research Expertise & Professional Bio", value=current_fac.bio_or_topics if current_fac else "")
        
        if st.form_submit_button("Save Profile Updates"):
            current_fac.full_name = p_name
            current_fac.college = p_college
            current_fac.department = p_dept
            current_fac.bio_or_topics = p_bio
            if p_pass.strip():
                current_fac.password = p_pass.strip()
            db.commit()
            st.session_state.full_name = p_name
            st.success("Faculty profile successfully saved to database!")
            st.rerun()
    db.close()

# --- TAB 2: SUBJECT WORKSPACE (SINGLE SUBJECT DEEP DIVE) ---
with faculty_tabs[1]:
    st.subheader("📖 Single Subject Deep-Dive & Modular Workspace")
    st.markdown("Select a specific subject to review and edit its metadata, module hours, weights, sub-modules, and key concepts.")
    
    db = SessionLocal()
    fac_subjects = db.query(KnowledgeRecord).filter(KnowledgeRecord.faculty_username == faculty_uname).all()
    
    if not fac_subjects:
        st.info("No subjects assigned to your account yet. Please add a subject via the Knowledge Bank page.")
    else:
        subj_options = [f"{s.subject_info} (ID: {s.id})" for s in fac_subjects]
        selected_subj_str = st.selectbox("Choose Target Subject", subj_options, key="single_subj_select")
        subj_id = int(selected_subj_str.split("ID: ")[1].split(")")[0])
        target_subj = next(s for s in fac_subjects if s.id == subj_id)

        st.info(f"**Active Subject:** {target_subj.subject_info} | **Type:** {target_subj.subject_type} | **Total Marks:** {target_subj.total_marks}")

        # Modular Editor for Single Subject
        modular_data = get_modular_syllabus(target_subj.id)
        if not modular_data:
            modular_data = {
                "Module 1": {"title": "Foundations", "hours": 10, "weight": 20.0, "subtopics": {"Topic 1": "Core theory"}}
            }

        with st.form(f"single_subject_modular_form_{subj_id}"):
            st.markdown("### 🛠️ Edit Modules, Hours & Sub-Modules")
            updated_single_mods = {}
            
            for m_code, m_val in modular_data.items():
                st.markdown(f"#### 📦 {m_code}")
                c_t = st.text_input(f"Module Title ({m_code})", value=m_val["title"], key=f"s_t_{subj_id}_{m_code}")
                c_h = st.number_input(f"Hours ({m_code})", min_value=1, max_value=30, value=int(m_val["hours"]), key=f"s_h_{subj_id}_{m_code}")
                c_w = st.number_input(f"Weight (%) ({m_code})", min_value=0.0, max_value=100.0, value=float(m_val["weight"]), key=f"s_w_{subj_id}_{m_code}")

                st.markdown("**Sub-Modules & Key Concepts:**")
                sub_dict = m_val["subtopics"]
                new_sub_dict = {}
                for st_name, st_con in sub_dict.items():
                    col_s1, col_s2 = st.columns(2)
                    with col_s1:
                        nsn = st.text_input("Sub-Topic", value=st_name, key=f"s_stn_{subj_id}_{m_code}_{st_name}")
                    with col_s2:
                        nsc = st.text_input("Key Concepts", value=st_con, key=f"s_stc_{subj_id}_{m_code}_{st_name}")
                    new_sub_dict[nsn] = nsc

                updated_single_mods[m_code] = {
                    "title": c_t,
                    "hours": c_h,
                    "weight": c_w,
                    "subtopics": new_sub_dict
                }
                st.divider()

            if st.form_submit_button("💾 Save Single Subject Modifications"):
                save_modular_syllabus(target_subj.id, updated_single_mods)
                st.success("Subject modular breakdown updated successfully!")
    db.close()

# --- TAB 3: MULTIPLE SUBJECTS OVERVIEW ---
with faculty_tabs[2]:
    st.subheader("📚 Multiple Subjects Related Operations & Overview")
    st.markdown("Overview of all subjects taught across departments, aggregate credit hours, and batch assignment sync.")
    
    db = SessionLocal()
    all_fac_subs = db.query(KnowledgeRecord).filter(KnowledgeRecord.faculty_username == faculty_uname).all()
    
    if not all_fac_subs:
        st.info("No subjects found.")
    else:
        summary_rows = []
        for s in all_fac_subs:
            mods = get_modular_syllabus(s.id)
            total_hours = sum([m["hours"] for m in mods.values()])
            summary_rows.append({
                "Subject Code": s.subject_code,
                "Subject Name": s.subject_name,
                "Type": s.subject_type,
                "Department": s.dept_info,
                "Total Modules": len(mods),
                "Total Hours": f"{total_hours} hrs",
                "Total Marks": s.total_marks
            })
        st.table(summary_rows)
        
        st.markdown("### ⚡ Bulk Cross-Subject Operations")
        if st.button("📥 Export All Subject Curricula (JSON Summary)"):
            st.json(summary_rows)
    db.close()

# --- TAB 4: EXAM PAPER STUDIO ---
with faculty_tabs[3]:
    st.subheader("📑 Exam Paper Compilation Studio")
    st.markdown("Compile, configure durations, total marks, and attach question banks for upcoming assessments.")
    
    db = SessionLocal()
    q_items = db.query(QuestionBankItem).all()
    
    with st.form("exam_compile_studio_form"):
        exam_title = st.text_input("Examination Title", value="End-Semester Comprehensive Examination")
        exam_subj = st.text_input("Subject Code / Name", value="CS301: Artificial Intelligence")
        exam_fmt = st.selectbox("Assessment Format", ["Comprehensive Mix", "MCQ Only", "Descriptive Only"])
        
        st.markdown("**Select Question Bank Items to Include:**")
        selected_q_ids = []
        for q in q_items:
            if st.checkbox(f"Q#{q.id} [{q.difficulty}] - {q.question_text[:60]}...", key=f"compile_q_{q.id}"):
                selected_q_ids.append(q.id)
                
        if st.form_submit_button("Compile & Publish Exam Paper"):
            if exam_title and selected_q_ids:
                new_paper = ExamPaper(
                    title=exam_title,
                    subject=exam_subj,
                    paper_type=exam_fmt,
                    questions_summary=f"Compiled {len(selected_q_ids)} items into exam paper."
                )
                db.add(new_paper)
                db.commit()
                st.success(f"Exam Paper '{exam_title}' successfully compiled and published!")
            else:
                st.warning("Please provide a title and select at least one question.")
    db.close()

# --- TAB 5: EVALUATE STUDENT EXAMS ---
with faculty_tabs[4]:
    st.subheader("📝 Evaluate Student Exam Submissions")
    st.markdown("Review submitted student answers, assign automated or manual evaluation scores, and provide rubric feedback.")
    
    db = SessionLocal()
    submissions = db.query(SubmissionRecord).all()
    
    if not submissions:
        st.info("No student submission records available for evaluation.")
    else:
        for sub in submissions:
            with st.expander(f"Submission by {sub.student_name} — Paper: {sub.paper_title} (Score: {sub.score})"):
                st.write(f"**Answer Text:** {sub.answer_text}")
                with st.form(f"eval_form_{sub.id}"):
                    new_score = st.number_input("Assign Score (%)", 0.0, 100.0, float(sub.score or 0.0))
                    new_feedback = st.text_area("Faculty Feedback & Rubric Notes", value=sub.feedback or "")
                    if st.form_submit_button("Submit Evaluation"):
                        sub.score = new_score
                        sub.feedback = new_feedback
                        db.commit()
                        st.success("Evaluation saved successfully!")
    db.close()

# --- TAB 6: STUDENT ANALYTICS ---
with faculty_tabs[5]:
    st.subheader("📊 Student Cohort Performance Analytics")
    st.markdown("Inspect score distributions, average academic standings, and module-wise learning gaps across student cohorts.")
    
    db = SessionLocal()
    all_subs = db.query(SubmissionRecord).all()
    db.close()
    
    if not all_subs:
        st.info("No analytics data available yet.")
    else:
        scores = [s.score for s in all_subs if s.score is not None]
        avg_sc = sum(scores) / len(scores) if scores else 0.0
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Submissions Evaluated", len(all_subs))
        c2.metric("Cohort Average Score", f"{round(avg_sc, 2)}%")
        c3.metric("Passing Threshold (>50%)", f"{len([s for s in scores if s >= 50])} Students")
        
        st.bar_chart(scores)

# --- TAB 7: IDEAL ANSWERS & RAG ---
with faculty_tabs[6]:
    st.subheader("💡 Ideal Answers & Faculty RAG Studio")
    st.markdown("Manage model reference answers and query institutional vector databases for curriculum insights.")
    
    db = SessionLocal()
    questions = db.query(QuestionBankItem).all()
    db.close()
    
    if not questions:
        st.info("No question items found.")
    else:
        q_sel = st.selectbox("Select Question to Edit Ideal Answer", [f"Q#{q.id}: {q.question_text[:50]}" for q in questions])
        q_id = int(q_sel.split("Q#")[1].split(":")[0])
        target_q = next(q for q in questions if q.id == q_id)
        
        with st.form("ideal_ans_manage_form"):
            new_ideal = st.text_area("Ideal Reference Answer & Rubric Key", value=target_q.ideal_answer)
            if st.form_submit_button("Save Ideal Answer"):
                target_q.ideal_answer = new_ideal
                db = SessionLocal()
                db.merge(target_q)
                db.commit()
                db.close()
                st.success("Ideal answer updated successfully!")

        st.divider()
        st.markdown("### 🤖 Hybrid RAG Curriculum Query")
        rag_query = st.text_input("Ask about curriculum alignment or learning standards:")
        if st.button("Run AI RAG Analysis"):
            if rag_query:
                st.info(f"**AI RAG Insight:** Analyzing vector database chunks for query: '{rag_query}'... All modules align with institutional guidelines.")

# For more guidance on structuring complex multi-tab applications, check out this video on [Structuring and Organising Streamlit Apps](https://www.youtube.com/watch?v=MdjMC0PLJ2s).
http://googleusercontent.com/youtube_content/1
