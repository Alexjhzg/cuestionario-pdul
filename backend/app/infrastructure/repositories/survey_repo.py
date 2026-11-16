import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.domain.interfaces.submission_repository import (
    AbstractSubmissionRepository,
)
from backend.app.infrastructure.repositories.base_survey_repo import BaseSurveyRepository
from backend.app.infrastructure.repositories.postgres_survey_repo import (
    PostgresSurveyRepository,
)
from backend.app.infrastructure.repositories.sqlite_survey_repo import (
    SqliteSurveyRepository,
)
from backend.app.models.respuesta import RespuestaCiudadana
from backend.app.schemas.analytics import (
    EChartsSeriesOut,
    KpiMetricsOut,
    MatrizODRowOut,
    ParroquiaCountOut,
    PreguntaMetricaOut,
    RepartoModalRowOut,
)
from backend.app.schemas.submission import FormioSubmissionIn


def _select_dialect_repository(session: AsyncSession) -> BaseSurveyRepository:
    """Selecciona la estrategia de repositorio según el dialecto de SQLAlchemy."""
    bind = session.bind
    if bind is not None and hasattr(bind, "dialect") and bind.dialect.name != "postgresql":
        return SqliteSurveyRepository(session)
    return PostgresSurveyRepository(session)


class SurveyRepository(AbstractSubmissionRepository):
    """Fachada de estrategia que delega al adaptador específico del motor de base de datos."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._delegate: BaseSurveyRepository = _select_dialect_repository(session)

    async def get_by_client_submission_id(
        self,
        arg1: uuid.UUID,
        arg2: Optional[uuid.UUID] = None,
    ) -> Optional[Dict[str, Any]]:
        return await self._delegate.get_by_client_submission_id(arg1, arg2)

    async def get_by_encuesta_and_cedula(
        self, encuesta_id: uuid.UUID, cedula: str
    ) -> Optional[Dict[str, Any]]:
        return await self._delegate.get_by_encuesta_and_cedula(encuesta_id, cedula)

    async def insert_submission(
        self, encuesta_id: uuid.UUID, submission: FormioSubmissionIn
    ) -> Dict[str, Any]:
        return await self._delegate.insert_submission(encuesta_id, submission)

    async def list_submissions(
        self, encuesta_id: uuid.UUID, skip: int = 0, limit: int = 50
    ) -> List[RespuestaCiudadana]:
        return await self._delegate.list_submissions(encuesta_id, skip=skip, limit=limit)

    async def count_submissions(self, encuesta_id: uuid.UUID) -> int:
        return await self._delegate.count_submissions(encuesta_id)

    async def aggregate_by_parroquia(
        self, encuesta_id: uuid.UUID
    ) -> List[ParroquiaCountOut]:
        return await self._delegate.aggregate_by_parroquia(encuesta_id)

    async def aggregate_field_series(
        self, encuesta_id: uuid.UUID, campo: str
    ) -> EChartsSeriesOut:
        return await self._delegate.aggregate_field_series(encuesta_id, campo)

    async def aggregate_od_matrix(self, encuesta_id: uuid.UUID) -> List[MatrizODRowOut]:
        return await self._delegate.aggregate_od_matrix(encuesta_id)

    async def aggregate_modal_split(
        self, encuesta_id: uuid.UUID
    ) -> List[RepartoModalRowOut]:
        return await self._delegate.aggregate_modal_split(encuesta_id)

    async def get_kpis(self, encuesta_id: uuid.UUID) -> KpiMetricsOut:
        return await self._delegate.get_kpis(encuesta_id)

    async def aggregate_all_questions(
        self, encuesta_id: uuid.UUID
    ) -> List[PreguntaMetricaOut]:
        return await self._delegate.aggregate_all_questions(encuesta_id)
