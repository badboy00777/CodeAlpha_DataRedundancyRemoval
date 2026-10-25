
from flask import Blueprint, jsonify, render_template, request

from app import services

bp = Blueprint("main", __name__)

# HTTP status for each verdict
STATUS = {"UNIQUE": 201, "REDUNDANT": 409, "FALSE_POSITIVE": 422}


@bp.get("/")
def index():
    return render_template("index.html")


@bp.get("/health")
def health():
    # Used by us (and later by AWS) to check that the app and database are alive
    up = services.db_is_up()
    return jsonify({"status": "ok" if up else "degraded", "database": up}), (200 if up else 503)


@bp.post("/api/records")
def add_record():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "send a JSON object"}), 400
    result = services.submit_record(data)
    body = {
        "verdict": result["verdict"],
        "reason": result["reason"],
        "matched_record_id": result["matched_record_id"],
        "record_id": result.get("record_id"),
    }
    return jsonify(body), STATUS[result["verdict"]]


@bp.get("/api/records")
def get_records():
    return jsonify(services.list_records())


@bp.get("/api/audit")
def get_audit():
    return jsonify(services.list_audit())


@bp.get("/api/stats")
def get_stats():
    return jsonify(services.get_stats())