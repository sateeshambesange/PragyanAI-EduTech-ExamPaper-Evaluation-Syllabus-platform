import streamlit as st
from database import SessionLocal, UserModel

st.set_page_config(page_title="Manage Users", page_icon="👥", layout="wide")

if st.session_state.get("role") != "PragyanAI Admin":
    st.error("Access Denied. Admins only.")
    st.stop()

st.title("👥 User Management Portal")
st.markdown("View, filter, edit, and manage all registered Faculty, Student, and Admin accounts.")

db = SessionLocal()
users = db.query(UserModel).all()

user_data = []
for u in users:
    user_data.append({
        "ID": u.id,
        "Username": u.username,
        "Full Name": u.full_name,
        "Role": u.role,
        "Department/Major": u.department
    })

st.table(user_data)

st.subheader("Edit or Reset User Record")
selected_username = st.selectbox("Select User to Edit", [u.username for u in users])

if selected_username:
    target_user = db.query(UserModel).filter(UserModel.username == selected_username).first()
    with st.form("edit_user_form"):
        new_name = st.text_input("Full Name", value=target_user.full_name)
        role_options = ["Faculty", "Student", "PragyanAI Admin"]
        current_role_index = role_options.index(target_user.role) if target_user.role in role_options else 0
        new_role = st.selectbox("Role", role_options, index=current_role_index)
        new_dept = st.text_input("Department/Major", value=target_user.department)
        new_password = st.text_input("New Password (leave blank or enter new)", type="password", value="")
        
        if st.form_submit_button("Save User Changes"):
            target_user.full_name = new_name
            target_user.role = new_role
            target_user.department = new_dept
            if new_password.strip():
                target_user.password = new_password.strip()
            db.commit()
            st.success(f"User @{selected_username} updated successfully!")
            st.rerun()

db.close()
