import os

import pytest


@pytest.fixture
def clean_db():
    """Empty the Ideas tables before a test. Needs a running SQL Server."""
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL is not set: start SQL Server with docker compose to run database tests")
    from app import db

    db.init_db()
    conn = db.get_connection()
    cur = conn.cursor()
    for table in ("idea_tags", "ideas", "tags", "people"):
        cur.execute(f"DELETE FROM {table}")
    conn.commit()
    conn.close()
