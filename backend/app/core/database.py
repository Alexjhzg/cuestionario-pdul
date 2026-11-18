import asyncio
from collections.abc import AsyncGenerator, Awaitable, Callable
from typing import Optional
import weakref
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
_fallback_seeded: bool = False
_fallback_needs_seed: bool = False
_fallback_locks: weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, asyncio.Lock] = (
    weakref.WeakKeyDictionary()
)
_fallback_seed_hook: Optional[Callable[[], Awaitable[None]]] = None


def _get_fallback_lock() -> asyncio.Lock:
    loop = asyncio.get_running_loop()
    lock = _fallback_locks.get(loop)
    if lock is None:
        lock = asyncio.Lock()
        _fallback_locks[loop] = lock
    return lock


def register_fallback_seed_hook(hook: Optional[Callable[[], Awaitable[None]]]) -> None:
    """Registra un callback asíncrono opcional para sembrar datos tras activar SQLite fallback."""
    global _fallback_seed_hook, _fallback_seeded, _fallback_needs_seed
    _fallback_seed_hook = hook
    _fallback_seeded = False
    _fallback_needs_seed = False


async def _init_sqlite_fallback_locked() -> AsyncEngine:
    global _fallback_engine, _fallback_ready
    from backend.app.core.migrations import run_migrations_for_engine

    if _fallback_engine is None:
        _fallback_engine = create_async_engine(
            settings.SQLITE_FALLBACK_URL,
            echo=False,
            future=True,
        )
    if not _fallback_ready:
        await run_migrations_for_engine(_fallback_engine)
        async_session_factory.configure(bind=_fallback_engine)
        _fallback_ready = True
    return _fallback_engine


async def init_sqlite_fallback() -> AsyncEngine:
    async with _get_fallback_lock():
        return await _init_sqlite_fallback_locked()


async def dispose_engines() -> None:
    """Libera conexiones del motor principal y del motor fallback si fue inicializado."""
    global _fallback_engine, _fallback_ready, _fallback_seeded, _fallback_needs_seed
    try:
        await engine.dispose()
    except Exception:
        pass
    if _fallback_engine is not None:
        try:
            await _fallback_engine.dispose()
        except Exception:
            pass
        _fallback_engine = None
    async_session_factory.configure(bind=engine)
    _fallback_ready = False
    _fallback_seeded = False
    _fallback_needs_seed = False


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependencia FastAPI que proporciona una sesión asíncrona de base de datos con fallback resiliente."""
    global _fallback_ready, _fallback_seeded, _fallback_needs_seed
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
                async with _get_fallback_lock():
                    if not _fallback_ready:
                        await _init_sqlite_fallback_locked()
                        _fallback_needs_seed = _fallback_seed_hook is not None
                    if _fallback_needs_seed and not _fallback_seeded and _fallback_seed_hook is not None:
                        await _fallback_seed_hook()
                        _fallback_seeded = True
                        _fallback_needs_seed = False
                session = async_session_factory()
        elif _fallback_needs_seed or _get_fallback_lock().locked():
            async with _get_fallback_lock():
                if _fallback_needs_seed and not _fallback_seeded and _fallback_seed_hook is not None:
                    await _fallback_seed_hook()
                    _fallback_seeded = True
                    _fallback_needs_seed = False

        yield session
    except Exception:
        if session:
            await session.rollback()
        raise
    finally:
        if session:
            await session.close()
