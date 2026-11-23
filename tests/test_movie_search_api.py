def test_movie_search_returns_ranked_movie_details_and_original_query(client):
    response = client.get(
        "/movies/search",
        params={"q": "  funny space adventure  ", "limit": 2},
    )

    assert response.status_code == 200
    assert response.json() == {
        "query": "  funny space adventure  ",
        "results": [
            {
                "movie_id": 2,
                "title": "Second Movie (2001)",
                "genres": ["Comedy"],
                "tags": ["funny"],
                "score": 1.0,
            },
            {
                "movie_id": 10,
                "title": "First Movie (2000)",
                "genres": ["Drama"],
                "tags": ["character study"],
                "score": 1.0,
            },
        ],
    }


def test_movie_search_rejects_missing_or_blank_query(client):
    assert client.get("/movies/search").status_code == 422
    assert client.get("/movies/search", params={"q": ""}).status_code == 422

    response = client.get("/movies/search", params={"q": "   "})

    assert response.status_code == 422
    assert response.json()["detail"] == "q must not be blank"


def test_movie_search_rejects_limits_outside_range(client):
    for limit in (0, 21, "not-an-integer"):
        response = client.get(
            "/movies/search",
            params={"q": "funny movies", "limit": limit},
        )
        assert response.status_code == 422
