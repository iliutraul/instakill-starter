"""HTTP boundary for semantic post search."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

from app.search.service import SearchResult

router = APIRouter()


class SearchResultResponse(BaseModel):
    post_id: int
    user_id: int
    content: str
    score: float


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultResponse]


@router.get("/search", response_model=SearchResponse)
def search_posts(
    request: Request,
    q: Annotated[str, Query(min_length=1)],
    limit: Annotated[int, Query(ge=1, le=20)] = 10,
) -> SearchResponse:
    if not q.strip():
        raise HTTPException(status_code=422, detail="q must not be blank")

    search_service = request.app.state.search_service
    results: list[SearchResult] = search_service.search(q.strip(), limit)
    return SearchResponse(
        query=q,
        results=[
            SearchResultResponse(
                post_id=result.post_id,
                user_id=result.user_id,
                content=result.content,
                score=result.score,
            )
            for result in results
        ],
    )