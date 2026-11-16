import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoints(async_client: AsyncClient):
    resp = await async_client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"

    resp_v1 = await async_client.get("/api/v1/health")
    assert resp_v1.status_code == 200
    assert resp_v1.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_admin_create_and_get_survey(
    async_client: AsyncClient, sample_formio_schema
):
    unique_slug = f"test-encuesta-{uuid.uuid4().hex[:8]}"
    create_payload = {
        "titulo": "Encuesta de Prueba Movilidad",
        "slug": unique_slug,
        "tipo_instrumento": "consulta_ciudadana",
        "esquema_formio": sample_formio_schema,
        "activa": True,
    }

    # 1. Crear encuesta
    res_create = await async_client.post(
        "/api/v1/admin/encuestas", json=create_payload
    )
    assert res_create.status_code == 201
    created_data = res_create.json()
    encuesta_id = created_data["id"]
    assert created_data["slug"] == unique_slug
    assert created_data["activa"] is True

    # 2. Consultar por slug en endpoint público
    res_slug = await async_client.get(f"/api/v1/encuestas/{unique_slug}")
    assert res_slug.status_code == 200
    assert res_slug.json()["id"] == encuesta_id

    # 3. Listar encuestas en admin
    res_list = await async_client.get("/api/v1/admin/encuestas")
    assert res_list.status_code == 200
    items = res_list.json()
    assert any(item["id"] == encuesta_id for item in items)


@pytest.mark.asyncio
async def test_admin_toggle_active_status_endpoint(
    async_client: AsyncClient, sample_formio_schema
):
    unique_slug = f"test-toggle-{uuid.uuid4().hex[:8]}"
    create_payload = {
        "titulo": "Encuesta para desactivar",
        "slug": unique_slug,
        "tipo_instrumento": "consulta_ciudadana",
        "esquema_formio": sample_formio_schema,
        "activa": True,
    }
    res_create = await async_client.post(
        "/api/v1/admin/encuestas", json=create_payload
    )
    encuesta_id = res_create.json()["id"]

    # Desactivar encuesta
    res_patch = await async_client.patch(
        f"/api/v1/admin/encuestas/{encuesta_id}/estado", json={"activa": False}
    )
    assert res_patch.status_code == 200
    assert res_patch.json()["activa"] is False

    # Al consultar el slug público, debe retornar 404 porque está inactiva
    res_public = await async_client.get(f"/api/v1/encuestas/{unique_slug}")
    assert res_public.status_code == 404
    assert res_public.json()["code"] == "ENCUESTA_NO_ENCONTRADA"


@pytest.mark.asyncio
async def test_submission_lifecycle_and_idempotency(
    async_client: AsyncClient, sample_formio_schema, sample_valid_submission_payload
):
    unique_slug = f"test-sub-{uuid.uuid4().hex[:8]}"
    create_payload = {
        "titulo": "Encuesta Ciclo de Vida",
        "slug": unique_slug,
        "tipo_instrumento": "encuesta_od_pdul",
        "esquema_formio": sample_formio_schema,
        "activa": True,
    }
    res_create = await async_client.post(
        "/api/v1/admin/encuestas", json=create_payload
    )
    encuesta_id = res_create.json()["id"]

    # 1. Enviar primera respuesta válida -> 201 Created
    res_sub1 = await async_client.post(
        f"/api/v1/encuestas/{encuesta_id}/respuestas",
        json=sample_valid_submission_payload,
    )
    assert res_sub1.status_code == 201
    receipt1 = res_sub1.json()
    sub_id = receipt1["id"]
    assert receipt1["idempotent_replay"] is False

    # 2. Reenviar idéntico envío (mismo client_submission_id) -> 200 OK idempotente
    res_sub2 = await async_client.post(
        f"/api/v1/encuestas/{encuesta_id}/respuestas",
        json=sample_valid_submission_payload,
    )
    assert res_sub2.status_code == 200
    receipt2 = res_sub2.json()
    assert receipt2["id"] == sub_id
    assert receipt2["idempotent_replay"] is True

    # 3. Enviar otra respuesta con cédula repetida pero diferente client_submission_id -> 409 Conflict
    dup_payload = {
        "client_submission_id": str(uuid.uuid4()),
        "data": {
            "cedula": sample_valid_submission_payload["data"]["cedula"],
            "parroquia": "boqueron",
        },
    }
    res_sub3 = await async_client.post(
        f"/api/v1/encuestas/{encuesta_id}/respuestas", json=dup_payload
    )
    assert res_sub3.status_code == 409
    detail = res_sub3.json()
    assert detail["code"] == "CEDULA_DUPLICADA"
    assert detail["field"] == "cedula"


