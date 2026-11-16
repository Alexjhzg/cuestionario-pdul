"""Contratos Opaque-Box y Utilidades de Verificación para la Suite E2E.

Provee resolvedores de activos canónicos, emuladores de validación Pydantic v2,
lógica de idempotencia, cola offline, encadenamiento de viajes y enmascaramiento de PII.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID

from tests_e2e.harness.fixtures import (
    MODOS_TRANSPORTE,
    MOTIVOS_VIAJE,
    PARROQUIAS_MATURIN,
    PARROQUIAS_NOMBRES,
)

CEDULA_RE = re.compile(r"^[0-9]{6,9}$")
SNAKE_CASE_RE = re.compile(r"^[a-z][a-z0-9_]*$")
FORBIDDEN_HOSTS = ("form.io", "googleapis.com", "mapbox.com", "amazonaws.com")
PII_KEYS = {
    "cedula",
    "nombre_primer_apellido",
    "nombre_apellido",
    "telefono",
    "email",
    "casa_apartamento",
    "avenida_calle",
}


class CanonicalAssetResolver:
    """Resuelve las rutas de los activos canónicos de Milestone 1."""

    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

    @classmethod
    def get_schema_path(cls) -> Path:
        p = cls.PROJECT_ROOT / "shared" / "schemas" / "pdul_origen_destino.json"
        if not p.exists():
            fallback = (
                cls.PROJECT_ROOT
                / ".agents"
                / "teamwork"
                / "spec_miner_survey_1"
                / "pdul-survey-full-spec.json"
            )
            if fallback.exists():
                return fallback
        return p

    @classmethod
    def load_schema(cls) -> Dict[str, Any]:
        path = cls.get_schema_path()
        if not path.exists():
            raise FileNotFoundError(f"Esquema canónico no encontrado en {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    @classmethod
    def get_geojson_path(cls) -> Path:
        return cls.PROJECT_ROOT / "shared" / "geojson" / "maturin_parroquias.geojson"

    @classmethod
    def load_geojson(cls) -> Dict[str, Any]:
        path = cls.get_geojson_path()
        if not path.exists():
            raise FileNotFoundError(f"GeoJSON de parroquias no encontrado en {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    @classmethod
    def get_catalogs_dir(cls) -> Path:
        return cls.PROJECT_ROOT / "shared" / "catalogs"

    @classmethod
    def load_catalog(cls, name: str) -> Any:
        path = cls.get_catalogs_dir() / f"{name}.json"
        if not path.exists():
            raise FileNotFoundError(f"Catálogo '{name}' no encontrado en {path}")
        return json.loads(path.read_text(encoding="utf-8"))


class FormioSchemaValidator:
    """Implementa las verificaciones oficiales de validate_formio_schema.py."""

    @classmethod
    def collect_components(
        cls,
        components: List[Dict[str, Any]],
        scope_path: str = "root",
        errors: Optional[List[str]] = None,
        all_keys: Optional[Set[str]] = None,
        conditionals: Optional[List[Tuple[str, str]]] = None,
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

            # Soberanía de Datos
            data_cfg = comp.get("data", {})
            if isinstance(data_cfg, dict) and "url" in data_cfg:
                url = str(data_cfg["url"]).lower()
                if url.startswith("http://") or url.startswith("https://"):
                    if any(host in url for host in FORBIDDEN_HOSTS) or not (
                        "localhost" in url or "127.0.0.1" in url
                    ):
                        errors.append(
                            f"[{scope_path}.{key}] Violación de Soberanía de Datos: URL externa '{data_cfg['url']}'."
                        )

            # Opciones de selección
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

            # Condicionales
            cond = comp.get("conditional")
            if isinstance(cond, dict) and cond.get("when"):
                conditionals.append((f"{scope_path}.{key}", str(cond["when"])))

            # Recursión
            sub_comps = comp.get("components")
            if isinstance(sub_comps, list):
                next_scope = (
                    f"{scope_path}.{key}"
                    if ctype in ("datagrid", "editgrid", "container")
                    else scope_path
                )
                cls.collect_components(sub_comps, next_scope, errors, all_keys, conditionals)

            columns = comp.get("columns")
            if isinstance(columns, list):
                for col_idx, col in enumerate(columns):
                    if isinstance(col, dict) and isinstance(col.get("components"), list):
                        cls.collect_components(
                            col["components"],
                            f"{scope_path}.col{col_idx}",
                            errors,
                            all_keys,
                            conditionals,
                        )

        return errors, all_keys, conditionals

    @classmethod
    def validate(cls, data: Dict[str, Any], require_cedula: bool = False) -> List[str]:
        if not isinstance(data, dict):
            return ["El esquema raíz debe ser un objeto JSON."]

        components = data.get("components")
        if not isinstance(components, list) or not components:
            return ["El esquema debe incluir una lista no vacía en 'components'."]

        errors, all_keys, conditionals = cls.collect_components(components)

        if "parroquia" not in all_keys:
            errors.append("Falta el campo obligatorio 'parroquia' para georreferenciación municipal.")

        if require_cedula and "cedula" not in all_keys:
            errors.append("Falta el campo obligatorio 'cedula' requerido en modo consulta.")

        for comp_ref, target_key in conditionals:
            if target_key not in all_keys:
                errors.append(
                    f"[{comp_ref}] El bloque 'conditional.when' apunta a una clave inexistente: '{target_key}'."
                )

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


class PydanticContractVerifier:
    """Verifica reglas de contratos del backend (Pydantic v2, normalización, RFC 7807)."""

    @staticmethod
    def normalize_cedula(raw_cedula: Any) -> str:
        s = str(raw_cedula or "").strip()
        digits = re.sub(r"\D", "", s)
        if not digits or not CEDULA_RE.match(digits):
            raise ValueError(
                "Escriba solo los números de su cédula (6 a 9 dígitos, sin puntos ni guiones)."
            )
        return digits

    @staticmethod
    def validate_parish(parroquia: str) -> str:
        p = str(parroquia or "").strip().lower()
        if p not in PARROQUIAS_MATURIN:
            raise ValueError(
                f"Seleccione una parroquia válida del Municipio Maturín ({', '.join(sorted(PARROQUIAS_MATURIN))})."
            )
        return p

    @classmethod
    def unwrap_payload(cls, payload: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str]]:
        if "data" in payload and isinstance(payload["data"], dict):
            data = payload["data"]
            client_sub_id = payload.get("client_submission_id") or data.get("client_submission_id")
        else:
            data = payload
            client_sub_id = payload.get("client_submission_id")

        if client_sub_id:
            client_sub_id = str(UUID(str(client_sub_id)))

        return data, client_sub_id


class InMemorySubmissionStore:
    """Simulador de base de datos PostgreSQL con soporte para idempotencia y restricciones UNIQUE."""

    def __init__(self) -> None:
        self.submissions: Dict[int, Dict[str, Any]] = {}
        self.by_client_submission_id: Dict[str, int] = {}
        self.by_survey_cedula: Dict[Tuple[str, str], int] = {}
        self._next_id = 1

    def submit(
        self,
        encuesta_id: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        data, client_sub_id = PydanticContractVerifier.unwrap_payload(payload)

        # 1. Idempotencia: Si ya se recibió client_submission_id, retornar el recibo existente
        if client_sub_id and client_sub_id in self.by_client_submission_id:
            sub_id = self.by_client_submission_id[client_sub_id]
            existing = self.submissions[sub_id]
            return {
                "id": sub_id,
                "fecha_registro": existing["fecha_registro"],
                "idempotent_replay": True,
                "mensaje": "Respuesta recibida previamente de forma idempotente.",
            }

        # 2. Validar cédula si está presente
        raw_cedula = data.get("cedula")
        cedula_limpia = None
        if raw_cedula:
            cedula_limpia = PydanticContractVerifier.normalize_cedula(raw_cedula)
            # Restricción UNIQUE (encuesta_id, cedula)
            pair = (encuesta_id, cedula_limpia)
            if pair in self.by_survey_cedula:
                raise ValueError("CEDULA_DUPLICADA: Ya se ha registrado una respuesta con esta cédula para esta encuesta.")

        # 3. Validar parroquia
        parroquia = PydanticContractVerifier.validate_parish(data.get("parroquia", ""))

        # 4. Registrar envío
        sub_id = self._next_id
        self._next_id += 1
        now_iso = datetime.now(timezone.utc).isoformat()

        record = {
            "id": sub_id,
            "encuesta_id": encuesta_id,
            "client_submission_id": client_sub_id,
            "cedula": cedula_limpia,
            "parroquia": parroquia,
            "zona_od": data.get("zona_residencia_od"),
            "datos": data,
            "fecha_registro": now_iso,
        }
        self.submissions[sub_id] = record

        if client_sub_id:
            self.by_client_submission_id[client_sub_id] = sub_id
        if cedula_limpia:
            self.by_survey_cedula[(encuesta_id, cedula_limpia)] = sub_id

        return {
            "id": sub_id,
            "fecha_registro": now_iso,
            "idempotent_replay": False,
            "mensaje": "Respuesta ciudadana persistida con éxito.",
        }


class PiiMaskingVerifier:
    """Verifica que ningún campo de datos personales (PII) se exponga en consultas públicas."""

    @classmethod
    def assert_no_pii_exposed(cls, obj: Any, path: str = "root") -> None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in PII_KEYS:
                    raise AssertionError(
                        f"Violación de Privacidad: Clave PII '{k}' detectada en '{path}.{k}'"
                    )
                cls.assert_no_pii_exposed(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for idx, item in enumerate(obj):
                cls.assert_no_pii_exposed(item, f"{path}[{idx}]")


class OfflineQueueSimulator:
    """Simulador de almacenamiento local y cola de sincronización offline (pdul_offline_queue)."""

    def __init__(self, slug: str = "cuestionario-origen-destino-pedul") -> None:
        self.slug = slug
        self.draft_storage_key = f"pdul_draft_{slug}"
        self.draft_storage: Optional[Dict[str, Any]] = None
        self.offline_queue: List[Dict[str, Any]] = []

    def save_draft(self, step: int, data: Dict[str, Any]) -> None:
        self.draft_storage = {
            "step": step,
            "data": data,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    def restore_draft(self) -> Optional[Dict[str, Any]]:
        return self.draft_storage

    def clear_draft(self) -> None:
        self.draft_storage = None

    def enqueue_submission(
        self,
        encuesta_id: str,
        data: Dict[str, Any],
        client_submission_id: Optional[str] = None,
    ) -> str:
        if not client_submission_id:
            import uuid
            client_submission_id = str(uuid.uuid4())

        entry = {
            "client_submission_id": client_submission_id,
            "encuesta_id": encuesta_id,
            "data": data,
            "queued_at": datetime.now(timezone.utc).isoformat(),
            "status": "pending",
        }
        self.offline_queue.append(entry)
        return client_submission_id

    def sync_all(
        self, store: InMemorySubmissionStore
    ) -> List[Dict[str, Any]]:
        results = []
        for entry in list(self.offline_queue):
            payload = {
                "client_submission_id": entry["client_submission_id"],
                "data": entry["data"],
            }
            res = store.submit(entry["encuesta_id"], payload)
            entry["status"] = "synced"
            entry["response"] = res
            results.append(res)
            self.offline_queue.remove(entry)
        return results


class TripChainSimulator:
    """Implementa la lógica UX de pre-llenado inteligente y viaje de retorno en 1 toque."""

    @staticmethod
    def prefill_next_trip(trips: List[Dict[str, Any]], resident_number: int = 1) -> Dict[str, Any]:
        """Pre-llena el siguiente viaje encadenando origen desde el destino anterior."""
        user_trips = [t for t in trips if t.get("persona_numero") == resident_number]
        next_trip_num = len(user_trips) + 1

        if not user_trips:
            return {
                "numero_viaje": next_trip_num,
                "persona_numero": resident_number,
                "origen": "",
                "zona_origen_od": "",
                "hora_salida": "07:00",
                "destino": "",
                "zona_destino_od": "",
                "hora_llegada": "07:30",
                "motivo_viaje": "1",
                "modo_principal": "1",
                "modo_secundario": "ninguno",
                "tiempo_minutos": 30,
                "costo_bolivares": 0.0,
            }

        last_trip = user_trips[-1]
        return {
            "numero_viaje": next_trip_num,
            "persona_numero": resident_number,
            "origen": last_trip.get("destino", ""),
            "zona_origen_od": last_trip.get("zona_destino_od", ""),
            "hora_salida": last_trip.get("hora_llegada", "12:00"),
            "destino": "",
            "zona_destino_od": "",
            "hora_llegada": "",
            "motivo_viaje": "8",  # Frecuente: regreso
            "modo_principal": last_trip.get("modo_principal", "1"),
            "modo_secundario": last_trip.get("modo_secundario", "ninguno"),
            "tiempo_minutos": last_trip.get("tiempo_minutos", 30),
            "costo_bolivares": last_trip.get("costo_bolivares", 0.0),
        }

    @staticmethod
    def one_touch_return_trip(trip_to_invert: Dict[str, Any], next_trip_num: int) -> Dict[str, Any]:
        """Genera el viaje de regreso en 1 toque invirtiendo origen ↔ destino."""
        return {
            "numero_viaje": next_trip_num,
            "persona_numero": trip_to_invert.get("persona_numero", 1),
            "origen": trip_to_invert.get("destino", ""),
            "zona_origen_od": trip_to_invert.get("zona_destino_od", ""),
            "hora_salida": trip_to_invert.get("hora_llegada", "17:00"),
            "destino": trip_to_invert.get("origen", ""),
            "zona_destino_od": trip_to_invert.get("zona_origen_od", ""),
            "hora_llegada": "17:45",
            "motivo_viaje": "8",  # Regreso al hogar
            "modo_principal": trip_to_invert.get("modo_principal", "1"),
            "modo_secundario": trip_to_invert.get("modo_secundario", "ninguno"),
            "tiempo_minutos": trip_to_invert.get("tiempo_minutos", 30),
            "costo_bolivares": trip_to_invert.get("costo_bolivares", 0.0),
        }


class KpiCalculator:
    """Calcula las 4 tarjetas KPI ejecutivas para el Dashboard Municipal."""

    @staticmethod
    def calculate_kpis(submissions: List[Dict[str, Any]]) -> Dict[str, Any]:
        total_encuestas = len(submissions)
        total_viajes = 0
        total_residentes = 0
        modos_conteo: Dict[str, int] = {}
        parroquias_conteo: Dict[str, int] = {}

        for sub in submissions:
            data = sub.get("datos", {})
            residentes = data.get("residentes", [])
            viajes = data.get("viajes", [])

            total_residentes += len(residentes)
            total_viajes += len(viajes)

            parroquia = sub.get("parroquia") or data.get("parroquia")
            if parroquia:
                parroquias_conteo[parroquia] = parroquias_conteo.get(parroquia, 0) + 1

            for v in viajes:
                modo = str(v.get("modo_principal", ""))
                if modo:
                    modos_conteo[modo] = modos_conteo.get(modo, 0) + 1

        # Modo dominante
        modo_dominante = max(modos_conteo, key=modos_conteo.get) if modos_conteo else "1"
        modo_dominante_label = MODOS_TRANSPORTE.get(modo_dominante, "Desconocido")

        # Parroquia con mayor participación
        parroquia_top = max(parroquias_conteo, key=parroquias_conteo.get) if parroquias_conteo else "san_simon"
        parroquia_top_nombre = PARROQUIAS_NOMBRES.get(parroquia_top, parroquia_top)

        promedio_viajes_hogar = round(total_viajes / total_encuestas, 2) if total_encuestas > 0 else 0.0

        return {
            "total_encuestas": total_encuestas,
            "total_residentes": total_residentes,
            "total_viajes": total_viajes,
            "promedio_viajes_hogar": promedio_viajes_hogar,
            "modo_dominante_codigo": modo_dominante,
            "modo_dominante_etiqueta": modo_dominante_label,
            "parroquia_top_codigo": parroquia_top,
            "parroquia_top_nombre": parroquia_top_nombre,
        }


class AccessibleTableGenerator:
    """Genera tablas semánticas HTML WCAG AA para gráficos y mapas interactivos."""

    @staticmethod
    def generate_html_table(caption: str, headers: List[str], rows: List[List[Any]]) -> str:
        lines = [
            f'<figure class="accessible-data-table">',
            f'  <table role="table" aria-label="{caption}">',
            f"    <caption>{caption}</caption>",
            "    <thead>",
            "      <tr>",
        ]
        for h in headers:
            lines.append(f'        <th scope="col">{h}</th>')
        lines.extend(["      </tr>", "    </thead>", "    <tbody>"])
        for r in rows:
            lines.append("      <tr>")
            for idx, cell in enumerate(r):
                if idx == 0:
                    lines.append(f'        <th scope="row">{cell}</th>')
                else:
                    lines.append(f"        <td>{cell}</td>")
            lines.append("      </tr>")
        lines.extend(["    </tbody>", "  </table>", "</figure>"])
        return "\n".join(lines)
