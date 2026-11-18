import asyncio
import contextlib
import io
import os
import sqlite3
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import create_async_engine

from backend.app.bootstrap.seeder import seed_default_pdul_survey
from backend.app.core import database as db_module
from backend.app.core.config import Settings, settings
from backend.app.core.database import Base
from backend.app.core.migrations import (
    ALEMBIC_INI_PATH,
    ALEMBIC_SCRIPT_LOCATION,
    PROJECT_ROOT,
    run_migrations_for_engine,
    run_migrations_for_url,
)
from backend.app.main import create_app


def _make_cli_style_config(db_url: str) -> Config:
    cfg = Config(str(ALEMBIC_INI_PATH))
    cfg.set_main_option("script_location", str(ALEMBIC_SCRIPT_LOCATION))
    cfg.attributes["configure_logger"] = False
    cfg.attributes["sqlalchemy_url"] = db_url
    return cfg


def test_clean_sqlite_upgrade_check_downgrade_roundtrip(tmp_path: Path) -> None:
    db_path = tmp_path / "clean_alembic.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"
    cfg = _make_cli_style_config(db_url)

    command.upgrade(cfg, "head")
    command.check(cfg)

    with sqlite3.connect(db_path) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        assert {"alembic_version", "encuestas", "respuestas_ciudadanas"}.issubset(tables)

        version = conn.execute("SELECT version_num FROM alembic_version").fetchone()
        assert version == ("0001_initial_schema",)

        indexes = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index'"
            ).fetchall()
        }
        assert {
            "ix_encuestas_slug",
            "ix_respuestas_ciudadanas_client_submission_id",
            "ix_respuestas_ciudadanas_encuesta_id",
            "ix_respuestas_ciudadanas_parroquia",
            "ix_respuestas_ciudadanas_zona_od",
        }.issubset(indexes)
        assert "idx_respuestas_datos_gin" not in indexes
        assert "idx_respuestas_encuesta_parroquia" not in indexes
        assert "idx_respuestas_encuesta_zona_od" not in indexes

    command.downgrade(cfg, "base")
    with sqlite3.connect(db_path) as conn:
        tables_after_downgrade = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        assert "encuestas" not in tables_after_downgrade
        assert "respuestas_ciudadanas" not in tables_after_downgrade

    command.upgrade(cfg, "head")
    with sqlite3.connect(db_path) as conn:
        version_reupgraded = conn.execute(
            "SELECT version_num FROM alembic_version"
        ).fetchone()
        assert version_reupgraded == ("0001_initial_schema",)


def test_offline_postgresql_sql_ddl_generation() -> None:
    up_buf = io.StringIO()
    up_cfg = _make_cli_style_config(
        "postgres://u:p@localhost:5432/pdul_db?sslmode=require",
    )
    with contextlib.redirect_stdout(up_buf):
        command.upgrade(up_cfg, "head", sql=True)
    up_sql = up_buf.getvalue()

    assert "CREATE TABLE encuestas" in up_sql
    assert "id UUID NOT NULL" in up_sql
    assert "esquema_formio JSONB NOT NULL" in up_sql
    assert "id BIGSERIAL NOT NULL" in up_sql
    assert "datos JSONB NOT NULL" in up_sql
    assert "TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL" in up_sql
    assert "CONSTRAINT uq_voto_ciudadano UNIQUE (encuesta_id, cedula)" in up_sql
    assert (
        "CREATE INDEX idx_respuestas_datos_gin ON respuestas_ciudadanas USING gin (datos jsonb_path_ops)"
        in up_sql
    )
    assert (
        "CREATE INDEX idx_respuestas_encuesta_parroquia ON respuestas_ciudadanas (encuesta_id, parroquia)"
        in up_sql
    )
    assert (
        "CREATE INDEX idx_respuestas_encuesta_zona_od ON respuestas_ciudadanas (encuesta_id, zona_od)"
        in up_sql
    )

    down_buf = io.StringIO()
    down_cfg = _make_cli_style_config(
        "postgresql+asyncpg://u:p@localhost:5432/pdul_db",
    )
    with contextlib.redirect_stdout(down_buf):
        command.downgrade(down_cfg, "head:base", sql=True)
    down_sql = down_buf.getvalue()

    assert "DROP INDEX idx_respuestas_encuesta_zona_od" in down_sql
    assert "DROP INDEX idx_respuestas_encuesta_parroquia" in down_sql
    assert "DROP INDEX idx_respuestas_datos_gin" in down_sql
    assert "DROP TABLE respuestas_ciudadanas" in down_sql
    assert "DROP TABLE encuestas" in down_sql


