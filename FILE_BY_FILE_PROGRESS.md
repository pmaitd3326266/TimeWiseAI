# TimeWise AI — file-by-file improvement log

## Pass 1: `backend/gemini_service.py`

**Baseline (reported by user):** 26% combined statement/branch coverage.

**Changes to production code**
- Rejects non-string Gemini response text with a controlled `GeminiAPIError`, instead of calling `.strip()` on arbitrary objects.
- Normalizes missing/null topic `subject` and `topic` fields without raising an unexpected attribute error.
- Handles `nan` and infinite daily study hours as invalid and uses the existing four-hour fallback.
- Gracefully ignores malformed session and notes collections in adaptive plans.

**New regression tests:** `tests/test_gemini_service.py` (49 parametrized cases collected in isolated run).
- No real API calls or API keys.
- Fake Gemini client exercises generated responses, failed connections, provider errors, invalid JSON, academic context, and planner input normalization.

**Verified here:** `49 passed`, `93%` combined coverage for `backend/gemini_service.py` using a temporary stand-in for the unavailable Gemini SDK; Python 3.13.5.

**Still to verify on your machine:** complete suite using the official `google-genai`, Flask, and other installed dependencies; live Gemini request behavior; overall coverage. Use the commands below.

```powershell
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -v
python -m pytest --cov=backend --cov=algorithms --cov-branch --cov-report=term-missing
```

**Next recommended module:** `backend/app.py`, currently 79% coverage in the supplied report. Avoid changing unrelated modules until the complete suite passes.

**Note:** Coverage does not establish that generated plans always follow academic constraints. Further validation of model-generated dates/topics and real Gemini behavior is needed before claiming production readiness.

## Pass 2: `backend/app.py`

**Baseline (user's verified report):** 79% combined statement/branch coverage for `backend/app.py`; 125 tests passed and 86% combined project coverage after Pass 1.

**Production changes:**
- Validates optional student branch, semester, study hours, exam date, subject list, and topic structures (including non-finite numbers and nested payloads) before persisting.
- Rejects control characters in names and identifiers.
- Preserves existing profile fields during partial authenticated updates instead of silently discarding fields not included in the request.
- Rejects malformed stored student/faculty records with controlled API errors instead of allowing unexpected attribute errors.
- Safely rejects malformed/legacy stored token hashes.
- Adds basic per-process throttling to profile writes; the existing rate-limit caveat for multi-worker deployments remains.

**Tests:** `tests/test_app_hardening.py` adds parametrized input-validation and regression cases for partial updates, malformed storage, missing tokens, failed persistence, provider exceptions, invalid origins, and request limits. All records are synthetic and API requests are local to Flask's test client.

**Verified in build environment:** Python syntax/compilation, 32 existing timetable/accessibility tests, and isolated validation smoke checks. **Not yet verified:** complete Flask API suite and revised coverage because Flask is unavailable in this offline container. Run locally:

```powershell
python -m pytest --cov=backend --cov=algorithms --cov-branch --cov-report=term-missing
```

Please compare the resulting coverage against **79% app.py / 86% overall** before claiming an improvement; investigate any failing tests rather than forcing pass results.


## Pass 3: `algorithms/timetable_generator.py`

**Baseline (user verified):** 98% coverage for the previous greedy generator; 158 project tests passed and 89% combined coverage before this pass.

**Production changes:** Replaced greedy lecture-by-lecture placement with a deterministic bipartite multigraph matching algorithm. This guarantees a conflict-free timetable for every feasible request under the existing class/faculty weekly-slot constraints (without room, availability or labs). Maintains the existing timetable dictionary and six daily period labels; validates noninteger lecture counts more strictly.

**New tests:** `tests/test_timetable_advanced.py` adds seeded feasible random schedules, saturation/teacher-clash checks, custom days, malformed input checks, deterministic ordering and a regression that the earlier greedy generator incorrectly rejected. `TIMETABLE_ALGORITHM.md` explains the model, guarantees and exclusions. `PERFORMANCE.md` documents scaling considerations.

**Verified here:** 82 generator tests passed with 97% combined statement/branch coverage for the **new**, longer generator. This slightly lower percentage than the old 98% is due to changed executable branches; functionality and proof-backed feasibility have improved. Full Flask/Gemini tests could not be run here because Flask and google-genai are not installed. The user's Windows environment must run the complete suite and report its overall coverage before comparison.

## File 4 — Frontend HTML/CSS/JS

- Updated `frontend/faculty.html`, `frontend/student.html`, `frontend/assets/faculty.js`, `frontend/assets/student.js`, and dashboard stylesheets.
- Repaired a malformed faculty-page button fragment, added accessible feedback elements, improved timetable edit keyboard behavior and chat focus behavior, and added narrow-screen table scrolling.
- Added 12 frontend regression checks in `tests/test_frontend_improvements.py`.
- Verification in authoring environment: 102 timetable/accessibility/frontend tests passed, JS syntax checks passed, Python compiled, and three HTML templates parsed. Full Flask tests and browser-based audits remain for the user's environment.
