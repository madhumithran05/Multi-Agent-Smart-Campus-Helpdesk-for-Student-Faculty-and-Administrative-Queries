"""
Event Agent
Recommends workshops, seminars, hackathons and placement drives based on interests.
"""
import random
from data_store import get_events


def respond(query: str) -> str:
    q = query.lower()
    events = get_events()

    tag_map = {
        "hackathon": "Hackathon", "workshop": "Workshop",
        "placement": "Placement", "seminar": "Seminar",
    }
    tag = next((v for k, v in tag_map.items() if k in q), None)

    if tag:
        matches = [e for e in events if e["tag"] == tag]
        if matches:
            e = matches[0]
            return (
                f"Found it — <b>{e['title']}</b> ({e['date']}) at {e['loc']}. {e['desc']} "
                f"Want me to reserve a seat?"
            )

    if "placement" in q or "drive" in q or "job" in q:
        matches = [e for e in events if e["tag"] == "Placement"]
        if matches:
            e = matches[0]
            return f"Nearest placement drive: <b>{e['title']}</b> on {e['date']} at {e['loc']}."

    top = events[0]
    fallback = [
        f"Based on trending interest, I'd recommend <b>{top['title']}</b> ({top['date']}). Check the Events tab for more.",
        "Tell me a topic — hackathons, workshops, seminars or placement drives — and I'll filter recommendations for you.",
    ]
    return random.choice(fallback)
