"""
Quadrant — Multi-Agent Smart Campus Helpdesk
=============================================
Flask backend that exposes the Coordinator Agent and four specialist
agents (Student, Faculty, Administrative, Navigation, Event) over a
small JSON API, plus the dashboard/navigator/events/lost-found data
those agents and the UI rely on.

Run:
    pip install -r requirements.txt
    python app.py
Then open http://127.0.0.1:5000
"""
from flask import Flask, render_template, request, jsonify

import data_store
from agents import coordinator

app = Flask(__name__)


# ---------------------------------------------------------------- pages ----
@app.route("/")
def index():
    return render_template("index.html")


# ------------------------------------------------------------- chat API ----
@app.route("/api/query", methods=["POST"])
def api_query():
    payload = request.get_json(force=True) or {}
    text = (payload.get("text") or "").strip()
    if not text:
        return jsonify({"error": "empty query"}), 400

    result = coordinator.route(text)
    
    # Log query with details
    user_ip = request.remote_addr
    user_name = payload.get("user_name", "Anonymous")
    data_store.log_query(result["agents"], user_question=text, user_ip=user_ip, user_name=user_name)
    
    return jsonify(result)


# ---------------------------------------------------------- faculty API ----
@app.route("/api/faculty")
def api_faculty():
    return jsonify(data_store.get_faculty())


@app.route("/api/queue")
def api_queue():
    return jsonify(data_store.get_queue())


@app.route("/api/student")
def api_student():
    return jsonify(data_store.get_student())


# ------------------------------------------------------------- admin API ----
@app.route("/api/complaints", methods=["GET", "POST"])
def api_complaints():
    if request.method == "POST":
        payload = request.get_json(force=True) or {}
        ticket = data_store.add_complaint(payload.get("text", ""))
        return jsonify(ticket), 201
    return jsonify(data_store.get_complaints())


# ------------------------------------------------------------ events API ----
@app.route("/api/events")
def api_events():
    return jsonify(data_store.get_events())


# -------------------------------------------------------- navigator API ----
@app.route("/api/buildings")
def api_buildings():
    return jsonify(data_store.get_buildings())


@app.route("/api/campus")
def api_campus():
    return jsonify(data_store.get_campus())


@app.route("/api/route", methods=["POST"])
def api_route():
    payload = request.get_json(force=True) or {}
    query = (payload.get("destination") or "").lower()
    match = data_store.find_building(query)
    if not match:
        buildings = [b for b in data_store.get_buildings() if b["id"] != "gate"]
        match = buildings[hash(query) % len(buildings)] if buildings else None
    if not match:
        return jsonify({"error": "no buildings configured"}), 404
    return jsonify(match)


# ----------------------------------------------------- lost & found API ----
@app.route("/api/lostfound", methods=["GET", "POST"])
def api_lostfound():
    if request.method == "POST":
        payload = request.get_json(force=True) or {}
        item = {
            "name": payload.get("name", "Unnamed item"),
            "type": payload.get("type", "Lost"),
            "loc": payload.get("loc") or "Not specified",
            "notes": payload.get("notes", ""),
            "status": "open",
        }
        data_store.add_lost_found(item)
        ticket = data_store.add_complaint(f"{item['type']} item: {item['name']} at {item['loc']}")
        return jsonify({"item": item, "ticket": ticket}), 201
    return jsonify(data_store.get_lost_found())


@app.route("/api/lostfound/<int:index>/toggle", methods=["POST"])
def api_lostfound_toggle(index):
    item = data_store.toggle_lost_found(index)
    if item is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(item)


# --------------------------------------------------------- dashboard API ----
@app.route("/api/dashboard")
def api_dashboard():
    return jsonify(data_store.get_dashboard_stats())


# -------------------------------------------------------- admin API ----
@app.route("/admin/queries")
def admin_queries():
    """Get all query logs for admin dashboard"""
    return jsonify(data_store.get_query_logs())


@app.route("/admin/unknown-queries")
def admin_unknown_queries():
    """Get only unknown/unanswered queries"""
    return jsonify(data_store.get_unknown_queries())


@app.route("/admin/query-stats")
def admin_query_stats():
    """Get query statistics"""
    return jsonify(data_store.get_query_stats())


@app.route("/admin/query/<int:query_id>/mark", methods=["POST"])
def admin_mark_query(query_id):
    """Admin marks a query quality (answered/unknown/partial/needs_follow_up)"""
    payload = request.get_json(force=True) or {}
    quality = payload.get("quality", "unknown")
    feedback = payload.get("feedback", "")
    data_store.update_query_quality(query_id, quality, feedback)
    return jsonify({"success": True, "query_id": query_id, "quality": quality})


@app.route("/admin")
def admin_dashboard():
    """Admin dashboard page"""
    return render_template("admin_dashboard.html")


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
