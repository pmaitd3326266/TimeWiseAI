# TimeWise AI

Academic timetable generation, student study planning, and optional Gemini assistance. This cleaned version focuses on predictable local setup, privacy, access controls, accessibility and automated testing.

## Run locally (no virtual environment required)

Python **3.11 or 3.12** recommended.

```powershell
cd TimeWise-AI
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python backend/app.py
```

Open http://127.0.0.1:5000. The Flask app **does not install packages automatically**; keeping installation in the setup step is more reliable and avoids modifying a live production environment.

Configure `.env` with `GEMINI_API_KEY` to enable Gemini-powered features. The local timetable generator and manual study planner work without a Gemini key. Set `FACULTY_ADMIN_TOKEN` to a random string of 24+ characters to enable faculty save and timetable endpoints. Generate a token with:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Paste the same token into the Faculty dashboard's access-token field when saving faculty assignments or generating the timetable. **Do not commit `.env` or share tokens.**

## Student profile privacy

The first time you save a student profile, the server generates a unique access key and the browser saves it in localStorage for subsequent saves/loads. Other users cannot retrieve a profile merely by guessing a name. This is a lightweight per-profile capability, **not a full account-login system**. If you clear browser storage or switch browsers you may lose access to your profile. For institution-wide use, replace it with real user authentication and a persistent database.

Existing legacy profiles without an access key **cannot be edited** through this interface; migrate them securely instead of automatically granting public access. Do not put real sensitive student data in a public demo.

## Automated checks

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -v
python -m pytest --cov=algorithms --cov=backend --cov-branch --cov-report=term-missing
```

GitHub Actions runs the same tests on pushes and pull requests.

## Release and integration verification

After installing dependencies, run the full test suite and verify the local site without
modifying user data:

```powershell
python -m pytest --cov=backend --cov=algorithms --cov-branch --cov-report=term-missing
python backend/app.py
```

With the site running, open **another** terminal:

```powershell
python scripts/smoke_test.py http://127.0.0.1:5000
```

Once Render is deployed, repeat with its public HTTPS URL. The smoke tester only
requests public pages, static files, health, and an intentionally unauthorized
timetable request. It does not modify any records or call the Gemini API.

See `RELEASE_AUDIT.md` for the final checklist, test scope, and known deployment risks.

## Deployment on Render

A `render.yaml` blueprint is included. Alternatively create a Python web service with:

- Build: `pip install -r requirements.txt`
- Start: `gunicorn backend.app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 90`
- Configure `GEMINI_API_KEY` and `FACULTY_ADMIN_TOKEN` as private Render environment variables. Set `FLASK_DEBUG=False`.

**Data persistence warning:** Default Render storage is ephemeral; JSON profile data will disappear on redeploy/restart. This implementation is suitable for demonstration with synthetic data, **not production student records**. Use a persistent database and proper role-based accounts for real deployment. A single Gunicorn worker avoids JSON write races *within one instance*; multiple instances need a transactional database.

## Security changes

- No embedded `.env`, API keys, personal JSON data, or bundled virtual environment.
- Limits request bodies and user-provided fields; JSON-only API mutations and same-origin checks.
- Faculty write/read endpoints require a secret access token.
- Student read/write operations require their individual access key (hash stored server-side); profile lookup uses POST rather than credentials in URL.
- Basic per-process AI request throttling, restrictive CSP and security headers, atomic writes, and generic server-error responses.
- Public landing page and learning features remain available. AI calls need a Gemini key and may incur usage costs.

## Documentation

See `SECURITY.md`, `PERFORMANCE.md` and `ACCESSIBILITY.md` for the security threat model, benchmark context, and manual audit checklist.

## Accessibility

Form controls now have labels, prominent keyboard focus, a skip link, status announcements and reduced-motion support. Full assistive-technology testing (NVDA, screen magnification, actual Lighthouse) remains necessary.

## Limitations

Timetable scheduling uses deterministic bipartite matching. Given the currently modeled class/teacher capacity constraints, it can schedule all feasible lecture assignments without double-booking. It does **not** model room availability, teacher unavailability, lab blocks, elective clashes, or institutional timetable preferences. A production institution would also need multi-user identity, durable database storage and distributed rate limiting.
