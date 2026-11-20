import logging
import os
import time
from datetime import date, datetime

from flask import Flask, g, jsonify, request
from werkzeug.exceptions import HTTPException

from . import db, ideas_client, occasions

UI_ORIGIN = os.environ.get("UI_ORIGIN", "http://localhost:8080")
GIT_SHA = os.environ.get("GIT_SHA", "local")
MAX_LABEL = 200

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("occasions")

app = Flask(__name__)
db.init_db()


@app.before_request
def identify_user():
    g.started = time.time()
    if request.method == "OPTIONS" or request.path == "/health":
        return None
    user_id = request.headers.get("X-User-Id", "").strip()
    if not user_id or len(user_id) > 64:
        return jsonify(error="X-User-Id header is required (max 64 characters)"), 400
    g.user_id = user_id
    return None


@app.after_request
def cors_and_log(resp):
    if request.headers.get("Origin") == UI_ORIGIN:
        resp.headers["Access-Control-Allow-Origin"] = UI_ORIGIN
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type, X-User-Id"
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        resp.headers["Vary"] = "Origin"
    ms = int((time.time() - g.get("started", time.time())) * 1000)
    log.info("%s %s -> %s (%d ms)", request.method, request.path, resp.status_code, ms)
    return resp


@app.errorhandler(Exception)
def handle_error(exc):
    if isinstance(exc, HTTPException):
        return jsonify(error=exc.description), exc.code
    log.exception("unhandled error")
    return jsonify(error="internal error"), 500


def parse_occasion(body):
    """Return ((label, date, recurs_annually), None) or (None, error message)."""
    if not isinstance(body, dict):
        return None, "A JSON object is required"
    label = body.get("label")
    if not isinstance(label, str) or not label.strip():
        return None, "label is required"
    label = label.strip()
    if len(label) > MAX_LABEL:
        return None, f"label must be at most {MAX_LABEL} characters"
    raw = body.get("date")
    if not isinstance(raw, str) or len(raw) != 10:
        return None, "date is required in the format YYYY-MM-DD"
    try:
        parsed = datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        return None, "date must be a real calendar date in the format YYYY-MM-DD"
    recurs = body.get("recurs_annually", False)
    if not isinstance(recurs, bool):
        return None, "recurs_annually must be true or false"
    return (label, parsed, recurs), None


def as_json(row):
    return {
        "id": row["id"],
        "person_id": row["person_id"],
        "label": row["label"],
        "date": row["occasion_date"].isoformat(),
        "recurs_annually": bool(row["recurs_annually"]),
    }


@app.get("/health")
def health():
    try:
        db.check_db()
    except Exception:
        log.exception("health check failed")
        return jsonify(status="unavailable", service="occasions", version=GIT_SHA), 503
    return jsonify(status="ok", service="occasions", version=GIT_SHA)


@app.post("/people/<int:person_id>/occasions")
def add_occasion(person_id):
    parsed, error = parse_occasion(request.get_json(silent=True))
    if error:
        return jsonify(error=error), 400
    label, occasion_date, recurs = parsed
    try:
        ideas_client.get_person(g.user_id, person_id)
    except ideas_client.PersonNotFound:
        return jsonify(error="person not found"), 404
    except ideas_client.IdeasUnavailable:
        return jsonify(
            error="The Ideas service is unavailable, so the person could not be checked. "
            "Try again shortly."
        ), 503
    new_id = occasions.add_occasion(g.user_id, person_id, label, occasion_date, recurs)
    return jsonify(id=new_id, person_id=person_id, label=label,
                   date=occasion_date.isoformat(), recurs_annually=recurs), 201


@app.get("/people/<int:person_id>/occasions")
def list_occasions(person_id):
    rows = occasions.list_for_person(g.user_id, person_id)
    return jsonify(occasions=[as_json(r) for r in rows])


@app.get("/upcoming")
def upcoming():
    results, degraded = occasions.upcoming(g.user_id, date.today())
    return jsonify(occasions=results, degraded=degraded)
