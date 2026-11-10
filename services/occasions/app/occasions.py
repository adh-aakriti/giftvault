from datetime import date

from db import get_connection
import ideas


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


def add_occasion(person_id, label, date_str, recurs_annually):
    conn = get_connection()
    conn.execute(
        """INSERT INTO occasions (person_id, label, date, recurs_annually)
           VALUES (?, ?, ?, ?)""",
        (person_id, label.strip(), date_str, 1 if recurs_annually else 0),
    )
    conn.commit()
    conn.close()


def list_for_person(person_id):
    conn = get_connection()
    rows = conn.execute(
        """SELECT id, label, date, recurs_annually
           FROM occasions WHERE person_id = ? ORDER BY date""",
        (person_id,),
    ).fetchall()
    conn.close()
    return rows


def upcoming(user_id, today):
    conn = get_connection()
    rows = conn.execute(
        """SELECT o.id, o.label, o.date, o.recurs_annually,
                  p.id AS person_id, p.name AS person_name
           FROM occasions o
           JOIN people p ON p.id = o.person_id
           WHERE p.user_id = ?""",
        (user_id,),
    ).fetchall()
    conn.close()

    results = []
    for row in rows:
        occasion_date = date.fromisoformat(row["date"])
        nxt = next_occurrence(occasion_date, row["recurs_annually"], today)
        if nxt is None:
            continue
        results.append({
            "label": row["label"],
            "person_id": row["person_id"],
            "person_name": row["person_name"],
            "date": nxt,
            "days": days_until(nxt, today),
            "idea_count": ideas.count_ideas_for(row["person_id"]),
        })

    results.sort(key=lambda r: r["days"])
    return results