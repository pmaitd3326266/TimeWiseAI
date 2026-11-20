# Browser verification — TimeWise AI

The earlier `scripts/smoke_test.py` verifies that the **real Flask server** responds to seven read-only requests. The next layer is `scripts/browser_workflows.py`, which loads the **real served HTML/CSS/JavaScript** in Chromium and uses synthetic, intercepted API responses to check UI behaviors.

## Run browser tests locally

In one PowerShell terminal from the project root:

```powershell
python backend/app.py
```

In a second terminal:

```powershell
python -m pip install playwright
python -m playwright install chromium
python scripts/browser_workflows.py http://127.0.0.1:5000
```

Add `--headed` to watch the browser. These commands use your installed Python and do not require a virtual environment. Do **not** point the browser test at a production system unless you have permission to test it. The script intercepts faculty/student writes, student loads, timetable generation, and Gemini responses; it never uses real tokens and never modifies stored profiles.

## What the browser check covers

- Faculty form labeling and subject selection
- Faculty save request and access-token header
- Timetable rendering, focus, and keyboard editing
- Student profile save/load using a synthetic access key
- Adding a subject
- Opening and closing AI chat with Escape
- Displaying a mocked AI response and checking browser JavaScript errors

## What is not verified by mocks

These checks do **not** prove the real Flask data store, token validation, or Gemini API are working together. Backend API contracts are exercised separately by `pytest` and the read-only `scripts/smoke_test.py`.

For the **actual Gemini integration**, set `GEMINI_API_KEY` in your local `.env` and manually verify one safe study question in the Student dashboard. A valid key, network connectivity and the provider's availability are required. Verify that failed AI requests show useful error messages, without exposing the key. Avoid including your `.env` or private records in screenshots or ZIPs.

For browser accessibility, also test 200% zoom, mobile width, visible focus, keyboard-only navigation, and a screen reader (NVDA or VoiceOver). Automated checks alone cannot certify WCAG compliance.

## Browser checker troubleshooting

If Chromium is installed outside Playwright's cache, set `TIMEWISE_CHROMIUM_PATH` to its executable location. Otherwise run `python -m playwright install chromium`. Start Flask before the browser check, just as with the smoke test. The browser check currently uses mocked data and does not attempt to reproduce backend storage mutations; the real backend tests remain in pytest.
