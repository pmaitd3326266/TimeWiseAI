"""Cross-module contract tests. Uses temp files and no real Gemini requests."""
import pytest

from algorithms.subjects_data import BRANCHES, SUBJECTS
from backend import app as module


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(module, 'FACULTY_FILE', tmp_path / 'faculty.json')
    monkeypatch.setattr(module, 'STUDENT_FILE', tmp_path / 'students.json')
    monkeypatch.setenv('FACULTY_ADMIN_TOKEN', 'R' * 40)
    module.rate_state.clear()
    module.app.config['TESTING'] = True
    with module.app.test_client() as api:
        yield api
    module.rate_state.clear()


def first_valid_subject():
    # Use actual current subject data, not hardcoded codes that may later change.
    for branch, stream in BRANCHES.items():
        for semester in range(1, 9):
            items = SUBJECTS.get(stream, {}).get(f'semester_{semester}', [])
            if not items:
                continue
            first = items[0]
            code = first['subjects'][0][0] if isinstance(first, dict) else first[0]
            return branch, semester, code
    raise AssertionError('No subjects configured')


@pytest.mark.parametrize('field,value', [
    ('semester', True), ('semester', 1.5), ('semester', '1.5'),
    ('weekly_lectures', True), ('weekly_lectures', 2.7),
    ('weekly_lectures', '2.7'), ('weekly_lectures', None),
])
def test_faculty_rejects_fractional_and_boolean_counts(client, field, value):
    branch, semester, code = first_valid_subject()
    record = {'faculty_name': 'Demo Teacher', 'faculty_id': 'DEMO01',
              'branch': branch, 'semester': semester, 'subject': code,
              'weekly_lectures': 2}
    record[field] = value
    response = client.post('/api/save-faculty', json=record,
                           headers={'X-Faculty-Token': 'R' * 40})
    assert response.status_code == 400
    assert not module.FACULTY_FILE.exists()


def test_faculty_save_generate_end_to_end(client):
    branch, semester, code = first_valid_subject()
    record = {'faculty_name': 'Demo Teacher', 'faculty_id': 'DEMO01',
              'branch': branch, 'semester': str(semester), 'subject': code,
              'weekly_lectures': '3'}
    assert client.post('/api/save-faculty', json=record).status_code == 403
    saved = client.post('/api/save-faculty', json=record,
                        headers={'X-Faculty-Token': 'R' * 40})
    assert saved.status_code == 200
    endpoint = f'/api/generate-timetable?branch={branch}&semester={semester}'
    assert client.get(endpoint).status_code == 403
    generated = client.get(endpoint, headers={'X-Faculty-Token': 'R' * 40})
    assert generated.status_code == 200
    days = generated.json['timetable']
    real = [slot for day in days.values() for slot in day if slot['subject'] != 'Free']
    assert len(real) == 3
    assert all(slot['faculty_id'] == 'DEMO01' and slot['subject'] == code for slot in real)


def test_student_save_load_access_boundary(client):
    data = {'studentName': 'Synthetic Test Student', 'subjects': ['Mathematics'],
            'studyHours': '2'}
    saved = client.post('/api/save-student-data', json=data)
    assert saved.status_code == 200
    key = saved.json['profileToken']
    query = {'studentName': data['studentName']}
    assert client.post('/api/get-student-data', json=query).status_code == 403
    assert client.post('/api/get-student-data', json=query,
                       headers={'X-Profile-Token': 'x' * 40}).status_code == 403
    result = client.post('/api/get-student-data', json=query,
                         headers={'X-Profile-Token': key})
    assert result.status_code == 200
    assert result.json['data']['subjects'] == ['Mathematics']
    assert '_token_hash' not in result.json['data']


def test_api_response_security_contract(client):
    for url in ('/', '/faculty', '/student', '/healthz', '/api/subjects?branch=invalid'):
        response = client.get(url)
        assert response.headers.get('X-Content-Type-Options') == 'nosniff'
        assert response.headers.get('X-Frame-Options') == 'DENY'
        assert "script-src 'self'" in response.headers.get('Content-Security-Policy', '')
    assert client.get('/healthz').json == {'status': 'ok'}


def test_cross_origin_student_write_blocked(client):
    result = client.post('/api/save-student-data', json={'studentName': 'Synthetic'},
                         headers={'Origin': 'https://attacker.invalid'})
    assert result.status_code == 403
    assert not module.STUDENT_FILE.exists()
