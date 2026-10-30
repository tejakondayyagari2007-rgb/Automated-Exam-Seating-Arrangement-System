from unittest.mock import patch

import pytest


@pytest.fixture(scope="module")
def app():
    with patch("backend.database.connection.init_db"):
        from app import app as flask_app

    flask_app.config.update(TESTING=True)
    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()


def sign_in(client, role, user_id=7, email=None):
    with client.session_transaction() as browser_session:
        browser_session["user"] = {
            "id": user_id,
            "name": "Test User",
            "role": role,
            "email": email or f"{role.lower()}@example.test",
            "username": f"{role.lower()}-user",
        }


def test_unauthenticated_pages_and_apis_are_protected(client):
    assert client.get("/dashboard").status_code == 302
    assert client.get("/api/students").status_code == 401
    assert client.get("/api/exams").status_code == 401


@pytest.mark.parametrize(
    ("role", "allowed_page", "blocked_page"),
    [
        ("ADMIN", "/settings", "/unknown-management-page"),
        ("TEACHER", "/attendance", "/teachers"),
        ("STUDENT", "/exams", "/attendance"),
    ],
)
def test_role_page_access(client, role, allowed_page, blocked_page):
    sign_in(client, role)

    assert client.get(allowed_page).status_code == 200
    assert client.get(blocked_page).status_code in (302, 404)


@pytest.mark.parametrize("page", ["/teachers", "/rooms", "/subjects"])
def test_admin_only_pages_are_not_directly_accessible_to_teachers(client, page):
    sign_in(client, "TEACHER")
    assert client.get(page).status_code == 302

    sign_in(client, "ADMIN")
    assert client.get(page).status_code == 200


@pytest.mark.parametrize(
    ("path", "response_key"),
    [
        ("/api/teachers", "teachers"),
        ("/api/rooms", "rooms"),
        ("/api/subjects", "subjects"),
    ],
)
def test_admin_only_list_apis_are_not_accessible_to_teachers(
    client, monkeypatch, path, response_key
):
    from backend.routes import room_routes, subject_routes, teacher_routes

    for route_module in (room_routes, subject_routes, teacher_routes):
        monkeypatch.setattr(route_module, "fetch_all", lambda query: [])

    sign_in(client, "TEACHER")
    assert client.get(path).status_code == 403

    sign_in(client, "ADMIN")
    response = client.get(path)
    assert response.status_code == 200
    assert response.get_json()[response_key] == []


def test_teacher_navigation_uses_only_approved_page_links():
    from pathlib import Path

    root = Path(__file__).parent.parent
    auth_source = (root / "static" / "js" / "auth.js").read_text(encoding="utf-8")
    common_source = (root / "static" / "js" / "common.js").read_text(encoding="utf-8")

    assert (
        "TEACHER: ['/dashboard', '/exams', '/timetable', '/students', "
        "'/attendance', '/seating', '/reports', '/notifications']"
    ) in auth_source
    for label in (
        "Dashboard",
        "Assigned Exams",
        "My Timetable",
        "Assigned Students",
        "Attendance",
        "Seating Details",
        "Relevant Reports",
        "Notifications",
        "Logout",
    ):
        assert f"'{label}'" in common_source


