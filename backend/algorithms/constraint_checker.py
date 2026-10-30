def validate_arrangement(assignments, exam_id=None, arrangement_id=None):
    seen_students = set()
    seen_seats = set()
    errors = []
    for item in assignments:
        student_id = item.get("student_id") or item.get("id")
        seat_key = f"{item.get('room_id')}-{item.get('seat_number') or item.get('row')}-{item.get('column')}"
        if student_id in seen_students:
            errors.append("Duplicate student assignment detected.")
        if seat_key in seen_seats:
            errors.append("Duplicate seat assignment detected.")
        seen_students.add(student_id)
        seen_seats.add(seat_key)

    if errors:
        return {"valid": False, "message": " ; ".join(errors)}
    return {"valid": True, "message": "Arrangement validation passed."}
