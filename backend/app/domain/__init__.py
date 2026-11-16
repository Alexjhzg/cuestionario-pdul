"""Capa de dominio puro del sistema PDUL."""

from backend.app.domain.entities import CitizenSubmission, Survey
from backend.app.domain.exceptions import (
    DomainError,
    DuplicateCedulaError,
    DuplicateSlugError,
    PersistenceUnavailableError,
    RestrictedPiiFieldError,
    SurveyInactiveError,
    SurveyNotFoundError,
)
from backend.app.domain.interfaces import (
    AbstractSubmissionRepository,
    AbstractSurveyRepository,
    AbstractUnitOfWork,
)
from backend.app.domain.value_objects import Cedula, Parroquia, Trip

__all__ = [
    "AbstractSubmissionRepository",
    "AbstractSurveyRepository",
    "AbstractUnitOfWork",
    "Cedula",
    "CitizenSubmission",
    "DomainError",
    "DuplicateCedulaError",
    "DuplicateSlugError",
    "Parroquia",
    "PersistenceUnavailableError",
    "RestrictedPiiFieldError",
    "Survey",
    "SurveyInactiveError",
    "SurveyNotFoundError",
    "Trip",
]
