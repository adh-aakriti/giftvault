# AI Usage Log
 
## 2026-09-20 — Flask skeleton
Tool: Claude
Prompt: Minimal Flask app satisfying the deployment contract in section 7 (bind to 0.0.0.0, port and data directory from environment variables)
Disposition: Modified
What changed and why: Default port changed from 5000 to 5001, because macOS uses 5000 for AirPlay Receiver.
In my own words, how this works: Env vars come out of the shell as strings, Flask needs a number for the port, so `int()` parses it. The app listens on `0.0.0.0` so requests from outside the container reach it, rather than only the internal loopback. `DATA_DIR` is read from the environment because the database has to go wherever persistent storage is mounted, and hardcoding it means the file dies when the container restarts.
 
## 2026-09-29 — SQLite schema and database initialisation
Tool: Claude
Prompt: Schema for the five tables, plus a db module to open connections and create tables at startup
Disposition: Modified
What changed and why: Added a CHECK constraint so an idea must have either a url or a note. Built the schema path from `__file__` so the app runs from any working directory rather than only from inside the project folder.
In my own words, how this works: `init_db()` runs on every startup. `IF NOT EXISTS` means existing tables are left alone and only missing ones are created, so the second run doesn't error. That is what lets someone clone and start the app with no migration step.
 
SQLite ignores foreign key constraints unless they are switched on, and the setting is per connection rather than a property of the file. Without `PRAGMA foreign_keys = ON`, `REFERENCES` and `ON DELETE CASCADE` do nothing, so deleting a person would leave their ideas behind as orphans.
 
Without `row_factory = sqlite3.Row`, queries return tuples, so columns are accessed by position (`row[0]`) and the order has to be remembered. `sqlite3.Row` makes rows behave like dictionaries, so it is `row["name"]` in Python and `person.name` in the template.
 
## 2026-09-29 — Cookie-based visitor identity
Tool: Claude
Prompt: Identify visitors without a login, using a random id in a cookie
Disposition: Accepted
What changed and why: Accepted as written.
In my own words, how this works: `before_request` is a Flask hook that runs before every route function. Mine reads the user id from the cookie, or generates one if the visitor doesn't have it yet. `after_request` runs once the route has returned and receives the response object, which is where the cookie gets set, since setting a cookie means adding a header to the outgoing response. `g` is Flask's per-request scratchpad: anything stored on it is available to every function handling that request and discarded afterwards. The cookie is only set for new visitors, because an existing visitor's browser already holds it and sends it with every request.
 
## 2026-09-30 — People and ideas query modules, routes and templates
Tool: Claude
Prompt: Query modules for people and ideas, with the list page, person page, and their templates
Disposition: Accepted
What changed and why: Accepted as written.
In my own words, how this works: `?` placeholders mean the driver sends the query and the values separately, so a value can never be interpreted as SQL. Building the query with an f-string would let a crafted input run as a command, which is SQL injection.
 
`get_person` filters on user_id as well as id because person_id comes from the URL and anyone can change it. Without the user_id check they could open someone else's person page. With it, the query returns nothing and they get a 404, which also doesn't reveal whether that id exists.

## 2026-10-06 — Tagging: parser, storage and form
Tool: Claude
Prompt: Comma-separated tag input on the idea form, stored through the tags and idea_tags tables
Disposition: Accepted
What changed and why: Accepted as written. Kept the tagger deliberately simple after the professor's feedback that two well-executed features beat three partly finished ones.
In my own words, how this works: `parse_tags` takes the raw string from the form, splits it on commas, strips whitespace from each part, lowercases it, and drops duplicates within the same submission. Lowercasing is what makes "Marvel" and "marvel" the same tag rather than two.
 
`set_tags` uses `INSERT OR IGNORE` twice. On the tags table, the UNIQUE constraint on (user_id, name) means an existing tag is silently skipped instead of being duplicated. On idea_tags, the composite primary key on (idea_id, tag_id) does the same for an idea that already carries that tag. In both cases the database enforces it, so the application does not have to check first.
 
