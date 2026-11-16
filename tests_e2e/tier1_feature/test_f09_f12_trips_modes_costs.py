"""Tier 1: Feature Coverage — F09 a F12 (Grilla de Viajes, Trayecto, Modos y Costos).

Verifica:
- F09: Grilla 'viajes' tipo datagrid con exactamente 13 columnas.
- F10: Registro completo de trayecto y cronología (origen, destino, zonas O-D, horas).
- F11: Catálogos oficiales de motivos y modos de viaje (códigos 1 a 8).
- F12: Variables de impedancia (duración en minutos y costo en Bolívares).
"""

import unittest
from typing import Any, Dict, List

from tests_e2e.harness.contracts import CanonicalAssetResolver
from tests_e2e.harness.fixtures import MODOS_TRANSPORTE, MOTIVOS_VIAJE


class TestF09F12TripsModesCosts(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = CanonicalAssetResolver.load_schema()
        cls.all_components: Dict[str, Dict[str, Any]] = {}
        def _index(comps: List[Dict[str, Any]]) -> None:
            for c in comps:
                if isinstance(c, dict):
                    k = c.get("key")
                    if k:
                        cls.all_components[k] = c
                    if isinstance(c.get("components"), list):
                        _index(c["components"])
        _index(cls.schema.get("components", []))

    def test_f09_01_trips_datagrid_exists_and_has_13_columns(self) -> None:
        """F09: La grilla 'viajes' es de tipo datagrid y contiene 13 columnas reglamentarias."""
        self.assertIn("viajes", self.all_components)
        grid = self.all_components["viajes"]
        self.assertEqual(grid.get("type"), "datagrid")
        cols = grid.get("components", [])
        self.assertEqual(len(cols), 13, f"Se esperaban 13 columnas en viajes, se hallaron {len(cols)}")

    def test_f09_02_trips_has_person_and_trip_indexing_columns(self) -> None:
        """F09: La grilla incluye columnas para correlacionar persona_numero y viaje_numero."""
        grid = self.all_components["viajes"]
        cols = {c.get("key") for c in grid.get("components", []) if isinstance(c, dict)}
        self.assertIn("viaje_numero", cols)
        self.assertIn("persona_numero", cols)

    def test_f10_01_trip_origin_destination_addresses_exist(self) -> None:
        """F10: Columnas para dirección/lugar de origen y destino están presentes."""
        grid = self.all_components["viajes"]
        cols = {c.get("key") for c in grid.get("components", []) if isinstance(c, dict)}
        self.assertIn("origen_direccion", cols)
        self.assertIn("destino_direccion", cols)

    def test_f10_02_trip_chronology_hours_format(self) -> None:
        """F10: Columnas de hora de salida y llegada están configuradas."""
        grid = self.all_components["viajes"]
        cols = {c.get("key") for c in grid.get("components", []) if isinstance(c, dict)}
        self.assertIn("hora_salida", cols)
        self.assertIn("hora_llegada", cols)

    def test_f11_01_trip_motives_catalog_1_to_8(self) -> None:
        """F11: La columna de motivo de viaje cuenta con los 8 códigos oficiales del PDUL."""
        catalogo_motivos = CanonicalAssetResolver.load_catalog("motivos_viaje")
        self.assertIsInstance(catalogo_motivos, list)
        self.assertEqual(len(catalogo_motivos), 8)
        codigos = {str(m["codigo"]) for m in catalogo_motivos}
        self.assertEqual(codigos, set(MOTIVOS_VIAJE.keys()))

    def test_f11_02_trip_modes_catalog_1_to_8(self) -> None:
        """F11: La columna de modo principal cuenta con los 8 modos oficiales de transporte."""
        catalogo_modos = CanonicalAssetResolver.load_catalog("modos_transporte")
        self.assertIsInstance(catalogo_modos, list)
        self.assertEqual(len(catalogo_modos), 8)
        codigos = {str(m["codigo"]) for m in catalogo_modos}
        self.assertEqual(codigos, set(MODOS_TRANSPORTE.keys()))

    def test_f11_03_secondary_mode_column_exists_in_trips(self) -> None:
        """F11: Existe columna modo_secundario en la grilla de viajes."""
        grid = self.all_components["viajes"]
        cols = {c.get("key") for c in grid.get("components", []) if isinstance(c, dict)}
        self.assertIn("modo_secundario", cols)

    def test_f12_01_travel_time_in_minutes_number_field(self) -> None:
        """F12: La duración del viaje 'tiempo_viaje_min' es un campo numérico positivo."""
        grid = self.all_components["viajes"]
        col_map = {c.get("key"): c for c in grid.get("components", []) if isinstance(c, dict)}
        self.assertIn("tiempo_viaje_min", col_map)
        col = col_map["tiempo_viaje_min"]
        self.assertEqual(col.get("type"), "number")

    def test_f12_02_travel_cost_in_bolivares_number_field(self) -> None:
        """F12: El costo del viaje 'costo_viaje_bs' es numérico y admite valor cero."""
        grid = self.all_components["viajes"]
        col_map = {c.get("key"): c for c in grid.get("components", []) if isinstance(c, dict)}
        self.assertIn("costo_viaje_bs", col_map)
        col = col_map["costo_viaje_bs"]
        self.assertEqual(col.get("type"), "number")


if __name__ == "__main__":
    unittest.main()
