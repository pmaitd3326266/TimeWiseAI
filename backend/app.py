from flask import Flask, send_from_directory, jsonify, request
import os
import json
import sys
import secrets
import hashlib
import hmac
import logging
from pathlib import Path
from threading import Lock
from time import monotonic
from datetime import date
import math

app = Flask(__name__)

PROJECT_FOLDER = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)


FRONTEND_FOLDER = os.path.join(PROJECT_FOLDER, "frontend")

# Import AKTU subject database
sys.path.insert(0, PROJECT_FOLDER)

from algorithms.subjects_data import BRANCHES, SUBJECTS
from algorithms.timetable_generator import TimetableGenerator

from backend.gemini_service import (
        generate_study_assistant_response,
        generate_adaptive_study_plan,
        GeminiConfigError,
        GeminiAPIError,
    )
MAX_STUDENT_MESSAGE_LENGTH = 2000
app.config["MAX_CONTENT_LENGTH"] = 256 * 1024
app.json.ensure_ascii = False
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
log = logging.getLogger("timewise")
DATA_FOLDER = Path(os.getenv("TIMEWISE_DATA_DIR") or (Path(PROJECT_FOLDER) / "data"))
DATA_FOLDER.mkdir(parents=True, exist_ok=True)
FACULTY_FILE = DATA_FOLDER / "faculty_data.json"
STUDENT_FILE = DATA_FOLDER / "student_data.json"
faculty_lock = Lock()
student_lock = Lock()
rate_lock = Lock()
rate_state = {}


def error(message, status=400):
    return jsonify({"error": message}), status


def json_object():
    payload = request.get_json(silent=True)
    return payload if isinstance(payload, dict) else None


def valid_text(value, max_length=120):
    """Reject empty, oversized, or control-character-containing identifiers."""
    return (isinstance(value, str) and bool(value.strip())
            and len(value.strip()) <= max_length
            and not any(ord(char) < 32 or ord(char) == 127 for char in value))


def strict_integer(value):
    """Parse a whole number without truncating floats or treating bool as 1."""
    if isinstance(value, bool):
        raise ValueError("Boolean values are not valid integers")
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isascii() and value.strip().isdigit():
        return int(value.strip())
    raise ValueError("Expected a whole number")


def valid_profile_fields(data):
    """Validate optional student fields without requiring fields absent in older clients."""
    if "branch" in data and data["branch"] not in BRANCHES:
        return "Please select a valid branch."
    if "semester" in data:
        try:
            semester = int(data["semester"])
        except (TypeError, ValueError, OverflowError):
            return "Semester must be an integer between 1 and 8."
        if isinstance(data["semester"], bool) or not 1 <= semester <= 8:
            return "Semester must be an integer between 1 and 8."
    if "studyHours" in data:
        try:
            hours = float(data["studyHours"])
        except (TypeError, ValueError, OverflowError):
            return "Study hours must be a number between 0.5 and 24."
        if isinstance(data["studyHours"], bool) or not math.isfinite(hours) or not 0.5 <= hours <= 24:
            return "Study hours must be a number between 0.5 and 24."
    if "examDate" in data and data["examDate"]:
        if not isinstance(data["examDate"], str):
            return "Exam date must use YYYY-MM-DD format."
        try:
            date.fromisoformat(data["examDate"])
        except ValueError:
            return "Exam date must use YYYY-MM-DD format."
    if "subjects" in data:
        if not isinstance(data["subjects"], list) or len(data["subjects"]) > 200:
            return "Invalid subjects."
        if any(not valid_text(item, 150) for item in data["subjects"]):
            return "Each subject must be a non-empty string of at most 150 characters."
    if "studyTopics" in data:
        if not isinstance(data["studyTopics"], list) or len(data["studyTopics"]) > 200:
            return "Invalid studyTopics."
        for item in data["studyTopics"]:
            if not isinstance(item, dict) or len(item) > 12:
                return "Invalid study topic entry."
            if any(not isinstance(key, str) or len(key) > 64 for key in item):
                return "Invalid study topic entry."
            if any(isinstance(value, (dict, list)) for value in item.values()):
                return "Nested study topics are not supported."
            if any(isinstance(value, str) and len(value) > 500 for value in item.values()):
                return "Study topic fields must be at most 500 characters."
    return None


