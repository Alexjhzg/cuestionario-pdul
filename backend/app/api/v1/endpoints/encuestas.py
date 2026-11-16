import uuid
from typing import List
from fastapi import APIRouter, Depends, Response, status

from backend.app.api.deps import (
    get_admin_service,
    get_encuesta_repo,
    get_survey_service,
)
from backend.app.schemas.encuesta import EncuestaListItem, EncuestaOut
from backend.app.schemas.problem import ProblemDetailOut
from backend.app.schemas.submission import (
    FormioSubmissionIn,
    SubmissionReceiptOut,
)
from backend.app.services.admin_service import AdminService
from backend.app.services.survey_service import SurveyService

router = APIRouter()

__all__ = [
    "get_admin_service",
    "get_encuesta_repo",
    "get_survey_service",
    "router",
]


@router.get(
    "",
    response_model=List[EncuestaListItem],
    summary="Lista las encuestas registradas para selección y analítica",
)
async def listar_encuestas(
    service: AdminService = Depends(get_admin_service),
) -> List[EncuestaListItem]:
    return await service.list_surveys()


@router.get(
    "/{slug}",
    response_model=EncuestaOut,
    summary="Obtiene el esquema Form.io de una encuesta activa por su slug",
    responses={
        404: {"model": ProblemDetailOut, "description": "Encuesta no encontrada o inactiva"}
    },
)
async def obtener_encuesta_activa(
    slug: str,
    service: SurveyService = Depends(get_survey_service),
) -> EncuestaOut:
    return await service.get_active_survey_by_slug(slug)


@router.post(
    "/{encuesta_id}/respuestas",
    response_model=SubmissionReceiptOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registra un envío de respuestas con soporte offline idempotente",
    responses={
        200: {"model": SubmissionReceiptOut, "description": "Reenvío idempotente exitoso"},
        201: {"model": SubmissionReceiptOut, "description": "Participación registrada"},
        400: {"model": ProblemDetailOut, "description": "Encuesta inactiva"},
        404: {"model": ProblemDetailOut, "description": "Encuesta no encontrada"},
        409: {"model": ProblemDetailOut, "description": "Cédula duplicada"},
        422: {"model": ProblemDetailOut, "description": "Error de validación del payload"},
    },
)
async def registrar_respuesta(
    encuesta_id: uuid.UUID,
    submission: FormioSubmissionIn,
    response: Response,
    service: SurveyService = Depends(get_survey_service),
) -> SubmissionReceiptOut:
    receipt = await service.register_participation(encuesta_id, submission)
    if receipt.idempotent_replay:
        response.status_code = status.HTTP_200_OK
    return receipt