@pytest.mark.asyncio
async def test_submission_validation_error_parroquia(
    async_client: AsyncClient, sample_formio_schema
):
    unique_slug = f"test-val-{uuid.uuid4().hex[:8]}"
    create_payload = {
        "titulo": "Encuesta Validación",
        "slug": unique_slug,
        "tipo_instrumento": "consulta_ciudadana",
        "esquema_formio": sample_formio_schema,
        "activa": True,
    }
    res_create = await async_client.post(
        "/api/v1/admin/encuestas", json=create_payload
    )
    encuesta_id = res_create.json()["id"]

    bad_payload = {
        "data": {
            "cedula": "12345678",
            "parroquia": "   ",
        }
    }
    res = await async_client.post(
        f"/api/v1/encuestas/{encuesta_id}/respuestas", json=bad_payload
    )
    assert res.status_code == 422
    err_json = res.json()
    assert err_json["code"] == "VALIDATION_ERROR"
    assert err_json["status"] == 422


@pytest.mark.asyncio
async def test_analytics_endpoints(
    async_client: AsyncClient, sample_formio_schema, sample_valid_submission_payload
):
    unique_slug = f"test-analytics-{uuid.uuid4().hex[:8]}"
    create_payload = {
        "titulo": "Encuesta Analítica",
        "slug": unique_slug,
        "tipo_instrumento": "encuesta_od_pdul",
        "esquema_formio": sample_formio_schema,
        "activa": True,
    }
    res_create = await async_client.post(
        "/api/v1/admin/encuestas", json=create_payload
    )
    encuesta_id = res_create.json()["id"]

    # Registrar dos respuestas en parroquias distintas
    await async_client.post(
        f"/api/v1/encuestas/{encuesta_id}/respuestas",
        json=sample_valid_submission_payload,
    )

    sub2 = {
        "client_submission_id": str(uuid.uuid4()),
        "data": {
            "cedula": "98765432",
            "parroquia": "las_cocuizas",
            "tipo_vivienda": "quinta",
            "viajes": [
                {
                    "zona_od_origen": "ZONA_03",
                    "zona_od_destino": "ZONA_01",
                    "motivo_viaje": "2",
                    "modo_principal": "1",
                    "tiempo_viaje_min": 15,
                    "costo_viaje_bs": 0,
                }
            ],
        },
    }
    await async_client.post(
        f"/api/v1/encuestas/{encuesta_id}/respuestas", json=sub2
    )

    # 1. Resultados Parroquia (Leaflet)
    res_parroquia = await async_client.get(
        f"/api/v1/encuestas/{encuesta_id}/resultados-parroquia"
    )
    assert res_parroquia.status_code == 200
    parroquias_data = res_parroquia.json()
    assert len(parroquias_data) >= 2
    for item in parroquias_data:
        assert "parroquia" in item
        assert "total_respuestas" in item
        assert "porcentaje" in item
        # Sin PII
        assert "cedula" not in item

    # 2. Métricas ECharts (por campo)
    res_metricas = await async_client.get(
        f"/api/v1/encuestas/{encuesta_id}/metricas?campo=tipo_vivienda"
    )
    assert res_metricas.status_code == 200
    metricas = res_metricas.json()
    assert metricas["campo"] == "tipo_vivienda"
    assert "quinta" in metricas["labels"]
    assert metricas["values"][metricas["labels"].index("quinta")] == 2

    # 3. Matriz Origen-Destino
    res_od = await async_client.get(f"/api/v1/encuestas/{encuesta_id}/matriz-od")
    assert res_od.status_code == 200
    od_rows = res_od.json()
    assert len(od_rows) >= 1
    assert "zona_origen" in od_rows[0]
    assert "zona_destino" in od_rows[0]
    assert "total_viajes" in od_rows[0]

    # 4. Reparto Modal
    res_modal = await async_client.get(
        f"/api/v1/encuestas/{encuesta_id}/reparto-modal"
    )
    assert res_modal.status_code == 200
    modos = res_modal.json()
    assert len(modos) >= 1
    assert "modo" in modos[0]
    assert "etiqueta" in modos[0]
    assert "total_viajes" in modos[0]

    # 5. KPIs
    res_kpis = await async_client.get(f"/api/v1/encuestas/{encuesta_id}/kpis")
    assert res_kpis.status_code == 200
    kpis = res_kpis.json()
    assert kpis["total_encuestas"] == 2
    assert kpis["total_viajes"] >= 3


