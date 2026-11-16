from app.search.movie_repository import MovieLensMovieRepository


def test_repository_loads_movies_and_deduplicates_tags(tmp_path):
    (tmp_path / "movies.csv").write_text(
        'movieId,title,genres\n1,"A Movie, The (2000)",Comedy|Drama\n'
        '2,Untitled (2001),(no genres listed)\n',
        encoding="utf-8",
    )
    (tmp_path / "tags.csv").write_text(
        'userId,movieId,tag,timestamp\n'
        '1,1,"great, funny",100\n'
        '2,1,"GREAT, FUNNY",200\n'
        '3,2,hidden gem,300\n',
        encoding="utf-8",
    )

    movies = MovieLensMovieRepository(tmp_path).list_movies()

    assert [movie.model_dump() for movie in movies] == [
        {
            "movie_id": 1,
            "title": "A Movie, The (2000)",
            "genres": ["Comedy", "Drama"],
            "tags": ["great, funny"],
        },
        {
            "movie_id": 2,
            "title": "Untitled (2001)",
            "genres": [],
            "tags": ["hidden gem"],
        },
    ]
