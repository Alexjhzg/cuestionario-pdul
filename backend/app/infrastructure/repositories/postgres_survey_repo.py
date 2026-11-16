import uuid
from typing import List
from sqlalchemy import text

from backend.app.infrastructure.repositories.base_survey_repo import (
    MODOS_TRANSPORTE_ETIQUETAS,
    BaseSurveyRepository,
)
from backend.app.schemas.analytics import (
    EChartsSeriesOut,
    MatrizODRowOut,
    ParroquiaCountOut,
    RepartoModalRowOut,
)


class PostgresSurveyRepository(BaseSurveyRepository):
    """Adaptador de persistencia optimizado para PostgreSQL con consultas JSONB nativas."""

    async def aggregate_by_parroquia(
        self, encuesta_id: uuid.UUID
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
        self, encuesta_id: uuid.UUID, campo: str
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

    async def aggregate_od_matrix(self, encuesta_id: uuid.UUID) -> List[MatrizODRowOut]:
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

    async def aggregate_modal_split(
        self, encuesta_id: uuid.UUID
    ) -> List[RepartoModalRowOut]:
        sql = text(
            """
            WITH viajes_desagregados AS (
                SELECT
                    v.viaje->>'modo_principal' AS modo
                FROM respuestas_ciudadanas r
                CROSS JOIN LATERAL jsonb_array_elements(
                    CASE
                        WHEN jsonb_typeof(r.datos->'viajes') = 'array' THEN r.datos->'viajes'
                        ELSE '[]'::jsonb
                    END
                ) AS v(viaje)
                WHERE r.encuesta_id = :encuesta_id
                  AND v.viaje->>'modo_principal' IS NOT NULL
            )
            SELECT
                modo,
                COUNT(*)::int AS total_viajes,
                ROUND(100.0 * COUNT(*) / NULLIF(SUM(COUNT(*)) OVER (), 0), 2)::float AS porcentaje
            FROM viajes_desagregados
            GROUP BY modo
            ORDER BY total_viajes DESC
            """
        )
        rows = (
            await self.session.execute(sql, {"encuesta_id": str(encuesta_id)})
        ).mappings().all()
        return [
            RepartoModalRowOut(
                modo=r["modo"],
                etiqueta=MODOS_TRANSPORTE_ETIQUETAS.get(
                    str(r["modo"]), f"Modo {r['modo']}"
                ),
                total_viajes=r["total_viajes"],
                porcentaje=r["porcentaje"],
            )
            for r in rows
        ]

