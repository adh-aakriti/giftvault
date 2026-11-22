-- Migration 002: an idea can be marked as a top pick (priority 1 to 3).
-- Existing ideas keep all their data and get the default priority of 2.
ALTER TABLE ideas
    ADD priority TINYINT NOT NULL
        CONSTRAINT DF_ideas_priority DEFAULT 2
        CONSTRAINT CK_ideas_priority CHECK (priority BETWEEN 1 AND 3);
