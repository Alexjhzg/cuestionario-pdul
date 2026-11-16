import json
import logging
import uuid
from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.bootstrap.seeder import seed_default_pdul_survey
from backend.app.core.config import settings
from sqlalchemy.ext.asyncio import async_sessionmaker


@pytest.mark.asyncio
async def test_phase4_full_system_integration_five_scenarios_and_clean_logs(
    async_client: AsyncClient,
    test_db_session: AsyncSession,
    caplog: pytest.LogCaptureFixture,
):
    """Valida interoperabilidad de extremo a extremo (Shared -> Backend -> SQL -> API)
    simulando los 5 perfiles operativos reales sin emitir logs ERROR/CRITICAL.
    """
    caplog.set_level(logging.INFO, logger="alcaldia.pdul")

    # 0. Seeding real desde shared/schemas/pdul_origen_destino.json
    session_factory = async_sessionmaker(
        bind=test_db_session.bind,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    await seed_default_pdul_survey(session_factory)

    # Confirmar catálogo canónico disponible vía endpoint público
    res_public = await async_client.get(f"/api/v1/encuestas/{settings.CANONICAL_SURVEY_SLUG}")
    assert res_public.status_code == 200
    pdul_meta = res_public.json()
    pdul_id = pdul_meta["id"]
    assert pdul_id == settings.CANONICAL_SURVEY_ID

    shared_schema = json.loads(Path(settings.DEFAULT_PDUL_SCHEMA_PATH).read_text(encoding="utf-8"))
    assert pdul_meta["esquema_formio"]["display"] == shared_schema["display"]

    # 1. Escenario 1: Estudiante universitario en San Simón (movilidad a pie)
    sub_student_id = str(uuid.uuid4())
    res_student = await async_client.post(
        f"/api/v1/encuestas/{pdul_id}/respuestas",
        json={
            "client_submission_id": sub_student_id,
            "data": {
                "cedula": "V-28.111.222",
                "parroquia": "san_simon",
                "zona_residencia_od": "ZONA_01",
                "tipo_vivienda": "apartamento",
                "calificacion_servicio_tp": "regular",
                "residentes": [
                    {"nombre_apellido": "Estudiante Prueba", "sexo": "1", "edad": 21, "medio_transporte_habitual": "3"}
                ],
                "viajes": [
                    {
                        "zona_od_origen": "ZONA_01",
                        "zona_od_destino": "ZONA_02",
                        "modo_principal": "3",
                        "tiempo_viaje_min": 18,
                        "costo_viaje_bs": 0,
                    }
                ],
            },
        },
    )
    assert res_student.status_code == 201
    assert res_student.json()["idempotent_replay"] is False

    # 2. Escenario 2: Familia multimodal en Boquerón
    res_family = await async_client.post(
        f"/api/v1/encuestas/{pdul_id}/respuestas",
        json={
            "client_submission_id": str(uuid.uuid4()),
            "data": {
                "cedula": "15999888",
                "parroquia": "boqueron",
                "zona_residencia_od": "ZONA_03",
                "tipo_vivienda": "quinta",
                "calificacion_servicio_tp": "bueno",
                "residentes": [
                    {"nombre_apellido": "Padre Familia", "sexo": "1", "edad": 44},
                    {"nombre_apellido": "Madre Familia", "sexo": "2", "edad": 42},
                ],
                "viajes": [
                    {
                        "zona_od_origen": "ZONA_03",
                        "zona_od_destino": "ZONA_01",
                        "modo_principal": "6",
                        "tiempo_viaje_min": 35,
                        "costo_viaje_bs": 20,
                    },
                    {
                        "zona_od_origen": "ZONA_01",
                        "zona_od_destino": "ZONA_03",
                        "modo_principal": "6",
                        "tiempo_viaje_min": 40,
                        "costo_viaje_bs": 20,
                    },
                ],
            },
        },
    )
    assert res_family.status_code == 201

    # 3. Escenario 3: Encuestador rural con sincronización offline + replay idempotente
    offline_batch_id = str(uuid.uuid4())
    offline_payload = {
        "client_submission_id": offline_batch_id,
        "data": {
            "cedula": "14222333",
            "parroquia": "el_corozo",
            "zona_residencia_od": "ZONA_05",
            "tipo_vivienda": "casa",
            "calificacion_servicio_tp": "malo",
            "residentes": [{"nombre_apellido": "Productor Rural", "sexo": "1", "edad": 50}],
            "viajes": [
                {
                    "zona_od_origen": "ZONA_05",
                    "zona_od_destino": "ZONA_01",
                    "modo_principal": "4",
                    "tiempo_viaje_min": 45,
                    "costo_viaje_bs": 35,
                }
            ],
        },
    }
    first_sync = await async_client.post(f"/api/v1/encuestas/{pdul_id}/respuestas", json=offline_payload)
    assert first_sync.status_code == 201
    assert first_sync.json()["idempotent_replay"] is False

    replay_sync = await async_client.post(f"/api/v1/encuestas/{pdul_id}/respuestas", json=offline_payload)
    assert replay_sync.status_code in (200, 201)
    assert replay_sync.json()["idempotent_replay"] is True
    assert replay_sync.json()["id"] == first_sync.json()["id"]

    # 4. Escenario 4: Administrador consulta respuestas y exporta CSV redactado (0 fugas PII)
    res_admin_list = await async_client.get(f"/api/v1/admin/encuestas/{pdul_id}/respuestas?skip=0&limit=10")
    assert res_admin_list.status_code == 200
    assert res_admin_list.json()["total"] == 3

    res_csv_redacted = await async_client.get(
        f"/api/v1/admin/encuestas/{pdul_id}/exportar?formato=csv&redact_pii=true"
    )
    assert res_csv_redacted.status_code == 200
    csv_text = res_csv_redacted.text
    for sensitive in ("28111222", "15999888", "14222333", "Estudiante Prueba", "Padre Familia", "Productor Rural"):
        assert sensitive not in csv_text

    # 5. Escenario 5: Dashboard analítico (KPIs, Parroquias, Modal Split, Matriz O-D)
    res_kpis = await async_client.get(f"/api/v1/encuestas/{pdul_id}/kpis")
    assert res_kpis.status_code == 200
    kpis = res_kpis.json()
    assert kpis["total_encuestas"] == 3
    assert kpis["total_residentes"] == 4
    assert kpis["total_viajes"] == 4

    res_parr = await async_client.get(f"/api/v1/encuestas/{pdul_id}/resultados-parroquia")
    assert res_parr.status_code == 200
    assert len(res_parr.json()) == 3

    res_modal = await async_client.get(f"/api/v1/encuestas/{pdul_id}/reparto-modal")
    assert res_modal.status_code == 200
    assert sum(item["total_viajes"] for item in res_modal.json()) == 4

    res_od = await async_client.get(f"/api/v1/encuestas/{pdul_id}/matriz-od")
    assert res_od.status_code == 200
    assert sum(item["total_viajes"] for item in res_od.json()) == 4

    # Cero registros ERROR o CRITICAL en logs estructurados del backend
    error_logs = [rec for rec in caplog.records if rec.levelno >= logging.ERROR]
    assert error_logs == []

