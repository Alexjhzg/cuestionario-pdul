"""Tier 1 & Tier 2 Opaque-Box Acceptance Tests for R2 (Database & Startup):
- Feature F3: Alembic config, initial migration, SQLite & offline PostgreSQL DDL, idempotency, downgrade/upgrade
- Feature F4: App lifespan migration startup, pre-Alembic stamp safety, SQLite fallback, and render.yaml
"""

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Dict, Optional

import httpx
import pytest
import yaml

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from conftest import (  # noqa: E402
    ALEMBIC_BIN,
    CANONICAL_SURVEY_ID,
    CANONICAL_SURVEY_SLUG,
    LEGACY_SURVEY_SLUG,
    PYTHON_BIN,
    REPO_ROOT,
    launch_isolated_uvicorn,
)


def _run_alembic(
    args: list[str],
    database_url: str,
    fallback_url: Optional[str] = None,
) -> subprocess.CompletedProcess[str]:
    assert ALEMBIC_BIN.is_file(), f"Alembic CLI missing at {ALEMBIC_BIN}"
    env = os.environ.copy()
    env["DATABASE_URL"] = database_url
    env["SQLITE_FALLBACK_URL"] = fallback_url or database_url
    return subprocess.run(
        [str(ALEMBIC_BIN), "-c", str(REPO_ROOT / "alembic.ini"), *args],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _sqlite_table_names(db_path: Path) -> set[str]:
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    return {r[0] for r in rows}


def _sqlite_index_names(db_path: Path) -> set[str]:
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index'"
        ).fetchall()
    return {r[0] for r in rows}


# ---------------------------------------------------------------------------
# Feature F3 — Alembic config & initial migration (Tier 1 & Tier 2)
# ---------------------------------------------------------------------------


def test_f3_alembic_files_and_dependencies_exist(repo_root: Path) -> None:
    assert (repo_root / "alembic.ini").is_file(), "Missing root alembic.ini"
    assert (repo_root / "backend" / "alembic" / "env.py").is_file(), "Missing backend/alembic/env.py"
    versions_dir = repo_root / "backend" / "alembic" / "versions"
    assert versions_dir.is_dir(), "Missing backend/alembic/versions/"
    migration_files = [p for p in versions_dir.glob("*.py") if not p.name.startswith("__")]
    assert len(migration_files) >= 1, "Expected at least one Alembic migration revision"
    assert ALEMBIC_BIN.is_file(), f"Expected alembic executable in backend/.venv/bin: {ALEMBIC_BIN}"


def test_f3_alembic_has_single_linear_head(tmp_path: Path) -> None:
    db_url = f"sqlite+aiosqlite:///{tmp_path / 'heads.db'}"
    res = _run_alembic(["heads"], database_url=db_url)
    assert res.returncode == 0, f"alembic heads failed:\n{res.stdout}\n{res.stderr}"
    head_lines = [ln.strip() for ln in res.stdout.splitlines() if ln.strip()]
    assert len(head_lines) == 1, f"Expected single linear head, got: {head_lines}"


