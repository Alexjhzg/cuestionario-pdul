"""Motor de agregación de métricas por pregunta del cuestionario PDUL."""

from collections import Counter
from typing import Any, Dict, List

from backend.app.schemas.analytics import PreguntaMetricaOut
from backend.app.services.analytics.labels_catalog import (
    _build_options_lookup,
    _humanize_value,
)
from backend.app.services.analytics.questions_config import QUESTIONS_METRIC_CONFIG


def _bucket_age(cv: Any) -> str:
    try:
        age = int(cv)
        if age < 18:
            return "Menor de 18 años"
        if age <= 35:
            return "18 a 35 años"
        if age <= 50:
            return "36 a 50 años"
        if age <= 65:
            return "51 a 65 años"
        return "Mayor de 65 años"
    except Exception:
        return str(cv)


def _bucket_trip_time(cv: Any) -> str:
    try:
        t = float(cv)
        if t <= 15:
            return "Hasta 15 min"
        if t <= 30:
            return "16 a 30 min"
        if t <= 45:
            return "31 a 45 min"
        if t <= 60:
            return "46 a 60 min"
        return "Más de 60 min"
    except Exception:
        return str(cv)


def _bucket_trip_cost(cv: Any) -> str:
    try:
        co = float(cv)
        if co == 0:
            return "0 Bs (Gratuito / A pie)"
        if co <= 15:
            return "1 a 15 Bs"
        if co <= 30:
            return "16 a 30 Bs"
        if co <= 50:
            return "31 a 50 Bs"
        return "Más de 50 Bs"
    except Exception:
        return str(cv)


def aggregate_all_survey_questions(
    schema: Dict[str, Any], rows: List[Dict[str, Any]]
) -> List[PreguntaMetricaOut]:
    """Agrega todas las preguntas predefinidas del cuestionario PDUL."""
    options_map = _build_options_lookup(schema)
    results: List[PreguntaMetricaOut] = []

    for cfg in QUESTIONS_METRIC_CONFIG:
        seccion = cfg["seccion"]
        clave = cfg["clave"]
        pregunta = cfg["pregunta"]
        tipo_grafico = cfg["tipo_grafico"]
        aliases = cfg["aliases"]

        counts: Counter[str] = Counter()
        total_respuestas = 0

        for r in rows:
            for a in aliases:
                if ":" in a:
                    parent, child = a.split(":", 1)
                    sub_items = r.get(parent, [])
                    if isinstance(sub_items, list):
                        for item in sub_items:
                            if isinstance(item, dict):
                                cv = item.get(child)
                                if cv is not None and cv != "":
                                    total_respuestas += 1
                                    if clave == "edad_residentes":
                                        label = _bucket_age(cv)
                                    elif clave == "tiempo_viaje_rangos":
                                        label = _bucket_trip_time(cv)
                                    elif clave == "costo_viaje_rangos":
                                        label = _bucket_trip_cost(cv)
                                    else:
                                        label = _humanize_value(child, cv, options_map)
                                    counts[label] += 1
                else:
                    if a in r and r[a] is not None and r[a] != "" and r[a] != []:
                        val = r[a]
                        total_respuestas += 1
                        if isinstance(val, dict):
                            for subk, subv in val.items():
                                if subv:
                                    lbl = _humanize_value(subk, subk, options_map)
                                    counts[lbl] += 1
                        elif isinstance(val, list):
                            for list_item in val:
                                lbl = _humanize_value(a, list_item, options_map)
                                counts[lbl] += 1
                        else:
                            lbl = _humanize_value(a, val, options_map)
                            counts[lbl] += 1
                        break

        sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        labels = [item[0] for item in sorted_items]
        values = [item[1] for item in sorted_items]

        results.append(
            PreguntaMetricaOut(
                seccion=seccion,
                clave=clave,
                pregunta=pregunta,
                tipo_grafico=tipo_grafico,
                total_respuestas=total_respuestas,
                labels=labels,
                values=values,
            )
        )

    return results
