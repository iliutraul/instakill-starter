# API Contract: Search Posts

## `GET /search`

Searches the seeded post corpus using semantic similarity. The application loads the encoder and builds an in-memory index during startup.

### Query parameters

- `q` (required): a non-empty, non-whitespace query string.
- `limit` (optional): integer from 1 through 20; defaults to 10.

Example: `GET /search?q=cosine%20similarity&limit=5`

### Successful response

`200 OK`

```json
{
  "query": "cosine similarity",
  "results": [
    {
      "post_id": 3,
      "user_id": 2,
      "content": "just shipped a cosine similarity search, feels great",
      "score": 0.82
    }
  ]
}
```

Results contain no more than `limit` posts, ordered by descending cosine similarity. Equal scores are ordered by ascending `post_id`. An empty corpus returns an empty `results` list.

### Validation and error cases

- `422 Unprocessable Entity` when `q` is missing, empty, or whitespace-only.
- `422 Unprocessable Entity` when `limit` is not an integer or is outside 1 through 20.

Errors use FastAPI's standard `detail` response shape.

## `GET /feed`

Ranks available posts through the shared feed service.

### Query parameters

- `user_id` (required): positive integer user ID.
- `strategy` (optional): `chronological`, `for_you`, or `learned`; defaults to `for_you`. `popularity` is an evaluation-only baseline and is not exposed by the API.
- `limit` (optional): integer from 1 through 50; defaults to 10.

Example: `GET /feed?user_id=12&strategy=learned&limit=10`

The response contains the requested `user_id` and `strategy`, plus ranked results with `post_id`, author `user_id`, `content`, `created_at`, and strategy `score`. Posts created in the future or already liked by the requesting user are not returned. `learned` loads the repository's `like_model.npz`; if that model is missing, the request returns an explicit server error rather than silently switching strategies.

## `GET /movies/search`

Searches the MovieLens collection semantically using movie titles, genres, and user-applied tags. The application loads `data/movielens/movies.csv` and `data/movielens/tags.csv`, builds an in-memory index during startup, and uses the same CPU sentence encoder as post search.

### Query parameters

- `q` (required): a non-empty, non-whitespace query string.
- `limit` (optional): integer from 1 through 20; defaults to 10.

Example: `GET /movies/search?q=space%20adventure&limit=5`

### Successful response

`200 OK`

```json
{
  "query": "space adventure",
  "results": [
    {
      "movie_id": 1,
      "title": "Toy Story (1995)",
      "genres": ["Adventure", "Animation", "Children", "Comedy", "Fantasy"],
      "tags": ["pixar"],
      "score": 0.82
    }
  ]
}
```

Results contain no more than `limit` movies, ordered by descending cosine similarity. Equal scores are ordered by ascending `movie_id`. An empty movie collection returns an empty `results` list. Missing, empty, or whitespace-only queries and limits outside 1 through 20 return `422` with FastAPI's standard `detail` response shape.