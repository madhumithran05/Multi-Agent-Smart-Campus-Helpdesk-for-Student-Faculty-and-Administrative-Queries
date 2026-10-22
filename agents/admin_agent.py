"""
Administrative Agent
Handles fee details, certificates, complaints, lost-and-found and campus services.
"""
import random
from data_store import get_student, add_complaint, get_queue


def respond(query: str) -> str:
    q = query.lower()
    student = get_student()

    if "lost" in q or "complaint" in q or "found" in q:
        ticket = add_complaint(query)
        return (
            f"I've generated complaint ticket <b>#{ticket['id']}</b> and routed it to the "
            f"relevant department / Lost &amp; Found desk. You'll get status updates automatically."
        )

    if "fee" in q or "payment" in q or "due" in q:
        return (
            f"Your pending fee balance is <b>₹{student['fee_due']:,}</b>, due {student['fee_due_date']}. "
            f"I can set a reminder 2 days before the deadline."
        )

    if "certificate" in q or "bonafide" in q:
        return (
            "A bonafide certificate request has been queued at the Admin Block counter. "
            "Current wait time is about 10 minutes — I'll notify you when it's ready."
        )

    if "queue" in q:
        queue = get_queue()
        lines = ", ".join(f"{item['label']} ({item['n']} waiting)" for item in queue)
        return f"Current wait times — {lines}."

    fallback = [
        "I handle fees, certificates, complaints and campus services — could you tell me which one you need?",
        "I can raise a ticket, check your fee status, or queue a certificate request. What would you like to do?",
    ]
    return random.choice(fallback)