def test_f3_upgrade_head_on_clean_sqlite_creates_full_schema_and_indexes(tmp_path: Path) -> None:
    db_path = tmp_path / "clean_migrate.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"
    res = _run_alembic(["upgrade", "head"], database_url=db_url)
    assert res.returncode == 0, f"alembic upgrade head failed:\n{res.stdout}\n{res.stderr}"

    tables = _sqlite_table_names(db_path)
    assert {"alembic_version", "encuestas", "respuestas_ciudadanas"}.issubset(tables), (
        f"Missing expected tables, found: {tables}"
    )

    with sqlite3.connect(db_path) as conn:
        enc_cols = {r[1] for r in conn.execute("PRAGMA table_info(encuestas)").fetchall()}
        resp_cols = {r[1] for r in conn.execute("PRAGMA table_info(respuestas_ciudadanas)").fetchall()}
        fks = conn.execute("PRAGMA foreign_key_list(respuestas_ciudadanas)").fetchall()
        ddl_row = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='respuestas_ciudadanas'"
        ).fetchone()
        version_row = conn.execute("SELECT version_num FROM alembic_version").fetchone()

    assert {
        "id", "titulo", "slug", "tipo_instrumento", "esquema_formio", "activa", "creado_en"
    }.issubset(enc_cols)
    assert {
        "id", "encuesta_id", "client_submission_id", "cedula", "parroquia", "zona_od", "datos", "fecha_registro"
    }.issubset(resp_cols)
    assert any(fk[2] == "encuestas" and fk[6].upper() == "RESTRICT" for fk in fks), (
        f"Expected ON DELETE RESTRICT FK to encuestas, got: {fks}"
    )
    assert ddl_row and "uq_voto_ciudadano" in ddl_row[0], (
        f"Expected uq_voto_ciudadano constraint in table DDL, got: {ddl_row}"
    )
    assert version_row and version_row[0], "alembic_version should be populated"

    indexes = _sqlite_index_names(db_path)
    expected_indexes = {
        "ix_encuestas_slug",
        "ix_respuestas_ciudadanas_encuesta_id",
        "ix_respuestas_ciudadanas_client_submission_id",
        "ix_respuestas_ciudadanas_parroquia",
        "ix_respuestas_ciudadanas_zona_od",
    }
    assert expected_indexes.issubset(indexes), (
        f"Missing expected indexes {expected_indexes - indexes}; found: {indexes}"
    )


def test_f3_offline_postgresql_sql_emits_valid_pg_ddl(tmp_path: Path) -> None:
    pg_url = "postgresql+asyncpg://user:pass@localhost:5432/pdul_db"
    fallback_url = f"sqlite+aiosqlite:///{tmp_path / 'unused.db'}"
    res = _run_alembic(["upgrade", "head", "--sql"], database_url=pg_url, fallback_url=fallback_url)
    assert res.returncode == 0, f"Offline PG --sql failed:\n{res.stdout}\n{res.stderr}"
    sql_out = res.stdout
    assert "CREATE TABLE encuestas" in sql_out
    assert "CREATE TABLE respuestas_ciudadanas" in sql_out
    assert "UUID" in sql_out.upper()
    assert "JSONB" in sql_out.upper()
    assert "uq_voto_ciudadano" in sql_out
    assert "ON DELETE RESTRICT" in sql_out.upper()
    assert "alembic_version" in sql_out
    for pg_index in (
        "idx_respuestas_datos_gin",
        "idx_respuestas_encuesta_parroquia",
        "idx_respuestas_encuesta_zona_od",
    ):
        assert pg_index in sql_out, f"Expected PostgreSQL-only index {pg_index} in offline PG DDL"


def test_f3_tier2_upgrade_head_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "idempotent.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"
    first = _run_alembic(["upgrade", "head"], database_url=db_url)
    assert first.returncode == 0, first.stderr

    # Seed one row and re-run upgrade head
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO encuestas (id, titulo, slug, tipo_instrumento, esquema_formio, activa) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), "Test", "test_idem", "consulta_ciudadana", "{}", 1),
        )
        conn.commit()

    second = _run_alembic(["upgrade", "head"], database_url=db_url)
    assert second.returncode == 0, f"Second upgrade head failed:\n{second.stdout}\n{second.stderr}"
    with sqlite3.connect(db_path) as conn:
        count = conn.execute("SELECT COUNT(*) FROM encuestas WHERE slug='test_idem'").fetchone()[0]
    assert count == 1


def test_f3_tier2_downgrade_base_and_reupgrade_cycle(tmp_path: Path) -> None:
    db_path = tmp_path / "cycle.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"

    up1 = _run_alembic(["upgrade", "head"], database_url=db_url)
    assert up1.returncode == 0, up1.stderr

    down = _run_alembic(["downgrade", "base"], database_url=db_url)
    assert down.returncode == 0, f"alembic downgrade base failed:\n{down.stdout}\n{down.stderr}"
    tables_after_down = _sqlite_table_names(db_path)
    assert "encuestas" not in tables_after_down
    assert "respuestas_ciudadanas" not in tables_after_down

    up2 = _run_alembic(["upgrade", "head"], database_url=db_url)
    assert up2.returncode == 0, f"Re-upgrade after downgrade failed:\n{up2.stdout}\n{up2.stderr}"
    tables_after_up2 = _sqlite_table_names(db_path)
    assert {"encuestas", "respuestas_ciudadanas"}.issubset(tables_after_up2)


