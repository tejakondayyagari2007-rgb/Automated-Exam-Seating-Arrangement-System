from flask import Blueprint, jsonify, request

from backend.database.connection import execute, fetch_all, fetch_one
from backend.middleware.auth_middleware import login_required, role_required

bp = Blueprint("room_routes", __name__)


@bp.route("/api/rooms", methods=["GET"])
@login_required
@role_required("ADMIN")
def list_rooms():
    return jsonify({"success": True, "rooms": fetch_all("SELECT * FROM rooms ORDER BY room_number ASC")})


@bp.route("/api/rooms", methods=["POST"])
@login_required
@role_required("ADMIN")
def create_room():
    payload = request.get_json(silent=True) or {}
    rows = int(payload.get("rows") or 0)
    cols = int(payload.get("columns") or 0)
    capacity = rows * cols
    room_id = execute(
        "INSERT INTO rooms (room_number, building, floor, `rows`, `columns`, capacity, facilities, status, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())",
        (payload.get("room_number"), payload.get("building"), payload.get("floor"), rows, cols, capacity, payload.get("facilities", "standard"), payload.get("status", "active")),
    )
    return jsonify({"success": True, "message": "Room created successfully.", "id": room_id})


@bp.route("/api/rooms/<int:room_id>", methods=["PUT"])
@login_required
@role_required("ADMIN")
def update_room(room_id):
    payload = request.get_json(silent=True) or {}
    rows = int(payload.get("rows") or 0)
    cols = int(payload.get("columns") or 0)
    capacity = rows * cols
    execute(
        "UPDATE rooms SET room_number = %s, building = %s, floor = %s, `rows` = %s, `columns` = %s, capacity = %s, facilities = %s, status = %s, updated_at = NOW() WHERE id = %s",
        (payload.get("room_number"), payload.get("building"), payload.get("floor"), rows, cols, capacity, payload.get("facilities", "standard"), payload.get("status", "active"), room_id),
    )
    return jsonify({"success": True, "message": "Room updated successfully."})


@bp.route("/api/rooms/<int:room_id>", methods=["DELETE"])
@login_required
@role_required("ADMIN")
def delete_room(room_id):
    execute("DELETE FROM rooms WHERE id = %s", (room_id,))
    return jsonify({"success": True, "message": "Room deleted successfully."})
