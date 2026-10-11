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
 
 ## 4. Testing the pure logic first, database access second
Date: 2026-10-09
Status: Decided
Context: Section 4 asks for coverage of core business logic rather than framework glue or routing, so the first question was which code actually contains rules that could be wrong.
Decision: Tag parsing and date recurrence are tested directly as pure functions. Database access is tested only where it enforces a rule, which is ownership filtering and the upcoming query. Coverage is measured on tagger.py and occasions.py with `pytest --cov=tagger --cov=occasions --cov-report=term-missing`, currently 96% across 25 tests.
Alternatives considered: Testing the Flask routes with a test client, rejected because the routes contain no logic of their own. They read a form, call a domain function and redirect, so a route test would mostly assert that Flask works. Testing people.py, rejected for the same reason: it is an INSERT and a SELECT with no branch that could produce a wrong answer.
Consequences: The two uncovered lines in occasions.py are the leap-year fallback inside the first branch of next_occurrence. The templates and routes are untested, so a broken form or a wrong template variable would not be caught by the suite. Testing the database functions required reloading the modules inside the fixture, because db.py reads DATA_DIR at import time rather than inside get_connection; computing the path per connection would have avoided that and is the cleaner design.
 
## 5. Not building automatic tagging
Date: 2026-10-09
Status: Decided
Context: Tags are typed by hand, so "book" and "books" become separate tags and nothing connects "marvel" to "mcu". Either a keyword dictionary or a language model would close that gap.
Decision: Tags are entered manually, with a datalist of previously used tags as the only assistance.
Alternatives considered: A hardcoded keyword dictionary mapping terms to themes, rejected because it only recognises words chosen in advance and still fails on typos and synonyms. A language model API, rejected because it is non-deterministic, which makes the tagging logic untestable against a coverage target, and because it requires an API key the grader would not have, breaking the clone-and-run requirement in section 7.4.
Consequences: Tag quality depends on the user being consistent, and near-duplicate tags will accumulate. In exchange the tagging logic stays a pure function with no external dependency, which is what makes it the most thoroughly covered module in the project.