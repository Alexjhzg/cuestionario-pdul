#!/usr/bin/env python3
"""Validador de esquemas JSON de Form.io (@formio/js) para encuestas municipales y PDUL.

Verifica:
1. Estructura raíz válida (`components` como lista).
2. Nombres de claves (`key`) en `snake_case` ASCII sin duplicados en el mismo ámbito.
3. Ausencia de URLs externas o propietarias (Soberanía de Datos).
4. Integridad de referencias en bloques `conditional.when`.
5. Presencia de campo `parroquia` y botón final `action: "submit"`.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

SNAKE_CASE_RE = re.compile(r"^[a-z][a-z0-9_]*$")
FORBIDDEN_HOSTS = ("form.io", "googleapis.com", "mapbox.com", "amazonaws.com")


def collect_components(
    components: List[Dict[str, Any]],
    scope_path: str = "root",
    errors: List[str] | None = None,
    all_keys: Set[str] | None = None,
    conditionals: List[Tuple[str, str]] | None = None,
) -> Tuple[List[str], Set[str], List[Tuple[str, str]]]:
    if errors is None:
        errors = []
    if all_keys is None:
        all_keys = set()
    if conditionals is None:
        conditionals = []

    scope_keys: Set[str] = set()

    for idx, comp in enumerate(components):
        if not isinstance(comp, dict):
            errors.append(f"[{scope_path}[{idx}]] El componente no es un objeto JSON.")
            continue

        ctype = comp.get("type")
        key = comp.get("key")
        label = comp.get("label", "")

        if not ctype:
            errors.append(f"[{scope_path}[{idx}]] Falta la propiedad 'type' (key={key}).")

        if key:
            if not SNAKE_CASE_RE.match(key):
                errors.append(
                    f"[{scope_path}] La clave '{key}' no cumple snake_case ASCII puro."
                )
            if key in scope_keys and ctype not in ("panel", "htmlelement", "content"):
                errors.append(
                    f"[{scope_path}] Clave duplicada en el mismo ámbito: '{key}'."
                )
            scope_keys.add(key)
            all_keys.add(key)
        else:
            if ctype not in ("panel", "columns", "fieldset", "Well", "htmlelement"):
                errors.append(
                    f"[{scope_path}[{idx}]] Componente de tipo '{ctype}' sin 'key'."
                )

        # Validar Soberanía de Datos (prohibir URLs externas en select/datasource)
        data_cfg = comp.get("data", {})
        if isinstance(data_cfg, dict) and "url" in data_cfg:
            url = str(data_cfg["url"]).lower()
            if url.startswith("http://") or url.startswith("https://"):
                if any(host in url for host in FORBIDDEN_HOSTS) or not (
                    "localhost" in url or "127.0.0.1" in url
                ):
                    errors.append(
                        f"[{scope_path}.{key}] Violación de Soberanía de Datos: URL externa '{data_cfg['url']}'. Usa rutas relativas como '/api/v1/...'."
                    )

        # Validar opciones en radio / select / selectboxes
        values = comp.get("values") or (
            data_cfg.get("values") if isinstance(data_cfg, dict) else None
        )
        if isinstance(values, list):
            for v in values:
                if isinstance(v, dict):
                    val = str(v.get("value", ""))
                    if val and not re.match(r"^[a-z0-9_]+$", val):
                        errors.append(
                            f"[{scope_path}.{key}] El valor de opción '{val}' debe estar en snake_case minúscula o código numérico."
                        )

        # Registrar condicionales para verificación posterior
        cond = comp.get("conditional")
        if isinstance(cond, dict) and cond.get("when"):
            conditionals.append((f"{scope_path}.{key}", str(cond["when"])))

        # Recursión en contenedores (panel, datagrid, editgrid, fieldset)
        sub_components = comp.get("components")
        if isinstance(sub_components, list):
            next_scope = (
                f"{scope_path}.{key}"
                if ctype in ("datagrid", "editgrid", "container")
                else scope_path
            )
            collect_components(
                sub_components, next_scope, errors, all_keys, conditionals
            )

        # Recursión en columnas (columns)
        columns = comp.get("columns")
        if isinstance(columns, list):
            for col_idx, col in enumerate(columns):
                if isinstance(col, dict) and isinstance(col.get("components"), list):
                    collect_components(
                        col["components"],
                        f"{scope_path}.col{col_idx}",
                        errors,
                        all_keys,
                        conditionals,
                    )

    return errors, all_keys, conditionals


def validate_schema(file_path: Path, require_cedula: bool = False) -> List[str]:
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"Error al parsear JSON en {file_path}: {exc}"]

    if not isinstance(data, dict):
        return ["El esquema raíz debe ser un objeto JSON."]

    components = data.get("components")
    if not isinstance(components, list) or not components:
        return ["El esquema debe incluir una lista no vacía en 'components'."]

    errors, all_keys, conditionals = collect_components(components)

    if "parroquia" not in all_keys:
        errors.append(
            "Falta el campo obligatorio 'parroquia' para georreferenciación municipal."
        )

    if require_cedula and "cedula" not in all_keys:
        errors.append("Falta el campo obligatorio 'cedula' requerido en modo consulta.")

    # Verificar que todas las referencias condicionales existan
    for comp_ref, target_key in conditionals:
        if target_key not in all_keys:
            errors.append(
                f"[{comp_ref}] El bloque 'conditional.when' apunta a una clave inexistente: '{target_key}'."
            )

    # Verificar botón submit al final
    last_comp = components[-1]
    if not (
        isinstance(last_comp, dict)
        and last_comp.get("type") == "button"
        and last_comp.get("action") == "submit"
    ):
        errors.append(
            "El último componente del arreglo raíz 'components' debe ser un botón con type='button' y action='submit'."
        )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Valida esquemas JSON de Form.io según estándares municipales y PDUL."
    )
    parser.add_argument("schema_path", type=Path, help="Ruta al archivo JSON a validar.")
    parser.add_argument(
        "--require-cedula",
        action="store_true",
        help="Exige explícitamente el campo 'cedula' (obligatorio en consultas abiertas).",
    )
    args = parser.parse_args()

    if not args.schema_path.exists():
        print(f"ERROR: No existe el archivo {args.schema_path}", file=sys.stderr)
        return 1

    errors = validate_schema(args.schema_path, require_cedula=args.require_cedula)
    if errors:
        print(f"FALLÓ LA VALIDACIÓN ({len(errors)} errores encontrados):", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(f"OK: El esquema '{args.schema_path}' es 100% válido según las reglas de Form.io municipal.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