def test_admin_and_teacher_receive_role_appropriate_dashboards(client, monkeypatch):
    from backend.routes import dashboard_routes

    monkeypatch.setattr(dashboard_routes, "get_current_teacher", lambda: {"id": 6})
    monkeypatch.setattr(dashboard_routes, "get_teacher_exam_ids", lambda teacher_id: [5])
    monkeypatch.setattr(
        dashboard_routes,
        "get_dashboard_stats",
        lambda: {
            "total_students": 40,
            "total_teachers": 5,
            "total_rooms": 3,
            "total_seats": 100,
            "available_seats": 80,
            "total_exams": 12,
            "upcoming_exams": 4,
            "published_arrangements": 6,
            "attendance_percentage": 92,
        },
    )
    monkeypatch.setattr(
        dashboard_routes,
        "fetch_all",
        lambda query, params=(): (
            [{"value": 4}]
            if "COUNT(*) AS value" in query
            else [{"value": 6}]
            if "COUNT(*)" in query
            else [{"value": 92}]
            if "AVG(present_status)" in query
            else [{"name": "Exam A", "exam_code": "A1", "date_value": "2026-11-01"}]
            if "FROM exams" in query
            else [{"action": "Login"}]
        ),
    )

    sign_in(client, "ADMIN")
    admin_result = client.get("/api/dashboard").get_json()
    assert admin_result["role"] == "ADMIN"
    assert admin_result["stats"]["total_students"] == 40
    assert admin_result["recent_activity"] == [{"action": "Login"}]

    sign_in(client, "TEACHER")
    teacher_result = client.get("/api/dashboard").get_json()
    assert teacher_result["role"] == "TEACHER"
    assert set(teacher_result["stats"]) == {
        "total_exams",
        "upcoming_exams",
        "published_arrangements",
        "attendance_percentage",
    }
    assert teacher_result["recent_activity"] == []


def test_student_dashboard_uses_only_the_linked_student_id(client, monkeypatch):
    from backend.routes import dashboard_routes

    student = {"id": 31, "name": "Student One", "roll_no": "R031"}
    monkeypatch.setattr(dashboard_routes, "get_current_student", lambda: student)
    calls = []

    def fetch_all(query, params=()):
        calls.append((query, params))
        if "AS upcoming_exams" in query:
            return [{
                "upcoming_exams": 2,
                "published_seats": 1,
                "timetable_entries": 2,
            }]
        return [{"name": "Own Exam", "exam_code": "OWN", "date_value": "2026-11-01"}]

    monkeypatch.setattr(dashboard_routes, "fetch_all", fetch_all)
    sign_in(client, "STUDENT", user_id=8)

    response = client.get("/api/dashboard?student_id=999").get_json()

    assert response["student"] == {"name": "Student One", "roll_no": "R031"}
    assert response["recent_activity"] == []
    assert calls[0][1] == (31, 31, 31, 31, 31)
    assert calls[1][1] == (31, 31)


def test_student_profile_query_cannot_be_widened_with_parameters(client, monkeypatch):
    from backend.routes import student_routes

    captured = {}

    def fetch_all(query, params=()):
        captured["query"] = query
        captured["params"] = params
        return [{"id": 31, "email": "student@example.test"}]

    monkeypatch.setattr(student_routes, "fetch_all", fetch_all)
    sign_in(client, "STUDENT", email="student@example.test")

    result = client.get(
        "/api/students?student_id=999&department_id=4&search=someone-else"
    ).get_json()

    assert result["students"] == [{"id": 31, "email": "student@example.test"}]
    assert "LOWER(s.email) = LOWER(%s)" in captured["query"]
    assert captured["params"] == (
        "student@example.test",
        "%someone-else%",
        "%someone-else%",
        "%someone-else%",
        "4",
    )
    assert client.get("/api/students/999").status_code == 405


@pytest.mark.parametrize(
    ("module_name", "path", "expected_params"),
    [
        ("exam_routes", "/api/exams?student_id=999", (31, 31)),
        ("timetable_routes", "/api/timetable?student_id=999", (31, 31)),
        ("seating_routes", "/api/seating?student_id=999&exam_id=44", (31, "44")),
    ],
)
def test_student_academic_apis_always_scope_to_own_record(
    client, monkeypatch, module_name, path, expected_params
):
    from backend.routes import exam_routes, seating_routes, timetable_routes

    route_modules = {
        "exam_routes": exam_routes,
        "timetable_routes": timetable_routes,
        "seating_routes": seating_routes,
    }
    route_module = route_modules[module_name]
    monkeypatch.setattr(route_module, "get_current_student", lambda: {"id": 31})
    captured = {}

    def fetch_all(query, params=()):
        captured["query"] = query
        captured["params"] = params
        return []

    monkeypatch.setattr(route_module, "fetch_all", fetch_all)
    sign_in(client, "STUDENT", email="student@example.test")

    assert client.get(path).get_json()["success"] is True
    assert expected_params == captured["params"]
    assert "student_id = %s" in captured["query"]