`tagger.py` imports nothing and touches neither Flask nor the database. That keeps `parse_tags` a pure function: the same input always produces the same output, so it can be tested directly without a server or a database file. It is the main coverage target for the Ideas domain.

## 2026-10-07 — Occasions domain: date logic, countdown and routes
Tool: Claude
Prompt: Occasions module with annual recurrence, days-until calculation and an upcoming page sorted by urgency
Disposition: Accepted
What changed and why: Accepted as written.
In my own words, how this works: `next_occurrence` checks whether a recurring date has already passed this year and rolls it forward to next year if so, rather than returning a negative countdown. A non-recurring date that has passed returns None and drops off the list. Leap-year dates fall back to 1 March in non-leap years, because `replace(year=...)` raises ValueError when 29 February does not exist in the target year.
 
`today` is a parameter rather than something the function looks up itself, so the function is deterministic and can be tested with any date. If it called `date.today()` internally, a test asserting "8 days away" would fail the next day, and a leap-year case could only be tested in a leap year. The real date enters at the route, which calls `occasions.upcoming(g.user_id, date.today())`.
 
`upcoming` joins to `people` because it needs user_id to check ownership, which is its own domain's relationship. For the idea count it calls `ideas.count_ideas_for()` rather than joining to the ideas table. That function call is the seam between the two domains: if they were split into separate services later, the call would become a request and nothing else would change.

## 2026-10-11 — Unit tests and coverage configuration
Tool: Claude
Prompt: pytest tests for tag parsing, date recurrence and ownership filtering, with coverage measured on the logic modules
Disposition: Modified
What changed and why: Added a pytest.ini after the first run failed to import the project modules. Added further tests for list_for_person and a leap-year case, which raised coverage from 56% to 96%.
In my own words, how this works: The tests sit in a subfolder, so when pytest imports a test file and that file does `from tagger import parse_tags`, Python looks for `tagger` on its import path, where the project root is not present by default. That is the ModuleNotFoundError I got on the first run. `pythonpath = .` adds the root, so the import resolves.
 
`temp_db` is a pytest fixture, so it runs before any test that takes it as a parameter. It creates a temporary directory, points DATA_DIR at it, and initialises the schema. Each test gets its own call, so tests cannot contaminate the real database or each other. That isolation is what lets a test assert the people list equals exactly one name.
 
`monkeypatch.setenv` sets DATA_DIR for the duration of one test and restores it afterwards. It works because db.py reads the path from the environment rather than hardcoding it, which was already required so the deployment can point the database at mounted storage. The same property lets a test point it at a temporary directory.
 
db.py reads DATA_DIR at import time, so the value is fixed once the module loads and the fixture's change would otherwise be ignored. `importlib.reload` re-executes the file so it picks up the temporary directory, and people, ideas and occasions are reloaded too because they hold a reference to db's connection function. Reading the path inside `get_connection()` instead would remove the need for this.

## 2026-10-12 — Parametrizing the tag parsing tests
Tool: Claude
Prompt: Rewrite the seven separate tag parsing tests as a single parametrized test
Disposition: Accepted
What changed and why: Two cases were added that the original tests did not cover: a single tag with no comma, and whitespace-only input. Test count went from 25 to 28; coverage unchanged at 96%.
In my own words, how this works: `@pytest.mark.parametrize` takes a table of input and expected-output pairs and runs the same test body once for each row, so seven near-identical test functions collapse into one. pytest counts each row as its own test, which is why the suite still reports a count rather than a single test.
 
The count went up by three rather than two because one of the original functions held two assertions in the same body, for `""` and for `None`. Splitting them into separate rows is the real benefit, not just tidiness: if the first assertion fails, the second never runs, so a bug in the `None` case would have been invisible until the first one was fixed. As separate rows each case is reported independently.
 