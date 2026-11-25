from contextlib import asynccontextmanager
from collections.abc import Callable

from fastapi import FastAPI

from app.api.feed import router as feed_router
from app.api.movies import router as movies_router
from app.api.search import router as search_router
from app.db.database import init_db
from app.search.encoder import get_sentence_transformer_encoder
from app.search.movie_repository import MovieLensMovieRepository
from app.search.movie_service import MovieSearchService
from app.search.repository import SQLitePostRepository
from app.search.service import SearchService


def build_search_service() -> SearchService:
    return SearchService(SQLitePostRepository(), get_sentence_transformer_encoder())


def build_movie_search_service() -> MovieSearchService:
    return MovieSearchService(
        MovieLensMovieRepository(),
        get_sentence_transformer_encoder(),
    )


def create_app(
    search_service_factory: Callable[[], SearchService] = build_search_service,
    database_initializer: Callable[[], None] = init_db,
    movie_search_service_factory: Callable[
        [], MovieSearchService
    ] = build_movie_search_service,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        database_initializer()
        search_service = search_service_factory()
        search_service.build_index()
        app.state.search_service = search_service
        movie_search_service = movie_search_service_factory()
        movie_search_service.build_index()
        app.state.movie_search_service = movie_search_service
        yield

    app = FastAPI(title="InstaKill", lifespan=lifespan)
    app.include_router(feed_router)
    app.include_router(search_router)
    app.include_router(movies_router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
