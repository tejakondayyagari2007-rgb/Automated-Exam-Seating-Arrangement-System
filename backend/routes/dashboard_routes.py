from flask import Blueprint, jsonify

from backend.database.connection import fetch_all
from backend.middleware.auth_middleware import (
    get_current_student,
    get_current_teacher,
    get_current_user,
    get_teacher_exam_ids,
    login_required,
    role_required,
)
from backend.services.auth_service import get_dashboard_stats

bp = Blueprint("dashboard_routes", __name__)


@bp.route("/api/dashboard", methods=["GET"])
@login_required
@role_required("ADMIN", "TEACHER", "STUDENT")
def dashboard():
    current_user = get_current_user()
    if current_user.get("role") == "STUDENT":
        student = get_current_student()
        if not student:
            return jsonify({"success": False, "message": "Student profile is not linked to this account."}), 403

        student_id = student["id"]
        stats = fetch_all(
            """
            SELECT
                (
                    SELECT COUNT(DISTINCT e.id)
                    FROM exams e
                    WHERE e.date_value >= CURRENT_DATE
                        AND e.status IN ('Upcoming', 'Ongoing')
                        AND (
                            EXISTS (
                                SELECT 1 FROM exam_students es
                                WHERE es.exam_id = e.id AND es.student_id = %s
                            )
                            OR EXISTS (
                                SELECT 1
                                FROM seat_assignments sa
                                INNER JOIN seating_arrangements arr ON arr.id = sa.arrangement_id
                                WHERE arr.exam_id = e.id AND sa.student_id = %s
                            )
                        )
                ) AS upcoming_exams,
                (
                    SELECT COUNT(*)
                    FROM seat_assignments sa
                    INNER JOIN seating_arrangements arr ON arr.id = sa.arrangement_id
                    WHERE sa.student_id = %s AND arr.status = 'PUBLISHED'
                ) AS published_seats,
                (
                    SELECT COUNT(*)
                    FROM timetable t
                    WHERE EXISTS (
                        SELECT 1 FROM exam_students es
                        WHERE es.exam_id = t.exam_id AND es.student_id = %s
                    ) OR EXISTS (
                        SELECT 1
                        FROM seat_assignments sa
                        INNER JOIN seating_arrangements arr ON arr.id = sa.arrangement_id
                        WHERE arr.exam_id = t.exam_id AND sa.student_id = %s
                    )
                ) AS timetable_entries
            """,
            (student_id, student_id, student_id, student_id, student_id),
        )[0]
        recent_exams = fetch_all(
            """
            SELECT e.name, e.exam_code, e.date_value
            FROM exams e
            WHERE EXISTS (
                SELECT 1 FROM exam_students es
                WHERE es.exam_id = e.id AND es.student_id = %s
            ) OR EXISTS (
                SELECT 1
                FROM seat_assignments sa
                INNER JOIN seating_arrangements arr ON arr.id = sa.arrangement_id
                WHERE arr.exam_id = e.id AND sa.student_id = %s
            )
            ORDER BY e.date_value DESC, e.start_time DESC
            LIMIT 5
            """,
            (student_id, student_id),
        )
        for exam in recent_exams:
            if hasattr(exam["date_value"], "isoformat"):
                exam["date_value"] = exam["date_value"].isoformat()
        return jsonify({
            "success": True,
            "role": "STUDENT",
            "student": {"name": student["name"], "roll_no": student["roll_no"]},
            "stats": stats,
            "recent_exams": recent_exams,
            "recent_activity": [],
        })

    if current_user.get("role") == "TEACHER":
        teacher = get_current_teacher()
        if not teacher:
            return jsonify({"success": False, "message": "Teacher profile is not linked to this account."}), 403
        exam_ids = get_teacher_exam_ids(teacher["id"])
        if exam_ids:
            placeholders = ", ".join(["%s"] * len(exam_ids))
            stats = {
                "total_exams": len(exam_ids),
                "upcoming_exams": fetch_all(
                    f"""
                    SELECT COUNT(*) AS value FROM exams
                    WHERE id IN ({placeholders}) AND status = 'Upcoming'
                    """,
                    tuple(exam_ids),
                )[0]["value"],
                "published_arrangements": fetch_all(
                    f"""
                    SELECT COUNT(*) AS value
                    FROM seating_arrangements
                    WHERE exam_id IN ({placeholders}) AND status = 'PUBLISHED'
                    """,
                    tuple(exam_ids),
                )[0]["value"],
                "attendance_percentage": fetch_all(
                    f"""
                    SELECT COALESCE(ROUND(AVG(present_status) * 100), 0) AS value
                    FROM attendance
                    WHERE exam_id IN ({placeholders})
                        AND present_status IS NOT NULL
                    """,
                    tuple(exam_ids),
                )[0]["value"],
            }
        else:
            exam_ids = []
            stats = {
                "total_exams": 0,
                "upcoming_exams": 0,
                "published_arrangements": 0,
                "attendance_percentage": 0,
            }
    else:
        exam_ids = None
        stats = get_dashboard_stats()
    if current_user.get("role") == "TEACHER":
        placeholders = ", ".join(["%s"] * len(exam_ids))
        recent_exams = fetch_all(
            f"""
            SELECT name, exam_code, date_value FROM exams
            WHERE id IN ({placeholders})
            ORDER BY created_at DESC LIMIT 5
            """,
            tuple(exam_ids),
        ) if exam_ids else []
    else:
        recent_exams = fetch_all(
            "SELECT name, exam_code, date_value FROM exams ORDER BY created_at DESC LIMIT 5"
        )
    for exam in recent_exams:
        if hasattr(exam["date_value"], "isoformat"):
            exam["date_value"] = exam["date_value"].isoformat()
    recent_activity = []
    if current_user.get("role") == "ADMIN":
        recent_activity = fetch_all("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 8")
    return jsonify({
        "success": True,
        "role": current_user.get("role"),
        "stats": stats,
        "recent_exams": recent_exams,
        "recent_activity": recent_activity,
    })


@bp.route("/api/dashboard/admin", methods=["GET"])
@login_required
@role_required("ADMIN")
def admin_dashboard():
    return dashboard()
