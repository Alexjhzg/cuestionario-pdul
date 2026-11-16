import uuid
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.repositories.encuesta_repo import EncuestaRepository
from backend.app.repositories.survey_repo import SurveyRepository
from backend.app.schemas.analytics import (
    EChartsSeriesOut,
    KpiMetricsOut,
    MatrizODRowOut,
    ParroquiaCountOut,
    PreguntaMetricaOut,
    RepartoModalRowOut,
)
from backend.app.services.survey_service import SurveyService

router = APIRouter()


def get_survey_service(db: AsyncSession = Depends(get_db)) -> SurveyService:
    return SurveyService(SurveyRepository(db), EncuestaRepository(db))


@router.get(
    "/{encuesta_id}/resultados-parroquia",
    response_model=List[ParroquiaCountOut],
    summary="Conteo y porcentaje agregado por parroquia para mapa coroplético Leaflet",
)
async def obtener_resultados_parroquia(
    encuesta_id: uuid.UUID,
    service: SurveyService = Depends(get_survey_service),
) -> List[ParroquiaCountOut]:
    return await service.get_parroquia_results(encuesta_id)


@router.get(
    "/{encuesta_id}/metricas",
    response_model=EChartsSeriesOut,
    summary="Serie de frecuencias (labels, values) por campo para gráficos Apache ECharts",
)
async def obtener_metricas_campo(
    encuesta_id: uuid.UUID,
    campo: str = Query(..., pattern=r"^[a-z][a-z0-9_]*$", description="Clave snake_case del campo a agregar"),
    service: SurveyService = Depends(get_survey_service),
) -> EChartsSeriesOut:
    return await service.get_field_metrics(encuesta_id, campo)


@router.get(
    "/{encuesta_id}/matriz-od",
    response_model=List[MatrizODRowOut],
    summary="Matriz agregada de viajes por pares de zonas Origen-Destino",
)
async def obtener_matriz_od(
    encuesta_id: uuid.UUID,
    service: SurveyService = Depends(get_survey_service),
) -> List[MatrizODRowOut]:
    return await service.get_od_matrix(encuesta_id)


@router.get(
    "/{encuesta_id}/reparto-modal",
    response_model=List[RepartoModalRowOut],
    summary="Distribución de viajes según modo de transporte principal",
)
async def obtener_reparto_modal(
    encuesta_id: uuid.UUID,
    service: SurveyService = Depends(get_survey_service),
) -> List[RepartoModalRowOut]:
    return await service.get_modal_split(encuesta_id)


@router.get(
    "/{encuesta_id}/kpis",
    response_model=KpiMetricsOut,
    summary="Tarjetas de indicadores ejecutivos del levantamiento (total encuestas, viajes, residentes)",
)
async def obtener_kpis_generales(
    encuesta_id: uuid.UUID,
    service: SurveyService = Depends(get_survey_service),
) -> KpiMetricsOut:
    return await service.get_kpis(encuesta_id)


@router.get(
    "/{encuesta_id}/preguntas-metricas",
    response_model=List[PreguntaMetricaOut],
    summary="Métricas agregadas para cada una de las preguntas del cuestionario",
)
async def obtener_metricas_todas_preguntas(
    encuesta_id: uuid.UUID,
    service: SurveyService = Depends(get_survey_service),
) -> List[PreguntaMetricaOut]:
    return await service.get_all_questions_metrics(encuesta_id)
