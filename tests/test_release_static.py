"""Self-contained deployment hygiene checks; no Flask dependency required."""
from pathlib import Path
import ast
import re

ROOT = Path(__file__).resolve().parents[1]


def test_public_assets_contain_no_server_secrets():
    for path in (ROOT / 'frontend').rglob('*'):
        if path.suffix not in ('.js', '.html', '.css'):
            continue
        src = path.read_text(encoding='utf-8')
        assert not re.search(r'AIza[0-9A-Za-z_-]{30,}', src), str(path)
        assert 'GEMINI_API_KEY=' not in src, str(path)


def test_release_has_no_embedded_secrets_or_virtualenv():
    # Developer-local files are allowed, but must never be tracked or packaged.
    import subprocess
    ignore_file = (ROOT / '.gitignore').read_text(encoding='utf-8')
    for pattern in ('.env', '.venv', 'venv', 'student_data.json', 'faculty_data.json'):
        assert pattern in ignore_file, f"Missing ignore rule: {pattern}"
    if (ROOT / '.git').exists():
        tracked = subprocess.run(
            ['git', '-C', str(ROOT), 'ls-files', '--cached', '-z'],
            capture_output=True, check=True
        ).stdout.decode('utf-8', errors='replace').split('\0')
        for name in tracked:
            path = Path(name)
            assert path.name not in {'.env', 'student_data.json', 'faculty_data.json'}
            assert not any(part in {'.venv', 'venv'} for part in path.parts)



def test_app_and_gemini_are_valid_python():
    for path in (ROOT / 'backend').glob('*.py'):
        ast.parse(path.read_text(encoding='utf-8'), filename=str(path))


def test_render_and_ci_configuration_present():
    render = (ROOT / 'render.yaml').read_text(encoding='utf-8')
    ci = (ROOT / '.github/workflows/tests.yml').read_text(encoding='utf-8')
    assert 'gunicorn backend.app:app' in render
    assert 'pytest' in ci
    assert 'FACULTY_ADMIN_TOKEN' in render


def test_smoke_script_is_read_only():
    src = (ROOT / 'scripts/smoke_test.py').read_text(encoding='utf-8')
    assert 'Request(' in src and 'urlopen(' in src
    assert 'get-student-data' not in src
    assert 'save-student-data' not in src
    assert 'study-assistant' not in src
