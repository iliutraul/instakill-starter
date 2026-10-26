# API Contract: Create Post

**Status:** planned; this endpoint is not implemented.

## `POST /posts`

### Request

```json
{
  "user_id": 7,
  "content": "A short post"
}
```

Both fields are required. `user_id` must be an integer identifying an existing user. `content` must be a non-empty string.

### Successful response

`201 Created`

```json
{
  "id": 42,
  "user_id": 7,
  "content": "A short post",
  "created_at": "2026-10-26T12:00:00Z"
}
```

### Validation and error cases

- `422 Unprocessable Entity` when a required field is missing, has the wrong type, or `content` is empty.
- `404 Not Found` when `user_id` does not identify an existing user.

Errors use the standard FastAPI `detail` response shape. These behaviors describe the future endpoint only; no route or persistence behavior is added in this iteration.