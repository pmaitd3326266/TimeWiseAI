"""Non-destructive real-browser checks for TimeWise AI.

Uses actual HTML/JavaScript served by a running app, but intercepts write and AI
API calls with synthetic responses. No student data is written and no Gemini
quota is consumed. Run: python scripts/browser_workflows.py http://127.0.0.1:5000
Requires: python -m pip install playwright; python -m playwright install chromium
"""
import argparse
import json
import os
import sys
from datetime import date, timedelta


def check(condition, message):
    if not condition:
        raise AssertionError(message)
    print(f"PASS {message}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('base_url', nargs='?', default='http://127.0.0.1:5000')
    parser.add_argument('--headed', action='store_true', help='Show the real browser')
    args = parser.parse_args()
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print('Missing browser runner: python -m pip install playwright', file=sys.stderr)
        return 2

    base_url = args.base_url.rstrip('/')
    errors = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=not args.headed, executable_path=os.environ.get("TIMEWISE_CHROMIUM_PATH") or None)
        context = browser.new_context(viewport={'width': 1280, 'height': 900}, locale='en-US')
        page = context.new_page()
        page.on('pageerror', lambda exc: errors.append(str(exc)))
        try:
            # Read-only availability checks hit the real server. Intercept all
            # application mutations and AI requests before interacting with UI.
            page.goto(base_url + '/faculty', wait_until='domcontentloaded', timeout=15000)
            check(page.locator('#saveFacultyButton').count() == 1, 'Faculty dashboard loads')
            check(page.locator('.skip-link').count() == 1, 'Faculty skip-navigation link exists')
            check(page.locator('label[for="facultyName"]').count() == 1, 'Faculty name has a label')

            captured = {'faculty': None, 'generate': None, 'student_save': None, 'student_load': None, 'assistant': None, 'adaptive': None}
            slots = [{'lecture': i + 1, 'time': f'{i + 10}:00', 'subject': 'Free', 'faculty_name': '', 'faculty_id': ''} for i in range(6)]
            day_slots = {day: [dict(x) for x in slots] for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']}
            day_slots['Monday'][0].update(subject='CS101', faculty_name='Synthetic Faculty', faculty_id='DEMO-E2E')
            def faculty_route(route):
                captured['faculty'] = {'headers': route.request.headers, 'json': route.request.post_data_json}
                route.fulfill(status=200, content_type='application/json', body=json.dumps({'message': 'Faculty information saved successfully!'}))
            def generate_route(route):
                captured['generate'] = route.request.headers
                route.fulfill(status=200, content_type='application/json', body=json.dumps({'timetable': day_slots, 'message': 'Timetable generated successfully!'}))
            def subjects_route(route):
                route.fulfill(status=200, content_type='application/json', body=json.dumps({'subjects': [{'code': 'CS101', 'name': 'Synthetic Subject'}]}))
            page.route('**/api/subjects?*', subjects_route)
            page.route('**/api/save-faculty', faculty_route)
            page.route('**/api/generate-timetable?*', generate_route)

            page.locator('#facultyAccessToken').fill('demo-browser-token-not-real')
            page.locator('#facultyName').fill('Synthetic Faculty')
            page.locator('#facultyId').fill('DEMO-E2E')
            page.locator('#departmentSelect').select_option('CSE')
            page.locator('#semesterSelect').select_option('1')
            page.locator('#subjectSelect option[value="CS101"]').wait_for()
            page.locator('#subjectSelect').select_option('CS101')
            page.locator('#weeklyLectures').fill('1')
            page.locator('#saveFacultyButton').click()
            page.locator('#facultyStatus').get_by_text('saved successfully', exact=False).wait_for()
            check(captured['faculty'] is not None and captured['faculty']['json']['faculty_id'] == 'DEMO-E2E', 'Faculty form sends expected record')
            check(captured['faculty']['headers'].get('x-faculty-token') == 'demo-browser-token-not-real', 'Faculty request includes access token')

            page.locator('#generateTimetableButton').click()
            page.locator('#timetableResult table').wait_for()
            check('CS101' in page.locator('#timetableResult').inner_text(), 'Timetable renders generated subject')
            check(page.locator('#timetableResult').evaluate('(e) => document.activeElement === e'), 'Timetable takes keyboard focus')
            check(captured['generate'] is not None, 'Timetable generation sends request')
            cell = page.locator('#timetableResult .editable-cell').first
            cell.focus()
            cell.press('Enter')
            check(page.locator('#timetableResult input').count() + page.locator('#timetableResult select').count() > 0, 'Timetable cell is keyboard-editable')

            page.goto(base_url + '/student', wait_until='domcontentloaded', timeout=15000)
            check(page.locator('#saveStudentDataButton').count() == 1, 'Student dashboard loads')
            check(page.locator('label[for="studentName"]').count() == 1, 'Student name has an accessible label')

            def save_route(route):
                captured['student_save'] = route.request.post_data_json
                route.fulfill(status=200, content_type='application/json', body=json.dumps({'success': True, 'message': 'Student data saved successfully!', 'profileToken': 'synthetic-browser-only-key'}))
            def load_route(route):
                captured['student_load'] = route.request.headers
                route.fulfill(status=200, content_type='application/json', body=json.dumps({'success': True, 'data': {'studentName': 'Synthetic Browser Student', 'branch': 'CSE', 'semester': '1st', 'studyHours': '2', 'examDate': (date.today() + timedelta(days=15)).isoformat(), 'subjects': ['Mathematics'], 'studyTopics': []}}))
            def ai_route(route):
                captured['assistant'] = route.request.post_data_json
                route.fulfill(status=200, content_type='application/json', body=json.dumps({'reply': 'Synthetic AI response: review Mathematics for thirty minutes.'}))
            def adaptive_route(route):
                captured['adaptive'] = route.request.post_data_json
                route.fulfill(status=503, content_type='application/json', body=json.dumps({'error': 'Synthetic AI service unavailable'}))
            page.route('**/api/save-student-data', save_route)
            page.route('**/api/get-student-data', load_route)
            page.route('**/api/ai/study-assistant', ai_route)
            page.route('**/api/ai/adaptive-plan', adaptive_route)

            page.locator('#studentName').fill('Synthetic Browser Student')
            page.locator('#studentBranch').select_option('CSE')
            page.locator('#studentSemester').select_option('1st')
            page.locator('#subjectInput').fill('Mathematics')
            page.locator('#addSubjectButton').click()
            check('Mathematics' in page.locator('#subjectList').inner_text(), 'Student subject added')
            page.locator('#studyHours').select_option('2')
            page.locator('#examDate').fill((date.today() + timedelta(days=15)).isoformat())
            page.locator('#saveStudentDataButton').click()
            page.locator('#saveStatus').get_by_text('saved successfully', exact=False).wait_for()
            check(captured['student_save'] is not None and 'Mathematics' in captured['student_save']['subjects'], 'Student save sends profile with subjects')
            check(page.evaluate('localStorage.getItem("timewise-profile:synthetic browser student")') == 'synthetic-browser-only-key', 'Student token is saved for subsequent load')
            page.locator('#loadStudentDataButton').click()
            page.locator('#saveStatus').get_by_text('loaded successfully', exact=False).wait_for()
            check(captured['student_load'] is not None and captured['student_load'].get('x-profile-token') == 'synthetic-browser-only-key', 'Student load sends correct profile token')

            page.locator('#aiChatToggleBtn').click()
            check(page.locator('#aiChatPanel').get_attribute('aria-hidden') == 'false', 'AI chat opens accessibly')
            page.locator('#aiChatInput').fill('How should I revise Mathematics?')
            page.locator('#aiChatSendBtn').click()
            page.get_by_text('Synthetic AI response: review Mathematics for thirty minutes.', exact=False).wait_for()
            check(captured['assistant'] is not None and captured['assistant']['message'] == 'How should I revise Mathematics?', 'AI assistant sends academic question and displays response')
            page.locator('#aiChatInput').press('Escape')
            check(page.locator('#aiChatPanel').get_attribute('aria-hidden') == 'true', 'Escape closes AI chat')
            check(not errors, 'No browser JavaScript errors: ' + '; '.join(errors[:3]))
            print('\nBrowser workflow checks completed successfully. All API writes and AI responses were mocked.')
            return 0
        finally:
            context.close()
            browser.close()


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        print(f'FAIL browser workflow: {exc}', file=sys.stderr)
        sys.exit(1)
