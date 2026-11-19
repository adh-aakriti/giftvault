from .db import get_connection


def get_person(user_id, person_id):
    conn = get_connection()
    cur = conn.cursor(as_dict=True)
    cur.execute(
        "SELECT id, name FROM people WHERE id = %s AND user_id = %s",
        (person_id, user_id),
    )
    row = cur.fetchone()
    conn.close()
    return row


def list_ideas(person_id):
    conn = get_connection()
    cur = conn.cursor(as_dict=True)
    cur.execute(
        """SELECT id, url, note, created_at, given_at
           FROM ideas WHERE person_id = %s
           ORDER BY created_at DESC""",
        (person_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def add_idea(person_id, url, note):
    conn = get_connection()
    cur = conn.cursor(as_dict=True)
    cur.execute(
        "INSERT INTO ideas (person_id, url, note) OUTPUT INSERTED.id VALUES (%s, %s, %s)",
        (person_id, url.strip() or None, note.strip() or None),
    )
    idea_id = cur.fetchone()["id"]
    conn.commit()
    conn.close()
    return idea_id


def count_ideas_for(person_id):
    conn = get_connection()
    cur = conn.cursor(as_dict=True)
    cur.execute(
        "SELECT COUNT(*) AS n FROM ideas WHERE person_id = %s",
        (person_id,),
    )
    row = cur.fetchone()
    conn.close()
    return row["n"]


def set_tags(user_id, idea_id, tag_names):
    conn = get_connection()
    cur = conn.cursor(as_dict=True)
    for name in tag_names:
        cur.execute(
            "IF NOT EXISTS (SELECT 1 FROM tags WHERE user_id = %s AND name = %s) "
            "INSERT INTO tags (user_id, name) VALUES (%s, %s)",
            (user_id, name, user_id, name),
        )
        cur.execute(
            "SELECT id FROM tags WHERE user_id = %s AND name = %s",
            (user_id, name),
        )
        tag = cur.fetchone()
        cur.execute(
            "IF NOT EXISTS (SELECT 1 FROM idea_tags WHERE idea_id = %s AND tag_id = %s) "
            "INSERT INTO idea_tags (idea_id, tag_id) VALUES (%s, %s)",
            (idea_id, tag["id"], idea_id, tag["id"]),
        )
    conn.commit()
    conn.close()


def tags_for_idea(idea_id):
    conn = get_connection()
    cur = conn.cursor(as_dict=True)
    cur.execute(
        """SELECT t.name FROM tags t
           JOIN idea_tags it ON it.tag_id = t.id
           WHERE it.idea_id = %s
           ORDER BY t.name""",
        (idea_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return [r["name"] for r in rows]


def all_tags(user_id):
    conn = get_connection()
    cur = conn.cursor(as_dict=True)
    cur.execute(
        "SELECT name FROM tags WHERE user_id = %s ORDER BY name",
        (user_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return [r["name"] for r in rows]