@pytest.mark.asyncio
async def test_admin_export_json_and_csv(
    async_client: AsyncClient, sample_formio_schema, sample_valid_submission_payload
):
    unique_slug = f"test-export-{uuid.uuid4().hex[:8]}"
    create_payload = {
        "titulo": "Encuesta Exportación",
        "slug": unique_slug,
        "tipo_instrumento": "consulta_ciudadana",
        "esquema_formio": sample_formio_schema,
        "activa": True,
    }
    res_create = await async_client.post(
        "/api/v1/admin/encuestas", json=create_payload
    )
    encuesta_id = res_create.json()["id"]

    await async_client.post(
        f"/api/v1/encuestas/{encuesta_id}/respuestas",
        json=sample_valid_submission_payload,
    )

    # Exportación JSON con redact_pii=True
    res_json_redacted = await async_client.get(
        f"/api/v1/admin/encuestas/{encuesta_id}/exportar?formato=json&redact_pii=true"
    )
    assert res_json_redacted.status_code == 200
    data = res_json_redacted.json()
    assert len(data) == 1
    assert "cedula" not in data[0]
    assert "nombre_apellido" not in data[0]["datos"]

    # Exportación CSV
    res_csv = await async_client.get(
        f"/api/v1/admin/encuestas/{encuesta_id}/exportar?formato=csv&redact_pii=false"
    )
    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.headers["content-type"]
    csv_text = res_csv.text
    assert "parroquia" in csv_text
    assert "san_simon" in csv_text


@pytest.mark.asyncio
async def test_metricas_endpoint_blocks_pii_fields(
    async_client: AsyncClient, sample_formio_schema, sample_valid_submission_payload
):
    unique_slug = f"test-pii-block-{uuid.uuid4().hex[:8]}"
    create_payload = {
        "titulo": "Encuesta Bloqueo PII",
        "slug": unique_slug,
        "tipo_instrumento": "encuesta_od_pdul",
        "esquema_formio": sample_formio_schema,
        "activa": True,
    }
    res_create = await async_client.post(
        "/api/v1/admin/encuestas", json=create_payload
    )
    assert res_create.status_code == 201
    encuesta_id = res_create.json()["id"]

    # Registrar respuesta con PII
    sub_payload = {
        "client_submission_id": str(uuid.uuid4()),
        "data": {
            "cedula": "12345678",
            "nombre_apellido": "Ciudadano Confidencial",
            "telefono": "0414-1234567",
            "correo": "ciudadano@alcaldia.gob.ve",
            "casa_apartamento": "Casa 99",
            "parroquia": "san_simon",
            "zona_residencia_od": "ZONA_01",
        },
    }
    res_sub = await async_client.post(
        f"/api/v1/encuestas/{encuesta_id}/respuestas", json=sub_payload
    )
    assert res_sub.status_code == 201

    # Verificar que consultar campos PII en /metricas es rechazado con HTTP 400 y CAMPO_PII_RESTRINGIDO
    pii_probes = ["cedula", "nombre_apellido", "telefono", "correo", "casa_apartamento"]
    for pii_field in pii_probes:
        res_pii = await async_client.get(
            f"/api/v1/encuestas/{encuesta_id}/metricas?campo={pii_field}"
        )
        assert res_pii.status_code == 400
        problem = res_pii.json()
        assert problem["code"] == "CAMPO_PII_RESTRINGIDO"
        assert problem["status"] == 400
        assert problem["field"] == "campo"
        assert pii_field in problem["detail"]
        # Ningún dato personal expuesto en el cuerpo de la respuesta
        assert "12345678" not in res_pii.text
        assert "Ciudadano Confidencial" not in res_pii.text
        assert "0414-1234567" not in res_pii.text


@pytest.mark.asyncio
async def test_get_survey_by_maturin_slug_resolves_and_aliases(
    async_client: AsyncClient, sample_formio_schema
):
    """Verifica que el slug canónico 'cuestionario-od-maturin' y el alias 'pdul_origen_destino' resuelven."""
    create_payload = {
        "titulo": "Encuesta Origen-Destino Maturín (PDUL)",
        "slug": "cuestionario-od-maturin",
        "tipo_instrumento": "encuesta_od_pdul",
        "esquema_formio": sample_formio_schema,
        "activa": True,
    }
    res_create = await async_client.post(
        "/api/v1/admin/encuestas", json=create_payload
    )
    assert res_create.status_code == 201
    encuesta_id = res_create.json()["id"]

    # 1. Consultar por slug canónico
    res_canonical = await async_client.get("/api/v1/encuestas/cuestionario-od-maturin")
    assert res_canonical.status_code == 200
    assert res_canonical.json()["id"] == encuesta_id

    # 2. Consultar por slug alternativo mediante fallback de alias
    res_alias = await async_client.get("/api/v1/encuestas/pdul_origen_destino")
    assert res_alias.status_code == 200
    assert res_alias.json()["id"] == encuesta_id


