from flask import Flask, jsonify, redirect, send_from_directory
from mysql.connector import Error as MySQLError

from backend.database.connection import check_mysql, close_db, init_db
from backend.middleware.auth_middleware import role_required
from backend.routes.attendance_routes import bp as attendance_bp
from backend.routes.auth_routes import bp as auth_bp
from backend.routes.dashboard_routes import bp as dashboard_bp
from backend.routes.exam_routes import bp as exam_bp
from backend.routes.notification_routes import bp as notification_bp
from backend.routes.report_routes import bp as report_bp
from backend.routes.room_routes import bp as room_bp
from backend.routes.seating_routes import bp as seating_bp
from backend.routes.settings_routes import bp as settings_bp
from backend.routes.student_routes import bp as student_bp
from backend.routes.subject_routes import bp as subject_bp
from backend.routes.teacher_routes import bp as teacher_bp
from backend.routes.timetable_routes import bp as timetable_bp
from config import Config


app = Flask(__name__, static_folder="static", template_folder="templates")
app.config.from_object(Config)

app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(student_bp)
app.register_blueprint(teacher_bp)
app.register_blueprint(room_bp)
app.register_blueprint(subject_bp)
app.register_blueprint(exam_bp)
app.register_blueprint(timetable_bp)
app.register_blueprint(seating_bp)
app.register_blueprint(attendance_bp)
app.register_blueprint(report_bp)
app.register_blueprint(notification_bp)
app.register_blueprint(settings_bp)

app.teardown_appcontext(close_db)


@app.route("/")
def index():
    return redirect("/login")


@app.route("/login")
def login_page():
    return send_from_directory("frontend/pages", "login.html")


@app.route("/dashboard")
@role_required("ADMIN", "TEACHER", "STUDENT")
def dashboard_page():
    return send_from_directory("frontend/pages", "dashboard.html")


@app.route("/students")
@role_required("ADMIN", "TEACHER", "STUDENT")
def students_page():
    return send_from_directory("frontend/pages", "students.html")


@app.route("/teachers")
@role_required("ADMIN")
def teachers_page():
    return send_from_directory("frontend/pages", "teachers.html")


@app.route("/rooms")
@role_required("ADMIN")
def rooms_page():
    return send_from_directory("frontend/pages", "rooms.html")


@app.route("/subjects")
@role_required("ADMIN")
def subjects_page():
    return send_from_directory("frontend/pages", "subjects.html")


@app.route("/exams")
@role_required("ADMIN", "TEACHER", "STUDENT")
def exams_page():
    return send_from_directory("frontend/pages", "exams.html")


@app.route("/timetable")
@role_required("ADMIN", "TEACHER", "STUDENT")
def timetable_page():
    return send_from_directory("frontend/pages", "timetable.html")


@app.route("/seating")
@role_required("ADMIN", "TEACHER", "STUDENT")
def seating_page():
    return send_from_directory("frontend/pages", "seating.html")


@app.route("/attendance")
@role_required("ADMIN", "TEACHER")
def attendance_page():
    return send_from_directory("frontend/pages", "attendance.html")


@app.route("/reports")
@role_required("ADMIN", "TEACHER")
def reports_page():
    return send_from_directory("frontend/pages", "reports.html")


@app.route("/notifications")
@role_required("ADMIN", "TEACHER", "STUDENT")
def notifications_page():
    return send_from_directory("frontend/pages", "notifications.html")


@app.route("/settings")
@role_required("ADMIN")
def settings_page():
    return send_from_directory("frontend/pages", "settings.html")


@app.route("/api/health")
def health():
    try:
        if not check_mysql():
            return jsonify({"success": False, "message": "Database unavailable."}), 503
    except MySQLError:
        app.logger.exception("MySQL health check failed.")
        return jsonify({"success": False, "message": "Database unavailable."}), 503

    return jsonify({"success": True, "message": "System healthy."})


@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "message": "The page or API route you requested was not found."}), 404


@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({"success": False, "message": "An unexpected error occurred. Please contact the administrator."}), 500


with app.app_context():
    init_db()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
