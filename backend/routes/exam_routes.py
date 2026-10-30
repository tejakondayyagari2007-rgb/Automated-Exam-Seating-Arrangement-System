import sqlite3
from datetime import date, time

from flask import Blueprint, jsonify, request
from mysql.connector import IntegrityError

from backend.database.connection import execute, fetch_all, fetch_one
from backend.middleware.auth_middleware import (
    get_current_student,
    get_current_teacher,
    get_current_user,
    get_teacher_exam_ids,
    login_required,
    role_required,
)

bp = Blueprint("exam_routes", __name__)

EXAM_STATUSES = {"Upcoming", "Ongoing", "Completed", "Cancelled"}


def validate_exam_payload(payload, exam_id=None):
    fields = ("name", "exam_code", "subject_id", "date_value", "start_time", "end_time", "duration_minutes", "status")
    values = {field: payload.get(field) for field in fields}
    for field in ("name", "exam_code", "subject_id", "date_value", "start_time", "end_time", "duration_minutes", "status"):
        if values[field] is None or str(values[field]).strip() == "":
            return None, f"{field.replace('_', ' ').capitalize()} is required."

    values["name"] = str(values["name"]).strip()
    values["exam_code"] = str(values["exam_code"]).strip()
    values["status"] = str(values["status"]).strip()
    if len(values["name"]) > 200:
        return None, "Exam name must be 200 characters or fewer."
    if len(values["exam_code"]) > 40:
        return None, "Exam code must be 40 characters or fewer."
    if values["status"] not in EXAM_STATUSES:
        return None, "Choose a valid exam status."

    try:
        subject_id = int(values["subject_id"])
    except (TypeError, ValueError):
        return None, "Choose a valid subject."
    if subject_id < 1 or not fetch_one("SELECT id FROM subjects WHERE id = %s", (subject_id,)):
        return None, "The selected subject does not exist."
    values["subject_id"] = subject_id

    try:
        date.fromisoformat(str(values["date_value"]))
        start_time = time.fromisoformat(str(values["start_time"]))
        end_time = time.fromisoformat(str(values["end_time"]))
    except ValueError:
        return None, "Enter a valid exam date and time."
    if end_time <= start_time:
        return None, "End time must be later than start time."
    values["date_value"] = str(values["date_value"])
    values["start_time"] = start_time.strftime("%H:%M:%S")
    values["end_time"] = end_time.strftime("%H:%M:%S")

    try:
        duration = int(values["duration_minutes"])
        if str(values["duration_minutes"]).strip() != str(duration) or duration <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return None, "Duration must be a positive whole number of minutes."
    values["duration_minutes"] = duration

    duplicate_query = "SELECT id FROM exams WHERE exam_code = %s"
    duplicate_params = [values["exam_code"]]
    if exam_id is not None:
        duplicate_query += " AND id != %s"
        duplicate_params.append(exam_id)
    if fetch_one(duplicate_query, tuple(duplicate_params)):
        return None, "That exam code is already in use."
    return values, None


def serialize_exam(row):
    date_value = row.get("date_value")
    if date_value is not None:
        row["date_value"] = date_value.isoformat()[:10] if hasattr(date_value, "isoformat") else str(date_value)[:10]
    for field in ("start_time", "end_time"):
        value = row.get(field)
        if value is None:
            continue
        if hasattr(value, "strftime"):
            row[field] = value.strftime("%H:%M")
        else:
            time_value = str(value).split(".", 1)[0]
            hour, minute, *_ = time_value.split(":")
            row[field] = f"{hour.zfill(2)}:{minute}"
    return row


def is_duplicate_exam_code_error(error):
    if getattr(error, "errno", None) == 1062:
        return True
    return isinstance(error, sqlite3.IntegrityError) and "UNIQUE constraint failed: exams.exam_code" in str(error)


