import pathlib

import pymssql
import pytest
from app import db, ideas, people
from app import main as main_module

USER_A = "user-a"
USER_B = "user-b"
H = {"X-User-Id": USER_A}
OTHER = {"X-User-Id": USER_B}
MIGRATION = pathlib.Path(db.MIGRATIONS_DIR) / "002_add_idea_priority.sql"


def undo_priority_column():
    """Put the ideas table back to how migration 001 left it."""
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute(
        """IF COL_LENGTH('ideas', 'priority') IS NOT NULL
           BEGIN
               ALTER TABLE ideas DROP CONSTRAINT CK_ideas_priority;
               ALTER TABLE ideas DROP CONSTRAINT DF_ideas_priority;
               ALTER TABLE ideas DROP COLUMN priority;
           END"""
    )
    conn.commit()
    conn.close()


# ---- the migration keeps existing data -------------------------------------------------


def test_migration_002_keeps_existing_ideas_and_gives_them_priority_2(clean_db):
    person_id = people.add_person(USER_A, "Maya")
    undo_priority_column()  # the table as it was before this migration
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO ideas (person_id, note) VALUES (%s, %s)", (person_id, "old idea"))
    conn.commit()
    cur.execute(MIGRATION.read_text())  # apply migration 002 to a table that holds a row
    conn.commit()
    conn.close()
    rows = ideas.list_ideas(person_id)
    assert [(r["note"], r["priority"]) for r in rows] == [("old idea", 2)]


# ---- storage ---------------------------------------------------------------------------


def test_a_new_idea_has_priority_2_by_default(clean_db):
    person_id = people.add_person(USER_A, "Maya")
    ideas.add_idea(person_id, "", "socks")
    assert ideas.list_ideas(person_id)[0]["priority"] == 2


def test_an_idea_can_be_saved_with_a_priority(clean_db):
    person_id = people.add_person(USER_A, "Maya")
    ideas.add_idea(person_id, "", "watch", priority=3)
    assert ideas.list_ideas(person_id)[0]["priority"] == 3


def test_top_picks_are_listed_first(clean_db):
    person_id = people.add_person(USER_A, "Maya")
    ideas.add_idea(person_id, "", "socks", priority=1)
    ideas.add_idea(person_id, "", "watch", priority=3)
    ideas.add_idea(person_id, "", "book")
    assert [r["note"] for r in ideas.list_ideas(person_id)] == ["watch", "book", "socks"]


def test_the_owner_can_change_the_priority(clean_db):
    person_id = people.add_person(USER_A, "Maya")
    idea_id = ideas.add_idea(person_id, "", "socks")
    assert ideas.set_priority(USER_A, idea_id, 3) is True
    assert ideas.list_ideas(person_id)[0]["priority"] == 3


def test_another_user_cannot_change_the_priority(clean_db):
    person_id = people.add_person(USER_A, "Maya")
    idea_id = ideas.add_idea(person_id, "", "socks")
    assert ideas.set_priority(USER_B, idea_id, 3) is False
    assert ideas.list_ideas(person_id)[0]["priority"] == 2


def test_the_database_rejects_a_priority_outside_1_to_3(clean_db):
    person_id = people.add_person(USER_A, "Maya")
    with pytest.raises(pymssql.IntegrityError):
        ideas.add_idea(person_id, "", "gold watch", priority=4)


# ---- API -------------------------------------------------------------------------------


@pytest.fixture
def client(clean_db):
    return main_module.app.test_client()


def api_person(client, name="Maya"):
    return client.post("/people", json={"name": name}, headers=H).get_json()["id"]


def api_idea(client, person_id, body):
    return client.post(f"/people/{person_id}/ideas", json=body, headers=H)


def api_ideas(client, person_id):
    return client.get(f"/people/{person_id}", headers=H).get_json()["ideas"]


def test_api_returns_the_priority_and_lists_top_picks_first(client):
    person_id = api_person(client)
    api_idea(client, person_id, {"note": "socks"})
    api_idea(client, person_id, {"note": "watch", "priority": 3})
    items = api_ideas(client, person_id)
    assert [(i["note"], i["priority"]) for i in items] == [("watch", 3), ("socks", 2)]


@pytest.mark.parametrize("bad", [0, 4, -1, "high", 2.5, True])
def test_api_rejects_a_bad_priority_and_stores_nothing(client, bad):
    person_id = api_person(client)
    response = api_idea(client, person_id, {"note": "x", "priority": bad})
    assert response.status_code == 400
    assert api_ideas(client, person_id) == []


def test_api_priority_can_be_changed(client):
    person_id = api_person(client)
    idea_id = api_idea(client, person_id, {"note": "socks"}).get_json()["id"]
    response = client.patch(f"/ideas/{idea_id}", json={"priority": 3}, headers=H)
    assert response.status_code == 200
    assert api_ideas(client, person_id)[0]["priority"] == 3


def test_api_another_user_cannot_change_the_priority(client):
    person_id = api_person(client)
    idea_id = api_idea(client, person_id, {"note": "socks"}).get_json()["id"]
    response = client.patch(f"/ideas/{idea_id}", json={"priority": 3}, headers=OTHER)
    assert response.status_code == 404
    assert api_ideas(client, person_id)[0]["priority"] == 2


def test_api_patch_rejects_a_bad_priority(client):
    person_id = api_person(client)
    idea_id = api_idea(client, person_id, {"note": "socks"}).get_json()["id"]
    response = client.patch(f"/ideas/{idea_id}", json={"priority": 9}, headers=H)
    assert response.status_code == 400
    assert api_ideas(client, person_id)[0]["priority"] == 2


def test_api_cors_preflight_allows_patch(client):
    response = client.options("/ideas/1", headers={"Origin": "http://localhost:8080"})
    assert response.status_code == 204
    assert "PATCH" in response.headers.get("Access-Control-Allow-Methods", "")
