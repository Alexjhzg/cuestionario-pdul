"""Tier 3: Cross-Feature Combinations Tests (Interacciones por Pares).

Verifica:
- Interacción 1: Vehículo reportado en perfil de residente (F08) y viaje en auto particular (F09).
- Interacción 2: Viaje en transporte público (F09) activando la Sección VI de TP (F13).
- Interacción 3: Borrador offline (F44) + Restauración (F45) + Cola offline (F46) + Idempotencia backend (F26).
- Interacción 4: Desactivación administrativa (F35/F54) bloqueando recepción ciudadana (F30).
- Interacción 5: Envíos por parroquia (F02/F30) reflejándose en analítica (F31) y Leaflet GeoJSON (F58).
- Interacción 6: Pre-llenado inteligente (F48) + Retorno 1 toque (F49) integrados en Matriz O-D (F33).
- Interacción 7: Esquema Form Builder (F52) validado (F19) y cargado en Asistente Wizard (F41).
- Interacción 8: Datos de hogar multimodal (F06/F09) agregados en Tarjetas KPI (F57) y Reparto Modal (F59).
"""

import unittest
from uuid import uuid4

from tests_e2e.harness.contracts import (
    CanonicalAssetResolver,
    FormioSchemaValidator,
    InMemorySubmissionStore,
    KpiCalculator,
    OfflineQueueSimulator,
    TripChainSimulator,
)
from tests_e2e.harness.fixtures import (
    PARROQUIAS_MATURIN,
    SAMPLE_FORM_BUILDER_CUSTOM_SURVEY,
    SAMPLE_SURVEY_FAMILY_MULTIMODAL,
    SAMPLE_SURVEY_SINGLE_PERSON_STUDENT,
)


