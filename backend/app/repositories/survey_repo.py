"""Fachada transicional de compatibilidad hacia infrastructure/repositories/survey_repo.py."""

from backend.app.infrastructure.repositories.base_survey_repo import (
    MODOS_TRANSPORTE_ETIQUETAS,
)
from backend.app.infrastructure.repositories.postgres_survey_repo import (
    PostgresSurveyRepository,
)
from backend.app.infrastructure.repositories.sqlite_survey_repo import (
    SqliteSurveyRepository,
)
from backend.app.infrastructure.repositories.survey_repo import SurveyRepository

__all__ = [
    "MODOS_TRANSPORTE_ETIQUETAS",
    "PostgresSurveyRepository",
    "SqliteSurveyRepository",
    "SurveyRepository",
]
