from datetime import date, datetime, time, timedelta

from flask import Blueprint, jsonify, request

from backend.database.connection import execute, fetch_all
from backend.middleware.auth_middleware import (
    get_current_student,
    get_current_teacher,
    get_current_user,
    get_teacher_exam_ids,
    login_required,
    role_required,
)

bp = Blueprint("timetable_routes", __name__)


def serialize_timetable_entry(entry):
    for field in ("exam_date", "created_at", "updated_at"):
        value = entry.get(field)
        if isinstance(value, (date, datetime)):
            entry[field] = value.isoformat()
    for field in ("start_time", "end_time"):
        value = entry.get(field)
        if isinstance(value, timedelta):
            seconds = int(value.total_seconds())
            sign = "-" if seconds < 0 else ""
            hours, remainder = divmod(abs(seconds), 3600)
            minutes, seconds = divmod(remainder, 60)
            entry[field] = f"{sign}{hours:02}:{minutes:02}:{seconds:02}"
        elif isinstance(value, time):
            entry[field] = value.isoformat()
    return entry


@bp.route("/api/timetable", methods=["GET"])
@login_required
@role_required("ADMIN", "TEACHER", "STUDENT")
def get_timetable():
    if get_current_user().get("role") == "STUDENT":
        student = get_current_student()
        if not student:
            return jsonify({"success": False, "message": "Student profile is not linked to this account."}), 403
        entries = fetch_all(
            """
            SELECT t.*, e.name AS exam_name, r.room_number,
                teacher.name AS invigilator_name
            FROM timetable t
            INNER JOIN exams e ON e.id = t.exam_id
            LEFT JOIN rooms r ON r.id = t.room_id
            LEFT JOIN teachers teacher ON teacher.id = t.invigilator_id
            WHERE EXISTS (
                SELECT 1 FROM exam_students es
                WHERE es.exam_id = t.exam_id AND es.student_id = %s
            ) OR EXISTS (
                SELECT 1
                FROM seat_assignments sa
                INNER JOIN seating_arrangements arr ON arr.id = sa.arrangement_id
                WHERE arr.exam_id = t.exam_id AND sa.student_id = %s
            )
            ORDER BY t.exam_date DESC
            """,
            (student["id"], student["id"]),
        )
    elif get_current_user().get("role") == "TEACHER":
        teacher = get_current_teacher()
        if not teacher:
            return jsonify({"success": False, "message": "Teacher profile is not linked to this account."}), 403
        exam_ids = get_teacher_exam_ids(teacher["id"])
        if not exam_ids:
            return jsonify({"success": True, "timetable": []})
        placeholders = ", ".join(["%s"] * len(exam_ids))
        entries = fetch_all(
            f"""
            SELECT t.*, e.name AS exam_name, r.room_number,
                teacher.name AS invigilator_name
            FROM timetable t
            INNER JOIN exams e ON e.id = t.exam_id
            LEFT JOIN rooms r ON r.id = t.room_id
            LEFT JOIN teachers teacher ON teacher.id = t.invigilator_id
            WHERE t.exam_id IN ({placeholders})
            ORDER BY t.exam_date DESC
            """,
            tuple(exam_ids),
        )
    else:
        entries = fetch_all("SELECT * FROM timetable ORDER BY exam_date DESC")
    return jsonify({"success": True, "timetable": [serialize_timetable_entry(entry) for entry in entries]})


@bp.route("/api/timetable", methods=["POST"])
@login_required
@role_required("ADMIN")
def create_timetable():
    payload = request.get_json(silent=True) or {}
    execute(
        "INSERT INTO timetable (exam_id, room_id, invigilator_id, exam_date, start_time, end_time, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())",
        (payload.get("exam_id"), payload.get("room_id"), payload.get("invigilator_id"), payload.get("exam_date"), payload.get("start_time"), payload.get("end_time")),
    )
    return jsonify({"success": True, "message": "Timetable entry created successfully."})
