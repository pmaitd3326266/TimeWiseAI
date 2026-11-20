# TimeWise AI — release-wide audit

This audit uses the File 4 frontend ZIP as baseline (the user verified **228 passing tests, 89% combined coverage** on Python 3.15). The release changes add integration tests, smoke checks, strict integer validation, CI branch coverage and updated documentation. **The revised full suite must be run in an environment with Flask and Google GenAI installed**; its pass count and coverage must not be assumed from the baseline.

## Findings and disposition

| Area | Finding | Action / status |
|---|---|---|
| Student profiles | Name alone is insufficient to load a profile, but access relies on a browser-held capability token | Covered by cross-module integration tests. **Not equivalent to institutional account authentication.** |
| Faculty API | Shared bearer token is required to save records or generate a timetable | Added end-to-end protected save/generate test. For real multi-user use replace with role-based login. |
| Faculty validation | Previously `int(2.7)` or `int(True)` silently converted to 2 or 1 | Fixed with a strict parser and regression cases. |
| Timetable generator | README still described older greedy algorithm | Corrected to matching-based algorithm and its documented constraints. |
| Deployment | No safe, automated live smoke check | Added `scripts/smoke_test.py` for read-only checks and access-control status. |
| CI | Did not collect branch coverage | GitHub Actions command now measures branch coverage. |
| Privacy | Static distribution must not contain raw student records, API keys, or virtual environments | Added hygiene tests and ensured generated ZIP excludes them. |
| Error handling | Tests for provider failures and malformed requests are present | Still require end-to-end live Gemini verification with a test account and limited quota. |
| Accessibility | Static accessibility tests and keyboard improvements exist | **Manual** keyboard, screen-reader, responsive zoom, and Lighthouse audit outstanding. |
| Storage | On-disk JSON files are not durable on default Render | Production blocker for real records. Use managed database/storage with backup and access policy. |

## Local release validation

1. Install with `python -m pip install -r requirements-dev.txt` (Python 3.11/3.12 recommended).
2. Run `python -m pytest --cov=backend --cov=algorithms --cov-branch --cov-report=term-missing`.
3. In a terminal run `python backend/app.py`; in a second run `python scripts/smoke_test.py http://127.0.0.1:5000`.
4. Manually verify faculty save -> generate timetable, student save -> load, AI assistant (only with a test Gemini key and suitable quota), mobile layout, keyboard navigation and status announcements.
5. Configure `GEMINI_API_KEY`, a unique high-entropy `FACULTY_ADMIN_TOKEN`, `FLASK_DEBUG=False`, and appropriate persistent storage before accepting real user records.
6. Deploy to Render with `render.yaml` or the documented Gunicorn command. Repeat the smoke script against the HTTPS service URL.

## What can and cannot be claimed

**Verified in this build environment:** Python compilation, both frontend JS syntax checks, 107 scheduler/accessibility/release-static tests. No Gemini calls were made. The complete Flask + Gemini regression suite cannot run here because Flask is not installed. **Previously user verified** 228 tests passing at 89% coverage on File 4, *before these final changes.*

**Not verified:** full new Flask suite, real Gemini requests, browser and screen-reader accessibility, sustained load, multi-process persistence, automated external scoring, and 95+/100 benchmark. Do not claim those as passed until tested on their target environments.

## Production limitations

This remains a demonstration architecture, not an institution-ready multi-tenant service: JSON file storage and in-process locks/rate limits, shared faculty bearer token, localStorage student capability tokens, no faculty identity audit trail, limited timetable constraints and potentially metered AI endpoints. Use synthetic data for a public demo. Do not enter real student data without a privacy/security review and durable storage.
