# giftvault
 
A personal gift-idea notebook. Save links and notes about people through the year, tag them, and see them again shortly before the occasion they are for.
 
Built for Individual Assignment 1 (SWD).
 
Two feature domains: **Ideas** (capture, collections, tagging) and **Occasions** (dates, annual recurrence, countdowns). They share only `person_id`. There is no login; each visitor is identified by a random id stored in a cookie on first visit.
 
## Requirements
 
Python 3.10 or newer. No external services, no database server.
 
## Setup
 
```bash
git clone https://github.com/adh-aakriti/giftvault
cd giftvault
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```
 
## Running
 
```bash
python app.py
```
 
Then open http://localhost:5001
 
The database file and its directory are created automatically on first start. There is no migration step.
 
### Configuration
 
Both settings are read from environment variables, with defaults, so nothing needs editing to run:
 
| Variable | Default | Purpose |
|---|---|---|
| `PORT` | `5001` | Port the app listens on |
| `DATA_DIR` | `./data` | Directory holding the SQLite file (`app.db`) |
 
```bash
PORT=8000 DATA_DIR=/tmp/giftvault python app.py
```
 
The port defaults to 5001 rather than Flask's usual 5000, which macOS uses for AirPlay Receiver. Set `PORT` to use any other.

## Tests
 
```bash
pytest --cov=tagger --cov=occasions --cov-report=term-missing
```
 
28 tests, 96% coverage on the two logic modules.
 
## Using it
 
1. Add a person on the people page.
2. Open that person and save an idea: a link, a note, or both, with optional comma-separated tags.
3. Add an occasion for them, ticking "every year" for a birthday.
4. The upcoming page lists everyone by how soon their occasion is, with how many ideas are saved for each.
## Project structure
 
```
app.py              Flask routes, cookie identity
db.py               connection handling, schema initialisation
schema.sql          table definitions
people.py           people queries
ideas.py            ideas and tags queries
tagger.py           tag parsing (pure functions)
occasions.py        date logic (pure functions) and occasion queries
templates/          Jinja templates, extending base.html
static/             stylesheet
tests/              pytest suite
docs/               architecture and database diagrams
ADR.md              architecture decision record
AI_USAGE.md         AI usage log
```
 