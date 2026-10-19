import os
import logging
from datetime import date, datetime, timedelta
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from models.database import init_db, get_db
from services.gym_service import (
    create_member, list_members, get_member, update_member, renew_membership,
    record_attendance, create_workout, list_workouts, record_progress,
    get_analytics, get_member_workouts
)
from analytics.charts import generate_charts

load_dotenv()
app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("gym_system.log", encoding="utf-8")]
)
logger = logging.getLogger("gym-system")
init_db()

@app.before_request
def log_request():
    logger.info("%s %s", request.method, request.path)

@app.errorhandler(404)
def not_found(_):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(405)
def method_not_allowed(_):
    return jsonify({"error": "Method not allowed for this endpoint"}), 405

@app.errorhandler(500)
def internal_error(error):
    logger.exception("Unhandled server error: %s", error)
    return jsonify({"error": "Internal server error"}), 500

def respond(fn, success_status=200):
    try:
        payload, status = fn()
        return jsonify(payload), status or success_status
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except LookupError as exc:
        return jsonify({"error": str(exc)}), 404
    except Exception:
        logger.exception("Request failed")
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.get("/")
def home():
    return render_template("index.html")

@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "date": date.today().isoformat()})

@app.get("/api/docs")
def docs():
    return jsonify({
        "message": "Gym Management API",
        "endpoints": [
            {"method":"POST","path":"/api/members","purpose":"Register member"},
            {"method":"GET","path":"/api/members","purpose":"List/search members (?q=term, ?status=active)"},
            {"method":"GET","path":"/api/members/<id>","purpose":"Get member profile"},
            {"method":"PUT","path":"/api/members/<id>","purpose":"Update member profile"},
            {"method":"POST","path":"/api/members/<id>/renew","purpose":"Renew membership"},
            {"method":"POST","path":"/api/attendance","purpose":"Record attendance"},
            {"method":"GET","path":"/api/attendance?member_id=<id>","purpose":"List attendance"},
            {"method":"POST","path":"/api/workouts","purpose":"Create/assign workout plan"},
            {"method":"GET","path":"/api/members/<id>/workouts","purpose":"List member workouts"},
            {"method":"POST","path":"/api/workouts/<id>/progress","purpose":"Record workout completion/progress"},
            {"method":"GET","path":"/api/analytics","purpose":"Analytics summary"},
            {"method":"POST","path":"/api/analytics/charts","purpose":"Generate analytics charts"}
        ],
        "membership_plans": {"monthly": 30, "quarterly": 90, "yearly": 365},
        "note": "Send JSON request bodies with Content-Type: application/json."
    })

@app.post("/api/members")
def add_member():
    return respond(lambda: ({"member": create_member(request.get_json(silent=True) or {})}, 201))

@app.get("/api/members")
def members():
    return respond(lambda: ({"members": list_members(request.args.get("q"), request.args.get("status"))}, 200))

@app.get("/api/members/<int:member_id>")
def member_detail(member_id):
    return respond(lambda: ({"member": get_member(member_id)}, 200))

@app.put("/api/members/<int:member_id>")
def member_update(member_id):
    return respond(lambda: ({"member": update_member(member_id, request.get_json(silent=True) or {})}, 200))

@app.post("/api/members/<int:member_id>/renew")
def member_renew(member_id):
    return respond(lambda: ({"member": renew_membership(member_id, (request.get_json(silent=True) or {}))}, 200))

@app.post("/api/attendance")
def attendance_add():
    return respond(lambda: ({"attendance": record_attendance(request.get_json(silent=True) or {})}, 201))

@app.get("/api/attendance")
def attendance_list():
    member_id = request.args.get("member_id", type=int)
    with get_db() as conn:
        if member_id:
            rows = conn.execute("""SELECT a.*, m.name AS member_name FROM attendance a
                JOIN members m ON m.id=a.member_id WHERE a.member_id=? ORDER BY a.attended_at DESC""",
                (member_id,)).fetchall()
        else:
            rows = conn.execute("""SELECT a.*, m.name AS member_name FROM attendance a
                JOIN members m ON m.id=a.member_id ORDER BY a.attended_at DESC LIMIT 500""").fetchall()
    return jsonify({"attendance": [dict(r) for r in rows]})

@app.post("/api/workouts")
def workout_add():
    return respond(lambda: ({"workout": create_workout(request.get_json(silent=True) or {})}, 201))

@app.get("/api/members/<int:member_id>/workouts")
def member_workouts(member_id):
    return respond(lambda: ({"workouts": get_member_workouts(member_id)}, 200))

@app.get("/api/workouts")
def workouts():
    return jsonify({"workouts": list_workouts(request.args.get("member_id", type=int))})

@app.post("/api/workouts/<int:workout_id>/progress")
def workout_progress(workout_id):
    return respond(lambda: ({"progress": record_progress(workout_id, request.get_json(silent=True) or {})}, 201))

@app.get("/api/analytics")
def analytics():
    return respond(lambda: (get_analytics(), 200))

@app.post("/api/analytics/charts")
def charts():
    result = generate_charts()
    return jsonify({"message": "Charts generated", "files": result})

if __name__ == "__main__":
    app.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