async def test_preexisting_db_is_stamped_and_preserves_rows(tmp_path: Path) -> None:
    db_path = tmp_path / "preexisting.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"

    # Simulate legacy DB created via Base.metadata.create_all before Alembic existed
    legacy_engine = create_async_engine(db_url, echo=False, future=True)
    encuesta_id = str(uuid.uuid4())
    try:
        async with legacy_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await conn.execute(
                text(
                    "INSERT INTO encuestas (id, titulo, slug, tipo_instrumento, esquema_formio, activa) "
                    "VALUES (:id, :titulo, :slug, :tipo, :esquema, :activa)"
                ),
                {
                    "id": encuesta_id,
                    "titulo": "Encuesta Preexistente",
                    "slug": "encuesta-preexistente",
                    "tipo": "encuesta_od_pdul",
                    "esquema": '{"components": []}',
                    "activa": True,
                },
            )
            await conn.execute(
                text(
                    "INSERT INTO respuestas_ciudadanas (encuesta_id, cedula, parroquia, zona_od, datos) "
                    "VALUES (:eid, :cedula, :parroquia, :zona, :datos)"
                ),
                {
                    "eid": encuesta_id,
                    "cedula": "12345678",
                    "parroquia": "Alto de los Godos",
                    "zona": "Z01",
                    "datos": '{"parroquia": "Alto de los Godos"}',
                },
            )
    finally:
        await legacy_engine.dispose()

    await run_migrations_for_url(db_url)
    # Idempotent second run
    await run_migrations_for_url(db_url)

    with sqlite3.connect(db_path) as conn:
        version = conn.execute("SELECT version_num FROM alembic_version").fetchone()
        assert version == ("0001_initial_schema",)
        enc_count = conn.execute("SELECT COUNT(*) FROM encuestas").fetchone()[0]
        resp_count = conn.execute(
            "SELECT COUNT(*) FROM respuestas_ciudadanas"
        ).fetchone()[0]
        assert enc_count == 1
        assert resp_count == 1


async def test_in_memory_sqlite_migrations_inside_running_event_loop() -> None:
    mem_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False, future=True)
    try:
        await run_migrations_for_engine(mem_engine)
        async with mem_engine.connect() as conn:
            tables = await conn.run_sync(
                lambda sync_conn: set(inspect(sync_conn).get_table_names())
            )
            assert {"alembic_version", "encuestas", "respuestas_ciudadanas"}.issubset(
                tables
            )
    finally:
        await mem_engine.dispose()


async def test_lifespan_sqlite_fallback_runs_alembic_and_seeds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fallback_db = tmp_path / "fallback_lifespan.db"
    fallback_url = f"sqlite+aiosqlite:///{fallback_db}"
    unreachable_pg = create_async_engine(
        "postgresql+asyncpg://postgres:postgres@127.0.0.1:59999/nope",
        echo=False,
        future=True,
    )

    orig_engine = db_module.engine
    await db_module.dispose_engines()
    monkeypatch.setattr(db_module, "engine", unreachable_pg)
    monkeypatch.setattr("backend.app.main.engine", unreachable_pg)
    monkeypatch.setattr(settings, "SQLITE_FALLBACK_URL", fallback_url)

    app = create_app()
    try:
        async with app.router.lifespan_context(app):
            assert db_module._fallback_ready is True
            assert db_module._fallback_engine is not None

            with sqlite3.connect(fallback_db) as conn:
                tables = {
                    row[0]
                    for row in conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    ).fetchall()
                }
                assert {
                    "alembic_version",
                    "encuestas",
                    "respuestas_ciudadanas",
                }.issubset(tables)
                version = conn.execute(
                    "SELECT version_num FROM alembic_version"
                ).fetchone()
                assert version == ("0001_initial_schema",)
                seeded_count = conn.execute(
                    "SELECT COUNT(*) FROM encuestas"
                ).fetchone()[0]
                assert seeded_count >= 1
    finally:
        monkeypatch.undo()
        await unreachable_pg.dispose()
        await db_module.dispose_engines()
        assert db_module.async_session_factory.kw.get("bind") is orig_engine


