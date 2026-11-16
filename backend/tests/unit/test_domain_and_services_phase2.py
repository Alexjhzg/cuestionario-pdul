from pathlib import Path
import uuid
import pytest

from backend.app.api.error_handlers import domain_error_to_problem
from backend.app.domain.entities import CitizenSubmission, Survey
from backend.app.domain.exceptions import (
    DuplicateCedulaError,
    DuplicateSlugError,
    PersistenceUnavailableError,
    RestrictedPiiFieldError,
    SurveyInactiveError,
    SurveyNotFoundError,
)
from backend.app.domain.value_objects import Cedula, Parroquia, Trip
from backend.app.schemas.encuesta import EncuestaCreate
from backend.app.services.admin_service import AdminService
from backend.app.services.analytics_service import AnalyticsService


def test_value_objects_validation_and_normalization():
    ced = Cedula("V-14.852.963")
    assert str(ced) == "14852963"
    assert Cedula.from_optional("   ") is None
    with pytest.raises(ValueError):
        Cedula("123")

    parr = Parroquia("San Simón")
    assert str(parr) == "san_simon"
    assert parr.is_official is True

    custom_parr = Parroquia("Sector Nuevo")
    assert str(custom_parr) == "Sector Nuevo"
    assert custom_parr.is_official is False

    trip = Trip(
        zona_od_origen="ZONA_01",
        zona_od_destino="ZONA_02",
        modo_principal="6",
        tiempo_viaje_min=20,
        costo_viaje_bs=15.0,
    )
    assert trip.tiempo_viaje_min == 20
    with pytest.raises(ValueError):
        Trip("ZONA_01", "ZONA_02", "6", tiempo_viaje_min=0)
    with pytest.raises(ValueError):
        Trip("ZONA_01", "ZONA_02", "6", costo_viaje_bs=-1)


def test_survey_entity_rejects_submissions_when_inactive():
    survey = Survey(
        id=uuid.uuid4(),
        titulo="Test",
        slug="test",
        tipo_instrumento="consulta_ciudadana",
        activa=False,
    )
    with pytest.raises(SurveyInactiveError):
        survey.ensure_accepts_submissions()

    sub = CitizenSubmission(encuesta_id=survey.id, parroquia="san_simon")
    assert sub.parroquia == "san_simon"


def test_domain_error_to_problem_maps_rfc7807_codes():
    cases = [
        (SurveyNotFoundError("abc"), 404, "ENCUESTA_NO_ENCONTRADA"),
        (SurveyInactiveError(), 400, "ENCUESTA_INACTIVA"),
        (DuplicateCedulaError(), 409, "CEDULA_DUPLICADA"),
        (DuplicateSlugError("slug-x"), 409, "CONFLICT"),
        (RestrictedPiiFieldError("cedula"), 400, "CAMPO_PII_RESTRINGIDO"),
        (PersistenceUnavailableError(), 503, "DATABASE_UNAVAILABLE"),
    ]
    for exc, expected_status, expected_code in cases:
        http_status, problem = domain_error_to_problem(exc)
        assert http_status == expected_status
        assert problem.status == expected_status
        assert problem.code == expected_code


@pytest.mark.asyncio
async def test_admin_service_duplicate_slug_and_not_found_raise_domain_errors(mock_uow):
    service = AdminService(mock_uow)

    mock_uow.surveys.get_by_slug.return_value = object()
    with pytest.raises(DuplicateSlugError):
        await service.create_survey(
            EncuestaCreate(
                titulo="Duplicada",
                slug="ya-existe",
                esquema_formio={"components": []},
            )
        )

    mock_uow.surveys.get_by_id.return_value = None
    with pytest.raises(SurveyNotFoundError):
        await service.get_survey(uuid.uuid4())


@pytest.mark.asyncio
async def test_analytics_service_requires_existing_survey(mock_uow):
    service = AnalyticsService(mock_uow)
    mock_uow.surveys.get_by_id.return_value = None

    with pytest.raises(SurveyNotFoundError):
        await service.get_kpis(uuid.uuid4())


def test_clean_architecture_no_fastapi_or_session_leak_in_domain_and_services():
    app_dir = Path(__file__).resolve().parents[2] / "app"

    for layer in ("domain", "services"):
        for py_file in (app_dir / layer).rglob("*.py"):
            content = py_file.read_text(encoding="utf-8")
            assert "fastapi" not in content.lower(), f"FastAPI import detectado en {py_file}"
            assert "session.commit" not in content, f"session.commit detectado en {py_file}"
            assert "session.rollback" not in content, f"session.rollback detectado en {py_file}"

    db_content = (app_dir / "core" / "database.py").read_text(encoding="utf-8")
    assert "backend.app.main" not in db_content
    assert "seed_default_pdul_survey" not in db_content
