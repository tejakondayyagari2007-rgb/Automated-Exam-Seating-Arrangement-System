from flask import Blueprint, jsonify, request

from backend.database.connection import execute, fetch_all, fetch_one
from backend.middleware.auth_middleware import login_required, role_required

bp = Blueprint("teacher_routes", __name__)


@bp.route("/api/teachers", methods=["GET"])
@login_required
@role_required("ADMIN")
def list_teachers():
    return jsonify({"success": True, "teachers": fetch_all("SELECT * FROM teachers ORDER BY id DESC")})


@bp.route("/api/teachers", methods=["POST"])
@login_required
@role_required("ADMIN")
def create_teacher():
    payload = request.get_json(silent=True) or {}
    required = ["employee_id", "name", "email", "department_id", "designation"]
    if not all(payload.get(field) not in (None, "") for field in required):
        return jsonify({"success": False, "message": "All teacher details are required."}), 400
    teacher_id = execute(
        "INSERT INTO teachers (employee_id, name, email, phone, department_id, designation, availability, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())",
        (payload["employee_id"], payload["name"], payload["email"], payload.get("phone", ""), payload["department_id"], payload["designation"], payload.get("availability", "available")),
    )
    return jsonify({"success": True, "message": "Teacher created successfully.", "id": teacher_id})


@bp.route("/api/teachers/<int:teacher_id>", methods=["PUT"])
@login_required
@role_required("ADMIN")
def update_teacher(teacher_id):
    payload = request.get_json(silent=True) or {}
    execute(
        "UPDATE teachers SET employee_id = %s, name = %s, email = %s, phone = %s, department_id = %s, designation = %s, availability = %s, updated_at = NOW() WHERE id = %s",
        (
            payload.get("employee_id"),
            payload.get("name"),
            payload.get("email"),
            payload.get("phone", ""),
            payload.get("department_id"),
            payload.get("designation"),
            payload.get("availability", "available"),
            teacher_id,
        ),
    )
    return jsonify({"success": True, "message": "Teacher updated successfully."})


@bp.route("/api/teachers/<int:teacher_id>", methods=["DELETE"])
@login_required
@role_required("ADMIN")
def delete_teacher(teacher_id):
    execute("DELETE FROM teachers WHERE id = %s", (teacher_id,))
    return jsonify({"success": True, "message": "Teacher deleted successfully."})
