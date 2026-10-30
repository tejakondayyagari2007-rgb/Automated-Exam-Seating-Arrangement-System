from backend.database.connection import fetch_one
from backend.utils.security import verify_password


def authenticate_user(username: str, password: str):
    query = """
        SELECT * FROM users
        WHERE (username = %s OR email = %s)
        LIMIT 1
    """
    if not username or not password:
        return None
    user = fetch_one(query, (username, username))
    if not user:
        return None
    if verify_password(password, user.get("password_hash") or ""):
        return user
    return None


def get_user_by_id(user_id):
    return fetch_one("SELECT * FROM users WHERE id = %s", (user_id,))


def get_dashboard_stats():
    from backend.database.connection import fetch_one

    stats = {
        "total_students": 0,
        "total_teachers": 0,
        "total_rooms": 0,
        "total_seats": 0,
        "available_seats": 0,
        "total_exams": 0,
        "upcoming_exams": 0,
        "published_arrangements": 0,
        "attendance_percentage": 0,
    }
    stats["total_students"] = fetch_one("SELECT COUNT(*) AS value FROM students")["value"]
    stats["total_teachers"] = fetch_one("SELECT COUNT(*) AS value FROM teachers")["value"]
    stats["total_rooms"] = fetch_one("SELECT COUNT(*) AS value FROM rooms")["value"]
    stats["total_seats"] = fetch_one("SELECT COALESCE(SUM(capacity), 0) AS value FROM rooms")["value"]
    stats["available_seats"] = fetch_one("SELECT COALESCE(SUM(capacity), 0) AS value FROM rooms WHERE status = 'active'")["value"]
    stats["total_exams"] = fetch_one("SELECT COUNT(*) AS value FROM exams")["value"]
    stats["upcoming_exams"] = fetch_one("SELECT COUNT(*) AS value FROM exams WHERE status = 'Upcoming'")["value"]
    stats["published_arrangements"] = fetch_one("SELECT COUNT(*) AS value FROM seating_arrangements WHERE status = 'PUBLISHED'")["value"]
    attendance = fetch_one("SELECT AVG(present_status) * 100 AS value FROM attendance WHERE present_status IS NOT NULL")
    stats["attendance_percentage"] = int(attendance["value"] or 0) if attendance else 0
    return stats
