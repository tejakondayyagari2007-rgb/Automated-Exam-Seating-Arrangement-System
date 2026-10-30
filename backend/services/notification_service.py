from backend.database.connection import execute, fetch_all, fetch_one


def create_notification(user_id, title, message):
    return execute(
        "INSERT INTO notifications (user_id, title, message, status, created_at, updated_at) VALUES (%s, %s, %s, 'unread', NOW(), NOW())",
        (user_id, title, message),
    )


def get_notifications(user_id=None):
    if user_id:
        return fetch_all("SELECT * FROM notifications WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
    return fetch_all("SELECT * FROM notifications ORDER BY created_at DESC")


def unread_count(user_id=None):
    return fetch_one("SELECT COUNT(*) AS count FROM notifications WHERE status = 'unread'" if not user_id else "SELECT COUNT(*) AS count FROM notifications WHERE user_id = %s AND status = 'unread'", (user_id,) if user_id else ())['count']
