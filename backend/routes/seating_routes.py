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
from backend.services.seating_service import (
    generate_exam_arrangement,
    move_student_assignment,
    publish_arrangement,
    swap_student_assignments,
    validate_arrangement_for_db,
)

bp = Blueprint("seating_routes", __name__)


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


@bp.route("/api/seating/generate", methods=["POST"])
@login_required
@role_required("ADMIN", "TEACHER")
def generate_seating():
    payload = request.get_json(silent=True) or {}
    exam_id = payload.get("exam_id")
    room_ids = payload.get("room_ids") or []
    if get_current_user().get("role") == "TEACHER":
        teacher = get_current_teacher()
        if not teacher:
            return jsonify({"success": False, "message": "Teacher profile is not linked to this account."}), 403
        try:
            permitted_exam_ids = get_teacher_exam_ids(teacher["id"])
            if int(exam_id) not in permitted_exam_ids:
                return jsonify({"success": False, "message": "You are not assigned to this exam."}), 403
        except (TypeError, ValueError):
            return jsonify({"success": False, "message": "A valid exam ID is required."}), 400
    try:
        result = generate_exam_arrangement(exam_id, room_ids)
        return jsonify({"success": True, "result": result})
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400


@bp.route("/api/seating/validate", methods=["POST"])
@login_required
@role_required("ADMIN", "TEACHER")
def validate_seating():
    payload = request.get_json(silent=True) or {}
    arrangement_id = payload.get("arrangement_id")
    if not arrangement_id:
        return jsonify({"success": False, "message": "Arrangement ID is required."}), 400
    if get_current_user().get("role") == "TEACHER":
        teacher = get_current_teacher()
        if not teacher:
            return jsonify({"success": False, "message": "Teacher profile is not linked to this account."}), 403
        arrangement = fetch_one(
            "SELECT exam_id FROM seating_arrangements WHERE id = %s",
            (arrangement_id,),
        )
        if not arrangement or arrangement["exam_id"] not in get_teacher_exam_ids(teacher["id"]):
            return jsonify({"success": False, "message": "You are not assigned to this exam."}), 403
    result = validate_arrangement_for_db(arrangement_id)
    return jsonify({"success": result["valid"], "message": result["message"]})


@bp.route("/api/seating/publish", methods=["POST"])
@login_required
@role_required("ADMIN")
def publish_seating():
    payload = request.get_json(silent=True) or {}
    arrangement_id = payload.get("arrangement_id")
    if not arrangement_id:
        return jsonify({"success": False, "message": "Arrangement ID is required."}), 400
    try:
        result = publish_arrangement(arrangement_id)
        return jsonify({"success": True, "message": result["message"]})
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400


@bp.route("/api/seating/lock", methods=["POST"])
@login_required
@role_required("ADMIN")
def lock_seating():
    payload = request.get_json(silent=True) or {}
    arrangement_id = payload.get("arrangement_id")
    if not arrangement_id:
        return jsonify({"success": False, "message": "Arrangement ID is required."}), 400
    execute("UPDATE seating_arrangements SET status = 'LOCKED', updated_at = NOW() WHERE id = %s", (arrangement_id,))
    return jsonify({"success": True, "message": "Arrangement locked successfully."})


@bp.route("/api/seating/swap", methods=["POST"])
@login_required
@role_required("ADMIN")
def swap_students():
    payload = request.get_json(silent=True) or {}
    arrangement_id = payload.get("arrangement_id")
    first_student_id = payload.get("first_student_id")
    second_student_id = payload.get("second_student_id")
    if not all([arrangement_id, first_student_id, second_student_id]):
        return jsonify({
            "success": False,
            "message": "Arrangement ID and two student IDs are required.",
        }), 400
    try:
        swap_student_assignments(
            arrangement_id,
            first_student_id,
            second_student_id,
        )
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400
    return jsonify({"success": True, "message": "Seat swap updated successfully."})


