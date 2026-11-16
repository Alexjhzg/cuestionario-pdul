from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.domain.interfaces.unit_of_work import AbstractUnitOfWork
from backend.app.infrastructure.repositories.encuesta_repo import EncuestaRepository
from backend.app.infrastructure.repositories.survey_repo import SurveyRepository


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    """Implementación de Unit of Work respaldada por AsyncSession de SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.surveys = EncuestaRepository(session)
        self.submissions = SurveyRepository(session)

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()

