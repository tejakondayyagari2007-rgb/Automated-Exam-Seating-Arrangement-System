from datetime import date, datetime, time, timedelta

from flask import Blueprint, jsonify, request

from backend.database.connection import execute, fetch_all, fetch_one
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


def _parse_positive_id(value):
    if isinstance(value, bool):
        return None
    try:
        parsed_id = int(value)
    except (TypeError, ValueError):
        return None
    if parsed_id < 1 or str(value).strip() != str(parsed_id):
        return None
    return parsed_id


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
    if not isinstance(payload, dict):
        return jsonify({"success": False, "message": "Valid timetable details are required."}), 400

    exam_id = _parse_positive_id(payload.get("exam_id"))
    room_id = _parse_positive_id(payload.get("room_id"))
    invigilator_id = _parse_positive_id(payload.get("invigilator_id"))
    if not exam_id or not room_id or not invigilator_id:
        return jsonify({
            "success": False,
            "message": "Valid exam, room, and invigilator IDs are required.",
        }), 400

    try:
        exam_date = date.fromisoformat(str(payload.get("exam_date", "")))
        start_time = time.fromisoformat(str(payload.get("start_time", "")))
        end_time = time.fromisoformat(str(payload.get("end_time", "")))
    except ValueError:
        return jsonify({
            "success": False,
            "message": "Enter a valid exam date, start time, and end time.",
        }), 400
    if end_time <= start_time:
        return jsonify({
            "success": False,
            "message": "End time must be later than start time.",
        }), 400

    if not fetch_one("SELECT id FROM exams WHERE id = %s", (exam_id,)):
        return jsonify({"success": False, "message": "Exam not found."}), 404
    if not fetch_one("SELECT id FROM rooms WHERE id = %s", (room_id,)):
        return jsonify({"success": False, "message": "Room not found."}), 404
    if not fetch_one("SELECT id FROM teachers WHERE id = %s", (invigilator_id,)):
        return jsonify({"success": False, "message": "Invigilator not found."}), 404

    room_conflict = fetch_one(
        """
        SELECT id FROM timetable
        WHERE room_id = %s AND exam_date = %s
            AND start_time < %s AND end_time > %s
        LIMIT 1
        """,
        (room_id, exam_date, end_time, start_time),
    )
    if room_conflict:
        return jsonify({
            "success": False,
            "message": "The room is already booked during this time.",
        }), 409

    invigilator_conflict = fetch_one(
        """
        SELECT id FROM timetable
        WHERE invigilator_id = %s AND exam_date = %s AND exam_id != %s
            AND start_time < %s AND end_time > %s
        LIMIT 1
        """,
        (invigilator_id, exam_date, exam_id, end_time, start_time),
    )
    if invigilator_conflict:
        return jsonify({
            "success": False,
            "message": "The invigilator is already assigned to another exam during this time.",
        }), 409

    execute(
        "INSERT INTO timetable (exam_id, room_id, invigilator_id, exam_date, start_time, end_time, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())",
        (exam_id, room_id, invigilator_id, exam_date, start_time, end_time),
    )
    return jsonify({"success": True, "message": "Timetable entry created successfully."})
