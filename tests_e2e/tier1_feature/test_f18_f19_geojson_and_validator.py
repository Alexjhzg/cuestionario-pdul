"""Tier 1: Feature Coverage — F18 y F19 (GeoJSON Parroquias y Validador Form.io).

Verifica:
- F18: Archivo GeoJSON oficial con los 11 polígonos de Maturín, atributos y coordenadas.
- F19: Ejecución del validador oficial Form.io, rechazo de dominios externos y claves inválidas.
"""

import json
from pathlib import Path
import subprocess
import sys
import unittest

from tests_e2e.harness.contracts import (
    CanonicalAssetResolver,
    FormioSchemaValidator,
)
from tests_e2e.harness.fixtures import PARROQUIAS_MATURIN


class TestF18F19GeojsonAndValidator(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.geojson = CanonicalAssetResolver.load_geojson()
        cls.schema = CanonicalAssetResolver.load_schema()

    def test_f18_01_geojson_is_feature_collection(self) -> None:
        """F18: El archivo GeoJSON es de tipo 'FeatureCollection' con lista de features."""
        self.assertEqual(self.geojson.get("type"), "FeatureCollection")
        self.assertIn("features", self.geojson)
        self.assertIsInstance(self.geojson["features"], list)

    def test_f18_02_geojson_contains_exact_11_features(self) -> None:
        """F18: La capa contiene exactamente 11 features correspondientes a las 11 parroquias."""
        features = self.geojson["features"]
        self.assertEqual(
            len(features),
            11,
            f"Se esperaban 11 polígonos parroquiales, se hallaron {len(features)}",
        )

    def test_f18_03_geojson_features_have_required_properties(self) -> None:
        """F18: Cada feature tiene 'codigo_parroquia' (snake_case) y 'nombre_parroquia'."""
        features = self.geojson["features"]
        codigos_presentes = set()
        for idx, feat in enumerate(features):
            props = feat.get("properties", {})
            self.assertIn("codigo_parroquia", props, f"Feature [{idx}] carece de codigo_parroquia")
            self.assertIn("nombre_parroquia", props, f"Feature [{idx}] carece de nombre_parroquia")
            codigo = props["codigo_parroquia"]
            self.assertIn(
                codigo,
                PARROQUIAS_MATURIN,
                f"Código '{codigo}' en feature [{idx}] no pertenece a las 11 parroquias oficiales",
            )
            codigos_presentes.add(codigo)

        self.assertEqual(codigos_presentes, set(PARROQUIAS_MATURIN))

    def test_f18_04_geojson_coordinates_bounded_within_maturin(self) -> None:
        """F18: Las coordenadas geométricas caen dentro de los límites espaciales del Municipio Maturín."""
        # Maturín se sitúa aproximadamente entre Lat 9.0 a 10.5 N y Lon -64.0 a -62.5 W
        features = self.geojson["features"]
        for idx, feat in enumerate(features):
            geom = feat.get("geometry", {})
            self.assertIn(geom.get("type"), ["Polygon", "MultiPolygon"])
            coords = geom.get("coordinates", [])
            self.assertTrue(len(coords) > 0, f"Feature [{idx}] tiene coordenadas vacías")

            # Muestrear el primer anillo
            ring = coords[0] if geom["type"] == "Polygon" else coords[0][0]
            for pt in ring:
                lon, lat = pt[0], pt[1]
                self.assertGreaterEqual(lat, 8.5, f"Latitud fuera de rango inferior: {lat}")
                self.assertLessEqual(lat, 11.0, f"Latitud fuera de rango superior: {lat}")
                self.assertGreaterEqual(lon, -64.5, f"Longitud fuera de rango inferior: {lon}")
                self.assertLessEqual(lon, -62.0, f"Longitud fuera de rango superior: {lon}")

    def test_f19_01_canonical_schema_passes_validator_script(self) -> None:
        """F19: El script oficial validate_formio_schema.py pasa sin errores sobre el esquema canónico."""
        schema_path = CanonicalAssetResolver.get_schema_path()
        script_path = (
            CanonicalAssetResolver.PROJECT_ROOT
            / ".agent"
            / "skills"
            / "formio-survey-architect"
            / "scripts"
            / "validate_formio_schema.py"
        )
        self.assertTrue(script_path.exists(), f"Script validador no existe en {script_path}")

        res = subprocess.run(
            [sys.executable, str(script_path), "--require-cedula", str(schema_path)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            res.returncode,
            0,
            f"El validador oficial falló con código {res.returncode}. STDERR: {res.stderr}",
        )
        self.assertIn("OK", res.stdout)

    def test_f19_02_validator_detects_forbidden_external_host(self) -> None:
        """F19: El validador detecta y bloquea URLs externas que violen la soberanía de datos."""
        import copy
        bad_schema = copy.deepcopy(self.schema)
        # Inyectar componente con URL externa prohibida
        bad_schema["components"].insert(0, {
            "type": "select",
            "key": "componente_inseguro",
            "data": {
                "url": "https://api.form.io/submission"
            }
        })
        errors = FormioSchemaValidator.validate(bad_schema, require_cedula=True)
        self.assertTrue(
            any("Soberanía de Datos" in err for err in errors),
            f"No se detectó violación de soberanía de datos: {errors}",
        )

    def test_f19_03_validator_detects_duplicate_or_non_snake_case_keys(self) -> None:
        """F19: El validador detecta claves no-snake-case o duplicadas en el mismo ámbito."""
        bad_schema = {
            "display": "form",
            "components": [
                {"type": "textfield", "key": "nombre-invalido"},
                {"type": "textfield", "key": "clave_duplicada"},
                {"type": "textfield", "key": "clave_duplicada"},
                {"type": "button", "action": "submit", "key": "submit"},
            ]
        }
        errors = FormioSchemaValidator.validate(bad_schema, require_cedula=False)
        self.assertTrue(any("snake_case" in err for err in errors))
        self.assertTrue(any("duplicada" in err for err in errors))


if __name__ == "__main__":
    unittest.main()
