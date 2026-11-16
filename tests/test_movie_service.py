import numpy as np

from app.domain.models import Movie
from app.search.movie_service import MovieSearchService


class InMemoryMovieRepository:
    def list_movies(self) -> list[Movie]:
        return [
            Movie(
                movie_id=7,
                title="A Film (2020)",
                genres=["Comedy"],
                tags=["witty dialogue"],
            )
        ]


class RecordingEncoder:
    def __init__(self):
        self.documents: list[str] = []

    def encode_documents(self, texts: list[str]) -> np.ndarray:
        self.documents = list(texts)
        return np.array([[1.0, 0.0]])

    def encode_query(self, text: str) -> np.ndarray:
        return np.array([1.0, 0.0]) if text.strip() else np.zeros(2)


def test_search_index_includes_movie_title_genres_and_tags():
    encoder = RecordingEncoder()
    service = MovieSearchService(InMemoryMovieRepository(), encoder)

    service.build_index()

    assert encoder.documents == [
        "A Film (2020) Genres: Comedy Tags: witty dialogue"
    ]
