"""Shared feed-ranking service used by HTTP and offline evaluation."""

import sqlite3
from collections.abc import Callable
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import numpy as np

from app.db.database import get_connection

FeedStrategy = Literal["chronological", "for_you", "learned"]
EvaluationScorer = Callable[[np.ndarray], np.ndarray]
MODEL_PATH = Path(__file__).resolve().parents[2] / "like_model.npz"
STRATEGIES: tuple[FeedStrategy, ...] = (
    "chronological",
    "for_you",
    "learned",
)


@dataclass(frozen=True)
class FeedItem:
    post_id: int
    user_id: int
    content: str
    created_at: str
    score: float


def _utc_iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds")


def _features(
    posts: list[dict[str, object]],
    item_stats: dict[int, tuple[int, float]],
    user_ratings: list[dict[str, object]],
    now: datetime,
) -> np.ndarray:
    user_item_ids = {int(row["post_id"]) for row in user_ratings}
    user_mean = (
        float(np.mean([float(row["value"]) for row in user_ratings]))
        if user_ratings
        else 3.5
    )
    genres_by_post = {
        int(post["id"]): {genre for genre in str(post["genres"]).split("|") if genre}
        for post in posts
    }
    user_item_genres = [
        {genre for genre in str(row["genres"]).split("|") if genre}
        for row in user_ratings
    ]

    values = []
    for post in posts:
        post_id = int(post["id"])
        created_at = datetime.fromisoformat(
            str(post["created_at"]).replace("Z", "+00:00")
        )
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        age_seconds = (now - created_at.astimezone(timezone.utc)).total_seconds()
        freshness = 1.0 - min(
            1.0, max(0.0, age_seconds / (365.25 * 24 * 3600 * 6))
        )
        item_count, item_mean = item_stats.get(post_id, (0, 3.5))
        popularity = item_count / 500.0
        genres = genres_by_post[post_id]
        shared = sum(bool(genres & prior_genres) for prior_genres in user_item_genres)
        genre_affinity = 3.5 + 0.3 * shared / max(1, len(user_item_ids))
        values.append(
            [
                freshness,
                popularity,
                (user_mean - 3.5) / 1.5,
                (item_mean - 3.5) / 1.5,
                (genre_affinity - 3.5) / 1.5,
                float(post_id not in user_item_ids),
            ]
        )
    return np.asarray(values, dtype=np.float64)


def _learned_scores(features: np.ndarray) -> np.ndarray:
    if not MODEL_PATH.is_file():
        raise FileNotFoundError(f"learned feed model not found: {MODEL_PATH}")
    with np.load(MODEL_PATH) as model:
        weights = model["W1"]
        bias = model["b1"]
        output_weights = model["W2"]
        output_bias = float(model["b2"].reshape(-1)[0])
        means = model["Xmean"]
        scales = model["Xstd"]
    standardized = (features - means) / scales
    hidden = np.maximum(standardized @ weights + bias, 0)
    logits = hidden @ output_weights + output_bias
    return 1.0 / (1.0 + np.exp(-np.clip(logits, -40, 40)))


def rank_feed(
    user_id: int,
    strategy: str,
    limit: int = 10,
    now: datetime | None = None,
    connection: sqlite3.Connection | None = None,
    scorer: EvaluationScorer | None = None,
) -> list[FeedItem]:
    """Rank available, not-yet-liked posts as of ``now``."""
    if strategy not in STRATEGIES and not (
        strategy == "popularity" and scorer is not None
    ):
        raise ValueError(f"unsupported feed strategy: {strategy}")
    if limit < 1:
        raise ValueError("limit must be at least 1")
    cutoff = now or datetime.now(timezone.utc)
    cutoff_text = _utc_iso(cutoff)

    owns_connection = connection is None
    conn = connection if connection is not None else get_connection()
    try:
        posts = [
            dict(row)
            for row in conn.execute(
                """
                SELECT p.id, p.user_id, p.content, p.created_at, p.genres
                FROM post AS p
                WHERE p.created_at < ?
                  AND NOT EXISTS (
                      SELECT 1 FROM post_like AS l
                      WHERE l.user_id = ? AND l.post_id = p.id AND l.created_at < ?
                  )
                ORDER BY p.id
                """,
                (cutoff_text, user_id, cutoff_text),
            ).fetchall()
        ]
        if not posts:
            return []

        item_stats = {
            int(row["post_id"]): (int(row["rating_count"]), float(row["rating_mean"]))
            for row in conn.execute(
                """
                SELECT post_id, COUNT(*) AS rating_count, AVG(value) AS rating_mean
                FROM rating WHERE created_at < ? GROUP BY post_id
                """,
                (cutoff_text,),
            ).fetchall()
        }
        user_ratings = [
            dict(row)
            for row in conn.execute(
                """
                SELECT r.post_id, r.value, p.genres
                FROM rating AS r JOIN post AS p ON p.id = r.post_id
                WHERE r.user_id = ? AND r.created_at < ?
                """,
                (user_id, cutoff_text),
            ).fetchall()
        ]
        features = _features(posts, item_stats, user_ratings, cutoff)
        if strategy == "popularity":
            if scorer is None:
                raise ValueError("popularity is available only through evaluation")
            scores = scorer(features)
        elif strategy == "chronological":
            scores = features[:, 0]
        elif strategy == "for_you":
            scores = (
                0.40 * features[:, 4]
                + 0.35 * features[:, 0]
                + 0.25 * features[:, 1]
            )
        else:
            scores = _learned_scores(features)
        scores = np.asarray(scores, dtype=np.float64)
        if scores.shape != (len(posts),) or not np.isfinite(scores).all():
            raise ValueError("feed scorer must return one finite score per post")

        ranked = sorted(
            zip(posts, scores.tolist()),
            key=lambda item: (-float(item[1]), int(item[0]["id"])),
        )[:limit]
        return [
            FeedItem(
                post_id=int(post["id"]),
                user_id=int(post["user_id"]),
                content=str(post["content"]),
                created_at=str(post["created_at"]),
                score=float(score),
            )
            for post, score in ranked
        ]
    finally:
        if owns_connection:
            conn.close()