def test_student_notifications_ignore_requested_user_id(client, monkeypatch):
    from backend.routes import notification_routes

    requested_ids = []
    monkeypatch.setattr(
        notification_routes,
        "get_notifications",
        lambda user_id: requested_ids.append(user_id) or [],
    )
    monkeypatch.setattr(notification_routes, "unread_count", lambda user_id: 0)
    sign_in(client, "STUDENT", user_id=8)

    response = client.get("/api/notifications?user_id=999").get_json()

    assert response["notifications"] == []
    assert requested_ids == [8]


def test_students_cannot_call_management_apis(client):
    sign_in(client, "STUDENT")

    forbidden_requests = [
        ("POST", "/api/students", {}),
        ("PUT", "/api/students/999", {}),
        ("DELETE", "/api/students/999", None),
        ("POST", "/api/exams", {}),
        ("POST", "/api/timetable", {}),
        ("POST", "/api/attendance", {}),
        ("POST", "/api/notifications", {}),
        ("POST", "/api/seating/generate", {}),
        ("POST", "/api/rooms", {}),
        ("POST", "/api/subjects", {}),
        ("POST", "/api/teachers", {}),
        ("GET", "/api/reports", None),
        ("GET", "/api/settings", None),
        ("POST", "/api/auth/register", {}),
    ]
    for method, path, payload in forbidden_requests:
        response = client.open(
            path,
            method=method,
            json=payload,
        )
        assert response.status_code == 403, path
    assert client.get("/api/dashboard/admin").status_code == 403


def test_admin_exam_management_and_teacher_exam_read_access(client, monkeypatch):
    from backend.routes import exam_routes

    monkeypatch.setattr(exam_routes, "get_current_teacher", lambda: {"id": 6})
    monkeypatch.setattr(exam_routes, "get_teacher_exam_ids", lambda teacher_id: [5])
    monkeypatch.setattr(
        exam_routes,
        "fetch_all",
        lambda query, params=(): [{"id": 5, "name": "Exam A", "exam_code": "A1"}],
    )
    monkeypatch.setattr(
        exam_routes,
        "fetch_one",
        lambda query, params=(): {"id": 1} if "FROM subjects" in query else None,
    )
    monkeypatch.setattr(exam_routes, "execute", lambda query, params=(): 17)

    sign_in(client, "ADMIN")
    assert client.get("/api/exams").get_json()["exams"][0]["id"] == 5
    create_result = client.post(
        "/api/exams",
        json={
            "name": "New Exam",
            "exam_code": "NEW1",
            "subject_id": 1,
            "date_value": "2026-11-05",
            "start_time": "09:00",
            "end_time": "10:00",
            "duration_minutes": 60,
            "status": "Upcoming",
        },
    )
    assert create_result.status_code == 200
    assert create_result.get_json()["id"] == 17

    sign_in(client, "TEACHER")
    assert client.get("/api/exams").get_json()["exams"][0]["id"] == 5
    assert client.post("/api/exams", json={}).status_code == 403


def test_public_registration_cannot_claim_student_or_teacher_roles(client):
    assert client.post(
        "/api/auth/register",
        json={"name": "Claim", "username": "claim", "email": "student@example.test", "password": "pw"},
    ).status_code == 401

    sign_in(client, "TEACHER")
    assert client.post(
        "/api/auth/register",
        json={"name": "Claim", "username": "claim", "email": "student@example.test", "password": "pw"},
    ).status_code == 403


def test_login_role_must_match_the_authenticated_account(client, monkeypatch):
    from backend.routes import auth_routes

    account = {
        "id": 4,
        "name": "Admin User",
        "role": "ADMIN",
        "email": "admin@example.test",
        "username": "admin-user",
    }
    monkeypatch.setattr(auth_routes, "authenticate_user", lambda username, password: account)
    monkeypatch.setattr(auth_routes, "record_action", lambda *args: None)

    mismatch = client.post(
        "/api/auth/login",
        json={"username": "admin-user", "password": "valid", "role": "STUDENT"},
    )
    assert mismatch.status_code == 403

    authenticated = client.post(
        "/api/auth/login",
        json={"username": "admin-user", "password": "valid", "role": "ADMIN"},
    )
    assert authenticated.status_code == 200
    assert authenticated.get_json()["user"]["role"] == "ADMIN"


