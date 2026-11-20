CREATE TABLE occasions (
    id               INT IDENTITY(1,1) PRIMARY KEY,
    user_id          NVARCHAR(64)  NOT NULL,
    person_id        INT           NOT NULL,
    label            NVARCHAR(200) NOT NULL,
    occasion_date    DATE          NOT NULL,
    recurs_annually  BIT           NOT NULL DEFAULT 0,
    created_at       DATETIME2     NOT NULL DEFAULT SYSUTCDATETIME()
);

CREATE INDEX idx_occasions_user   ON occasions(user_id);
CREATE INDEX idx_occasions_person ON occasions(person_id);
