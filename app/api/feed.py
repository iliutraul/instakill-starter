"""HTTP boundary for the shared feed-ranking service."""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.services import feed as feed_service
from app.services.feed import FeedStrategy

router = APIRouter()


class FeedItemResponse(BaseModel):
    post_id: int
    user_id: int
    content: str
    created_at: str
    score: float


class FeedResponse(BaseModel):
    user_id: int
    strategy: FeedStrategy
    results: list[FeedItemResponse]


@router.get("/feed", response_model=FeedResponse)
def get_feed(
    user_id: Annotated[int, Query(ge=1)],
    strategy: FeedStrategy = "for_you",
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
) -> FeedResponse:
    items = feed_service.rank_feed(
        user_id=user_id,
        strategy=strategy,
        limit=limit,
        now=datetime.now(timezone.utc),
    )
    return FeedResponse(
        user_id=user_id,
        strategy=strategy,
        results=[
            FeedItemResponse.model_validate(item, from_attributes=True)
            for item in items
        ],
    )
