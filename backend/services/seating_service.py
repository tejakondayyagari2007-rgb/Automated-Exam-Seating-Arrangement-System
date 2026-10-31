from contextlib import contextmanager

from backend.algorithms.constraint_checker import validate_arrangement
from backend.algorithms.quality_score import quality_score_from_assignments
from backend.database.connection import execute, fetch_all, fetch_one, get_db


@contextmanager
def _transaction():
    connection = get_db()
    if connection.__class__.__module__.startswith("mysql"):
        connection.start_transaction()
    else:
        connection.execute("BEGIN")

    try:
        yield
        connection.commit()
    except Exception:
        connection.rollback()
        raise


def build_exam_assignments(students, rooms, unavailable_seats):
    if not students:
        raise ValueError("No students are registered for this exam.")
    if not rooms:
        raise ValueError("No active rooms available for this exam.")

    available_seats = []
    for room in rooms:
        room_id = room["id"]
        row_count = int(room.get("rows") or 0)
        column_count = int(room.get("columns") or 0)
        capacity = int(room.get("capacity") or 0)
        if row_count <= 0 or column_count <= 0 or capacity != row_count * column_count:
            raise ValueError(f"Room {room.get('room_number', room_id)} has an invalid seat layout.")

        physical_seats = {
            f"{chr(64 + row)}{column:02d}": (row, column)
            for row in range(1, row_count + 1)
            for column in range(1, column_count + 1)
        }
        unavailable = unavailable_seats.get(room_id, {})
        invalid_labels = set(unavailable) - set(physical_seats)
        if invalid_labels:
            raise ValueError(f"Room {room.get('room_number', room_id)} has invalid seat records.")
        available_seats.extend(
            (room, seat_number, position)
            for seat_number, position in physical_seats.items()
            if unavailable.get(seat_number, "available") == "available"
        )

    if len(available_seats) < len(students):
        raise ValueError(
            f"Available room capacity ({len(available_seats)}) is insufficient "
            f"for the exam roster ({len(students)})."
        )

    multiple_rooms = len(rooms) > 1
    assignments = []
    seen_seats = set()
    for student, (room, local_seat, (row, column)) in zip(students, available_seats):
        seat_number = (
            f"{room['room_number']}-{local_seat}" if multiple_rooms else local_seat
        )
        seat_key = (room["id"], seat_number)
        if seat_key in seen_seats:
            raise ValueError("Duplicate seat assignment detected.")
        seen_seats.add(seat_key)
        assignments.append(
            {
                "student_id": student["id"],
                "room_id": room["id"],
                "room_number": room.get("room_number", room["id"]),
                "row": row,
                "column": column,
                "seat_number": seat_number,
                "student_name": student["name"],
                "roll_no": student["roll_no"],
            }
        )

    validation = validate_arrangement(assignments)
    if not validation["valid"]:
        raise ValueError(validation["message"])
    return assignments


