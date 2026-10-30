from backend.database.connection import fetch_all


def get_reports(exam_ids=None):
    if exam_ids is not None and not exam_ids:
        return {
            "student_seating": [],
            "room_seating": [],
            "exam_summary": [],
            "attendance_summary": [],
        }

    filter_clause = ""
    params = ()
    if exam_ids is not None:
        placeholders = ", ".join(["%s"] * len(exam_ids))
        filter_clause = f" WHERE arr.exam_id IN ({placeholders})"
        params = tuple(exam_ids)

    reports = {
        "student_seating": fetch_all("""
            SELECT sa.student_id, s.roll_no, s.name, sa.room_id, r.room_number,
                sa.seat_number, e.name AS exam_name, e.exam_code,
                arr.status AS arrangement_status
            FROM seat_assignments sa
            LEFT JOIN students s ON s.id = sa.student_id
            LEFT JOIN rooms r ON r.id = sa.room_id
            LEFT JOIN seating_arrangements arr ON arr.id = sa.arrangement_id
            LEFT JOIN exams e ON e.id = arr.exam_id
        """ + filter_clause + " ORDER BY e.date_value, e.id, sa.row_no, sa.column_no", params),
        "room_seating": fetch_all("""
            SELECT e.name AS exam_name, e.exam_code, e.date_value,
                r.room_number, COUNT(sa.id) AS assigned_students, r.capacity
            FROM rooms r
            INNER JOIN seat_assignments sa ON sa.room_id = r.id
            INNER JOIN seating_arrangements arr ON arr.id = sa.arrangement_id
            INNER JOIN exams e ON e.id = arr.exam_id
        """ + filter_clause + """
            GROUP BY e.id, e.name, e.exam_code, e.date_value,
                r.id, r.room_number, r.capacity
            ORDER BY e.date_value, e.id, r.room_number
        """, params),
        "exam_summary": fetch_all("""
            SELECT e.id AS exam_id, e.name AS exam_name, e.exam_code,
                e.date_value,
                (SELECT COUNT(*) FROM exam_students es
                 WHERE es.exam_id = e.id) AS registered_students,
                (SELECT COUNT(DISTINCT sa.student_id)
                 FROM seating_arrangements arr
                 INNER JOIN seat_assignments sa ON sa.arrangement_id = arr.id
                 WHERE arr.exam_id = e.id) AS students_assigned,
                (SELECT COUNT(*) FROM seating_arrangements arr
                 WHERE arr.exam_id = e.id) AS arrangement_count
            FROM exams e
        """ + (
            f" WHERE e.id IN ({', '.join(['%s'] * len(exam_ids))})"
            if exam_ids is not None else ""
        ) + """
            ORDER BY e.date_value, e.start_time, e.id
        """, params),
        "attendance_summary": fetch_all("""
            SELECT e.name AS exam_name,
                   SUM(CASE WHEN a.present_status = 1 THEN 1 ELSE 0 END) AS present,
                   SUM(CASE WHEN a.present_status = 0 THEN 1 ELSE 0 END) AS absent,
                   SUM(CASE WHEN a.remarks LIKE 'DEMO ONLY%' THEN 1 ELSE 0 END) AS demo_records
            FROM exams e
            LEFT JOIN attendance a ON a.exam_id = e.id
        """ + (
            f" WHERE e.id IN ({', '.join(['%s'] * len(exam_ids))})"
            if exam_ids is not None else ""
        ) + """
            GROUP BY e.id
        """, params),
    }
    return reports
