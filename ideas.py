from db import get_connection


def get_person(user_id, person_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT id, name FROM people WHERE id = ? AND user_id = ?",
        (person_id, user_id),
    ).fetchone()
    conn.close()
    return row


def list_ideas(person_id):
    conn = get_connection()
    rows = conn.execute(
        """SELECT id, url, note, created_at, given_at
           FROM ideas WHERE person_id = ?
           ORDER BY created_at DESC""",
        (person_id,),
    ).fetchall()
    conn.close()
    return rows


def add_idea(person_id, url, note):
    conn = get_connection()
    conn.execute(
        "INSERT INTO ideas (person_id, url, note) VALUES (?, ?, ?)",
        (person_id, url.strip() or None, note.strip() or None),
    )
    conn.commit()
    conn.close()


def count_ideas_for(person_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM ideas WHERE person_id = ?",
        (person_id,),
    ).fetchone()
    conn.close()
    return row["n"]