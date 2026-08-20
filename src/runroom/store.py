"""SQLite schema. The append-only guarantee is enforced here, in the database.

Triggers, not application code, reject edits and deletes on `events`. A future
feature, a stray migration, or someone at a `sqlite3` prompt all hit the same wall.
"""

import sqlite3
from pathlib import Path

DB_FILENAME = "runroom.db"

SCHEMA = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS participants (
    name           TEXT PRIMARY KEY,
    kind           TEXT NOT NULL CHECK (kind IN ('agent', 'human')),
    provider       TEXT,
    credential_ref TEXT,
    reviewer       INTEGER NOT NULL DEFAULT 0,
    created_at     REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS runs (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    title            TEXT NOT NULL,
    notes            TEXT NOT NULL DEFAULT '',
    status           TEXT NOT NULL,
    holder           TEXT REFERENCES participants(name),
    scope            TEXT,
    lease_expires_at REAL,
    lease_seconds    REAL,
    submitted_by     TEXT,
    created_at       REAL NOT NULL,
    updated_at       REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    seq    INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES runs(id),
    at     REAL NOT NULL,
    actor  TEXT NOT NULL,
    action TEXT NOT NULL,
    detail TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS events_by_run ON events (run_id, seq);

-- The audit history is append-only. This is not a policy; it is a constraint.
CREATE TRIGGER IF NOT EXISTS events_are_immutable_update
BEFORE UPDATE ON events
BEGIN
    SELECT RAISE(ABORT, 'runroom: audit history is append-only (update rejected)');
END;

CREATE TRIGGER IF NOT EXISTS events_are_immutable_delete
BEFORE DELETE ON events
BEGIN
    SELECT RAISE(ABORT, 'runroom: audit history is append-only (delete rejected)');
END;
"""


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = connect(db_path)
    conn.executescript(SCHEMA)
    return conn
