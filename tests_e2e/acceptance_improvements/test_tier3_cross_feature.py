"""Tier 3 Pairwise Cross-Feature Opaque-Box Acceptance Tests (F1–F13)."""

from __future__ import annotations

import csv
import io
import json
import re
import sqlite3
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any, Dict

import httpx

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from conftest import (  # noqa: E402
    ALEMBIC_BIN,
    CANONICAL_SURVEY_ID,
    PII_FIELDS,
    REPO_ROOT,
    build_full_citizen_payload,
    launch_isolated_uvicorn,
)


def test_t3_alembic_submission_analytics_paginated_and_streaming_export_parity(
    tmp_path: Path,
) -> None:
    """F3/F4 + F5 + F6 + F9: Alembic-migrated DB -> citizen submissions ->
    /preguntas-metricas + /admin/respuestas + streaming CSV/JSON export parity.
    """
    db_path = tmp_path / "pairwise_parity.db"
    fallback_db = tmp_path / "pairwise_fallback.db"
    db_url = f"sqlite+aiosqlite:///{db_path}"
    fallback_url = f"sqlite+aiosqlite:///{fallback_db}"

    # Pre-migrate via Alembic CLI
    mig = subprocess.run(
        [str(ALEMBIC_BIN), "-c", str(REPO_ROOT / "alembic.ini"), "upgrade", "head"],
        cwd=str(REPO_ROOT),
        env={"PATH": "", **dict(**__import__("os").environ), "DATABASE_URL": db_url, "SQLITE_FALLBACK_URL": fallback_url},
        capture_output=True,
        text=True,
        check=False,
    )
    assert mig.returncode == 0, mig.stderr

    with launch_isolated_uvicorn(db_url, fallback_url) as srv:
        base_url = srv["base_url"]
        p1 = build_full_citizen_payload(cedula="20111222", parroquia="san_simon")
        p2 = build_full_citizen_payload(cedula="20333444", parroquia="boqueron")
        p2["data"]["viajes"][0]["modo_principal"] = "4"

        for payload in (p1, p2):
            r = httpx.post(
                f"{base_url}/api/v1/encuestas/{CANONICAL_SURVEY_ID}/respuestas",
                json=payload,
                timeout=10.0,
            )
            assert r.status_code == 201, r.text

        # /preguntas-metricas
        metrics = httpx.get(
            f"{base_url}/api/v1/encuestas/{CANONICAL_SURVEY_ID}/preguntas-metricas",
            timeout=10.0,
        )
        assert metrics.status_code == 200
        by_clave = {m["clave"]: m for m in metrics.json()}
        assert by_clave["parroquia"]["total_respuestas"] == 2
        assert set(by_clave["parroquia"]["labels"]) == {"San Simón", "Boquerón"}

        # /admin/encuestas/{id}/respuestas
        resp_list = httpx.get(
            f"{base_url}/api/v1/admin/encuestas/{CANONICAL_SURVEY_ID}/respuestas?skip=0&limit=50",
            timeout=10.0,
        )
        assert resp_list.status_code == 200
        assert resp_list.json()["total"] == 2
        assert len(resp_list.json()["items"]) == 2

        # Streaming JSON & CSV parity
        exp_json = httpx.get(
            f"{base_url}/api/v1/admin/encuestas/{CANONICAL_SURVEY_ID}/exportar?formato=json&redact_pii=true",
            timeout=10.0,
        )
        assert exp_json.status_code == 200
        json_rows = exp_json.json()
        assert len(json_rows) == 2
        assert {r["parroquia"] for r in json_rows} == {"san_simon", "boqueron"}

        exp_csv = httpx.get(
            f"{base_url}/api/v1/admin/encuestas/{CANONICAL_SURVEY_ID}/exportar?formato=csv&redact_pii=true",
            timeout=10.0,
        )
        assert exp_csv.status_code == 200
        csv_rows = list(csv.DictReader(io.StringIO(exp_csv.text)))
        assert len(csv_rows) == 2
        assert {r["parroquia"] for r in csv_rows} == {"san_simon", "boqueron"}


