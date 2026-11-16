"""Plantilla de Referencia: Clean Architecture (Repository + Service + Router) en FastAPI + Pydantic v2.

Implementa:
1. Separación de responsabilidades (Router -> Service -> Repository).
2. Idempotencia nativa con `client_submission_id` (UUID v4) para soporte de cola offline.
3. Respuestas de error estructuradas (RFC 7807 Problem Details) asociables a campos UI.
4. Anonimización estricta de PII en endpoints públicos de analítica.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("alcaldia.encuestas")

PARROQUIAS_MATURIN = {
    "alto_de_los_godos",
    "boqueron",
    "las_cocuizas",
    "la_cruz",
    "san_simon",
    "santa_cruz",
    "el_corozo",
    "el_furrial",
    "jusepin",
    "la_pica",
    "san_vicente",
}

CEDULA_RE = re.compile(r"^[0-9]{6,9}$")


# =============================================================================
# 1. CAPA DE ESQUEMAS Y CONTRATOS (Pydantic v2)
# =============================================================================


class ProblemDetailOut(BaseModel):
    """Estructura de error estándar RFC 7807 amigable con citizen-survey-ux."""

    code: str
    title: str
    detail: str
    field: Optional[str] = None


class FormioSubmissionIn(BaseModel):
    """Valida tanto un payload envuelto en {'data': {...}} como el objeto directo."""

    model_config = ConfigDict(extra="ignore")

    data: Dict[str, Any] = Field(..., description="Datos enviados por @formio/js")
    client_submission_id: Optional[UUID] = Field(
        default=None,
        description="UUID v4 generado en el cliente para garantizar idempotencia offline.",
    )
    cedula_limpia: Optional[str] = None
    parroquia: str = ""
    zona_od: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def unwrap_formio_payload(cls, values: Any) -> Dict[str, Any]:
        if isinstance(values, dict) and "data" not in values:
            return {
                "data": values,
                "client_submission_id": values.get("client_submission_id"),
            }
        if isinstance(values, dict) and isinstance(values.get("data"), dict):
            if not values.get("client_submission_id") and values["data"].get(
                "client_submission_id"
            ):
                values["client_submission_id"] = values["data"]["client_submission_id"]
        return values

    @model_validator(mode="after")
    def validate_and_extract_indexed_fields(self) -> "FormioSubmissionIn":
        raw_cedula = str(self.data.get("cedula", "") or "").strip()
        if raw_cedula:
            digits_only = re.sub(r"\D", "", raw_cedula)
            if not CEDULA_RE.match(digits_only):
                raise ValueError(
                    "Escriba solo los números de su cédula (6 a 9 dígitos, sin puntos ni guiones)."
                )
            self.cedula_limpia = digits_only
            self.data["cedula"] = digits_only

        parroquia = str(self.data.get("parroquia", "") or "").strip().lower()
        if parroquia not in PARROQUIAS_MATURIN:
            raise ValueError(
                f"Seleccione una parroquia válida del Municipio Maturín ({', '.join(sorted(PARROQUIAS_MATURIN))})."
            )
        self.parroquia = parroquia
        self.zona_od = str(self.data.get("zona_residencia_od", "")).strip() or None
        return self


class SubmissionReceiptOut(BaseModel):
    id: int
    fecha_registro: Any
    idempotent_replay: bool = False
    mensaje: str


class ParroquiaCountOut(BaseModel):
    parroquia: str
    total_respuestas: int
    porcentaje: float


class EChartsSeriesOut(BaseModel):
    campo: str
    labels: List[str]
    values: List[int]


class MatrizODRowOut(BaseModel):
    zona_origen: str
    zona_destino: str
    total_viajes: int
    tiempo_promedio_min: Optional[float] = None
    costo_promedio_bs: Optional[float] = None


# =============================================================================
# 2. CAPA DE REPOSITORIO (Acceso a Datos PostgreSQL + JSONB Parametrizado)
# =============================================================================


class SurveyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_client_submission_id(
        self, client_submission_id: UUID
    ) -> Optional[Dict[str, Any]]:
        sql = text(
            """
            SELECT id, fecha_registro
            FROM respuestas_ciudadanas
            WHERE client_submission_id = :client_submission_id
            LIMIT 1
            """
        )
        row = (
            await self.session.execute(
                sql, {"client_submission_id": str(client_submission_id)}
            )
        ).mappings().first()
        return dict(row) if row else None

    async def insert_submission(
        self, encuesta_id: UUID, submission: FormioSubmissionIn
    ) -> Dict[str, Any]:
        sql = text(
            """
            INSERT INTO respuestas_ciudadanas (
                encuesta_id, client_submission_id, cedula, parroquia, zona_od, datos
            )
            VALUES (
                :encuesta_id, :client_submission_id, :cedula, :parroquia, :zona_od, CAST(:datos AS jsonb)
            )
            RETURNING id, fecha_registro
            """
        )
        result = await self.session.execute(
            sql,
            {
                "encuesta_id": str(encuesta_id),
                "client_submission_id": (
                    str(submission.client_submission_id)
                    if submission.client_submission_id
                    else None
                ),
                "cedula": submission.cedula_limpia,
                "parroquia": submission.parroquia,
                "zona_od": submission.zona_od,
                "datos": json.dumps(submission.data, ensure_ascii=False),
            },
        )
        return dict(result.mappings().one())

    async def aggregate_by_parroquia(
        self, encuesta_id: UUID
    ) -> List[ParroquiaCountOut]:
        sql = text(
            """
            SELECT
                parroquia,
                COUNT(*)::int AS total_respuestas,
                ROUND(100.0 * COUNT(*) / NULLIF(SUM(COUNT(*)) OVER (), 0), 2)::float AS porcentaje
            FROM respuestas_ciudadanas
            WHERE encuesta_id = :encuesta_id
            GROUP BY parroquia
            ORDER BY total_respuestas DESC
            """
        )
        rows = (
            await self.session.execute(sql, {"encuesta_id": str(encuesta_id)})
        ).mappings().all()
        return [ParroquiaCountOut(**r) for r in rows]

    async def aggregate_field_series(
        self, encuesta_id: UUID, campo: str
    ) -> EChartsSeriesOut:
        sql = text(
            """
            SELECT
                COALESCE(datos->>:campo, 'Sin respuesta') AS etiqueta,
                COUNT(*)::int AS total
            FROM respuestas_ciudadanas
            WHERE encuesta_id = :encuesta_id
            GROUP BY etiqueta
            ORDER BY total DESC
            """
        )
        rows = (
            await self.session.execute(
                sql, {"encuesta_id": str(encuesta_id), "campo": campo}
            )
        ).mappings().all()
        return EChartsSeriesOut(
            campo=campo,
            labels=[r["etiqueta"] for r in rows],
            values=[r["total"] for r in rows],
        )

    async def aggregate_od_matrix(self, encuesta_id: UUID) -> List[MatrizODRowOut]:
        sql = text(
            """
            SELECT
                v.viaje->>'zona_od_origen' AS zona_origen,
                v.viaje->>'zona_od_destino' AS zona_destino,
                COUNT(*)::int AS total_viajes,
                ROUND(AVG(NULLIF(trim(v.viaje->>'tiempo_viaje_min'), '')::NUMERIC), 1)::float AS tiempo_promedio_min,
                ROUND(AVG(NULLIF(trim(v.viaje->>'costo_viaje_bs'), '')::NUMERIC), 2)::float AS costo_promedio_bs
            FROM respuestas_ciudadanas r
            CROSS JOIN LATERAL jsonb_array_elements(
                CASE
                    WHEN jsonb_typeof(r.datos->'viajes') = 'array' THEN r.datos->'viajes'
                    ELSE '[]'::jsonb
                END
            ) AS v(viaje)
            WHERE r.encuesta_id = :encuesta_id
              AND v.viaje->>'zona_od_origen' IS NOT NULL
              AND v.viaje->>'zona_od_destino' IS NOT NULL
            GROUP BY zona_origen, zona_destino
            ORDER BY total_viajes DESC
            """
        )
        rows = (
            await self.session.execute(sql, {"encuesta_id": str(encuesta_id)})
        ).mappings().all()
        return [MatrizODRowOut(**r) for r in rows]


# =============================================================================
# 3. CAPA DE SERVICIO (Lógica de Negocio, Idempotencia y Control de Errores)
# =============================================================================


class SurveyService:
    def __init__(self, repo: SurveyRepository) -> None:
        self.repo = repo

    async def register_participation(
        self, encuesta_id: UUID, submission: FormioSubmissionIn
    ) -> SubmissionReceiptOut:
        # 1. Verificar idempotencia si viene desde cola offline (client_submission_id)
        if submission.client_submission_id:
            existing = await self.repo.get_by_client_submission_id(
                submission.client_submission_id
            )
            if existing:
                return SubmissionReceiptOut(
                    id=existing["id"],
                    fecha_registro=existing["fecha_registro"],
                    idempotent_replay=True,
                    mensaje="Participación sincronizada previamente (idempotente).",
                )

        # 2. Insertar y manejar restricción de cédula única por encuesta
        try:
            created = await self.repo.insert_submission(encuesta_id, submission)
            await self.repo.session.commit()
            # Log estructurado sin exponer PII (cédula omitida deliberadamente)
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
            await self.repo.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=ProblemDetailOut(
                    code="DUPLICATE_PARTICIPATION",
                    title="Participación duplicada",
                    detail="La cédula indicada ya participó en esta consulta pública.",
                    field="cedula",
                ).model_dump(),
            ) from exc


# =============================================================================
# 4. CAPA DE TRANSPORTE HTTP (FastAPI Router)
# =============================================================================

router = APIRouter(prefix="/api/v1/encuestas", tags=["Encuestas Municipales"])


async def get_db() -> AsyncSession:
    """Placeholder de dependencia para inyección de AsyncSession."""
    raise NotImplementedError("Inyectar sesión asíncrona de SQLAlchemy (asyncpg).")


def get_survey_service(db: AsyncSession = Depends(get_db)) -> SurveyService:
    return SurveyService(SurveyRepository(db))


@router.post(
    "/{encuesta_id}/respuestas",
    response_model=SubmissionReceiptOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registra una participación ciudadana o encuesta PDUL con soporte offline idempotente",
)
async def registrar_respuesta(
    encuesta_id: UUID,
    submission: FormioSubmissionIn,
    service: SurveyService = Depends(get_survey_service),
) -> SubmissionReceiptOut:
    return await service.register_participation(encuesta_id, submission)


@router.get(
    "/{encuesta_id}/resultados-parroquia",
    response_model=List[ParroquiaCountOut],
    summary="Conteo agrupado por parroquia para mapa coroplético en Leaflet",
)
async def obtener_resultados_parroquia(
    encuesta_id: UUID,
    service: SurveyService = Depends(get_survey_service),
) -> List[ParroquiaCountOut]:
    return await service.repo.aggregate_by_parroquia(encuesta_id)


@router.get(
    "/{encuesta_id}/metricas",
    response_model=EChartsSeriesOut,
    summary="Serie formateada (labels, values) para gráficos Apache ECharts",
)
async def obtener_metricas_campo(
    encuesta_id: UUID,
    campo: str = Query(..., pattern=r"^[a-z][a-z0-9_]*$"),
    service: SurveyService = Depends(get_survey_service),
) -> EChartsSeriesOut:
    return await service.repo.aggregate_field_series(encuesta_id, campo)


@router.get(
    "/{encuesta_id}/matriz-od",
    response_model=List[MatrizODRowOut],
    summary="Matriz Origen-Destino agregada desde la grilla de viajes (PDUL)",
)
async def obtener_matriz_od(
    encuesta_id: UUID,
    service: SurveyService = Depends(get_survey_service),
) -> List[MatrizODRowOut]:
    return await service.repo.aggregate_od_matrix(encuesta_id)
