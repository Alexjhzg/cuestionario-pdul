from typing import Optional


class DomainError(Exception):
    """Excepción base de dominio desacoplada de la capa HTTP."""

    def __init__(
        self,
        message: str,
        code: str = "DOMAIN_ERROR",
        field: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.field = field


class SurveyNotFoundError(DomainError):
    """Se lanza cuando el instrumento solicitado no existe o no está disponible."""

    def __init__(self, identifier: str, message: Optional[str] = None) -> None:
        detail = message or f"No se encontró la encuesta '{identifier}'."
        super().__init__(detail, code="ENCUESTA_NO_ENCONTRADA")


class SurveyInactiveError(DomainError):
    """Se lanza al intentar enviar respuestas a una encuesta desactivada."""

    def __init__(self) -> None:
        super().__init__(
            "La encuesta especificada se encuentra inactiva y no acepta envíos.",
            code="ENCUESTA_INACTIVA",
        )


class DuplicateCedulaError(DomainError):
    """Se lanza cuando la cédula ya participó en la misma consulta."""

    def __init__(self) -> None:
        super().__init__(
            "La cédula indicada ya participó en esta consulta pública.",
            code="CEDULA_DUPLICADA",
            field="cedula",
        )


class DuplicateSlugError(DomainError):
    """Se lanza al intentar crear una encuesta con un slug ya registrado."""

    def __init__(self, slug: str) -> None:
        super().__init__(
            f"Ya existe una encuesta registrada con el slug '{slug}'.",
            code="CONFLICT",
            field="slug",
        )


class RestrictedPiiFieldError(DomainError):
    """Se lanza al intentar consultar métricas públicas de un campo PII."""

    def __init__(self, field_name: str) -> None:
        super().__init__(
            (
                f"El campo '{field_name}' contiene información de identificación personal (PII) "
                "y no puede ser consultado en endpoints analíticos."
            ),
            code="CAMPO_PII_RESTRINGIDO",
            field="campo",
        )


class PersistenceUnavailableError(DomainError):
    """Se lanza cuando ocurre un fallo temporal de persistencia en base de datos."""

    def __init__(self) -> None:
        super().__init__(
            "Error temporal en la base de datos. Por favor reintente su envío.",
            code="DATABASE_UNAVAILABLE",
        )


class SubmissionNotFoundError(DomainError):
    """Se lanza cuando la respuesta solicitada no existe o no pertenece a la encuesta."""

    def __init__(self, identifier: str, message: Optional[str] = None) -> None:
        detail = message or f"No se encontró la respuesta '{identifier}'."
        super().__init__(detail, code="RESPUESTA_NO_ENCONTRADA")