def test_f3_tier2_sqlite_enforces_on_delete_restrict_and_uq_voto_ciudadano(tmp_path: Path) -> None:
    db_path = tmp_path / "constraints.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"
    res = _run_alembic(["upgrade", "head"], database_url=db_url)
    assert res.returncode == 0, res.stderr

    enc_id = str(uuid.uuid4())
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(
            "INSERT INTO encuestas (id, titulo, slug, tipo_instrumento, esquema_formio, activa) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (enc_id, "Restricción", "restriccion_slug", "consulta_ciudadana", "{}", 1),
        )
        conn.execute(
            "INSERT INTO respuestas_ciudadanas (encuesta_id, cedula, parroquia, datos) "
            "VALUES (?, ?, ?, ?)",
            (enc_id, "12345678", "san_simon", '{"parroquia":"san_simon"}'),
        )
        conn.commit()

        # Duplicate (encuesta_id, cedula) must fail uq_voto_ciudadano
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO respuestas_ciudadanas (encuesta_id, cedula, parroquia, datos) "
                "VALUES (?, ?, ?, ?)",
                (enc_id, "12345678", "san_simon", '{"parroquia":"san_simon"}'),
            )

        # Multiple NULL cedula rows for same survey must be allowed
        conn.execute(
            "INSERT INTO respuestas_ciudadanas (encuesta_id, cedula, parroquia, datos) "
            "VALUES (?, NULL, ?, ?)",
            (enc_id, "boqueron", '{"parroquia":"boqueron"}'),
        )
        conn.execute(
            "INSERT INTO respuestas_ciudadanas (encuesta_id, cedula, parroquia, datos) "
            "VALUES (?, NULL, ?, ?)",
            (enc_id, "boqueron", '{"parroquia":"boqueron"}'),
        )

        # Deleting encuesta with responses must violate ON DELETE RESTRICT
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("DELETE FROM encuestas WHERE id = ?", (enc_id,))


def test_f3_tier2_backend_requirements_and_pyproject_declare_alembic(repo_root: Path) -> None:
    req_txt = (repo_root / "backend" / "requirements.txt").read_text(encoding="utf-8").lower()
    pyproject = (repo_root / "backend" / "pyproject.toml").read_text(encoding="utf-8").lower()
    assert "alembic" in req_txt, "backend/requirements.txt must declare alembic"
    assert "alembic" in pyproject, "backend/pyproject.toml must declare alembic"


# ---------------------------------------------------------------------------
# Feature F4 — App startup, pre-Alembic stamp safety, fallback & render.yaml
# ---------------------------------------------------------------------------


def test_f4_clean_startup_migrates_stamps_alembic_and_seeds_surveys(tmp_path: Path) -> None:
    app_db = tmp_path / "clean_startup.db"
    fallback_db = tmp_path / "unused_fallback.db"
    db_url = f"sqlite+aiosqlite:///{app_db}"
    fallback_url = f"sqlite+aiosqlite:///{fallback_db}"

    with launch_isolated_uvicorn(db_url, fallback_url) as srv:
        health = httpx.get(f"{srv['base_url']}/health", timeout=5.0)
        assert health.status_code == 200
        assert health.json()["status"] == "ok"

        v1_health = httpx.get(f"{srv['base_url']}/api/v1/health", timeout=5.0)
        assert v1_health.status_code == 200
        assert v1_health.json()["status"] == "ok"

        surveys_resp = httpx.get(f"{srv['base_url']}/api/v1/encuestas", timeout=5.0)
        assert surveys_resp.status_code == 200
        surveys = surveys_resp.json()
        by_slug = {s["slug"]: s for s in surveys}
        assert CANONICAL_SURVEY_SLUG in by_slug
        assert by_slug[CANONICAL_SURVEY_SLUG]["id"] == CANONICAL_SURVEY_ID
        assert by_slug[CANONICAL_SURVEY_SLUG]["activa"] is True

        # EncuestaRepository.get_by_slug() aliases LEGACY_SURVEY_SLUG -> CANONICAL_SURVEY_SLUG
        legacy_resp = httpx.get(
            f"{srv['base_url']}/api/v1/encuestas/{LEGACY_SURVEY_SLUG}",
            timeout=5.0,
        )
        assert legacy_resp.status_code == 200, legacy_resp.text
        legacy_survey = legacy_resp.json()
        assert legacy_survey["id"] == CANONICAL_SURVEY_ID
        assert legacy_survey["slug"] == CANONICAL_SURVEY_SLUG
        assert legacy_survey["activa"] is True

    assert "alembic_version" in _sqlite_table_names(app_db)
    with sqlite3.connect(app_db) as conn:
        ver = conn.execute("SELECT version_num FROM alembic_version").fetchone()
    assert ver and ver[0], "Clean startup must populate alembic_version"


