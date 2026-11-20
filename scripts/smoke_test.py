"""Non-destructive HTTP smoke test for local/Render TimeWise AI deployments.

Usage:
    python scripts/smoke_test.py http://127.0.0.1:5000
    python scripts/smoke_test.py https://your-service.onrender.com

Only GET requests. Never writes profiles, generates timetable, or contacts Gemini.
"""
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def check(base_url, path, expected_status, expected_type=None):
    req = Request(base_url.rstrip('/') + path,
                  headers={'User-Agent': 'TimeWise-Deployment-SmokeTest/1.0'})
    try:
        with urlopen(req, timeout=20) as response:
            status = response.status
            body = response.read(32768)
            kind = response.headers.get('Content-Type', '')
            headers = response.headers
    except HTTPError as exc:
        status = exc.code
        body = exc.read(32768)
        kind = exc.headers.get('Content-Type', '')
        headers = exc.headers
    except (URLError, TimeoutError, OSError) as exc:
        print(f'FAIL {path}: connection failure ({exc})')
        return False
    good = status == expected_status and (not expected_type or expected_type in kind)
    if 'X-Content-Type-Options' not in headers:
        good = False
    if path == '/healthz' and status == 200:
        try:
            good = good and json.loads(body)['status'] == 'ok'
        except (ValueError, KeyError, TypeError):
            good = False
    print(f'{"PASS" if good else "FAIL"} {path}: HTTP {status}, Content-Type {kind}')
    return good


def main():
    if len(sys.argv) != 2 or not sys.argv[1].startswith(('http://', 'https://')):
        print('Usage: python scripts/smoke_test.py http://127.0.0.1:5000')
        return 2
    base = sys.argv[1]
    checks = [
        ('/healthz', 200, 'application/json'),
        ('/', 200, 'text/html'),
        ('/faculty', 200, 'text/html'),
        ('/student', 200, 'text/html'),
        ('/assets/faculty.js', 200, 'javascript'),
        ('/assets/student.js', 200, 'javascript'),
        ('/api/generate-timetable?branch=CSE&semester=1', 403, 'application/json'),
    ]
    results = [check(base, path, status, kind) for path, status, kind in checks]
    print(f'\n{sum(results)}/{len(results)} non-destructive smoke checks passed')
    return 0 if all(results) else 1


if __name__ == '__main__':
    sys.exit(main())
