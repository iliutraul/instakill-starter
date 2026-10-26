# InstaKill — Starter Repo

Mini social-media platform. Mandatory backend: Python + FastAPI + SQLite (default) / PostgreSQL (allowed). See the full brief and grading rubric in `masterplan.md` (course root).

What the instructor provides (this starter):

- `app/main.py` — FastAPI hello-world with `GET /health`
- `app/db/database.py` — SQLite bootstrap (creates tables on startup)
- `app/domain/models.py` — `User` / `Post` schema
- `scripts/seed_db.py` — 5-10 synthetic users/posts
- `tests/test_health.py` — test skeleton

This week's addition is `GET /search`, an in-memory semantic index over posts in SQLite. Retrieval and deterministic NumPy cosine ranking are separate from the HTTP, database, and model-loading boundaries.

## Running it

```bash
pip install -e .
python scripts/seed_db.py
uvicorn app.main:app --reload
# other terminal:
curl "localhost:8000/search?q=cosine%20similarity&limit=5"
pytest
```

At application startup, `app.main` loads the CPU `all-MiniLM-L6-v2` encoder, reads posts through `SQLitePostRepository`, and asks `SearchService` to build an in-memory index. The first startup downloads the pretrained model if it is not cached. A future post-creation operation should refresh the index by calling `SearchService.build_index()` after the database write; no post-writing endpoint is included yet.

## Milestones (see masterplan.md for full details)

W1 Repo+API → W3 CRUD+DB → W4 Feed v0 → W7 Baseline+eval plan → W9 ML+pretrained feature → W11 Profile+optimize → W13 Feature freeze+E2E → W14 Red-team+Demo Day.

At the end of each week: a demonstrable commit/tag.