def test_admin_can_still_create_accounts(client, monkeypatch):
    from backend.routes import auth_routes

    monkeypatch.setattr(auth_routes, "fetch_one", lambda query, params=(): None)
    monkeypatch.setattr(auth_routes, "execute", lambda query, params=(): 20)
    sign_in(client, "ADMIN")

    response = client.post(
        "/api/auth/register",
        json={
            "name": "Student One",
            "username": "student-one",
            "email": "student@example.test",
            "password": "test-password",
            "role": "STUDENT",
        },
    )

    assert response.status_code == 200
    assert response.get_json()["success"] is True


def test_secret_key_configuration_rejects_missing_or_known_production_keys():
    from config import Config, get_secret_key

    with pytest.raises(RuntimeError, match="configured in production"):
        get_secret_key("production", None)
    with pytest.raises(RuntimeError, match="configured in production"):
        get_secret_key("prod", None)
    with pytest.raises(RuntimeError, match="known default"):
        get_secret_key("production", "change_this_secret_key")

    secure_key = "a" * 48
    assert get_secret_key("production", secure_key) == secure_key
    assert len(get_secret_key("development", None)) >= 32
    assert Config.DEBUG is False


def test_exam_seating_uses_registered_candidates_and_excludes_blocked_reserved_seats(
    app, monkeypatch
):
    import sqlite3
    from backend.services import seating_service

    candidates = [
        {"id": 11, "name": "Student A", "roll_no": "A11", "status": "active"},
        {"id": 12, "name": "Student B", "roll_no": "B12", "status": "active"},
    ]
    rooms = [
        {"id": 1, "room_number": "101", "rows": 1, "columns": 2, "capacity": 2},
        {"id": 2, "room_number": "102", "rows": 1, "columns": 2, "capacity": 2},
    ]
    inserted = []

    monkeypatch.setattr(seating_service, "get_db", lambda: sqlite3.connect(":memory:"))
    monkeypatch.setattr(
        seating_service,
        "fetch_one",
        lambda query, params=(): {"id": 4} if "FROM exams" in query else None,
    )

    def fetch_all(query, params=()):
        if "FROM exam_students es" in query:
            assert params == (4,)
            return candidates
        if "FROM rooms" in query:
            return rooms
        if "FROM room_seats" in query:
            return [
                {"room_id": 1, "seat_number": "A02", "status": "blocked"},
                {"room_id": 2, "seat_number": "A02", "status": "reserved"},
            ]
        raise AssertionError(f"Unexpected query: {query}")

    def execute(query, params=()):
        inserted.append((query, params))
        return 81 if "INSERT INTO seating_arrangements" in query else 1

    monkeypatch.setattr(seating_service, "fetch_all", fetch_all)
    monkeypatch.setattr(seating_service, "execute", execute)

    with app.app_context():
        result = seating_service.generate_exam_arrangement(4)

    assert {row["student_id"] for row in result["assignments"]} == {11, 12}
    assert [(row["room_id"], row["seat_number"]) for row in result["assignments"]] == [
        (1, "101-A01"),
        (2, "102-A01"),
    ]
    assert len({row["seat_number"] for row in result["assignments"]}) == 2
    assert len(inserted) == 3


def test_exam_seating_rejects_roster_larger_than_unblocked_capacity():
    from backend.services.seating_service import build_exam_assignments

    students = [
        {"id": index, "name": f"Student {index}", "roll_no": str(index)}
        for index in range(1, 4)
    ]
    rooms = [
        {"id": 1, "room_number": "101", "rows": 1, "columns": 2, "capacity": 2},
        {"id": 2, "room_number": "102", "rows": 1, "columns": 2, "capacity": 2},
    ]

    with pytest.raises(ValueError, match="Available room capacity \\(2\\)"):
        build_exam_assignments(
            students,
            rooms,
            {1: {"A02": "blocked"}, 2: {"A02": "reserved"}},
        )


