# InstaKill — Starter Repo

Mini social-media platform. Mandatory backend: Python + FastAPI + SQLite (default) / PostgreSQL (allowed). See the full brief and grading rubric in `masterplan.md` (course root).

What the instructor provides (this starter):

- `app/main.py` — FastAPI hello-world with `GET /health`
- `app/db/database.py` — SQLite bootstrap (creates tables on startup)
- `app/domain/models.py` — `User` / `Post` schema
- `scripts/seed_db.py` — MovieLens users, movie posts, ratings, likes, and follows
- `tests/test_health.py` — test skeleton

The feed milestone exposes `GET /feed` with `chronological`, `for_you`, and
`learned` strategies; popularity is an evaluation-only baseline.
`scripts/seed_db.py` seeds MovieLens ratings, likes, and movie posts for the
offline time-split replay; install the
optional evaluation tools with `pip install -e ".[eval]"`, then run
`python scripts/evaluate.py`. The evaluator writes a user-level CSV, a
baseline/interval table, and a self-contained HTML dashboard under `reports/`.
See [the evaluation protocol](docs/evaluation-protocol.md) and
[API contract](docs/api-contract.md).

This week's additions are `GET /search`, an in-memory semantic index over posts in SQLite, and `GET /movies/search`, a semantic MovieLens search over movie titles, genres, and user tags. Retrieval and deterministic NumPy cosine ranking are separate from the HTTP, data, and model-loading boundaries.

## Running it

```bash
pip install -e .
python scripts/seed_db.py
uvicorn app.main:app --reload
# other terminal:
curl "localhost:8000/search?q=cosine%20similarity&limit=5"
curl "localhost:8000/movies/search?q=space%20adventure&limit=5"
curl "localhost:8000/feed?user_id=1&strategy=for_you&limit=10"
pytest
```

Seed and evaluate the temporal replay separately:

```bash
python scripts/seed_db.py
python scripts/evaluate.py --db instakill.db --out reports/
```

At application startup, `app.main` loads the CPU `all-MiniLM-L6-v2` encoder, reads posts through `SQLitePostRepository` and MovieLens data from `data/movielens/`, then builds both in-memory indices. The first startup downloads the pretrained model if it is not cached. The MovieLens files and their use terms/citation are in `data/movielens/README.txt`. A future post-creation operation should refresh the post index by calling `SearchService.build_index()` after the database write; no post-writing endpoint is included yet.

## Milestones (see masterplan.md for full details)

W1 Repo+API → W3 CRUD+DB → W4 Feed v0 → W7 Baseline+eval plan → W9 ML+pretrained feature → W11 Profile+optimize → W13 Feature freeze+E2E → W14 Red-team+Demo Day.

At the end of each week: a demonstrable commit/tag.
