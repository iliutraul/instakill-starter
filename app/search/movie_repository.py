"""CSV-backed read boundary for the MovieLens movie and tag data."""

import csv
from pathlib import Path

from app.domain.models import Movie


class MovieLensMovieRepository:
    def __init__(self, data_dir: Path | None = None):
        self._data_dir = (
            data_dir
            if data_dir is not None
            else Path(__file__).resolve().parents[2] / "data" / "movielens"
        )

    def list_movies(self) -> list[Movie]:
        movies_path = self._data_dir / "movies.csv"
        tags_path = self._data_dir / "tags.csv"
        movies: list[tuple[int, str, list[str]]] = []

        with movies_path.open(encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames is None or not {
                "movieId",
                "title",
                "genres",
            }.issubset(reader.fieldnames):
                raise ValueError(f"{movies_path} must contain movieId, title, genres")

            for row in reader:
                movie_id = int(row["movieId"])
                title = row["title"]
                genre_values = row["genres"]
                if title is None or genre_values is None:
                    raise ValueError(f"{movies_path} contains an incomplete movie row")
                genres = (
                    []
                    if genre_values == "(no genres listed)"
                    else genre_values.split("|")
                )
                movies.append((movie_id, title, genres))

        movie_ids = {movie_id for movie_id, _, _ in movies}
        tags_by_movie: dict[int, list[str]] = {}
        seen_tags: dict[int, set[str]] = {}
        with tags_path.open(encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames is None or not {
                "movieId",
                "tag",
            }.issubset(reader.fieldnames):
                raise ValueError(f"{tags_path} must contain movieId, tag")

            for row in reader:
                movie_id = int(row["movieId"])
                tag = row["tag"]
                if tag is None:
                    raise ValueError(f"{tags_path} contains an incomplete tag row")
                if movie_id not in movie_ids:
                    raise ValueError(
                        f"{tags_path} references unknown movie ID {movie_id}"
                    )

                normalized_tag = tag.strip()
                if not normalized_tag:
                    continue
                movie_tags = tags_by_movie.setdefault(movie_id, [])
                movie_seen_tags = seen_tags.setdefault(movie_id, set())
                if normalized_tag.casefold() not in movie_seen_tags:
                    movie_tags.append(normalized_tag)
                    movie_seen_tags.add(normalized_tag.casefold())

        return [
            Movie(
                movie_id=movie_id,
                title=title,
                genres=genres,
                tags=tags_by_movie.get(movie_id, []),
            )
            for movie_id, title, genres in movies
        ]
