"""Application orchestration for semantic MovieLens search."""

from dataclasses import dataclass
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from app.domain.models import Movie
from app.search.retrieval import cosine_top_k
from app.search.service import TextEncoder


class MovieReader(Protocol):
    def list_movies(self) -> list[Movie]: ...


@dataclass(frozen=True)
class MovieSearchResult:
    movie_id: int
    title: str
    genres: list[str]
    tags: list[str]
    score: float


class MovieSearchService:
    def __init__(self, movies: MovieReader, encoder: TextEncoder):
        self._movies = movies
        self._encoder = encoder
        self._indexed_movies: list[Movie] = []
        self._movie_ids: list[int] = []
        self._vectors: NDArray[np.floating] = np.empty((0, 0), dtype=np.float32)

    def build_index(self) -> None:
        movies = self._movies.list_movies()
        movie_ids = [movie.movie_id for movie in movies]
        if len(set(movie_ids)) != len(movie_ids):
            raise ValueError("indexed movies must have unique movie IDs")

        documents = [
            " ".join(
                part
                for part in (
                    movie.title,
                    "Genres: " + ", ".join(movie.genres),
                    "Tags: " + ", ".join(movie.tags),
                )
                if part
            )
            for movie in movies
        ]
        vectors = (
            self._encoder.encode_documents(documents)
            if movies
            else np.empty((0, 0), dtype=np.float32)
        )
        if vectors.ndim != 2 or vectors.shape[0] != len(movies):
            raise ValueError("document embeddings must contain one vector per movie")

        self._indexed_movies = movies
        self._movie_ids = movie_ids
        self._vectors = vectors

    def search(self, query: str, limit: int) -> list[MovieSearchResult]:
        if not self._indexed_movies:
            return []

        query_vector = self._encoder.encode_query(query)
        hits = cosine_top_k(query_vector, self._vectors, self._movie_ids, limit)
        movies_by_id = {movie.movie_id: movie for movie in self._indexed_movies}
        return [
            MovieSearchResult(
                movie_id=hit.post_id,
                title=movies_by_id[hit.post_id].title,
                genres=movies_by_id[hit.post_id].genres,
                tags=movies_by_id[hit.post_id].tags,
                score=hit.score,
            )
            for hit in hits
        ]