def read_json(path, default):
    if not path.exists():
        return default
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path, value):
    # Atomic replacement avoids corrupting the file after partial writes.
    import tempfile
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".timewise-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(value, fh, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def sanitize_topics(value):
    if not isinstance(value, list):
        value = [value] if value else []
    cleaned = []
    for item in value[:50]:
        if isinstance(item, dict):
            cleaned.append({
                "subject": str(item.get("subject") or "")[:100],
                "topic": str(item.get("topic") or "")[:150],
            })
        elif isinstance(item, (str, int, float)):
            cleaned.append(str(item)[:150])
    return cleaned


def token_digest(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def token_matches(token, stored_digest):
    return (isinstance(token, str) and len(token) >= 32
            and isinstance(stored_digest, str) and len(stored_digest) == 64
            and hmac.compare_digest(token_digest(token), stored_digest))


def faculty_authorized():
    configured = os.getenv("FACULTY_ADMIN_TOKEN", "")
    provided = request.headers.get("X-Faculty-Token", "")
    return len(configured) >= 24 and hmac.compare_digest(provided, configured)


def rate_allowed(bucket, limit, window=60):
    # Per-process guard; for multi-instance deployments use Redis/API gateway rate limiting.
    identifier = (bucket, request.remote_addr or "unknown")
    now = monotonic()
    with rate_lock:
        if len(rate_state) > 10000:
            rate_state.clear()
        start, hits = rate_state.get(identifier, (now, 0))
        if now - start >= window:
            start, hits = now, 0
        if hits >= limit:
            return False
        rate_state[identifier] = (start, hits + 1)
        return True


@app.before_request
def request_guard():
    if request.path.startswith("/api/") and request.method in ("POST", "PUT", "PATCH", "DELETE"):
        if not request.is_json:
            return error("Content-Type must be application/json.", 415)
        origin = request.headers.get("Origin")
        if origin:
            from urllib.parse import urlsplit
            origin_url = urlsplit(origin)
            # Render terminates TLS at a proxy; Flask may see an internal http scheme.
            # Compare the canonical host, not the upstream transport scheme.
            if origin_url.scheme not in ("https", "http") or origin_url.netloc != request.host:
                return error("Cross-origin requests are not permitted.", 403)


@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; font-src 'self' data:; connect-src 'self'; "
        "object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'"
    )
    response.headers["Cache-Control"] = "no-store" if request.path.startswith("/api/") else "no-cache"
    return response


@app.errorhandler(413)
def large_request(_):
    return error("Request is too large (maximum 256 KB).", 413)


@app.route("/healthz")
def healthz():
    return jsonify({"status": "ok"})

@app.route("/assets/<path:filename>")
def asset(filename):
    return send_from_directory(os.path.join(FRONTEND_FOLDER, "assets"), filename)


@app.route("/")
def home():
    return send_from_directory(FRONTEND_FOLDER, "index.html")


@app.route("/faculty")
def faculty():
    return send_from_directory(FRONTEND_FOLDER, "faculty.html")


@app.route("/student")
def student():
    return send_from_directory(FRONTEND_FOLDER, "student.html")


# API: Get branch-wise and semester-wise subjects
@app.route("/api/subjects")
def get_subjects():

    branch = request.args.get("branch", "")
    semester = request.args.get("semester", "")

    if branch not in BRANCHES:
        return jsonify({
            "error": "Please select a valid branch."
        }), 400

    try:
        semester_number = int(semester)
    except (ValueError, TypeError):
        return jsonify({
            "error": "Please select a valid semester."
        }), 400

    if not 1 <= semester_number <= 8:
        return error("Please select a valid semester.")

    stream = BRANCHES[branch]

    semester_key = f"semester_{semester_number}"

    subject_data = SUBJECTS.get(stream, {}).get(
        semester_key, []
    )

    subject_list = []

    for item in subject_data:

        if isinstance(item, dict):

            for code, name in item["subjects"]:
                subject_list.append({
                    "code": code,
                    "name": name
                })

        else:
            code, name = item

            subject_list.append({
                "code": code,
                "name": name
            })

    return jsonify({
        "branch": branch,
        "semester": semester_number,
        "subjects": subject_list
    })


