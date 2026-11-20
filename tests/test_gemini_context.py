from backend.gemini_service import format_academic_context


def test_empty_context():
    assert "No profile details" in format_academic_context()


def test_academic_context_includes_subjects():
    result = format_academic_context(branch="CSE", semester="3", subjects=["Math", "Physics"])
    assert "CSE" in result and "Math" in result and "Physics" in result


def test_pending_topic_context():
    result = format_academic_context(pending_topics=[{"subject": "Math", "topic": "Vectors"}])
    assert "Math: Vectors" in result
