import uuid
from typing import Any, Dict, List, Tuple
from sqlalchemy import func, select

from backend.app.infrastructure.repositories.base_survey_repo import (
    MODOS_TRANSPORTE_ETIQUETAS,
    BaseSurveyRepository,
)
from backend.app.models.respuesta import RespuestaCiudadana
from backend.app.schemas.analytics import (
    EChartsSeriesOut,
    MatrizODRowOut,
    ParroquiaCountOut,
    RepartoModalRowOut,
)


class SqliteSurveyRepository(BaseSurveyRepository):
    """Adaptador de persistencia para SQLite y pruebas unitarias/integración locales."""

    async def aggregate_by_parroquia(
        self, encuesta_id: uuid.UUID
    ) -> List[ParroquiaCountOut]:
        stmt = (
            select(
                RespuestaCiudadana.parroquia,
                func.count(RespuestaCiudadana.id).label("total"),
            )
            .where(RespuestaCiudadana.encuesta_id == encuesta_id)
            .group_by(RespuestaCiudadana.parroquia)
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

