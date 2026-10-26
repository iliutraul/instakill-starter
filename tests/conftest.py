import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.domain.models import Post
from app.main import create_app
from app.search.service import SearchService


class InMemoryPostRepository:
    def list_posts(self) -> list[Post]:
        return [
            Post(id=10, user_id=1, content="first matching post"),
            Post(id=2, user_id=2, content="second matching post"),
            Post(id=3, user_id=3, content="different direction"),
        ]


class FixedEncoder:
    def encode_documents(self, texts: list[str]) -> np.ndarray:
        return np.array([[1.0, 0.0], [1.0, 0.0], [0.0, 1.0]])

    def encode_query(self, text: str) -> np.ndarray:
        return np.array([1.0, 0.0])


@pytest.fixture
def client():
    search_service = SearchService(InMemoryPostRepository(), FixedEncoder())
    app = create_app(
        search_service_factory=lambda: search_service,
        database_initializer=lambda: None,
    )
    with TestClient(app) as test_client:
        yield test_client