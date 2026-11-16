from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import uuid

from backend.app.schemas.analytics import (
    EChartsSeriesOut,
    KpiMetricsOut,
    MatrizODRowOut,
    ParroquiaCountOut,
    PreguntaMetricaOut,
    RepartoModalRowOut,
)
from backend.app.schemas.submission import FormioSubmissionIn


class AbstractSubmissionRepository(ABC):
    """Contrato abstracto para persistencia y analítica de respuestas ciudadanas."""

    @abstractmethod
    async def get_by_client_submission_id(
        self,
        arg1: uuid.UUID,
        arg2: Optional[uuid.UUID] = None,
    ) -> Optional[Dict[str, Any]]:
        ...

    @abstractmethod
    async def get_by_encuesta_and_cedula(
        self, encuesta_id: uuid.UUID, cedula: str
    ) -> Optional[Dict[str, Any]]:
        ...

    @abstractmethod
    async def insert_submission(
        self, encuesta_id: uuid.UUID, submission: FormioSubmissionIn
    ) -> Dict[str, Any]:
        ...

    @abstractmethod
    async def list_submissions(
        self, encuesta_id: uuid.UUID, skip: int = 0, limit: int = 50
    ) -> List[Any]:
        ...

    @abstractmethod
    async def count_submissions(self, encuesta_id: uuid.UUID) -> int:
        ...

    @abstractmethod
    async def aggregate_by_parroquia(
        self, encuesta_id: uuid.UUID
    ) -> List[ParroquiaCountOut]:
        ...

    @abstractmethod
    async def aggregate_field_series(
        self, encuesta_id: uuid.UUID, campo: str
    ) -> EChartsSeriesOut:
        ...

    @abstractmethod
    async def aggregate_od_matrix(self, encuesta_id: uuid.UUID) -> List[MatrizODRowOut]:
        ...

    @abstractmethod
    async def aggregate_modal_split(
        self, encuesta_id: uuid.UUID
    ) -> List[RepartoModalRowOut]:
        ...

    @abstractmethod
    async def get_kpis(self, encuesta_id: uuid.UUID) -> KpiMetricsOut:
        ...

    @abstractmethod
    async def aggregate_all_questions(
        self, encuesta_id: uuid.UUID
    ) -> List[PreguntaMetricaOut]:
        ...
