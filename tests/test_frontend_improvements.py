"""Regression checks for front-end accessibility and safe DOM practices.

These static checks complement, but do not replace, browser-based accessibility tests.
"""
from html.parser import HTMLParser
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1] / "frontend"


class Elements(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements = []

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))


def elements(filename):
    parser = Elements()
    parser.feed((ROOT / filename).read_text(encoding="utf-8"))
    return parser.elements


def get_id(filename, id_):
    return [(tag, attrs) for tag, attrs in elements(filename) if attrs.get("id") == id_]


@pytest.mark.parametrize("filename,element_id", [
    ("faculty.html", "facultyStatus"),
    ("student.html", "studentFeedback"),
])
def test_feedback_is_announced(filename, element_id):
    result = get_id(filename, element_id)
    assert len(result) == 1
    assert result[0][1].get("role") == "status"
    assert result[0][1].get("aria-live") == "polite"


def test_faculty_form_has_functional_save_button():
    assert get_id("faculty.html", "saveFacultyButton") == [("button", {"type": "button", "id": "saveFacultyButton"})]
    assert "('Faculty details form is ready!')" not in (ROOT / "faculty.html").read_text(encoding="utf-8")


def test_timetable_result_can_receive_keyboard_focus():
    assert get_id("faculty.html", "timetableResult")[0][1].get("tabindex") == "-1"


def test_chat_trigger_discloses_expansion_and_controls():
    attrs = get_id("student.html", "aiChatToggleBtn")[0][1]
    assert attrs["aria-expanded"] == "false"
    assert attrs["aria-controls"] == "aiChatPanel"


def test_chat_is_hidden_from_assistive_technology_initially():
    assert get_id("student.html", "aiChatPanel")[0][1]["aria-hidden"] == "true"


def test_chat_keyboard_closing_and_focus_restoration():
    src = (ROOT / "assets/student.js").read_text(encoding="utf-8")
    assert 'event.key === "Escape"' in src
    assert "aiChatToggleBtn.focus()" in src
    assert 'setAttribute("aria-expanded"' in src


def test_cell_editing_supports_keyboard_after_rerender():
    src = (ROOT / "assets/faculty.js").read_text(encoding="utf-8")
    assert "td.onkeydown = function" in src
    assert 'event.target !== td' in src
    assert 'event.key === "Escape"' in src
    assert 'subjLabel.htmlFor = subjInput.id' in src
    assert 'facLabel.htmlFor = facInput.id' in src


@pytest.mark.parametrize("name", ["faculty", "student"])
def test_status_updates_use_text_not_html(name):
    src = (ROOT / f"assets/{name}.js").read_text(encoding="utf-8")
    expected = "facultyStatus.textContent" if name == "faculty" else "studentFeedback.textContent"
    assert expected in src


@pytest.mark.parametrize("name", ["faculty", "student"])
def test_styles_provide_error_feedback_and_small_screen_layout(name):
    src = (ROOT / f"assets/{name}.css").read_text(encoding="utf-8")
    assert ".form-feedback.feedback-error" in src
    assert "overflow-x: auto" in src
