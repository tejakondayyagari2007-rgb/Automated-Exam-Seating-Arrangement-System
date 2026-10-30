from backend.database.connection import execute


def record_action(user_id, action, description):
    return execute(
        "INSERT INTO audit_logs (user_id, action, description, created_at) VALUES (%s, %s, %s, NOW())",
        (user_id, action, description),
    )
