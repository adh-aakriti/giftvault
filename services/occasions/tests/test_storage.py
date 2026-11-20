from datetime import date

from app import occasions

TODAY = date(2026, 10, 8)
USER_A = "user-a"
USER_B = "user-b"


def test_added_occasion_is_listed_for_its_owner(clean_db):
    new_id = occasions.add_occasion(USER_A, 1, "  Birthday ", date(1999, 12, 1), True)
    rows = occasions.list_for_person(USER_A, 1)
    assert len(rows) == 1
    assert rows[0]["id"] == new_id
    assert rows[0]["label"] == "Birthday"
    assert rows[0]["occasion_date"] == date(1999, 12, 1)
    assert rows[0]["recurs_annually"]


def test_list_hides_other_users_and_other_people(clean_db):
    occasions.add_occasion(USER_A, 1, "mine", date(2027, 1, 1), False)
    occasions.add_occasion(USER_B, 1, "theirs", date(2027, 1, 1), False)
    occasions.add_occasion(USER_A, 2, "other person", date(2027, 1, 1), False)
    assert [r["label"] for r in occasions.list_for_person(USER_A, 1)] == ["mine"]


def test_list_is_ordered_by_date(clean_db):
    occasions.add_occasion(USER_A, 1, "later", date(2027, 6, 1), False)
    occasions.add_occasion(USER_A, 1, "sooner", date(2027, 2, 1), False)
    assert [r["label"] for r in occasions.list_for_person(USER_A, 1)] == ["sooner", "later"]


def test_upcoming_sorts_by_days_remaining(clean_db, ideas_stub):
    ideas_stub["people"] = {1: {"name": "Maya", "ideas": []}, 2: {"name": "Sam", "ideas": []}}
    occasions.add_occasion(USER_A, 1, "Birthday", date(1999, 12, 1), True)
    occasions.add_occasion(USER_A, 2, "Birthday", date(1999, 10, 20), True)
    results, degraded = occasions.upcoming(USER_A, TODAY)
    assert [r["person_name"] for r in results] == ["Sam", "Maya"]
    assert degraded is False


def test_upcoming_excludes_other_users(clean_db, ideas_stub):
    occasions.add_occasion(USER_A, 1, "Birthday", date(1999, 12, 1), True)
    occasions.add_occasion(USER_B, 2, "Birthday", date(1999, 11, 1), True)
    results, _ = occasions.upcoming(USER_A, TODAY)
    assert [r["person_id"] for r in results] == [1]
    assert ideas_stub["calls"] == 1


def test_upcoming_includes_idea_count_from_ideas(clean_db, ideas_stub):
    ideas_stub["people"] = {1: {"name": "Maya", "ideas": [{"id": 1}, {"id": 2}]}}
    occasions.add_occasion(USER_A, 1, "Birthday", date(1999, 12, 1), True)
    results, _ = occasions.upcoming(USER_A, TODAY)
    assert results[0]["idea_count"] == 2


def test_upcoming_drops_passed_non_recurring_occasions(clean_db, ideas_stub):
    occasions.add_occasion(USER_A, 1, "Wedding", date(2026, 3, 1), False)
    results, _ = occasions.upcoming(USER_A, TODAY)
    assert results == []


def test_upcoming_asks_ideas_once_per_person(clean_db, ideas_stub):
    occasions.add_occasion(USER_A, 1, "Birthday", date(1999, 12, 1), True)
    occasions.add_occasion(USER_A, 1, "Graduation", date(2027, 6, 15), False)
    results, _ = occasions.upcoming(USER_A, TODAY)
    assert len(results) == 2
    assert ideas_stub["calls"] == 1


def test_upcoming_still_returns_occasions_when_ideas_is_down(clean_db, ideas_stub):
    ideas_stub["mode"] = "down"
    occasions.add_occasion(USER_A, 1, "Birthday", date(1999, 12, 1), True)
    occasions.add_occasion(USER_A, 2, "Birthday", date(1999, 10, 20), True)
    results, degraded = occasions.upcoming(USER_A, TODAY)
    assert degraded is True
    assert len(results) == 2
    assert all(r["person_name"] is None and r["idea_count"] is None for r in results)
    assert ideas_stub["calls"] == 1


def test_upcoming_handles_a_person_missing_in_ideas(clean_db, ideas_stub):
    ideas_stub["mode"] = "missing"
    occasions.add_occasion(USER_A, 1, "Birthday", date(1999, 12, 1), True)
    results, degraded = occasions.upcoming(USER_A, TODAY)
    assert degraded is False
    assert results[0]["person_name"] is None