# Faculty records are editable only with a server-configured token.
@app.route("/api/save-faculty", methods=["POST"])
def save_faculty():
    if not faculty_authorized():
        return error("Faculty access token required or invalid.", 403)
    data = json_object()
    if data is None:
        return error("Expected a JSON object.")
    faculty_name = data.get("faculty_name")
    faculty_id = data.get("faculty_id")
    branch = data.get("branch")
    subject = data.get("subject")
    if not all((valid_text(faculty_name), valid_text(faculty_id, 64), branch in BRANCHES, valid_text(subject, 60))):
        return error("Please provide valid faculty name, ID, branch and subject.")
    try:
        semester = strict_integer(data.get("semester"))
        weekly_lectures = strict_integer(data.get("weekly_lectures"))
    except (TypeError, ValueError, OverflowError):
        return error("Invalid semester or weekly lecture count.")
    if not (1 <= semester <= 8 and 1 <= weekly_lectures <= 36):
        return error("Semester must be 1–8; weekly lectures must be 1–36.")
    valid_subjects = []
    for item in SUBJECTS.get(BRANCHES[branch], {}).get(f"semester_{semester}", []):
        if isinstance(item, dict):
            valid_subjects.extend(code for code, _ in item.get("subjects", []))
        else:
            valid_subjects.append(item[0])
    if subject not in valid_subjects:
        return error("Invalid subject for selected branch and semester.")
    record = {"faculty_name": faculty_name.strip(), "faculty_id": faculty_id.strip(),
              "branch": branch, "semester": semester, "subject": subject,
              "weekly_lectures": weekly_lectures}
    try:
        with faculty_lock:
            existing = read_json(FACULTY_FILE, [])
            if not isinstance(existing, list):
                raise ValueError("Invalid faculty data format")
            # Each teacher can teach multiple subjects/classes; update only exact assignment.
            if any(not isinstance(item, dict) for item in existing):
                raise ValueError("Invalid faculty record")
            existing = [item for item in existing if not (
                item.get("faculty_id") == faculty_id.strip()
                and item.get("branch") == branch
                and item.get("semester") == semester
                and item.get("subject") == subject
            )]
            existing.append(record)
            write_json(FACULTY_FILE, existing)
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        log.exception("Unable to persist faculty records")
        return error("Unable to save faculty information.", 500)
    return jsonify({"message": "Faculty information saved successfully!"})


# API: Generate weekly timetable. A faculty token is required to access faculty details.
@app.route("/api/generate-timetable", methods=["GET"])
def generate_timetable():
    if not faculty_authorized():
        return error("Faculty access token required or invalid.", 403)
    branch = request.args.get("branch", "")
    if branch not in BRANCHES:
        return error("Please select a valid branch.")
    try:
        semester = int(request.args.get("semester", ""))
    except (ValueError, TypeError):
        return error("Please select a valid semester.")
    if not 1 <= semester <= 8:
        return error("Please select a valid semester.")
    try:
        with faculty_lock:
            faculty_list = read_json(FACULTY_FILE, [])
        if not isinstance(faculty_list, list):
            raise ValueError("Invalid faculty data")
        if any(not isinstance(record, dict) for record in faculty_list):
            raise ValueError("Invalid faculty record")
        selected = [r for r in faculty_list if r.get("branch") == branch and str(r.get("semester")) == str(semester)]
        if not selected:
            return error("No faculty records found for this branch and semester.", 404)
        timetable = TimetableGenerator(selected).generate_timetable()
        return jsonify({"message": "Timetable generated successfully!",
                        "timetable": timetable[f"{branch} - Semester {semester}"]})
    except ValueError as exc:
        return error(str(exc), 422)
    except (OSError, KeyError, TypeError, json.JSONDecodeError):
        log.exception("Timetable generation failed")
        return error("Unable to generate timetable.", 500)


