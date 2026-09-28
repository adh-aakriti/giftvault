# Architecture Decision Record

Decisions recorded as they were made. Format per assignment §5

## 1. Flask over Django and FastAPI
Date: 2026-09-28
Status: Decided
Context: The app has to run as a single process serving HTML pages, with SQLite underneath and roughly five tables. I needed a Python web framework to build it on.
Decision: Flask, with the standard library's sqlite3 module and Jinja templates. Three third-party dependencies in total (Flask, pytest, pytest-cov).
Alternatives considered: Django, rejected because its ORM, admin interface, auth system and migration framework are built for projects far larger than five tables — I would install all of it and use a fraction. FastAPI, rejected because it is designed for JSON APIs consumed by a separate frontend, and this app renders HTML from the same process, so its main strengths would go unused.
Consequences: No migration tooling, so schema changes mean editing schema.sql and recreating the database file. No admin interface, so every form is hand-written. In exchange the dependency count stays low and the SQL is written directly, which suits a database I designed myself.