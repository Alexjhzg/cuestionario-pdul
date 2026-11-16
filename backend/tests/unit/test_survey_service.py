import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from backend.app.models.encuesta import Encuesta
from backend.app.schemas.submission import FormioSubmissionIn
from backend.app.services.survey_service import SurveyService


@pytest.mark.asyncio
async def test_register_participation_new_submission_success(
    mock_survey_repo, mock_encuesta_repo, sample_valid_submission_payload
):
    encuesta_id = uuid.uuid4()
    mock_encuesta = MagicMock(spec=Encuesta)
    mock_encuesta.id = encuesta_id
    mock_encuesta.activa = True
    mock_encuesta_repo.get_by_id.return_value = mock_encuesta

    mock_survey_repo.get_by_client_submission_id.return_value = None
    mock_survey_repo.get_by_encuesta_and_cedula.return_value = None
    mock_survey_repo.insert_submission.return_value = {
        "id": 42,
        "fecha_registro": datetime.now(),
    }

    service = SurveyService(mock_survey_repo, mock_encuesta_repo)
    submission = FormioSubmissionIn.model_validate(sample_valid_submission_payload)

    receipt = await service.register_participation(encuesta_id, submission)

    assert receipt.id == 42
    assert receipt.idempotent_replay is False
    assert "exitosamente" in receipt.mensaje
    mock_survey_repo.insert_submission.assert_called_once()
    mock_survey_repo.session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_register_participation_idempotent_replay(
    mock_survey_repo, mock_encuesta_repo, sample_valid_submission_payload
):
    encuesta_id = uuid.uuid4()
    mock_encuesta = MagicMock(spec=Encuesta)
    mock_encuesta.id = encuesta_id
    mock_encuesta.activa = True
    mock_encuesta_repo.get_by_id.return_value = mock_encuesta

    existing_dt = datetime.now()
    mock_survey_repo.get_by_client_submission_id.return_value = {
        "id": 99,
        "fecha_registro": existing_dt,
    }

    service = SurveyService(mock_survey_repo, mock_encuesta_repo)
    submission = FormioSubmissionIn.model_validate(sample_valid_submission_payload)

    receipt = await service.register_participation(encuesta_id, submission)

    assert receipt.id == 99
    assert receipt.idempotent_replay is True
    assert "previamente" in receipt.mensaje
    # No debe llamar a insertar de nuevo
    mock_survey_repo.insert_submission.assert_not_called()


@pytest.mark.asyncio
async def test_register_participation_duplicate_cedula_raises_409(
    mock_survey_repo, mock_encuesta_repo, sample_valid_submission_payload
):
    encuesta_id = uuid.uuid4()
    mock_encuesta = MagicMock(spec=Encuesta)
    mock_encuesta.id = encuesta_id
    mock_encuesta.activa = True
    mock_encuesta_repo.get_by_id.return_value = mock_encuesta

    mock_survey_repo.get_by_client_submission_id.return_value = None
    mock_survey_repo.get_by_encuesta_and_cedula.return_value = {"id": 10}

    service = SurveyService(mock_survey_repo, mock_encuesta_repo)
    submission = FormioSubmissionIn.model_validate(sample_valid_submission_payload)

    with pytest.raises(HTTPException) as exc_info:
        await service.register_participation(encuesta_id, submission)

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail["code"] == "CEDULA_DUPLICADA"
    assert exc_info.value.detail["field"] == "cedula"


