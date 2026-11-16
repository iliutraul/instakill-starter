"""HTTP boundary for semantic MovieLens search."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

from app.search.movie_service import MovieSearchResult

router = APIRouter(prefix="/movies", tags=["movies"])


class MovieSearchResultResponse(BaseModel):
    movie_id: int
    title: str
    genres: list[str]
    tags: list[str]
    score: float


class MovieSearchResponse(BaseModel):
    query: str
    results: list[MovieSearchResultResponse]


@router.get("/search", response_model=MovieSearchResponse)
def search_movies(
    request: Request,
    q: Annotated[str, Query(min_length=1)],
    limit: Annotated[int, Query(ge=1, le=20)] = 10,
) -> MovieSearchResponse:
    if not q.strip():
        raise HTTPException(status_code=422, detail="q must not be blank")

    search_service = request.app.state.movie_search_service
    results: list[MovieSearchResult] = search_service.search(q.strip(), limit)
    return MovieSearchResponse(
        query=q,
        results=[
            MovieSearchResultResponse(
                movie_id=result.movie_id,
                title=result.title,
                genres=result.genres,
                tags=result.tags,
                score=result.score,
            )
            for result in results
        ],
    )
