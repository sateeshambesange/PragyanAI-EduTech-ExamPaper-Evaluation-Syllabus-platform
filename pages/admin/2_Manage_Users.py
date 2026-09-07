import streamlit as st
from database import SessionLocal, UserModel

st.set_page_config(page_title="Manage Users", page_icon="👥", layout="wide")

if st.session_state.get("role") != "PragyanAI Admin":
    st.error("Access Denied. Admins only.")
    st.stop()

st.title("👥 Enterprise User Management Portal")
st.markdown("View, filter, edit, provision, and delete registered Faculty, Student, and Admin accounts directly from the database.")

db = SessionLocal()
users = db.query(UserModel).all()

# --- Display Comprehensive User Table ---
user_data = []
for u in users:
    user_data.append({
        "ID": u.id,
        "Username": u.username,
        "Full Name": u.full_name,
        "Role": u.role,
        "College": u.college,
        "Department/Major": u.department
    })

st.markdown("### 📋 Registered System Users (Live Database Records)")
st.table(user_data)

st.divider()

# --- Manage/Edit Existing User Record ---
st.markdown("### ✏️ Edit Existing User Record")
if not users:
    st.info("No users found in database.")
else:
    selected_username = st.selectbox("Select User to Edit", [u.username for u in users])

    if selected_username:
        target_user = db.query(UserModel).filter(UserModel.username == selected_username).first()
        if target_user:
            with st.form(f"edit_user_form_{target_user.id}"):
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    new_name = st.text_input("Full Name", value=target_user.full_name)
                    role_options = ["Faculty", "Student", "PragyanAI Admin"]
                    current_role_index = role_options.index(target_user.role) if target_user.role in role_options else 0
                    new_role = st.selectbox("Role", role_options, index=current_role_index)
                    new_college = st.text_input("College / Institution", value=target_user.college or "")
                with col_e2:
                    new_dept = st.text_input("Department / Major", value=target_user.department or "")
                    new_password = st.text_input("New Password (leave blank to keep current)", type="password", value="")
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    save_submitted = st.form_submit_button("💾 Save User Changes to DB")
                with col_btn2:
                    delete_submitted = st.form_submit_button("🗑️ Delete User Account")

                if save_submitted:
                    target_user.full_name = new_name
                    target_user.role = new_role
                    target_user.college = new_college
                    target_user.department = new_dept
                    if new_password.strip():
                        target_user.password = new_password.strip()
                    db.commit()
                    st.success(f"User @{selected_username} updated and committed to database successfully!")
                    st.rerun()

                if delete_submitted:
                    if target_user.username == "admin":
                        st.error("Cannot delete the core system administrator account.")
                    else:
                        db.delete(target_user)
                        db.commit()
                        st.success(f"User @{selected_username} successfully deleted from database!")
                        st.rerun()

st.divider()

# --- Provision New User Record ---
st.markdown("### ➕ Provision New Institutional User")
with st.form("provision_new_user_form"):
    col_n1, col_n2 = st.columns(2)
    with col_n1:
        prov_username = st.text_input("Username", placeholder="e.g. faculty11 or student101")
        prov_password = st.text_input("Password", type="password", placeholder="Secure password")
        prov_role = st.selectbox("Assign Role", ["Faculty", "Student", "PragyanAI Admin"], key="prov_role_select")
    with col_n2:
        prov_name = st.text_input("Full Name", placeholder="e.g. Dr. Ada Lovelace")
        prov_college = st.text_input("College / Institution", value="Pragyan Institute of Technology, Bengaluru")
        prov_dept = st.text_input("Department / Major", value="Department of Computer Science & Engineering")

    if st.form_submit_button("🚀 Add User to Database"):
        if not prov_username.strip() or not prov_password.strip():
            st.warning("Username and password cannot be empty.")
        else:
            existing_check = db.query(UserModel).filter(UserModel.username == prov_username.strip()).first()
            if existing_check:
                st.error(f"Username '@{prov_username}' already exists in the database.")
            else:
                new_db_user = UserModel(
                    username=prov_username.strip(),
                    password=prov_password.strip(),
                    role=prov_role,
                    full_name=prov_name.strip(),
                    college=prov_college.strip(),
                    department=prov_dept.strip()
                )
                db.add(new_db_user)
                db.commit()
                st.success(f"New user '@{prov_username}' successfully provisioned and written to database!")
                st.rerun()

db.close()
