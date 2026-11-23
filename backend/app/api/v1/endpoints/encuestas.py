import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import (
    get_admin_service,
    get_encuesta_repo,
    get_survey_service,
)
from backend.app.core.database import get_db
from backend.app.models.comunidad import ComunidadCatalogo
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
    "/catalogo/comunidades",
    response_model=List[Dict[str, Any]],
    summary="Obtiene el catálogo de comunidades del Municipio Maturín filtrable por parroquia",
)
async def listar_catalogo_comunidades(
    parroquia: Optional[str] = Query(
        default=None,
        description="Slug de parroquia (ej. alto_de_los_godos, boqueron, san_simon) para filtrado en cascada",
    ),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    stmt = select(ComunidadCatalogo).order_by(ComunidadCatalogo.nombre.asc())
    if parroquia:
        par_norm = parroquia.strip().lower()
        if par_norm in ("la_cruz", "santa_cruz"):
            stmt = stmt.where(ComunidadCatalogo.parroquia.in_(["la_cruz", "santa_cruz"]))
        else:
            stmt = stmt.where(ComunidadCatalogo.parroquia == par_norm)
    rows = (await db.execute(stmt)).scalars().all()
    return [
        {
            "codigo": r.codigo,
            "nombre": r.nombre,
            "xpar": r.xpar,
            "parroquia": r.parroquia,
            "municipio_codigo": r.municipio_codigo,
            "municipio": r.municipio,
        }
        for r in rows
    ]


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
