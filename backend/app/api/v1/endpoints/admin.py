import uuid
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse

from backend.app.api.deps import get_admin_service
from backend.app.schemas.encuesta import (
    EncuestaCreate,
    EncuestaEstadoUpdate,
    EncuestaListItem,
    EncuestaOut,
    EncuestaUpdate,
)
from backend.app.schemas.field_map import FieldMapSummaryOut
from backend.app.schemas.problem import ProblemDetailOut
from backend.app.services.admin_service import AdminService

router = APIRouter()


@router.get(
    "/encuestas",
    response_model=List[EncuestaListItem],
    summary="Lista todas las encuestas registradas con total de respuestas acumuladas",
)
async def listar_encuestas_admin(
    service: AdminService = Depends(get_admin_service),
) -> List[EncuestaListItem]:
    return await service.list_surveys()


@router.post(
    "/encuestas",
    response_model=EncuestaOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crea una nueva encuesta a partir del Form Builder",
    responses={
        201: {"model": EncuestaOut, "description": "Encuesta creada exitosamente"},
        409: {"model": ProblemDetailOut, "description": "El slug ya existe"},
    },
)
async def crear_encuesta_admin(
    encuesta_in: EncuestaCreate,
    service: AdminService = Depends(get_admin_service),
) -> EncuestaOut:
    return await service.create_survey(encuesta_in)


@router.get(
    "/encuestas/{encuesta_id}",
    response_model=EncuestaOut,
    summary="Detalle completo de una encuesta para edición en Form Builder",
    responses={404: {"model": ProblemDetailOut, "description": "Encuesta no encontrada"}},
)
async def obtener_encuesta_admin(
    encuesta_id: uuid.UUID,
    service: AdminService = Depends(get_admin_service),
) -> EncuestaOut:
    return await service.get_survey(encuesta_id)


@router.patch(
    "/encuestas/{encuesta_id}/estado",
    response_model=EncuestaOut,
    summary="Alterna el estado activa/inactiva de la encuesta",
    responses={404: {"model": ProblemDetailOut, "description": "Encuesta no encontrada"}},
)
async def alternar_estado_encuesta(
    encuesta_id: uuid.UUID,
    body: EncuestaEstadoUpdate,
    service: AdminService = Depends(get_admin_service),
) -> EncuestaOut:
    return await service.toggle_status(encuesta_id, body.activa)


@router.put(
    "/encuestas/{encuesta_id}",
    response_model=EncuestaOut,
    summary="Actualiza metadatos o esquema Form.io de una encuesta",
    responses={404: {"model": ProblemDetailOut, "description": "Encuesta no encontrada"}},
)
async def actualizar_encuesta_admin(
    encuesta_id: uuid.UUID,
    body: EncuestaUpdate,
    service: AdminService = Depends(get_admin_service),
) -> EncuestaOut:
    return await service.update_survey(encuesta_id, body)


@router.get(
    "/encuestas/{encuesta_id}/respuestas",
    summary="Lista paginada de respuestas recibidas para el panel de supervisión",
    responses={404: {"model": ProblemDetailOut, "description": "Encuesta no encontrada"}},
)
async def listar_respuestas_admin(
    encuesta_id: uuid.UUID,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    service: AdminService = Depends(get_admin_service),
) -> Dict[str, Any]:
    return await service.list_submissions(encuesta_id, skip=skip, limit=limit)


@router.get(
    "/encuestas/{encuesta_id}/mapa-levantamiento",
    response_model=FieldMapSummaryOut,
    summary="Obtiene puntos georreferenciados no-PII y métricas de cobertura GPS de campo",
    responses={404: {"model": ProblemDetailOut, "description": "Encuesta no encontrada"}},
)
async def obtener_mapa_levantamiento_admin(
    encuesta_id: uuid.UUID,
    service: AdminService = Depends(get_admin_service),
) -> FieldMapSummaryOut:
    return await service.get_field_map_summary(encuesta_id)


@router.get(
    "/encuestas/{encuesta_id}/respuestas/{respuesta_id}",
    summary="Obtiene el detalle completo de una respuesta ciudadana por su ID",
    responses={404: {"model": ProblemDetailOut, "description": "Encuesta o respuesta no encontrada"}},
)
async def obtener_detalle_respuesta_admin(
    encuesta_id: uuid.UUID,
    respuesta_id: int,
    service: AdminService = Depends(get_admin_service),
) -> Dict[str, Any]:
    return await service.get_submission_detail(encuesta_id, respuesta_id)


@router.get(
    "/encuestas/{encuesta_id}/exportar",
    summary="Exporta todas las respuestas recibidas en formato CSV o JSON",
    responses={404: {"model": ProblemDetailOut, "description": "Encuesta no encontrada"}},
)
async def exportar_respuestas_admin(
    encuesta_id: uuid.UUID,
    formato: str = Query(default="json", pattern=r"^(json|csv)$"),
    redact_pii: bool = Query(default=False, description="Anonimizar datos personales en la descarga"),
    service: AdminService = Depends(get_admin_service),
) -> StreamingResponse:
    await service._require_survey(encuesta_id)
    stream = service.stream_export_submissions(
        encuesta_id, formato=formato, redact_pii=redact_pii
    )
    if formato.lower() == "csv":
        return StreamingResponse(
            content=stream,
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="encuesta_{encuesta_id}.csv"'
            },
        )
    return StreamingResponse(
        content=stream,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="encuesta_{encuesta_id}.json"'
        },
    )
