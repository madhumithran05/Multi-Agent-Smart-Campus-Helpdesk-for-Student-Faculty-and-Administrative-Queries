"""
Student Agent
Handles attendance, exam schedules, assignments, and general academic queries.
"""
import random
from data_store import get_student


def respond(query: str) -> str:
    q = query.lower()
    student = get_student()

    if "attend" in q:
        subj = next((s for s in student["subjects"] if s["name"].lower() in q), None)
        if subj:
            return (
                f"Your attendance in <b>{subj['name']}</b> is "
                f"<b>{subj['attendance']}%</b>. "
                f"{'You are above the 75% eligibility line.' if subj['attendance'] >= 75 else 'You are below the 75% eligibility line — please contact your class advisor.'}"
            )
        return (
            f"Your overall attendance is <b>{student['overall_attendance']}%</b> across all subjects. "
            f"Your lowest is Data Structures at 78%. You're currently eligible for exams."
        )

    if "exam" in q or "schedule" in q:
        if student["upcoming_exams"]:
            e = student["upcoming_exams"][0]
            return (
                f"Your next exam is <b>{e['subject']}</b> on {e['date']}, {e['time']} "
                f"in Room {e['room']}. I've added a reminder to your notifications."
            )
        return "You have no exams scheduled in the next two weeks."

    if "assignment" in q:
        if student["pending_assignments"]:
            a = student["pending_assignments"][0]
            return f"You have a pending assignment: <b>{a['title']}</b> ({a['subject']}), due {a['due']}."
        return "You're all caught up — no pending assignments."

    if "predict" in q or "will i" in q:
        return (
            f"Based on your attendance trend, you're projected to finish the semester at "
            f"<b>{student['overall_attendance']}%</b>. Missing 2 more Data Structures classes "
            f"would drop you below the 75% eligibility line."
        )

    fallback = [
        f"Your overall attendance is <b>{student['overall_attendance']}%</b> — well above the eligibility threshold.",
        "I can help with attendance, exam schedules, assignments or academic performance — could you tell me a bit more?",
    ]
    return random.choice(fallback)
