"""
Coordinator Agent
Classifies incoming queries and routes them to one or more specialist agents,
then merges their responses. This is the entry point the Flask app calls.
"""
import re
from agents import student_agent, faculty_agent, admin_agent, navigation_agent, event_agent

AGENT_META = {
    "student":    {"name": "Student Agent",         "icon": "🎓", "module": student_agent},
    "faculty":    {"name": "Faculty Agent",          "icon": "🧑‍🏫", "module": faculty_agent},
    "admin":      {"name": "Administrative Agent",   "icon": "🏛", "module": admin_agent},
    "navigation": {"name": "Navigation Agent",       "icon": "⌖", "module": navigation_agent},
    "event":      {"name": "Event Agent",            "icon": "✦", "module": event_agent},
}

PATTERNS = {
    "student": r"attend|exam|assignment|marks|result|schedule.*class|syllabus|predict",
    "faculty": r"faculty|professor|prof\.|\bprof\b|\bdr\b|\baiml\b|\bstaffs?\b|\bhod\b|available|leave|office hour|timetable",
    "admin": r"fee|certificate|complaint|bonafide|payment|due|service|id card|lost|found",
    "navigation": r"where|navigate|guide|direction|lab|room|building|classroom",
    "event": r"event|workshop|seminar|hackathon|placement|drive|interest",
}


def classify(query: str):
    q = query.lower()
    hits = [key for key, pattern in PATTERNS.items() if re.search(pattern, q)]
    if not hits:
        hits = ["student"]
    # de-duplicate while preserving order
    seen = set()
    ordered = [h for h in hits if not (h in seen or seen.add(h))]
    return ordered


def route(query: str):
    """
    Returns a dict describing the full multi-agent exchange:
    {
      "agents": ["student", "admin"],
      "responses": {"student": "...", "admin": "..."},
      "log": ["Coordinator -> routing to Student Agent + Administrative Agent", ...]
    }
    """
    agents_hit = classify(query)
    log = [f"Coordinator parsed the query and identified {len(agents_hit)} relevant agent(s)."]

    names = " + ".join(AGENT_META[a]["name"] for a in agents_hit)
    log.append(f"Coordinator -> routing to {names}")

    responses = {}
    for key in agents_hit:
        meta = AGENT_META[key]
        answer = meta["module"].respond(query)
        responses[key] = answer
        log.append(f"{meta['name']} -> response sent to Coordinator")

    if len(agents_hit) > 1:
        log.append(f"Coordinator -> merged {len(agents_hit)} agent responses into one answer")

    return {
        "agents": agents_hit,
        "agent_meta": {k: {"name": AGENT_META[k]["name"], "icon": AGENT_META[k]["icon"]} for k in agents_hit},
        "responses": responses,
        "log": log,
        "collab": len(agents_hit) > 1,
    }
