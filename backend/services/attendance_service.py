from backend.database.connection import execute, fetch_all, fetch_one


def get_attendance_rows(exam_id=None, permitted_exam_ids=None):
    if permitted_exam_ids is not None:
        if not permitted_exam_ids:
            return []
        placeholders = ", ".join(["%s"] * len(permitted_exam_ids))
        return fetch_all(
            f"""
            SELECT a.*, s.name, s.roll_no, e.name AS exam_name
            FROM attendance a
            LEFT JOIN students s ON s.id = a.student_id
            LEFT JOIN exams e ON e.id = a.exam_id
            WHERE a.exam_id IN ({placeholders})
            ORDER BY a.id DESC
            """,
            tuple(permitted_exam_ids),
        )
    if exam_id:
        return fetch_all(
            """
            SELECT a.*, s.name, s.roll_no, e.name AS exam_name
            FROM attendance a
            LEFT JOIN students s ON s.id = a.student_id
            LEFT JOIN exams e ON e.id = a.exam_id
            WHERE a.exam_id = %s
            """,
            (exam_id,),
        )
    return fetch_all(
        """
        SELECT a.*, s.name, s.roll_no, e.name AS exam_name
        FROM attendance a
        LEFT JOIN students s ON s.id = a.student_id
        LEFT JOIN exams e ON e.id = a.exam_id
        ORDER BY a.id DESC
        """
    )


def mark_attendance(student_id, exam_id, present_status):
    existing = fetch_one("SELECT * FROM attendance WHERE student_id = %s AND exam_id = %s", (student_id, exam_id))
    if existing:
        execute(
            "UPDATE attendance SET present_status = %s, updated_at = NOW() WHERE id = %s",
            (present_status, existing["id"]),
        )
        return existing["id"]
    return execute(
        "INSERT INTO attendance (student_id, exam_id, present_status, created_at, updated_at) VALUES (%s, %s, %s, NOW(), NOW())",
        (student_id, exam_id, present_status),
    )
