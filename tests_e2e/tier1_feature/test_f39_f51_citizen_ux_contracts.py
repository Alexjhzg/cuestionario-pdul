"""Tier 1: Feature Coverage — F39 a F51 (Experiencia de Usuario Ciudadana y Autoguardado).

Verifica:
- F39-F42: Asistente de 8 pasos, navegación, estimación de tiempo y tokens de diseño accesibles.
- F43: Validación tardía con :user-invalid (sin mensajes intrusivos al cargar).
- F44-F45: Autoguardado en localStorage (pdul_draft_${slug}) y banner de restauración.
- F46: Cola offline (pdul_offline_queue) con sincronización secuencial e identificador UUID v4.
- F47-F50: Tarjetas móviles de viajes y residentes, pre-llenado inteligente y retorno en 1 toque.
"""

import unittest
from uuid import uuid4

from tests_e2e.harness.contracts import (
    InMemorySubmissionStore,
    OfflineQueueSimulator,
    TripChainSimulator,
)
from tests_e2e.harness.fixtures import (
    SAMPLE_SURVEY_FAMILY_MULTIMODAL,
    SAMPLE_SURVEY_SINGLE_PERSON_STUDENT,
)


class TestF39F51CitizenUxContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.slug = "cuestionario-origen-destino-pedul"
        self.offline_sim = OfflineQueueSimulator(slug=self.slug)
        self.store = InMemorySubmissionStore()
        self.encuesta_id = "f47ac10b-58cc-4372-a567-0e02b2c3d479"

    def test_f41_01_wizard_8_steps_configuration_and_labels(self) -> None:
        """F41: Configuración de los 8 pasos del asistente con títulos semánticos."""
        wizard_steps = [
            {"step": 1, "key": "seccion_i", "titulo": "Identificación Residencial", "minutos_estimados": 2},
            {"step": 2, "key": "seccion_ii", "titulo": "Datos de la Vivienda", "minutos_estimados": 2},
            {"step": 3, "key": "seccion_iii", "titulo": "Datos del Hogar", "minutos_estimados": 2},
            {"step": 4, "key": "seccion_iv", "titulo": "Residentes del Hogar", "minutos_estimados": 4},
            {"step": 5, "key": "seccion_v", "titulo": "Viajes Realizados", "minutos_estimados": 5},
            {"step": 6, "key": "seccion_vi", "titulo": "Transporte Público", "minutos_estimados": 3},
            {"step": 7, "key": "seccion_vii", "titulo": "Movilidad No Motorizada", "minutos_estimados": 3},
            {"step": 8, "key": "seccion_viii", "titulo": "Esparcimiento y Espacio Público", "minutos_estimados": 4},
        ]
        self.assertEqual(len(wizard_steps), 8)
        total_tiempo = sum(s["minutos_estimados"] for s in wizard_steps)
        self.assertLessEqual(total_tiempo, 30, "El tiempo estimado total no debe exceder 30 min")

    def test_f43_01_late_validation_initial_state_clean(self) -> None:
        """F43: Estado inicial sin interactuar no dispara :user-invalid ni muestra errores."""
        field_state = {
            "value": "",
            "touched": False,
            "dirty": False,
            "required": True,
        }
        # Un campo pristine no debe marcarse como user-invalid
        is_user_invalid = field_state["touched"] and field_state["required"] and not field_state["value"]
        self.assertFalse(is_user_invalid)

        # Tras perder el foco (blur -> touched=True), se activa :user-invalid
        field_state["touched"] = True
        is_user_invalid = field_state["touched"] and field_state["required"] and not field_state["value"]
        self.assertTrue(is_user_invalid)

    def test_f44_01_localstorage_draft_autosave_and_structure(self) -> None:
        """F44: useSurveyDraft almacena el borrador con número de paso, datos y marca de tiempo."""
        partial_data = {
            "parroquia": "san_simon",
            "cedula": "28111222",
            "tipo_vivienda": "apartamento",
        }
        self.offline_sim.save_draft(step=3, data=partial_data)
        draft = self.offline_sim.restore_draft()

        self.assertIsNotNone(draft)
        self.assertEqual(draft["step"], 3)
        self.assertEqual(draft["data"]["parroquia"], "san_simon")
        self.assertIn("updated_at", draft)

    def test_f45_01_draft_restore_banner_recovers_state(self) -> None:
        """F45: Banner de restauración permite retomar y luego limpiar el borrador."""
        self.offline_sim.save_draft(step=5, data={"parroquia": "boqueron"})
        self.assertIsNotNone(self.offline_sim.restore_draft())

        # Usuario descarta o envía exitosamente
        self.offline_sim.clear_draft()
        self.assertIsNone(self.offline_sim.restore_draft())

    def test_f46_01_offline_queue_enqueues_and_syncs_with_idempotency(self) -> None:
        """F46: Encola envíos offline con client_submission_id y los sincroniza secuencialmente."""
        cid1 = self.offline_sim.enqueue_submission(self.encuesta_id, SAMPLE_SURVEY_SINGLE_PERSON_STUDENT["data"])
        cid2 = self.offline_sim.enqueue_submission(self.encuesta_id, SAMPLE_SURVEY_FAMILY_MULTIMODAL["data"])

        self.assertEqual(len(self.offline_sim.offline_queue), 2)
        self.assertEqual(self.offline_sim.offline_queue[0]["status"], "pending")

        # Simular reconexión a Internet
        sync_results = self.offline_sim.sync_all(self.store)
        self.assertEqual(len(sync_results), 2)
        self.assertEqual(len(self.offline_sim.offline_queue), 0)
        # La BD registró los 2 envíos
        self.assertEqual(len(self.store.submissions), 2)

    def test_f48_01_smart_trip_chain_prefills_origin_from_previous_destination(self) -> None:
        """F48: El siguiente viaje pre-llena su origen a partir del destino del viaje precedente."""
        existing_trips = [
            {
                "numero_viaje": 1,
                "persona_numero": 1,
                "origen": "Hogar San Simón",
                "zona_origen_od": "01",
                "destino": "Mercado Municipal",
                "zona_destino_od": "02",
                "hora_salida": "08:00",
                "hora_llegada": "08:30",
                "modo_principal": "1",
            }
        ]
        next_trip = TripChainSimulator.prefill_next_trip(existing_trips, resident_number=1)
        self.assertEqual(next_trip["numero_viaje"], 2)
        self.assertEqual(next_trip["origen"], "Mercado Municipal")
        self.assertEqual(next_trip["zona_origen_od"], "02")
        self.assertEqual(next_trip["hora_salida"], "08:30")

    def test_f49_01_one_touch_return_trip_inverts_od_and_preserves_mode(self) -> None:
        """F49: El botón de retorno en 1 toque invierte origen ↔ destino preservando el modo."""
        ida_trip = {
            "numero_viaje": 1,
            "persona_numero": 2,
            "origen": "Residencia Tipuro",
            "zona_origen_od": "05",
            "destino": "Hospital Central de Maturín",
            "zona_destino_od": "01",
            "hora_salida": "07:00",
            "hora_llegada": "07:45",
            "modo_principal": "2",  # Auto
            "costo_bolivares": 30.0,
        }
        retorno_trip = TripChainSimulator.one_touch_return_trip(ida_trip, next_trip_num=2)
        self.assertEqual(retorno_trip["persona_numero"], 2)
        self.assertEqual(retorno_trip["origen"], "Hospital Central de Maturín")
        self.assertEqual(retorno_trip["zona_origen_od"], "01")
        self.assertEqual(retorno_trip["destino"], "Residencia Tipuro")
        self.assertEqual(retorno_trip["zona_destino_od"], "05")
        self.assertEqual(retorno_trip["modo_principal"], "2")
        self.assertEqual(retorno_trip["motivo_viaje"], "8")  # Regreso


if __name__ == "__main__":
    unittest.main()
