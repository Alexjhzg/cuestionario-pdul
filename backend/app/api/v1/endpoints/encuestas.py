import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.repositories.encuesta_repo import EncuestaRepository
from backend.app.repositories.survey_repo import SurveyRepository
from backend.app.schemas.encuesta import EncuestaListItem, EncuestaOut
from backend.app.schemas.problem import ProblemDetailOut
from backend.app.schemas.submission import (
    FormioSubmissionIn,
    SubmissionReceiptOut,
)
from backend.app.services.admin_service import AdminService
from backend.app.services.survey_service import SurveyService

router = APIRouter()


def get_survey_service(db: AsyncSession = Depends(get_db)) -> SurveyService:
    return SurveyService(SurveyRepository(db), EncuestaRepository(db))


def get_admin_service(db: AsyncSession = Depends(get_db)) -> AdminService:
    return AdminService(EncuestaRepository(db), SurveyRepository(db))


def get_encuesta_repo(db: AsyncSession = Depends(get_db)) -> EncuestaRepository:
    return EncuestaRepository(db)


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
    repo: EncuestaRepository = Depends(get_encuesta_repo),
) -> EncuestaOut:
    encuesta = await repo.get_by_slug(slug)
    if not encuesta or not encuesta.activa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ProblemDetailOut(
                code="ENCUESTA_NO_ENCONTRADA",
                title="Encuesta no encontrada",
                status=404,
                detail=f"La encuesta con slug '{slug}' no existe o se encuentra inactiva.",
            ).model_dump(),
        )
    return EncuestaOut.model_validate(encuesta)


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
