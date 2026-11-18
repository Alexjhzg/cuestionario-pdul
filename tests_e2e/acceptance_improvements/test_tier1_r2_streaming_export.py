"""Tier 1 & Tier 2 Opaque-Box Acceptance Tests for R2 (Streaming Export & Analytics):
- Feature F5: Streaming CSV/JSON export, Transfer-Encoding: chunked, redact_pii, RFC 7807 404, 1,200+ rows
- Feature F6: question_analytics.py facade compatibility & GET /api/v1/encuestas/{id}/preguntas-metricas
"""

from __future__ import annotations

import csv
import io
import json
import sqlite3
import subprocess
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

import httpx
import pytest

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from conftest import (  # noqa: E402
    CANONICAL_SURVEY_ID,
    PII_FIELDS,
    PYTHON_BIN,
    REPO_ROOT,
    build_full_citizen_payload,
    build_minimal_citizen_payload,
)


def _assert_no_pii_recursive(obj: Any, pii_keys: tuple[str, ...]) -> None:
    lowered_pii = {k.lower() for k in pii_keys}
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert k.lower() not in lowered_pii, f"PII key '{k}' leaked in redacted payload"
            _assert_no_pii_recursive(v, pii_keys)
    elif isinstance(obj, list):
        for item in obj:
            _assert_no_pii_recursive(item, pii_keys)


