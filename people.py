from db import get_connection


def list_people(user_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, name FROM people WHERE user_id = ? ORDER BY name",
        (user_id,),
    ).fetchall()
    conn.close()
    return rows


def add_person(user_id, name):
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO people (user_id, name) VALUES (?, ?)",
        (user_id, name.strip()),
    )
    conn.commit()
    person_id = cur.lastrowid
    conn.close()
    return person_id