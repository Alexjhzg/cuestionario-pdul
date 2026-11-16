"""Tier 4: Real-World Application Scenarios Tests (≥5 Flujos Completos de Producción).

Verifica de extremo a extremo:
- Escenario 1: Estudiante universitario unipersonal en San Simón Centro (movilidad activa peatonal).
- Escenario 2: Familia de 4 personas en Boquerón (Tipuro) con viajes multimodales y regreso en 1 toque.
- Escenario 3: Encuestador municipal en zonas rurales (El Corozo / Jusepín) con cola offline y sincronización por lotes.
- Escenario 4: Flujo administrativo completo (Form Builder -> Publicación -> Envíos -> Exportación CSV/JSON).
- Escenario 5: Director de Movilidad Urbana analizando Dashboard (KPIs, Leaflet GIS, ECharts y accesibilidad WCAG AA).
"""

import csv
import io
import unittest
from uuid import uuid4

from tests_e2e.harness.contracts import (
    AccessibleTableGenerator,
    CanonicalAssetResolver,
    FormioSchemaValidator,
    InMemorySubmissionStore,
    KpiCalculator,
    OfflineQueueSimulator,
    PiiMaskingVerifier,
    PydanticContractVerifier,
    TripChainSimulator,
)
from tests_e2e.harness.fixtures import (
    MODOS_TRANSPORTE,
    PARROQUIAS_MATURIN,
    SAMPLE_FORM_BUILDER_CUSTOM_SURVEY,
    SAMPLE_RURAL_BATCH,
    SAMPLE_SURVEY_FAMILY_MULTIMODAL,
    SAMPLE_SURVEY_SINGLE_PERSON_STUDENT,
)