@pytest.mark.asyncio
async def test_submission_full_eight_step_payload_persists_successfully(
    async_client: AsyncClient, sample_formio_schema
):
    """Verifica el envío exitoso de un cuestionario completo de 8 pasos (R6)."""
    create_payload = {
        "titulo": "Encuesta Completa 8 Pasos PDUL",
        "slug": f"full-pdul-{uuid.uuid4().hex[:8]}",
        "tipo_instrumento": "encuesta_od_pdul",
        "esquema_formio": sample_formio_schema,
        "activa": True,
    }
    res_create = await async_client.post(
        "/api/v1/admin/encuestas", json=create_payload
    )
    assert res_create.status_code == 201
    encuesta_id = res_create.json()["id"]

    client_sub_id = str(uuid.uuid4())
    full_payload = {
        "client_submission_id": client_sub_id,
        "data": {
            # Paso 1: Ubicación
            "cedula": "V-19.876.543",
            "parroquia": "las_cocuizas",
            "sector_barrio": "La Floresta",
            "zona_residencia_od": "ZONA_04",
            # Paso 2: Vivienda y servicios
            "tipo_vivienda": "1",
            "condicion_ocupacion": "1",
            "agua_consumo": "1",
            # Paso 3: Equipamiento
            "vehiculos_particulares": 1,
            "motocicletas": 0,
            "bicicletas": 2,
            # Paso 4: Residentes
            "residentes": [
                {
                    "persona_numero": 1,
                    "nombres": "Jefe de Familia",
                    "parentesco": "1",
                    "sexo": "1",
                    "edad": 45,
                    "nivel_educativo": "4",
                    "actividad_principal": "1",
                },
                {
                    "persona_numero": 2,
                    "nombres": "Hijo",
                    "parentesco": "3",
                    "sexo": "1",
                    "edad": 18,
                    "nivel_educativo": "3",
                    "actividad_principal": "2",
                },
            ],
            # Paso 5: Viajes O-D
            "viajes": [
                {
                    "viaje_numero": 1,
                    "persona_numero": 1,
                    "zona_od_origen": "las_cocuizas",
                    "zona_od_destino": "san_simon",
                    "motivo_viaje": "1",
                    "modo_principal": "6",
                    "tiempo_viaje_min": 35,
                    "costo_viaje_bs": 15.0,
                },
                {
                    "viaje_numero": 2,
                    "persona_numero": 1,
                    "zona_od_origen": "san_simon",
                    "zona_od_destino": "las_cocuizas",
                    "motivo_viaje": "1",
                    "modo_principal": "6",
                    "tiempo_viaje_min": 40,
                    "costo_viaje_bs": 15.0,
                },
            ],
            # Paso 6: Transporte público
            "utiliza_tp": "si",
            "tiempo_espera_promedio": 25,
            "calificacion_servicio_tp": "regular",
            # Paso 7: Movilidad activa
            "frecuencia_caminata": "todos_los_dias",
            "condicion_aceras": "regular",
            # Paso 8: Cierre
            "observaciones_generales": "Se requieren mejores unidades y mayor frecuencia en La Floresta.",
            "acepta_declaracion": True,
        },
    }

    # Enviar respuesta
    res_sub = await async_client.post(
        f"/api/v1/encuestas/{encuesta_id}/respuestas", json=full_payload
    )
    assert res_sub.status_code == 201
    receipt = res_sub.json()
    assert receipt["id"] > 0
    assert receipt["idempotent_replay"] is False
    assert receipt["fecha_registro"] is not None

    # Verificar que el folio o recibo generado refleja la persistencia
    res_admin = await async_client.get(f"/api/v1/admin/encuestas/{encuesta_id}/respuestas")
    assert res_admin.status_code == 200
    admin_data = res_admin.json()
    assert admin_data["total"] >= 1
    item = admin_data["items"][0]
    assert item["parroquia"] == "las_cocuizas"
    assert item["datos"]["residentes"][0]["nombres"] == "Jefe de Familia"

