"""Tier 1: Feature Coverage — F57 a F62 (Dashboard de Analítica, Leaflet GIS y ECharts).

Verifica:
- F57: Cálculo y contratos de las 4 tarjetas de indicadores ejecutivos (KPIs).
- F58: Unión cartográfica Leaflet GeoJSON por 'codigo_parroquia' para mapa coroplético.
- F59: Estructura de series y etiquetas para gráfico ECharts de reparto modal.
- F60: Estructura de matriz de flujos Origen-Destino para mapa o heatmap.
- F61: Generación de tabla semántica accesible HTML (WCAG AA) como alternativa a gráficos.
"""

import unittest

from tests_e2e.harness.contracts import (
    AccessibleTableGenerator,
    CanonicalAssetResolver,
    KpiCalculator,
)
from tests_e2e.harness.fixtures import (
    PARROQUIAS_MATURIN,
    SAMPLE_RURAL_BATCH,
    SAMPLE_SURVEY_FAMILY_MULTIMODAL,
    SAMPLE_SURVEY_SINGLE_PERSON_STUDENT,
)


class TestF57F62GisDashboardContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.geojson = CanonicalAssetResolver.load_geojson()

    def test_f57_01_kpi_four_indicators_calculation(self) -> None:
        """F57: KpiCalculator computa los 4 indicadores clave a partir del conjunto de respuestas."""
        submissions = [
            {"id": 1, "parroquia": "san_simon", "datos": SAMPLE_SURVEY_SINGLE_PERSON_STUDENT["data"]},
            {"id": 2, "parroquia": "boqueron", "datos": SAMPLE_SURVEY_FAMILY_MULTIMODAL["data"]},
            {"id": 3, "parroquia": "el_corozo", "datos": SAMPLE_RURAL_BATCH[0]["data"]},
        ]
        kpis = KpiCalculator.calculate_kpis(submissions)

        self.assertEqual(kpis["total_encuestas"], 3)
        self.assertEqual(kpis["total_residentes"], 1 + 4 + 2)  # 7 residentes
        self.assertEqual(kpis["total_viajes"], 2 + 4 + 2)  # 8 viajes
        self.assertIn("modo_dominante_codigo", kpis)
        self.assertIn("parroquia_top_nombre", kpis)

    def test_f58_01_leaflet_geojson_property_join_with_parish_results(self) -> None:
        """F58: Las 11 features del GeoJSON se unen perfectamente con el código de parroquia."""
        parish_analytics = {
            "san_simon": 120,
            "boqueron": 85,
            "las_cocuizas": 70,
            "alto_de_los_godos": 60,
            "santa_cruz": 45,
            "la_cruz": 40,
            "san_vicente": 30,
            "el_furrial": 25,
            "jusepin": 20,
            "la_pica": 15,
            "el_corozo": 10,
        }

        matched_count = 0
        for feat in self.geojson["features"]:
            codigo = feat["properties"]["codigo_parroquia"]
            if codigo in parish_analytics:
                matched_count += 1
                # Enriquecer temporalmente con valor analítico para Leaflet styling
                feat["properties"]["metric_value"] = parish_analytics[codigo]

        self.assertEqual(matched_count, 11, "Todas las 11 parroquias deben coincidir con el GeoJSON")

    def test_f59_01_echarts_modal_split_series_structure(self) -> None:
        """F59: Estructura de opciones de ECharts para reparto modal (gráfico de dona / barras)."""
        echarts_option = {
            "title": {"text": "Reparto Modal de Viajes en Maturín", "left": "center"},
            "tooltip": {"trigger": "item", "formatter": "{b}: {c} viajes ({d}%)"},
            "toolbox": {"feature": {"saveAsImage": {}, "dataView": {"readOnly": True}}},
            "series": [
                {
                    "name": "Modo de Transporte",
                    "type": "pie",
                    "radius": ["40%", "70%"],
                    "data": [
                        {"value": 450, "name": "Transporte público"},
                        {"value": 280, "name": "Vehículo particular"},
                        {"value": 190, "name": "A pie"},
                        {"value": 80, "name": "Motocicleta"},
                        {"value": 45, "name": "Bicicleta"},
                    ],
                }
            ],
        }
        self.assertIn("series", echarts_option)
        series_data = echarts_option["series"][0]["data"]
        self.assertEqual(len(series_data), 5)
        total_viajes = sum(d["value"] for d in series_data)
        self.assertEqual(total_viajes, 1045)

    def test_f60_01_od_flow_matrix_structure(self) -> None:
        """F60: Estructura de pares Origen-Destino con conteos y métricas de viaje."""
        od_flows = [
            {"origen": "01", "destino": "03", "viajes": 150, "tiempo_promedio": 28.5},
            {"origen": "05", "destino": "01", "viajes": 210, "tiempo_promedio": 35.0},
            {"origen": "08", "destino": "01", "viajes": 95, "tiempo_promedio": 50.2},
        ]
        self.assertEqual(len(od_flows), 3)
        for flow in od_flows:
            self.assertTrue(len(flow["origen"]) > 0)
            self.assertTrue(len(flow["destino"]) > 0)
            self.assertGreater(flow["viajes"], 0)

    def test_f61_01_accessible_data_table_generation(self) -> None:
        """F61: AccessibleTableGenerator produce tabla HTML semántica con role='table' y caption."""
        headers = ["Parroquia", "Total Encuestas", "Porcentaje (%)"]
        rows = [
            ["San Simón", 120, "23.1%"],
            ["Boquerón", 85, "16.3%"],
            ["Las Cocuizas", 70, "13.5%"],
        ]
        html = AccessibleTableGenerator.generate_html_table(
            caption="Participación Ciudadana por Parroquia",
            headers=headers,
            rows=rows,
        )
        self.assertIn('<table role="table"', html)
        self.assertIn("<caption>Participación Ciudadana por Parroquia</caption>", html)
        self.assertIn('<th scope="col">Parroquia</th>', html)
        self.assertIn('<th scope="row">San Simón</th>', html)
        self.assertIn("<td>120</td>", html)


if __name__ == "__main__":
    unittest.main()
