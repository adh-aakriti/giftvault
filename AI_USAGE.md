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
 
## 2026-09-29 — People and ideas query modules, routes and templates
Tool: Claude
Prompt: Query modules for people and ideas, with the list page, person page, and their templates
Disposition: Accepted
What changed and why: Accepted as written.
In my own words, how this works: `?` placeholders mean the driver sends the query and the values separately, so a value can never be interpreted as SQL. Building the query with an f-string would let a crafted input run as a command, which is SQL injection.
 
`get_person` filters on user_id as well as id because person_id comes from the URL and anyone can change it. Without the user_id check they could open someone else's person page. With it, the query returns nothing and they get a 404, which also doesn't reveal whether that id exists.