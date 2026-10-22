"""
Lightweight in-memory data layer for the Smart Campus Helpdesk demo.
Loads seed data from /data/*.json on startup and exposes simple
getters/mutators used by the agents and Flask routes.

In a production system this would be swapped for a real database
(Postgres / MongoDB) without changing the agent code, since agents only
talk to this module, never to the JSON files directly.
"""
import json
import os
import random
import itertools

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")


def _load(filename):
    with open(os.path.join(DATA_DIR, filename), "r", encoding="utf-8") as f:
        return json.load(f)


# ---------- seed data (loaded once at startup) ----------
_faculty = _load("faculty.json")
_events = _load("events.json")
_buildings = _load("buildings.json")
_students = _load("students.json")

_queue = [
    {"label": "Fee receipt counter", "n": 4},
    {"label": "Bonafide certificate", "n": 2},
    {"label": "Complaint desk", "n": 6},
]

_complaints = []
_complaint_id_counter = itertools.count(4820)

_lost_found = [
    {"name": "Black backpack", "type": "Found", "loc": "Cafeteria", "notes": "Has a laptop sleeve inside", "status": "open"},
    {"name": "Casio calculator", "type": "Lost", "loc": "Exam Hall 2", "notes": "Name tag: R. Sharma", "status": "resolved"},
    {"name": "Silver wristwatch", "type": "Found", "loc": "Sports Ground", "notes": "Leather strap", "status": "open"},
]

_query_log = []  # every processed query, used to build dashboard stats

# Query logging with detailed tracking
_query_logs_detailed = [
    {"id": 1, "question": "What's my attendance?", "agents": ["student"], "quality": "answered", "timestamp": "2024-07-15 10:30", "user": "Unknown"},
    {"id": 2, "question": "Where is the library?", "agents": ["navigation"], "quality": "answered", "timestamp": "2024-07-15 10:35", "user": "Unknown"},
    {"id": 3, "question": "How do I reset my password?", "agents": ["admin"], "quality": "unknown", "timestamp": "2024-07-15 10:40", "user": "Unknown"},
]
_query_id_counter = itertools.count(4)


# ---------- faculty ----------
def get_faculty():
    return _faculty


# ---------- students ----------
def get_student(_roll_no=None):
    return _students["default_student"]


# ---------- queue ----------
def get_queue():
    for item in _queue:
        item["n"] = max(0, item["n"] + random.choice([-1, 0, 1]))
    return _queue


# ---------- complaints ----------
def add_complaint(text):
    ticket = {
        "id": f"CMP-{next(_complaint_id_counter)}",
        "text": text,
        "status": "open",
    }
    _complaints.append(ticket)
    return ticket


def get_complaints():
    return _complaints


# ---------- events ----------
def get_events():
    return _events


# ---------- buildings / navigation ----------
CAMPUS = {
    "name": "Bannari Amman Institute of Technology",
    "short": "BIT",
    "address": "Sathy-Bhavani Road, Alathukombai, Sathyamangalam, Erode - 638 401",
    "lat": 11.4975,
    "lng": 77.2757,
    "zoom": 17,
}


def get_campus():
    return CAMPUS


def get_buildings():
    return _buildings


def find_building(query_lower):
    for b in _buildings:
        if b["id"] == "gate":
            continue
        if b["name"].lower() in query_lower or any(w in query_lower for w in b["name"].lower().split()):
            return b
    return None


# ---------- lost & found ----------
def get_lost_found():
    return _lost_found


def add_lost_found(item):
    _lost_found.insert(0, item)
    return item


def toggle_lost_found(index):
    if 0 <= index < len(_lost_found):
        item = _lost_found[index]
        item["status"] = "resolved" if item["status"] == "open" else "open"
        return item
    return None


# ---------- dashboard / analytics ----------
def log_query(agents_hit, user_question="", user_ip="Unknown", user_name="Unknown"):
    """Log query with detailed tracking for admin dashboard"""
    _query_log.append(agents_hit)
    
    # Detailed logging
    query_entry = {
        "id": next(_query_id_counter),
        "question": user_question,
        "agents": agents_hit,
        "quality": "answered" if agents_hit else "unknown",
        "timestamp": __import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": user_name,
        "ip": user_ip,
        "feedback": ""
    }
    _query_logs_detailed.insert(0, query_entry)  # Add to front (newest first)


def get_query_logs():
    """Get all query logs for admin dashboard"""
    return _query_logs_detailed


def update_query_quality(query_id, quality, feedback=""):
    """Admin marks a query as answered/unknown/needs_follow_up"""
    for log in _query_logs_detailed:
        if log["id"] == query_id:
            log["quality"] = quality
            log["feedback"] = feedback
            break
    return True


def get_unknown_queries():
    """Get only queries marked as unknown or not well answered"""
    return [q for q in _query_logs_detailed if q["quality"] in ["unknown", "partial", "needs_follow_up"]]


def get_query_stats():
    """Get statistics about queries"""
    total = len(_query_logs_detailed)
    answered = len([q for q in _query_logs_detailed if q["quality"] == "answered"])
    unknown = len([q for q in _query_logs_detailed if q["quality"] == "unknown"])
    partial = len([q for q in _query_logs_detailed if q["quality"] == "partial"])
    
    return {
        "total_queries": total,
        "answered": answered,
        "unknown": unknown,
        "partial": partial,
        "success_rate": (answered / total * 100) if total > 0 else 0
    }


def get_dashboard_stats():
    agent_counts = {"student": 912, "faculty": 438, "admin": 601, "navigation": 287, "event": 200}
    # fold in live demo traffic on top of the seeded baseline
    for entry in _query_log:
        for a in entry:
            agent_counts[a] = agent_counts.get(a, 0) + 1

    total_queries = sum(agent_counts.values())
    open_complaints = len([c for c in _complaints if c["status"] == "open"]) + 37
    resolved_complaints = len([c for c in _complaints if c["status"] == "resolved"]) + 142
    in_progress_complaints = 28

    return {
        "total_queries": total_queries,
        "open_complaints": open_complaints,
        "avg_response_time": 3.1,
        "resolution_rate": 96.4,
        "agent_counts": agent_counts,
        "complaint_status": {
            "resolved": resolved_complaints,
            "in_progress": in_progress_complaints,
            "open": open_complaints,
        },
        "response_trend": {
            "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            "values": [3.8, 3.5, 3.2, 3.4, 3.0, 2.7, 3.1],
        },
        "agent_performance": [
            {"agent": "Student Agent", "queries": agent_counts.get("student", 0), "accuracy": 97, "avg_time": "2.4s", "color": "#4FD1C5"},
            {"agent": "Faculty Agent", "queries": agent_counts.get("faculty", 0), "accuracy": 95, "avg_time": "2.9s", "color": "#9B8CFF"},
            {"agent": "Administrative Agent", "queries": agent_counts.get("admin", 0), "accuracy": 93, "avg_time": "3.8s", "color": "#F2795C"},
            {"agent": "Navigation Agent", "queries": agent_counts.get("navigation", 0), "accuracy": 99, "avg_time": "1.6s", "color": "#5CA8F2"},
            {"agent": "Event Agent", "queries": agent_counts.get("event", 0), "accuracy": 96, "avg_time": "2.1s", "color": "#A8D65C"},
        ],
    }
