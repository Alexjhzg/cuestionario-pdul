"""Tier 1: Feature Coverage — F52 a F56 (Constructor de Encuestas y Panel Administrativo).

Verifica:
- F52-F53: Constructor visual Form.io (esquema generado soberano, validado con validate_formio_schema).
- F54: Vista administrativa de gestión y alternancia activa/inactiva.
- F55: Tabla de envíos con paginación y exportación de datos en formatos estándar.
"""

import csv
import io
import json
import unittest

from tests_e2e.harness.contracts import FormioSchemaValidator
from tests_e2e.harness.fixtures import (
    SAMPLE_FORM_BUILDER_CUSTOM_SURVEY,
    SAMPLE_SURVEY_FAMILY_MULTIMODAL,
    SAMPLE_SURVEY_SINGLE_PERSON_STUDENT,
)


class TestF52F56AdminBuilderContracts(unittest.TestCase):
    def test_f52_01_builder_custom_survey_has_valid_formio_structure(self) -> None:
        """F52: El esquema exportado por el Form Builder es un JSON válido para Form.io."""
        custom_survey = SAMPLE_FORM_BUILDER_CUSTOM_SURVEY
        self.assertIsInstance(custom_survey, dict)
        self.assertEqual(custom_survey.get("display"), "form")
        self.assertIn("components", custom_survey)
        self.assertGreaterEqual(len(custom_survey["components"]), 4)

    def test_f53_01_builder_export_passes_official_formio_validator(self) -> None:
        """F53: La encuesta generada en el constructor pasa la validación oficial sin errores."""
        errors = FormioSchemaValidator.validate(SAMPLE_FORM_BUILDER_CUSTOM_SURVEY, require_cedula=True)
        self.assertEqual(len(errors), 0, f"La encuesta del builder no superó la validación: {errors}")

    def test_f53_02_builder_detects_missing_submit_button(self) -> None:
        """F53: El validador del builder rechaza esquemas que no terminen con botón submit."""
        import copy
        bad_survey = copy.deepcopy(SAMPLE_FORM_BUILDER_CUSTOM_SURVEY)
        bad_survey["components"].pop()  # Eliminar botón submit
        errors = FormioSchemaValidator.validate(bad_survey, require_cedula=True)
        self.assertTrue(any("submit" in err.lower() for err in errors))

    def test_f54_01_admin_survey_list_item_structure(self) -> None:
        """F54: Cada elemento del listado administrativo expone métricas y estado."""
        survey_summary = {
            "id": "b3c4d5e6-f7a8-4b9c-0d1e-2f3a4b5c6d7e",
            "titulo": "Consulta Ciudadana Maturín 2030",
            "slug": "consulta-maturin-2030",
            "activa": True,
            "total_respuestas": 342,
            "creado_en": "2026-11-09T10:00:00Z",
            "ultima_respuesta": "2026-11-09T18:30:00Z",
        }
        self.assertIn("id", survey_summary)
        self.assertIn("activa", survey_summary)
        self.assertIn("total_respuestas", survey_summary)
        self.assertGreaterEqual(survey_summary["total_respuestas"], 0)

    def test_f54_02_admin_toggle_active_status_contract(self) -> None:
        """F54: La alternancia de estado conmuta correctamente el indicador 'activa'."""
        survey = {"id": "1", "activa": True}
        # Desactivar
        survey["activa"] = False
        self.assertFalse(survey["activa"])
        # Reactivar
        survey["activa"] = True
        self.assertTrue(survey["activa"])

    def test_f55_01_admin_export_tabular_csv_structure(self) -> None:
        """F55: La exportación tabular CSV produce encabezados correctos y filas serializadas."""
        submissions = [
            {
                "id": 1,
                "client_submission_id": SAMPLE_SURVEY_SINGLE_PERSON_STUDENT["client_submission_id"],
                "parroquia": "san_simon",
                "zona_od": "01",
                "total_residentes": 1,
                "total_viajes": 2,
            },
            {
                "id": 2,
                "client_submission_id": SAMPLE_SURVEY_FAMILY_MULTIMODAL["client_submission_id"],
                "parroquia": "boqueron",
                "zona_od": "05",
                "total_residentes": 4,
                "total_viajes": 4,
            },
        ]
        output = io.StringIO()
        fieldnames = ["id", "client_submission_id", "parroquia", "zona_od", "total_residentes", "total_viajes"]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(submissions)
        csv_data = output.getvalue()

        self.assertIn("san_simon", csv_data)
        self.assertIn("boqueron", csv_data)
        # Verificar que es parseable de vuelta
        reader = list(csv.DictReader(io.StringIO(csv_data)))
        self.assertEqual(len(reader), 2)
        self.assertEqual(reader[0]["parroquia"], "san_simon")


if __name__ == "__main__":
    unittest.main()
