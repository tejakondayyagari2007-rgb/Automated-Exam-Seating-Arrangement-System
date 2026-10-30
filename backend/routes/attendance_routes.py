from flask import Blueprint, jsonify, request

from backend.database.connection import fetch_one
from backend.middleware.auth_middleware import (
    get_current_user,
    get_current_teacher,
    get_teacher_exam_ids,
    login_required,
    role_required,
)
from backend.services.attendance_service import get_attendance_rows, mark_attendance

bp = Blueprint("attendance_routes", __name__)


@bp.route("/api/attendance", methods=["GET"])
@login_required
@role_required("ADMIN", "TEACHER")
def list_attendance():
    exam_id = request.args.get("exam_id")
    if get_current_user().get("role") == "TEACHER":
        teacher = get_current_teacher()
        if not teacher:
            return jsonify({"success": False, "message": "Teacher profile is not linked to this account."}), 403
        permitted_exam_ids = get_teacher_exam_ids(teacher["id"])
        if exam_id and str(exam_id) not in {str(value) for value in permitted_exam_ids}:
            return jsonify({"success": False, "message": "You are not assigned to this exam."}), 403
        rows = get_attendance_rows(permitted_exam_ids=permitted_exam_ids)
        if exam_id:
            rows = [row for row in rows if str(row["exam_id"]) == str(exam_id)]
        return jsonify({"success": True, "attendance": rows})
    rows = get_attendance_rows(exam_id) if exam_id else get_attendance_rows()
    return jsonify({"success": True, "attendance": rows})


@bp.route("/api/attendance", methods=["POST"])
@login_required
@role_required("ADMIN", "TEACHER")
def create_attendance():
    payload = request.get_json(silent=True) or {}
    student_id = payload.get("student_id")
    exam_id = payload.get("exam_id")
    present_status = payload.get("present_status")
    if not all([student_id, exam_id, present_status is not None]):
        return jsonify({"success": False, "message": "Student, exam and attendance status are required."}), 400
    try:
        student_id = int(student_id)
        exam_id = int(exam_id)
        present_status = int(present_status)
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Student, exam and attendance values must be valid integers."}), 400
    if present_status not in (0, 1):
        return jsonify({"success": False, "message": "Attendance status must be present (1) or absent (0)."}), 400

    current_user = get_current_user()
    if current_user.get("role") == "TEACHER":
        teacher = get_current_teacher()
        if not teacher:
            return jsonify({"success": False, "message": "Teacher profile is not linked to this account."}), 403
        if exam_id not in get_teacher_exam_ids(teacher["id"]):
            return jsonify({"success": False, "message": "You are not assigned to this exam."}), 403

    if not fetch_one("SELECT id FROM students WHERE id = %s", (student_id,)):
        return jsonify({"success": False, "message": "Student not found."}), 404
    if not fetch_one("SELECT id FROM exams WHERE id = %s", (exam_id,)):
        return jsonify({"success": False, "message": "Exam not found."}), 404
    if not fetch_one(
        "SELECT id FROM exam_students WHERE exam_id = %s AND student_id = %s",
        (exam_id, student_id),
    ):
        return jsonify({"success": False, "message": "Student is not registered for this exam."}), 400

    mark_attendance(student_id, exam_id, present_status)
    return jsonify({"success": True, "message": "Attendance updated successfully."})
