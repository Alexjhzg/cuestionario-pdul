"""Servicio de agregación y análisis pregunta por pregunta para el Dashboard Municipal.

Delega catálogos de etiquetas, configuración de métricas por sección y lógica de
agregación a `backend.app.services.question_analytics_parts`, preservando todos los símbolos públicos.
"""

from backend.app.services.question_analytics_parts.aggregator import (
    _bucket_age,
    _bucket_trip_cost,
    _bucket_trip_time,
    aggregate_all_survey_questions,
)
from backend.app.services.question_analytics_parts.config import QUESTIONS_METRIC_CONFIG
from backend.app.services.question_analytics_parts.labels import (
    COMMON_LABELS,
    CUSTOM_FIELD_LABELS,
    _build_options_lookup,
    _humanize_value,
)

__all__ = [
    "COMMON_LABELS",
    "CUSTOM_FIELD_LABELS",
    "QUESTIONS_METRIC_CONFIG",
    "_bucket_age",
    "_bucket_trip_cost",
    "_bucket_trip_time",
    "_build_options_lookup",
    "_humanize_value",
    "aggregate_all_survey_questions",
]
