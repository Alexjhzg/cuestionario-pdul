import asyncio
import os
import sys
from logging.config import fileConfig
from pathlib import Path
from typing import Any, Optional

from alembic import context
import sqlalchemy as sa
from sqlalchemy import pool
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

# Ensure repository root is importable regardless of invocation CWD
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.core.config import Settings, settings  # noqa: E402
from backend.app.core.database import Base  # noqa: E402
import backend.app.models  # noqa: E402, F401
from backend.app.models.encuesta import GUID, UniversalJSON  # noqa: E402

config = context.config

if config.config_file_name is not None and config.attributes.get("configure_logger", True):
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata

PLACEHOLDER_URL = "driver://user:pass@localhost/dbname"
PG_ONLY_INDEXES = {
    "idx_respuestas_datos_gin",
    "idx_respuestas_encuesta_parroquia",
    "idx_respuestas_encuesta_zona_od",
}


def resolve_database_url() -> str:
    """Resolve and normalize the target async database URL."""
    x_args = context.get_x_argument(as_dictionary=True)
    raw_url: Optional[str] = x_args.get("url")

    if not raw_url:
        attr_url = config.attributes.get("sqlalchemy_url") or config.attributes.get("url")
        if isinstance(attr_url, str) and attr_url.strip():
            raw_url = attr_url

    if not raw_url:
        ini_url = config.get_main_option("sqlalchemy.url")
        if ini_url and ini_url.strip() and ini_url.strip() != PLACEHOLDER_URL:
            raw_url = ini_url

    if not raw_url:
        env_url = os.environ.get("DATABASE_URL")
        if env_url and env_url.strip():
            raw_url = env_url

    if not raw_url:
        raw_url = settings.DATABASE_URL

    normalized = Settings.assemble_database_url(raw_url)
    if normalized.startswith("sqlite://") and not normalized.startswith("sqlite+aiosqlite://"):
        normalized = normalized.replace("sqlite://", "sqlite+aiosqlite://", 1)
    return normalized


def include_object(
    object_: Any,
    name: Optional[str],
    type_: str,
    reflected: bool,
    compare_to: Any,
) -> bool:
    """Ignore PostgreSQL-only indexes managed in migrations when reflecting for autogenerate/check."""
    if type_ == "index" and reflected and name in PG_ONLY_INDEXES:
        return False
    return True


def compare_type(
    migration_context: Any,
    inspected_column: Any,
    metadata_column: Any,
    inspected_type: Any,
    metadata_type: Any,
) -> Optional[bool]:
    """Suppress false-positive type diffs for GUID and UniversalJSON TypeDecorators."""
    if isinstance(metadata_type, GUID):
        if (
            isinstance(inspected_type, postgresql.UUID)
            or isinstance(inspected_type, sa.Uuid)
            or (isinstance(inspected_type, sa.CHAR) and getattr(inspected_type, "length", None) == 36)
        ):
            return False
    if isinstance(metadata_type, UniversalJSON):
        if isinstance(inspected_type, (sa.JSON, postgresql.JSONB, postgresql.JSON)):
            return False
    return None


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (--sql)."""
    url = resolve_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=compare_type,
        include_object=include_object,
        render_as_batch=url.startswith("sqlite"),
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Configure MigrationContext and run migrations on a synchronous Connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=compare_type,
        include_object=include_object,
        render_as_batch=connection.dialect.name == "sqlite",
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an AsyncEngine from the resolved URL and execute migrations."""
    connectable = create_async_engine(
        resolve_database_url(),
        poolclass=pool.NullPool,
    )
    try:
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)
    finally:
        await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (CLI async engine or caller-supplied connection)."""
    connectable = config.attributes.get("connection")
    if connectable is not None:
        do_run_migrations(connectable)
    else:
        asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
