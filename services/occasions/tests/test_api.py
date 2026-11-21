from datetime import date, timedelta

import pytest

H = {"X-User-Id": "user-a"}


@pytest.fixture
def client(clean_db, ideas_stub):
    from app.main import app

    return app.test_client()


def post(client, body, person_id=1, headers=H):
    return client.post(f"/people/{person_id}/occasions", json=body, headers=headers)


def stored(client, person_id=1):
    return client.get(f"/people/{person_id}/occasions", headers=H).get_json()["occasions"]


def test_health_is_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_missing_user_header_is_rejected(client):
    assert client.get("/upcoming").status_code == 400


@pytest.mark.parametrize("body", [
    {"label": "Birthday", "date": "notadate"},
    {"label": "Birthday", "date": "2026-02-30"},
    {"label": "Birthday", "date": "2026-2-3"},
    {"label": "Birthday"},
    {"label": "  ", "date": "2026-12-01"},
    {"date": "2026-12-01"},
    {"label": "x" * 201, "date": "2026-12-01"},
    {"label": "Birthday", "date": "2026-12-01", "recurs_annually": "yes"},
])
def test_invalid_input_is_rejected_and_nothing_is_stored(client, body):
    response = post(client, body)
    assert response.status_code == 400
    assert "error" in response.get_json()
    assert stored(client) == []


def test_a_body_that_is_not_json_is_rejected(client):
    response = client.post("/people/1/occasions", data="hello", headers=H)
    assert response.status_code == 400


def test_valid_occasion_is_created_and_listed(client):
    response = post(client, {"label": "Birthday", "date": "1999-12-01", "recurs_annually": True})
    assert response.status_code == 201
    assert response.get_json()["date"] == "1999-12-01"
    listed = stored(client)
    assert [o["label"] for o in listed] == ["Birthday"]
    assert listed[0]["recurs_annually"] is True


def test_unknown_person_gives_404_and_stores_nothing(client, ideas_stub):
    ideas_stub["mode"] = "missing"
    assert post(client, {"label": "Birthday", "date": "1999-12-01"}).status_code == 404
    assert stored(client) == []


def test_create_gives_503_when_ideas_is_down(client, ideas_stub):
    ideas_stub["mode"] = "down"
    assert post(client, {"label": "Birthday", "date": "1999-12-01"}).status_code == 503
    assert stored(client) == []


def test_upcoming_has_names_and_idea_counts_when_ideas_is_up(client, ideas_stub):
    ideas_stub["people"] = {1: {"name": "Maya", "ideas": [{"id": 1}]}}
    soon = (date.today() + timedelta(days=10)).isoformat()
    post(client, {"label": "Birthday", "date": soon})
    body = client.get("/upcoming", headers=H).get_json()
    assert body["degraded"] is False
    assert body["occasions"][0]["person_name"] == "Maya"
    assert body["occasions"][0]["idea_count"] == 1
    assert body["occasions"][0]["days"] == 10


def test_upcoming_still_answers_when_ideas_is_down(client, ideas_stub):
    soon = (date.today() + timedelta(days=10)).isoformat()
    post(client, {"label": "Birthday", "date": soon})
    ideas_stub["mode"] = "down"
    response = client.get("/upcoming", headers=H)
    body = response.get_json()
    assert response.status_code == 200
    assert body["degraded"] is True
    assert len(body["occasions"]) == 1
    assert body["occasions"][0]["person_name"] is None


def test_cors_allows_only_the_ui_origin(client):
    ok = client.options("/upcoming", headers={"Origin": "http://localhost:8080"})
    assert ok.headers.get("Access-Control-Allow-Origin") == "http://localhost:8080"
    other = client.options("/upcoming", headers={"Origin": "https://evil.example"})
    assert other.headers.get("Access-Control-Allow-Origin") is None