@app.route("/api/save-student-data", methods=["POST"])
def save_student_data():
    data = json_object()
    if data is None or not valid_text(data.get("studentName"), 100):
        return jsonify({"success": False, "message": "A valid student name is required."}), 400
    validation_error = valid_profile_fields(data)
    if validation_error:
        return jsonify({"success": False, "message": validation_error}), 400
    if not rate_allowed("save-profile", 60):
        return error("Too many profile updates. Try again shortly.", 429)
    name = data["studentName"].strip()
    supplied_token = request.headers.get("X-Profile-Token", "")
    try:
        with student_lock:
            db = read_json(STUDENT_FILE, {"students": []})
            if not isinstance(db, dict) or not isinstance(db.get("students"), list):
                raise ValueError("Invalid student database")
            students = db["students"]
            if any(not isinstance(item, dict) or not isinstance(item.get("studentName"), str)
                   for item in students):
                raise ValueError("Invalid student record")
            existing = next((item for item in students if item["studentName"].casefold() == name.casefold()), None)
            new_token = None
            if existing is not None:
                if not token_matches(supplied_token, existing.get("_token_hash", "")):
                    return jsonify({"success": False, "message": "Profile access key required or invalid."}), 403
                students.remove(existing)
                token_hash = existing["_token_hash"]
            else:
                new_token = secrets.token_urlsafe(32)
                token_hash = token_digest(new_token)
            # Preserve prior fields on partial updates; never copy the private token to a response.
            allowed_fields = ("studentName", "branch", "semester", "studyHours", "examDate", "subjects", "studyTopics")
            safe_data = {key: existing[key] for key in allowed_fields if existing is not None and key in existing}
            safe_data.update({key: data[key] for key in allowed_fields if key in data})
            safe_data["studentName"] = name
            safe_data["_token_hash"] = token_hash
            students.append(safe_data)
            write_json(STUDENT_FILE, db)
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        log.exception("Unable to persist student profile")
        return jsonify({"success": False, "message": "Unable to save profile."}), 500
    reply = {"success": True, "message": "Student data saved successfully!"}
    if new_token:
        reply["profileToken"] = new_token
    return jsonify(reply)


@app.route("/api/get-student-data", methods=["POST"])
def get_student_data():
    payload = json_object()
    if payload is None or not valid_text(payload.get("studentName"), 100):
        return jsonify({"success": False, "message": "A valid student name is required."}), 400
    token = request.headers.get("X-Profile-Token", "")
    if not rate_allowed("profile", 30):
        return error("Too many requests. Try again shortly.", 429)
    try:
        with student_lock:
            db = read_json(STUDENT_FILE, {"students": []})
        if not isinstance(db, dict) or not isinstance(db.get("students"), list):
            raise ValueError("Invalid student database")
        if any(not isinstance(item, dict) or not isinstance(item.get("studentName"), str)
               for item in db["students"]):
            raise ValueError("Invalid student record")
        found = next((x for x in db["students"] if x["studentName"].casefold() == payload["studentName"].strip().casefold()), None)
        if found is None:
            return jsonify({"success": False, "message": "Student record not found."}), 404
        if not token_matches(token, found.get("_token_hash", "")):
            return jsonify({"success": False, "message": "Profile access key required or invalid."}), 403
        return jsonify({"success": True, "data": {k: v for k, v in found.items() if k != "_token_hash"}})
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        log.exception("Unable to load student profile")
        return jsonify({"success": False, "message": "Unable to load profile."}), 500


