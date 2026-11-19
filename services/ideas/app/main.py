import os
import time

from flask import Flask, g, jsonify, request
from werkzeug.exceptions import HTTPException

from . import ideas, people, tagger
from .db import init_db

UI_ORIGIN = os.environ.get("UI_ORIGIN", "http://localhost:8080")

app = Flask(__name__)
init_db()


def json_body():
    body = request.get_json(silent=True)
    return body if isinstance(body, dict) else {}


def iso(value):
    return value.isoformat() if value is not None else None


@app.before_request
def start_timer_and_identify():
    g.start = time.monotonic()
    if request.method == "OPTIONS":
        return "", 204
    user_id = request.headers.get("X-User-Id", "").strip()
    if not user_id or len(user_id) > 64:
        return jsonify(error="X-User-Id header is required (max 64 characters)"), 400
    g.user_id = user_id


@app.after_request
def add_cors_and_log(response):
    origin = request.headers.get("Origin")
    if origin and origin == UI_ORIGIN:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-User-Id"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Vary"] = "Origin"
    ms = (time.monotonic() - g.get("start", time.monotonic())) * 1000
    print(f"{request.method} {request.path} {response.status_code} {ms:.0f}ms", flush=True)
    return response


@app.errorhandler(Exception)
def handle_error(exc):
    if isinstance(exc, HTTPException):
        return jsonify(error=exc.description), exc.code
    print(f"unhandled {type(exc).__name__}: {exc}", flush=True)
    return jsonify(error="internal error"), 500


@app.route("/people", methods=["GET"])
def list_people():
    rows = people.list_people(g.user_id)
    return jsonify([
        {"id": r["id"], "name": r["name"], "idea_count": ideas.count_ideas_for(r["id"])}
        for r in rows
    ])


@app.route("/people", methods=["POST"])
def create_person():
    name = str(json_body().get("name") or "").strip()
    if not name or len(name) > 200:
        return jsonify(error="name is required (max 200 characters)"), 400
    person_id = people.add_person(g.user_id, name)
    return jsonify(id=person_id, name=name), 201


@app.route("/people/<int:person_id>", methods=["GET"])
def get_person(person_id):
    person = ideas.get_person(g.user_id, person_id)
    if person is None:
        return jsonify(error="person not found"), 404
    items = [
        {
            "id": r["id"],
            "url": r["url"],
            "note": r["note"],
            "created_at": iso(r["created_at"]),
            "given_at": iso(r["given_at"]),
            "tags": ideas.tags_for_idea(r["id"]),
        }
        for r in ideas.list_ideas(person_id)
    ]
    return jsonify(id=person["id"], name=person["name"], ideas=items)


@app.route("/people/<int:person_id>/ideas", methods=["POST"])
def create_idea(person_id):
    if ideas.get_person(g.user_id, person_id) is None:
        return jsonify(error="person not found"), 404
    body = json_body()
    url = str(body.get("url") or "")
    note = str(body.get("note") or "")
    if not url.strip() and not note.strip():
        return jsonify(error="Add a link or a note."), 400
    if len(url) > 2000 or len(note) > 2000:
        return jsonify(error="url and note are limited to 2000 characters"), 400
    idea_id = ideas.add_idea(person_id, url, note)
    raw_tags = body.get("tags") or ""
    if isinstance(raw_tags, list):
        raw_tags = ",".join(str(t) for t in raw_tags)
    tag_names = tagger.parse_tags(str(raw_tags))
    if tag_names:
        ideas.set_tags(g.user_id, idea_id, tag_names)
    return jsonify(id=idea_id), 201


@app.route("/tags", methods=["GET"])
def list_tags():
    return jsonify(ideas.all_tags(g.user_id))