def test_exam_seating_uses_local_labels_when_one_room_is_selected():
    from backend.services.seating_service import build_exam_assignments

    assignments = build_exam_assignments(
        [{"id": 11, "name": "Student A", "roll_no": "A11"}],
        [{"id": 1, "room_number": "101", "rows": 1, "columns": 2, "capacity": 2}],
        {},
    )

    assert assignments[0]["seat_number"] == "A01"
    assert assignments[0]["room_number"] == "101"


def test_seat_swap_updates_both_assignment_locations(app, monkeypatch):
    import sqlite3
    from backend.services import seating_service

    records = [
        {"id": 101, "room_id": 1, "row_no": 1, "column_no": 1, "seat_number": "101-A01"},
        {"id": 102, "room_id": 2, "row_no": 1, "column_no": 1, "seat_number": "102-A01"},
    ]
    calls = []

    monkeypatch.setattr(seating_service, "get_db", lambda: sqlite3.connect(":memory:"))
    monkeypatch.setattr(
        seating_service,
        "fetch_one",
        lambda query, params=(): (
            {"id": 9, "status": "PUBLISHED"}
            if "FROM seating_arrangements" in query
            else records[0]
            if params == (9, 11)
            else records[1]
        ),
    )
    monkeypatch.setattr(
        seating_service,
        "execute",
        lambda query, params=(): calls.append((query, params)),
    )

    with app.app_context():
        seating_service.swap_student_assignments(9, 11, 12)

    assert len(calls) == 3
    assert calls[0][1] == ("__sw_101", 101)
    assert calls[1][1] == (1, 1, 1, "101-A01", 102)
    assert calls[2][1] == (2, 1, 1, "102-A01", 101)


def test_teacher_student_search_is_limited_to_assigned_exam_rosters(client, monkeypatch):
    from backend.routes import student_routes

    captured = {}
    monkeypatch.setattr(student_routes, "get_current_teacher", lambda: {"id": 6})
    monkeypatch.setattr(student_routes, "get_teacher_exam_ids", lambda teacher_id: [3, 5])
    monkeypatch.setattr(
        student_routes,
        "fetch_all",
        lambda query, params=(): captured.update(query=query, params=params) or [],
    )
    sign_in(client, "TEACHER", email="teacher@example.test")

    response = client.get("/api/students?search=R1&department_id=2")

    assert response.status_code == 200
    assert "es.exam_id IN (%s, %s)" in captured["query"]
    assert captured["params"] == (3, 5, "%R1%", "%R1%", "%R1%", "2")


def test_teacher_attendance_and_reports_are_limited_to_assigned_exams(
    client, monkeypatch
):
    from backend.routes import attendance_routes, report_routes

    monkeypatch.setattr(attendance_routes, "get_current_teacher", lambda: {"id": 6})
    monkeypatch.setattr(attendance_routes, "get_teacher_exam_ids", lambda teacher_id: [3])
    monkeypatch.setattr(
        attendance_routes,
        "get_attendance_rows",
        lambda exam_id=None, permitted_exam_ids=None: (
            [{"exam_id": 3}] if permitted_exam_ids == [3] else []
        ),
    )
    monkeypatch.setattr(report_routes, "get_current_teacher", lambda: {"id": 6})
    monkeypatch.setattr(report_routes, "get_teacher_exam_ids", lambda teacher_id: [3])
    captured = {}
    monkeypatch.setattr(
        report_routes,
        "get_reports",
        lambda exam_ids=None: captured.update(exam_ids=exam_ids) or {},
    )
    sign_in(client, "TEACHER", email="teacher@example.test")

    assert client.get("/api/attendance").get_json()["attendance"] == [{"exam_id": 3}]
    assert client.get("/api/attendance?exam_id=4").status_code == 403
    assert client.get("/api/reports").status_code == 200
    assert captured["exam_ids"] == [3]
    assert client.post("/api/notifications", json={}).status_code == 403


