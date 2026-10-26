"""Pure NumPy cosine retrieval for an in-memory post index."""

from dataclasses import dataclass
from collections.abc import Sequence

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class SimilarityHit:
    post_id: int
    score: float


def cosine_top_k(
    query_vector: NDArray[np.floating],
    corpus_vectors: NDArray[np.floating],
    post_ids: Sequence[int],
    limit: int,
) -> list[SimilarityHit]:
    """Return highest cosine scores, breaking ties by ascending post ID."""
    if limit < 1:
        raise ValueError("limit must be at least 1")

    query = np.asarray(query_vector, dtype=np.float64)
    corpus = np.asarray(corpus_vectors, dtype=np.float64)
    ids = np.asarray(post_ids, dtype=np.int64)

    if query.ndim != 1:
        raise ValueError("query_vector must be one-dimensional")
    if corpus.ndim != 2:
        raise ValueError("corpus_vectors must be two-dimensional")
    if query.shape[0] != corpus.shape[1]:
        raise ValueError("query and corpus embedding dimensions must match")
    if corpus.shape[0] != len(ids):
        raise ValueError("post_ids must match the number of corpus vectors")
    if len(np.unique(ids)) != len(ids):
        raise ValueError("post_ids must be unique")
    if not np.isfinite(query).all() or not np.isfinite(corpus).all():
        raise ValueError("vectors must contain only finite values")
    if not len(ids):
        return []

    query_norm = np.linalg.norm(query)
    corpus_norms = np.linalg.norm(corpus, axis=1)
    denominators = corpus_norms * query_norm
    scores = np.zeros(len(ids), dtype=np.float64)
    nonzero = denominators > 0
    scores[nonzero] = (corpus[nonzero] @ query) / denominators[nonzero]
    np.clip(scores, -1.0, 1.0, out=scores)

    ranked_indices = np.lexsort((ids, -scores))[:limit]
    return [
        SimilarityHit(post_id=int(ids[index]), score=float(scores[index]))
        for index in ranked_indices
    ]