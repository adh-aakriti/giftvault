CREATE TABLE IF NOT EXISTS people (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id  TEXT NOT NULL,
    name     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ideas (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id  INTEGER NOT NULL REFERENCES people(id) ON DELETE CASCADE,
    url        TEXT,
    note       TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    given_at   TEXT,
    CHECK (
        (url IS NOT NULL AND url != '')
        OR (note IS NOT NULL AND note != '')
    )
);

CREATE TABLE IF NOT EXISTS tags (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id  TEXT NOT NULL,
    name     TEXT NOT NULL,
    UNIQUE (user_id, name)
);

CREATE TABLE IF NOT EXISTS idea_tags (
    idea_id  INTEGER NOT NULL REFERENCES ideas(id) ON DELETE CASCADE,
    tag_id   INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (idea_id, tag_id)
);

CREATE TABLE IF NOT EXISTS occasions (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id        INTEGER NOT NULL REFERENCES people(id) ON DELETE CASCADE,
    label            TEXT NOT NULL,
    date             TEXT NOT NULL,
    recurs_annually  INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_people_user ON people(user_id);
CREATE INDEX IF NOT EXISTS idx_ideas_person ON ideas(person_id);
CREATE INDEX IF NOT EXISTS idx_occasions_person ON occasions(person_id);