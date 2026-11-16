import json
import uuid
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.encuesta import Encuesta
from backend.app.models.respuesta import RespuestaCiudadana
from backend.app.schemas.analytics import (
    EChartsSeriesOut,
    KpiMetricsOut,
    MatrizODRowOut,
    ParroquiaCountOut,
    PreguntaMetricaOut,
    RepartoModalRowOut,
)
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


class SurveyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _is_postgres(self) -> bool:
        bind = self.session.bind
        if bind is not None and hasattr(bind, "dialect"):
            return bind.dialect.name == "postgresql"
        return True

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

    async def aggregate_by_parroquia(
        self, encuesta_id: uuid.UUID
    ) -> List[ParroquiaCountOut]:
        if self._is_postgres():
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
        else:
            # Fallback Python / SQLite para pruebas aisladas
            stmt = select(
                RespuestaCiudadana.parroquia,
                func.count(RespuestaCiudadana.id).label("total"),
            ).where(RespuestaCiudadana.encuesta_id == encuesta_id).group_by(
                RespuestaCiudadana.parroquia
            )
            rows = (await self.session.execute(stmt)).all()
            total_sum = sum(r[1] for r in rows) or 1
            return [
                ParroquiaCountOut(
                    parroquia=r[0],
                    total_respuestas=r[1],
                    porcentaje=round(100.0 * r[1] / total_sum, 2),
                )
                for r in sorted(rows, key=lambda x: x[1], reverse=True)
            ]

    async def aggregate_field_series(
        self, encuesta_id: uuid.UUID, campo: str
    ) -> EChartsSeriesOut:
        if self._is_postgres():
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
        else:
            stmt = select(RespuestaCiudadana.datos).where(
                RespuestaCiudadana.encuesta_id == encuesta_id
            )
            rows = (await self.session.execute(stmt)).scalars().all()
            counts: Dict[str, int] = {}
            for d in rows:
                val = d.get(campo) if isinstance(d, dict) else None
                label = str(val) if val is not None else "Sin respuesta"
                counts[label] = counts.get(label, 0) + 1

            sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
            return EChartsSeriesOut(
                campo=campo,
                labels=[k for k, _ in sorted_items],
                values=[v for _, v in sorted_items],
            )

    async def aggregate_od_matrix(self, encuesta_id: uuid.UUID) -> List[MatrizODRowOut]:
        if self._is_postgres():
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
        else:
            stmt = select(RespuestaCiudadana.datos).where(
                RespuestaCiudadana.encuesta_id == encuesta_id
            )
            rows = (await self.session.execute(stmt)).scalars().all()
            pairs: Dict[Tuple[str, str], Dict[str, Any]] = {}
            for d in rows:
                if isinstance(d, dict) and isinstance(d.get("viajes"), list):
                    for viaje in d["viajes"]:
                        if isinstance(viaje, dict):
                            o = viaje.get("zona_od_origen")
                            dst = viaje.get("zona_od_destino")
                            if o and dst:
                                pair = (str(o), str(dst))
                                if pair not in pairs:
                                    pairs[pair] = {
                                        "total": 0,
                                        "tiempos": [],
                                        "costos": [],
                                    }
                                pairs[pair]["total"] += 1
                                t = viaje.get("tiempo_viaje_min")
                                if t not in (None, ""):
                                    try:
                                        pairs[pair]["tiempos"].append(float(t))
                                    except (ValueError, TypeError):
                                        pass
                                c = viaje.get("costo_viaje_bs")
                                if c not in (None, ""):
                                    try:
                                        pairs[pair]["costos"].append(float(c))
                                    except (ValueError, TypeError):
                                        pass

            results = []
            for (zo, zd), stats in sorted(
                pairs.items(), key=lambda x: x[1]["total"], reverse=True
            ):
                avg_t = (
                    round(sum(stats["tiempos"]) / len(stats["tiempos"]), 1)
                    if stats["tiempos"]
                    else None
                )
                avg_c = (
                    round(sum(stats["costos"]) / len(stats["costos"]), 2)
                    if stats["costos"]
                    else None
                )
                results.append(
                    MatrizODRowOut(
                        zona_origen=zo,
                        zona_destino=zd,
                        total_viajes=stats["total"],
                        tiempo_promedio_min=avg_t,
                        costo_promedio_bs=avg_c,
                    )
                )
            return results

    async def aggregate_modal_split(
        self, encuesta_id: uuid.UUID
    ) -> List[RepartoModalRowOut]:
        if self._is_postgres():
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
        else:
            stmt = select(RespuestaCiudadana.datos).where(
                RespuestaCiudadana.encuesta_id == encuesta_id
            )
            rows = (await self.session.execute(stmt)).scalars().all()
            modos: Dict[str, int] = {}
            for d in rows:
                if isinstance(d, dict) and isinstance(d.get("viajes"), list):
                    for viaje in d["viajes"]:
                        if isinstance(viaje, dict):
                            m = viaje.get("modo_principal")
                            if m:
                                m_str = str(m)
                                modos[m_str] = modos.get(m_str, 0) + 1

            total_m = sum(modos.values()) or 1
            return [
                RepartoModalRowOut(
                    modo=k,
                    etiqueta=MODOS_TRANSPORTE_ETIQUETAS.get(k, f"Modo {k}"),
                    total_viajes=v,
                    porcentaje=round(100.0 * v / total_m, 2),
                )
                for k, v in sorted(modos.items(), key=lambda x: x[1], reverse=True)
            ]

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
