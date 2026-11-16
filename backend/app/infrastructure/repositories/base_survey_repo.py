import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.domain.interfaces.submission_repository import (
    AbstractSubmissionRepository,
)
from backend.app.models.encuesta import Encuesta
from backend.app.models.respuesta import RespuestaCiudadana
from backend.app.schemas.analytics import KpiMetricsOut, PreguntaMetricaOut
from backend.app.schemas.submission import FormioSubmissionIn

MODOS_TRANSPORTE_ETIQUETAS: Dict[str, str] = {
    "1": "A pie",
    "2": "Bicicleta",
    "3": "Motocicleta",
    "4": "Automóvil particular",
    "5": "Taxi",
    "6": "Transporte público (bus/buseta)",
    "7": "Transporte informal (por puesto/mototaxi)",
    "8": "Otro",
}


class BaseSurveyRepository(AbstractSubmissionRepository):
    """Base común independiente del dialecto para operaciones CRUD y lecturas de respuestas."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_client_submission_id(
        self,
        arg1: uuid.UUID,
        arg2: Optional[uuid.UUID] = None,
    ) -> Optional[Dict[str, Any]]:
        if arg2 is None:
            stmt = select(RespuestaCiudadana.id, RespuestaCiudadana.fecha_registro).where(
                RespuestaCiudadana.client_submission_id == arg1
            ).limit(1)
        else:
            stmt = select(RespuestaCiudadana.id, RespuestaCiudadana.fecha_registro).where(
                (
                    (RespuestaCiudadana.client_submission_id == arg1)
                    & (RespuestaCiudadana.encuesta_id == arg2)
                )
                | (
                    (RespuestaCiudadana.client_submission_id == arg2)
                    & (RespuestaCiudadana.encuesta_id == arg1)
                )
            ).limit(1)
        result = await self.session.execute(stmt)
        row = result.first()
        if row:
            return {"id": row[0], "fecha_registro": row[1]}
        return None

    async def get_by_encuesta_and_cedula(
        self, encuesta_id: uuid.UUID, cedula: str
    ) -> Optional[Dict[str, Any]]:
        stmt = select(RespuestaCiudadana.id).where(
            RespuestaCiudadana.encuesta_id == encuesta_id,
            RespuestaCiudadana.cedula == cedula,
        ).limit(1)
        result = await self.session.execute(stmt)
        row = result.first()
        if row:
            return {"id": row[0]}
        return None

    async def insert_submission(
        self, encuesta_id: uuid.UUID, submission: FormioSubmissionIn
    ) -> Dict[str, Any]:
        nueva_respuesta = RespuestaCiudadana(
            encuesta_id=encuesta_id,
            client_submission_id=submission.client_submission_id,
            cedula=submission.cedula_limpia,
            parroquia=submission.parroquia,
            zona_od=submission.zona_od,
            datos=submission.data,
        )
        self.session.add(nueva_respuesta)
        await self.session.flush()
        return {
            "id": nueva_respuesta.id,
            "fecha_registro": nueva_respuesta.fecha_registro,
        }

    async def list_submissions(
        self, encuesta_id: uuid.UUID, skip: int = 0, limit: int = 50
    ) -> List[RespuestaCiudadana]:
        stmt = (
            select(RespuestaCiudadana)
            .where(RespuestaCiudadana.encuesta_id == encuesta_id)
            .order_by(RespuestaCiudadana.fecha_registro.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_submissions(self, encuesta_id: uuid.UUID) -> int:
        stmt = (
            select(func.count(RespuestaCiudadana.id))
            .where(RespuestaCiudadana.encuesta_id == encuesta_id)
        )
        result = await self.session.execute(stmt)
        return int(result.scalar_one() or 0)

    async def get_kpis(self, encuesta_id: uuid.UUID) -> KpiMetricsOut:
        total_encuestas = await self.count_submissions(encuesta_id)
        stmt = select(RespuestaCiudadana.datos, RespuestaCiudadana.parroquia).where(
            RespuestaCiudadana.encuesta_id == encuesta_id
        )
        rows = (await self.session.execute(stmt)).all()

        total_viajes = 0
        total_residentes = 0
        parroquia_counts: Dict[str, int] = {}

        for d, p in rows:
            parroquia_counts[p] = parroquia_counts.get(p, 0) + 1
            if isinstance(d, dict):
                viajes = d.get("viajes")
                if isinstance(viajes, list):
                    total_viajes += len(viajes)
                residentes = d.get("residentes")
                if isinstance(residentes, list):
                    total_residentes += len(residentes)
                elif "num_residentes_hogar" in d:
                    try:
                        total_residentes += int(d["num_residentes_hogar"])
                    except (ValueError, TypeError):
                        pass

        parroquia_lider = None
        if parroquia_counts:
            parroquia_lider = max(parroquia_counts.items(), key=lambda x: x[1])[0]

        return KpiMetricsOut(
            total_encuestas=total_encuestas,
            total_viajes=total_viajes,
            total_residentes=total_residentes,
            parroquia_lider=parroquia_lider,
        )

    async def aggregate_all_questions(
        self, encuesta_id: uuid.UUID
    ) -> List[PreguntaMetricaOut]:
        encuesta = await self.session.get(Encuesta, encuesta_id)
        if not encuesta:
            return []
        schema = encuesta.esquema_formio if isinstance(encuesta.esquema_formio, dict) else {}

        stmt = select(RespuestaCiudadana.datos).where(
            RespuestaCiudadana.encuesta_id == encuesta_id
        )
        rows = (await self.session.execute(stmt)).scalars().all()
        data_rows = [r for r in rows if isinstance(r, dict)]

        from backend.app.services.question_analytics import aggregate_all_survey_questions
        return aggregate_all_survey_questions(schema, data_rows)

