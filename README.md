# giftvault

A personal gift-idea notebook. Save links and notes about people through the year, tag them, and see them again shortly before the occasion they are for.

Built for Individual Assignment 1 (SWD).

Two feature domains: **Ideas** (capture, collections, tagging) and **Occasions** (dates, annual recurrence, countdowns). They share only `person_id`. There is no login; each visitor is identified by a random id stored in a cookie on first visit.

## Requirements

Python 3.10 or newer to run directly, or Docker to run in a container. No external services, no database server.

## Setup

```
git clone https://github.com/adh-aakriti/giftvault
cd giftvault
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Running

### Directly

```
python app.py
```

Then open http://localhost:5001

### In a container

```
docker build -t giftvault .
docker run -p 8000:8000 -v giftvault-data:/data giftvault
```

Then open http://localhost:8000

The database file and its directory are created on first start. There is no migration step either way.

### Configuration

Every setting is read from an environment variable with a default, so nothing needs editing to run:

| Variable | Default (direct) | Default (container) | Purpose |
|---|---|---|---|
| `PORT` | `5001` | `8000` | Port the app listens on |
| `DATA_DIR` | `./data` | `/data` | Directory holding the SQLite file |

The SQLite file is always `$DATA_DIR/app.db`. The container defaults come from the Dockerfile, which sets `PORT=8000` and `DATA_DIR=/data` so a volume can be mounted at `/data` and the database survives the container being recreated.

Running directly, the port defaults to 5001 rather than Flask's usual 5000, which macOS uses for AirPlay Receiver. Either variable can be overridden at the command line:

```
PORT=8000 DATA_DIR=/tmp/giftvault python app.py
docker run -e PORT=9000 -p 9000:9000 -v giftvault-data:/data giftvault
```

## Tests

```
pytest --cov=tagger --cov=occasions --cov-report=term-missing
```

28 tests, 96% coverage on the two logic modules.

## Container contract

Output of `container/run.sh` from the assignment repository, run against this repo:

```
=== SDD Assignment 1 contract check ===
Repository: /Users/aakriti/giftvault

==> Repository shape
  PASS  one Dockerfile, one manifest (requirements.txt)

==> Build from a clean context, no build args
  PASS  image built
  PASS  image size 53 MB

==> Start on PORT=8000 and reach it from the host
  PASS  HTTP 302 from http://localhost:8000/

==> SQLite file under DATA_DIR
  PASS  found in /data: app.db

==> Data persists, and a second boot does not re-seed
  PASS  volume at /data persists
  PASS  row counts unchanged across restart: idea_tags=0 ideas=0 occasions=0 people=0 tags=0

==> PORT override is honoured (not hardcoded)
  PASS  HTTP 302 from http://localhost:9123/

=== ALL CHECKS PASSED ===
```

The app ships no seed data, and the schema is created with `CREATE TABLE IF NOT EXISTS` on every boot, so a restart creates what is missing and leaves everything else alone.

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
Dockerfile          provided template with its TODOs filled in
ADR.md              architecture decision record
AI_USAGE.md         AI usage log
```