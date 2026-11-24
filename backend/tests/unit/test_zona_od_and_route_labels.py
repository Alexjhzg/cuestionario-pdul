"""Pruebas unitarias para zona_od ampliada y etiquetas legibles de las 103 rutas de Maturín."""

from backend.app.schemas.submission import FormioSubmissionIn
from backend.app.services.question_analytics import (
    CUSTOM_FIELD_LABELS,
    aggregate_all_survey_questions,
)


def test_zona_od_accepts_long_text_and_truncates_indexed_column_at_120() -> None:
    medium_zone = "Sector Tipuro Norte frente a Palma Real"  # > 30 chars
    sub_medium = FormioSubmissionIn(
        data={"parroquia": "boqueron", "zona_residencia_od": medium_zone}
    )
    assert sub_medium.zona_od == medium_zone
    assert sub_medium.data["zona_od"] == medium_zone

    very_long_zone = "Z" * 160
    sub_long = FormioSubmissionIn(
        data={"parroquia": "boqueron", "zona_residencia_od": very_long_zone}
    )
    assert sub_long.zona_od is not None
    assert len(sub_long.zona_od) == 120
    assert sub_long.data["zona_residencia_od"] == very_long_zone


def test_analytics_humanizes_rutas_tp_utilizadas_from_catalog_for_list_and_dict() -> None:
    rutas_map = CUSTOM_FIELD_LABELS["rutas_tp_utilizadas"]
    assert len(rutas_map) >= 104  # 103 rutas oficiales + 'otra'
    assert (
        rutas_map["ruta_01_y_05_union_de_conductores_lucas_perez"]
        == 'RUTA 01 Y 05 UNION DE CONDUCTORES "LUCAS PEREZ"'
    )

    rows = [
        {
            "rutas_tp_utilizadas": [
                "ruta_01_y_05_union_de_conductores_lucas_perez",
                "otra",
            ]
        },
        {
            "rutas_tp_utilizadas": {
                "ruta_02_a_civil_linea_conductores_la_pica": True,
                "ruta_01_y_05_union_de_conductores_lucas_perez": True,
            }
        },
    ]

    metrics = aggregate_all_survey_questions(schema={}, rows=rows)
    rutas_metric = next(m for m in metrics if m.clave == "rutas_tp_utilizadas")

    assert rutas_metric.total_respuestas == 2
    assert 'RUTA 01 Y 05 UNION DE CONDUCTORES "LUCAS PEREZ"' in rutas_metric.labels
    assert "RUTA 02 / A. CIVIL LINEA CONDUCTORES LA PICA" in rutas_metric.labels
    assert "Otra" in rutas_metric.labels
    idx_lucas = rutas_metric.labels.index(
        'RUTA 01 Y 05 UNION DE CONDUCTORES "LUCAS PEREZ"'
    )
    assert rutas_metric.values[idx_lucas] == 2
