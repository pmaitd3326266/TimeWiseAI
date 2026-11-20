"""Focused unit tests for the Gemini integration. All network calls are mocked."""
import json

import pytest
import httpx
from backend import gemini_service as svc


@pytest.fixture
def fake_gemini(monkeypatch):
    """Mock the actual service boundary: no SDK or network calls occur."""
    calls = []
    state = {"response": "OK", "error": None}

    def fake_request(api_key, model, prompt, system_instruction, **kwargs):
        assert api_key == "fake-key-only-for-tests"
        calls.append({"model": model, "contents": prompt,
                      "system_instruction": system_instruction, **kwargs})
        if state["error"] is not None:
            raise state["error"]
        return state["response"]

    monkeypatch.setattr(svc, "get_gemini_config",
                        lambda: ("fake-key-only-for-tests", "fake-model"))
    monkeypatch.setattr(svc, "_gemini_request", fake_request)
    return state, calls


def valid_plan(**overrides):
    body = {
        "plan": [{"date": "2026-12-01", "sessions": [
            {"subject": "Physics", "topic": "Waves", "durationMinutes": 45, "activity": "Learn"}
        ]}], "notes": ["Review notes"],
    }
    body.update(overrides)
    return json.dumps(body)


def test_configuration_reads_environment(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "secret-test-key")
    monkeypatch.setenv("GEMINI_MODEL", "chosen-model")
    assert svc.get_gemini_config() == ("secret-test-key", "chosen-model")