@pytest.mark.asyncio
async def test_register_participation_integrity_error_raises_409(
    mock_survey_repo, mock_encuesta_repo, sample_valid_submission_payload
):
    encuesta_id = uuid.uuid4()
    mock_encuesta = MagicMock(spec=Encuesta)
    mock_encuesta.id = encuesta_id
    mock_encuesta.activa = True
    mock_encuesta_repo.get_by_id.return_value = mock_encuesta

    mock_survey_repo.get_by_client_submission_id.return_value = None
    mock_survey_repo.get_by_encuesta_and_cedula.return_value = None
    mock_survey_repo.insert_submission.side_effect = IntegrityError(
        "duplicate key uq_voto_ciudadano", params={}, orig=Exception()
    )

    service = SurveyService(mock_survey_repo, mock_encuesta_repo)
    submission = FormioSubmissionIn.model_validate(sample_valid_submission_payload)

    with pytest.raises(HTTPException) as exc_info:
        await service.register_participation(encuesta_id, submission)

    assert exc_info.value.status_code == 409
    mock_survey_repo.session.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_register_participation_concurrent_race_idempotent_replay(
    mock_survey_repo, mock_encuesta_repo, sample_valid_submission_payload
):
    encuesta_id = uuid.uuid4()
    mock_encuesta = MagicMock(spec=Encuesta)
    mock_encuesta.id = encuesta_id
    mock_encuesta.activa = True
    mock_encuesta_repo.get_by_id.return_value = mock_encuesta

    # Primera comprobación antes del insert: None (aún no insertado por la otra transacción)
    # Segunda comprobación tras IntegrityError: ya existe (insertado concurrentemente)
    now_dt = datetime.now()
    mock_survey_repo.get_by_client_submission_id.side_effect = [
        None,
        {"id": 42, "fecha_registro": now_dt},
    ]
    mock_survey_repo.get_by_encuesta_and_cedula.return_value = None
    mock_survey_repo.insert_submission.side_effect = IntegrityError(
        "duplicate key client_submission_id", params={}, orig=Exception()
    )

    service = SurveyService(mock_survey_repo, mock_encuesta_repo)
    submission = FormioSubmissionIn.model_validate(sample_valid_submission_payload)

    receipt = await service.register_participation(encuesta_id, submission)

    assert receipt.id == 42
    assert receipt.idempotent_replay is True
    assert "previamente" in receipt.mensaje
    mock_survey_repo.session.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_register_participation_inactive_survey_rejection(
    mock_survey_repo, mock_encuesta_repo, sample_valid_submission_payload
):
    encuesta_id = uuid.uuid4()
    mock_encuesta = MagicMock(spec=Encuesta)
    mock_encuesta.id = encuesta_id
    mock_encuesta.activa = False
    mock_encuesta_repo.get_by_id.return_value = mock_encuesta

    service = SurveyService(mock_survey_repo, mock_encuesta_repo)
    submission = FormioSubmissionIn.model_validate(sample_valid_submission_payload)

    with pytest.raises(HTTPException) as exc_info:
        await service.register_participation(encuesta_id, submission)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["code"] == "ENCUESTA_INACTIVA"


@pytest.mark.asyncio
async def test_register_participation_not_found_survey_rejection(
    mock_survey_repo, mock_encuesta_repo, sample_valid_submission_payload
):
    encuesta_id = uuid.uuid4()
    mock_encuesta_repo.get_by_id.return_value = None

    service = SurveyService(mock_survey_repo, mock_encuesta_repo)
    submission = FormioSubmissionIn.model_validate(sample_valid_submission_payload)

    with pytest.raises(HTTPException) as exc_info:
        await service.register_participation(encuesta_id, submission)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail["code"] == "ENCUESTA_NO_ENCONTRADA"


@pytest.mark.asyncio
async def test_structured_logging_omits_cedula_and_pii(
    mock_survey_repo, mock_encuesta_repo, sample_valid_submission_payload
):
    encuesta_id = uuid.uuid4()
    mock_encuesta = MagicMock(spec=Encuesta)
    mock_encuesta.id = encuesta_id
    mock_encuesta.activa = True
    mock_encuesta_repo.get_by_id.return_value = mock_encuesta

    mock_survey_repo.get_by_client_submission_id.return_value = None
    mock_survey_repo.get_by_encuesta_and_cedula.return_value = None
    mock_survey_repo.insert_submission.return_value = {
        "id": 105,
        "fecha_registro": datetime.now(),
    }

    service = SurveyService(mock_survey_repo, mock_encuesta_repo)
    submission = FormioSubmissionIn.model_validate(sample_valid_submission_payload)

    with patch("backend.app.services.survey_service.logger.info") as mock_logger:
        await service.register_participation(encuesta_id, submission)
        mock_logger.assert_called_once()
        args, kwargs = mock_logger.call_args
        extra_data = kwargs.get("extra", {})

        # Asegurar que la cédula y datos personales NO están en el payload del log
        assert "cedula" not in extra_data
        assert "nombre_apellido" not in extra_data
        assert extra_data["encuesta_id"] == str(encuesta_id)
        assert extra_data["parroquia"] == "san_simon"
        assert extra_data["submission_id"] == 105