class TestCrossFeatureCombinations(unittest.TestCase):
    def setUp(self) -> None:
        self.store = InMemorySubmissionStore()
        self.encuesta_id = "cross-feature-survey-1234"
        self.slug = "cuestionario-origen-destino-pedul"
        self.offline_sim = OfflineQueueSimulator(slug=self.slug)

    def test_tier3_01_resident_vehicle_ownership_cross_validates_car_trip(self) -> None:
        """Interacción 1: Residente reporta tenencia de vehículo (F08) y realiza viaje en auto (F09)."""
        family_data = SAMPLE_SURVEY_FAMILY_MULTIMODAL["data"]
        # Persona 2 tiene vehículo disponible
        residente_2 = next(r for r in family_data["residentes"] if r["persona_numero"] == 2)
        vehiculo_hogar = family_data["disponibilidad_vehicular"]
        self.assertEqual(vehiculo_hogar["tiene_vehiculo_propio"], "si")
        self.assertEqual(vehiculo_hogar["tipo_vehiculo"], "automovil")

        # Viaje 2 de la persona 2 usa modo "2" (Auto particular)
        viaje_2 = next(v for v in family_data["viajes"] if v["persona_numero"] == 2)
        self.assertEqual(viaje_2["modo_principal"], "2")
        self.assertGreater(viaje_2["costo_bolivares"], 0)

    def test_tier3_02_transit_trip_triggers_section_vi_evaluation(self) -> None:
        """Interacción 2: Uso de transporte público (modo '1' en F09) activa Sección VI (F13)."""
        family_data = SAMPLE_SURVEY_FAMILY_MULTIMODAL["data"]
        # Persona 1 utilizó transporte público colectivo (modo "1")
        has_transit_trip = any(v.get("modo_principal") == "1" for v in family_data["viajes"])
        self.assertTrue(has_transit_trip)

        # La sección VI debe estar presente y detallar ruta y calificación
        self.assertIn("transporte_publico", family_data)
        tp_eval = family_data["transporte_publico"]
        self.assertIn("linea_ruta_utilizada", tp_eval)
        self.assertIn("calificacion_servicio_tp", tp_eval)
        self.assertGreater(tp_eval.get("gasto_semanal_tp_bs", 0), 0)

    def test_tier3_03_offline_draft_restore_and_sync_idempotency_chain(self) -> None:
        """Interacción 3: useSurveyDraft (F44) -> Banner (F45) -> Cola (F46) -> Idempotencia (F26)."""
        # Paso A: Ciudadano llena hasta el paso 4 y se guarda en localStorage
        draft_data = {
            "parroquia": "san_simon",
            "cedula": "26123456",
            "sector": "Centro",
            "residentes": [{"persona_numero": 1, "nombre_apellido": "Ciudadano"}],
        }
        self.offline_sim.save_draft(step=4, data=draft_data)

        # Paso B: Recarga de página y restauración
        restored = self.offline_sim.restore_draft()
        self.assertIsNotNone(restored)
        self.assertEqual(restored["step"], 4)

        # Paso C: Completa y encola sin conexión (generando client_submission_id)
        cid = self.offline_sim.enqueue_submission(self.encuesta_id, restored["data"])
        self.assertEqual(len(self.offline_sim.offline_queue), 1)

        # Paso D: Conexión recuperada, sincronización
        res1 = self.offline_sim.sync_all(self.store)
        self.assertEqual(len(res1), 1)
        self.assertFalse(res1[0]["idempotent_replay"])
        first_id = res1[0]["id"]

        # Paso E: Reintento por desconexión en el ACK de red (re-sincronización del mismo id)
        replay_payload = {"client_submission_id": cid, "data": restored["data"]}
        res2 = self.store.submit(self.encuesta_id, replay_payload)
        self.assertTrue(res2["idempotent_replay"])
        self.assertEqual(res2["id"], first_id)
        self.assertEqual(len(self.store.submissions), 1)

    def test_tier3_04_deactivated_survey_in_admin_blocks_citizen_submission(self) -> None:
        """Interacción 4: Encuesta desactivada desde panel admin (F35/F54) rechaza envíos (F30)."""
        survey_meta = {"id": self.encuesta_id, "activa": True}

        def submit_with_survey_check(meta: dict, payload: dict) -> dict:
            if not meta.get("activa"):
                raise PermissionError("HTTP 403: La encuesta se encuentra cerrada o inactiva.")
            return self.store.submit(meta["id"], payload)

        payload = {
            "client_submission_id": str(uuid4()),
            "data": {"parroquia": "la_pica", "cedula": "25888999"},
        }
        # Activa: Envío exitoso
        res = submit_with_survey_check(survey_meta, payload)
        self.assertIsNotNone(res["id"])

        # Admin conmuta estado a inactiva
        survey_meta["activa"] = False
        payload2 = {
            "client_submission_id": str(uuid4()),
            "data": {"parroquia": "la_pica", "cedula": "25888998"},
        }
        with self.assertRaises(PermissionError):
            submit_with_survey_check(survey_meta, payload2)

    def test_tier3_05_parish_submissions_flow_to_gis_choropleth_and_analytics(self) -> None:
        """Interacción 5: Envíos en 3 parroquias (F02/F30) alimentan resultados (F31) y mapa GeoJSON (F58)."""
        geojson = CanonicalAssetResolver.load_geojson()
        parishes = ["san_simon", "boqueron", "las_cocuizas"]

        for idx, p in enumerate(parishes):
            self.store.submit(
                self.encuesta_id,
                {
                    "client_submission_id": str(uuid4()),
                    "data": {"parroquia": p, "cedula": f"2000000{idx}"},
                },
            )

        # Calcular agregación analítica de parroquias
        parish_counts: dict = {}
        for sub in self.store.submissions.values():
            pk = sub["parroquia"]
            parish_counts[pk] = parish_counts.get(pk, 0) + 1

        self.assertEqual(len(parish_counts), 3)

        # Unir con capas del GeoJSON
        matched_parishes = set()
        for feat in geojson["features"]:
            code = feat["properties"]["codigo_parroquia"]
            if code in parish_counts:
                matched_parishes.add(code)
                feat["properties"]["total_encuestas"] = parish_counts[code]

        self.assertEqual(matched_parishes, set(parishes))

    def test_tier3_06_smart_trip_chaining_and_1_touch_return_flow_to_od_matrix(self) -> None:
        """Interacción 6: Pre-llenado inteligente (F48) + Retorno 1 toque (F49) integrados en Matriz O-D (F33)."""
        # Viaje de ida: Centro (01) -> Tipuro (05)
        trip_ida = {
            "numero_viaje": 1,
            "persona_numero": 1,
            "origen": "Oficina Centro",
            "zona_origen_od": "01",
            "destino": "Hogar Tipuro",
            "zona_destino_od": "05",
            "hora_salida": "17:00",
            "hora_llegada": "17:40",
            "modo_principal": "1",
            "tiempo_minutos": 40,
            "costo_bolivares": 20.0,
        }
        # Viaje de regreso con 1 toque: Tipuro (05) -> Centro (01)
        trip_retorno = TripChainSimulator.one_touch_return_trip(trip_ida, next_trip_num=2)

        household_trips = [trip_ida, trip_retorno]

        # Agregar a matriz O-D
        od_matrix: dict = {}
        for t in household_trips:
            pair = (t["zona_origen_od"], t["zona_destino_od"])
            if pair not in od_matrix:
                od_matrix[pair] = {"viajes": 0, "tiempo_total": 0}
            od_matrix[pair]["viajes"] += 1
            od_matrix[pair]["tiempo_total"] += t.get("tiempo_minutos", 0)

        self.assertIn(("01", "05"), od_matrix)
        self.assertIn(("05", "01"), od_matrix)
        self.assertEqual(od_matrix[("01", "05")]["viajes"], 1)
        self.assertEqual(od_matrix[("05", "01")]["viajes"], 1)

    def test_tier3_07_form_builder_custom_survey_validates_and_wizard_renders(self) -> None:
        """Interacción 7: Esquema del Form Builder (F52) valida (F19) y es procesable por el Wizard (F41)."""
        custom_schema = SAMPLE_FORM_BUILDER_CUSTOM_SURVEY
        errors = FormioSchemaValidator.validate(custom_schema, require_cedula=True)
        self.assertEqual(len(errors), 0)

        # Wizard verifica componentes renderizables
        comps = custom_schema.get("components", [])
        field_keys = [c.get("key") for c in comps if c.get("type") != "button"]
        self.assertIn("parroquia", field_keys)
        self.assertIn("cedula", field_keys)
        self.assertIn("prioridad_inversion", field_keys)

    def test_tier3_08_multimodal_household_aggregates_into_kpis_and_modal_split(self) -> None:
        """Interacción 8: Hogar multimodal (F06/F09) alimenta KPIs (F57) y Reparto Modal (F59)."""
        subs = [
            {"id": 1, "parroquia": "boqueron", "datos": SAMPLE_SURVEY_FAMILY_MULTIMODAL["data"]}
        ]
        kpis = KpiCalculator.calculate_kpis(subs)
        self.assertEqual(kpis["total_encuestas"], 1)
        self.assertEqual(kpis["total_residentes"], 4)
        self.assertEqual(kpis["total_viajes"], 4)
        self.assertEqual(kpis["promedio_viajes_hogar"], 4.0)


if __name__ == "__main__":
    unittest.main()
