import uuid
from typing import List

from backend.app.domain.exceptions import RestrictedPiiFieldError, SurveyNotFoundError
from backend.app.domain.interfaces.unit_of_work import AbstractUnitOfWork
from backend.app.schemas.analytics import (
    EChartsSeriesOut,
    KpiMetricsOut,
    MatrizODRowOut,
    ParroquiaCountOut,
    PreguntaMetricaOut,
    RepartoModalRowOut,
)
from backend.app.services.normalizers import PII_FIELDS


class AnalyticsService:
    """Servicio de aplicación para analítica espacial, modal y agregaciones PDUL."""

    def __init__(self, uow: AbstractUnitOfWork) -> None:
        self.uow = uow

    async def _require_survey(self, encuesta_id: uuid.UUID) -> None:
        encuesta = await self.uow.surveys.get_by_id(encuesta_id)
        if not encuesta:
            raise SurveyNotFoundError(
                str(encuesta_id),
                f"Encuesta '{encuesta_id}' no encontrada.",
            )

    async def get_parroquia_results(
        self, encuesta_id: uuid.UUID
    ) -> List[ParroquiaCountOut]:
        await self._require_survey(encuesta_id)
        return await self.uow.submissions.aggregate_by_parroquia(encuesta_id)

    async def get_field_metrics(
        self, encuesta_id: uuid.UUID, campo: str
    ) -> EChartsSeriesOut:
        if campo.lower() in PII_FIELDS:
            raise RestrictedPiiFieldError(campo)
        await self._require_survey(encuesta_id)
        return await self.uow.submissions.aggregate_field_series(encuesta_id, campo)

    async def get_od_matrix(self, encuesta_id: uuid.UUID) -> List[MatrizODRowOut]:
        await self._require_survey(encuesta_id)
        return await self.uow.submissions.aggregate_od_matrix(encuesta_id)

    async def get_modal_split(
        self, encuesta_id: uuid.UUID
    ) -> List[RepartoModalRowOut]:
        await self._require_survey(encuesta_id)
        return await self.uow.submissions.aggregate_modal_split(encuesta_id)

    async def get_kpis(self, encuesta_id: uuid.UUID) -> KpiMetricsOut:
        await self._require_survey(encuesta_id)
        return await self.uow.submissions.get_kpis(encuesta_id)

    async def get_all_questions_metrics(
        self, encuesta_id: uuid.UUID
    ) -> List[PreguntaMetricaOut]:
        await self._require_survey(encuesta_id)
        return await self.uow.submissions.aggregate_all_questions(encuesta_id)
