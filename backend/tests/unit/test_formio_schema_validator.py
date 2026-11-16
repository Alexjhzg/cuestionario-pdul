import json
import sys
from pathlib import Path
import pytest

# Agregar la ruta del validador a sys.path
root_dir = Path(__file__).resolve().parents[3]
validator_script_path = root_dir / ".agent" / "skills" / "formio-survey-architect" / "scripts"
if not validator_script_path.exists():
    validator_script_path = root_dir / "skills-antigravity-alcaldia" / ".agent" / "skills" / "formio-survey-architect" / "scripts"
if str(validator_script_path) not in sys.path:
    sys.path.insert(0, str(validator_script_path))

import validate_formio_schema as vfs


def test_validate_schema_valid_pdul_passes():
    schema_path = root_dir / "shared" / "schemas" / "pdul_origen_destino.json"
    assert schema_path.exists(), f"El esquema PDUL debe existir en shared/schemas/ ({schema_path})"
    errors = vfs.validate_schema(schema_path, require_cedula=False)
    assert errors == [], f"El esquema PDUL debe superar la validación sin errores: {errors}"


def test_validate_schema_detects_non_snake_case_keys(tmp_path):
    bad_schema = {
        "components": [
            {
                "type": "textfield",
                "key": "parroquia",
                "label": "Parroquia",
            },
            {
                "type": "textfield",
                "key": "camelCaseKey",
                "label": "Camel Case",
            },
            {
                "type": "button",
                "key": "submit",
                "action": "submit",
                "label": "Enviar",
            },
        ]
    }
    file_p = tmp_path / "bad_keys.json"
    file_p.write_text(json.dumps(bad_schema), encoding="utf-8")

    errors = vfs.validate_schema(file_p)
    assert any("camelCaseKey" in err and "snake_case" in err for err in errors)


def test_validate_schema_detects_forbidden_external_hosts(tmp_path):
    bad_schema = {
        "components": [
            {
                "type": "select",
                "key": "parroquia",
                "label": "Parroquia",
                "data": {"url": "https://api.form.io/v1/parroquias"},
            },
            {
                "type": "button",
                "key": "submit",
                "action": "submit",
                "label": "Enviar",
            },
        ]
    }
    file_p = tmp_path / "bad_sovereignty.json"
    file_p.write_text(json.dumps(bad_schema), encoding="utf-8")

    errors = vfs.validate_schema(file_p)
    assert any("Soberanía de Datos" in err and "form.io" in err for err in errors)


def test_validate_schema_detects_broken_conditional_target(tmp_path):
    bad_schema = {
        "components": [
            {
                "type": "textfield",
                "key": "parroquia",
                "label": "Parroquia",
            },
            {
                "type": "textfield",
                "key": "especifique_otro",
                "label": "Especifique otro",
                "conditional": {"when": "clave_inexistente", "eq": "otro"},
            },
            {
                "type": "button",
                "key": "submit",
                "action": "submit",
                "label": "Enviar",
            },
        ]
    }
    file_p = tmp_path / "bad_cond.json"
    file_p.write_text(json.dumps(bad_schema), encoding="utf-8")

    errors = vfs.validate_schema(file_p)
    assert any("conditional.when" in err and "clave_inexistente" in err for err in errors)


def test_validate_schema_requires_parroquia_component(tmp_path):
    bad_schema = {
        "components": [
            {
                "type": "textfield",
                "key": "nombre_completo",
                "label": "Nombre",
            },
            {
                "type": "button",
                "key": "submit",
                "action": "submit",
                "label": "Enviar",
            },
        ]
    }
    file_p = tmp_path / "missing_parroquia.json"
    file_p.write_text(json.dumps(bad_schema), encoding="utf-8")

    errors = vfs.validate_schema(file_p)
    assert any("parroquia" in err for err in errors)


def test_validate_schema_requires_final_submit_button(tmp_path):
    bad_schema = {
        "components": [
            {
                "type": "textfield",
                "key": "parroquia",
                "label": "Parroquia",
            },
            {
                "type": "textfield",
                "key": "zona_od",
                "label": "Zona",
            },
        ]
    }
    file_p = tmp_path / "missing_submit.json"
    file_p.write_text(json.dumps(bad_schema), encoding="utf-8")

    errors = vfs.validate_schema(file_p)
    assert any("action='submit'" in err for err in errors)
