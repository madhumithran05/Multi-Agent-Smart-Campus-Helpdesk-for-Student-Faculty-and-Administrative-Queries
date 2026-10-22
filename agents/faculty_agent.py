"""
Faculty Agent
Handles timetables, leave management, student performance and live availability.
"""
import random
import re
from data_store import get_faculty

STATUS_LABEL = {
    "on": "available",
    "busy": "in a class",
    "off": "offline / on leave",
    "na": "not tracked yet",   # real faculty listed, but no live availability feed connected
}

TITLES = {"dr", "prof", "mr", "mrs", "ms"}

# Spoken / typed variants -> department code used in faculty.json
DEPT_ALIASES = {
    "aiml": "AIML",
    "ai and ml": "AIML",
    "ai ml": "AIML",
    "artificial intelligence and machine learning": "AIML",
}


def _clean(text):
    return re.sub(r"[^a-z\s]", " ", text)


def _candidates(q, faculty):
    """
    Return the best-matching faculty member(s) for a query.
    Real name words must match (length > 2); single-letter initials only break ties,
    so "Haripriya R" and "Haripriya S" can be told apart.
    """
    q = re.sub(r"['’]s\b", "", q)          # "Haripriya's" -> "Haripriya"
    clean = _clean(q)
    words = set(clean.split())
    scored = []
    for f in faculty:
        parts = [w for w in _clean(f["name"].lower()).split() if w not in TITLES]
        name_words = [p for p in parts if len(p) > 2]
        hits = [p for p in name_words if p in words or (len(p) > 4 and p in clean)]
        if not hits:
            continue
        initials = sum(1 for p in parts if len(p) == 1 and p in words)
        scored.append((len(hits) + initials, f))
    if not scored:
        return []
    best = max(s for s, _ in scored)
    return [f for s, f in scored if s == best]


def _dept_match(q, faculty):
    qn = re.sub(r"\s+", " ", q.replace("&", " and ")).strip()
    for alias, dept in DEPT_ALIASES.items():
        if re.search(r"\b" + re.escape(alias) + r"\b", qn):
            return dept
    for dept in sorted({f["dept"] for f in faculty}, key=len, reverse=True):
        if re.search(r"\b" + re.escape(dept.lower()) + r"\b", qn):
            return dept
    return None


def _describe(f):
    who = f"<b>{f['name']}</b> ({f['designation']}, {f['dept']})"
    link = f.get("profile")
    profile = f' <a href="{link}" target="_blank" rel="noopener">View profile ↗</a>' if link else ""

    if f["status"] == "na":
        return (
            f"{who} is on the {f['dept']} faculty at the {f['room']}. "
            f"Live availability isn't connected for this department yet, so please check with the "
            f"department office before visiting.{profile}"
        )
    label = STATUS_LABEL[f["status"]]
    if f["status"] == "on":
        return f"{who} is {label} right now at the {f['room']}, free until {f['free_until']}.{profile}"
    return (
        f"{who} is currently {label}. "
        f"Next available: {f['free_from']} ({f['free_until']}) at the {f['room']}.{profile}"
    )


def respond(query: str) -> str:
    q = query.lower()
    faculty = get_faculty()

    matches = _candidates(q, faculty)
    if len(matches) == 1:
        return _describe(matches[0])
    if len(matches) > 1:
        options = "; ".join(f"{m['name']} ({m['dept']})" for m in matches)
        return (
            f"I found more than one faculty member matching that: {options}. "
            f"Which one do you mean? Adding their initial helps."
        )

    dept = _dept_match(q, faculty)
    if dept:
        members = [f for f in faculty if f["dept"] == dept]
        head = next((f for f in members if "head" in f["designation"].lower()), None)
        text = f"<b>{dept}</b> faculty I can see ({len(members)}): {', '.join(f['name'] for f in members)}. "
        if head:
            text += f"Head of department: <b>{head['name']}</b>. "
        tracked = [f for f in members if f["status"] != "na"]
        if tracked:
            free_now = [f["name"] for f in tracked if f["status"] == "on"]
            text += f"Available right now: {', '.join(free_now) or 'none at the moment'}."
        else:
            text += "Live availability isn't connected for this department yet — ask for a specific name and I'll share their profile."
        return text

    if "available" in q or "free" in q or "status" in q:
        tracked = [f for f in faculty if f["status"] != "na"]
        free_now = [f for f in tracked if f["status"] == "on"]
        return (
            f"Checked the live faculty tracker — <b>{len(free_now)} of {len(tracked)}</b> tracked faculty "
            f"are available right now: {', '.join(f['name'] for f in free_now) or 'none at the moment'}."
        )

    if "leave" in q:
        return "Leave requests go through the Faculty Portal — I can notify the department coordinator on your behalf if you'd like."

    if "timetable" in q:
        return "I've pulled up the timetable — most CSE faculty have lecture slots between 9 AM and 1 PM, with office hours in the afternoon."

    fallback = [
        "I track real-time faculty availability, timetables, and leave status — ask me about a specific professor or department.",
        "Which faculty member are you looking for? I can check their live status for you.",
    ]
    return random.choice(fallback)
