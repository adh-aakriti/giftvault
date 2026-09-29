# Architecture Decision Record

Decisions recorded as they were made. Format per assignment §5

## 1. Flask over Django and FastAPI
Date: 2026-09-28
Status: Decided
Context: The app has to run as a single process serving HTML pages, with SQLite underneath and roughly five tables. I needed a Python web framework to build it on.
Decision: Flask, with the standard library's sqlite3 module and Jinja templates. Three third-party dependencies in total (Flask, pytest, pytest-cov).
Alternatives considered: Django, rejected because its ORM, admin interface, auth system and migration framework are built for projects far larger than five tables — I would install all of it and use a fraction. FastAPI, rejected because it is designed for JSON APIs consumed by a separate frontend, and this app renders HTML from the same process, so its main strengths would go unused.
Consequences: No migration tooling, so schema changes mean editing schema.sql and recreating the database file. No admin interface, so every form is hand-written. In exchange the dependency count stays low and the SQL is written directly, which suits a database I designed myself.

## 2. Scoping Ideas and Occasions as independently modularizable domains
Date: 2026-09-29
Status: Decided
Context: The assignment requires two feature domains that could each become a separate service later. Everything in this app relates to a person, so the split had to be drawn by behaviour rather than by entity.
Decision: Ideas owns capture, collections and tagging. Occasions owns dates, recurrence and countdowns. They share only person_id, and Occasions never queries the ideas tables. When the countdown needs an idea count, it calls a function that ideas.py exposes.
Alternatives considered: A People domain separate from Ideas, rejected because People holds almost no logic and the result would be one empty domain and one doing all the work.
Consequences: The seam is a function boundary, so splitting these into services later means replacing a call with a request. The cost is discipline, since the join that would answer the countdown's idea count directly is available and has to be deliberately avoided.
 
## 3. Data model: per-user tags, and where ownership lives
Date: 2026-09-29
Status: Decided
Context: There is no login. Each visitor is a random id stored in a cookie, so every table has to answer whose row it is.
Decision: people and tags carry user_id. ideas and occasions carry only person_id and derive ownership through the join to people. Tags relate to ideas through idea_tags, keyed on the composite (idea_id, tag_id).
Alternatives considered: A global tags table shared across users, rejected because tag names are personal and one user's rename would affect everyone. Storing user_id on ideas as well, rejected because it depends on person_id rather than on the idea itself, which violates third normal form.
Consequences: Ideas queries join through people to check ownership. The composite key means the database rejects a duplicate tag on an idea rather than application code having to check first. Dates are stored as ISO text and recurs_annually as 0 or 1, since SQLite has neither a date nor a boolean type.
 