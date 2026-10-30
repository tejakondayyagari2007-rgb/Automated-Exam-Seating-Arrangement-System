from flask import Blueprint, jsonify, request, session

from backend.database.connection import execute, fetch_one
from backend.middleware.auth_middleware import login_required, role_required
from backend.services.auth_service import authenticate_user
from backend.services.audit_service import record_action
from backend.utils.security import hash_password

bp = Blueprint("auth_routes", __name__)


@bp.route("/api/auth/login", methods=["POST"])
def login():
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    email = (payload.get("email") or "").strip()
    password = payload.get("password") or ""
    role = (payload.get("role") or "ADMIN").upper()

    if not username and not email:
        return jsonify({"success": False, "message": "Username or email is required."}), 400
    if not password:
        return jsonify({"success": False, "message": "Password is required."}), 400

    user = authenticate_user(username or email, password)
    if not user:
        return jsonify({"success": False, "message": "Invalid username/email or password."}), 401
    if role and user.get("role") and user.get("role").upper() != role:
        return jsonify({"success": False, "message": "Selected role does not match the user account."}), 403

    session["user"] = {
        "id": user["id"],
        "name": user["name"],
        "role": user["role"],
        "email": user["email"],
        "username": user["username"],
    }
    record_action(user["id"], "Login", f"User {user['name']} logged in.")
    return jsonify({"success": True, "user": session["user"]})


@bp.route("/api/auth/logout", methods=["POST"])
@login_required
def logout():
    user = session.get("user")
    if user:
        record_action(user["id"], "Logout", f"User {user['name']} logged out.")
    session.clear()
    return jsonify({"success": True, "message": "Logged out successfully."})


@bp.route("/api/auth/me", methods=["GET"])
@login_required
def me():
    return jsonify({"success": True, "user": session.get("user")})


@bp.route("/api/auth/register", methods=["POST"])
@login_required
@role_required("ADMIN")
def register():
    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    username = (payload.get("username") or "").strip()
    email = (payload.get("email") or "").strip()
    password = payload.get("password") or ""
    role = payload.get("role") or "STUDENT"

    if not isinstance(role, str):
        return jsonify({"success": False, "message": "Invalid role."}), 400
    role = role.upper()
    if role == "ADMIN":
        return jsonify({"success": False, "message": "Admin accounts cannot be created through public registration."}), 403
    if role not in {"STUDENT", "TEACHER"}:
        return jsonify({"success": False, "message": "Invalid role."}), 400

    if not all([name, username, email, password]):
        return jsonify({"success": False, "message": "All fields are required."}), 400

    if fetch_one("SELECT id FROM users WHERE username = %s OR email = %s", (username, email)):
        return jsonify({"success": False, "message": "User already exists."}), 409

    execute(
        "INSERT INTO users (name, username, email, role, password_hash, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, NOW(), NOW())",
        (name, username, email, role, hash_password(password)),
    )
    return jsonify({"success": True, "message": "User created successfully."})
