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