from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.domain.interfaces.unit_of_work import AbstractUnitOfWork
from backend.app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from backend.app.infrastructure.repositories.encuesta_repo import EncuestaRepository
from backend.app.services.admin_service import AdminService
from backend.app.services.analytics_service import AnalyticsService
from backend.app.services.survey_service import SurveyService


async def get_uow(db: AsyncSession = Depends(get_db)) -> AbstractUnitOfWork:
    """Proveedor centralizado de Unit of Work conectado al ciclo de sesión FastAPI."""
    return SqlAlchemyUnitOfWork(db)


def get_survey_service(
    uow: AbstractUnitOfWork = Depends(get_uow),
) -> SurveyService:
    return SurveyService(uow)


def get_admin_service(
    uow: AbstractUnitOfWork = Depends(get_uow),
) -> AdminService:
    return AdminService(uow)


def get_analytics_service(
    uow: AbstractUnitOfWork = Depends(get_uow),
) -> AnalyticsService:
    return AnalyticsService(uow)


def get_encuesta_repo(db: AsyncSession = Depends(get_db)) -> EncuestaRepository:
    return EncuestaRepository(db)
