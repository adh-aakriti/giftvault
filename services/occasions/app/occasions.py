from datetime import date

from . import ideas_client
from .db import get_connection


def next_occurrence(occasion_date, recurs_annually, today):
    """Return the next date this occasion falls on, or None if it has passed."""
    if not recurs_annually:
        return occasion_date if occasion_date >= today else None

    try:
        this_year = occasion_date.replace(year=today.year)
    except ValueError:
        this_year = date(today.year, 3, 1)

    if this_year >= today:
        return this_year

    try:
        return occasion_date.replace(year=today.year + 1)
    except ValueError:
        return date(today.year + 1, 3, 1)


def days_until(target, today):
    return (target - today).days


def add_occasion(user_id, person_id, label, occasion_date, recurs_annually):
    """Insert one occasion and return its id. occasion_date is a date object."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO occasions (user_id, person_id, label, occasion_date, recurs_annually)
               OUTPUT INSERTED.id
               VALUES (%s, %s, %s, %s, %s)""",
            (user_id, person_id, label.strip(), occasion_date, 1 if recurs_annually else 0),
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        return new_id
    finally:
        conn.close()


def list_for_person(user_id, person_id):
    conn = get_connection()
    try:
        cur = conn.cursor(as_dict=True)
        cur.execute(
            """SELECT id, person_id, label, occasion_date, recurs_annually
               FROM occasions WHERE user_id = %s AND person_id = %s
               ORDER BY occasion_date""",
            (user_id, person_id),
        )
        return cur.fetchall()
    finally:
        conn.close()


def _rows_for_user(user_id):
    conn = get_connection()
    try:
        cur = conn.cursor(as_dict=True)
        cur.execute(
            """SELECT id, person_id, label, occasion_date, recurs_annually
               FROM occasions WHERE user_id = %s""",
            (user_id,),
        )
        return cur.fetchall()
    finally:
        conn.close()


def upcoming(user_id, today):
    """Return (results, degraded). If Ideas is down, occasions still come back,
    with person_name and idea_count set to None, and degraded is True."""
    rows = _rows_for_user(user_id)

    people = {}
    degraded = False
    for person_id in sorted({r["person_id"] for r in rows}):
        if degraded:
            break
        try:
            people[person_id] = ideas_client.get_person(user_id, person_id)
        except ideas_client.PersonNotFound:
            people[person_id] = None
        except ideas_client.IdeasUnavailable:
            degraded = True

    results = []
    for row in rows:
        nxt = next_occurrence(row["occasion_date"], row["recurs_annually"], today)
        if nxt is None:
            continue
        person = people.get(row["person_id"])
        results.append({
            "id": row["id"],
            "label": row["label"],
            "person_id": row["person_id"],
            "person_name": person.get("name") if person else None,
            "date": nxt.isoformat(),
            "days": days_until(nxt, today),
            "idea_count": ideas_client.idea_count(person) if person else None,
        })

    results.sort(key=lambda r: r["days"])
    return results, degraded