def test_f4_render_yaml_runs_alembic_upgrade_head_before_uvicorn(repo_root: Path) -> None:
    render_cfg = yaml.safe_load((repo_root / "render.yaml").read_text(encoding="utf-8"))
    services = render_cfg.get("services", [])
    backend_svc = next((s for s in services if s.get("name") == "cuestionario-pdul-backend"), None)
    assert backend_svc is not None, "Missing cuestionario-pdul-backend in render.yaml"

    start_cmd = backend_svc.get("startCommand", "")
    assert "alembic upgrade head" in start_cmd, (
        f"render.yaml startCommand must run 'alembic upgrade head', got: {start_cmd!r}"
    )
    assert start_cmd.index("alembic upgrade head") < start_cmd.index("uvicorn"), (
        "alembic upgrade head must execute before uvicorn in render.yaml startCommand"
    )
    assert backend_svc.get("healthCheckPath") == "/health"
    env_vars: Dict[str, dict] = {e["key"]: e for e in backend_svc.get("envVars", [])}
    assert "DATABASE_URL" in env_vars
    assert env_vars["DATABASE_URL"].get("fromDatabase", {}).get("name") == "cuestionario-pdul-db"


def test_f4_tier2_unreachable_postgres_falls_back_to_temp_sqlite(
    tmp_path: Path,
    repo_root: Path,
) -> None:
    root_db = repo_root / "pdul_dev.db"
    before_stat = root_db.stat() if root_db.exists() else None

    fallback_db = tmp_path / "fallback_resilience.db"
    bad_pg_url = "postgresql+asyncpg://baduser:badpass@127.0.0.1:59999/nonexistent"
    fallback_url = f"sqlite+aiosqlite:///{fallback_db}"

    with launch_isolated_uvicorn(bad_pg_url, fallback_url) as srv:
        health = httpx.get(f"{srv['base_url']}/health", timeout=5.0)
        assert health.status_code == 200
        surveys = httpx.get(f"{srv['base_url']}/api/v1/encuestas", timeout=5.0)
        assert surveys.status_code == 200
        slugs = {s["slug"] for s in surveys.json()}
        assert CANONICAL_SURVEY_SLUG in slugs

        legacy_resp = httpx.get(
            f"{srv['base_url']}/api/v1/encuestas/{LEGACY_SURVEY_SLUG}",
            timeout=5.0,
        )
        assert legacy_resp.status_code == 200, legacy_resp.text
        assert legacy_resp.json()["id"] == CANONICAL_SURVEY_ID
        assert legacy_resp.json()["activa"] is True

    assert fallback_db.is_file()
    assert "alembic_version" in _sqlite_table_names(fallback_db)

    if before_stat is not None:
        after_stat = root_db.stat()
        assert after_stat.st_size == before_stat.st_size
        assert after_stat.st_mtime_ns == before_stat.st_mtime_ns


