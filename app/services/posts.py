"""Application operations for posts."""

from app.domain.models import Post


def build_post(user_id: int, content: str) -> Post:
    """Build a validated post model without persisting it."""
    return Post(user_id=user_id, content=content)