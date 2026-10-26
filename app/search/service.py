"""Application orchestration for semantic post search."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from app.domain.models import Post
from app.search.retrieval import cosine_top_k


class PostReader(Protocol):
    def list_posts(self) -> list[Post]: ...


class TextEncoder(Protocol):
    def encode_documents(self, texts: Sequence[str]) -> NDArray[np.floating]: ...

    def encode_query(self, text: str) -> NDArray[np.floating]: ...


@dataclass(frozen=True)
class SearchResult:
    post_id: int
    user_id: int
    content: str
    score: float


class SearchService:
    def __init__(self, posts: PostReader, encoder: TextEncoder):
        self._posts = posts
        self._encoder = encoder
        self._indexed_posts: list[Post] = []
        self._post_ids: list[int] = []
        self._vectors: NDArray[np.floating] = np.empty((0, 0), dtype=np.float32)

    def build_index(self) -> None:
        posts = self._posts.list_posts()
        post_ids: list[int] = []
        for post in posts:
            if post.id is None:
                raise ValueError("indexed posts must have a database ID")
            post_ids.append(post.id)

        vectors = (
            self._encoder.encode_documents([post.content for post in posts])
            if posts
            else np.empty((0, 0), dtype=np.float32)
        )
        if vectors.ndim != 2 or vectors.shape[0] != len(posts):
            raise ValueError("document embeddings must contain one vector per post")

        self._indexed_posts = posts
        self._post_ids = post_ids
        self._vectors = vectors

    def search(self, query: str, limit: int) -> list[SearchResult]:
        if not self._indexed_posts:
            return []

        query_vector = self._encoder.encode_query(query)
        hits = cosine_top_k(query_vector, self._vectors, self._post_ids, limit)
        posts_by_id = {post.id: post for post in self._indexed_posts}
        return [
            SearchResult(
                post_id=hit.post_id,
                user_id=posts_by_id[hit.post_id].user_id,
                content=posts_by_id[hit.post_id].content,
                score=hit.score,
            )
            for hit in hits
        ]