@bp.route("/api/seating/move", methods=["POST"])
@login_required
@role_required("ADMIN")
def move_student():
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return jsonify({"success": False, "message": "Valid assignment, room, and seat details are required."}), 400
    assignment_id = _parse_positive_id(payload.get("assignment_id"))
    room_id = _parse_positive_id(payload.get("room_id"))
    seat_number = payload.get("seat_number")
    if not assignment_id or not room_id or not isinstance(seat_number, str) or not seat_number.strip():
        return jsonify({
            "success": False,
            "message": "Valid assignment ID, room ID, and seat number are required.",
        }), 400

    result = move_student_assignment(assignment_id, room_id, seat_number)
    errors = {
        "assignment_not_found": ("Seat assignment not found.", 404),
        "arrangement_locked": ("The seating arrangement is locked.", 409),
        "room_not_found": ("Room not found.", 404),
        "room_inactive": ("The target room is not active.", 400),
        "invalid_seat": ("The target seat does not exist in this room.", 400),
        "seat_unavailable": ("The target seat is blocked, reserved, or unavailable.", 409),
        "seat_occupied": ("The target seat is already occupied in this arrangement.", 409),
    }
    if result in errors:
        message, status_code = errors[result]
        return jsonify({"success": False, "message": message}), status_code
    return jsonify({"success": True, "message": "Student moved successfully."})


@bp.route("/api/seating", methods=["GET"])
@login_required
@role_required("ADMIN", "TEACHER", "STUDENT")
def get_seating_data():
    exam_id = request.args.get("exam_id")
    role = get_current_user().get("role")
    if role == "STUDENT":
        student = get_current_student()
        if not student:
            return jsonify({"success": False, "message": "Student profile is not linked to this account."}), 403

        query = """
            SELECT sa.id AS assignment_id, sa.arrangement_id, arr.exam_id,
                arr.status, sa.room_id, r.room_number, sa.seat_number,
                e.name AS exam_name, e.exam_code, e.date_value
            FROM seat_assignments sa
            INNER JOIN seating_arrangements arr ON arr.id = sa.arrangement_id
            INNER JOIN exams e ON e.id = arr.exam_id
            LEFT JOIN rooms r ON r.id = sa.room_id
            WHERE sa.student_id = %s AND arr.status = 'PUBLISHED'
        """
        params = [student["id"]]
        if exam_id:
            query += " AND arr.exam_id = %s"
            params.append(exam_id)
        query += " ORDER BY e.date_value DESC, arr.id DESC"
        return jsonify({"success": True, "arrangements": fetch_all(query, tuple(params))})

    if role == "TEACHER":
        teacher = get_current_teacher()
        if not teacher:
            return jsonify({"success": False, "message": "Teacher profile is not linked to this account."}), 403
        exam_ids = get_teacher_exam_ids(teacher["id"])
        if not exam_ids:
            return jsonify({"success": True, "arrangements": []})
        if exam_id and str(exam_id) not in {str(value) for value in exam_ids}:
            return jsonify({"success": False, "message": "You are not assigned to this exam."}), 403
        placeholders = ", ".join(["%s"] * len(exam_ids))
        rows = fetch_all(
            f"""
            SELECT * FROM seating_arrangements
            WHERE exam_id IN ({placeholders})
            ORDER BY id DESC
            """,
            tuple(exam_ids),
        )
        assignments = fetch_all(
            f"""
            SELECT arr.id AS arrangement_id, arr.exam_id, arr.status,
                e.name AS exam_name, e.exam_code, e.date_value,
                sa.student_id, s.name AS student_name, s.roll_no,
                sa.room_id, r.room_number, sa.row_no, sa.column_no,
                sa.seat_number, sa.status AS assignment_status
            FROM seating_arrangements arr
            INNER JOIN seat_assignments sa ON sa.arrangement_id = arr.id
            INNER JOIN students s ON s.id = sa.student_id
            INNER JOIN exams e ON e.id = arr.exam_id
            LEFT JOIN rooms r ON r.id = sa.room_id
            WHERE arr.exam_id IN ({placeholders})
            ORDER BY e.date_value, arr.id, sa.row_no, sa.column_no
            """,
            tuple(exam_ids),
        )
        if exam_id:
            rows = [row for row in rows if str(row["exam_id"]) == str(exam_id)]
            assignments = [
                row for row in assignments if str(row["exam_id"]) == str(exam_id)
            ]
        return jsonify({
            "success": True,
            "arrangements": rows,
            "assignments": assignments,
        })

    rows = fetch_all("SELECT * FROM seating_arrangements WHERE exam_id = %s ORDER BY id DESC", (exam_id,)) if exam_id else fetch_all("SELECT * FROM seating_arrangements ORDER BY id DESC")
    return jsonify({"success": True, "arrangements": rows})