def _create_survey(base_url: str, slug_prefix: str = "export_test") -> str:
    slug = f"{slug_prefix}_{uuid.uuid4().hex[:8]}"
    resp = httpx.post(
        f"{base_url}/api/v1/admin/encuestas",
        json={
            "titulo": f"Encuesta {slug}",
            "slug": slug,
            "tipo_instrumento": "consulta_ciudadana",
            "esquema_formio": {"display": "form", "components": []},
            "activa": True,
        },
        timeout=10.0,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


# ---------------------------------------------------------------------------
# Feature F5 — Streaming CSV/JSON Export (Tier 1 & Tier 2)
# ---------------------------------------------------------------------------


def test_f5_empty_survey_export_csv_and_json_headers(
    isolated_backend_server: Dict[str, Any],
) -> None:
    base_url = isolated_backend_server["base_url"]
    survey_id = _create_survey(base_url, "empty_export")

    # Empty JSON export
    with httpx.Client(timeout=15.0) as client:
        with client.stream(
            "GET", f"{base_url}/api/v1/admin/encuestas/{survey_id}/exportar?formato=json"
        ) as resp_json:
            assert resp_json.status_code == 200
            assert "application/json" in resp_json.headers.get("content-type", "").lower()
            assert (
                resp_json.headers.get("content-disposition")
                == f'attachment; filename="encuesta_{survey_id}.json"'
            )
            assert resp_json.headers.get("transfer-encoding", "").lower() == "chunked"
            assert "content-length" not in {k.lower() for k in resp_json.headers.keys()}
            body_json = resp_json.read().decode("utf-8")
            assert json.loads(body_json) == []

        # Empty CSV export
        with client.stream(
            "GET", f"{base_url}/api/v1/admin/encuestas/{survey_id}/exportar?formato=csv"
        ) as resp_csv:
            assert resp_csv.status_code == 200
            assert "text/csv" in resp_csv.headers.get("content-type", "").lower()
            assert (
                resp_csv.headers.get("content-disposition")
                == f'attachment; filename="encuesta_{survey_id}.csv"'
            )
            assert resp_csv.headers.get("transfer-encoding", "").lower() == "chunked"
            assert "content-length" not in {k.lower() for k in resp_csv.headers.keys()}
            body_csv = resp_csv.read().decode("utf-8")
            rows = list(csv.reader(io.StringIO(body_csv)))
            assert rows == [["id", "parroquia", "zona_od", "fecha_registro", "cedula", "datos_json"]]


def test_f5_export_defaults_to_json_and_unredacted(
    isolated_backend_server: Dict[str, Any],
) -> None:
    base_url = isolated_backend_server["base_url"]
    payload = build_full_citizen_payload(cedula="15001001", parroquia="san_simon")
    post_res = httpx.post(
        f"{base_url}/api/v1/encuestas/{CANONICAL_SURVEY_ID}/respuestas",
        json=payload,
        timeout=10.0,
    )
    assert post_res.status_code == 201, post_res.text

    resp = httpx.get(
        f"{base_url}/api/v1/admin/encuestas/{CANONICAL_SURVEY_ID}/exportar",
        timeout=10.0,
    )
    assert resp.status_code == 200
    assert "application/json" in resp.headers.get("content-type", "").lower()
    rows = resp.json()
    assert len(rows) == 1
    assert rows[0]["cedula"] == "15001001"
    assert rows[0]["datos"]["nombre_apellido"] == "Ana María Pérez"


def test_f5_populated_streaming_csv_and_json_newest_first_ordering(
    isolated_backend_server: Dict[str, Any],
) -> None:
    base_url = isolated_backend_server["base_url"]
    survey_id = _create_survey(base_url, "ordered_export")

    sub_ids: List[int] = []
    for idx, par in enumerate(["san_simon", "boqueron", "las_cocuizas"], start=1):
        res = httpx.post(
            f"{base_url}/api/v1/encuestas/{survey_id}/respuestas",
            json=build_full_citizen_payload(cedula=f"1700000{idx}", parroquia=par),
            timeout=10.0,
        )
        assert res.status_code == 201, res.text
        sub_ids.append(res.json()["id"])

    # JSON export
    resp_json = httpx.get(
        f"{base_url}/api/v1/admin/encuestas/{survey_id}/exportar?formato=json&redact_pii=false",
        timeout=10.0,
    )
    assert resp_json.status_code == 200
    items = resp_json.json()
    assert len(items) == 3
    # Newest-first ordering (fecha_registro DESC)
    timestamps = [datetime.fromisoformat(r["fecha_registro"]) for r in items]
    assert timestamps == sorted(timestamps, reverse=True)
    for row in items:
        assert {"id", "encuesta_id", "parroquia", "zona_od", "fecha_registro", "cedula", "datos"}.issubset(
            row.keys()
        )
        assert row["encuesta_id"] == survey_id

    # CSV export
    resp_csv = httpx.get(
        f"{base_url}/api/v1/admin/encuestas/{survey_id}/exportar?formato=csv&redact_pii=false",
        timeout=10.0,
    )
    assert resp_csv.status_code == 200
    reader = csv.DictReader(io.StringIO(resp_csv.text))
    assert reader.fieldnames == ["id", "parroquia", "zona_od", "fecha_registro", "cedula", "datos_json"]
    csv_rows = list(reader)
    assert len(csv_rows) == 3
    for crow in csv_rows:
        parsed_datos = json.loads(crow["datos_json"])
        assert parsed_datos["parroquia"] == crow["parroquia"]
        assert crow["cedula"].startswith("1700000")


def test_f5_tier2_redact_pii_strips_all_11_fields_and_nested_mixed_case(
    isolated_backend_server: Dict[str, Any],
) -> None:
    base_url = isolated_backend_server["base_url"]
    survey_id = _create_survey(base_url, "pii_redact")

    payload = build_full_citizen_payload(
        cedula="18999888",
        parroquia="alto_de_los_godos",
        include_all_pii=True,
        mixed_case_nested_pii=True,
    )
    post_res = httpx.post(
        f"{base_url}/api/v1/encuestas/{survey_id}/respuestas",
        json=payload,
        timeout=10.0,
    )
    assert post_res.status_code == 201, post_res.text

    # Redacted JSON
    resp_json = httpx.get(
        f"{base_url}/api/v1/admin/encuestas/{survey_id}/exportar?formato=json&redact_pii=true",
        timeout=10.0,
    )
    assert resp_json.status_code == 200
    json_rows = resp_json.json()
    assert len(json_rows) == 1
    row = json_rows[0]
    assert "cedula" not in row
    assert row["parroquia"] == "alto_de_los_godos"
    assert row["zona_od"] == "Z-01"
    _assert_no_pii_recursive(row["datos"], PII_FIELDS)
    # Non-PII nested attributes preserved
    assert row["datos"]["residentes"][0]["sexo"] == "2"
    assert row["datos"]["residentes"][0]["edad"] == 34
    assert len(row["datos"]["viajes"]) == 2
    assert "18999888" not in resp_json.text
    assert "ana.nested@ejemplo.ve" not in resp_json.text
    assert "0414-5550199" not in resp_json.text

    # Redacted CSV
    resp_csv = httpx.get(
        f"{base_url}/api/v1/admin/encuestas/{survey_id}/exportar?formato=csv&redact_pii=true",
        timeout=10.0,
    )
    assert resp_csv.status_code == 200
    reader = csv.DictReader(io.StringIO(resp_csv.text))
    assert reader.fieldnames == ["id", "parroquia", "zona_od", "fecha_registro", "datos_json"]
    csv_rows = list(reader)
    assert len(csv_rows) == 1
    datos_parsed = json.loads(csv_rows[0]["datos_json"])
    _assert_no_pii_recursive(datos_parsed, PII_FIELDS)
    assert datos_parsed["residentes"][0]["edad"] == 34
    assert "18999888" not in resp_csv.text
    assert "Av. Raúl Leoni, Casa 14-B" not in resp_csv.text


def test_f5_tier2_unredacted_retains_all_11_pii_fields(
    isolated_backend_server: Dict[str, Any],
) -> None:
    base_url = isolated_backend_server["base_url"]
    survey_id = _create_survey(base_url, "pii_keep")

    payload = build_full_citizen_payload(
        cedula="16222333",
        parroquia="la_cruz",
        include_all_pii=True,
    )
    post_res = httpx.post(
        f"{base_url}/api/v1/encuestas/{survey_id}/respuestas",
        json=payload,
        timeout=10.0,
    )
    assert post_res.status_code == 201, post_res.text

    resp_json = httpx.get(
        f"{base_url}/api/v1/admin/encuestas/{survey_id}/exportar?formato=json&redact_pii=false",
        timeout=10.0,
    )
    assert resp_json.status_code == 200
    row = resp_json.json()[0]
    assert row["cedula"] == "16222333"
    for key in PII_FIELDS:
        assert key in row["datos"], f"Expected PII field '{key}' to be retained when redact_pii=false"


def test_f5_tier2_unknown_survey_returns_404_rfc7807_before_stream(
    isolated_backend_server: Dict[str, Any],
) -> None:
    base_url = isolated_backend_server["base_url"]
    missing_id = "99999999-9999-4999-8999-999999999999"

    for fmt in ("csv", "json"):
        resp = httpx.get(
            f"{base_url}/api/v1/admin/encuestas/{missing_id}/exportar?formato={fmt}",
            timeout=10.0,
        )
        assert resp.status_code == 404
        assert "application/json" in resp.headers.get("content-type", "").lower()
        err = resp.json()
        assert err["code"] == "ENCUESTA_NO_ENCONTRADA"
        assert err["status"] == 404
        assert err["title"]
        assert err["detail"]


def test_f5_tier2_invalid_query_and_non_admin_route(
    isolated_backend_server: Dict[str, Any],
) -> None:
    base_url = isolated_backend_server["base_url"]

    bad_fmt = httpx.get(
        f"{base_url}/api/v1/admin/encuestas/{CANONICAL_SURVEY_ID}/exportar?formato=xml",
        timeout=10.0,
    )
    assert bad_fmt.status_code == 422
    assert bad_fmt.json()["code"] == "VALIDATION_ERROR"

    bad_uuid = httpx.get(
        f"{base_url}/api/v1/admin/encuestas/not-a-uuid/exportar?formato=csv",
        timeout=10.0,
    )
    assert bad_uuid.status_code == 422

    wrong_prefix = httpx.get(
        f"{base_url}/api/v1/encuestas/{CANONICAL_SURVEY_ID}/exportar?formato=csv",
        timeout=10.0,
    )
    assert wrong_prefix.status_code == 404


def test_f5_tier2_large_batch_multichunk_utf8_streaming(
    isolated_backend_server: Dict[str, Any],
) -> None:
    """Seed >1,200 rows (exceeding batch_size=500) and verify multi-chunk UTF-8 streaming."""
    base_url = isolated_backend_server["base_url"]
    db_path: Path = isolated_backend_server["db_path"]
    survey_id = _create_survey(base_url, "bulk_stream")

    total_rows = 1250
    base_dt = datetime(2026, 1, 1, 8, 0, 0, tzinfo=timezone.utc)
    records = []
    for i in range(total_rows):
        ts = (base_dt + timedelta(seconds=i)).isoformat()
        datos = json.dumps(
            {
                "parroquia": "san_simon",
                "comunidad_sector": f"Sector Maturín Ñ-{i} años",
                "observaciones_generales": f"Observación José #{i}: señalización peatonal",
            },
            ensure_ascii=False,
        )
        records.append((survey_id, str(uuid.uuid4()), None, "san_simon", "Z-01", datos, ts))

    with sqlite3.connect(db_path) as conn:
        conn.executemany(
            "INSERT INTO respuestas_ciudadanas "
            "(encuesta_id, client_submission_id, cedula, parroquia, zona_od, datos, fecha_registro) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            records,
        )
        conn.commit()

    # Stream CSV in raw chunks
    with httpx.Client(timeout=30.0) as client:
        with client.stream(
            "GET",
            f"{base_url}/api/v1/admin/encuestas/{survey_id}/exportar?formato=csv&redact_pii=true",
        ) as resp_csv:
            assert resp_csv.status_code == 200
            assert resp_csv.headers.get("transfer-encoding", "").lower() == "chunked"
            csv_chunks = [chunk for chunk in resp_csv.iter_bytes(chunk_size=4096) if chunk]
            assert len(csv_chunks) > 1, "Expected multi-chunk HTTP streaming for 1,250 CSV rows"
            csv_text = b"".join(csv_chunks).decode("utf-8")
            parsed_csv = list(csv.DictReader(io.StringIO(csv_text)))
            assert len(parsed_csv) == total_rows
            assert "Maturín" in parsed_csv[0]["datos_json"]
            assert "años" in parsed_csv[0]["datos_json"]

        # Stream JSON in raw chunks
        with client.stream(
            "GET",
            f"{base_url}/api/v1/admin/encuestas/{survey_id}/exportar?formato=json&redact_pii=false",
        ) as resp_json:
            assert resp_json.status_code == 200
            assert resp_json.headers.get("transfer-encoding", "").lower() == "chunked"
            json_chunks = [chunk for chunk in resp_json.iter_bytes(chunk_size=4096) if chunk]
            assert len(json_chunks) > 1, "Expected multi-chunk HTTP streaming for 1,250 JSON rows"
            json_text = b"".join(json_chunks).decode("utf-8")
            parsed_json = json.loads(json_text)
            assert len(parsed_json) == total_rows
            assert "José" in parsed_json[-1]["datos"]["observaciones_generales"]


# ---------------------------------------------------------------------------
# Feature F6 — question_analytics.py facade & /preguntas-metricas
# ---------------------------------------------------------------------------


def test_f6_question_analytics_facade_exports_and_metrics_count() -> None:
    script = (
        "from backend.app.services.question_analytics import ("
        "aggregate_all_survey_questions, COMMON_LABELS, CUSTOM_FIELD_LABELS, "
        "QUESTIONS_METRIC_CONFIG, _build_options_lookup, _humanize_value"
        "); "
        "assert isinstance(COMMON_LABELS, dict) and len(COMMON_LABELS) > 10; "
        "assert isinstance(CUSTOM_FIELD_LABELS, dict) and len(CUSTOM_FIELD_LABELS) >= 10; "
        "assert isinstance(QUESTIONS_METRIC_CONFIG, list) and len(QUESTIONS_METRIC_CONFIG) == 61; "
        "assert callable(_build_options_lookup) and callable(_humanize_value) and callable(aggregate_all_survey_questions); "
        "opts = _build_options_lookup({'components': [{'key': 'parroquia', 'data': {'values': [{'value': 'san_simon', 'label': 'San Simón'}]}}]}, ); "
        "assert _humanize_value('parroquia', 'san_simon', opts) == 'San Simón'; "
        "print('OK:', len(QUESTIONS_METRIC_CONFIG))"
    )
    res = subprocess.run(
        [str(PYTHON_BIN), "-c", script],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, f"Facade import check failed:\n{res.stdout}\n{res.stderr}"
    assert "OK: 61" in res.stdout


def test_f6_preguntas_metricas_populated_humanized_labels_and_buckets(
    isolated_backend_server: Dict[str, Any],
) -> None:
    base_url = isolated_backend_server["base_url"]
    survey_id = _create_survey(base_url, "analytics_pop")

    p1 = build_full_citizen_payload(cedula="14111222", parroquia="san_simon")
    p1["data"]["residentes"] = [
        {"persona_numero": 1, "edad": 25, "sexo": "1", "nivel_educativo": "universitario"}
    ]
    p1["data"]["viajes"] = [
        {"viaje_numero": 1, "persona_numero": 1, "modo_principal": "6", "motivo_viaje": "1", "tiempo_viaje_min": 20, "costo_viaje_bs": 0}
    ]

    p2 = build_full_citizen_payload(cedula="14333444", parroquia="boqueron")
    p2["data"]["residentes"] = [
        {"persona_numero": 1, "edad": 70, "sexo": "2", "nivel_educativo": "secundaria"}
    ]
    p2["data"]["viajes"] = [
        {"viaje_numero": 1, "persona_numero": 1, "modo_principal": "1", "motivo_viaje": "2", "tiempo_viaje_min": 45, "costo_viaje_bs": 20}
    ]

    for payload in (p1, p2):
        r = httpx.post(
            f"{base_url}/api/v1/encuestas/{survey_id}/respuestas",
            json=payload,
            timeout=10.0,
        )
        assert r.status_code == 201, r.text

    resp = httpx.get(
        f"{base_url}/api/v1/encuestas/{survey_id}/preguntas-metricas",
        timeout=10.0,
    )
    assert resp.status_code == 200
    metrics = resp.json()
    assert len(metrics) == 61

    by_clave = {m["clave"]: m for m in metrics}
    for m in metrics:
        assert m["tipo_grafico"] in {"bar", "donut"}
        assert len(m["labels"]) == len(m["values"])
        assert m["values"] == sorted(m["values"], reverse=True)

    assert "San Simón" in by_clave["parroquia"]["labels"]
    assert "Boquerón" in by_clave["parroquia"]["labels"]
    assert by_clave["parroquia"]["total_respuestas"] == 2
    assert "18 a 35 años" in by_clave["edad_residentes"]["labels"]
    assert "Mayor de 65 años" in by_clave["edad_residentes"]["labels"]
    assert "0 Bs (Gratuito / A pie)" in by_clave["costo_viaje_rangos"]["labels"]


def test_f6_tier2_preguntas_metricas_empty_survey(
    isolated_backend_server: Dict[str, Any],
) -> None:
    base_url = isolated_backend_server["base_url"]
    survey_id = _create_survey(base_url, "analytics_empty")

    resp = httpx.get(
        f"{base_url}/api/v1/encuestas/{survey_id}/preguntas-metricas",
        timeout=10.0,
    )
    assert resp.status_code == 200
    metrics = resp.json()
    assert len(metrics) == 61
    for m in metrics:
        assert m["total_respuestas"] == 0
        assert m["labels"] == []
        assert m["values"] == []


def test_f6_tier2_preguntas_metricas_malformed_numeric_fields_no_500(
    isolated_backend_server: Dict[str, Any],
) -> None:
    base_url = isolated_backend_server["base_url"]
    db_path: Path = isolated_backend_server["db_path"]
    survey_id = _create_survey(base_url, "analytics_malformed")

    corrupt_datos = json.dumps(
        {
            "parroquia": "san_simon",
            "residentes": [{"edad": "no_numerica", "sexo": {"value": "1"}}],
            "viajes": [{"tiempo_viaje_min": "abc", "costo_viaje_bs": "xyz", "modo_principal": None}],
            "actividades_parques": ["caminar", "deporte"],
        }
    )
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO respuestas_ciudadanas (encuesta_id, parroquia, datos) VALUES (?, ?, ?)",
            (survey_id, "san_simon", corrupt_datos),
        )
        conn.commit()

    resp = httpx.get(
        f"{base_url}/api/v1/encuestas/{survey_id}/preguntas-metricas",
        timeout=10.0,
    )
    assert resp.status_code == 200
    metrics = resp.json()
    assert len(metrics) == 61


def test_f6_tier2_preguntas_metricas_unknown_and_invalid_survey(
    isolated_backend_server: Dict[str, Any],
) -> None:
    base_url = isolated_backend_server["base_url"]

    missing = httpx.get(
        f"{base_url}/api/v1/encuestas/99999999-9999-4999-8999-999999999999/preguntas-metricas",
        timeout=10.0,
    )
    assert missing.status_code == 404
    assert missing.json()["code"] == "ENCUESTA_NO_ENCONTRADA"

    invalid = httpx.get(
        f"{base_url}/api/v1/encuestas/invalid-uuid/preguntas-metricas",
        timeout=10.0,
    )
    assert invalid.status_code == 422
