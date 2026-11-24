import uuid
import pytest
from pydantic import ValidationError

from backend.app.schemas.problem import ProblemDetailOut
from backend.app.schemas.submission import FormioSubmissionIn
from backend.app.services.normalizers import (
    PARROQUIAS_MATURIN,
    normalize_cedula,
    normalize_parroquia,
)


def test_unwrap_formio_payload_with_data_wrapper():
    sub_id = uuid.uuid4()
    payload = {
        "client_submission_id": str(sub_id),
        "data": {
            "cedula": "V-14.852.963",
            "parroquia": "san_simon",
            "zona_residencia_od": "ZONA_01",
        },
    }
    submission = FormioSubmissionIn.model_validate(payload)
    assert submission.client_submission_id == sub_id
    assert submission.cedula_limpia == "14852963"
    assert submission.parroquia == "san_simon"
    assert submission.zona_od == "ZONA_01"
    assert submission.data["cedula"] == "14852963"


def test_unwrap_formio_payload_flat_dict():
    sub_id = uuid.uuid4()
    payload = {
        "client_submission_id": str(sub_id),
        "cedula": "18999888",
        "parroquia": "boqueron",
        "zona_residencia_od": "ZONA_03",
    }
    submission = FormioSubmissionIn.model_validate(payload)
    assert submission.client_submission_id == sub_id
    assert submission.cedula_limpia == "18999888"
    assert submission.parroquia == "boqueron"
    assert submission.zona_od == "ZONA_03"
    assert submission.data["cedula"] == "18999888"


def test_client_submission_id_extraction_from_inside_data():
    sub_id = uuid.uuid4()
    payload = {
        "data": {
            "client_submission_id": str(sub_id),
            "parroquia": "la_cruz",
        }
    }
    submission = FormioSubmissionIn.model_validate(payload)
    assert submission.client_submission_id == sub_id
    assert submission.parroquia == "la_cruz"


@pytest.mark.parametrize(
    "raw_input,expected",
    [
        ("V-12.345.678", "12345678"),
        ("E-1.234.567", "1234567"),
        ("v-98765432", "98765432"),
        (" 123456 ", "123456"),
        ("123456789", "123456789"),
    ],
)
def test_cedula_normalization_valid_formats(raw_input, expected):
    assert normalize_cedula(raw_input) == expected


@pytest.mark.parametrize("short_input", ["12345", "V-1234", "12", ""])
def test_cedula_rejection_invalid_length_too_short(short_input):
    if not short_input:
        assert normalize_cedula(short_input) is None
    else:
        with pytest.raises(ValueError, match="6 a 9 dígitos"):
            normalize_cedula(short_input)


@pytest.mark.parametrize("long_input", ["1234567890", "V-123.456.789.0", "123456789012"])
def test_cedula_rejection_invalid_length_too_long(long_input):
    with pytest.raises(ValueError, match="6 a 9 dígitos"):
        normalize_cedula(long_input)


def test_cedula_optional_for_pdul_household():
    payload = {
        "data": {
            "parroquia": "las_cocuizas",
            "zona_residencia_od": "ZONA_04",
        }
    }
    submission = FormioSubmissionIn.model_validate(payload)
    assert submission.cedula_limpia is None
    assert submission.parroquia == "las_cocuizas"


def test_parroquia_valid_catalog_acceptance():
    for p in PARROQUIAS_MATURIN:
        norm = normalize_parroquia(p)
        assert norm == p

    assert len(PARROQUIAS_MATURIN) == 11


@pytest.mark.parametrize(
    "raw_input,expected",
    [
        ("San Simón", "san_simon"),
        ("SAN SIMÓN", "san_simon"),
        ("Alto de Los Godos", "alto_de_los_godos"),
        ("ALTO DE LOS GODOS", "alto_de_los_godos"),
        ("Las Cocuizas", "las_cocuizas"),
        ("La Pica", "la_pica"),
        ("El Furrial", "el_furrial"),
    ],
)
def test_parroquia_case_insensitivity_and_accents(raw_input, expected):
    assert normalize_parroquia(raw_input) == expected


def test_parroquia_free_text_and_required():
    # Pregunta abierta: texto desconocido se conserva tal cual
    assert normalize_parroquia("Caracas") == "Caracas"
    assert normalize_parroquia("  Las Cocuizas ") == "las_cocuizas"

    with pytest.raises(ValueError, match="requerida"):
        normalize_parroquia(None)

    with pytest.raises(ValueError, match="requerida"):
        normalize_parroquia("   ")


