import streamlit as st
from database import SessionLocal, SubmissionRecord

st.set_page_config(page_title="Student Leaderboard", page_icon="🏆", layout="wide")

if not st.session_state.get("authenticated"):
    st.error("Please log in first.")
    st.stop()

st.title("🏆 Student Ranking Leaderboard")
st.markdown("Track student performance, assessment completion rates, and global academic rankings across the portal.")

db = SessionLocal()
submissions = db.query(SubmissionRecord).all()
db.close()

if not submissions:
    st.info("No submission records found to build the leaderboard yet. Complete exams or practice submissions to rank up!")
else:
    # Aggregate scores per student
    student_stats = {}
    for sub in submissions:
        name = sub.student_name
        if name not in student_stats:
            student_stats[name] = {"total_score": 0.0, "count": 0}
        student_stats[name]["total_score"] += sub.score
        student_stats[name]["count"] += 1

    leaderboard_data = []
    for name, data in student_stats.items():
        avg = data["total_score"] / data["count"] if data["count"] > 0 else 0.0
        leaderboard_data.append({
            "Student": name,
            "Submissions": data["count"],
            "Average Score (%)": round(avg, 2)
        })

    # Sort by Average Score descending
    leaderboard_data = sorted(leaderboard_data, key=lambda x: x["Average Score (%)"], reverse=True)

    # Add Ranks
    ranked_data = []
    for rank, item in enumerate(leaderboard_data, start=1):
        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank}"
        ranked_data.append({
            "Rank": medal,
            "Student Name": item["Student"],
            "Submissions": item["Submissions"],
            "Average Score": f"{item['Average Score (%)']}%"
        })

    st.subheader("🌟 Global Academic Rankings")
    st.table(ranked_data)
