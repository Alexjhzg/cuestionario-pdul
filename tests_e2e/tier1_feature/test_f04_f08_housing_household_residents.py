"""Tier 1: Feature Coverage — F04 a F08 (Vivienda, Hogar, Grilla y Perfil de Residentes, Vehículos).

Verifica:
- F04: Tipología habitacional, especificación 'otro' y recuento de cuartos.
- F05: Datos del hogar (grupos de gastos, número de hogar, densidad y tenencia).
- F06: Grilla de residentes datagrid con sus 13 columnas reglamentarias.
- F07: Variables demográficas y sociolaborales del perfil de residentes.
- F08: Disponibilidad vehicular (licencia, posesión, tipo y cantidad condicional).
"""

import unittest
from typing import Any, Dict, List

from tests_e2e.harness.contracts import CanonicalAssetResolver


class TestF04F08HousingHouseholdResidents(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = CanonicalAssetResolver.load_schema()
        cls.components: List[Dict[str, Any]] = cls.schema.get("components", [])

        # Indexar todos los componentes recursivamente
        cls.all_components: Dict[str, Dict[str, Any]] = {}
        def _index(comps: List[Dict[str, Any]]) -> None:
            for c in comps:
                if isinstance(c, dict):
                    k = c.get("key")
                    if k:
                        cls.all_components[k] = c
                    if isinstance(c.get("components"), list):
                        _index(c["components"])
        _index(cls.components)

    def test_f04_01_housing_type_radio_component_and_options(self) -> None:
        """F04: El tipo de vivienda es de tipo radio y cuenta con opciones estándar."""
        self.assertIn("tipo_vivienda", self.all_components)
        comp = self.all_components["tipo_vivienda"]
        self.assertIn(comp.get("type"), ["radio", "select"])
        values = comp.get("values") or comp.get("data", {}).get("values") or []
        option_values = {v.get("value") for v in values if isinstance(v, dict)}
        # Comprobar presencia de opciones clave como casa, apartamento, rancho/otro
        self.assertTrue(
            any("casa" in v for v in option_values),
            f"Falta opción de casa en tipo_vivienda: {option_values}",
        )
        self.assertTrue(
            any("apartamento" in v for v in option_values),
            f"Falta opción de apartamento en tipo_vivienda: {option_values}",
        )

    def test_f04_02_housing_other_conditional_field(self) -> None:
        """F04: Existe campo condicional para especificar 'otro' tipo de vivienda."""
        self.assertIn("tipo_vivienda_otro", self.all_components)
        comp = self.all_components["tipo_vivienda_otro"]
        self.assertEqual(comp.get("type"), "textfield")
        cond = comp.get("conditional", {})
        self.assertEqual(cond.get("when"), "tipo_vivienda")

    def test_f04_03_total_rooms_number_field_constraints(self) -> None:
        """F04: El total de cuartos de la vivienda es numérico y con límite inferior positivo."""
        self.assertIn("total_cuartos_vivienda", self.all_components)
        comp = self.all_components["total_cuartos_vivienda"]
        self.assertEqual(comp.get("type"), "number")
        val = comp.get("validate", {})
        if "min" in val:
            self.assertGreaterEqual(val["min"], 1)

    def test_f05_01_household_data_fields_exist(self) -> None:
        """F05: Existen campos para grupos de gastos, número de hogar y cuartos de dormir."""
        self.assertIn("grupos_gastos_separados", self.all_components)
        self.assertIn("hogar_numero", self.all_components)
        self.assertIn("cuartos_dormir_hogar", self.all_components)
        self.assertIn("numero_personas_hogar", self.all_components)

    def test_f05_02_household_tenure_radio_and_other_conditional(self) -> None:
        """F05: Régimen de tenencia cuenta con opciones y campo condicional 'otro'."""
        self.assertIn("tenencia_vivienda", self.all_components)
        comp = self.all_components["tenencia_vivienda"]
        self.assertIn(comp.get("type"), ["radio", "select"])

        self.assertIn("tenencia_vivienda_otro", self.all_components)
        otro = self.all_components["tenencia_vivienda_otro"]
        self.assertEqual(otro.get("conditional", {}).get("when"), "tenencia_vivienda")

    def test_f06_01_residents_datagrid_exists_with_13_columns(self) -> None:
        """F06: La grilla 'residentes' es de tipo datagrid y contiene exactamente 13 columnas."""
        self.assertIn("residentes", self.all_components)
        grid = self.all_components["residentes"]
        self.assertEqual(grid.get("type"), "datagrid")
        cols = grid.get("components", [])
        self.assertEqual(len(cols), 13, f"Se esperaban 13 columnas en residentes, se hallaron {len(cols)}")

    def test_f07_01_resident_profile_demographic_and_social_columns(self) -> None:
        """F07: Las columnas de residentes cubren número, parentesco, sexo, edad, educación y ocupación."""
        grid = self.all_components["residentes"]
        cols = {c.get("key") for c in grid.get("components", []) if isinstance(c, dict)}

        expected_core_cols = {
            "persona_numero",
            "nombre_apellido",
            "parentesco_jefe_hogar",
            "sexo",
            "edad",
            "sabe_leer_escribir",
            "nivel_educativo",
            "ocupacion_principal",
            "medio_transporte_habitual",
        }
        for ec in expected_core_cols:
            self.assertIn(ec, cols, f"Columna requerida '{ec}' ausente en grilla de residentes")

    def test_f08_01_vehicle_availability_columns_in_residents_grid(self) -> None:
        """F08: Las columnas de disponibilidad vehicular están presentes en la grilla."""
        grid = self.all_components["residentes"]
        cols = {c.get("key") for c in grid.get("components", []) if isinstance(c, dict)}

        vehicle_cols = {
            "posee_licencia",
            "tiene_vehiculo_disponible",
            "tipo_vehiculo",
            "cantidad_vehiculo",
        }
        for vc in vehicle_cols:
            self.assertIn(vc, cols, f"Columna vehicular '{vc}' ausente en residentes")

    def test_f08_02_vehicle_conditional_display_rules(self) -> None:
        """F08: Las columnas tipo_vehiculo y cantidad_vehiculo tienen reglas condicionales."""
        grid = self.all_components["residentes"]
        col_map = {c.get("key"): c for c in grid.get("components", []) if isinstance(c, dict)}

        tipo_v = col_map["tipo_vehiculo"]
        cant_v = col_map["cantidad_vehiculo"]

        self.assertIn("conditional", tipo_v)
        self.assertEqual(tipo_v["conditional"].get("when"), "tiene_vehiculo_disponible")
        self.assertIn("conditional", cant_v)
        self.assertEqual(cant_v["conditional"].get("when"), "tiene_vehiculo_disponible")


if __name__ == "__main__":
    unittest.main()
