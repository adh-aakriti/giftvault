from .db import get_connection


def list_people(user_id):
    conn = get_connection()
    cur = conn.cursor(as_dict=True)
    cur.execute(
        "SELECT id, name FROM people WHERE user_id = %s ORDER BY name",
        (user_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def add_person(user_id, name):
    conn = get_connection()
    cur = conn.cursor(as_dict=True)
    cur.execute(
        "INSERT INTO people (user_id, name) OUTPUT INSERTED.id VALUES (%s, %s)",
        (user_id, name.strip()),
    )
    person_id = cur.fetchone()["id"]
    conn.commit()
    conn.close()
    return person_id
