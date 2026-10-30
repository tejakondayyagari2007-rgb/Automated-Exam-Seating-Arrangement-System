from flask import Blueprint, jsonify

from backend.database.connection import fetch_all
from backend.middleware.auth_middleware import (
    get_current_teacher,
    get_current_user,
    get_teacher_exam_ids,
    login_required,
    role_required,
)
from backend.services.report_service import get_reports

bp = Blueprint("report_routes", __name__)


@bp.route("/api/reports", methods=["GET"])
@login_required
@role_required("ADMIN", "TEACHER")
def reports():
    exam_ids = None
    if get_current_user().get("role") == "TEACHER":
        teacher = get_current_teacher()
        if not teacher:
            return jsonify({"success": False, "message": "Teacher profile is not linked to this account."}), 403
        exam_ids = get_teacher_exam_ids(teacher["id"])
    return jsonify({"success": True, "reports": get_reports(exam_ids)})


@bp.route("/api/reports/export", methods=["GET"])
@login_required
@role_required("ADMIN", "TEACHER")
def export_reports():
    if get_current_user().get("role") == "TEACHER":
        teacher = get_current_teacher()
        if not teacher:
            return jsonify({"success": False, "message": "Teacher profile is not linked to this account."}), 403
        exam_ids = get_teacher_exam_ids(teacher["id"])
        if not exam_ids:
            return jsonify({"success": True, "data": []})
        placeholders = ", ".join(["%s"] * len(exam_ids))
        rows = fetch_all(
            f"""
            SELECT DISTINCT s.id, s.roll_no, s.name, s.email, s.phone
            FROM students s
            INNER JOIN exam_students es ON es.student_id = s.id
            WHERE es.exam_id IN ({placeholders})
            ORDER BY s.roll_no
            """,
            tuple(exam_ids),
        )
    else:
        rows = fetch_all("SELECT * FROM students")
    return jsonify({"success": True, "data": rows})