def test_viajes_grid_validation_valid_and_invalid():
    # Viajes válidos
    payload_valid = {
        "data": {
            "parroquia": "santa_cruz",
            "viajes": [
                {
                    "zona_od_origen": "ZONA_01",
                    "zona_od_destino": "ZONA_02",
                    "tiempo_viaje_min": 20,
                }
            ],
        }
    }
    sub = FormioSubmissionIn.model_validate(payload_valid)
    assert len(sub.data["viajes"]) == 1

    # Tiempo negativo o cero
    payload_invalid_time = {
        "data": {
            "parroquia": "santa_cruz",
            "viajes": [
                {
                    "zona_od_origen": "ZONA_01",
                    "zona_od_destino": "ZONA_02",
                    "tiempo_viaje_min": 0,
                }
            ],
        }
    }
    with pytest.raises(ValidationError, match="mayor a 0"):
        FormioSubmissionIn.model_validate(payload_invalid_time)


def test_problem_detail_rfc7807_serialization():
    problem = ProblemDetailOut(
        code="TEST_ERROR",
        title="Test Error Summary",
        status=400,
        detail="A detailed message for the user",
        field="cedula",
    )
    dumped = problem.model_dump()
    assert dumped["code"] == "TEST_ERROR"
    assert dumped["title"] == "Test Error Summary"
    assert dumped["status"] == 400
    assert dumped["detail"] == "A detailed message for the user"
    assert dumped["field"] == "cedula"


def test_defensive_residentes_validations():
    # Edad fuera de rango (> 120)
    with pytest.raises(ValidationError, match="entre 0 y 120"):
        FormioSubmissionIn.model_validate(
            {"data": {"parroquia": "boqueron", "residentes": [{"edad": 135}]}}
        )

    # Edad negativa
    with pytest.raises(ValidationError, match="entre 0 y 120"):
        FormioSubmissionIn.model_validate(
            {"data": {"parroquia": "boqueron", "residentes": [{"edad": -2}]}}
        )

    # Menor de 16 años con licencia de conducir
    with pytest.raises(ValidationError, match="menor de 16 años"):
        FormioSubmissionIn.model_validate(
            {
                "data": {
                    "parroquia": "boqueron",
                    "residentes": [{"edad": 12, "posee_licencia": "si"}],
                }
            }
        )

    # Cantidad de vehículos inválida (< 1)
    with pytest.raises(ValidationError, match="al menos 1"):
        FormioSubmissionIn.model_validate(
            {
                "data": {
                    "parroquia": "boqueron",
                    "residentes": [{"edad": 30, "cantidad_vehiculo": 0}],
                }
            }
        )

    # Residente válido
    sub = FormioSubmissionIn.model_validate(
        {
            "data": {
                "parroquia": "boqueron",
                "residentes": [
                    {"edad": 30, "posee_licencia": "si", "cantidad_vehiculo": 1},
                    {"edad": 4, "posee_licencia": "no"},
                ],
            }
        }
    )
    assert len(sub.data["residentes"]) == 2


def test_defensive_viajes_gps_and_rutas_validations():
    # Costo negativo en viaje
    with pytest.raises(ValidationError, match="no puede ser negativo"):
        FormioSubmissionIn.model_validate(
            {
                "data": {
                    "parroquia": "san_simon",
                    "viajes": [{"tiempo_viaje_min": 15, "costo_viaje_bs": -5}],
                }
            }
        )

    # GPS incompleto o fuera de rango
    with pytest.raises(ValidationError, match="latitud como longitud"):
        FormioSubmissionIn.model_validate(
            {"data": {"parroquia": "san_simon", "gps_latitud": 9.74}}
        )
    with pytest.raises(ValidationError, match="fuera de rango"):
        FormioSubmissionIn.model_validate(
            {
                "data": {
                    "parroquia": "san_simon",
                    "gps_latitud": 95.0,
                    "gps_longitud": -63.18,
                }
            }
        )

    # rutas_tp_dia negativo
    with pytest.raises(ValidationError, match="no puede ser negativo"):
        FormioSubmissionIn.model_validate(
            {"data": {"parroquia": "san_simon", "rutas_tp_dia": -1}}
        )

    # Payload completo válido
    sub = FormioSubmissionIn.model_validate(
        {
            "data": {
                "parroquia": "san_simon",
                "gps_latitud": 9.7458,
                "gps_longitud": -63.1832,
                "viajes": [{"persona_numero": 1, "tiempo_viaje_min": 20, "costo_viaje_bs": 0}],
                "rutas_tp_dia": 0,
            }
        }
    )
    assert sub.parroquia == "san_simon"