def test_t3_deactivation_blocks_citizen_while_admin_export_and_inspection_stay_available(
    isolated_backend_server: Dict[str, Any],
) -> None:
    """F5 + F9 + F10 + F11: Create survey -> submit -> deactivate -> citizen blocked, admin export works."""
    base_url = isolated_backend_server["base_url"]
    slug = f"custom_deact_{uuid.uuid4().hex[:8]}"

    create_resp = httpx.post(
        f"{base_url}/api/v1/admin/encuestas",
        json={
            "titulo": "Encuesta Desactivable",
            "slug": slug,
            "tipo_instrumento": "consulta_ciudadana",
            "esquema_formio": {"display": "form", "components": []},
            "activa": True,
        },
        timeout=10.0,
    )
    assert create_resp.status_code == 201
    survey_id = create_resp.json()["id"]

    # Submit while active
    sub_ok = httpx.post(
        f"{base_url}/api/v1/encuestas/{survey_id}/respuestas",
        json=build_full_citizen_payload(cedula="21555666", parroquia="las_cocuizas"),
        timeout=10.0,
    )
    assert sub_ok.status_code == 201

    # Deactivate via admin PATCH
    patch_resp = httpx.patch(
        f"{base_url}/api/v1/admin/encuestas/{survey_id}/estado",
        json={"activa": False},
        timeout=10.0,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["activa"] is False

    # Citizen GET by slug and POST submission must be blocked
    citizen_get = httpx.get(f"{base_url}/api/v1/encuestas/{slug}", timeout=10.0)
    assert citizen_get.status_code == 404

    citizen_post = httpx.post(
        f"{base_url}/api/v1/encuestas/{survey_id}/respuestas",
        json=build_full_citizen_payload(cedula="21777888", parroquia="san_simon"),
        timeout=10.0,
    )
    assert citizen_post.status_code == 400

    # Admin inspection & streaming export remain available
    admin_get = httpx.get(f"{base_url}/api/v1/admin/encuestas/{survey_id}", timeout=10.0)
    assert admin_get.status_code == 200
    assert admin_get.json()["activa"] is False

    admin_rows = httpx.get(
        f"{base_url}/api/v1/admin/encuestas/{survey_id}/respuestas", timeout=10.0
    )
    assert admin_rows.status_code == 200
    assert admin_rows.json()["total"] == 1

    export_csv = httpx.get(
        f"{base_url}/api/v1/admin/encuestas/{survey_id}/exportar?formato=csv&redact_pii=true",
        timeout=10.0,
    )
    assert export_csv.status_code == 200
    parsed = list(csv.DictReader(io.StringIO(export_csv.text)))
    assert len(parsed) == 1
    assert "21555666" not in export_csv.text


def test_t3_dashboard_type_only_map_import_isolates_leaflet_from_citizen_and_dashboard_chunks(
    repo_root: Path,
    frontend_dist_dir: Path,
) -> None:
    """F1 + F2 + F12: DashboardView.vue uses `import type` for MaturinChoroplethMap,
    keeping leaflet out of both initial citizen entry bundle and DashboardView chunk.
    """
    dashboard_src = (repo_root / "frontend" / "src" / "views" / "DashboardView.vue").read_text(
        encoding="utf-8"
    )
    assert re.search(
        r"import\s+type\s+MaturinChoroplethMap\s+from\s+",
        dashboard_src,
    ) or "MaturinChoroplethMap" not in dashboard_src, (
        "DashboardView.vue must only reference MaturinChoroplethMap as a type (`import type`), not runtime import."
    )

    assets_dir = frontend_dist_dir / "assets"
    entry_js = [p for p in assets_dir.glob("index-*.js")]
    dashboard_js = [p for p in assets_dir.glob("DashboardView-*.js")]
    assert entry_js, "Missing index-*.js in frontend/dist/assets/"
    assert dashboard_js, "Missing DashboardView-*.js in frontend/dist/assets/"

    for chunk in entry_js + dashboard_js:
        content = chunk.read_text(encoding="utf-8")
        assert "leaflet-container" not in content, (
            f"Chunk {chunk.name} must not bundle leaflet runtime"
        )
        assert "tileLayer" not in content, (
            f"Chunk {chunk.name} must not bundle leaflet tileLayer"
        )


def test_t3_idempotent_replay_and_duplicate_cedula_do_not_inflate_export_or_kpis(
    isolated_backend_server: Dict[str, Any],
) -> None:
    """F5 + F6 + F9: Idempotent replay (201 -> 200) and duplicate cedula (409)
    leave exactly 1 row in DB, KPIs, paginated admin list, and streaming export.
    """
    base_url = isolated_backend_server["base_url"]
    sub_uuid = str(uuid.uuid4())
    payload = build_full_citizen_payload(
        cedula="22444555",
        parroquia="santa_cruz",
        client_submission_id=sub_uuid,
    )

    first = httpx.post(
        f"{base_url}/api/v1/encuestas/{CANONICAL_SURVEY_ID}/respuestas",
        json=payload,
        timeout=10.0,
    )
    assert first.status_code == 201
    assert first.json()["idempotent_replay"] is False

    replay = httpx.post(
        f"{base_url}/api/v1/encuestas/{CANONICAL_SURVEY_ID}/respuestas",
        json=payload,
        timeout=10.0,
    )
    assert replay.status_code == 200
    assert replay.json()["idempotent_replay"] is True
    assert replay.json()["id"] == first.json()["id"]

    # Different client_submission_id with same cedula -> 409 Conflict
    dup_payload = build_full_citizen_payload(
        cedula="22444555",
        parroquia="santa_cruz",
        client_submission_id=str(uuid.uuid4()),
    )
    conflict = httpx.post(
        f"{base_url}/api/v1/encuestas/{CANONICAL_SURVEY_ID}/respuestas",
        json=dup_payload,
        timeout=10.0,
    )
    assert conflict.status_code == 409

    kpis = httpx.get(
        f"{base_url}/api/v1/encuestas/{CANONICAL_SURVEY_ID}/kpis", timeout=10.0
    )
    assert kpis.status_code == 200
    assert kpis.json()["total_encuestas"] == 1

    export_json = httpx.get(
        f"{base_url}/api/v1/admin/encuestas/{CANONICAL_SURVEY_ID}/exportar?formato=json&redact_pii=true",
        timeout=10.0,
    )
    assert len(export_json.json()) == 1


def test_t3_analytics_endpoints_parity_on_multimodal_trips(
    isolated_backend_server: Dict[str, Any],
) -> None:
    """F6 + F12: Full submissions with chained OD trips reconcile across /kpis,
    /resultados-parroquia, /reparto-modal, /matriz-od, and /preguntas-metricas.
    """
    base_url = isolated_backend_server["base_url"]
    p1 = build_full_citizen_payload(cedula="23111222", parroquia="san_simon")
    p2 = build_full_citizen_payload(cedula="23333444", parroquia="alto_de_los_godos")

    for payload in (p1, p2):
        r = httpx.post(
            f"{base_url}/api/v1/encuestas/{CANONICAL_SURVEY_ID}/respuestas",
            json=payload,
            timeout=10.0,
        )
        assert r.status_code == 201

    kpis = httpx.get(f"{base_url}/api/v1/encuestas/{CANONICAL_SURVEY_ID}/kpis", timeout=10.0).json()
    parroquias = httpx.get(
        f"{base_url}/api/v1/encuestas/{CANONICAL_SURVEY_ID}/resultados-parroquia", timeout=10.0
    ).json()
    reparto = httpx.get(
        f"{base_url}/api/v1/encuestas/{CANONICAL_SURVEY_ID}/reparto-modal", timeout=10.0
    ).json()
    matriz = httpx.get(
        f"{base_url}/api/v1/encuestas/{CANONICAL_SURVEY_ID}/matriz-od", timeout=10.0
    ).json()
    preguntas = httpx.get(
        f"{base_url}/api/v1/encuestas/{CANONICAL_SURVEY_ID}/preguntas-metricas", timeout=10.0
    ).json()

    assert kpis["total_encuestas"] == 2
    assert sum(row["total_respuestas"] for row in parroquias) == 2
    assert sum(row["total_viajes"] for row in reparto) == 4
    assert sum(row["total_viajes"] for row in matriz) == 4
    by_clave = {m["clave"]: m for m in preguntas}
    assert by_clave["modo_principal_viajes"]["total_respuestas"] == 4


def test_t3_pre_alembic_db_upgrade_and_streaming_pii_redaction(tmp_path: Path) -> None:
    """F4 + F5: Pre-Alembic DB with existing PII row stamps on startup and streaming export redacts all 11 PII fields."""
    legacy_db = tmp_path / "legacy_pair.db"
    survey_id = str(uuid.uuid4())
    raw_datos = {
        "parroquia": "san_simon",
        "zona_residencia_od": "Z-05",
        "cedula": "24000111",
        "nombre_apellido": "Carlos Legacy",
        "telefono": "0412-0001111",
        "correo": "carlos@ejemplo.ve",
        "direccion_exacta": "Calle Real #9",
        "residentes": [{"persona_numero": 1, "nombre": "Carlos", "sexo": "1", "edad": 40}],
    }
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
            (survey_id, "Legacy Pair", "legacy_pair_slug", "consulta_ciudadana", '{"components":[]}', 1),
        )
        conn.execute(
            "INSERT INTO respuestas_ciudadanas (encuesta_id, cedula, parroquia, zona_od, datos) "
            "VALUES (?, ?, ?, ?, ?)",
            (survey_id, "24000111", "san_simon", "Z-05", json.dumps(raw_datos)),
        )
        conn.commit()

    db_url = f"sqlite+aiosqlite:///{legacy_db}"
    fallback_url = f"sqlite+aiosqlite:///{tmp_path / 'unused_fb.db'}"
    with launch_isolated_uvicorn(db_url, fallback_url) as srv:
        exp = httpx.get(
            f"{srv['base_url']}/api/v1/admin/encuestas/{survey_id}/exportar?formato=json&redact_pii=true",
            timeout=10.0,
        )
        assert exp.status_code == 200
        rows = exp.json()
        assert len(rows) == 1
        assert "cedula" not in rows[0]
        for pii_key in PII_FIELDS:
            assert pii_key not in rows[0]["datos"]
        assert "nombre" not in rows[0]["datos"]["residentes"][0]
        assert rows[0]["datos"]["residentes"][0]["edad"] == 40
