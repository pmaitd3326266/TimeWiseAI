"""No paid model API calls; use fixtures to verify API contracts."""
import pytest
from backend import app as module


@pytest.fixture
def client(monkeypatch):
    module.app.config["TESTING"] = True
    module.rate_state.clear()
    with module.app.test_client() as client:
        yield client


def test_assistant_success(client, monkeypatch):
    received = {}
    def fake_ai(**kwargs):
        received.update(kwargs)
        return "Focus on the example first."
    monkeypatch.setattr(module, "generate_study_assistant_response", fake_ai)
    result = client.post("/api/ai/study-assistant", json={"message":"Explain pointers", "subjects":["C++"]})
    assert result.status_code == 200
    assert result.json["reply"].startswith("Focus")
    assert received["message"] == "Explain pointers"


@pytest.mark.parametrize("payload", [None, [], {}, {"message": 42}, {"message":"   "}])
def test_assistant_bad_inputs(client, payload):
    if payload is None:
        result = client.post("/api/ai/study-assistant", data="null", content_type="application/json")
    else:
        result = client.post("/api/ai/study-assistant", json=payload)
    assert result.status_code == 400


def test_assistant_configuration_error(client, monkeypatch):
    def missing(**kwargs):
        raise module.GeminiConfigError("Gemini is not configured")
    monkeypatch.setattr(module, "generate_study_assistant_response", missing)
    response = client.post("/api/ai/study-assistant", json={"message":"Help"})
    assert response.status_code == 503


def test_assistant_api_error(client, monkeypatch):
    def down(**kwargs):
        raise module.GeminiAPIError("Model unavailable")
    monkeypatch.setattr(module, "generate_study_assistant_response", down)
    response = client.post("/api/ai/study-assistant", json={"message":"Help"})
    assert response.status_code == 502


def test_assistant_sanitizes_large_lists(client, monkeypatch):
    received = {}
    monkeypatch.setattr(module, "generate_study_assistant_response", lambda **kwargs: received.update(kwargs) or "Done")
    response = client.post("/api/ai/study-assistant", json={"message":"Help", "subjects":["Subject"] * 55})
    assert response.status_code == 200
    assert len(received["subjects"]) == 30


def test_planner_requires_academic_context(client):
    response = client.post("/api/ai/adaptive-plan", json={"examDate":"2026-12-01"})
    assert response.status_code == 400


def test_planner_success(client, monkeypatch):
    monkeypatch.setattr(module, "generate_adaptive_study_plan", lambda **kwargs: {
        "plan": [{"date": "2026-12-01", "sessions": [{"subject":"Physics", "topic":"Waves", "durationMinutes":45,"activity":"Learn"}]}],
        "notes": ["Review daily"]})
    response = client.post("/api/ai/adaptive-plan", json={"examDate":"2026-12-15", "subjects":["Physics"]})
    assert response.status_code == 200
    assert response.json["plan"][0]["sessions"][0]["topic"] == "Waves"


def test_planner_bad_json(client):
    response = client.post("/api/ai/adaptive-plan", json=["wrong"])
    assert response.status_code == 400


def test_planner_service_error(client, monkeypatch):
    def missing(**kwargs):
        raise module.GeminiConfigError("No key")
    monkeypatch.setattr(module, "generate_adaptive_study_plan", missing)
    response = client.post("/api/ai/adaptive-plan", json={"examDate":"2026-12-15","subjects":["Physics"]})
    assert response.status_code == 503


def test_rate_limit(client, monkeypatch):
    monkeypatch.setattr(module, "generate_study_assistant_response", lambda **kwargs: "OK")
    responses = [client.post("/api/ai/study-assistant", json={"message":"Study"}) for _ in range(13)]
    assert all(r.status_code == 200 for r in responses[:12])
    assert responses[12].status_code == 429
