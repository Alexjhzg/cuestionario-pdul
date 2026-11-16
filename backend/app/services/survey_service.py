import uuid
from typing import List
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from backend.app.core.logging import logger
from backend.app.repositories.encuesta_repo import EncuestaRepository
from backend.app.repositories.survey_repo import SurveyRepository
from backend.app.schemas.analytics import (
    EChartsSeriesOut,
    KpiMetricsOut,
    MatrizODRowOut,
    ParroquiaCountOut,
    PreguntaMetricaOut,
    RepartoModalRowOut,
)
from backend.app.schemas.problem import ProblemDetailOut
from backend.app.schemas.submission import (
    FormioSubmissionIn,
    SubmissionReceiptOut,
)
from backend.app.services.normalizers import PII_FIELDS


class SurveyService:
    def __init__(
        self,
        survey_repo: SurveyRepository,
        encuesta_repo: EncuestaRepository,
    ) -> None:
        self.survey_repo = survey_repo
        self.encuesta_repo = encuesta_repo

    async def register_participation(
        self, encuesta_id: uuid.UUID, submission: FormioSubmissionIn
    ) -> SubmissionReceiptOut:
        # 1. Verificar existencia y estado activo de la encuesta
        encuesta = await self.encuesta_repo.get_by_id(encuesta_id)
        if not encuesta and str(encuesta_id) == "00000000-0000-0000-0000-000000000001":
            # Fallback defensivo hacia la encuesta canónica activa
            encuesta = await self.encuesta_repo.get_by_slug("cuestionario-od-maturin")
            if not encuesta:
                encuesta = await self.encuesta_repo.get_by_slug("pdul_origen_destino")
            if encuesta:
                encuesta_id = encuesta.id

        if not encuesta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ProblemDetailOut(
                    code="ENCUESTA_NO_ENCONTRADA",
                    title="Encuesta no encontrada",
                    status=404,
                    detail=f"No se encontró la encuesta con id '{encuesta_id}'.",
                ).model_dump(),
            )

        if not encuesta.activa:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ProblemDetailOut(
                    code="ENCUESTA_INACTIVA",
                    title="Encuesta inactiva",
                    status=400,
                    detail="La encuesta especificada se encuentra inactiva y no acepta envíos.",
                ).model_dump(),
            )

        # 2. Idempotencia mediante client_submission_id (cola offline)
        if submission.client_submission_id:
            existing = await self.survey_repo.get_by_client_submission_id(
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
            dup = await self.survey_repo.get_by_encuesta_and_cedula(
                encuesta_id, submission.cedula_limpia
            )
            if dup:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=ProblemDetailOut(
                        code="CEDULA_DUPLICADA",
                        title="Conflicto de participación",
                        status=409,
                        detail="La cédula indicada ya participó en esta consulta pública.",
                        field="cedula",
                    ).model_dump(),
                )

        # 4. Insertar registro y manejar restricción de integridad a nivel de base de datos
        try:
            created = await self.survey_repo.insert_submission(encuesta_id, submission)
            await self.survey_repo.session.commit()

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
            await self.survey_repo.session.rollback()
            if submission.client_submission_id:
                existing = await self.survey_repo.get_by_client_submission_id(
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
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=ProblemDetailOut(
                        code="ENCUESTA_NO_ENCONTRADA",
                        title="Encuesta no encontrada",
                        status=404,
                        detail="La encuesta especificada no existe.",
                    ).model_dump(),
                ) from exc

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=ProblemDetailOut(
                    code="CEDULA_DUPLICADA",
                    title="Conflicto de participación",
                    status=409,
                    detail="La cédula indicada ya participó en esta consulta pública.",
                    field="cedula",
                ).model_dump(),
            ) from exc
        except SQLAlchemyError as exc:
            await self.survey_repo.session.rollback()
            logger.error("database_persistence_error", exc_info=exc)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=ProblemDetailOut(
                    code="DATABASE_UNAVAILABLE",
                    title="Error de persistencia",
                    status=503,
                    detail="Error temporal en la base de datos. Por favor reintente su envío.",
                ).model_dump(),
            ) from exc

    async def get_parroquia_results(
        self, encuesta_id: uuid.UUID
    ) -> List[ParroquiaCountOut]:
        encuesta = await self.encuesta_repo.get_by_id(encuesta_id)
        if not encuesta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Encuesta '{encuesta_id}' no encontrada.",
            )
        return await self.survey_repo.aggregate_by_parroquia(encuesta_id)

    async def get_field_metrics(
        self, encuesta_id: uuid.UUID, campo: str
    ) -> EChartsSeriesOut:
        if campo.lower() in PII_FIELDS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ProblemDetailOut(
                    code="CAMPO_PII_RESTRINGIDO",
                    title="Acceso no permitido",
                    status=400,
                    detail=f"El campo '{campo}' contiene información de identificación personal (PII) y no puede ser consultado en endpoints analíticos.",
                    field="campo",
                ).model_dump(),
            )
        encuesta = await self.encuesta_repo.get_by_id(encuesta_id)
        if not encuesta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Encuesta '{encuesta_id}' no encontrada.",
            )
        return await self.survey_repo.aggregate_field_series(encuesta_id, campo)

    async def get_od_matrix(self, encuesta_id: uuid.UUID) -> List[MatrizODRowOut]:
        encuesta = await self.encuesta_repo.get_by_id(encuesta_id)
        if not encuesta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Encuesta '{encuesta_id}' no encontrada.",
            )
        return await self.survey_repo.aggregate_od_matrix(encuesta_id)

    async def get_modal_split(
        self, encuesta_id: uuid.UUID
    ) -> List[RepartoModalRowOut]:
        encuesta = await self.encuesta_repo.get_by_id(encuesta_id)
        if not encuesta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Encuesta '{encuesta_id}' no encontrada.",
            )
        return await self.survey_repo.aggregate_modal_split(encuesta_id)

    async def get_kpis(self, encuesta_id: uuid.UUID) -> KpiMetricsOut:
        encuesta = await self.encuesta_repo.get_by_id(encuesta_id)
        if not encuesta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Encuesta '{encuesta_id}' no encontrada.",
            )
        return await self.survey_repo.get_kpis(encuesta_id)

    async def get_all_questions_metrics(
        self, encuesta_id: uuid.UUID
    ) -> List[PreguntaMetricaOut]:
        encuesta = await self.encuesta_repo.get_by_id(encuesta_id)
        if not encuesta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Encuesta '{encuesta_id}' no encontrada.",
            )
        return await self.survey_repo.aggregate_all_questions(encuesta_id)
