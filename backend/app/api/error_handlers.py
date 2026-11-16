from typing import Dict, Tuple, Type

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.app.core.logging import logger
from backend.app.domain.exceptions import (
    DomainError,
    DuplicateCedulaError,
    DuplicateSlugError,
    PersistenceUnavailableError,
    RestrictedPiiFieldError,
    SurveyInactiveError,
    SurveyNotFoundError,
)
from backend.app.schemas.problem import ProblemDetailOut

DOMAIN_ERROR_HTTP_MAP: Dict[Type[DomainError], Tuple[int, str]] = {
    SurveyNotFoundError: (status.HTTP_404_NOT_FOUND, "Encuesta no encontrada"),
    SurveyInactiveError: (status.HTTP_400_BAD_REQUEST, "Encuesta inactiva"),
    DuplicateCedulaError: (status.HTTP_409_CONFLICT, "Conflicto de participación"),
    DuplicateSlugError: (status.HTTP_409_CONFLICT, "Conflicto de registro"),
    RestrictedPiiFieldError: (status.HTTP_400_BAD_REQUEST, "Acceso no permitido"),
    PersistenceUnavailableError: (
        status.HTTP_503_SERVICE_UNAVAILABLE,
        "Error de persistencia",
    ),
}


def domain_error_to_problem(exc: DomainError) -> Tuple[int, ProblemDetailOut]:
    """Convierte una excepción de dominio pura en código HTTP y payload RFC 7807."""
    http_status, title = DOMAIN_ERROR_HTTP_MAP.get(
        type(exc),
        (status.HTTP_400_BAD_REQUEST, "Error de negocio"),
    )
    return http_status, ProblemDetailOut(
        code=exc.code,
        title=title,
        status=http_status,
        detail=exc.message,
        field=exc.field,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Registra los manejadores globales de excepción con formato RFC 7807."""

    @app.exception_handler(DomainError)
    async def domain_exception_handler(
        request: Request, exc: DomainError
    ) -> JSONResponse:
        http_status, problem = domain_error_to_problem(exc)
        return JSONResponse(status_code=http_status, content=problem.model_dump())

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = []
        first_field = None
        for err in exc.errors():
            loc = err.get("loc", [])
            field_name = str(loc[-1]) if loc else None
            if first_field is None and field_name and field_name not in ("body", "data"):
                first_field = field_name
            errors.append(
                {
                    "loc": [str(x) for x in loc],
                    "msg": err.get("msg"),
                    "type": err.get("type"),
                }
            )

        problem = ProblemDetailOut(
            code="VALIDATION_ERROR",
            title="Error de validación de datos",
            status=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Los datos enviados no superaron las validaciones requeridas.",
            field=first_field,
            errors=errors,
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=problem.model_dump(),
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        if isinstance(exc.detail, dict) and "code" in exc.detail:
            return JSONResponse(status_code=exc.status_code, content=exc.detail)

        code_map = {
            400: "BAD_REQUEST",
            404: "NOT_FOUND",
            409: "CONFLICT",
            422: "UNPROCESSABLE_ENTITY",
            500: "INTERNAL_ERROR",
        }
        problem = ProblemDetailOut(
            code=code_map.get(exc.status_code, "HTTP_ERROR"),
            title="Error en la solicitud",
            status=exc.status_code,
            detail=str(exc.detail),
        )
        return JSONResponse(status_code=exc.status_code, content=problem.model_dump())

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.error("unhandled_server_exception", exc_info=exc)
        problem = ProblemDetailOut(
            code="INTERNAL_SERVER_ERROR",
            title="Error interno del servidor",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error inesperado al procesar la solicitud en el servidor.",
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=problem.model_dump(),
        )
