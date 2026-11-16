import json
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import create_async_engine

from backend.app.api.v1.api import api_router
from backend.app.core.config import settings
from backend.app.core.database import Base, async_session_factory, engine
from backend.app.core.logging import logger
from backend.app.models.encuesta import Encuesta
from backend.app.repositories.encuesta_repo import EncuestaRepository
from backend.app.schemas.encuesta import EncuestaCreate
from backend.app.schemas.problem import ProblemDetailOut


async def seed_default_pdul_survey() -> None:
    """Precarga el esquema oficial del Cuestionario PDUL con el slug canónico y fallback UUID."""
    schema_path = Path(settings.DEFAULT_PDUL_SCHEMA_PATH)
    if not schema_path.is_absolute():
        # Resolver relativo a la raíz del repositorio
        root_dir = Path(__file__).resolve().parent.parent.parent
        schema_path = root_dir / settings.DEFAULT_PDUL_SCHEMA_PATH

    if not schema_path.exists():
        logger.warning(
            "default_pdul_schema_not_found",
            extra={"path": str(schema_path)},
        )
        return

    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            esquema = json.load(f)

        canonical_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
        canonical_slug = "cuestionario-od-maturin"
        legacy_slug = "pdul_origen_destino"

        async with async_session_factory() as session:
            repo = EncuestaRepository(session)
            existing = await repo.get_by_id(canonical_id)
            if not existing:
                existing_by_slug = await repo.get_by_slug(canonical_slug)
                if existing_by_slug:
                    existing = existing_by_slug

            if not existing:
                encuesta_canonical = Encuesta(
                    id=canonical_id,
                    titulo="Encuesta Origen-Destino Maturín (PDUL)",
                    slug=canonical_slug,
                    tipo_instrumento="encuesta_od_pdul",
                    esquema_formio=esquema,
                    activa=True,
                )
                session.add(encuesta_canonical)
                await session.commit()
                logger.info(
                    "default_pdul_survey_seeded",
                    extra={"id": str(canonical_id), "slug": canonical_slug, "titulo": encuesta_canonical.titulo},
                )

            # Asegurar que el slug legacy también esté disponible si no se resuelve por alias
            legacy_existing = await repo.get_by_slug(legacy_slug)
            if not legacy_existing:
                encuesta_legacy = Encuesta(
                    titulo="Encuesta Origen-Destino Maturín (PDUL Legacy)",
                    slug=legacy_slug,
                    tipo_instrumento="encuesta_od_pdul",
                    esquema_formio=esquema,
                    activa=True,
                )
                session.add(encuesta_legacy)
                await session.commit()
    except Exception as exc:
        logger.warning(
            "default_pdul_seeding_skipped",
            extra={"error": str(exc)},
        )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup: intentar conectar a PostgreSQL; si falla en desarrollo local, realizar fallback automático a SQLite
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await seed_default_pdul_survey()
    except Exception as e:
        logger.warning(
            "postgres_unavailable_falling_back_to_sqlite",
            extra={"error": str(e)},
        )
        try:
            fallback_engine = create_async_engine(
                "sqlite+aiosqlite:///pdul_dev.db",
                echo=False,
                future=True,
            )
            async with fallback_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            async_session_factory.configure(bind=fallback_engine)
            await seed_default_pdul_survey()
        except Exception as exc_fallback:
            logger.error(
                "database_initialization_failed",
                extra={"error": str(exc_fallback)},
            )
    yield
    # Shutdown
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

    # Configuración de CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Manejadores de excepción con formato estándar RFC 7807
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = []
        first_field = None
        for err in exc.errors():
            loc = err.get("loc", [])
            field_name = str(loc[-1]) if loc else None
            if first_field is None and field_name and field_name not in ("body", "data"):
                first_field = field_name
            errors.append(
                {
                    "loc": [str(x) for x in loc],
                    "msg": err.get("msg"),
                    "type": err.get("type"),
                }
            )

        problem = ProblemDetailOut(
            code="VALIDATION_ERROR",
            title="Error de validación de datos",
            status=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Los datos enviados no superaron las validaciones requeridas.",
            field=first_field,
            errors=errors,
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=problem.model_dump(),
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        if isinstance(exc.detail, dict) and "code" in exc.detail:
            # Ya viene estructurado como RFC 7807
            return JSONResponse(status_code=exc.status_code, content=exc.detail)

        code_map = {
            400: "BAD_REQUEST",
            404: "NOT_FOUND",
            409: "CONFLICT",
            422: "UNPROCESSABLE_ENTITY",
            500: "INTERNAL_ERROR",
        }
        problem = ProblemDetailOut(
            code=code_map.get(exc.status_code, "HTTP_ERROR"),
            title="Error en la solicitud",
            status=exc.status_code,
            detail=str(exc.detail),
        )
        return JSONResponse(status_code=exc.status_code, content=problem.model_dump())

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.error("unhandled_server_exception", exc_info=exc)
        problem = ProblemDetailOut(
            code="INTERNAL_SERVER_ERROR",
            title="Error interno del servidor",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error inesperado al procesar la solicitud en el servidor.",
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=problem.model_dump(),
        )

    # Endpoints de estado y salud
    @app.get("/health", tags=["Salud"])
    @app.get(f"{settings.API_V1_STR}/health", tags=["Salud"])
    async def health_check() -> dict:
        return {
            "status": "ok",
            "service": settings.PROJECT_NAME,
            "version": "0.1.0",
        }

    # Registro de rutas de API v1
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app


app = create_app()