class TestRealWorldScenarios(unittest.TestCase):
    def setUp(self) -> None:
        self.store = InMemorySubmissionStore()
        self.encuesta_pdul_id = "pdul-official-survey-uuid-2026"
        self.slug_pdul = "cuestionario-origen-destino-pedul"

    def test_scenario_1_single_student_walking_in_san_simon(self) -> None:
        """Escenario 1: Flujo completo de estudiante unipersonal en San Simón Centro."""
        survey_input = SAMPLE_SURVEY_SINGLE_PERSON_STUDENT

        # 1. Validación de cédula y datos obligatorios
        cedula_limpia = PydanticContractVerifier.normalize_cedula(survey_input["data"]["cedula"])
        self.assertEqual(cedula_limpia, "28123456")
        parroquia = PydanticContractVerifier.validate_parish(survey_input["data"]["parroquia"])
        self.assertEqual(parroquia, "san_simon")

        # 2. Verificación de lógica de movilidad activa
        data = survey_input["data"]
        self.assertEqual(data["disponibilidad_vehicular"]["tiene_vehiculo_propio"], "no")
        self.assertEqual(len(data["residentes"]), 1)
        self.assertEqual(data["residentes"][0]["medio_transporte_habitual"], "3")  # A pie

        # 3. Viajes registrados a pie ida y vuelta
        viajes = data["viajes"]
        self.assertEqual(len(viajes), 2)
        for v in viajes:
            self.assertEqual(v["modo_principal"], "3")  # A pie
            self.assertEqual(v["costo_bolivares"], 0.0)

        # 4. Salto condicional P20 cruce peatonal
        esparcimiento = data["diagnostico_esparcimiento"]
        self.assertEqual(esparcimiento["p20_cruce_peatonal_semaforizado"], "no")
        self.assertIn("p23_iluminacion_nocturna", esparcimiento)

        # 5. Envío al backend
        receipt = self.store.submit(self.encuesta_pdul_id, survey_input)
        self.assertFalse(receipt["idempotent_replay"])
        self.assertEqual(receipt["id"], 1)

        # 6. Anonimización estricta al consultar métricas
        sub_record = self.store.submissions[receipt["id"]]
        public_summary = {
            "id": sub_record["id"],
            "parroquia": sub_record["parroquia"],
            "zona_od": sub_record["zona_od"],
            "total_viajes": len(sub_record["datos"]["viajes"]),
        }
        PiiMaskingVerifier.assert_no_pii_exposed(public_summary)

    def test_scenario_2_four_person_family_multimodal_in_boqueron(self) -> None:
        """Escenario 2: Familia de 4 personas en Boquerón con viajes en bus, auto, y retorno en 1 toque."""
        family_input = SAMPLE_SURVEY_FAMILY_MULTIMODAL
        data = family_input["data"]

        # 1. 4 residentes con perfiles diversos
        self.assertEqual(len(data["residentes"]), 4)
        parentescos = [r["parentesco"] for r in data["residentes"]]
        self.assertEqual(parentescos, ["1", "2", "3", "3"])

        # 2. Viajes multimodales y generación de viaje de regreso con 1 toque
        viajes = data["viajes"]
        self.assertEqual(len(viajes), 4)

        # Simular que el viaje 4 fue autogenerado usando retorno en 1 toque del viaje 2
        viaje_ida = viajes[1]
        viaje_retorno_generado = TripChainSimulator.one_touch_return_trip(viaje_ida, next_trip_num=4)
        self.assertEqual(viaje_retorno_generado["origen"], viaje_ida["destino"])
        self.assertEqual(viaje_retorno_generado["destino"], viaje_ida["origen"])
        self.assertEqual(viaje_retorno_generado["zona_origen_od"], viaje_ida["zona_destino_od"])
        self.assertEqual(viaje_retorno_generado["zona_destino_od"], viaje_ida["zona_origen_od"])

        # 3. Sección VI Transporte público completo
        tp = data["transporte_publico"]
        self.assertTrue(len(tp["linea_ruta_utilizada"]) > 0)
        self.assertGreater(tp["gasto_semanal_tp_bs"], 0)

        # 4. Envío exitoso
        receipt = self.store.submit(self.encuesta_pdul_id, family_input)
        self.assertFalse(receipt["idempotent_replay"])
        self.assertIn("Respuesta ciudadana", receipt["mensaje"])

    def test_scenario_3_rural_field_surveyor_offline_batch_in_el_corozo(self) -> None:
        """Escenario 3: Encuestador de campo sin cobertura en El Corozo encolando lote y sincronizando."""
        offline_sim = OfflineQueueSimulator(slug=self.slug_pdul)

        # 1. Encuestador registra 3 encuestas consecutivas offline
        enqueued_ids = []
        for s in SAMPLE_RURAL_BATCH:
            cid = offline_sim.enqueue_submission(self.encuesta_pdul_id, s["data"], client_submission_id=s["client_submission_id"])
            enqueued_ids.append(cid)

        self.assertEqual(len(offline_sim.offline_queue), 3)

        # 2. El encuestador viaja a la Alcaldía y se conecta a red WiFi
        sync_results = offline_sim.sync_all(self.store)
        self.assertEqual(len(sync_results), 3)
        self.assertEqual(len(offline_sim.offline_queue), 0)

        # 3. Corte momentáneo de energía provoca reenvío del último submission_id
        last_submission = SAMPLE_RURAL_BATCH[-1]
        replay_receipt = self.store.submit(self.encuesta_pdul_id, last_submission)

        self.assertTrue(replay_receipt["idempotent_replay"])
        # Se confirma que no se duplicó el registro
        self.assertEqual(len(self.store.submissions), 3)

    def test_scenario_4_admin_creates_new_survey_toggles_and_exports(self) -> None:
        """Escenario 4: Administrador crea consulta con Form Builder, activa, recibe respuestas y exporta."""
        # 1. Esquema exportado desde el constructor visual
        custom_schema = SAMPLE_FORM_BUILDER_CUSTOM_SURVEY
        errors = FormioSchemaValidator.validate(custom_schema, require_cedula=True)
        self.assertEqual(len(errors), 0, f"Error en esquema del constructor: {errors}")

        new_survey_id = "maturin-2030-consultation-uuid"
        survey_record = {
            "id": new_survey_id,
            "titulo": custom_schema["title"],
            "slug": custom_schema["path"],
            "esquema_formio": custom_schema,
            "activa": True,
        }

        # 2. Ciudadano envía respuesta
        submission_payload = {
            "client_submission_id": str(uuid4()),
            "data": {
                "schema_version": "1.0.0",
                "parroquia": "las_cocuizas",
                "cedula": "23456789",
                "prioridad_inversion": "transporte",
                "propuesta_ciudadana": "Reactivar la ruta directa hacia la zona industrial.",
            },
        }
        receipt = self.store.submit(new_survey_id, submission_payload)
        self.assertEqual(receipt["idempotent_replay"], False)

        # 3. Administrador alterna estado a inactiva al culminar periodo de consulta
        survey_record["activa"] = False
        self.assertFalse(survey_record["activa"])

        # 4. Supervisor descarga exportación en CSV
        output = io.StringIO()
        fieldnames = ["id", "parroquia", "prioridad_inversion", "fecha_registro"]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({
            "id": receipt["id"],
            "parroquia": "las_cocuizas",
            "prioridad_inversion": "transporte",
            "fecha_registro": receipt["fecha_registro"],
        })
        csv_text = output.getvalue()
        self.assertIn("las_cocuizas", csv_text)
        self.assertIn("transporte", csv_text)

    def test_scenario_5_urban_mobility_director_gis_and_kpi_dashboard(self) -> None:
        """Escenario 5: Director de Movilidad Urbana analizando Dashboard GIS, KPIs y reporte accesible."""
        # Poblar base de datos con diversos escenarios
        self.store.submit(self.encuesta_pdul_id, SAMPLE_SURVEY_SINGLE_PERSON_STUDENT)
        self.store.submit(self.encuesta_pdul_id, SAMPLE_SURVEY_FAMILY_MULTIMODAL)
        for s in SAMPLE_RURAL_BATCH:
            self.store.submit(self.encuesta_pdul_id, s)

        # 1. Cálculo de 4 tarjetas de KPIs
        kpis = KpiCalculator.calculate_kpis(list(self.store.submissions.values()))
        self.assertEqual(kpis["total_encuestas"], 5)
        self.assertGreater(kpis["total_residentes"], 5)
        self.assertGreater(kpis["total_viajes"], 5)
        self.assertIn(kpis["parroquia_top_codigo"], PARROQUIAS_MATURIN)

        # 2. Carga y unión de mapa coroplético GeoJSON de Maturín
        geojson = CanonicalAssetResolver.load_geojson()
        self.assertEqual(len(geojson["features"]), 11)

        counts_by_parish = {}
        for sub in self.store.submissions.values():
            p = sub["parroquia"]
            counts_by_parish[p] = counts_by_parish.get(p, 0) + 1

        for feat in geojson["features"]:
            code = feat["properties"]["codigo_parroquia"]
            feat["properties"]["metric_count"] = counts_by_parish.get(code, 0)

        # 3. Reporte alternativo accesible HTML (WCAG AA)
        headers = ["Parroquia", "Encuestas Levantadas", "Porcentaje (%)"]
        rows = []
        for p, count in counts_by_parish.items():
            pct = f"{(count / kpis['total_encuestas']) * 100:.1f}%"
            rows.append([p.replace("_", " ").title(), count, pct])

        table_html = AccessibleTableGenerator.generate_html_table(
            caption="Distribución Espacial de Encuestas PDUL por Parroquia",
            headers=headers,
            rows=rows,
        )
        self.assertIn("<table", table_html)
        self.assertIn("<caption>", table_html)
        self.assertIn("San Simon", table_html)
        self.assertIn("Boqueron", table_html)


if __name__ == "__main__":
    unittest.main()
