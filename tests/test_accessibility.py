"""Basic structural accessibility regression checks without third-party HTML parsers."""
from html.parser import HTMLParser
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1] / "frontend"


class AccessibilityParser(HTMLParser):
    """Collect HTML tags and meaningful skip-link text for structural checks."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.elements = []
        self._skip_link_depth = 0
        self.skip_link_text = ""

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        self.elements.append((tag, attributes))
        if tag == "a" and attributes.get("href") == "#main-content":
            self._skip_link_depth += 1

    def handle_endtag(self, tag):
        if tag == "a" and self._skip_link_depth:
            self._skip_link_depth -= 1

    def handle_data(self, data):
        if self._skip_link_depth:
            self.skip_link_text += data


def parse_file(filename):
    parser = AccessibilityParser()
    parser.feed((ROOT / filename).read_text(encoding="utf-8"))
    parser.close()
    return parser


@pytest.mark.parametrize("file", ["index.html", "student.html", "faculty.html"])
def test_page_has_main_and_skip_link(file):
    document = parse_file(file)
    assert any(attrs.get("id") == "main-content" for _, attrs in document.elements)
    assert any(tag == "a" and attrs.get("href") == "#main-content"
               for tag, attrs in document.elements)
    assert document.skip_link_text.strip()


@pytest.mark.parametrize("file", ["student.html", "faculty.html"])
def test_visible_form_fields_have_labels(file):
    document = parse_file(file)
    label_targets = {attrs.get("for") for tag, attrs in document.elements if tag == "label"}
    for tag, attrs in document.elements:
        if tag not in {"input", "select", "textarea"} or "id" not in attrs:
            continue
        if attrs.get("type") == "hidden":
            continue
        assert attrs["id"] in label_targets or attrs.get("aria-label"), (
            f"Unlabelled field: {file}#{attrs['id']}"
        )


@pytest.mark.parametrize("file", ["index.html", "student.html", "faculty.html"])
def test_document_language(file):
    document = parse_file(file)
    assert any(tag == "html" and attrs.get("lang") == "en"
               for tag, attrs in document.elements)
