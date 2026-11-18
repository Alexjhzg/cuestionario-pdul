import asyncio
import os
from pathlib import Path
from typing import Optional

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from backend.app.core.config import Settings, settings
from backend.app.core.logging import logger

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ALEMBIC_INI_PATH = PROJECT_ROOT / "alembic.ini"
ALEMBIC_SCRIPT_LOCATION = PROJECT_ROOT / "backend" / "alembic"


def build_alembic_config(database_url: Optional[str] = None) -> Config:
    """Build a CWD-independent Alembic Config suitable for programmatic async execution."""
    cfg = Config(str(ALEMBIC_INI_PATH)) if ALEMBIC_INI_PATH.exists() else Config()
    cfg.set_main_option("script_location", str(ALEMBIC_SCRIPT_LOCATION))
    cfg.set_main_option("prepend_sys_path", str(PROJECT_ROOT))
    cfg.attributes["configure_logger"] = False
    if database_url is not None:
        cfg.attributes["sqlalchemy_url"] = database_url
    return cfg


def _get_existing_tables(sync_conn: Connection) -> set[str]:
    return set(inspect(sync_conn).get_table_names())


def _run_alembic_stamp_head(sync_conn: Connection, cfg: Config) -> None:
    cfg.attributes["connection"] = sync_conn
    command.stamp(cfg, "head")


def _run_alembic_upgrade_head(sync_conn: Connection, cfg: Config) -> None:
    cfg.attributes["connection"] = sync_conn
    command.upgrade(cfg, "head")


async def run_migrations_for_engine(target_engine: AsyncEngine) -> None:
    """Apply Alembic migrations on an existing AsyncEngine, stamping pre-Alembic schemas first."""
    cfg = build_alembic_config()
    async with target_engine.connect() as conn:
        tables = await conn.run_sync(_get_existing_tables)
        # Clear SQLAlchemy 2.x autobegin transaction triggered by inspect()
        await conn.rollback()

        if {"encuestas", "respuestas_ciudadanas"}.issubset(tables) and "alembic_version" not in tables:
            logger.info(
                "alembic_stamping_preexisting_schema",
                extra={"tables": sorted(tables)},
            )
            await conn.run_sync(_run_alembic_stamp_head, cfg)
            if conn.in_transaction():
                await conn.commit()

        await conn.run_sync(_run_alembic_upgrade_head, cfg)
        if conn.in_transaction():
            await conn.commit()


async def run_migrations_for_url(database_url: str) -> None:
    """Create a transient AsyncEngine for database_url, run migrations, and dispose it."""
    normalized = Settings.assemble_database_url(database_url)
    if normalized.startswith("sqlite://") and not normalized.startswith("sqlite+aiosqlite://"):
        normalized = normalized.replace("sqlite://", "sqlite+aiosqlite://", 1)

    temp_engine = create_async_engine(normalized, echo=False, future=True)
    try:
        await run_migrations_for_engine(temp_engine)
    finally:
        await temp_engine.dispose()


def main() -> None:
    target_url = os.environ.get("DATABASE_URL") or settings.DATABASE_URL
    asyncio.run(run_migrations_for_url(target_url))


if __name__ == "__main__":
    main()
