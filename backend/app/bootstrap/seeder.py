import json
from pathlib import Path
from typing import Any, Callable, Optional
import uuid

from sqlalchemy import func, select

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from backend.app.models.comunidad import ComunidadCatalogo
from backend.app.schemas.encuesta import EncuestaCreate


def _resolve_root_dir() -> Path:
    return Path(__file__).resolve().parent.parent.parent.parent


def _resolve_schema_path() -> Path:
    schema_path = Path(settings.DEFAULT_PDUL_SCHEMA_PATH)
    if not schema_path.is_absolute():
        schema_path = _resolve_root_dir() / settings.DEFAULT_PDUL_SCHEMA_PATH
    return schema_path


def _resolve_comunidades_catalog_path() -> Path:
    return _resolve_root_dir() / "shared" / "catalogs" / "comunidades_maturin.json"


async def seed_comunidades_catalog(session: Any) -> None:
    """Precarga las 846 comunidades del Municipio Maturín en la tabla catalogo_comunidades."""
    catalog_path = _resolve_comunidades_catalog_path()
    if not catalog_path.exists():
        return

    try:
        count = (
            await session.execute(select(func.count()).select_from(ComunidadCatalogo))
        ).scalar_one()
        if count and count > 0:
            return

        with open(catalog_path, "r", encoding="utf-8") as f:
            items = json.load(f)

        records = [
            ComunidadCatalogo(
                codigo=str(it["codigo"]),
                nombre=str(it["nombre"]),
                xpar=str(it["xpar"]),
                parroquia=str(it["parroquia"]),
                municipio_codigo=str(it.get("municipio_codigo", "1608")),
                municipio=str(it.get("municipio", "MATURIN")),
            )
            for it in items
            if it.get("codigo") and it.get("nombre")
        ]
        session.add_all(records)
        await session.commit()
        logger.info(
            "comunidades_maturin_catalog_seeded",
            extra={"total": len(records)},
        )
    except Exception as exc:
        await session.rollback()
        logger.warning(
            "comunidades_maturin_seeding_skipped",
            extra={"error": str(exc)},
        )


async def seed_default_pdul_survey(
    session_factory: Optional[Callable[[], Any]] = None,
) -> None:
    """Precarga el esquema oficial del Cuestionario PDUL y el catálogo de comunidades."""
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
            await seed_comunidades_catalog(session)
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
