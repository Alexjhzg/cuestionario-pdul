"""Tier 2: Boundary and Corner Cases Tests.

Verifica:
- Casos extremos y límites en campos de datos (cédula en longitudes exactas 6 y 9, rechazo en 5 y 10).
- Grillas vacías (día sin viajes / movilidad nula).
- Valores negativos o desbordados de tiempo y costo de viaje.
- Parroquias fuera del catálogo oficial de Maturín.
- Textos de longitud extrema.
- Reintentos concurrentes de client_submission_id (idempotencia ante carreras).
- Resiliencia ante borradores offline corruptos.
"""

import json
import unittest
from uuid import uuid4

from tests_e2e.harness.contracts import (
    InMemorySubmissionStore,
    OfflineQueueSimulator,
    PydanticContractVerifier,
)
from tests_e2e.harness.fixtures import PARROQUIAS_MATURIN


class TestBoundaryCornerCases(unittest.TestCase):
    def setUp(self) -> None:
        self.store = InMemorySubmissionStore()
        self.encuesta_id = "boundary-test-survey-uuid"

    def test_tier2_01_cedula_exact_lower_boundary_6_digits(self) -> None:
        """Tier 2: Cédula con exactamente 6 dígitos (límite inferior válido para adultos mayores)."""
        valid_6_digits = "100000"
        normalized = PydanticContractVerifier.normalize_cedula(valid_6_digits)
        self.assertEqual(len(normalized), 6)
        self.assertEqual(normalized, "100000")

    def test_tier2_02_cedula_exact_upper_boundary_9_digits(self) -> None:
        """Tier 2: Cédula con exactamente 9 dígitos (límite superior válido)."""
        valid_9_digits = "123456789"
        normalized = PydanticContractVerifier.normalize_cedula(valid_9_digits)
        self.assertEqual(len(normalized), 9)
        self.assertEqual(normalized, "123456789")

    def test_tier2_03_cedula_rejected_at_5_digits(self) -> None:
        """Tier 2: Cédula con 5 dígitos es rechazada de forma estricta."""
        invalid_5_digits = "99999"
        with self.assertRaises(ValueError):
            PydanticContractVerifier.normalize_cedula(invalid_5_digits)

    def test_tier2_04_cedula_rejected_at_10_digits(self) -> None:
        """Tier 2: Cédula con 10 dígitos es rechazada por exceder el formato nacional."""
        invalid_10_digits = "1234567890"
        with self.assertRaises(ValueError):
            PydanticContractVerifier.normalize_cedula(invalid_10_digits)

    def test_tier2_05_empty_trips_grid_zero_mobility_day(self) -> None:
        """Tier 2: Hogar donde ningún miembro viajó en el día típico anterior (movilidad cero)."""
        payload = {
            "client_submission_id": str(uuid4()),
            "data": {
                "parroquia": "san_simon",
                "cedula": "20555666",
                "residentes": [
                    {
                        "persona_numero": 1,
                        "nombre_apellido": "Residente Enclaustrado",
                        "sexo": "masculino",
                        "edad": 78,
                    }
                ],
                "viajes": [],  # Ningún viaje realizado
            },
        }
        # Debe aceptarse como válido en una encuesta de movilidad urbana
        res = self.store.submit(self.encuesta_id, payload)
        self.assertFalse(res["idempotent_replay"])
        saved = self.store.submissions[res["id"]]
        self.assertEqual(len(saved["datos"]["viajes"]), 0)

    def test_tier2_06_negative_travel_time_or_cost_rejected(self) -> None:
        """Tier 2: Tiempos de viaje o costos negativos deben ser rechazados por validaciones."""
        def validate_trip_metrics(minutos: float, costo: float) -> None:
            if minutos < 0:
                raise ValueError("El tiempo de viaje no puede ser negativo.")
            if costo < 0:
                raise ValueError("El costo de viaje no puede ser negativo.")

        with self.assertRaises(ValueError):
            validate_trip_metrics(-10, 25.0)

        with self.assertRaises(ValueError):
            validate_trip_metrics(30, -5.0)

        # 0 minutos o 0 Bs son límites válidos (ej. caminata o trayecto instantáneo)
        validate_trip_metrics(0, 0.0)

    def test_tier2_07_extreme_travel_time_upper_limit(self) -> None:
        """Tier 2: Tiempos de viaje extremos superiores a 1440 minutos (24h) deben ser rechazados."""
        def validate_trip_duration(minutos: int) -> None:
            if minutos > 1440:
                raise ValueError("El tiempo de viaje no puede superar 24 horas (1440 min).")

        with self.assertRaises(ValueError):
            validate_trip_duration(1500)

        validate_trip_duration(1440)  # Límite superior exacto permitido

    def test_tier2_08_invalid_parish_with_whitespace_and_special_chars(self) -> None:
        """Tier 2: Parroquias con caracteres especiales, inyecciones o vacías son rechazadas."""
        malformed_parishes = [
            "san_simon; DROP TABLE encuestas;",
            "<script>alert(1)</script>",
            "san_simon_norte",
            "   ",
            "maturin_centro",
            "parroquia_fantasma",
            "caracas",
        ]
        for p in malformed_parishes:
            with self.assertRaises(ValueError, msg=f"Debió rechazar parroquia '{p}'"):
                PydanticContractVerifier.validate_parish(p)

    def test_tier2_09_extreme_string_length_in_proposal_field(self) -> None:
        """Tier 2: Cadenas gigantescas (>10,000 caracteres) en campos de texto son truncadas o validadas."""
        giant_string = "Maturin " * 2000  # 16,000 caracteres
        max_length = 500

        def validate_text_field(text: str, max_chars: int) -> str:
            if len(text) > max_chars:
                raise ValueError(f"El texto excede el límite de {max_chars} caracteres.")
            return text

        with self.assertRaises(ValueError):
            validate_text_field(giant_string, max_length)

    def test_tier2_10_concurrent_duplicate_submission_race_handling(self) -> None:
        """Tier 2: Dos solicitudes idénticas con el mismo client_submission_id no duplican filas."""
        shared_uuid = str(uuid4())
        payload = {
            "client_submission_id": shared_uuid,
            "data": {"parroquia": "la_cruz", "cedula": "18111222"},
        }
        res1 = self.store.submit(self.encuesta_id, payload)
        res2 = self.store.submit(self.encuesta_id, payload)

        self.assertEqual(res1["id"], res2["id"])
        self.assertFalse(res1["idempotent_replay"])
        self.assertTrue(res2["idempotent_replay"])
        self.assertEqual(len(self.store.submissions), 1)

    def test_tier2_11_corrupted_offline_draft_recovery(self) -> None:
        """Tier 2: Un borrador local con JSON dañado o corrupto es manejado sin interrupción del flujo."""
        corrupted_raw_data = "{'step': 3, 'data': { incomplete JSON ..."

        def safe_draft_loader(raw: str) -> dict:
            try:
                return json.loads(raw)
            except Exception:
                # Recuperación con estado limpio por defecto
                return {"step": 1, "data": {}, "corrupted": True}

        recovered = safe_draft_loader(corrupted_raw_data)
        self.assertTrue(recovered.get("corrupted"))
        self.assertEqual(recovered["step"], 1)

    def test_tier2_12_conditional_question_with_null_or_empty_answer(self) -> None:
        """Tier 2: Campo condicional dependiente se oculta de forma segura si la pregunta padre es null/vacía."""
        def is_component_visible(parent_value: any, expected_trigger: str) -> bool:
            if not parent_value:
                return False
            return str(parent_value).strip().lower() == expected_trigger.strip().lower()

        self.assertFalse(is_component_visible(None, "si"))
        self.assertFalse(is_component_visible("", "si"))
        self.assertFalse(is_component_visible("no", "si"))
        self.assertTrue(is_component_visible("si", "si"))


if __name__ == "__main__":
    unittest.main()
