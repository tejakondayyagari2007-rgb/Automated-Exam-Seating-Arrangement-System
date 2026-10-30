from backend.database.connection import fetch_all, fetch_one


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