def test_f4_tier2_pre_alembic_legacy_sqlite_stamps_and_preserves_rows(tmp_path: Path) -> None:
    legacy_db = tmp_path / "legacy_pre_alembic.db"
    custom_survey_id = str(uuid.uuid4())

    # Create legacy schema WITHOUT alembic_version + insert 1 survey & 1 submission
    with sqlite3.connect(legacy_db) as conn:
        conn.executescript(
            """
            CREATE TABLE encuestas (
                id CHAR(36) NOT NULL PRIMARY KEY,
                titulo VARCHAR(255) NOT NULL,
                slug VARCHAR(120) NOT NULL,
                tipo_instrumento VARCHAR(30) NOT NULL,
                esquema_formio JSON NOT NULL,
                activa BOOLEAN NOT NULL,
                creado_en DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
            );
            CREATE UNIQUE INDEX ix_encuestas_slug ON encuestas (slug);
            CREATE TABLE respuestas_ciudadanas (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                encuesta_id CHAR(36) NOT NULL,
                client_submission_id CHAR(36),
                cedula VARCHAR(15),
                parroquia VARCHAR(60) NOT NULL,
                zona_od VARCHAR(30),
                datos JSON NOT NULL,
                fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                CONSTRAINT uq_voto_ciudadano UNIQUE (encuesta_id, cedula),
                FOREIGN KEY(encuesta_id) REFERENCES encuestas (id) ON DELETE RESTRICT
            );
            """
        )
        conn.execute(
            "INSERT INTO encuestas (id, titulo, slug, tipo_instrumento, esquema_formio, activa) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                custom_survey_id,
                "Encuesta Pre-Alembic Preservada",
                "encuesta_legacy_preservada",
                "consulta_ciudadana",
                '{"display":"form","components":[]}',
                1,
            ),
        )
        conn.execute(
            "INSERT INTO respuestas_ciudadanas (encuesta_id, cedula, parroquia, zona_od, datos) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                custom_survey_id,
                "19111222",
                "san_simon",
                "Z-99",
                '{"parroquia":"san_simon","cedula":"19111222","observaciones_generales":"Dato previo"}',
            ),
        )
        conn.commit()

    assert "alembic_version" not in _sqlite_table_names(legacy_db)

    db_url = f"sqlite+aiosqlite:///{legacy_db}"
    fallback_url = f"sqlite+aiosqlite:///{tmp_path / 'legacy_fallback.db'}"

    with launch_isolated_uvicorn(db_url, fallback_url) as srv:
        resp = httpx.get(
            f"{srv['base_url']}/api/v1/admin/encuestas/{custom_survey_id}/respuestas",
            timeout=5.0,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["parroquia"] == "san_simon"
        assert body["items"][0]["datos"]["observaciones_generales"] == "Dato previo"

    assert "alembic_version" in _sqlite_table_names(legacy_db)


def test_f4_tier2_main_py_delegates_schema_evolution_to_migrations(repo_root: Path) -> None:
    main_py = (repo_root / "backend" / "app" / "main.py").read_text(encoding="utf-8")
    assert (repo_root / "backend" / "app" / "core" / "migrations.py").is_file(), (
        "Expected backend/app/core/migrations.py to exist"
    )
    assert "migrations" in main_py or "run_migrations" in main_py, (
        "backend/app/main.py must delegate schema initialization to migrations module"
    )
    assert "Base.metadata.create_all" not in main_py, (
        "backend/app/main.py must not rely on Base.metadata.create_all directly"
    )


def test_f4_tier2_database_url_normalizes_postgres_scheme_and_sslmode() -> None:
    script = (
        "from backend.app.core.config import Settings; "
        "s1 = Settings(DATABASE_URL='postgres://u:p@db.render.internal:5432/pdul?sslmode=require', "
        "SQLITE_FALLBACK_URL='sqlite:///local_test.db'); "
        "assert s1.DATABASE_URL == 'postgresql+asyncpg://u:p@db.render.internal:5432/pdul?ssl=require', s1.DATABASE_URL; "
        "assert s1.SQLITE_FALLBACK_URL == 'sqlite+aiosqlite:///local_test.db', s1.SQLITE_FALLBACK_URL; "
        "s2 = Settings(DATABASE_URL='postgresql://u:p@localhost:5432/pdul?sslmode=disable'); "
        "assert s2.DATABASE_URL == 'postgresql+asyncpg://u:p@localhost:5432/pdul', s2.DATABASE_URL; "
        "print('OK')"
    )
    res = subprocess.run(
        [str(PYTHON_BIN), "-c", script],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, f"Settings URL validator check failed:\n{res.stdout}\n{res.stderr}"
    assert "OK" in res.stdout
