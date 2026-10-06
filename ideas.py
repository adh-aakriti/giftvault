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
    cur = conn.execute(
        "INSERT INTO ideas (person_id, url, note) VALUES (?, ?, ?)",
        (person_id, url.strip() or None, note.strip() or None),
    )
    conn.commit()
    idea_id = cur.lastrowid
    conn.close()
    return idea_id


def count_ideas_for(person_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM ideas WHERE person_id = ?",
        (person_id,),
    ).fetchone()
    conn.close()
    return row["n"]


def set_tags(user_id, idea_id, tag_names):
    conn = get_connection()
    for name in tag_names:
        conn.execute(
            "INSERT OR IGNORE INTO tags (user_id, name) VALUES (?, ?)",
            (user_id, name),
        )
        tag = conn.execute(
            "SELECT id FROM tags WHERE user_id = ? AND name = ?",
            (user_id, name),
        ).fetchone()
        conn.execute(
            "INSERT OR IGNORE INTO idea_tags (idea_id, tag_id) VALUES (?, ?)",
            (idea_id, tag["id"]),
        )
    conn.commit()
    conn.close()


def tags_for_idea(idea_id):
    conn = get_connection()
    rows = conn.execute(
        """SELECT t.name FROM tags t
           JOIN idea_tags it ON it.tag_id = t.id
           WHERE it.idea_id = ?
           ORDER BY t.name""",
        (idea_id,),
    ).fetchall()
    conn.close()
    return [r["name"] for r in rows]


def all_tags(user_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT name FROM tags WHERE user_id = ? ORDER BY name",
        (user_id,),
    ).fetchall()
    conn.close()
    return [r["name"] for r in rows]