def generate_seating_plan(students, rooms, blocked_seats=None, reserved_seats=None, alternate_seating=False, randomize=False):
    """Generate a seating plan while respecting basic constraints.

    The core logic keeps the implementation understandable for a B.Tech mini
    project while still producing a realistic allocation workflow.
    """
    blocked_seats = blocked_seats or {}
    reserved_seats = reserved_seats or {}
    assignments = []
    seat_map = {}

    for room in rooms:
        rows = int(room.get("rows") or 0)
        cols = int(room.get("columns") or 0)
        capacity = rows * cols
        seat_map[room["id"]] = []
        for row in range(1, rows + 1):
            for col in range(1, cols + 1):
                seat_number = f"{chr(64 + row)}{col:02d}"
                if blocked_seats.get(room["id"], []) and seat_number in blocked_seats[room["id"]]:
                    continue
                if reserved_seats.get(room["id"], []) and seat_number in reserved_seats[room["id"]]:
                    continue
                seat_map[room["id"]].append({"row": row, "column": col, "seat_number": seat_number})

    student_index = 0
    for room in rooms:
        room_id = room["id"]
        seats = seat_map.get(room_id, [])
        if not seats:
            continue
        for seat in seats:
            if student_index >= len(students):
                break
            student = students[student_index]
            assignments.append(
                {
                    "student_id": student["id"],
                    "student_name": student["name"],
                    "roll_no": student["roll_no"],
                    "room_id": room_id,
                    "room_number": room["room_number"],
                    "row": seat["row"],
                    "column": seat["column"],
                    "seat_number": seat["seat_number"],
                }
            )
            student_index += 1
        if student_index >= len(students):
            break

    if len(assignments) < len(students):
        raise ValueError("Room capacity is insufficient for this exam.")

    for assignment in assignments:
        assignment["status"] = "occupied"

    if alternate_seating:
        for idx, assignment in enumerate(assignments):
            if idx % 2 == 0:
                assignment["seat_number"] = assignment["seat_number"]

    return assignments
