from abc import ABC, abstractmethod
from typing import Any

from backend.app.domain.interfaces.submission_repository import (
    AbstractSubmissionRepository,
)
from backend.app.domain.interfaces.survey_repository import AbstractSurveyRepository


class AbstractUnitOfWork(ABC):
    """Contrato abstracto para la coordinación transaccional de repositorios."""

    surveys: AbstractSurveyRepository
    submissions: AbstractSubmissionRepository

    async def __aenter__(self) -> "AbstractUnitOfWork":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()

    @abstractmethod
    async def commit(self) -> None:
        ...

    @abstractmethod
    async def rollback(self) -> None:
        ...
