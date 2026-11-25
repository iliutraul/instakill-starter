"""Seed SQLite with MovieLens users, movie posts, ratings, likes, and follows."""

import csv
from datetime import datetime, timezone
from pathlib import Path

from app.db.database import DB_PATH, get_connection, init_db

ROOT = Path(__file__).resolve().parents[1]
RATINGS_PATH = ROOT / "ml-latest-small" / "ml-latest-small" / "ratings.csv"
MOVIES_PATH = ROOT / "data" / "movielens" / "movies.csv"


def _iso_timestamp(unix_seconds: int) -> str:
    return datetime.fromtimestamp(unix_seconds, timezone.utc).isoformat(
        timespec="microseconds"
    )


def seed(
    ratings_path: Path = RATINGS_PATH,
    movies_path: Path = MOVIES_PATH,
    db_path: Path = DB_PATH,
) -> None:
    if not ratings_path.is_file():
        raise FileNotFoundError(f"MovieLens ratings file not found: {ratings_path}")
    if not movies_path.is_file():
        raise FileNotFoundError(f"MovieLens movies file not found: {movies_path}")

    with movies_path.open(newline="", encoding="utf-8") as file:
        movies = {
            int(row["movieId"]): (row["title"], row["genres"])
            for row in csv.DictReader(file)
        }
    with ratings_path.open(newline="", encoding="utf-8") as file:
        ratings = [
            (
                int(row["userId"]),
                int(row["movieId"]),
                float(row["rating"]),
                int(row["timestamp"]),
            )
            for row in csv.DictReader(file)
        ]
    if not ratings:
        raise ValueError(f"MovieLens ratings file is empty: {ratings_path}")

    user_first_seen: dict[int, int] = {}
    post_first_seen: dict[int, int] = {}
    for user_id, movie_id, _, timestamp in ratings:
        if movie_id not in movies:
            raise ValueError(f"MovieLens rating references unknown movie ID {movie_id}")
        user_first_seen[user_id] = min(user_first_seen.get(user_id, timestamp), timestamp)
        post_first_seen[movie_id] = min(
            post_first_seen.get(movie_id, timestamp), timestamp
        )
    source_user_ids = sorted(user_first_seen)

    init_db(db_path)
    with get_connection(db_path) as connection:
        connection.executemany(
            """
            INSERT INTO user (username, created_at) VALUES (?, ?)
            ON CONFLICT(username) DO UPDATE SET
                created_at = excluded.created_at
            """,
            [
                (f"ml-user-{user_id}", _iso_timestamp(timestamp))
                for user_id, timestamp in sorted(user_first_seen.items())
            ],
        )
        user_ids = {
            source_id: int(
                connection.execute(
                    "SELECT id FROM user WHERE username = ?",
                    (f"ml-user-{source_id}",),
                ).fetchone()["id"]
            )
            for source_id in user_first_seen
        }
        connection.executemany(
            """
            INSERT INTO post (user_id, content, created_at, genres, movie_id)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(movie_id) DO UPDATE SET
                user_id = excluded.user_id,
                content = excluded.content,
                created_at = excluded.created_at,
                genres = excluded.genres
            """,
            [
                (
                    user_ids[source_user_ids[movie_id % len(source_user_ids)]],
                    movies[movie_id][0],
                    _iso_timestamp(timestamp),
                    "" if movies[movie_id][1] == "(no genres listed)" else movies[movie_id][1],
                    movie_id,
                )
                for movie_id, timestamp in sorted(post_first_seen.items())
            ],
        )
        post_ids = {
            int(row["movie_id"]): int(row["id"])
            for row in connection.execute(
                "SELECT id, movie_id FROM post WHERE movie_id IS NOT NULL"
            )
        }
        connection.executemany(
            """
            INSERT INTO rating (user_id, post_id, value, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, post_id) DO UPDATE SET
                value = excluded.value, created_at = excluded.created_at
            """,
            [
                (
                    user_ids[user_id],
                    post_ids[movie_id],
                    value,
                    _iso_timestamp(timestamp),
                )
                for user_id, movie_id, value, timestamp in ratings
            ],
        )
        liked_rows = [
            (user_ids[user_id], post_ids[movie_id], _iso_timestamp(timestamp))
            for user_id, movie_id, value, timestamp in ratings
            if value >= 4.0
        ]
        connection.executemany(
            """
            INSERT INTO post_like (user_id, post_id, created_at) VALUES (?, ?, ?)
            ON CONFLICT(user_id, post_id) DO UPDATE SET created_at = excluded.created_at
            """,
            liked_rows,
        )

        authors = {
            int(row["id"]): int(row["user_id"])
            for row in connection.execute("SELECT id, user_id FROM post")
        }
        first_follow: dict[tuple[int, int], str] = {}
        for user_id, movie_id, created_at in liked_rows:
            followee_id = authors[movie_id]
            if user_id != followee_id:
                key = (user_id, followee_id)
                first_follow[key] = min(first_follow.get(key, created_at), created_at)
        connection.executemany(
            """
            INSERT INTO follow (follower_id, followee_id, created_at)
            VALUES (?, ?, ?)
            ON CONFLICT(follower_id, followee_id) DO UPDATE SET
                created_at = excluded.created_at
            """,
            [
                (follower_id, followee_id, created_at)
                for (follower_id, followee_id), created_at in sorted(first_follow.items())
            ],
        )

    print(
        f"Seeded {len(user_first_seen)} users, {len(post_first_seen)} movie posts, "
        f"{len(ratings)} ratings, and {len(liked_rows)} likes into {db_path}."
    )


if __name__ == "__main__":
    seed()
