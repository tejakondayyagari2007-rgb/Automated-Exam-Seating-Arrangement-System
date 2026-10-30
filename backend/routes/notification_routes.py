from flask import Blueprint, jsonify, request

from backend.database.connection import fetch_all
from backend.middleware.auth_middleware import (
    get_current_teacher,
    get_current_user,
    get_teacher_exam_ids,
    login_required,
    role_required,
)
from backend.services.notification_service import create_notification, get_notifications, unread_count

bp = Blueprint("notification_routes", __name__)


@bp.route("/api/notifications", methods=["GET"])
@login_required
@role_required("ADMIN", "TEACHER", "STUDENT")
def list_notifications():
    current_user = get_current_user()
    role = current_user.get("role")
    if role == "ADMIN":
        user = request.args.get("user_id")
        notifications = get_notifications(user)
        count = unread_count(user)
    else:
        user = current_user.get("id")
        notifications = get_notifications(user)
        if role == "TEACHER":
            teacher = get_current_teacher()
            if not teacher:
                return jsonify({
                    "success": False,
                    "message": "Teacher profile is not linked to this account.",
                }), 403
            exam_ids = get_teacher_exam_ids(teacher["id"])
            if exam_ids:
                placeholders = ", ".join(["%s"] * len(exam_ids))
                exam_rows = fetch_all(
                    f"SELECT name FROM exams WHERE id IN ({placeholders})",
                    tuple(exam_ids),
                )
                assigned_exam_names = [
                    row["name"].casefold()
                    for row in exam_rows
                    if row.get("name")
                ]
                all_exam_rows = fetch_all("SELECT name FROM exams")
                all_exam_names = [
                    row["name"].casefold()
                    for row in all_exam_rows
                    if row.get("name")
                ]
                global_notifications = [
                    notification
                    for notification in get_notifications()
                    if notification.get("user_id") is None
                ]
                for notification in global_notifications:
                    content = " ".join(
                        (
                            notification.get("title") or "",
                            notification.get("message") or "",
                        )
                    ).casefold()
                    mentioned_exams = [
                        name for name in all_exam_names if name in content
                    ]
                    if not mentioned_exams or any(
                        name in assigned_exam_names for name in mentioned_exams
                    ):
                        if notification not in notifications:
                            notifications.append(notification)
            notifications.sort(
                key=lambda notification: str(notification.get("created_at") or ""),
                reverse=True,
            )
            count = sum(
                1
                for notification in notifications
                if str(notification.get("status", "")).casefold() == "unread"
            )
        else:
            count = unread_count(user)
    return jsonify({
        "success": True,
        "notifications": notifications,
        "unread_count": count,
    })


@bp.route("/api/notifications", methods=["POST"])
@login_required
@role_required("ADMIN")
def create_notification_route():
    payload = request.get_json(silent=True) or {}
    user_id = payload.get("user_id")
    title = payload.get("title")
    message = payload.get("message")
    if not all([user_id, title, message]):
        return jsonify({"success": False, "message": "User, title and message are required."}), 400
    create_notification(user_id, title, message)
    return jsonify({"success": True, "message": "Notification created successfully."})
