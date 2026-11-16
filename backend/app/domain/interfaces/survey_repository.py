from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
import uuid


class AbstractSurveyRepository(ABC):
    """Contrato abstracto para la gestión de instrumentos de encuesta."""

    @abstractmethod
    async def get_by_id(self, encuesta_id: uuid.UUID) -> Optional[Any]:
        ...

    @abstractmethod
    async def get_by_slug(self, slug: str) -> Optional[Any]:
        ...

    @abstractmethod
    async def list_all(self) -> List[Tuple[Any, int]]:
        ...

    @abstractmethod
    async def create(self, encuesta_in: Any) -> Any:
        ...

    @abstractmethod
    async def update(self, encuesta: Any, update_data: Dict[str, Any]) -> Any:
        ...

    @abstractmethod
    async def update_status(self, encuesta_id: uuid.UUID, activa: bool) -> Optional[Any]:
        ...