def test_teacher_notifications_include_only_relevant_global_exam_notices(
    client, monkeypatch
):
    from backend.routes import notification_routes

    notifications = [
        {
            "id": 10,
            "user_id": 20,
            "title": "Personal",
            "message": "Assigned exam notice",
            "status": "unread",
            "created_at": "2026-10-30 12:00:00",
        },
        {
            "id": 11,
            "user_id": None,
            "title": "Exam timetable published",
            "message": "The November sample exam timetable is available.",
            "status": "unread",
            "created_at": "2026-10-30 11:00:00",
        },
        {
            "id": 12,
            "user_id": None,
            "title": "Seating arrangement ready",
            "message": "A sample seating arrangement is available for Database Systems Midterm.",
            "status": "unread",
            "created_at": "2026-10-30 10:00:00",
        },
        {
            "id": 13,
            "user_id": None,
            "title": "Seating arrangement ready",
            "message": "A sample seating arrangement is available for Digital Circuits Quiz.",
            "status": "unread",
            "created_at": "2026-10-30 09:00:00",
        },
    ]
    monkeypatch.setattr(
        notification_routes,
        "get_current_teacher",
        lambda: {"id": 4},
    )
    monkeypatch.setattr(
        notification_routes,
        "get_teacher_exam_ids",
        lambda teacher_id: [1],
    )
    monkeypatch.setattr(
        notification_routes,
        "fetch_all",
        lambda query, params=(): (
            [{"name": "Database Systems Midterm"}]
            if params == (1,)
            else [
                {"name": "Database Systems Midterm"},
                {"name": "Digital Circuits Quiz"},
            ]
        ),
    )
    monkeypatch.setattr(
        notification_routes,
        "get_notifications",
        lambda user_id=None: (
            [item for item in notifications if item["user_id"] == user_id]
            if user_id is not None
            else notifications
        ),
    )
    sign_in(client, "TEACHER", user_id=20, email="teacher@example.test")

    response = client.get("/api/notifications").get_json()

    assert [item["id"] for item in response["notifications"]] == [10, 11, 12]
    assert response["unread_count"] == 3


def test_teacher_seating_response_includes_only_assigned_seat_details(
    client, monkeypatch
):
    from backend.routes import seating_routes

    monkeypatch.setattr(seating_routes, "get_current_teacher", lambda: {"id": 6})
    monkeypatch.setattr(seating_routes, "get_teacher_exam_ids", lambda teacher_id: [3])
    monkeypatch.setattr(
        seating_routes,
        "fetch_all",
        lambda query, params=(): (
            [{"id": 7, "exam_id": 3, "status": "GENERATED"}]
            if "SELECT * FROM seating_arrangements" in query
            else [{"exam_id": 3, "roll_no": "CS26-003", "seat_number": "A01"}]
        ),
    )
    sign_in(client, "TEACHER", email="teacher@example.test")

    response = client.get("/api/seating").get_json()

    assert response["arrangements"] == [
        {"id": 7, "exam_id": 3, "status": "GENERATED"}
    ]
    assert response["assignments"] == [
        {"exam_id": 3, "roll_no": "CS26-003", "seat_number": "A01"}
    ]


def test_notification_page_renders_untrusted_content_as_text():
    from pathlib import Path

    page = (
        Path(__file__).parent.parent
        / "frontend"
        / "pages"
        / "notifications.html"
    ).read_text(encoding="utf-8")

    assert "title.textContent = notification.title" in page
    assert "message.textContent = notification.message" in page
    assert "notifications || []).map" not in page


def test_teacher_reports_show_registered_counts_and_seat_details(monkeypatch):
    from backend.services import report_service

    queries = []
    monkeypatch.setattr(
        report_service,
        "fetch_all",
        lambda query, params=(): queries.append((query, params)) or [],
    )

    report_service.get_reports([2, 3])

    exam_summary_query, exam_summary_params = next(
        (query, params)
        for query, params in queries
        if "AS registered_students" in query
    )
    assert "FROM exam_students es" in exam_summary_query
    assert "AS students_assigned" in exam_summary_query
    assert exam_summary_params == (2, 3)
    assert any("arr.status AS arrangement_status" in query for query, _ in queries)


