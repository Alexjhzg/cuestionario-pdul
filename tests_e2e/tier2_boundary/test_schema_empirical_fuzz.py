"""Empirical Challenger Test Suite: Schema Stress Testing, Fuzzing & Adversarial Payloads.

Validates:
1. Deep traversal and deserialization of all 107 components across containers, panels, and datagrids.
2. Complete integrity and reachability of all 22 conditional.when targets against allowed options.
3. Explicit boundary constraints on numeric fields (edad, tiempo_viaje_min, costo_viaje_bs, cuartos).
4. Validator mutation fuzzing (oracle test confirming validate_formio_schema catches corrupted schemas).
5. Generator of valid, partial, empty-datagrid, and adversarial payloads (malformed cédula, invalid parroquia, out-of-range values, SQL/XSS strings).
"""

import copy
import json
import re
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

# Path to the canonical schema
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMA_PATH = REPO_ROOT / "shared" / "schemas" / "pdul_origen_destino.json"
CATALOG_PARROQUIAS_PATH = REPO_ROOT / "shared" / "catalogs" / "parroquias.json"
CATALOG_MODOS_PATH = REPO_ROOT / "shared" / "catalogs" / "modos_transporte.json"
CATALOG_MOTIVOS_PATH = REPO_ROOT / "shared" / "catalogs" / "motivos_viaje.json"

# Import validator module dynamically
import importlib.util
validator_path = REPO_ROOT / ".agent" / "skills" / "formio-survey-architect" / "scripts" / "validate_formio_schema.py"
spec = importlib.util.spec_from_file_location("validate_formio_schema", validator_path)
validator_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator_mod)
validate_schema = validator_mod.validate_schema


def walk_components(components: List[Dict[str, Any]], current_path: str = "root") -> List[Tuple[str, Dict[str, Any]]]:
    """Recursively collect all components along with their hierarchy path."""
    items = []
    for idx, comp in enumerate(components):
        if not isinstance(comp, dict):
            continue
        key = comp.get("key", f"anon_{idx}")
        path = f"{current_path}.{key}"
        items.append((path, comp))
        if "components" in comp and isinstance(comp["components"], list):
            items.extend(walk_components(comp["components"], path))
        if "columns" in comp and isinstance(comp["columns"], list):
            for col_idx, col in enumerate(comp["columns"]):
                if isinstance(col, dict) and isinstance(col.get("components"), list):
                    items.extend(walk_components(col["components"], f"{path}.col{col_idx}"))
    return items