def test_settings_database_url_normalization_and_bare_sqlite_import(tmp_path: Path) -> None:
    db_file = tmp_path / "bare_primary.db"
    fb_file = tmp_path / "bare_fallback.db"
    cfg = Settings(
        DATABASE_URL=f"sqlite:///{db_file}",
        SQLITE_FALLBACK_URL=f"sqlite:///{fb_file}",
    )
    assert cfg.DATABASE_URL == f"sqlite+aiosqlite:///{db_file}"
    assert cfg.SQLITE_FALLBACK_URL == f"sqlite+aiosqlite:///{fb_file}"

    assert (
        Settings.assemble_database_url(
            "postgresql://u:p@h:5432/db?sslmode=prefer&connect_timeout=5"
        )
        == "postgresql+asyncpg://u:p@h:5432/db?connect_timeout=5"
    )
    assert (
        Settings.assemble_database_url(
            "postgresql://u:p@h:5432/db?connect_timeout=5&sslmode=disable"
        )
        == "postgresql+asyncpg://u:p@h:5432/db?connect_timeout=5"
    )
    assert (
        Settings.assemble_database_url("postgresql://u:p@h:5432/db?sslmode=prefer")
        == "postgresql+asyncpg://u:p@h:5432/db"
    )
    assert (
        Settings.assemble_database_url(
            "postgres://u:p%40ss%25w0rd@h:5432/db?sslmode=require"
        )
        == "postgresql+asyncpg://u:p%40ss%25w0rd@h:5432/db?ssl=require"
    )
    assert Settings.assemble_database_url("sqlite:///:memory:") == "sqlite+aiosqlite:///:memory:"
    assert (
        Settings.assemble_database_url("sqlite+aiosqlite:///./pdul_dev.db")
        == "sqlite+aiosqlite:///./pdul_dev.db"
    )

    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{db_file}"
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    proc = subprocess.run(
        [sys.executable, "-m", "backend.app.core.migrations"],
        cwd=str(tmp_path),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    with sqlite3.connect(db_file) as conn:
        version = conn.execute("SELECT version_num FROM alembic_version").fetchone()
        assert version == ("0001_initial_schema",)


async def test_concurrent_get_db_fallback_seeding_waits_for_seed_completion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fallback_db = tmp_path / "concurrent_get_db.db"
    fallback_url = f"sqlite+aiosqlite:///{fallback_db}"
    unreachable_pg = create_async_engine(
        "postgresql+asyncpg://postgres:postgres@127.0.0.1:59999/nope",
        echo=False,
        future=True,
    )
    orig_hook = db_module._fallback_seed_hook

    await db_module.dispose_engines()
    monkeypatch.setattr(db_module, "engine", unreachable_pg)
    monkeypatch.setattr(settings, "SQLITE_FALLBACK_URL", fallback_url)
    db_module.register_fallback_seed_hook(seed_default_pdul_survey)

    async def hit() -> int:
        gen = db_module.get_db()
        session = await anext(gen)
        count = (
            await session.execute(text("SELECT COUNT(*) FROM encuestas"))
        ).scalar_one()
        try:
            await anext(gen)
        except StopAsyncIteration:
            pass
        return int(count)

    try:
        counts = await asyncio.gather(*[hit() for _ in range(5)])
        assert counts == [1, 1, 1, 1, 1]
        assert db_module._fallback_seeded is True
    finally:
        monkeypatch.undo()
        await unreachable_pg.dispose()
        await db_module.dispose_engines()
        db_module.register_fallback_seed_hook(orig_hook)


async def test_failed_fallback_seed_does_not_mark_seeded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fallback_db = tmp_path / "retry_seed.db"
    fallback_url = f"sqlite+aiosqlite:///{fallback_db}"
    unreachable_pg = create_async_engine(
        "postgresql+asyncpg://postgres:postgres@127.0.0.1:59999/nope",
        echo=False,
        future=True,
    )
    orig_hook = db_module._fallback_seed_hook
    attempts = 0

    async def flaky_seed() -> None:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RuntimeError("transient seed error")
        await seed_default_pdul_survey()

    await db_module.dispose_engines()
    monkeypatch.setattr(db_module, "engine", unreachable_pg)
    monkeypatch.setattr(settings, "SQLITE_FALLBACK_URL", fallback_url)
    db_module.register_fallback_seed_hook(flaky_seed)

    try:
        gen1 = db_module.get_db()
        with pytest.raises(RuntimeError, match="transient seed error"):
            await anext(gen1)
        assert db_module._fallback_seeded is False

        gen2 = db_module.get_db()
        session2 = await anext(gen2)
        count = (
            await session2.execute(text("SELECT COUNT(*) FROM encuestas"))
        ).scalar_one()
        try:
            await anext(gen2)
        except StopAsyncIteration:
            pass
        assert count == 1
        assert db_module._fallback_seeded is True
    finally:
        monkeypatch.undo()
        await unreachable_pg.dispose()
        await db_module.dispose_engines()
        db_module.register_fallback_seed_hook(orig_hook)


def test_sequential_asyncio_run_fallback_cycles(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def cycle(idx: int) -> None:
        monkeypatch.setattr(
            settings,
            "SQLITE_FALLBACK_URL",
            f"sqlite+aiosqlite:///{tmp_path / f'cycle_{idx}.db'}",
        )
        engines = await asyncio.gather(
            *[db_module.init_sqlite_fallback() for _ in range(5)]
        )
        assert len({id(eng) for eng in engines}) == 1
        await db_module.dispose_engines()

    try:
        asyncio.run(cycle(1))
        asyncio.run(cycle(2))
    finally:
        monkeypatch.undo()


def test_alembic_cli_works_from_arbitrary_cwd(tmp_path: Path) -> None:
    db_file = tmp_path / "cwd_test.db"
    alembic_bin = Path(sys.executable).parent / "alembic"
    proc = subprocess.run(
        [
            str(alembic_bin),
            "-c",
            str(ALEMBIC_INI_PATH),
            "-x",
            f"url=sqlite:///{db_file}",
            "upgrade",
            "head",
        ],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    with sqlite3.connect(db_file) as conn:
        version = conn.execute("SELECT version_num FROM alembic_version").fetchone()
        assert version == ("0001_initial_schema",)
