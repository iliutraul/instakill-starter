"""SQLite-backed read boundary for searchable posts."""

from contextlib import closing

from app.db.database import get_connection
from app.domain.models import Post


class SQLitePostRepository:
    def list_posts(self) -> list[Post]:
        with closing(get_connection()) as connection:
            rows = connection.execute(
                "SELECT id, user_id, content, created_at FROM post ORDER BY id"
            ).fetchall()
        return [Post.model_validate(dict(row)) for row in rows]