CREATE TABLE people (
    id       INT IDENTITY(1,1) PRIMARY KEY,
    user_id  NVARCHAR(64)  NOT NULL,
    name     NVARCHAR(200) NOT NULL
);

CREATE TABLE ideas (
    id         INT IDENTITY(1,1) PRIMARY KEY,
    person_id  INT NOT NULL REFERENCES people(id) ON DELETE CASCADE,
    url        NVARCHAR(2000) NULL,
    note       NVARCHAR(2000) NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    given_at   DATETIME2 NULL,
    CHECK (
        (url IS NOT NULL AND url <> '')
        OR (note IS NOT NULL AND note <> '')
    )
);

CREATE TABLE tags (
    id       INT IDENTITY(1,1) PRIMARY KEY,
    user_id  NVARCHAR(64)  NOT NULL,
    name     NVARCHAR(100) NOT NULL,
    UNIQUE (user_id, name)
);

CREATE TABLE idea_tags (
    idea_id  INT NOT NULL REFERENCES ideas(id) ON DELETE CASCADE,
    tag_id   INT NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (idea_id, tag_id)
);

CREATE INDEX idx_people_user ON people(user_id);
CREATE INDEX idx_ideas_person ON ideas(person_id);
