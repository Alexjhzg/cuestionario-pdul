from collections.abc import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, OperationalError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from backend.app.core.config import settings
from backend.app.core.logging import logger


class Base(DeclarativeBase):
    pass


# Configuración del motor asíncrono
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

_fallback_engine: AsyncEngine | None = None
_fallback_ready: bool = False


async def init_sqlite_fallback() -> AsyncEngine:
    global _fallback_engine, _fallback_ready
    if _fallback_engine is None:
        _fallback_engine = create_async_engine(
            "sqlite+aiosqlite:///pdul_dev.db",
            echo=False,
            future=True,
        )
    if not _fallback_ready:
        async with _fallback_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async_session_factory.configure(bind=_fallback_engine)
        _fallback_ready = True
    return _fallback_engine


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependencia FastAPI que proporciona una sesión asíncrona de base de datos con fallback resiliente."""
    global _fallback_ready
    session: AsyncSession | None = None
    try:
        session = async_session_factory()
        # Verificar conectividad temprana si aún no se ha activado el fallback
        if not _fallback_ready:
            try:
                await session.execute(text("SELECT 1"))
            except (DBAPIError, OperationalError, ConnectionError, Exception) as test_err:
                await session.close()
                session = None
                logger.warning(
                    "database_connection_failed_activating_sqlite_fallback",
                    extra={"error": str(test_err)},
                )
                await init_sqlite_fallback()
                from backend.app.main import seed_default_pdul_survey
                await seed_default_pdul_survey()
                session = async_session_factory()

        yield session
    except Exception:
        if session:
            await session.rollback()
        raise
    finally:
        if session:
            await session.close()
