import pytest

from app import main as main_module

H = {"X-User-Id": "user-a"}
OTHER = {"X-User-Id": "user-b"}


@pytest.fixture
def client(clean_db):
    return main_module.app.test_client()


def add_person(client, name="Maya", headers=H):
    response = client.post("/people", json={"name": name}, headers=headers)
    return response.get_json()["id"]


def person(client, person_id, headers=H):
    return client.get(f"/people/{person_id}", headers=headers)


def add_idea(client, person_id, body, headers=H):
    return client.post(f"/people/{person_id}/ideas", json=body, headers=headers)


def test_health_is_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["db"] == "ok"


def test_health_gives_503_when_the_database_fails(client, monkeypatch):
    def broken():
        raise RuntimeError("database is down")

    monkeypatch.setattr(main_module, "check_db", broken)
    response = client.get("/health")
    assert response.status_code == 503
    assert response.get_json()["status"] == "error"


def test_missing_user_header_is_rejected(client):
    assert client.get("/people").status_code == 400


def test_user_header_longer_than_64_characters_is_rejected(client):
    assert client.get("/people", headers={"X-User-Id": "x" * 65}).status_code == 400


def test_created_person_appears_in_the_list_with_an_idea_count(client):
    person_id = add_person(client)
    listed = client.get("/people", headers=H).get_json()
    assert listed == [{"id": person_id, "name": "Maya", "idea_count": 0}]


@pytest.mark.parametrize("body", [{"name": "   "}, {}, {"name": "x" * 201}])
def test_invalid_person_name_is_rejected(client, body):
    assert client.post("/people", json=body, headers=H).status_code == 400
    assert client.get("/people", headers=H).get_json() == []


def test_a_person_body_that_is_not_json_is_rejected(client):
    assert client.post("/people", data="hello", headers=H).status_code == 400


def test_people_list_only_returns_your_own(client):
    add_person(client, "Maya", H)
    add_person(client, "Sam", OTHER)
    names = [p["name"] for p in client.get("/people", headers=H).get_json()]
    assert names == ["Maya"]


def test_get_person_returns_name_and_no_ideas_yet(client):
    person_id = add_person(client)
    body = person(client, person_id).get_json()
    assert body["name"] == "Maya"
    assert body["ideas"] == []


def test_another_users_person_gives_404(client):
    person_id = add_person(client, "Maya", H)
    assert person(client, person_id, OTHER).status_code == 404


def test_unknown_person_gives_404(client):
    assert person(client, 999999).status_code == 404


def test_idea_tags_are_normalised_and_returned(client):
    person_id = add_person(client)
    response = add_idea(client, person_id, {"url": "https://example.com", "note": "boots", "tags": "Shoes, winter, shoes"})
    assert response.status_code == 201
    idea = person(client, person_id).get_json()["ideas"][0]
    assert idea["tags"] == ["shoes", "winter"]
    assert idea["url"] == "https://example.com"
    assert idea["given_at"] is None


def test_idea_tags_can_be_sent_as_a_list(client):
    person_id = add_person(client)
    add_idea(client, person_id, {"note": "a book", "tags": ["Books", "books"]})
    assert person(client, person_id).get_json()["ideas"][0]["tags"] == ["books"]


def test_idea_count_in_the_people_list_goes_up(client):
    person_id = add_person(client)
    add_idea(client, person_id, {"note": "one"})
    add_idea(client, person_id, {"note": "two"})
    assert client.get("/people", headers=H).get_json()[0]["idea_count"] == 2


def test_empty_idea_is_rejected_with_a_clear_message(client):
    person_id = add_person(client)
    response = add_idea(client, person_id, {"url": " ", "note": ""})
    assert response.status_code == 400
    assert response.get_json()["error"] == "Add a link or a note."
    assert person(client, person_id).get_json()["ideas"] == []


def test_idea_that_is_too_long_is_rejected(client):
    person_id = add_person(client)
    assert add_idea(client, person_id, {"note": "x" * 2001}).status_code == 400


def test_idea_for_another_users_person_gives_404_and_writes_nothing(client):
    person_id = add_person(client, "Maya", H)
    assert add_idea(client, person_id, {"note": "sneaky"}, OTHER).status_code == 404
    assert person(client, person_id).get_json()["ideas"] == []


def test_tags_list_only_returns_your_own(client):
    person_id = add_person(client, "Maya", H)
    add_idea(client, person_id, {"note": "boots", "tags": "shoes"})
    assert client.get("/tags", headers=H).get_json() == ["shoes"]
    assert client.get("/tags", headers=OTHER).get_json() == []


def test_cors_allows_only_the_ui_origin(client):
    ok = client.options("/people", headers={"Origin": "http://localhost:8080"})
    assert ok.status_code == 204
    assert ok.headers.get("Access-Control-Allow-Origin") == "http://localhost:8080"
    other = client.options("/people", headers={"Origin": "https://evil.example"})
    assert other.headers.get("Access-Control-Allow-Origin") is None


def test_unknown_route_gives_a_json_404(client):
    response = client.get("/nope", headers=H)
    assert response.status_code == 404
    assert "error" in response.get_json()


def test_unexpected_failure_gives_a_generic_500(client, monkeypatch):
    def broken(user_id):
        raise RuntimeError("secret internal detail")

    monkeypatch.setattr(main_module.people, "list_people", broken)
    response = client.get("/people", headers=H)
    assert response.status_code == 500
    assert response.get_json() == {"error": "internal error"}