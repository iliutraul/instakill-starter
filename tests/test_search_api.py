def test_search_returns_original_query_and_sorted_results(client):
    response = client.get("/search", params={"q": "  cats  ", "limit": 2})

    assert response.status_code == 200
    assert response.json() == {
        "query": "  cats  ",
        "results": [
            {
                "post_id": 2,
                "user_id": 2,
                "content": "second matching post",
                "score": 1.0,
            },
            {
                "post_id": 10,
                "user_id": 1,
                "content": "first matching post",
                "score": 1.0,
            },
        ],
    }


def test_search_rejects_missing_or_blank_query(client):
    assert client.get("/search").status_code == 422
    assert client.get("/search", params={"q": ""}).status_code == 422
    response = client.get("/search", params={"q": "   "})
    assert response.status_code == 422
    assert response.json()["detail"] == "q must not be blank"


def test_search_rejects_limits_outside_range(client):
    for limit in (0, 21, "not-an-integer"):
        response = client.get("/search", params={"q": "cats", "limit": limit})
        assert response.status_code == 422


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}