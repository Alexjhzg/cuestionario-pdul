"""Tier 1: Feature Coverage — F01 a F03 (Esquema Base, Parroquias y Zonas O-D).

Verifica:
- F01: Estructura raíz, versión de esquema y metadatos de Form.io.
- F02: Catálogo estricto de las 11 parroquias oficiales de Maturín en snake_case.
- F03: Definición y restricciones de campos para códigos de zona O-D.
"""

import unittest
from pathlib import Path
from typing import Any, Dict, List

from tests_e2e.harness.contracts import (
    CanonicalAssetResolver,
    PydanticContractVerifier,
)
from tests_e2e.harness.fixtures import (
    PARROQUIAS_MATURIN,
    PARROQUIAS_NOMBRES,
)


class TestF01F03SchemaMetadataParishesZones(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = CanonicalAssetResolver.load_schema()
        cls.components: List[Dict[str, Any]] = cls.schema.get("components", [])
        cls.components_by_key = {
            c.get("key"): c for c in cls.components if isinstance(c, dict) and c.get("key")
        }

    def test_f01_01_schema_root_attributes_and_type(self) -> None:
        """F01: El esquema contiene display, title, name, path y components no vacío."""
        self.assertIsInstance(self.schema, dict)
        self.assertIn("display", self.schema)
        self.assertIn("title", self.schema)
        self.assertIn("components", self.schema)
        self.assertIsInstance(self.components, list)
        self.assertGreaterEqual(len(self.components), 5)

    def test_f01_02_schema_version_hidden_component(self) -> None:
        """F01: Existe el componente hidden con key 'schema_version'."""
        self.assertIn("schema_version", self.components_by_key)
        comp = self.components_by_key["schema_version"]
        self.assertEqual(comp.get("type"), "hidden")
        self.assertTrue(comp.get("defaultValue") or comp.get("default"))

    def test_f01_03_all_root_components_have_snake_case_keys(self) -> None:
        """F01: Todas las claves de primer nivel cumplen con el regex snake_case."""
        import re
        pattern = re.compile(r"^[a-z][a-z0-9_]*$")
        for comp in self.components:
            key = comp.get("key")
            if key:
                self.assertTrue(
                    pattern.match(key),
                    f"Clave raíz '{key}' no cumple snake_case ASCII puro",
                )

    def test_f02_01_parish_catalog_matches_11_official_codes(self) -> None:
        """F02: El catálogo de parroquias del municipio cuenta con exactamente 11 registros oficiales."""
        catalogo_parroquias = CanonicalAssetResolver.load_catalog("parroquias")
        self.assertIsInstance(catalogo_parroquias, list)
        self.assertEqual(len(catalogo_parroquias), 11)
        codigos = {p["codigo"] for p in catalogo_parroquias}
        self.assertEqual(codigos, set(PARROQUIAS_MATURIN))

    def test_f02_02_schema_contains_parish_field_with_official_values(self) -> None:
        """F02: El campo 'parroquia' en el esquema incluye las 11 opciones oficiales de Maturín."""
        # Puede estar en la raíz o dentro del panel de Sección I
        all_comps: List[Dict[str, Any]] = []
        def _recurse(comps: List[Dict[str, Any]]) -> None:
            for c in comps:
                all_comps.append(c)
                if isinstance(c.get("components"), list):
                    _recurse(c["components"])

        _recurse(self.components)
        parroquia_comp = next((c for c in all_comps if c.get("key") == "parroquia"), None)
        self.assertIsNotNone(parroquia_comp, "El campo 'parroquia' no fue encontrado en el formulario")

        data_values = (
            parroquia_comp.get("data", {}).get("values")
            or parroquia_comp.get("values")
            or []
        )
        self.assertGreaterEqual(len(data_values), 11)
        schema_parish_codes = {v.get("value") for v in data_values if isinstance(v, dict)}
        for p in PARROQUIAS_MATURIN:
            self.assertIn(p, schema_parish_codes, f"Falta la parroquia '{p}' en el campo parroquia")

    def test_f02_03_parish_validator_accepts_valid_and_rejects_invalid(self) -> None:
        """F02: Validador de contrato acepta parroquias válidas y rechaza códigos no existentes."""
        for p in PARROQUIAS_MATURIN:
            self.assertEqual(PydanticContractVerifier.validate_parish(p), p)
            self.assertEqual(PydanticContractVerifier.validate_parish(p.upper()), p)

        invalid_parishes = ["caracas", "maracaibo", "maturin_central", "", "123", "san-simon"]
        for invalid in invalid_parishes:
            with self.assertRaises(ValueError):
                PydanticContractVerifier.validate_parish(invalid)

    def test_f03_01_residence_od_zone_field_exists_in_schema(self) -> None:
        """F03: Existe el campo 'zona_residencia_od' en la sección de identificación residencial."""
        all_comps: List[Dict[str, Any]] = []
        def _recurse(comps: List[Dict[str, Any]]) -> None:
            for c in comps:
                all_comps.append(c)
                if isinstance(c.get("components"), list):
                    _recurse(c["components"])

        _recurse(self.components)
        zona_comp = next((c for c in all_comps if c.get("key") == "zona_residencia_od"), None)
        self.assertIsNotNone(zona_comp, "Falta el campo 'zona_residencia_od' en el esquema")
        self.assertIn(zona_comp.get("type"), ["textfield", "select", "number"])

    def test_f03_02_trips_datagrid_contains_od_zone_columns(self) -> None:
        """F03: La grilla de viajes contiene columnas para zona de origen y destino O-D."""
        all_comps: List[Dict[str, Any]] = []
        def _recurse(comps: List[Dict[str, Any]]) -> None:
            for c in comps:
                all_comps.append(c)
                if isinstance(c.get("components"), list):
                    _recurse(c["components"])

        _recurse(self.components)
        viajes_grid = next((c for c in all_comps if c.get("key") == "viajes"), None)
        self.assertIsNotNone(viajes_grid, "No se encontró el datagrid 'viajes'")
        trip_col_keys = {
            col.get("key") for col in viajes_grid.get("components", []) if isinstance(col, dict)
        }
        self.assertTrue(
            "zona_od_origen" in trip_col_keys or "zona_origen_od" in trip_col_keys,
            f"Falta columna de zona O-D de origen en viajes: {trip_col_keys}",
        )
        self.assertTrue(
            "zona_od_destino" in trip_col_keys or "zona_destino_od" in trip_col_keys,
            f"Falta columna de zona O-D de destino en viajes: {trip_col_keys}",
        )


if __name__ == "__main__":
    unittest.main()
