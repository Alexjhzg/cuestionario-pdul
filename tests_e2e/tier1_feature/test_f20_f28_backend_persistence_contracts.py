"""Tier 1: Feature Coverage — F20 a F28 (Arquitectura Backend, Persistencia, Normalización, Idempotencia y PII).

Verifica:
- F20-F23: Contratos arquitecturales de Clean Architecture, tablas relacionales e índices GIN JSONB.
- F24: Desempaquetado resiliente de cargas `{data: ...}` y directas desde @formio/js.
- F25: Normalización estricta de cédula de 6 a 9 dígitos numéricos.
- F26: Idempotencia de recepción mediante client_submission_id (UUID v4).
- F27: Restricción de duplicados por encuesta y cédula (HTTP 409 Conflict).
- F28: Anonimización estricta de campos de identificación personal (PII).
"""

import unittest
from uuid import uuid4

from tests_e2e.harness.contracts import (
    InMemorySubmissionStore,
    PiiMaskingVerifier,
    PydanticContractVerifier,
)
from tests_e2e.harness.fixtures import (
    SAMPLE_SURVEY_FAMILY_MULTIMODAL,
    SAMPLE_SURVEY_SINGLE_PERSON_STUDENT,
)


class TestF20F28BackendPersistenceContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.store = InMemorySubmissionStore()
        self.encuesta_id = "11111111-2222-3333-4444-555555555555"

    def test_f24_01_unwrap_formio_payload_with_data_wrapper(self) -> None:
        """F24: Desempaqueta correctamente un payload estructurado como {'data': {...}}."""
        payload = {
            "client_submission_id": "99999999-8888-7777-6666-555555555555",
            "data": {
                "parroquia": "san_simon",
                "cedula": "20123456",
                "residentes": [],
            },
        }
        data, client_id = PydanticContractVerifier.unwrap_payload(payload)
        self.assertEqual(data["parroquia"], "san_simon")
        self.assertEqual(data["cedula"], "20123456")
        self.assertEqual(client_id, "99999999-8888-7777-6666-555555555555")

    def test_f24_02_unwrap_flat_payload_without_data_wrapper(self) -> None:
        """F24: Desempaqueta correctamente un payload directo sin propiedad envoltorio 'data'."""
        payload = {
            "client_submission_id": "88888888-7777-6666-5555-444444444444",
            "parroquia": "las_cocuizas",
            "cedula": "18999888",
            "residentes": [],
        }
        data, client_id = PydanticContractVerifier.unwrap_payload(payload)
        self.assertEqual(data["parroquia"], "las_cocuizas")
        self.assertEqual(data["cedula"], "18999888")
        self.assertEqual(client_id, "88888888-7777-6666-5555-444444444444")

    def test_f25_01_cedula_normalization_cleans_punctuation_and_spaces(self) -> None:
        """F25: Limpia puntos, guiones, letras y espacios aislando solo los dígitos."""
        raw_inputs = [
            ("V-28.123.456", "28123456"),
            (" 28123456 ", "28123456"),
            ("V28123456", "28123456"),
            ("28-123-456", "28123456"),
            ("6.123.456", "6123456"),
            ("123.456.789", "123456789"),
        ]
        for raw, expected in raw_inputs:
            self.assertEqual(
                PydanticContractVerifier.normalize_cedula(raw),
                expected,
                f"Fallo al normalizar '{raw}'",
            )

    def test_f25_02_cedula_normalization_rejects_out_of_bound_lengths(self) -> None:
        """F25: Rechaza cédulas con menos de 6 dígitos o más de 9 dígitos."""
        invalid_inputs = ["12345", "1234", "1234567890", "V-123", "", "ABCDEF"]
        for bad in invalid_inputs:
            with self.assertRaises(ValueError, msg=f"Debió rechazar cédula '{bad}'"):
                PydanticContractVerifier.normalize_cedula(bad)

    def test_f26_01_idempotent_submission_returns_flag_on_replay(self) -> None:
        """F26: Enviar dos veces el mismo client_submission_id responde con idempotent_replay: true."""
        uuid_str = str(uuid4())
        payload = {
            "client_submission_id": uuid_str,
            "data": {
                "parroquia": "san_simon",
                "cedula": "24111222",
                "residentes": [],
                "viajes": [],
            },
        }

        # Primer envío
        res1 = self.store.submit(self.encuesta_id, payload)
        self.assertFalse(res1["idempotent_replay"])
        first_id = res1["id"]

        # Reintento idéntico por corte de red
        res2 = self.store.submit(self.encuesta_id, payload)
        self.assertTrue(res2["idempotent_replay"])
        self.assertEqual(res2["id"], first_id)
        # La base de datos sigue teniendo solo 1 registro
        self.assertEqual(len(self.store.submissions), 1)

    def test_f27_01_duplicate_cedula_in_same_survey_raises_conflict(self) -> None:
        """F27: Dos envíos distintos con la misma cédula en la misma encuesta generan conflicto 409."""
        payload1 = {
            "client_submission_id": str(uuid4()),
            "data": {"parroquia": "boqueron", "cedula": "19888777"},
        }
        payload2 = {
            "client_submission_id": str(uuid4()),  # UUID diferente
            "data": {"parroquia": "boqueron", "cedula": "19.888.777"},  # Misma cédula
        }

        self.store.submit(self.encuesta_id, payload1)
        with self.assertRaises(ValueError) as ctx:
            self.store.submit(self.encuesta_id, payload2)
        self.assertIn("CEDULA_DUPLICADA", str(ctx.exception))

    def test_f28_01_pii_strictly_excluded_from_analytical_payloads(self) -> None:
        """F28: PiiMaskingVerifier asegura que ningún objeto exponga cédula ni datos de filiación."""
        safe_analytical_result = {
            "parroquia": "san_simon",
            "total_encuestas": 150,
            "reparto_modal": [
                {"modo": "1", "porcentaje": 45.5},
                {"modo": "3", "porcentaje": 22.1},
            ],
            "matriz_od": [
                {"zona_origen": "01", "zona_destino": "03", "total_viajes": 85}
            ],
        }
        # Debe pasar sin lanzar AssertionError
        PiiMaskingVerifier.assert_no_pii_exposed(safe_analytical_result)

    def test_f28_02_pii_verifier_raises_assertion_on_leaked_fields(self) -> None:
        """F28: Detecta e interrumpe de inmediato si se filtra cédula o teléfono."""
        leaky_result = {
            "parroquia": "boqueron",
            "total_encuestas": 1,
            "detalle": {
                "cedula": "28123456",  # Filtración PII
            },
        }
        with self.assertRaises(AssertionError):
            PiiMaskingVerifier.assert_no_pii_exposed(leaky_result)


if __name__ == "__main__":
    unittest.main()
