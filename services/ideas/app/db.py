import os
import time
import uuid
from urllib.parse import unquote, urlparse

import pymssql

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "migrations")
CONNECT_RETRY_SECONDS = int(os.environ.get("DB_CONNECT_RETRY_S", "90"))


def _connection_params():
    url = urlparse(os.environ["DATABASE_URL"])
    return {
        "server": url.hostname,
        "port": url.port or 1433,
        "user": unquote(url.username),
        "password": unquote(url.password),
        "database": url.path.lstrip("/"),
    }


def get_connection(retry_seconds=None):
    params = _connection_params()
    deadline = time.monotonic() + (CONNECT_RETRY_SECONDS if retry_seconds is None else retry_seconds)
    delay = 1
    while True:
        try:
            return pymssql.connect(login_timeout=10, **params)
        except pymssql.Error as exc:
            if time.monotonic() + delay > deadline:
                raise
            print(f"database not ready ({type(exc).__name__}), retrying in {delay}s", flush=True)
            time.sleep(delay)
            delay = min(delay * 2, 10)


def init_db():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "IF OBJECT_ID('schema_migrations') IS NULL "
            "CREATE TABLE schema_migrations ("
            "version NVARCHAR(100) PRIMARY KEY, "
            "applied_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME())"
        )
        conn.commit()
        cur.execute("SELECT version FROM schema_migrations")
        applied = {row[0] for row in cur.fetchall()}
        for name in sorted(os.listdir(MIGRATIONS_DIR)):
            if not name.endswith(".sql") or name in applied:
                continue
            with open(os.path.join(MIGRATIONS_DIR, name), encoding="utf-8") as f:
                sql = f.read()
            try:
                cur.execute(sql)
                cur.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (name,))
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            print(f"migration applied: {name}", flush=True)
    finally:
        conn.close()


def check_db():
    """Fail fast (no retries): can this service read and write its own database?"""
    conn = get_connection(retry_seconds=0)
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchall()
        cur.execute("INSERT INTO schema_migrations (version) VALUES (%s)",
                    ("_health_" + uuid.uuid4().hex,))
        conn.rollback()
    finally:
        conn.close()
