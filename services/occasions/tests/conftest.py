import os

import pytest


@pytest.fixture
def clean_db():
    """Empty the occasions table before a test. Needs a running SQL Server."""
    if not os.environ.get("DATABASE_URL"):
        pytest.skip(
            "DATABASE_URL is not set: start SQL Server with docker compose to run database tests"
        )
    from app import db

    db.init_db()
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM occasions")
    conn.commit()
    conn.close()


@pytest.fixture
def ideas_stub(monkeypatch):
    """Stand in for the Ideas service. Set mode to 'ok', 'missing' or 'down'."""
    from app import ideas_client

    state = {"mode": "ok", "calls": 0, "people": {}}

    def fake_get_person(user_id, person_id):
        state["calls"] += 1
        if state["mode"] == "down":
            raise ideas_client.IdeasUnavailable("stub: ideas is down")
        if state["mode"] == "missing":
            raise ideas_client.PersonNotFound(person_id)
        return state["people"].get(person_id, {"name": f"Person {person_id}", "ideas": []})

    monkeypatch.setattr(ideas_client, "get_person", fake_get_person)
    return state
