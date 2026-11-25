"""SQLite bootstrap for InstaKill. Uses the stdlib sqlite3 module (see R11)."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent.parent / "instakill.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS post (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES user(id),
    content TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    genres TEXT NOT NULL DEFAULT '',
    movie_id INTEGER
);

CREATE TABLE IF NOT EXISTS rating (
    user_id INTEGER NOT NULL REFERENCES user(id),
    post_id INTEGER NOT NULL REFERENCES post(id),
    value REAL NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (user_id, post_id)
);

CREATE TABLE IF NOT EXISTS post_like (
    user_id INTEGER NOT NULL REFERENCES user(id),
    post_id INTEGER NOT NULL REFERENCES post(id),
    created_at TEXT NOT NULL,
    PRIMARY KEY (user_id, post_id)
);

CREATE TABLE IF NOT EXISTS follow (
    follower_id INTEGER NOT NULL REFERENCES user(id),
    followee_id INTEGER NOT NULL REFERENCES user(id),
    created_at TEXT NOT NULL,
    PRIMARY KEY (follower_id, followee_id),
    CHECK (follower_id != followee_id)
);

CREATE INDEX IF NOT EXISTS rating_post_time ON rating(post_id, created_at);
CREATE INDEX IF NOT EXISTS rating_user_time ON rating(user_id, created_at);
CREATE INDEX IF NOT EXISTS like_post_time ON post_like(post_id, created_at);
CREATE INDEX IF NOT EXISTS like_user_time ON post_like(user_id, created_at);
CREATE INDEX IF NOT EXISTS post_created_at ON post(created_at);
"""


def get_connection(path: Path | str | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(path if path is not None else DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(path: Path | str | None = None) -> None:
    with get_connection(path) as conn:
        conn.executescript(SCHEMA)
        columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(post)").fetchall()
        }
        if "genres" not in columns:
            conn.execute("ALTER TABLE post ADD COLUMN genres TEXT NOT NULL DEFAULT ''")
        if "movie_id" not in columns:
            conn.execute("ALTER TABLE post ADD COLUMN movie_id INTEGER")
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS post_movie_id ON post(movie_id)"
        )


if __name__ == "__main__":
    init_db()
    print(f"Initialized database at {DB_PATH}")
