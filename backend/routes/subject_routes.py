from flask import Blueprint, jsonify, request

from backend.database.connection import execute, fetch_all
from backend.middleware.auth_middleware import login_required, role_required

bp = Blueprint("subject_routes", __name__)


@bp.route("/api/subjects", methods=["GET"])
@login_required
@role_required("ADMIN")
def list_subjects():
    return jsonify({"success": True, "subjects": fetch_all("SELECT * FROM subjects ORDER BY id DESC")})


@bp.route("/api/subjects", methods=["POST"])
@login_required
@role_required("ADMIN")
def create_subject():
    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    if not name:
        return jsonify({"success": False, "message": "Subject name is required."}), 400
    subject_id = execute("INSERT INTO subjects (name, code, credits, created_at, updated_at) VALUES (%s, %s, %s, NOW(), NOW())", (name, payload.get("code", ""), payload.get("credits", 3)))
    return jsonify({"success": True, "message": "Subject created successfully.", "id": subject_id})


@bp.route("/api/subjects/<int:subject_id>", methods=["PUT"])
@login_required
@role_required("ADMIN")
def update_subject(subject_id):
    payload = request.get_json(silent=True) or {}
    execute("UPDATE subjects SET name = %s, code = %s, credits = %s, updated_at = NOW() WHERE id = %s", (payload.get("name"), payload.get("code", ""), payload.get("credits", 3), subject_id))
    return jsonify({"success": True, "message": "Subject updated successfully."})


@bp.route("/api/subjects/<int:subject_id>", methods=["DELETE"])
@login_required
@role_required("ADMIN")
def delete_subject(subject_id):
    execute("DELETE FROM subjects WHERE id = %s", (subject_id,))
    return jsonify({"success": True, "message": "Subject deleted successfully."})
