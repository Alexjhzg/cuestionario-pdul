import uuid
from typing import List
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.domain.exceptions import (
    DuplicateCedulaError,
    PersistenceUnavailableError,
    SurveyInactiveError,
    SurveyNotFoundError,
)
from backend.app.domain.interfaces.unit_of_work import AbstractUnitOfWork
from backend.app.schemas.analytics import (
    EChartsSeriesOut,
    KpiMetricsOut,
    MatrizODRowOut,
    ParroquiaCountOut,
    PreguntaMetricaOut,
    RepartoModalRowOut,
)
from backend.app.schemas.encuesta import EncuestaOut
from backend.app.schemas.submission import (
    FormioSubmissionIn,
    SubmissionReceiptOut,
)
from backend.app.services.analytics_service import AnalyticsService


class SurveyService:
    """Servicio de aplicación para consulta ciudadana, envíos idempotentes y delegación analítica."""

    def __init__(self, uow: AbstractUnitOfWork) -> None:
        self.uow = uow
        self._analytics = AnalyticsService(uow)

    async def get_active_survey_by_slug(self, slug: str) -> EncuestaOut:
        encuesta = await self.uow.surveys.get_by_slug(slug)
        if not encuesta or not encuesta.activa:
            raise SurveyNotFoundError(
                slug,
                f"La encuesta con slug '{slug}' no existe o se encuentra inactiva.",
            )
        return EncuestaOut.model_validate(encuesta)

    async def register_participation(
        self, encuesta_id: uuid.UUID, submission: FormioSubmissionIn
    ) -> SubmissionReceiptOut:
        # 1. Verificar existencia y estado activo de la encuesta
        encuesta = await self.uow.surveys.get_by_id(encuesta_id)
        if not encuesta and str(encuesta_id) == settings.CANONICAL_SURVEY_ID:
            # Fallback defensivo hacia la encuesta canónica activa
            encuesta = await self.uow.surveys.get_by_slug(settings.CANONICAL_SURVEY_SLUG)
            if not encuesta:
                encuesta = await self.uow.surveys.get_by_slug(settings.LEGACY_SURVEY_SLUG)
            if encuesta:
                encuesta_id = encuesta.id

        if not encuesta:
            raise SurveyNotFoundError(
                str(encuesta_id),
                f"No se encontró la encuesta con id '{encuesta_id}'.",
            )

        if not encuesta.activa:
            raise SurveyInactiveError()

        # 2. Idempotencia mediante client_submission_id (cola offline)
        if submission.client_submission_id:
            existing = await self.uow.submissions.get_by_client_submission_id(
                submission.client_submission_id
            )
            if existing:
                return SubmissionReceiptOut(
                    id=existing["id"],
                    fecha_registro=existing["fecha_registro"],
                    idempotent_replay=True,
                    mensaje="Participación sincronizada previamente (idempotente).",
                )

        # 3. Verificación previa de cédula única si fue provista
        if submission.cedula_limpia:
            dup = await self.uow.submissions.get_by_encuesta_and_cedula(
                encuesta_id, submission.cedula_limpia
            )
            if dup:
                raise DuplicateCedulaError()

        # 4. Insertar registro y manejar restricción de integridad a nivel de base de datos
        try:
            created = await self.uow.submissions.insert_submission(encuesta_id, submission)
            await self.uow.commit()

            # Log estructurado omitting PII (cédula y nombres estrictamente ausentes)
            logger.info(
                "survey_submission_registered",
                extra={
                    "encuesta_id": str(encuesta_id),
                    "parroquia": submission.parroquia,
                    "zona_od": submission.zona_od,
                    "submission_id": created["id"],
                },
            )

            return SubmissionReceiptOut(
                id=created["id"],
                fecha_registro=created["fecha_registro"],
                idempotent_replay=False,
                mensaje="Participación registrada exitosamente.",
            )
        except IntegrityError as exc:
            await self.uow.rollback()
            if submission.client_submission_id:
                existing = await self.uow.submissions.get_by_client_submission_id(
                    submission.client_submission_id, encuesta_id
                )
                if existing:
                    return SubmissionReceiptOut(
                        id=existing["id"],
                        fecha_registro=existing["fecha_registro"],
                        idempotent_replay=True,
                        mensaje="Participación sincronizada previamente (idempotente).",
                    )
            exc_str = str(exc).lower()
            if "foreign key" in exc_str or "fk_" in exc_str:
                raise SurveyNotFoundError(
                    str(encuesta_id),
                    "La encuesta especificada no existe.",
                ) from exc

            raise DuplicateCedulaError() from exc
        except SQLAlchemyError as exc:
            await self.uow.rollback()
            logger.error("database_persistence_error", exc_info=exc)
            raise PersistenceUnavailableError() from exc

    async def get_parroquia_results(
        self, encuesta_id: uuid.UUID
    ) -> List[ParroquiaCountOut]:
        return await self._analytics.get_parroquia_results(encuesta_id)

    async def get_field_metrics(
        self, encuesta_id: uuid.UUID, campo: str
    ) -> EChartsSeriesOut:
        return await self._analytics.get_field_metrics(encuesta_id, campo)

    async def get_od_matrix(self, encuesta_id: uuid.UUID) -> List[MatrizODRowOut]:
        return await self._analytics.get_od_matrix(encuesta_id)

    async def get_modal_split(
        self, encuesta_id: uuid.UUID
    ) -> List[RepartoModalRowOut]:
        return await self._analytics.get_modal_split(encuesta_id)

    async def get_kpis(self, encuesta_id: uuid.UUID) -> KpiMetricsOut:
        return await self._analytics.get_kpis(encuesta_id)

    async def get_all_questions_metrics(
        self, encuesta_id: uuid.UUID
    ) -> List[PreguntaMetricaOut]:
        return await self._analytics.get_all_questions_metrics(encuesta_id)