def generate_exam_arrangement(exam_id, room_ids=None):
    exam = fetch_one(
        "SELECT id, date_value, start_time, end_time FROM exams WHERE id = %s",
        (exam_id,),
    )
    if not exam:
        raise ValueError("Exam not found.")
    if not all(exam.get(field) is not None for field in ("date_value", "start_time", "end_time")):
        raise ValueError("The exam is missing its scheduled date or time.")

    students = fetch_all(
        """
        SELECT s.id, s.name, s.roll_no, s.status
        FROM exam_students es
        INNER JOIN students s ON s.id = es.student_id
        WHERE es.exam_id = %s
        ORDER BY s.id
        """,
        (exam_id,),
    )
    if any(student.get("status") != "active" for student in students):
        raise ValueError("The exam roster contains inactive students.")

    if room_ids is not None and not isinstance(room_ids, (list, tuple)):
        raise ValueError("Room IDs must be provided as a list.")
    try:
        selected_room_ids = [int(room_id) for room_id in (room_ids or [])]
    except (TypeError, ValueError):
        raise ValueError("Room IDs must be positive integers.") from None
    if any(room_id <= 0 for room_id in selected_room_ids):
        raise ValueError("Room IDs must be positive integers.")
    if len(set(selected_room_ids)) != len(selected_room_ids):
        raise ValueError("A room may only be selected once.")

    booked_rooms = fetch_all(
        """
        SELECT DISTINCT room_id
        FROM timetable
        WHERE exam_date = %s AND exam_id != %s
            AND start_time < %s AND end_time > %s
        """,
        (
            exam["date_value"],
            exam_id,
            exam["end_time"],
            exam["start_time"],
        ),
    )
    booked_room_ids = {row["room_id"] for row in booked_rooms}
    if selected_room_ids and booked_room_ids.intersection(selected_room_ids):
        raise ValueError("A selected room is booked for an overlapping exam.")

    room_query = "SELECT * FROM rooms WHERE status = 'active'"
    room_params = ()
    if selected_room_ids:
        placeholders = ", ".join(["%s"] * len(selected_room_ids))
        room_query += f" AND id IN ({placeholders})"
        room_params = tuple(selected_room_ids)
    room_query += " ORDER BY id"
    rooms = fetch_all(room_query, room_params)
    if selected_room_ids and len(rooms) != len(selected_room_ids):
        raise ValueError("One or more selected rooms are unavailable.")
    rooms = [room for room in rooms if room["id"] not in booked_room_ids]

    unavailable_seats = {}
    if rooms:
        placeholders = ", ".join(["%s"] * len(rooms))
        room_ids_for_query = tuple(room["id"] for room in rooms)
        seat_rows = fetch_all(
            f"""
            SELECT room_id, seat_number, status
            FROM room_seats
            WHERE room_id IN ({placeholders})
            """,
            room_ids_for_query,
        )
        for seat in seat_rows:
            status = str(seat.get("status") or "").strip().lower()
            if status != "available":
                unavailable_seats.setdefault(seat["room_id"], {})[
                    seat["seat_number"]
                ] = status

    assignments = build_exam_assignments(students, rooms, unavailable_seats)
    result = validate_arrangement(assignments, exam_id=exam_id)
    if not result["valid"]:
        raise ValueError(result["message"])

    score = quality_score_from_assignments(assignments)
    with _transaction():
        arrangement_id = execute(
            """
            INSERT INTO seating_arrangements (exam_id, status, quality_score, created_at, updated_at)
            VALUES (%s, 'GENERATED', %s, NOW(), NOW())
            """,
            (exam_id, score),
        )
        for assignment in assignments:
            execute(
                """
                INSERT INTO seat_assignments
                    (arrangement_id, student_id, room_id, row_no, column_no,
                     seat_number, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
                """,
                (
                    arrangement_id,
                    assignment["student_id"],
                    assignment["room_id"],
                    assignment["row"],
                    assignment["column"],
                    assignment["seat_number"],
                ),
            )

    return {
        "arrangement_id": arrangement_id,
        "assignments": assignments,
        "quality_score": score,
    }


def move_student_assignment(assignment_id, room_id, seat_number):
    assignment = fetch_one(
        """
        SELECT sa.id, sa.arrangement_id, sa.room_id, arr.status AS arrangement_status
        FROM seat_assignments sa
        INNER JOIN seating_arrangements arr ON arr.id = sa.arrangement_id
        WHERE sa.id = %s
        """,
        (assignment_id,),
    )
    if not assignment:
        return "assignment_not_found"
    if assignment["arrangement_status"] == "LOCKED":
        return "arrangement_locked"

    room = fetch_one(
        "SELECT id, room_number, `rows`, `columns`, status FROM rooms WHERE id = %s",
        (room_id,),
    )
    if not room:
        return "room_not_found"
    if str(room.get("status") or "").strip().lower() != "active":
        return "room_inactive"

    seat_number = seat_number.strip()
    room_prefix = f"{room['room_number']}-"
    local_seat_number = (
        seat_number[len(room_prefix):]
        if seat_number.startswith(room_prefix)
        else seat_number
    )
    row_count = int(room.get("rows") or 0)
    column_count = int(room.get("columns") or 0)
    seat_position = next(
        (
            (row, column)
            for row in range(1, row_count + 1)
            for column in range(1, column_count + 1)
            if f"{chr(64 + row)}{column:02d}" == local_seat_number
        ),
        None,
    )
    if not seat_position:
        return "invalid_seat"

    seat = fetch_one(
        """
        SELECT row_no, column_no, status
        FROM room_seats
        WHERE room_id = %s AND seat_number = %s
        """,
        (room_id, local_seat_number),
    )
    if seat and str(seat.get("status") or "").strip().lower() != "available":
        return "seat_unavailable"

    row_no, column_no = seat_position
    if seat:
        if (
            seat.get("row_no") is not None
            and seat["row_no"] != row_no
        ) or (
            seat.get("column_no") is not None
            and seat["column_no"] != column_no
        ):
            return "invalid_seat"

    room_count = fetch_one(
        """
        SELECT COUNT(DISTINCT room_id) AS room_count
        FROM seat_assignments
        WHERE arrangement_id = %s
        """,
        (assignment["arrangement_id"],),
    )
    stored_seat_number = (
        f"{room['room_number']}-{local_seat_number}"
        if room_count["room_count"] > 1 or room_id != assignment["room_id"]
        else local_seat_number
    )
    occupied = fetch_one(
        """
        SELECT id FROM seat_assignments
        WHERE arrangement_id = %s AND room_id = %s AND id != %s
            AND (seat_number = %s OR (row_no = %s AND column_no = %s))
        LIMIT 1
        """,
        (
            assignment["arrangement_id"],
            room_id,
            assignment_id,
            stored_seat_number,
            row_no,
            column_no,
        ),
    )
    if occupied:
        return "seat_occupied"

    execute(
        """
        UPDATE seat_assignments
        SET room_id = %s, seat_number = %s, row_no = %s, column_no = %s,
            updated_at = NOW()
        WHERE id = %s
        """,
        (room_id, stored_seat_number, row_no, column_no, assignment_id),
    )
    return "moved"


