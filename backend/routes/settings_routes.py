from flask import Blueprint, jsonify, request

from backend.database.connection import execute, fetch_all
from backend.middleware.auth_middleware import login_required, role_required

bp = Blueprint("settings_routes", __name__)


@bp.route("/api/settings", methods=["GET"])
@login_required
@role_required("ADMIN")
def get_settings():
    return jsonify({"success": True, "settings": fetch_all("SELECT * FROM system_settings ORDER BY id DESC")})


@bp.route("/api/settings", methods=["POST"])
@login_required
@role_required("ADMIN")
def save_settings():
    payload = request.get_json(silent=True) or {}
    key_name = payload.get("key_name")
    value = payload.get("value")
    if not all([key_name, value is not None]):
        return jsonify({"success": False, "message": "Key and value are required."}), 400
    execute("INSERT INTO system_settings (key_name, value, updated_at) VALUES (%s, %s, NOW()) AS new_setting ON DUPLICATE KEY UPDATE value = new_setting.value, updated_at = NOW()", (key_name, str(value)))
    return jsonify({"success": True, "message": "Settings saved."})
