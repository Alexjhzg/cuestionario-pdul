import json
from pathlib import Path
from typing import Any, Callable, Optional
import uuid

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from backend.app.schemas.encuesta import EncuestaCreate


def _resolve_schema_path() -> Path:
    schema_path = Path(settings.DEFAULT_PDUL_SCHEMA_PATH)
    if not schema_path.is_absolute():
        root_dir = Path(__file__).resolve().parent.parent.parent.parent
        schema_path = root_dir / settings.DEFAULT_PDUL_SCHEMA_PATH
    return schema_path


async def seed_default_pdul_survey(
    session_factory: Optional[Callable[[], Any]] = None,
) -> None:
    """Precarga el esquema oficial del Cuestionario PDUL de forma desacoplada."""
    if session_factory is None:
        from backend.app.core.database import async_session_factory

        session_factory = async_session_factory

    schema_path = _resolve_schema_path()
    if not schema_path.exists():
        logger.warning(
            "default_pdul_schema_not_found",
            extra={"path": str(schema_path)},
        )
        return

    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            esquema = json.load(f)

        canonical_id = uuid.UUID(settings.CANONICAL_SURVEY_ID)
        canonical_slug = settings.CANONICAL_SURVEY_SLUG
        legacy_slug = settings.LEGACY_SURVEY_SLUG

        async with session_factory() as session:
            async with SqlAlchemyUnitOfWork(session) as uow:
                existing = await uow.surveys.get_by_id(canonical_id)
                if not existing:
                    existing = await uow.surveys.get_by_slug(canonical_slug)

                if not existing:
                    encuesta_canonical = await uow.surveys.create(
                        EncuestaCreate(
                            titulo="Encuesta Origen-Destino Maturín (PDUL)",
                            slug=canonical_slug,
                            tipo_instrumento="encuesta_od_pdul",
                            esquema_formio=esquema,
                            activa=True,
                        ),
                        encuesta_id=canonical_id,
                    )
                    logger.info(
                        "default_pdul_survey_seeded",
                        extra={
                            "id": str(canonical_id),
                            "slug": canonical_slug,
                            "titulo": encuesta_canonical.titulo,
                        },
                    )

                legacy_existing = await uow.surveys.get_by_slug(legacy_slug)
                if not legacy_existing:
                    await uow.surveys.create(
                        EncuestaCreate(
                            titulo="Encuesta Origen-Destino Maturín (PDUL Legacy)",
                            slug=legacy_slug,
                            tipo_instrumento="encuesta_od_pdul",
                            esquema_formio=esquema,
                            activa=True,
                        )
                    )
    except Exception as exc:
        logger.warning(
            "default_pdul_seeding_skipped",
            extra={"error": str(exc)},
        )
