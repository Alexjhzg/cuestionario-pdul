from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import create_async_engine

from backend.app.api.error_handlers import register_exception_handlers
from backend.app.api.v1.api import api_router
from backend.app.bootstrap.seeder import seed_default_pdul_survey
from backend.app.core.config import settings
from backend.app.core.database import (
    Base,
    async_session_factory,
    engine,
    register_fallback_seed_hook,
)
from backend.app.core.logging import logger

register_fallback_seed_hook(seed_default_pdul_survey)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup: intentar conectar a PostgreSQL; si falla en desarrollo local, activar fallback SQLite
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await seed_default_pdul_survey(async_session_factory)
    except Exception as e:
        logger.warning(
            "postgres_unavailable_falling_back_to_sqlite",
            extra={"error": str(e)},
        )
        try:
            fallback_engine = create_async_engine(
                settings.SQLITE_FALLBACK_URL,
                echo=False,
                future=True,
            )
            async with fallback_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            async_session_factory.configure(bind=fallback_engine)
            await seed_default_pdul_survey(async_session_factory)
        except Exception as exc_fallback:
            logger.error(
                "database_initialization_failed",
                extra={"error": str(exc_fallback)},
            )
    yield
    try:
        await engine.dispose()
    except Exception:
        pass


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="0.1.0",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    @app.get("/health", tags=["Salud"])
    @app.get(f"{settings.API_V1_STR}/health", tags=["Salud"])
    async def health_check() -> dict:
        return {
            "status": "ok",
            "service": settings.PROJECT_NAME,
            "version": "0.1.0",
        }

    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app


app = create_app()
