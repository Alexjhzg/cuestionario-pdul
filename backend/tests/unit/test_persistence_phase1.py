from unittest.mock import AsyncMock, MagicMock
import pytest

from backend.app.domain.interfaces import (
    AbstractSubmissionRepository,
    AbstractSurveyRepository,
    AbstractUnitOfWork,
)
from backend.app.infrastructure.database import SqlAlchemyUnitOfWork
from backend.app.infrastructure.repositories import (
    EncuestaRepository as InfraEncuestaRepository,
    PostgresSurveyRepository,
    SqliteSurveyRepository,
    SurveyRepository as InfraSurveyRepository,
)
from backend.app.repositories import (
    EncuestaRepository as LegacyEncuestaRepository,
    SurveyRepository as LegacySurveyRepository,
)


def _mock_session_with_dialect(dialect_name: str) -> AsyncMock:
    session = AsyncMock()
    session.bind = MagicMock()
    session.bind.dialect = MagicMock()
    session.bind.dialect.name = dialect_name
    return session


def test_transitional_facades_reexport_infrastructure_classes():
    assert LegacyEncuestaRepository is InfraEncuestaRepository
    assert LegacySurveyRepository is InfraSurveyRepository
    assert issubclass(InfraEncuestaRepository, AbstractSurveyRepository)
    assert issubclass(InfraSurveyRepository, AbstractSubmissionRepository)
    assert issubclass(SqlAlchemyUnitOfWork, AbstractUnitOfWork)


def test_survey_repository_selects_postgres_or_sqlite_strategy():
    pg_repo = InfraSurveyRepository(_mock_session_with_dialect("postgresql"))
    sqlite_repo = InfraSurveyRepository(_mock_session_with_dialect("sqlite"))

    assert isinstance(pg_repo._delegate, PostgresSurveyRepository)
    assert isinstance(sqlite_repo._delegate, SqliteSurveyRepository)


@pytest.mark.asyncio
async def test_sqlalchemy_unit_of_work_commits_on_clean_exit():
    session = _mock_session_with_dialect("sqlite")

    async with SqlAlchemyUnitOfWork(session) as uow:
        assert isinstance(uow.surveys, AbstractSurveyRepository)
        assert isinstance(uow.submissions, AbstractSubmissionRepository)

    session.commit.assert_awaited_once()
    session.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_sqlalchemy_unit_of_work_rolls_back_on_exception():
    session = _mock_session_with_dialect("sqlite")

    with pytest.raises(RuntimeError, match="boom"):
        async with SqlAlchemyUnitOfWork(session):
            raise RuntimeError("boom")

    session.rollback.assert_awaited_once()
    session.commit.assert_not_awaited()
