"""Regression tests for app.py: validation, storage failures and API boundaries.

All data is synthetic; local test-client calls never contact Gemini or mutate user files.
"""
import json
import pytest
from backend import app as module


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(module, "FACULTY_FILE", tmp_path / "faculty.json")
    monkeypatch.setattr(module, "STUDENT_FILE", tmp_path / "students.json")
    monkeypatch.setenv("FACULTY_ADMIN_TOKEN", "F" * 32)
    module.rate_state.clear()
    module.app.config["TESTING"] = True
    with module.app.test_client() as session:
        yield session
    module.rate_state.clear()


FACULTY_HEADERS = {"X-Faculty-Token": "F" * 32}


def test_student_partial_update_preserves_existing_fields(client):
    initial = client.post("/api/save-student-data", json={
        "studentName": "Example Learner", "branch": "CSE", "semester": "3",
        "subjects": ["Physics"], "studyHours": "2", "studyTopics": []
    })
    assert initial.status_code == 200
    token = initial.json["profileToken"]
    updated = client.post("/api/save-student-data", json={
        "studentName": "Example Learner", "studyHours": "4"
    }, headers={"X-Profile-Token": token})
    assert updated.status_code == 200
    loaded = client.post("/api/get-student-data", json={
        "studentName": "Example Learner"
    }, headers={"X-Profile-Token": token})
    assert loaded.status_code == 200
    assert loaded.json["data"]["subjects"] == ["Physics"]
    assert loaded.json["data"]["branch"] == "CSE"
    assert loaded.json["data"]["studyHours"] == "4"
    assert "_token_hash" not in loaded.json["data"]


@pytest.mark.parametrize("extra", [
    {"branch": "NOT_A_BRANCH"},
    {"semester": "nope"}, {"semester": "9"}, {"semester": True},
    {"studyHours": "NaN"}, {"studyHours": "Infinity"},
    {"studyHours": 0}, {"studyHours": 25}, {"studyHours": True},
    {"examDate": "31-12-2026"},
    {"subjects": ["Math", None]},
    {"subjects": ["x" * 151]},
    {"studyTopics": ["not-an-object"]},
    {"studyTopics": [{"topic": {"nested": "value"}}]},
    {"studyTopics": [{"topic": "x" * 501}]},
])
def test_rejects_invalid_student_fields(client, extra):
    result = client.post("/api/save-student-data", json={
        "studentName": "Synthetic", **extra
    })
    assert result.status_code == 400
    assert result.json["success"] is False
    assert not module.STUDENT_FILE.exists()


@pytest.mark.parametrize("name", ["\nBad", "Bad\tName", "x" * 101])
def test_rejects_invalid_student_names(client, name):
    result = client.post("/api/save-student-data", json={"studentName": name})
    assert result.status_code == 400


def test_corrupt_student_json_returns_controlled_error(client):
    module.STUDENT_FILE.write_text("{not json", encoding="utf-8")
    save = client.post("/api/save-student-data", json={"studentName": "Synthetic"})
    lookup = client.post("/api/get-student-data", json={"studentName": "Synthetic"})
    assert save.status_code == 500
    assert lookup.status_code == 500
    assert "Traceback" not in save.get_data(as_text=True)


def test_malformed_stored_student_records_do_not_crash(client):
    module.STUDENT_FILE.write_text(json.dumps({"students": [None]}), encoding="utf-8")
    assert client.post("/api/save-student-data", json={"studentName": "Synthetic"}).status_code == 500
    assert client.post("/api/get-student-data", json={"studentName": "Synthetic"}).status_code == 500


def test_missing_profile_and_token_hash_are_handled(client):
    module.STUDENT_FILE.write_text(json.dumps({"students": [
        {"studentName": "Legacy", "_token_hash": None}
    ]}), encoding="utf-8")
    response = client.post("/api/get-student-data", json={"studentName": "Legacy"},
                           headers={"X-Profile-Token": "T" * 40})
    assert response.status_code == 403


def test_missing_faculty_configuration_denies_management(client, monkeypatch):
    monkeypatch.delenv("FACULTY_ADMIN_TOKEN", raising=False)
    assert client.post("/api/save-faculty", json={}, headers=FACULTY_HEADERS).status_code == 403


def test_invalid_faculty_json_returns_400(client):
    assert client.post("/api/save-faculty", json=[], headers=FACULTY_HEADERS).status_code == 400


def test_invalid_faculty_lecture_count_returns_400(client):
    response = client.post("/api/save-faculty", json={
        "faculty_name": "Teacher", "faculty_id": "T01", "branch": "CSE",
        "semester": "2", "subject": "A", "weekly_lectures": "not-a-number"
    }, headers=FACULTY_HEADERS)
    assert response.status_code == 400


def test_malformed_faculty_file_produces_controlled_error(client):
    module.FACULTY_FILE.write_text(json.dumps([None]), encoding="utf-8")
    result = client.get("/api/generate-timetable?branch=CSE&semester=1", headers=FACULTY_HEADERS)
    assert result.status_code == 422


def test_subject_endpoint_rejects_non_numeric_semester(client):
    response = client.get("/api/subjects?branch=CSE&semester=not-a-number")
    assert response.status_code == 400


def test_request_origin_with_wrong_host_is_denied(client):
    result = client.post("/api/save-student-data", json={"studentName": "Test"},
                         headers={"Origin": "https://untrusted.example"})
    assert result.status_code == 403


def test_faculty_storage_failure_does_not_leak_exception(client, monkeypatch):
    from algorithms.subjects_data import SUBJECTS, BRANCHES
    first = SUBJECTS[BRANCHES["CSE"]]["semester_1"][0]
    subject_code = first["subjects"][0][0] if isinstance(first, dict) else first[0]
    def fail(*args, **kwargs):
        raise OSError("internal path details must not be returned")
    monkeypatch.setattr(module, "write_json", fail)
    result = client.post("/api/save-faculty", json={
        "faculty_name": "Example", "faculty_id": "F001", "branch": "CSE",
        "semester": 1, "subject": subject_code, "weekly_lectures": 2
    }, headers=FACULTY_HEADERS)
    assert result.status_code == 500
    assert "internal path details" not in result.get_data(as_text=True)


def test_study_assistant_unexpected_provider_exception_is_generic(client, monkeypatch):
    def fail(**kwargs):
        raise RuntimeError("private provider information")
    monkeypatch.setattr(module, "generate_study_assistant_response", fail)
    response = client.post("/api/ai/study-assistant", json={"message": "Help me learn"})
    assert response.status_code == 500
    assert "private provider information" not in response.get_data(as_text=True)


def test_adaptive_planner_unexpected_provider_exception_is_generic(client, monkeypatch):
    def fail(**kwargs):
        raise RuntimeError("private provider information")
    monkeypatch.setattr(module, "generate_adaptive_study_plan", fail)
    response = client.post("/api/ai/adaptive-plan", json={
        "examDate": "2027-01-01", "subjects": ["Physics"]
    })
    assert response.status_code == 500
    assert "private provider information" not in response.get_data(as_text=True)


def test_save_student_rate_limit_returns_429(client, monkeypatch):
    monkeypatch.setattr(module, "rate_allowed", lambda bucket, limit, window=60: False)
    result = client.post("/api/save-student-data", json={"studentName": "Synthetic"})
    assert result.status_code == 429
    assert not module.STUDENT_FILE.exists()


def test_oversized_student_request_returns_413(client):
    result = client.post("/api/save-student-data", data="x" * 300_000,
                         content_type="application/json")
    assert result.status_code == 413
