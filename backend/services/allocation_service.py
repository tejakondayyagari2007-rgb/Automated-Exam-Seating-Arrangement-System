from mysql.connector import IntegrityError

from backend.database.connection import execute, fetch_all, fetch_one


def get_exam_roster(exam_id):
    if not fetch_one("SELECT id FROM exams WHERE id = %s", (exam_id,)):
        return None

    allocated_students = fetch_all(
        """
        SELECT s.id, s.roll_no, s.name, s.email
        FROM exam_students es
        INNER JOIN students s ON s.id = es.student_id
        WHERE es.exam_id = %s
        ORDER BY s.roll_no
        """,
        (exam_id,),
    )
    available_students = fetch_all(
        """
        SELECT s.id, s.roll_no, s.name, s.email
        FROM students s
        WHERE NOT EXISTS (
            SELECT 1 FROM exam_students es
            WHERE es.exam_id = %s AND es.student_id = s.id
        )
        ORDER BY s.roll_no
        """,
        (exam_id,),
    )
    return {
        "allocated_students": allocated_students,
        "available_students": available_students,
    }


def allocate_student_to_exam(exam_id, student_id):
    if not fetch_one("SELECT id FROM exams WHERE id = %s", (exam_id,)):
        return "exam_not_found"
    if not fetch_one("SELECT id FROM students WHERE id = %s", (student_id,)):
        return "student_not_found"
    if fetch_one(
        "SELECT id FROM exam_students WHERE exam_id = %s AND student_id = %s",
        (exam_id, student_id),
    ):
        return "already_allocated"

    try:
        execute(
            """
            INSERT INTO exam_students (exam_id, student_id)
            VALUES (%s, %s)
            """,
            (exam_id, student_id),
        )
    except IntegrityError as error:
        if error.errno == 1062:
            return "already_allocated"
        raise
    return "allocated"


def remove_student_from_exam(exam_id, student_id):
    if not fetch_one("SELECT id FROM exams WHERE id = %s", (exam_id,)):
        return "exam_not_found"
    if not fetch_one("SELECT id FROM students WHERE id = %s", (student_id,)):
        return "student_not_found"
    if not fetch_one(
        "SELECT id FROM exam_students WHERE exam_id = %s AND student_id = %s",
        (exam_id, student_id),
    ):
        return "allocation_not_found"

    execute(
        "DELETE FROM exam_students WHERE exam_id = %s AND student_id = %s",
        (exam_id, student_id),
    )
    return "removed"


def get_timetable():
    query = """
        SELECT t.*, e.name AS exam_name, s.name AS subject_name, r.room_number, inv.name AS invigilator_name
        FROM timetable t
        LEFT JOIN exams e ON e.id = t.exam_id
        LEFT JOIN subjects s ON s.id = e.subject_id
        LEFT JOIN rooms r ON r.id = t.room_id
        LEFT JOIN teachers inv ON inv.id = t.invigilator_id
    """
    return fetch_all(query)


def create_timetable_entry(exam_id, room_id, invigilator_id, date_value, start_time, end_time):
    return fetch_one(
        """
        INSERT INTO timetable (exam_id, room_id, invigilator_id, exam_date, start_time, end_time, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
        """,
        (exam_id, room_id, invigilator_id, date_value, start_time, end_time),
    )