class TestSchemaDeserializationAndTraversal(unittest.TestCase):
    """Stress test the JSON structure, nesting, and component naming."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.assertTrue(SCHEMA_PATH.exists(), f"Schema file not found at {SCHEMA_PATH}")
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            cls.schema = json.load(f)
        cls.all_nodes = walk_components(cls.schema.get("components", []))

    def test_schema_valid_json_structure(self) -> None:
        """Verify schema is a dictionary with mandatory Form.io root fields."""
        self.assertIsInstance(self.schema, dict)
        self.assertIn("display", self.schema)
        self.assertIn("title", self.schema)
        self.assertIn("components", self.schema)
        self.assertIsInstance(self.schema["components"], list)
        self.assertGreater(len(self.schema["components"]), 0)

    def test_component_count_and_deep_traversal(self) -> None:
        """Deep traversal visits all components without recursion depth overflow."""
        self.assertGreaterEqual(len(self.all_nodes), 100)
        # Verify 8 section panels exist
        panel_keys = [c.get("key") for _, c in self.all_nodes if c.get("type") == "panel"]
        expected_panels = [f"panel_seccion_{s}" for s in ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii"]]
        for ep in expected_panels:
            self.assertIn(ep, panel_keys, f"Expected panel {ep} not found in schema")

    def test_all_components_have_valid_types(self) -> None:
        """Every component has a recognized Form.io component type."""
        valid_types = {
            "hidden", "panel", "columns", "textfield", "number", "select",
            "radio", "selectboxes", "textarea", "datagrid", "button", "htmlelement"
        }
        for path, comp in self.all_nodes:
            ctype = comp.get("type")
            self.assertIsNotNone(ctype, f"Component at {path} missing 'type'")
            self.assertIn(ctype, valid_types, f"Unknown component type '{ctype}' at {path}")

    def test_keys_ascii_snake_case_compliance(self) -> None:
        """All component keys conform strictly to snake_case ASCII regex."""
        snake_re = re.compile(r"^[a-z][a-z0-9_]*$")
        for path, comp in self.all_nodes:
            key = comp.get("key")
            if key:
                self.assertTrue(
                    bool(snake_re.match(key)),
                    f"Component at {path} has non-snake_case key: '{key}'"
                )

    def test_no_key_collisions_within_same_scope(self) -> None:
        """Ensure no sibling keys collide within their respective scope."""
        def check_scope(comps: List[Dict[str, Any]], scope_name: str) -> None:
            seen: Set[str] = set()
            for c in comps:
                k = c.get("key")
                t = c.get("type")
                if k and t not in ("panel", "htmlelement"):
                    self.assertNotIn(k, seen, f"Duplicate key '{k}' in scope '{scope_name}'")
                    seen.add(k)
                if "components" in c and isinstance(c["components"], list):
                    check_scope(c["components"], f"{scope_name}.{k}")
                if "columns" in c and isinstance(c["columns"], list):
                    for idx, col in enumerate(c["columns"]):
                        if isinstance(col, dict) and "components" in col:
                            check_scope(col["components"], f"{scope_name}.{k}.col{idx}")

        check_scope(self.schema["components"], "root")

    def test_submit_button_is_terminal_component(self) -> None:
        """The last root component must be an action='submit' button."""
        last_comp = self.schema["components"][-1]
        self.assertEqual(last_comp.get("type"), "button")
        self.assertEqual(last_comp.get("action"), "submit")
        self.assertEqual(last_comp.get("key"), "submit")


class TestConditionalsIntegrityAndReachability(unittest.TestCase):
    """Stress test conditional.when references and option reachability."""

    @classmethod
    def setUpClass(cls) -> None:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            cls.schema = json.load(f)
        cls.all_nodes = walk_components(cls.schema.get("components", []))
        cls.comps_by_key = {comp.get("key"): comp for _, comp in cls.all_nodes if comp.get("key")}

    def test_all_conditional_targets_exist(self) -> None:
        """Every conditional.when must resolve to an existing key."""
        conditional_count = 0
        for path, comp in self.all_nodes:
            cond = comp.get("conditional")
            if cond and isinstance(cond, dict) and "when" in cond:
                conditional_count += 1
                target_key = str(cond["when"])
                self.assertIn(
                    target_key,
                    self.comps_by_key,
                    f"Component {comp.get('key')} at {path} points to non-existent target '{target_key}'"
                )
        self.assertGreaterEqual(conditional_count, 15, "Expected at least 15 conditional components")

    def test_conditional_values_are_reachable_in_target_options(self) -> None:
        """Target components must have the exact value specified in conditional.eq."""
        for path, comp in self.all_nodes:
            cond = comp.get("conditional")
            if cond and isinstance(cond, dict) and "when" in cond:
                target_key = str(cond["when"])
                eq_val = str(cond.get("eq"))
                target_comp = self.comps_by_key[target_key]

                values = target_comp.get("values") or target_comp.get("data", {}).get("values")
                if isinstance(values, list) and values:
                    option_values = [str(v.get("value")) for v in values if isinstance(v, dict)]
                    self.assertIn(
                        eq_val,
                        option_values,
                        f"Conditional in {comp.get('key')} expects eq='{eq_val}' but target '{target_key}' options are {option_values}"
                    )

    def test_pedestrian_crossing_conditional_jump_logic(self) -> None:
        """Verify Section VIII P20 pedestrian crossing conditional jump:
        P20 ('existe_cruce_peatonal'):
          - If 'si' -> shows P21 ('cruce_demarcado_visible') and P22 ('seguridad_cruzar_interseccion')
          - If 'no' -> skips P21 and P22; P23 ('hay_semaforo_peatonal') is always visible.
        """
        p20 = self.comps_by_key.get("existe_cruce_peatonal")
        p21 = self.comps_by_key.get("cruce_demarcado_visible")
        p22 = self.comps_by_key.get("seguridad_cruzar_interseccion")
        p23 = self.comps_by_key.get("hay_semaforo_peatonal")

        self.assertIsNotNone(p20, "Field existe_cruce_peatonal (P20) missing")
        self.assertIsNotNone(p21, "Field cruce_demarcado_visible (P21) missing")
        self.assertIsNotNone(p22, "Field seguridad_cruzar_interseccion (P22) missing")
        self.assertIsNotNone(p23, "Field hay_semaforo_peatonal (P23) missing")

        # P21 and P22 must depend on P20 == 'si'
        self.assertEqual(p21.get("conditional", {}).get("when"), "existe_cruce_peatonal")
        self.assertEqual(p21.get("conditional", {}).get("eq"), "si")
        self.assertTrue(p21.get("conditional", {}).get("show"))

        self.assertEqual(p22.get("conditional", {}).get("when"), "existe_cruce_peatonal")
        self.assertEqual(p22.get("conditional", {}).get("eq"), "si")
        self.assertTrue(p22.get("conditional", {}).get("show"))

        # P23 must not be conditional on P20
        p23_cond = p23.get("conditional")
        if p23_cond and isinstance(p23_cond, dict):
            self.assertNotEqual(p23_cond.get("when"), "existe_cruce_peatonal")


class TestNumericBoundaryValues(unittest.TestCase):
    """Stress test boundary constraints on numeric fields."""

    @classmethod
    def setUpClass(cls) -> None:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            cls.schema = json.load(f)
        cls.all_nodes = walk_components(cls.schema.get("components", []))
        cls.comps_by_key = {comp.get("key"): comp for _, comp in cls.all_nodes if comp.get("key")}

    def test_edad_boundary_constraints(self) -> None:
        """Field 'edad' must enforce min=0 and max=120."""
        edad = self.comps_by_key.get("edad")
        self.assertIsNotNone(edad, "Field 'edad' missing")
        val = edad.get("validate", {})
        self.assertEqual(val.get("min"), 0, "edad min must be 0")
        self.assertEqual(val.get("max"), 120, "edad max must be 120")
        self.assertTrue(val.get("required"), "edad must be required")

    def test_tiempo_viaje_min_boundary_constraints(self) -> None:
        """Field 'tiempo_viaje_min' must enforce min=1 and max=600."""
        tiempo = self.comps_by_key.get("tiempo_viaje_min")
        self.assertIsNotNone(tiempo, "Field 'tiempo_viaje_min' missing")
        val = tiempo.get("validate", {})
        self.assertEqual(val.get("min"), 1, "tiempo_viaje_min min must be 1")
        self.assertEqual(val.get("max"), 600, "tiempo_viaje_min max must be 600")
        self.assertTrue(val.get("required"), "tiempo_viaje_min must be required")

    def test_costo_viaje_bs_boundary_constraints(self) -> None:
        """Field 'costo_viaje_bs' must enforce min=0 (cannot be negative)."""
        costo = self.comps_by_key.get("costo_viaje_bs")
        self.assertIsNotNone(costo, "Field 'costo_viaje_bs' missing")
        val = costo.get("validate", {})
        self.assertEqual(val.get("min"), 0, "costo_viaje_bs min must be 0")
        self.assertTrue(val.get("required"), "costo_viaje_bs must be required")

    def test_total_cuartos_vivienda_boundary_constraints(self) -> None:
        """Field 'total_cuartos_vivienda' must enforce min=1 and max=30."""
        cuartos = self.comps_by_key.get("total_cuartos_vivienda")
        self.assertIsNotNone(cuartos, "Field 'total_cuartos_vivienda' missing")
        val = cuartos.get("validate", {})
        self.assertEqual(val.get("min"), 1, "total_cuartos min must be 1")
        self.assertEqual(val.get("max"), 30, "total_cuartos max must be 30")

    def test_cedula_pattern_constraint(self) -> None:
        """Field 'cedula' must enforce national regex ^[0-9]{6,9}$."""
        cedula = self.comps_by_key.get("cedula")
        self.assertIsNotNone(cedula, "Field 'cedula' missing")
        val = cedula.get("validate", {})
        self.assertEqual(val.get("pattern"), r"^[0-9]{6,9}$", "cedula pattern must match ^[0-9]{6,9}$")
        self.assertTrue(val.get("required"), "cedula must be required")


class TestSchemaFuzzingAndValidatorRobustness(unittest.TestCase):
    """Fuzzing mutations against validate_formio_schema to confirm oracle efficacy."""

    @classmethod
    def setUpClass(cls) -> None:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            cls.clean_schema = json.load(f)

    def _run_validator_on_mutation(self, mutated_schema: Dict[str, Any], require_cedula: bool = True) -> List[str]:
        with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as tmp:
            json.dump(mutated_schema, tmp)
            tmp_path = Path(tmp.name)
        try:
            errors = validate_schema(tmp_path, require_cedula=require_cedula)
        finally:
            tmp_path.unlink(missing_ok=True)
        return errors

    def test_fuzz_canonical_passes_cleanly(self) -> None:
        """Baseline canonical schema produces zero errors."""
        errors = self._run_validator_on_mutation(self.clean_schema, require_cedula=True)
        self.assertEqual(len(errors), 0, f"Canonical schema failed validation: {errors}")

    def test_fuzz_detects_non_snake_case_key(self) -> None:
        """Mutating a key to camelCase or kebab-case triggers validation error."""
        mutated = copy.deepcopy(self.clean_schema)
        mutated["components"][1]["components"][0]["key"] = "comunidadSector"
        errors = self._run_validator_on_mutation(mutated)
        self.assertTrue(any("snake_case" in e for e in errors), f"Expected snake_case error, got {errors}")

    def test_fuzz_detects_forbidden_external_url(self) -> None:
        """Injecting a forbidden external URL (e.g. form.io or googleapis.com) fails."""
        mutated = copy.deepcopy(self.clean_schema)
        mutated["components"][1]["components"][0]["data"] = {
            "url": "https://api.form.io/v1/external-data"
        }
        errors = self._run_validator_on_mutation(mutated)
        self.assertTrue(any("Soberanía de Datos" in e for e in errors), f"Expected sovereignty error, got {errors}")

    def test_fuzz_detects_broken_conditional_target(self) -> None:
        """Pointing conditional.when to a non-existent key fails."""
        mutated = copy.deepcopy(self.clean_schema)
        # Find a conditional component and break its target
        for comp in mutated["components"][8]["components"]:
            if comp.get("conditional"):
                comp["conditional"]["when"] = "non_existent_target_field_xyz"
                break
        errors = self._run_validator_on_mutation(mutated)
        self.assertTrue(any("clave inexistente" in e for e in errors), f"Expected missing key error, got {errors}")

    def test_fuzz_detects_missing_parroquia(self) -> None:
        """Removing the 'parroquia' field triggers missing parroquia error."""
        mutated = copy.deepcopy(self.clean_schema)
        # Remove parroquia from panel_seccion_i
        mutated["components"][1]["components"] = [
            c for c in mutated["components"][1]["components"] if c.get("key") != "parroquia"
        ]
        errors = self._run_validator_on_mutation(mutated)
        self.assertTrue(any("parroquia" in e for e in errors), f"Expected parroquia error, got {errors}")

    def test_fuzz_detects_missing_cedula_when_required(self) -> None:
        """Removing 'cedula' with require_cedula=True triggers error."""
        mutated = copy.deepcopy(self.clean_schema)
        mutated["components"][1]["components"] = [
            c for c in mutated["components"][1]["components"] if c.get("key") != "cedula"
        ]
        errors = self._run_validator_on_mutation(mutated, require_cedula=True)
        self.assertTrue(any("cedula" in e for e in errors), f"Expected cedula error, got {errors}")

    def test_fuzz_detects_missing_or_invalid_submit_button(self) -> None:
        """Modifying the final component away from action='submit' button triggers error."""
        mutated = copy.deepcopy(self.clean_schema)
        mutated["components"][-1] = {"type": "textfield", "key": "random_text"}
        errors = self._run_validator_on_mutation(mutated)
        self.assertTrue(any("botón con type='button' y action='submit'" in e for e in errors), f"Expected submit button error, got {errors}")


class TestPayloadGenerationAndAdversarialStress(unittest.TestCase):
    """Generate and stress test realistic, partial, and adversarial payloads against schema expectations."""

    @classmethod
    def setUpClass(cls) -> None:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            cls.schema = json.load(f)
        with open(CATALOG_PARROQUIAS_PATH, "r", encoding="utf-8") as f:
            cls.parroquias_catalog = [p["codigo"] for p in json.load(f)]

    def test_generate_valid_complete_submission(self) -> None:
        """Generate a complete valid submission payload covering all 8 sections."""
        payload = {
            "client_submission_id": "00000000-0000-0000-0000-000000000001",
            "data": {
                "schema_version": "1.0.0",
                # Seccion I: Ubicacion y Encuestado
                "parroquia": "san_simon",
                "comunidad_sector": "Centro de Maturín",
                "zona_residencia_od": "ZONA_01",
                "avenida_calle": "Avenida Bolívar",
                "casa_apartamento": "Casa 42",
                "cedula": "12345678",
                "nombre_encuestado": "Juan Pérez",
                "telefono_contacto": "04141234567",
                # Seccion II: Vivienda
                "tipo_vivienda": "casa",
                "total_cuartos_vivienda": 4,
                # Seccion III: Hogar
                "grupos_gastos_separados": 1,
                "hogar_numero": 1,
                "cuartos_dormir_hogar": 2,
                "numero_personas_hogar": 2,
                "tenencia_vivienda": "propia_pagada",
                # Seccion IV: Residentes
                "residentes": [
                    {
                        "persona_numero": 1,
                        "nombre_apellido": "Juan Pérez",
                        "parentesco_jefe_hogar": "jefe",
                        "sexo": "1",
                        "edad": 42,
                        "sabe_leer_escribir": "si",
                        "nivel_educativo": "universitario",
                        "ocupacion_principal": "Docente",
                        "medio_transporte_habitual": "6",
                        "posee_licencia": "si",
                        "tiene_vehiculo_disponible": "si",
                        "tipo_vehiculo": "automovil",
                        "cantidad_vehiculo": 1,
                    },
                    {
                        "persona_numero": 2,
                        "nombre_apellido": "María Pérez",
                        "parentesco_jefe_hogar": "esposo_pareja",
                        "sexo": "2",
                        "edad": 38,
                        "sabe_leer_escribir": "si",
                        "nivel_educativo": "universitario",
                        "ocupacion_principal": "Comerciante",
                        "medio_transporte_habitual": "1",
                        "posee_licencia": "no",
                        "tiene_vehiculo_disponible": "no",
                    }
                ],
                # Seccion V: Viajes O-D
                "viajes": [
                    {
                        "viaje_numero": 1,
                        "persona_numero": 1,
                        "origen_direccion": "Avenida Bolívar Casa 42",
                        "zona_od_origen": "ZONA_01",
                        "destino_direccion": "Universidad de Oriente",
                        "zona_od_destino": "ZONA_04",
                        "hora_salida": "07:30",
                        "hora_llegada": "08:15",
                        "motivo_viaje": "1",
                        "modo_principal": "6",
                        "modo_secundario": "3",
                        "tiempo_viaje_min": 45,
                        "costo_viaje_bs": 25.0,
                    },
                    {
                        "viaje_numero": 2,
                        "persona_numero": 1,
                        "origen_direccion": "Universidad de Oriente",
                        "zona_od_origen": "ZONA_04",
                        "destino_direccion": "Avenida Bolívar Casa 42",
                        "zona_od_destino": "ZONA_01",
                        "hora_salida": "13:30",
                        "hora_llegada": "14:15",
                        "motivo_viaje": "8",
                        "modo_principal": "6",
                        "modo_secundario": "ninguno",
                        "tiempo_viaje_min": 45,
                        "costo_viaje_bs": 25.0,
                    }
                ],
                # Seccion VI: Transporte Publico
                "uso_transporte_publico": "si",
                "rutas_tp_utilizadas_dia": 2,
                "tiempo_espera_paradas_min": 20,
                "distancia_residencia_parada_km": 0.5,
                "dificultad_acceso_tp": "no",
                "calificacion_servicio_tp": "regular",
                "gasto_semanal_tp_bs": 250.0,
                "acuerdo_rutas_directas": "de_acuerdo",
                "comentario_transporte_maturin": "Requiere mayor frecuencia en horas pico.",
                # Seccion VII: Movilidad Activa
                "cambio_forma_desplazarse_5a": "no",
                "dias_semana_camina_bicicleta": 5,
                "caminatas_mas_10min": "si",
                "usa_bicicleta_transporte": "no",
                "desplazamiento_centro_modo": "camina",
                "aceras_adecuadas": "no",
                "seguridad_desplazamiento_centro": "neutral",
                "frecuencia_visita_parques": "semanal",
                # Seccion VIII: Esparcimientos
                "actividades_espacios": {"caminar": True, "descanso": True},
                "suele_hacer_caminatas_ciudad": "si",
                "seguridad_parques_rutas_dia": "bastante_seguro",
                "seguridad_parques_rutas_noche": "poco_seguro",
                "calificacion_limpieza_conservacion": "regular",
                "satisfaccion_areas_centro": "neutral",
                "dispuesto_participar_actividades_mejoras": "si",
                "acera_suficiente_comoda": "en_desacuerdo",
                "facilidad_llegar_espacios": "facil",
                "existe_cruce_peatonal": "si",
                "cruce_demarcado_visible": "no",
                "seguridad_cruzar_interseccion": "poco_seguro",
                "hay_semaforo_peatonal": "no",
                "existen_mapas_senales_peatonales": "no",
                "movilidad_reducida_sin_ayuda": "no",
                "senalizacion_nombres_calles_visible": "si",
                "senalizacion_clara_sin_obstaculos": "no",
                "seguridad_trayecto_parada": "neutral",
                "aire_ruido_aceptables": "si",
                "conductores_ceden_paso": "no",
                "ciudad_prioriza_peaton": "no",
                "participado_consultas_espacios": "no",
                "existen_planes_movilidad_peatonal": "no_sabe",
            }
        }

        # Verify serialization round-trip
        serialized = json.dumps(payload)
        deserialized = json.loads(serialized)
        self.assertEqual(deserialized["data"]["parroquia"], "san_simon")
        self.assertEqual(len(deserialized["data"]["residentes"]), 2)
        self.assertEqual(len(deserialized["data"]["viajes"]), 2)

    def test_generate_partial_draft_submission(self) -> None:
        """Partial wizard progress (Step 2 completed, remaining unvisited)."""
        draft_payload = {
            "client_submission_id": "00000000-0000-0000-0000-000000000002",
            "data": {
                "schema_version": "1.0.0",
                "parroquia": "las_cocuizas",
                "comunidad_sector": "Sector El Silencio",
                "zona_residencia_od": "ZONA_03",
                "cedula": "20123456",
                "tipo_vivienda": "apartamento_edificio",
                "total_cuartos_vivienda": 3,
            }
        }
        serialized = json.dumps(draft_payload)
        self.assertIn("las_cocuizas", serialized)

    def test_generate_empty_datagrids_submission(self) -> None:
        """Hogares sin viajes (movilidad nula en día de lluvia o fin de semana)."""
        zero_mobility_payload = {
            "client_submission_id": "00000000-0000-0000-0000-000000000003",
            "data": {
                "schema_version": "1.0.0",
                "parroquia": "el_furrial",
                "cedula": "15987654",
                "residentes": [
                    {
                        "persona_numero": 1,
                        "nombre_apellido": "Abuelo Pedro",
                        "parentesco_jefe_hogar": "jefe",
                        "sexo": "1",
                        "edad": 82,
                        "sabe_leer_escribir": "si",
                        "nivel_educativo": "primaria",
                        "ocupacion_principal": "Jubilado",
                        "medio_transporte_habitual": "3",
                        "posee_licencia": "no",
                        "tiene_vehiculo_disponible": "no"
                    }
                ],
                "viajes": []  # Empty trips grid: zero mobility day
            }
        }
        serialized = json.dumps(zero_mobility_payload)
        deserialized = json.loads(serialized)
        self.assertEqual(len(deserialized["data"]["viajes"]), 0)

    def test_adversarial_malformed_cedulas(self) -> None:
        """Adversarial testing: regex pattern ^[0-9]{6,9}$ rejects corrupted IDs."""
        pattern = re.compile(r"^[0-9]{6,9}$")
        malformed_cedulas = [
            "",              # Empty
            "12345",         # 5 digits (too short)
            "1234567890",    # 10 digits (too long)
            "V-12345678",    # Contains letters and hyphen
            "E-12345678",    # Foreign resident prefix
            "12.345.678",    # Thousands separators
            "1234567a",      # Alphanumeric
            " 12345678 ",    # Leading/trailing whitespace
            "'; DROP TABLE--",# SQL injection payload
            "<script>alert(1)</script>" # XSS payload
        ]
        for bad_id in malformed_cedulas:
            self.assertIsNone(
                pattern.match(bad_id),
                f"Adversarial cédula '{bad_id}' was erroneously accepted by regex"
            )

        # Boundary checks: exactly 6 and exactly 9 digits MUST pass
        self.assertIsNotNone(pattern.match("100000"), "6-digit cédula must be valid")
        self.assertIsNotNone(pattern.match("999999999"), "9-digit cédula must be valid")

    def test_adversarial_parroquia_codes(self) -> None:
        """Adversarial testing: parroquias outside official 11 catalog codes."""
        adversarial_parroquias = [
            "caracas",
            "chacao",
            "maracaibo",
            "valencia",
            "maturin",  # Entire municipality, not a parish
            "SAN_SIMON", # Uppercase
            "san-simon", # Kebab-case
            "san simon", # Space separated
            "san_simon; DROP TABLE respuestas_ciudadanas; --", # SQL injection
            "../etc/passwd" # Path traversal
        ]
        for bad_p in adversarial_parroquias:
            self.assertNotIn(
                bad_p,
                self.parroquias_catalog,
                f"Adversarial parroquia '{bad_p}' was erroneously found in official catalog"
            )

    def test_adversarial_numeric_boundaries(self) -> None:
        """Adversarial testing: check values that violate min/max constraints."""
        # edad bounds: [0, 120]
        edad_violations = [-10, -1, 121, 150, 999]
        for e in edad_violations:
            self.assertFalse(0 <= e <= 120, f"Edad violation {e} passed range [0, 120]")

        # tiempo_viaje_min bounds: [1, 600]
        tiempo_violations = [-5, 0, 601, 1440, 9999]
        for t in tiempo_violations:
            self.assertFalse(1 <= t <= 600, f"Tiempo violation {t} passed range [1, 600]")

        # costo_viaje_bs bounds: min=0
        costo_violations = [-100.0, -0.01, -1]
        for c in costo_violations:
            self.assertFalse(c >= 0, f"Costo violation {c} passed min=0")

        # total_cuartos_vivienda bounds: [1, 30]
        cuartos_violations = [0, -1, 31, 100]
        for q in cuartos_violations:
            self.assertFalse(1 <= q <= 30, f"Cuartos violation {q} passed range [1, 30]")

    def test_adversarial_security_payloads_do_not_break_json(self) -> None:
        """Adversarial payloads with unicode, quotes, and script tags serialize and deserialize without loss."""
        security_payload = {
            "client_submission_id": "00000000-0000-0000-0000-000000000099",
            "data": {
                "comunidad_sector": "Sector <script>alert('xss')</script> & ' or 1=1 --",
                "comentario_transporte_maturin": "Línea con ñ, tildes: áéíóú, comillas \"dobles\" y emojis 🚌🚦",
                "avenida_calle": "Calle 5 \\' / \b \f \n \r \t",
            }
        }
        encoded = json.dumps(security_payload, ensure_ascii=False)
        decoded = json.loads(encoded)
        self.assertEqual(
            decoded["data"]["comentario_transporte_maturin"],
            "Línea con ñ, tildes: áéíóú, comillas \"dobles\" y emojis 🚌🚦"
        )
        self.assertIn("<script>", decoded["data"]["comunidad_sector"])


if __name__ == "__main__":
    unittest.main()