# API: Gemini AI Study Assistant
@app.route("/api/ai/study-assistant", methods=["POST"])
def study_assistant():
    if not rate_allowed("assistant", 12):
        return error("AI request limit reached. Try again in a minute.", 429)
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({
            "error": "Invalid request payload. Expected a JSON object."
        }), 400

    raw_message = data.get("message")
    if not isinstance(raw_message, str) or not raw_message.strip():
        return jsonify({
            "error": "Message is required and cannot be empty."
        }), 400

    message = raw_message.strip()
    if len(message) > MAX_STUDENT_MESSAGE_LENGTH:
        return jsonify({
            "error": f"Message is too long. Maximum allowed length is {MAX_STUDENT_MESSAGE_LENGTH} characters."
        }), 400

    # Extract student academic context safely with bounds
    branch = str(data.get("branch", "") or "").strip()[:100]
    semester = str(data.get("semester", "") or "").strip()[:50]
    subjects = data.get("subjects") or []
    pending_topics = data.get("pendingTopics") or []
    exam_date = str(data.get("examDate", "") or "").strip()[:50]
    available_hours = str(data.get("availableHours", "") or "").strip()[:20]

    # Sanitize lists safely
    if not isinstance(subjects, list):
        subjects = [str(subjects)[:100]] if subjects else []
    else:
        subjects = [str(s)[:100] for s in subjects[:30]]

    pending_topics = sanitize_topics(pending_topics)

    try:
        reply = generate_study_assistant_response(
            message=message,
            branch=branch,
            semester=semester,
            subjects=subjects,
            pending_topics=pending_topics,
            exam_date=exam_date,
            available_hours=available_hours
        )
        return jsonify({
            "reply": reply
        }), 200

    except GeminiConfigError as config_err:
        return jsonify({
            "error": str(config_err)
        }), 503

    except GeminiAPIError as api_err:
        return jsonify({
            "error": str(api_err)
        }), 502

    except Exception:
        return jsonify({
            "error": "An unexpected error occurred while communicating with the AI service. Please try again later."
        }), 500


# API: Gemini AI Adaptive Study Planner
@app.route("/api/ai/adaptive-plan", methods=["POST"])
def adaptive_plan():
    if not rate_allowed("planner", 6):
        return error("AI request limit reached. Try again in a minute.", 429)
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({
            "error": "Invalid request payload. Expected a JSON object."
        }), 400

    exam_date = str(data.get("examDate", "") or "").strip()[:50]
    if not exam_date:
        return jsonify({
            "error": "Upcoming exam date is required to generate a study plan."
        }), 400
    try:
        from datetime import date
        date.fromisoformat(exam_date)
    except (ValueError, TypeError):
        return error("Exam date must use YYYY-MM-DD format.")

    branch = str(data.get("branch", "") or "").strip()[:100]
    semester = str(data.get("semester", "") or "").strip()[:50]
    subjects = data.get("subjects") or []
    pending_topics = data.get("pendingTopics") or []
    completed_topics = data.get("completedTopics") or []
    available_hours = str(data.get("availableHours", "4") or "4").strip()[:20]
    current_date = str(data.get("currentDate", "") or "").strip()[:50]

    # Sanitize lists safely
    if not isinstance(subjects, list):
        subjects = [str(subjects)[:100]] if subjects else []
    else:
        subjects = [str(s)[:100] for s in subjects[:30]]

    pending_topics = sanitize_topics(pending_topics)

    completed_topics = sanitize_topics(completed_topics)

    if not subjects and not pending_topics:
        return jsonify({
            "error": "Please provide at least one subject or pending topic."
        }), 400

    try:
        result = generate_adaptive_study_plan(
            branch=branch,
            semester=semester,
            subjects=subjects,
            pending_topics=pending_topics,
            completed_topics=completed_topics,
            exam_date=exam_date,
            available_hours=available_hours,
            current_date=current_date
        )
        return jsonify(result), 200

    except GeminiConfigError as config_err:
        return jsonify({
            "error": str(config_err)
        }), 503

    except GeminiAPIError as api_err:
        return jsonify({
            "error": str(api_err)
        }), 502

    except Exception:
        return jsonify({
            "error": "An unexpected error occurred while communicating with the AI service. Please try again later."
        }), 500


if __name__ == "__main__":
    app.run(
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "5000")),
        debug=os.environ.get("FLASK_DEBUG", "False").lower() == "true",
    )