def test_default_model(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", " test-key ")
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    assert svc.get_gemini_config() == ("test-key", svc.DEFAULT_GEMINI_MODEL)


@pytest.mark.parametrize("context,expected", [
    ({"subjects": "Physics"}, "Enrolled Subjects: Physics"),
    ({"subjects": [" Math ", "", "Physics"]}, "Math, Physics"),
    ({"pending_topics": "Vector calculus"}, "Vector calculus"),
    ({"pending_topics": [{"subject": "Physics", "topic": " Waves "}]}, "Physics: Waves"),
    ({"pending_topics": [{"subject": "", "topic": " Waves "}]}, "Waves"),
    ({"pending_topics": ["Revision", ""]}, "Revision"),
    ({"pending_topics": [{"subject": None, "topic": "Waves"}]}, "Waves"),
    ({"exam_date": "2026-12-01"}, "2026-12-01"),
    ({"available_hours": "4"}, "4 hours/day"),
])
def test_context_fields(context, expected):
    assert expected in svc.format_academic_context(**context)


def test_context_empty():
    assert "No profile details" in svc.format_academic_context()


def test_assistant_missing_key(monkeypatch):
    monkeypatch.setattr(svc, "get_gemini_config", lambda: ("", "fake-model"))
    with pytest.raises(svc.GeminiConfigError):
        svc.generate_study_assistant_response("Hello")


def test_assistant_success(fake_gemini):
    state, calls = fake_gemini
    state["response"] = "  Helpful answer  "
    result = svc.generate_study_assistant_response("Explain concepts", branch="CSE", subjects=["Math"])
    assert result == "Helpful answer"
    assert "Student Query:\nExplain concepts" in calls[0]["contents"]
    assert "CSE" in calls[0]["contents"]
    assert calls[0]["model"] == "fake-model"


@pytest.mark.parametrize("bad", [None, "", " \n", 123])
def test_assistant_empty_or_invalid_reply(fake_gemini, bad):
    state, _ = fake_gemini
    state["response"] = bad
    with pytest.raises(svc.GeminiAPIError, match="empty response|Please enter a question"):
        svc.generate_study_assistant_response("Hello")


def test_assistant_network_error(fake_gemini):
    state, _ = fake_gemini
    state["error"] = svc.GeminiAPIError("Unable to connect to Gemini")
    with pytest.raises(svc.GeminiAPIError, match="Unable to connect"):
        svc.generate_study_assistant_response("Hello")


def test_planner_missing_key(monkeypatch):
    monkeypatch.setattr(svc, "get_gemini_config", lambda: ("", "fake-model"))
    with pytest.raises(svc.GeminiConfigError):
        svc.generate_adaptive_study_plan(subjects=["Math"])


@pytest.mark.parametrize("hours", ["0", "17", "nonsense", "nan", "inf", None])
def test_planner_invalid_hours_use_default(fake_gemini, hours):
    state, calls = fake_gemini
    state["response"] = valid_plan()
    svc.generate_adaptive_study_plan(subjects=["Physics"], available_hours=hours, current_date="2026-11-20")
    assert "240 minutes" in calls[0]["contents"]


def test_planner_valid_hours_and_dates(fake_gemini):
    state, calls = fake_gemini
    state["response"] = valid_plan()
    result = svc.generate_adaptive_study_plan(subjects=["Physics"], pending_topics=[{"subject":"Physics","topic":"Waves"}], completed_topics=[{"subject":"Physics","topic":"Optics"}], available_hours="2.5", current_date="2026-11-20", exam_date="2026-12-01")
    assert result["plan"][0]["sessions"][0]["durationMinutes"] == 45
    assert "150 minutes" in calls[0]["contents"]
    assert "Optics" in calls[0]["contents"]
    assert "2026-11-20" in calls[0]["contents"]


def test_planner_accepts_string_topics(fake_gemini):
    state, calls = fake_gemini
    state["response"] = valid_plan()
    svc.generate_adaptive_study_plan(subjects="Physics", pending_topics="Waves", completed_topics="Optics")
    assert "Waves" in calls[0]["contents"]
    assert "Optics" in calls[0]["contents"]


def test_planner_handles_null_values_in_topics(fake_gemini):
    state, calls = fake_gemini
    state["response"] = valid_plan()
    svc.generate_adaptive_study_plan(subjects=["Physics"], pending_topics=[{"subject":None,"topic":"Waves"}], completed_topics=[{"subject":"Physics","topic":None}])
    assert "Waves" in calls[0]["contents"]


def test_planner_requires_subject_or_pending_topic(fake_gemini):
    with pytest.raises(svc.GeminiAPIError, match="at least one subject"):
        svc.generate_adaptive_study_plan(subjects=[], pending_topics=[])


def test_planner_connection_error(fake_gemini):
    state, _ = fake_gemini
    state["error"] = svc.GeminiAPIError("Unable to connect to Gemini")
    with pytest.raises(svc.GeminiAPIError, match="Unable to connect"):
        svc.generate_adaptive_study_plan(subjects=["Physics"])


@pytest.mark.parametrize("bad", [None, "", 5])
def test_planner_empty_response(fake_gemini, bad):
    state, _ = fake_gemini
    state["response"] = bad
    with pytest.raises(svc.GeminiAPIError, match="empty response"):
        svc.generate_adaptive_study_plan(subjects=["Physics"])


@pytest.mark.parametrize("raw", [
    "not json", "[]", "{}", '{"plan":[]}', '{"plan":{}}',
    '{"plan":[{}]}', '{"plan":[{"date":"2026-12-01","sessions":[]}]}'
])
def test_planner_rejects_invalid_json(fake_gemini, raw):
    state, _ = fake_gemini
    state["response"] = raw
    with pytest.raises(svc.GeminiAPIError, match="Unable to parse"):
        svc.generate_adaptive_study_plan(subjects=["Physics"])


def test_planner_parses_markdown_fenced_json(fake_gemini):
    state, _ = fake_gemini
    state["response"] = "```json\n" + valid_plan() + "\n```"
    result = svc.generate_adaptive_study_plan(subjects=["Physics"])
    assert result["notes"] == ["Review notes"]


def test_planner_skips_invalid_days_and_sessions(fake_gemini):
    state, _ = fake_gemini
    state["response"] = valid_plan(plan=[
        "invalid", {"date":"", "sessions":[{"subject":"Math"}]},
        {"date":"2026-12-01", "sessions":"not-list"},
        {"date":"2026-12-02", "sessions":[None, {"subject":"Physics", "topic":"Waves", "durationMinutes":0, "activity":""}]}
    ], notes=["", "Review", None])
    result = svc.generate_adaptive_study_plan(subjects=["Physics"])
    assert len(result["plan"]) == 1
    assert result["plan"][0]["sessions"][0]["durationMinutes"] == 60
    assert result["plan"][0]["sessions"][0]["activity"] == "Learn"


@pytest.mark.parametrize("invalid_duration", ["nonsense", None, -20])
def test_planner_sanitizes_duration(fake_gemini, invalid_duration):
    state, _ = fake_gemini
    state["response"] = valid_plan(plan=[{"date":"2026-12-01", "sessions":[{"subject":"Physics", "topic":"Waves", "durationMinutes":invalid_duration}]}])
    result = svc.generate_adaptive_study_plan(subjects=["Physics"])
    assert result["plan"][0]["sessions"][0]["durationMinutes"] == 60


def test_planner_notes_not_array(fake_gemini):
    state, _ = fake_gemini
    state["response"] = valid_plan(notes="not-array")
    assert svc.generate_adaptive_study_plan(subjects=["Physics"])["notes"] == []


def test_assistant_provider_error(fake_gemini):
    state, _ = fake_gemini
    state["error"] = svc.GeminiAPIError("The AI service could not complete the request")
    with pytest.raises(svc.GeminiAPIError, match="could not complete"):
        svc.generate_study_assistant_response("Hello")


def test_planner_provider_error(fake_gemini):
    state, _ = fake_gemini
    state["error"] = svc.GeminiAPIError("The AI service could not complete the request")
    with pytest.raises(svc.GeminiAPIError, match="could not complete"):
        svc.generate_adaptive_study_plan(subjects=["Physics"])


@pytest.mark.parametrize("status,phrase", [
    (403, "access was denied"),
    (404, "model is unavailable"),
    (429, "rate-limited"),
    (503, "could not complete"),
])
def test_httpx_http_status_is_sanitized(monkeypatch, status, phrase):
    class Client:
        def __init__(self, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def post(self, url, headers, json):
            request = httpx.Request("POST", url)
            response = httpx.Response(status, request=request)
            response.raise_for_status()
    monkeypatch.setattr(svc.httpx, "Client", Client)
    with pytest.raises(svc.GeminiAPIError, match=phrase):
        svc._gemini_request("test-key", "fake-model", "Hi", "Instruction")


def test_httpx_timeout_is_handled(monkeypatch):
    class Client:
        def __init__(self, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def post(self, *args, **kwargs):
            raise httpx.ReadTimeout("timeout")
    monkeypatch.setattr(svc.httpx, "Client", Client)
    with pytest.raises(svc.GeminiAPIError, match="timed out"):
        svc._gemini_request("test-key", "fake-model", "Hi", "Instruction")


def test_httpx_valid_response_and_ipv4_binding(monkeypatch):
    config = {}
    class Client:
        def __init__(self, **kwargs): config.update(kwargs)
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def post(self, url, headers, json):
            config["payload"] = json
            return httpx.Response(200, json={"candidates":[{"content":{"parts":[
                {"text":"Hello"}, {"thoughtSignature":"opaque"}, {"text":"!"}
            ]}}]}, request=httpx.Request("POST", url))
    def fake_transport(**kwargs):
        config["bind"] = kwargs["local_address"]
        return object()
    monkeypatch.setattr(svc.httpx, "Client", Client)
    monkeypatch.setattr(svc.httpx, "HTTPTransport", fake_transport)
    result = svc._gemini_request("test-key", "fake-model", "Say hi", "Be concise", json_output=True)
    assert result == "Hello!"
    assert config["bind"] == "0.0.0.0"
    assert config["payload"]["generationConfig"]["responseMimeType"] == "application/json"
