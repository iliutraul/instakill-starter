import numpy as np
import pytest

from app.search.retrieval import cosine_top_k


def test_cosine_top_k_orders_ties_by_post_id():
    hits = cosine_top_k(
        np.array([1.0, 0.0]),
        np.array([[1.0, 0.0], [1.0, 0.0], [0.0, 1.0]]),
        [10, 2, 3],
        limit=2,
    )

    assert [hit.post_id for hit in hits] == [2, 10]
    assert [hit.score for hit in hits] == [1.0, 1.0]


def test_cosine_top_k_handles_zero_vectors():
    hits = cosine_top_k(
        np.zeros(2),
        np.array([[1.0, 0.0], [0.0, 0.0]]),
        [2, 1],
        limit=5,
    )

    assert [(hit.post_id, hit.score) for hit in hits] == [(1, 0.0), (2, 0.0)]


def test_cosine_top_k_rejects_mismatched_shapes():
    with pytest.raises(ValueError, match="dimensions must match"):
        cosine_top_k(np.array([1.0]), np.array([[1.0, 0.0]]), [1], limit=1)