"""Flask test-client tests. No real Gemini API requests or personal records."""
import pytest
from backend import app as module


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(module, "FACULTY_FILE", tmp_path / "faculty.json")
    monkeypatch.setattr(module, "STUDENT_FILE", tmp_path / "students.json")
    monkeypatch.setenv("FACULTY_ADMIN_TOKEN", "a" * 32)
    module.app.config["TESTING"] = True
    module.rate_state.clear()
    with module.app.test_client() as client:
        yield client


def test_healthcheck(client):
    assert client.get("/healthz").json == {"status": "ok"}


@pytest.mark.parametrize("page", ["/", "/faculty", "/student"])
def test_public_pages(client, page):
    response = client.get(page)
    assert response.status_code == 200
    assert b"TimeWise AI" in response.data


@pytest.mark.parametrize("route", ["/api/save-faculty", "/api/generate-timetable?branch=CSE&semester=1"])
def test_faculty_endpoints_reject_anonymous(client, route):
    response = client.post(route, json={}) if route.endswith("faculty") else client.get(route)
    assert response.status_code == 403


def test_faculty_rejects_short_token(client):
    result = client.post("/api/save-faculty", json={}, headers={"X-Faculty-Token": "wrong"})
    assert result.status_code == 403


def test_invalid_content_type(client):
    assert client.post("/api/save-student-data", data="hello", content_type="text/plain").status_code == 415


def test_cross_origin_mutation_denied(client):
    response = client.post("/api/save-student-data", json={}, headers={"Origin": "https://evil.example"})
    assert response.status_code == 403


def test_missing_student_name(client):
    assert client.post("/api/save-student-data", json={}).status_code == 400


def test_invalid_student_topics(client):
    assert client.post("/api/save-student-data", json={"studentName":"A", "studyTopics":{}}).status_code == 400


def test_student_profile_is_private(client):
    result = client.post("/api/save-student-data", json={"studentName":"Example", "subjects": ["Math"]})
    assert result.status_code == 200
    token = result.json["profileToken"]
    assert len(token) >= 32
    assert client.post("/api/get-student-data", json={"studentName":"Example"}).status_code == 403
    authorized = client.post("/api/get-student-data", json={"studentName":"Example"}, headers={"X-Profile-Token":token})
    assert authorized.status_code == 200
    assert "_token_hash" not in authorized.json["data"]
    assert authorized.json["data"]["subjects"] == ["Math"]


def test_profile_cannot_be_overwritten_without_token(client):
    first = client.post("/api/save-student-data", json={"studentName":"Alice", "subjects":["Math"]})
    assert first.status_code == 200
    second = client.post("/api/save-student-data", json={"studentName":"Alice", "subjects":["Hacked"]})
    assert second.status_code == 403
    original = client.post("/api/get-student-data", json={"studentName":"Alice"}, headers={"X-Profile-Token":first.json["profileToken"]})
    assert original.json["data"]["subjects"] == ["Math"]


def test_profile_update_retains_token(client):
    first = client.post("/api/save-student-data", json={"studentName":"Alice"})
    token = first.json["profileToken"]
    updated = client.post("/api/save-student-data", json={"studentName":"Alice", "subjects":["Physics"]}, headers={"X-Profile-Token":token})
    assert updated.status_code == 200
    assert "profileToken" not in updated.json


def test_get_profile_requires_post(client):
    assert client.get("/api/get-student-data?studentName=Alice").status_code == 405


def test_student_records_not_shared_through_name(client):
    assert client.post("/api/get-student-data", json={"studentName":"Unknown"}).status_code == 404


def test_subject_endpoint_rejects_invalid_branch(client):
    assert client.get("/api/subjects?branch=INVALID&semester=1").status_code == 400


def test_ai_message_rejects_empty(client):
    assert client.post("/api/ai/study-assistant", json={"message":""}).status_code == 400


def test_ai_message_rejects_oversize(client):
    assert client.post("/api/ai/study-assistant", json={"message":"a"*2001}).status_code == 400


def test_adaptive_plan_requires_exam_date(client):
    assert client.post("/api/ai/adaptive-plan", json={}).status_code == 400


def test_security_headers(client):
    result = client.get("/")
    assert result.headers["X-Content-Type-Options"] == "nosniff"
    assert result.headers["X-Frame-Options"] == "DENY"


def test_request_size_limit(client):
    result = client.post("/api/save-student-data", data="x" * (300 * 1024), content_type="application/json")
    assert result.status_code == 413


def test_invalid_faculty_branch(client):
    result = client.post("/api/save-faculty", json={"faculty_name":"J", "faculty_id":"T1", "branch":"FAKE", "semester":1, "subject":"X", "weekly_lectures":2}, headers={"X-Faculty-Token":"a"*32})
    assert result.status_code == 400


def test_valid_faculty_and_timetable(client):
    data = {"faculty_name":"Teacher", "faculty_id":"T1", "branch":"CSE", "semester":1, "subject":None, "weekly_lectures":2}
    from algorithms.subjects_data import SUBJECTS, BRANCHES
    records = SUBJECTS[BRANCHES["CSE"]]["semester_1"]
    entry = records[0]
    data["subject"] = entry["subjects"][0][0] if isinstance(entry, dict) else entry[0]
    saved = client.post("/api/save-faculty", json=data, headers={"X-Faculty-Token":"a"*32})
    assert saved.status_code == 200, saved.json
    result = client.get("/api/generate-timetable?branch=CSE&semester=1", headers={"X-Faculty-Token":"a"*32})
    assert result.status_code == 200, result.json
    assert len(result.json["timetable"]) == 6


def test_faculty_assignment_upsert_preserves_other_subjects(client):
    from algorithms.subjects_data import SUBJECTS, BRANCHES
    entry = SUBJECTS[BRANCHES["CSE"]]["semester_1"][0]
    options = entry["subjects"] if isinstance(entry, dict) else SUBJECTS[BRANCHES["CSE"]]["semester_1"]
    if len(options) < 2:
        pytest.skip("Dataset has only one subject for semester 1")
    for subject, _ in options[:2]:
        result = client.post("/api/save-faculty", json={"faculty_name":"A","faculty_id":"T1", "branch":"CSE", "semester":1, "subject":subject,"weekly_lectures":2}, headers={"X-Faculty-Token":"a"*32})
        assert result.status_code == 200
    assert len(module.read_json(module.FACULTY_FILE, [])) == 2


def test_asset_loading_and_csp(client):
    response = client.get("/assets/student.js")
    assert response.status_code == 200
    assert b"generateAdaptivePlanWithGemini" in response.data
    index = client.get("/")
    assert "script-src 'self'" in index.headers["Content-Security-Policy"]


def test_subject_endpoint_rejects_out_of_range_semester(client):
    assert client.get("/api/subjects?branch=CSE&semester=99").status_code == 400
