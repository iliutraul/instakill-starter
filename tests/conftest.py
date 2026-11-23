import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.domain.models import Movie, Post
from app.main import create_app
from app.search.movie_service import MovieSearchService
from app.search.service import SearchService


class InMemoryPostRepository:
    def list_posts(self) -> list[Post]:
        return [
            Post(id=10, user_id=1, content="first matching post"),
            Post(id=2, user_id=2, content="second matching post"),
            Post(id=3, user_id=3, content="different direction"),
        ]


class InMemoryMovieRepository:
    def list_movies(self) -> list[Movie]:
        return [
            Movie(
                movie_id=10,
                title="First Movie (2000)",
                genres=["Drama"],
                tags=["character study"],
            ),
            Movie(
                movie_id=2,
                title="Second Movie (2001)",
                genres=["Comedy"],
                tags=["funny"],
            ),
            Movie(
                movie_id=3,
                title="Different Movie (2002)",
                genres=["Action"],
                tags=[],
            ),
        ]


class FixedEncoder:
    def encode_documents(self, texts: list[str]) -> np.ndarray:
        return np.array(
            [[1.0, 0.0] if index < 2 else [0.0, 1.0] for index, _ in enumerate(texts)]
        )

    def encode_query(self, text: str) -> np.ndarray:
        return np.array([1.0, 0.0]) if text.strip() else np.zeros(2)


class FixedMovieEncoder:
    def encode_documents(self, texts: list[str]) -> np.ndarray:
        return np.array(
            [[1.0, 0.0] if index < 2 else [0.0, 1.0] for index, _ in enumerate(texts)]
        )

    def encode_query(self, text: str) -> np.ndarray:
        return np.array([1.0, 0.0]) if text.strip() else np.zeros(2)


@pytest.fixture
def client():
    search_service = SearchService(InMemoryPostRepository(), FixedEncoder())
    movie_search_service = MovieSearchService(
        InMemoryMovieRepository(),
        FixedMovieEncoder(),
    )
    app = create_app(
        search_service_factory=lambda: search_service,
        database_initializer=lambda: None,
        movie_search_service_factory=lambda: movie_search_service,
    )
    with TestClient(app) as test_client:
        yield test_client