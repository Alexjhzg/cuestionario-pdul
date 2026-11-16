import pytest

from backend.app.schemas.analytics import (
    EChartsSeriesOut,
    KpiMetricsOut,
    MatrizODRowOut,
    ParroquiaCountOut,
    RepartoModalRowOut,
)
from backend.app.services.normalizers import sanitize_pii

FORBIDDEN_PII_NAMES = {
    "cedula",
    "nombre_apellido",
    "nombres_apellidos",
    "nombre",
    "apellido",
    "telefono",
    "correo",
    "email",
    "casa_apartamento",
    "avenida_calle",
    "direccion_exacta",
}


def test_parroquia_counts_has_no_pii_columns():
    fields = set(ParroquiaCountOut.model_fields.keys())
    intersection = fields.intersection(FORBIDDEN_PII_NAMES)
    assert intersection == set(), f"ParroquiaCountOut expone PII: {intersection}"
    assert fields == {"parroquia", "total_respuestas", "porcentaje"}


def test_od_matrix_projection_excludes_personal_identities():
    fields = set(MatrizODRowOut.model_fields.keys())
    intersection = fields.intersection(FORBIDDEN_PII_NAMES)
    assert intersection == set(), f"MatrizODRowOut expone PII: {intersection}"
    assert fields == {
        "zona_origen",
        "zona_destino",
        "total_viajes",
        "tiempo_promedio_min",
        "costo_promedio_bs",
    }


def test_modal_split_projection_excludes_personal_identities():
    fields = set(RepartoModalRowOut.model_fields.keys())
    intersection = fields.intersection(FORBIDDEN_PII_NAMES)
    assert intersection == set(), f"RepartoModalRowOut expone PII: {intersection}"
    assert fields == {"modo", "etiqueta", "total_viajes", "porcentaje"}


def test_echarts_series_and_kpis_exclude_personal_identities():
    fields_echarts = set(EChartsSeriesOut.model_fields.keys())
    assert fields_echarts.intersection(FORBIDDEN_PII_NAMES) == set()

    fields_kpis = set(KpiMetricsOut.model_fields.keys())
    assert fields_kpis.intersection(FORBIDDEN_PII_NAMES) == set()


def test_sanitize_pii_scrubs_residential_identities_and_names():
    raw_citizen_data = {
        "cedula": "12345678",
        "nombre_apellido": "Carlos Mendoza",
        "parroquia": "san_simon",
        "telefono": "0414-1234567",
        "correo": "carlos@example.com",
        "casa_apartamento": "Casa #42",
        "avenida_calle": "Calle 10",
        "tipo_vivienda": "casa",
        "residentes": [
            {
                "nombre_apellido": "María Mendoza",
                "sexo": "2",
                "edad": 30,
                "parentesco": "2",
            }
        ],
        "viajes": [
            {
                "zona_od_origen": "ZONA_01",
                "zona_od_destino": "ZONA_02",
                "motivo_viaje": "1",
                "modo_principal": "4",
            }
        ],
    }

    sanitized = sanitize_pii(raw_citizen_data)

    # Verificar que los campos PII fueron eliminados en la raíz
    for key in FORBIDDEN_PII_NAMES:
        assert key not in sanitized

    # Verificar campos no-PII conservados
    assert sanitized["parroquia"] == "san_simon"
    assert sanitized["tipo_vivienda"] == "casa"

    # Verificar sanitización recursiva en lista de residentes
    assert len(sanitized["residentes"]) == 1
    residente = sanitized["residentes"][0]
    assert "nombre_apellido" not in residente
    assert residente["sexo"] == "2"
    assert residente["edad"] == 30

    # Verificar viajes conservados
    assert len(sanitized["viajes"]) == 1
    assert sanitized["viajes"][0]["zona_od_origen"] == "ZONA_01"


@pytest.mark.asyncio
async def test_survey_service_get_field_metrics_rejects_all_pii_fields(mock_uow):
    import uuid
    from backend.app.domain.exceptions import RestrictedPiiFieldError
    from backend.app.services.normalizers import PII_FIELDS
    from backend.app.services.survey_service import SurveyService

    service = SurveyService(mock_uow)
    encuesta_id = uuid.uuid4()

    for pii_field in PII_FIELDS:
        with pytest.raises(RestrictedPiiFieldError) as exc_info:
            await service.get_field_metrics(encuesta_id, pii_field)
        assert exc_info.value.code == "CAMPO_PII_RESTRINGIDO"
        assert exc_info.value.field == "campo"
        assert pii_field in exc_info.value.message

    # El repositorio nunca debe ser consultado para campos prohibidos
    mock_uow.submissions.aggregate_field_series.assert_not_called()

