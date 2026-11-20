import time

from app import ideas, people

USER_A = "user-a"
USER_B = "user-b"


def test_person_is_visible_to_its_owner(clean_db):
    person_id = people.add_person(USER_A, "Maya")
    assert ideas.get_person(USER_A, person_id)["name"] == "Maya"


def test_person_is_not_visible_to_another_user(clean_db):
    person_id = people.add_person(USER_A, "Maya")
    assert ideas.get_person(USER_B, person_id) is None


def test_add_person_trims_the_name(clean_db):
    person_id = people.add_person(USER_A, "  Maya  ")
    assert ideas.get_person(USER_A, person_id)["name"] == "Maya"


def test_people_list_returns_only_your_own_sorted_by_name(clean_db):
    people.add_person(USER_A, "Zoe")
    people.add_person(USER_A, "Maya")
    people.add_person(USER_B, "Sam")
    assert [p["name"] for p in people.list_people(USER_A)] == ["Maya", "Zoe"]


def test_add_idea_keeps_url_and_note_and_blank_becomes_null(clean_db):
    pid = people.add_person(USER_A, "Maya")
    ideas.add_idea(pid, "https://example.com", "")
    ideas.add_idea(pid, "", "a note")
    rows = {(r["url"], r["note"]) for r in ideas.list_ideas(pid)}
    assert rows == {("https://example.com", None), (None, "a note")}


def test_list_ideas_returns_newest_first(clean_db):
    pid = people.add_person(USER_A, "Maya")
    first = ideas.add_idea(pid, "", "first")
    time.sleep(0.05)
    second = ideas.add_idea(pid, "", "second")
    assert [r["id"] for r in ideas.list_ideas(pid)] == [second, first]


def test_list_ideas_only_returns_that_persons_ideas(clean_db):
    maya = people.add_person(USER_A, "Maya")
    sam = people.add_person(USER_A, "Sam")
    ideas.add_idea(maya, "", "for maya")
    ideas.add_idea(sam, "", "for sam")
    assert [r["note"] for r in ideas.list_ideas(maya)] == ["for maya"]


def test_count_ideas_counts_only_that_person(clean_db):
    maya = people.add_person(USER_A, "Maya")
    sam = people.add_person(USER_A, "Sam")
    ideas.add_idea(maya, "", "one")
    ideas.add_idea(maya, "", "two")
    assert ideas.count_ideas_for(maya) == 2
    assert ideas.count_ideas_for(sam) == 0


def test_set_tags_links_the_tags_to_the_idea(clean_db):
    pid = people.add_person(USER_A, "Maya")
    idea_id = ideas.add_idea(pid, "", "a note")
    ideas.set_tags(USER_A, idea_id, ["winter", "shoes"])
    assert ideas.tags_for_idea(idea_id) == ["shoes", "winter"]


def test_set_tags_does_not_duplicate_on_repeat(clean_db):
    pid = people.add_person(USER_A, "Maya")
    idea_id = ideas.add_idea(pid, "", "a note")
    ideas.set_tags(USER_A, idea_id, ["shoes", "shoes"])
    ideas.set_tags(USER_A, idea_id, ["shoes"])
    assert ideas.tags_for_idea(idea_id) == ["shoes"]
    assert ideas.all_tags(USER_A) == ["shoes"]


def test_tags_are_separate_for_each_user(clean_db):
    idea_a = ideas.add_idea(people.add_person(USER_A, "Maya"), "", "a")
    idea_b = ideas.add_idea(people.add_person(USER_B, "Sam"), "", "b")
    ideas.set_tags(USER_A, idea_a, ["shoes"])
    ideas.set_tags(USER_B, idea_b, ["shoes", "books"])
    assert ideas.all_tags(USER_A) == ["shoes"]
    assert ideas.all_tags(USER_B) == ["books", "shoes"]


def test_set_tags_with_no_names_changes_nothing(clean_db):
    idea_id = ideas.add_idea(people.add_person(USER_A, "Maya"), "", "a note")
    ideas.set_tags(USER_A, idea_id, [])
    assert ideas.tags_for_idea(idea_id) == []
    assert ideas.all_tags(USER_A) == []


def test_all_tags_are_sorted(clean_db):
    idea_id = ideas.add_idea(people.add_person(USER_A, "Maya"), "", "a note")
    ideas.set_tags(USER_A, idea_id, ["b", "a"])
    assert ideas.all_tags(USER_A) == ["a", "b"]