def swap_student_assignments(arrangement_id, first_student_id, second_student_id):
    if first_student_id == second_student_id:
        raise ValueError("Choose two different students to swap.")

    with _transaction():
        arrangement = fetch_one(
            "SELECT id, status FROM seating_arrangements WHERE id = %s",
            (arrangement_id,),
        )
        if not arrangement:
            raise ValueError("Arrangement not found.")
        if arrangement["status"] == "LOCKED":
            raise ValueError("The seating arrangement is locked.")

        first = fetch_one(
            """
            SELECT id, room_id, row_no, column_no, seat_number
            FROM seat_assignments
            WHERE arrangement_id = %s AND student_id = %s
            """,
            (arrangement_id, first_student_id),
        )
        second = fetch_one(
            """
            SELECT id, room_id, row_no, column_no, seat_number
            FROM seat_assignments
            WHERE arrangement_id = %s AND student_id = %s
            """,
            (arrangement_id, second_student_id),
        )
        if not first or not second:
            raise ValueError("Both students must have seats in this arrangement.")

        execute(
            """
            UPDATE seat_assignments
            SET seat_number = %s
            WHERE id = %s
            """,
            (f"__sw_{first['id']}", first["id"]),
        )
        execute(
            """
            UPDATE seat_assignments
            SET room_id = %s, row_no = %s, column_no = %s, seat_number = %s,
                updated_at = NOW()
            WHERE id = %s
            """,
            (
                first["room_id"],
                first["row_no"],
                first["column_no"],
                first["seat_number"],
                second["id"],
            ),
        )
        execute(
            """
            UPDATE seat_assignments
            SET room_id = %s, row_no = %s, column_no = %s, seat_number = %s,
                updated_at = NOW()
            WHERE id = %s
            """,
            (
                second["room_id"],
                second["row_no"],
                second["column_no"],
                second["seat_number"],
                first["id"],
            ),
        )


def list_arrangements_for_exam(exam_id):
    return fetch_all(
        "SELECT * FROM seating_arrangements WHERE exam_id = %s ORDER BY created_at DESC",
        (exam_id,),
    )


def publish_arrangement(arrangement_id):
    arrangement = fetch_one(
        "SELECT * FROM seating_arrangements WHERE id = %s",
        (arrangement_id,),
    )
    if not arrangement:
        raise ValueError("Arrangement not found.")
    validation = validate_arrangement_for_db(arrangement_id)
    if not validation["valid"]:
        raise ValueError(validation["message"])
    execute(
        "UPDATE seating_arrangements SET status = 'PUBLISHED', updated_at = NOW() WHERE id = %s",
        (arrangement_id,),
    )
    return {"success": True, "message": "Seating arrangement published."}


def validate_arrangement_for_db(arrangement_id):
    arrangement = fetch_one(
        "SELECT id, exam_id FROM seating_arrangements WHERE id = %s",
        (arrangement_id,),
    )
    if not arrangement:
        return {"valid": False, "message": "Arrangement not found."}

    assignments = fetch_all(
        """
        SELECT sa.*, s.name AS student_name, s.roll_no
        FROM seat_assignments sa
        LEFT JOIN students s ON s.id = sa.student_id
        WHERE sa.arrangement_id = %s
        """,
        (arrangement_id,),
    )
    validation = validate_arrangement(assignments, arrangement_id=arrangement_id)
    if not validation["valid"]:
        return validation

    candidates = fetch_all(
        """
        SELECT es.student_id, s.status
        FROM exam_students es
        INNER JOIN students s ON s.id = es.student_id
        WHERE es.exam_id = %s
        """,
        (arrangement["exam_id"],),
    )
    if not candidates or any(candidate["status"] != "active" for candidate in candidates):
        return {
            "valid": False,
            "message": "The exam must have registered active candidates before publishing.",
        }
    expected_ids = {row["student_id"] for row in candidates}
    assigned_ids = [row["student_id"] for row in assignments]
    if len(assigned_ids) != len(expected_ids) or set(assigned_ids) != expected_ids:
        return {
            "valid": False,
            "message": "The arrangement must include each registered exam candidate exactly once.",
        }
    return validation