@bp.route("/api/exams", methods=["GET"])
@login_required
@role_required("ADMIN", "TEACHER", "STUDENT")
def list_exams():
    if get_current_user().get("role") == "STUDENT":
        student = get_current_student()
        if not student:
            return jsonify({"success": False, "message": "Student profile is not linked to this account."}), 403
        exams = fetch_all(
            """
            SELECT e.*, s.name AS subject_name, s.code AS subject_code
            FROM exams e
            LEFT JOIN subjects s ON s.id = e.subject_id
            WHERE EXISTS (
                SELECT 1 FROM exam_students es
                WHERE es.exam_id = e.id AND es.student_id = %s
            ) OR EXISTS (
                SELECT 1
                FROM seat_assignments sa
                INNER JOIN seating_arrangements arr ON arr.id = sa.arrangement_id
                WHERE arr.exam_id = e.id AND sa.student_id = %s
            )
            ORDER BY e.date_value DESC, e.start_time DESC
            """,
            (student["id"], student["id"]),
        )
    elif get_current_user().get("role") == "TEACHER":
        teacher = get_current_teacher()
        if not teacher:
            return jsonify({"success": False, "message": "Teacher profile is not linked to this account."}), 403
        exam_ids = get_teacher_exam_ids(teacher["id"])
        if not exam_ids:
            return jsonify({"success": True, "exams": []})
        placeholders = ", ".join(["%s"] * len(exam_ids))
        exams = fetch_all(
            f"""
            SELECT e.*, s.name AS subject_name, s.code AS subject_code
            FROM exams e
            LEFT JOIN subjects s ON s.id = e.subject_id
            WHERE e.id IN ({placeholders})
            ORDER BY e.date_value DESC, e.start_time DESC
            """,
            tuple(exam_ids),
        )
    else:
        exams = fetch_all(
            """
            SELECT e.*, s.name AS subject_name, s.code AS subject_code
            FROM exams e
            LEFT JOIN subjects s ON s.id = e.subject_id
            ORDER BY e.date_value DESC, e.start_time DESC
            """
        )
    return jsonify({"success": True, "exams": [serialize_exam(exam) for exam in exams]})


@bp.route("/api/exams", methods=["POST"])
@login_required
@role_required("ADMIN")
def create_exam():
    payload = request.get_json(silent=True) or {}
    values, error = validate_exam_payload(payload)
    if error:
        status_code = 409 if error == "That exam code is already in use." else 400
        return jsonify({"success": False, "message": error}), status_code
    try:
        exam_id = execute(
            """
            INSERT INTO exams
                (name, exam_code, subject_id, date_value, start_time, end_time, duration_minutes, status, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """,
            (
                values["name"],
                values["exam_code"],
                values["subject_id"],
                values["date_value"],
                values["start_time"],
                values["end_time"],
                values["duration_minutes"],
                values["status"],
            ),
        )
    except (IntegrityError, sqlite3.IntegrityError) as error:
        if is_duplicate_exam_code_error(error):
            return jsonify({"success": False, "message": "That exam code is already in use."}), 409
        raise
    return jsonify({"success": True, "message": "Exam created successfully.", "id": exam_id})


@bp.route("/api/exams/<int:exam_id>", methods=["PUT"])
@login_required
@role_required("ADMIN")
def update_exam(exam_id):
    payload = request.get_json(silent=True) or {}
    if not fetch_one("SELECT id FROM exams WHERE id = %s", (exam_id,)):
        return jsonify({"success": False, "message": "Exam not found."}), 404
    values, error = validate_exam_payload(payload, exam_id)
    if error:
        status_code = 409 if error == "That exam code is already in use." else 400
        return jsonify({"success": False, "message": error}), status_code
    try:
        execute(
            """
            UPDATE exams
            SET name = %s, exam_code = %s, subject_id = %s, date_value = %s,
                start_time = %s, end_time = %s, duration_minutes = %s, status = %s,
                updated_at = NOW()
            WHERE id = %s
            """,
            (
                values["name"],
                values["exam_code"],
                values["subject_id"],
                values["date_value"],
                values["start_time"],
                values["end_time"],
                values["duration_minutes"],
                values["status"],
                exam_id,
            ),
        )
    except (IntegrityError, sqlite3.IntegrityError) as error:
        if is_duplicate_exam_code_error(error):
            return jsonify({"success": False, "message": "That exam code is already in use."}), 409
        raise
    return jsonify({"success": True, "message": "Exam updated successfully."})


@bp.route("/api/exams/<int:exam_id>", methods=["DELETE"])
@login_required
@role_required("ADMIN")
def delete_exam(exam_id):
    if not fetch_one("SELECT id FROM exams WHERE id = %s", (exam_id,)):
        return jsonify({"success": False, "message": "Exam not found."}), 404
    dependencies = (
        ("exam_students", "exam_id"),
        ("timetable", "exam_id"),
        ("invigilators", "exam_id"),
        ("seating_arrangements", "exam_id"),
        ("attendance", "exam_id"),
    )
    for table, field in dependencies:
        if fetch_one(f"SELECT id FROM {table} WHERE {field} = %s LIMIT 1", (exam_id,)):
            return jsonify({
                "success": False,
                "message": "This exam is linked to other records and cannot be deleted. Remove or update those links first.",
            }), 409
    execute("DELETE FROM exams WHERE id = %s", (exam_id,))
    return jsonify({"success": True, "message": "Exam deleted successfully."})
