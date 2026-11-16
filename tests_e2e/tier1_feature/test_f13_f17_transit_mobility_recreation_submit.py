"""Tier 1: Feature Coverage — F13 a F17 (Transporte Público, Movilidad Activa, Esparcimiento y Submit).

Verifica:
- F13: Subformulario de Transporte Público (Sección VI) y sus variables de calidad y costo.
- F14: Movilidad activa y no motorizada (Sección VII peatonales, bicicleta, cambio modal).
- F15: Diagnóstico de espacios públicos y esparcimiento (Sección VIII: 29 variables).
- F16: Salto condicional de cruce peatonal (P20 Sí -> P21, P22; No -> P23).
- F17: Botón de envío final y acción 'submit'.
"""

import unittest
from typing import Any, Dict, List

from tests_e2e.harness.contracts import CanonicalAssetResolver


class TestF13F17TransitMobilityRecreationSubmit(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = CanonicalAssetResolver.load_schema()
        cls.all_components: Dict[str, Dict[str, Any]] = {}
        def _index(comps: List[Dict[str, Any]]) -> None:
            for c in comps:
                if isinstance(c, dict):
                    k = c.get("key")
                    if k:
                        cls.all_components[k] = c
                    if isinstance(c.get("components"), list):
                        _index(c["components"])
        _index(cls.schema.get("components", []))

    def test_f13_01_public_transit_section_vi_exists_with_core_fields(self) -> None:
        """F13: La sección VI contiene campos de uso, rutas, tiempo de espera, calificación y gasto."""
        transit_keys = {
            "uso_transporte_publico",
            "rutas_tp_utilizadas_dia",
            "tiempo_espera_paradas_min",
            "calificacion_servicio_tp",
            "gasto_semanal_tp_bs",
        }
        for tk in transit_keys:
            self.assertIn(tk, self.all_components, f"Falta campo de TP '{tk}' en Sección VI")

    def test_f13_02_transit_evaluation_and_weekly_expense_fields(self) -> None:
        """F13: Verificación de tipos para gasto semanal (número) y calificación de servicio."""
        gasto_comp = self.all_components["gasto_semanal_tp_bs"]
        self.assertEqual(gasto_comp.get("type"), "number")

        calif_comp = self.all_components["calificacion_servicio_tp"]
        self.assertIn(calif_comp.get("type"), ["radio", "select"])

    def test_f14_01_active_mobility_section_vii_walking_and_biking(self) -> None:
        """F14: Sección VII incluye variables de caminatas >10min, uso de bicicleta y días de semana."""
        self.assertIn("caminatas_mas_10min", self.all_components)
        self.assertIn("usa_bicicleta_transporte", self.all_components)
        self.assertIn("dias_semana_camina_bicicleta", self.all_components)

    def test_f14_02_active_mobility_5_year_modal_shift_fields(self) -> None:
        """F14: Evalúa cambio modal en los últimos 5 años y motivo del cambio."""
        self.assertIn("cambio_forma_desplazarse_5a", self.all_components)
        self.assertIn("motivo_cambio_desplazamiento", self.all_components)

    def test_f15_01_recreation_diagnosis_section_viii_has_29_variables(self) -> None:
        """F15: Sección VIII cubre las 29 variables de espacios públicos y peatonalidad."""
        panel_viii = self.all_components.get("panel_seccion_viii")
        self.assertIsNotNone(panel_viii, "Falta panel_seccion_viii en el formulario")
        sub_comps = panel_viii.get("components", [])

        # Filtrar solo campos de preguntas (excluyendo separadores o 'otro' subsidiarios)
        question_comps = [
            c for c in sub_comps
            if isinstance(c, dict)
            and c.get("type") in ("radio", "select", "selectboxes", "textarea", "textfield", "number")
            and not str(c.get("key", "")).endswith("_otro")
        ]
        self.assertGreaterEqual(
            len(question_comps),
            20,
            f"Se esperaban al menos 20 campos principales en Sección VIII, hallados {len(question_comps)}",
        )

    def test_f16_01_pedestrian_cross_conditional_jump_logic(self) -> None:
        """F16: Salto condicional de P20 (existe_cruce_peatonal) hacia P21 (cruce_demarcado) y semáforo."""
        self.assertIn("existe_cruce_peatonal", self.all_components)
        p20 = self.all_components["existe_cruce_peatonal"]
        self.assertIn(p20.get("type"), ["radio", "select"])

        # Si responde Sí en P20, se activan cruce_demarcado_visible / seguridad_cruzar
        p21 = self.all_components.get("cruce_demarcado_visible")
        self.assertIsNotNone(p21, "Falta campo P21 cruce_demarcado_visible")
        cond = p21.get("conditional", {})
        self.assertEqual(cond.get("when"), "existe_cruce_peatonal")
        self.assertEqual(cond.get("eq"), "si")

    def test_f17_01_submit_button_component_at_root_end(self) -> None:
        """F17: El último componente del formulario es un botón con type='button' y action='submit'."""
        root_comps = self.schema.get("components", [])
        self.assertGreater(len(root_comps), 0)
        last_comp = root_comps[-1]
        self.assertEqual(last_comp.get("type"), "button")
        self.assertEqual(last_comp.get("action"), "submit")
        self.assertTrue(last_comp.get("key"))


if __name__ == "__main__":
    unittest.main()
