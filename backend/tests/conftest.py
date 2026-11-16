import asyncio
import uuid
from typing import AsyncGenerator, Dict, Any
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.app.core.database import Base, get_db
from backend.app.domain.interfaces.unit_of_work import AbstractUnitOfWork
from backend.app.main import create_app
from backend.app.models.encuesta import Encuesta
from backend.app.models.respuesta import RespuestaCiudadana
from backend.app.repositories.encuesta_repo import EncuestaRepository
from backend.app.repositories.survey_repo import SurveyRepository


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_formio_schema() -> Dict[str, Any]:
    return {
        "display": "wizard",
        "components": [
            {
                "type": "panel",
                "key": "seccion_i",
                "title": "I. Ubicación",
                "components": [
                    {
                        "type": "select",
                        "key": "parroquia",
                        "label": "Parroquia",
                        "data": {
                            "values": [
                                {"label": "San Simón", "value": "san_simon"},
                                {"label": "Alto de Los Godos", "value": "alto_de_los_godos"},
                            ]
                        },
                    },
                    {
                        "type": "textfield",
                        "key": "zona_residencia_od",
                        "label": "Zona OD",
                    },
                ],
            },
            {
                "type": "panel",
                "key": "seccion_cierre",
                "title": "Cierre",
                "components": [
                    {
                        "type": "button",
                        "action": "submit",
                        "key": "submit",
                        "label": "Finalizar Encuesta",
                    }
                ],
            },
        ],
    }


@pytest.fixture
def sample_valid_submission_payload() -> Dict[str, Any]:
    return {
        "client_submission_id": str(uuid.uuid4()),
        "data": {
            "cedula": "V-12.345.678",
            "parroquia": "san_simon",
            "zona_residencia_od": "ZONA_01",
            "tipo_vivienda": "quinta",
            "residentes": [
                {
                    "nombre_apellido": "Juan Pérez",
                    "sexo": "1",
                    "edad": 35,
                    "parentesco": "1",
                }
            ],
            "viajes": [
                {
                    "zona_od_origen": "ZONA_01",
                    "zona_od_destino": "ZONA_02",
                    "motivo_viaje": "1",
                    "modo_principal": "6",
                    "tiempo_viaje_min": 25,
                    "costo_viaje_bs": 15.5,
                },
                {
                    "zona_od_origen": "ZONA_02",
                    "zona_od_destino": "ZONA_01",
                    "motivo_viaje": "5",
                    "modo_principal": "6",
                    "tiempo_viaje_min": 30,
                    "costo_viaje_bs": 15.5,
                },
            ],
        },
    }


@pytest_asyncio.fixture
async def test_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Crea una base de datos en memoria para pruebas de integración aisladas."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async with session_maker() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def async_client(test_db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Cliente HTTP asíncrono configurado con la base de datos de pruebas."""
    app = create_app()

    async def override_get_db():
        yield test_db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def mock_survey_repo() -> AsyncMock:
    repo = AsyncMock(spec=SurveyRepository)
    repo.session = AsyncMock()
    return repo


@pytest.fixture
def mock_encuesta_repo() -> AsyncMock:
    repo = AsyncMock(spec=EncuestaRepository)
    repo.session = AsyncMock()
    return repo


@pytest.fixture
def mock_uow(mock_survey_repo: AsyncMock, mock_encuesta_repo: AsyncMock) -> AsyncMock:
    uow = AsyncMock(spec=AbstractUnitOfWork)
    uow.surveys = mock_encuesta_repo
    uow.submissions = mock_survey_repo
    return uow
