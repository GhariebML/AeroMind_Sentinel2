"""
dashboard/routes/api_db.py — Database CRUD API endpoints.
"""
from __future__ import annotations
from flask import Blueprint, jsonify, request
import dashboard.database as db

api_db_bp = Blueprint("api_db", __name__)

@api_db_bp.route("/api/db/stats")
def api_db_stats():
    return jsonify(db.get_stats())

@api_db_bp.route("/api/db/runs")
def api_db_runs():
    limit = min(int(request.args.get("limit", 50)), 200)
    return jsonify(db.get_runs(limit))

@api_db_bp.route("/api/db/runs/<int:run_id>")
def api_db_run(run_id: int):
    r = db.get_run(run_id)
    return jsonify(r) if r else (jsonify({"error": "not found"}), 404)

@api_db_bp.route("/api/db/runs/<int:run_id>/telemetry")
def api_db_run_telemetry(run_id: int):
    return jsonify(db.get_telemetry(run_id, min(int(request.args.get("limit", 500)), 2000)))

@api_db_bp.route("/api/db/runs/<int:run_id>/telemetry/recent")
def api_db_run_telemetry_recent(run_id: int):
    return jsonify(db.get_telemetry_recent(run_id, min(int(request.args.get("n", 60)), 200)))

@api_db_bp.route("/api/db/eval")
def api_db_eval():
    return jsonify(db.get_eval_history(min(int(request.args.get("limit", 20)), 100)))

@api_db_bp.route("/api/db/eval", methods=["POST"])
def api_db_eval_save():
    body = request.get_json(silent=True) or {}
    run_id = body.pop("run_id", None)
    eid = db.save_eval(body, run_id=run_id, source="api")
    db.log_event(f"Eval result saved — id={eid}", component="eval")
    return jsonify({"id": eid, "status": "saved"})

@api_db_bp.route("/api/db/gallery")
def api_db_gallery():
    return jsonify(db.get_gallery(min(int(request.args.get("limit", 100)), 500), request.args.get("scenario")))

@api_db_bp.route("/api/db/gallery", methods=["POST"])
def api_db_gallery_add():
    body = request.get_json(silent=True) or {}
    gid = db.add_capture(file_path=body.get("file_path", ""), scenario=body.get("scenario", "unknown"),
        run_id=body.get("run_id"), telemetry=body.get("telemetry"), tags=body.get("tags", []),
        title=body.get("title", ""), description=body.get("description", ""))
    return jsonify({"id": gid, "status": "saved"})

@api_db_bp.route("/api/db/events")
def api_db_events():
    return jsonify(db.get_events(min(int(request.args.get("limit", 100)), 500), request.args.get("component")))

@api_db_bp.route("/api/db/events", methods=["POST"])
def api_db_events_add():
    body = request.get_json(silent=True) or {}
    db.log_event(body.get("message", ""), body.get("level", "INFO"), body.get("component", "frontend"))
    return jsonify({"status": "logged"})
