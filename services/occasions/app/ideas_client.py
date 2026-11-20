import os

import requests

IDEAS_URL = os.environ.get("IDEAS_URL", "http://ideas:8000").rstrip("/")
TIMEOUT_S = float(os.environ.get("IDEAS_TIMEOUT_S", "3"))


class IdeasUnavailable(Exception):
    """Ideas could not be reached in time, or it answered with an error."""


class PersonNotFound(Exception):
    """Ideas says this person does not exist for this user."""


def get_person(user_id, person_id):
    """Fetch one person from the Ideas service. The owner check happens there."""
    url = f"{IDEAS_URL}/people/{int(person_id)}"
    try:
        resp = requests.get(url, headers={"X-User-Id": user_id}, timeout=TIMEOUT_S)
    except requests.RequestException as exc:
        raise IdeasUnavailable(str(exc)) from exc
    if resp.status_code == 404:
        raise PersonNotFound(person_id)
    if resp.status_code != 200:
        raise IdeasUnavailable(f"ideas answered {resp.status_code}")
    return resp.json()


def idea_count(person):
    return len(person.get("ideas", []))
