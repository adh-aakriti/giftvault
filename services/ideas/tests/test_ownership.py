import tempfile
from datetime import date

import pytest


@pytest.fixture
def temp_db(monkeypatch):
    tmpdir = tempfile.mkdtemp()
    monkeypatch.setenv("DATA_DIR", tmpdir)

    import importlib
    import db
    importlib.reload(db)
    import people
    importlib.reload(people)
    import ideas
    importlib.reload(ideas)
    import occasions
    importlib.reload(occasions)

    db.init_db()
    yield people, ideas, occasions


def test_person_is_visible_to_its_owner(temp_db):
    people, ideas, occasions = temp_db
    person_id = people.add_person("user-a", "Maya")
    assert ideas.get_person("user-a", person_id)["name"] == "Maya"


def test_person_is_not_visible_to_another_user(temp_db):
    people, ideas, occasions = temp_db
    person_id = people.add_person("user-a", "Maya")
    assert ideas.get_person("user-b", person_id) is None


def test_people_list_only_returns_your_own(temp_db):
    people, ideas, occasions = temp_db
    people.add_person("user-a", "Maya")
    people.add_person("user-b", "Sam")
    names = [row["name"] for row in people.list_people("user-a")]
    assert names == ["Maya"]


def test_upcoming_sorts_by_days_remaining(temp_db):
    people, ideas, occasions = temp_db
    a = people.add_person("user-a", "Maya")
    b = people.add_person("user-a", "Sam")
    occasions.add_occasion(a, "Birthday", "1999-12-01", True)
    occasions.add_occasion(b, "Birthday", "1999-10-20", True)

    result = occasions.upcoming("user-a", date(2026, 10, 8))
    assert [r["person_name"] for r in result] == ["Sam", "Maya"]


def test_upcoming_excludes_other_users(temp_db):
    people, ideas, occasions = temp_db
    mine = people.add_person("user-a", "Maya")
    theirs = people.add_person("user-b", "Sam")
    occasions.add_occasion(mine, "Birthday", "1999-12-01", True)
    occasions.add_occasion(theirs, "Birthday", "1999-11-01", True)

    result = occasions.upcoming("user-a", date(2026, 10, 8))
    assert len(result) == 1
    assert result[0]["person_name"] == "Maya"


def test_upcoming_includes_idea_count_from_ideas_domain(temp_db):
    people, ideas, occasions = temp_db
    person_id = people.add_person("user-a", "Maya")
    occasions.add_occasion(person_id, "Birthday", "1999-12-01", True)
    ideas.add_idea(person_id, "", "a note")
    ideas.add_idea(person_id, "https://example.com", "")

    result = occasions.upcoming("user-a", date(2026, 10, 8))
    assert result[0]["idea_count"] == 2


def test_upcoming_drops_passed_non_recurring_occasions(temp_db):
    people, ideas, occasions = temp_db
    person_id = people.add_person("user-a", "Maya")
    occasions.add_occasion(person_id, "Wedding", "2026-03-01", False)

    assert occasions.upcoming("user-a", date(2026, 10, 8)) == []

def test_list_for_person_returns_that_persons_occasions(temp_db):
    people, ideas, occasions = temp_db
    person_id = people.add_person("user-a", "Maya")
    occasions.add_occasion(person_id, "Birthday", "1999-12-01", True)
    occasions.add_occasion(person_id, "Graduation", "2027-06-15", False)

    rows = occasions.list_for_person(person_id)
    assert [r["label"] for r in rows] == ["Birthday", "Graduation"]