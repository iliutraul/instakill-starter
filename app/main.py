from contextlib import asynccontextmanager
from collections.abc import Callable

from fastapi import FastAPI

from app.api.search import router as search_router
from app.db.database import init_db
from app.search.encoder import SentenceTransformerEncoder
from app.search.repository import SQLitePostRepository
from app.search.service import SearchService


def build_search_service() -> SearchService:
    return SearchService(SQLitePostRepository(), SentenceTransformerEncoder())


def create_app(
    search_service_factory: Callable[[], SearchService] = build_search_service,
    database_initializer: Callable[[], None] = init_db,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        database_initializer()
        search_service = search_service_factory()
        search_service.build_index()
        app.state.search_service = search_service
        yield

    app = FastAPI(title="InstaKill", lifespan=lifespan)
    app.include_router(search_router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
