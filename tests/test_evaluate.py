from datetime import datetime, timezone

import numpy as np
import pytest

from app.api import feed as feed_api
from app.db.database import get_connection, init_db
from app.services import feed as feed_service
from scripts import evaluate as evaluation

CUTOFF = datetime(2020, 1, 2, tzinfo=timezone.utc)
CUTOFF_TEXT = "2020-01-02T00:00:00.000000+00:00"


def _fixture_database(path):
    init_db(path)
    with get_connection(path) as connection:
        connection.executemany(
            "INSERT INTO user (id, username, created_at) VALUES (?, ?, ?)",
            [
                (1, "one", "2020-01-01T00:00:00.000000+00:00"),
                (2, "two", "2020-01-01T00:00:00.000000+00:00"),
            ],
        )
        connection.executemany(
            """
            INSERT INTO post (id, user_id, content, created_at, genres)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (1, 2, "one", "2020-01-01T00:00:00.000000+00:00", "Drama"),
                (2, 2, "two", "2020-01-01T00:00:00.000000+00:00", "Drama"),
                (3, 1, "three", "2020-01-01T00:00:00.000000+00:00", "Comedy"),
                (4, 2, "four", "2020-01-01T00:00:00.000000+00:00", "Drama"),
                (5, 1, "five", "2020-01-01T00:00:00.000000+00:00", "Comedy"),
                (6, 2, "future post", CUTOFF_TEXT, "Drama"),
                (7, 1, "six", "2020-01-01T00:00:00.000000+00:00", "Action"),
            ],
        )
        ratings = [
            (1, 1, 5.0, "2020-01-01T00:00:00.000000+00:00"),
            (1, 2, 4.0, "2020-01-01T00:00:00.000000+00:00"),
            (1, 3, 4.0, "2020-01-01T00:00:00.000000+00:00"),
            (1, 4, 5.0, "2020-01-03T00:00:00.000000+00:00"),
            (2, 1, 5.0, "2020-01-01T00:00:00.000000+00:00"),
            (2, 2, 4.0, "2020-01-01T00:00:00.000000+00:00"),
            (2, 4, 4.0, "2020-01-01T00:00:00.000000+00:00"),
            (2, 5, 5.0, "2020-01-03T00:00:00.000000+00:00"),
        ]
        connection.executemany(
            "INSERT INTO rating (user_id, post_id, value, created_at) VALUES (?, ?, ?, ?)",
            ratings,
        )
        connection.executemany(
            "INSERT INTO post_like (user_id, post_id, created_at) VALUES (?, ?, ?)",
            [
                (1, 1, "2020-01-01T00:00:00.000000+00:00"),
                (1, 2, "2020-01-01T00:00:00.000000+00:00"),
                (1, 3, "2020-01-01T00:00:00.000000+00:00"),
                (1, 4, "2020-01-03T00:00:00.000000+00:00"),
                (2, 1, "2020-01-01T00:00:00.000000+00:00"),
                (2, 2, "2020-01-01T00:00:00.000000+00:00"),
                (2, 4, "2020-01-01T00:00:00.000000+00:00"),
                (2, 5, "2020-01-03T00:00:00.000000+00:00"),
                (1, 6, CUTOFF_TEXT),
            ],
        )
        connection.executemany(
            "INSERT INTO follow (follower_id, followee_id, created_at) VALUES (?, ?, ?)",
            [
                (1, 2, "2020-01-03T00:00:00.000000+00:00"),
                (2, 1, "2020-01-01T00:00:00.000000+00:00"),
            ],
        )


def test_ndcg_at_10_hand_made_rankings():
    assert evaluation.ndcg_at_10([1, 2, 3], set()) == 0.0
    assert evaluation.ndcg_at_10([1, 2, 3], {1, 2}) == 1.0
    assert evaluation.ndcg_at_10([1, 2, 3, 4], {4}) == pytest.approx(
        1 / np.log2(5)
    )


def test_snapshot_removes_everything_at_or_after_cutoff_and_rebuilds_follows(
    tmp_path,
):
    source = tmp_path / "source.sqlite"
    snapshot = tmp_path / "snapshot.sqlite"
    _fixture_database(source)

    evaluation.build_snapshot(source, snapshot, CUTOFF)

    with get_connection(snapshot) as connection:
        assert connection.execute("SELECT id FROM post WHERE id = 6").fetchone() is None
        assert connection.execute(
            "SELECT 1 FROM post_like WHERE created_at >= ?", (CUTOFF_TEXT,)
        ).fetchone() is None
        assert connection.execute(
            "SELECT 1 FROM rating WHERE created_at >= ?", (CUTOFF_TEXT,)
        ).fetchone() is None
        assert connection.execute(
            "SELECT 1 FROM follow WHERE created_at >= ?", (CUTOFF_TEXT,)
        ).fetchone() is None
        assert connection.execute(
            "SELECT 1 FROM follow WHERE follower_id = 1 AND followee_id = 2"
        ).fetchone() is not None


def test_two_runs_write_identical_results_and_markdown(tmp_path):
    database = tmp_path / "fixture.sqlite"
    _fixture_database(database)
    first, second = tmp_path / "first", tmp_path / "second"

    evaluation.run_evaluation(database, first, CUTOFF, 42)
    evaluation.run_evaluation(database, second, CUTOFF, 42)

    assert (first / "eval_results.csv").read_bytes() == (
        second / "eval_results.csv"
    ).read_bytes()
    assert (first / "baseline_table.md").read_bytes() == (
        second / "baseline_table.md"
    ).read_bytes()


def test_endpoint_and_evaluation_call_shared_feed_service(monkeypatch, tmp_path):
    calls = []

    def fake_rank_feed(
        user_id, strategy, limit=10, now=None, connection=None, scorer=None
    ):
        calls.append((user_id, strategy))
        return [
            feed_service.FeedItem(
                post_id=1,
                user_id=2,
                content="post",
                created_at="2020-01-01T00:00:00+00:00",
                score=0.5,
            )
        ]

    monkeypatch.setattr(feed_service, "rank_feed", fake_rank_feed)
    response = feed_api.get_feed(user_id=1, strategy="learned", limit=1)
    assert response.results[0].post_id == 1

    database = tmp_path / "fixture.sqlite"
    _fixture_database(database)
    rows, _ = evaluation.evaluate(database, CUTOFF, 42)

    assert len(rows) == 8
    assert len(calls) == 9
    assert calls[0] == (1, "learned")
    assert calls[1:] == [
        (user_id, strategy)
        for user_id in (1, 2)
        for strategy in evaluation.STRATEGIES
    ]
