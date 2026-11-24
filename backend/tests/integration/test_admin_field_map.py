import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_admin_field_map_summary_and_submission_detail(
    async_client: AsyncClient, sample_formio_schema
):
    unique_slug = f"test-field-map-{uuid.uuid4().hex[:8]}"
    res_create = await async_client.post(
        "/api/v1/admin/encuestas",
        json={
            "titulo": "Encuesta Mapa Levantamiento",
            "slug": unique_slug,
            "tipo_instrumento": "encuesta_od_pdul",
            "esquema_formio": sample_formio_schema,
            "activa": True,
        },
    )
    assert res_create.status_code == 201
    encuesta_id = res_create.json()["id"]

    # 1. Respuesta con GPS preciso en Maturín + PII sensible
    r1 = await async_client.post(
        f"/api/v1/encuestas/{encuesta_id}/respuestas",
        json={
            "client_submission_id": str(uuid.uuid4()),
            "data": {
                "cedula": "V-14111222",
                "parroquia": "san_simon",
                "comunidad_sector": "CENTRO",
                "zona_residencia_od": "Casco Central",
                "avenida_calle": "Av. Bolívar Secreta 99",
                "casa_apartamento": "Casa Privada 7",
                "gps_latitud": 9.7458,
                "gps_longitud": -63.1832,
                "gps_precision": 12,
                "dispositivo_tipo": "movil",
                "residentes": [{"nombres": "Pedro Confidencial", "edad": 35}],
            },
        },
    )
    assert r1.status_code == 201
    id_maturin = r1.json()["id"]

    # 2. Respuesta fuera de Maturín (Caracas por IP) + baja precisión
    r2 = await async_client.post(
        f"/api/v1/encuestas/{encuesta_id}/respuestas",
        json={
            "client_submission_id": str(uuid.uuid4()),
            "data": {
                "cedula": "V-15222333",
                "parroquia": "boqueron",
                "comunidad_sector": "TIPURO",
                "zona_residencia_od": "Tipuro Norte",
                "gps_latitud": 10.4806,
                "gps_longitud": -66.9036,
                "gps_precision": 1800,
                "dispositivo_tipo": "escritorio",
            },
        },
    )
    assert r2.status_code == 201
    id_caracas = r2.json()["id"]

    # 3. Respuesta sin GPS
    r3 = await async_client.post(
        f"/api/v1/encuestas/{encuesta_id}/respuestas",
        json={
            "client_submission_id": str(uuid.uuid4()),
            "data": {
                "parroquia": "alto_de_los_godos",
                "comunidad_sector": "LOS GUARITOS",
                "zona_residencia_od": "Los Guaritos",
                "dispositivo_tipo": "tablet",
            },
        },
    )
    assert r3.status_code == 201

    # Consultar mapa de levantamiento
    res_map = await async_client.get(
        f"/api/v1/admin/encuestas/{encuesta_id}/mapa-levantamiento"
    )
    assert res_map.status_code == 200
    body = res_map.json()

    assert body["encuesta_id"] == encuesta_id
    assert body["total_respuestas"] == 3
    assert body["total_con_gps"] == 2
    assert body["total_sin_gps"] == 1
    assert body["porcentaje_cobertura_gps"] == 66.7
    assert body["total_alertas_ubicacion"] == 1
    assert len(body["puntos"]) == 2

    # Verificar que NO se filtra PII en el endpoint del mapa
    serialized = res_map.text
    assert "14111222" not in serialized
    assert "15222333" not in serialized
    assert "Av. Bolívar Secreta 99" not in serialized
    assert "Casa Privada 7" not in serialized
    assert "Pedro Confidencial" not in serialized

    pts_by_id = {p["id"]: p for p in body["puntos"]}
    assert pts_by_id[id_maturin]["calidad_ubicacion"] == "alta"
    assert pts_by_id[id_maturin]["dispositivo_tipo"] == "movil"
    assert pts_by_id[id_maturin]["motivo_alerta"] is None

    assert pts_by_id[id_caracas]["calidad_ubicacion"] == "alerta"
    assert pts_by_id[id_caracas]["dispositivo_tipo"] == "escritorio"
    assert "fuera del ámbito" in pts_by_id[id_caracas]["motivo_alerta"]

    # Consultar detalle individual de respuesta
    res_detail = await async_client.get(
        f"/api/v1/admin/encuestas/{encuesta_id}/respuestas/{id_maturin}"
    )
    assert res_detail.status_code == 200
    detail_json = res_detail.json()
    assert detail_json["id"] == id_maturin
    assert detail_json["parroquia"] == "san_simon"
    assert detail_json["datos"]["gps_latitud"] == 9.7458

    # Respuesta inexistente -> 404 RFC 7807
    res_missing = await async_client.get(
        f"/api/v1/admin/encuestas/{encuesta_id}/respuestas/99999999"
    )
    assert res_missing.status_code == 404
    assert res_missing.json()["code"] == "RESPUESTA_NO_ENCONTRADA"

