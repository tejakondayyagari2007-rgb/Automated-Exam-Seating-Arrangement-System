from flask import Blueprint, jsonify, request

from backend.database.connection import execute, fetch_all, fetch_one
from backend.middleware.auth_middleware import (
    get_current_teacher,
    get_current_user,
    get_teacher_exam_ids,
    login_required,
    role_required,
)
from backend.utils.csv_handler import parse_csv_text
from backend.utils.export_handler import export_csv_data
from backend.utils.validators import is_valid_email

bp = Blueprint("student_routes", __name__)


@bp.route("/api/students", methods=["GET"])
@login_required
@role_required("ADMIN", "TEACHER", "STUDENT")
def list_students():
    search = request.args.get("search", "")
    department_id = request.args.get("department_id")
    query = """
        SELECT s.*, d.name AS department_name, sec.name AS section_name
        FROM students s
        LEFT JOIN departments d ON d.id = s.department_id
        LEFT JOIN sections sec ON sec.id = s.section_id
    """
    params = []
    clauses = []
    current_user = get_current_user()
    if current_user.get("role") == "STUDENT":
        email = current_user.get("email")
        if not email:
            return jsonify({"success": False, "message": "Student profile is not linked to this account."}), 403
        clauses.append("LOWER(s.email) = LOWER(%s)")
        params.append(email)
    elif current_user.get("role") == "TEACHER":
        teacher = get_current_teacher()
        if not teacher:
            return jsonify({"success": False, "message": "Teacher profile is not linked to this account."}), 403
        exam_ids = get_teacher_exam_ids(teacher["id"])
        if not exam_ids:
            return jsonify({"success": True, "students": []})
        placeholders = ", ".join(["%s"] * len(exam_ids))
        clauses.append(
            f"""
            EXISTS (
                SELECT 1 FROM exam_students es
                WHERE es.student_id = s.id AND es.exam_id IN ({placeholders})
            )
            """
        )
        params.extend(exam_ids)
    if search:
        clauses.append("(s.name LIKE %s OR s.roll_no LIKE %s OR s.email LIKE %s)")
        term = f"%{search}%"
        params.extend([term, term, term])
    if department_id:
        clauses.append("s.department_id = %s")
        params.append(department_id)
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY s.id DESC"
    students = fetch_all(query, tuple(params))
    if current_user.get("role") == "STUDENT" and not students:
        return jsonify({"success": False, "message": "Student profile is not linked to this account."}), 403
    return jsonify({"success": True, "students": students})


@bp.route("/api/students", methods=["POST"])
@login_required
@role_required("ADMIN")
def create_student():
    payload = request.get_json(silent=True) or {}
    required = ["roll_no", "name", "email", "phone", "department_id", "section_id", "year"]
    if not all(payload.get(field) not in (None, "") for field in required):
        return jsonify({"success": False, "message": "All required student fields are required."}), 400
    if not is_valid_email(payload["email"]):
        return jsonify({"success": False, "message": "Invalid email format."}), 400
    if fetch_one("SELECT id FROM students WHERE roll_no = %s", (payload["roll_no"],)):
        return jsonify({"success": False, "message": "Duplicate roll number detected."}), 409
    student_id = execute(
        """
        INSERT INTO students (roll_no, name, email, phone, department_id, section_id, year, gender, accessibility_requirement, status, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """,
        (
            payload["roll_no"],
            payload["name"],
            payload["email"],
            payload["phone"],
            payload["department_id"],
            payload["section_id"],
            payload["year"],
            payload.get("gender", "Other"),
            payload.get("accessibility_requirement", "No"),
            payload.get("status", "active"),
        ),
    )
    return jsonify({"success": True, "message": "Student created successfully.", "id": student_id})


@bp.route("/api/students/<int:student_id>", methods=["PUT"])
@login_required
@role_required("ADMIN")
def update_student(student_id):
    payload = request.get_json(silent=True) or {}
    if not payload:
        return jsonify({"success": False, "message": "No data provided."}), 400
    execute(
        """
        UPDATE students SET
            roll_no = %s,
            name = %s,
            email = %s,
            phone = %s,
            department_id = %s,
            section_id = %s,
            year = %s,
            gender = %s,
            accessibility_requirement = %s,
            status = %s,
            updated_at = NOW()
        WHERE id = %s
        """,
        (
            payload.get("roll_no"),
            payload.get("name"),
            payload.get("email"),
            payload.get("phone"),
            payload.get("department_id"),
            payload.get("section_id"),
            payload.get("year"),
            payload.get("gender", "Other"),
            payload.get("accessibility_requirement", "No"),
            payload.get("status", "active"),
            student_id,
        ),
    )
    return jsonify({"success": True, "message": "Student updated successfully."})


@bp.route("/api/students/<int:student_id>", methods=["DELETE"])
@login_required
@role_required("ADMIN")
def delete_student(student_id):
    execute("DELETE FROM students WHERE id = %s", (student_id,))
    return jsonify({"success": True, "message": "Student deleted successfully."})


@bp.route("/api/students/import", methods=["POST"])
@login_required
@role_required("ADMIN")
def import_students():
    file = request.files.get("file")
    if not file:
        return jsonify({"success": False, "message": "CSV file is required."}), 400
    content = file.read()
    rows = parse_csv_text(content)
    imported = 0
    skipped = 0
    errors = 0
    for row in rows:
        roll_no = (row.get("roll_no") or "").strip()
        name = (row.get("name") or "").strip()
        email = (row.get("email") or "").strip()
        if not all([roll_no, name, email]):
            skipped += 1
            errors += 1
            continue
        if fetch_one("SELECT id FROM students WHERE roll_no = %s", (roll_no,)):
            skipped += 1
            errors += 1
            continue
        if not is_valid_email(email):
            skipped += 1
            errors += 1
            continue
        execute(
            "INSERT INTO students (roll_no, name, email, phone, department_id, section_id, year, status, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, 'active', NOW(), NOW())",
            (roll_no, name, email, row.get("phone") or "", row.get("department_id") or 1, row.get("section_id") or 1, row.get("year") or 1),
        )
        imported += 1
    return jsonify({"success": True, "imported": imported, "skipped": skipped, "errors": errors})


@bp.route("/api/students/export", methods=["GET"])
@login_required
@role_required("ADMIN", "TEACHER")
def export_students():
    current_user = get_current_user()
    if current_user.get("role") == "TEACHER":
        teacher = get_current_teacher()
        if not teacher:
            return jsonify({"success": False, "message": "Teacher profile is not linked to this account."}), 403
        exam_ids = get_teacher_exam_ids(teacher["id"])
        if not exam_ids:
            rows = []
        else:
            placeholders = ", ".join(["%s"] * len(exam_ids))
            rows = fetch_all(
                f"""
                SELECT DISTINCT s.roll_no, s.name, s.email, s.phone,
                    s.department_id, s.section_id, s.year
                FROM students s
                INNER JOIN exam_students es ON es.student_id = s.id
                WHERE es.exam_id IN ({placeholders})
                ORDER BY s.roll_no
                """,
                tuple(exam_ids),
            )
    else:
        rows = fetch_all(
            "SELECT roll_no, name, email, phone, department_id, section_id, year FROM students"
        )
    csv_content = export_csv_data(rows, ["roll_no", "name", "email", "phone", "department_id", "section_id", "year"])
    return csv_content