def test_teacher_student_export_only_includes_assigned_exam_rosters(client, monkeypatch):
    from backend.routes import student_routes

    captured = {}
    monkeypatch.setattr(student_routes, "get_current_teacher", lambda: {"id": 6})
    monkeypatch.setattr(student_routes, "get_teacher_exam_ids", lambda teacher_id: [3, 5])
    monkeypatch.setattr(
        student_routes,
        "fetch_all",
        lambda query, params=(): captured.update(query=query, params=params) or [],
    )
    sign_in(client, "TEACHER", email="teacher@example.test")

    response = client.get("/api/students/export")

    assert response.status_code == 200
    assert "INNER JOIN exam_students" in captured["query"]
    assert captured["params"] == (3, 5)


def test_teacher_cannot_mark_attendance_for_unassigned_exam(client, monkeypatch):
    from backend.routes import attendance_routes

    marked = []
    monkeypatch.setattr(attendance_routes, "get_current_teacher", lambda: {"id": 6})
    monkeypatch.setattr(attendance_routes, "get_teacher_exam_ids", lambda teacher_id: [3])
    monkeypatch.setattr(
        attendance_routes,
        "mark_attendance",
        lambda *args: marked.append(args),
    )
    sign_in(client, "TEACHER", email="teacher@example.test")

    response = client.post(
        "/api/attendance",
        json={"student_id": 11, "exam_id": 4, "present_status": 1},
    )

    assert response.status_code == 403
    assert not marked


def test_teacher_cannot_generate_seating_for_unassigned_exam(client, monkeypatch):
    from backend.routes import seating_routes

    generated = []
    monkeypatch.setattr(seating_routes, "get_current_teacher", lambda: {"id": 6})
    monkeypatch.setattr(seating_routes, "get_teacher_exam_ids", lambda teacher_id: [3])
    monkeypatch.setattr(
        seating_routes,
        "generate_exam_arrangement",
        lambda *args: generated.append(args),
    )
    sign_in(client, "TEACHER", email="teacher@example.test")

    response = client.post("/api/seating/generate", json={"exam_id": 4})

    assert response.status_code == 403
    assert not generated


@pytest.mark.parametrize(
    ("module_name", "path", "response_key"),
    [
        ("exam_routes", "/api/exams?exam_id=999", "exams"),
        ("timetable_routes", "/api/timetable?exam_id=999", "timetable"),
    ],
)
def test_teacher_exam_and_timetable_lists_are_assignment_scoped(
    client, monkeypatch, module_name, path, response_key
):
    from backend.routes import exam_routes, timetable_routes

    route_module = {
        "exam_routes": exam_routes,
        "timetable_routes": timetable_routes,
    }[module_name]
    monkeypatch.setattr(route_module, "get_current_teacher", lambda: {"id": 6})
    monkeypatch.setattr(route_module, "get_teacher_exam_ids", lambda teacher_id: [3])
    captured = {}
    monkeypatch.setattr(
        route_module,
        "fetch_all",
        lambda query, params=(): captured.update(query=query, params=params) or [],
    )
    sign_in(client, "TEACHER", email="teacher@example.test")

    response = client.get(path)

    assert response.status_code == 200
    assert response.get_json()[response_key] == []
    assert captured["params"] == (3,)
    assert "IN (%s)" in captured["query"]


def test_only_admin_can_use_seat_swap_endpoint(client, monkeypatch):
    from backend.routes import seating_routes

    calls = []
    monkeypatch.setattr(
        seating_routes,
        "swap_student_assignments",
        lambda *args: calls.append(args),
    )

    sign_in(client, "TEACHER")
    assert client.post(
        "/api/seating/swap",
        json={"arrangement_id": 1, "first_student_id": 11, "second_student_id": 12},
    ).status_code == 403

    sign_in(client, "ADMIN")
    response = client.post(
        "/api/seating/swap",
        json={"arrangement_id": 1, "first_student_id": 11, "second_student_id": 12},
    )
    assert response.status_code == 200
    assert calls == [(1, 11, 12)]
