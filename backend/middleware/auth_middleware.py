from functools import wraps

from flask import jsonify, redirect, request, session


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"success": False, "message": "Authentication required."}), 401
            return redirect("/login")
        return view_func(*args, **kwargs)

    return wrapper


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            user = session.get("user")
            if not user:
                if request.path.startswith("/api/"):
                    return jsonify({"success": False, "message": "Authentication required."}), 401
                return redirect("/login")
            if user.get("role") not in roles:
                if request.path.startswith("/api/"):
                    return jsonify({"success": False, "message": "You do not have permission to access this resource."}), 403
                return redirect("/dashboard")
            return view_func(*args, **kwargs)

        return wrapper

    return decorator


def get_current_user():
    return session.get("user")


def get_current_student():
    user = get_current_user()
    if not user or not user.get("email"):
        return None

    from backend.database.connection import fetch_one

    return fetch_one(
        "SELECT * FROM students WHERE LOWER(email) = LOWER(%s)",
        (user["email"],),
    )


def get_current_teacher():
    user = get_current_user()
    if not user or not user.get("email"):
        return None

    from backend.database.connection import fetch_one

    return fetch_one(
        "SELECT * FROM teachers WHERE LOWER(email) = LOWER(%s)",
        (user["email"],),
    )


def get_teacher_exam_ids(teacher_id):
    from backend.database.connection import fetch_all

    rows = fetch_all(
        """
        SELECT exam_id FROM timetable WHERE invigilator_id = %s
        UNION
        SELECT exam_id FROM invigilators WHERE teacher_id = %s
        """,
        (teacher_id, teacher_id),
    )
    return [row["exam_id"] for row in rows]
