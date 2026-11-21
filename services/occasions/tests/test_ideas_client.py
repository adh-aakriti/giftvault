import pytest
import requests
from app import ideas_client


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}

    def json(self):
        return self._payload


@pytest.fixture
def ideas_call(monkeypatch):
    """Replace requests.get. Returns a function that sets the outcome and the call log."""
    log = []

    def install(outcome):
        def fake_get(url, headers=None, timeout=None):
            log.append({"url": url, "headers": headers, "timeout": timeout})
            if isinstance(outcome, Exception):
                raise outcome
            return outcome

        monkeypatch.setattr(ideas_client.requests, "get", fake_get)
        return log

    return install


def test_get_person_returns_the_person_and_sends_the_user_header(ideas_call):
    log = ideas_call(FakeResponse(200, {"id": 7, "name": "Maya", "ideas": []}))
    person = ideas_client.get_person("user-a", 7)
    assert person["name"] == "Maya"
    assert log[0]["url"] == f"{ideas_client.IDEAS_URL}/people/7"
    assert log[0]["headers"] == {"X-User-Id": "user-a"}
    assert log[0]["timeout"] == ideas_client.TIMEOUT_S


def test_person_id_is_sent_as_a_number(ideas_call):
    log = ideas_call(FakeResponse(200, {"id": 7, "ideas": []}))
    ideas_client.get_person("user-a", "7")
    assert log[0]["url"].endswith("/people/7")


def test_a_404_means_the_person_was_not_found(ideas_call):
    ideas_call(FakeResponse(404))
    with pytest.raises(ideas_client.PersonNotFound):
        ideas_client.get_person("user-a", 99)


@pytest.mark.parametrize("status", [500, 502, 503])
def test_an_error_status_means_ideas_is_unavailable(ideas_call, status):
    ideas_call(FakeResponse(status))
    with pytest.raises(ideas_client.IdeasUnavailable, match=str(status)):
        ideas_client.get_person("user-a", 1)


@pytest.mark.parametrize(
    "error",
    [requests.Timeout("too slow"), requests.ConnectionError("connection refused")],
)
def test_network_problems_mean_ideas_is_unavailable(ideas_call, error):
    ideas_call(error)
    with pytest.raises(ideas_client.IdeasUnavailable) as info:
        ideas_client.get_person("user-a", 1)
    assert info.value.__cause__ is error


def test_idea_count_counts_the_ideas_and_defaults_to_zero():
    assert ideas_client.idea_count({"ideas": [1, 2, 3]}) == 3
    assert ideas_client.idea_count({}) == 0
