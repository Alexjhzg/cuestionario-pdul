"""Shared opaque-box fixtures, constants, server launchers, and payload builders
for Tier 1–4 acceptance tests (cuestionario-pedul improvements R1, R2, R3).
"""

from __future__ import annotations

import hashlib
import mimetypes
import os
import socket
import subprocess
import tempfile
import threading
import time
import uuid
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Iterator, Optional
from urllib.parse import unquote, urlsplit

import httpx
import pytest

REPO_ROOT: Path = Path(__file__).resolve().parents[2]
FRONTEND_DIST_DIR: Path = REPO_ROOT / "frontend" / "dist"
BACKEND_VENV_BIN: Path = REPO_ROOT / "backend" / ".venv" / "bin"
PYTHON_BIN: Path = BACKEND_VENV_BIN / "python"
ALEMBIC_BIN: Path = BACKEND_VENV_BIN / "alembic"
UVICORN_BIN: Path = BACKEND_VENV_BIN / "uvicorn"

CANONICAL_SURVEY_ID: str = "00000000-0000-0000-0000-000000000001"
CANONICAL_SURVEY_SLUG: str = "cuestionario-od-maturin"
LEGACY_SURVEY_SLUG: str = "pdul_origen_destino"

R3_BASELINES: Dict[str, int] = {
    "frontend/src/views/AdminResponsesView.vue": 1633,
    "frontend/src/components/survey/ViajesMobileCards.vue": 1276,
    "frontend/src/views/AdminSurveyListView.vue": 991,
    "frontend/src/views/DashboardView.vue": 989,
    "frontend/src/views/FormBuilderView.vue": 895,
    "backend/app/services/question_analytics.py": 768,
}

RESIDUAL_FILES: Dict[str, Dict[str, Any]] = {
    "pdf_text.txt": {
        "size": 9729,
        "sha256": "5f656d3c7d4ebdd6867b615beea13849ac1e807e937b56f5e96f97617e7fece7",
    },
    "skills-antigravity-alcaldia.zip": {
        "size": 54714,
        "sha256": "618bce934250dc7386d4096bc31a05110948f6f85af065c255680d74eba16d6d",
    },
    "pdul_dev.db.backup_pre_seed": {
        "size": 110592,
        "sha256": "8592845c7c9611eb63b51c0d4c1f5e68263d5747327abda44a0c9d0be2fd4a2a",
    },
}

# All 11 PII fields from shared/types/pii.ts & backend/app/services/normalizers.py
PII_FIELDS: tuple[str, ...] = (
    "cedula",
    "nombre_apellido",
    "nombres_apellidos",
    "nombre",
    "apellido",
    "telefono",
    "correo",
    "email",
    "casa_apartamento",
    "avenida_calle",
    "direccion_exacta",
)


def free_tcp_port() -> int:
    """Allocate an ephemeral unused TCP port on 127.0.0.1."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        sock.listen(1)
        return int(sock.getsockname()[1])


def sha256_file(path: Path) -> str:
    """Compute SHA-256 hex digest of a file in streaming chunks."""
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def wait_for_health(
    base_url: str,
    timeout: float = 25.0,
    proc: Optional[subprocess.Popen[str]] = None,
    log_path: Optional[Path] = None,
) -> None:
    """Poll GET /health until HTTP 200 or raise RuntimeError."""
    deadline = time.monotonic() + timeout
    last_error: Optional[str] = None
    while time.monotonic() < deadline:
        if proc is not None and proc.poll() is not None:
            logs = ""
            if log_path is not None and log_path.is_file():
                logs = log_path.read_text(encoding="utf-8", errors="replace")
            elif proc.stdout is not None:
                stdout_data, stderr_data = proc.communicate(timeout=2)
                logs = f"STDOUT:\n{stdout_data}\nSTDERR:\n{stderr_data}"
            raise RuntimeError(
                f"uvicorn exited prematurely with code {proc.returncode}.\n{logs}"
            )
        try:
            resp = httpx.get(f"{base_url}/health", timeout=1.5)
            if resp.status_code == 200:
                return
            last_error = f"HTTP {resp.status_code}: {resp.text}"
        except Exception as exc:  # noqa: BLE001
            last_error = repr(exc)
        time.sleep(0.2)
    raise RuntimeError(f"Timed out waiting for {base_url}/health: {last_error}")


@contextmanager
def launch_isolated_uvicorn(
    database_url: str,
    sqlite_fallback_url: str,
    extra_env: Optional[Dict[str, str]] = None,
    timeout: float = 25.0,
) -> Iterator[Dict[str, Any]]:
    """Launch an ephemeral uvicorn process isolated from root pdul_dev.db."""
    port = free_tcp_port()
    base_url = f"http://127.0.0.1:{port}"
    env = os.environ.copy()
    env["DATABASE_URL"] = database_url
    env["SQLITE_FALLBACK_URL"] = sqlite_fallback_url
    env["PYTHONUNBUFFERED"] = "1"
    if extra_env:
        env.update(extra_env)

    cmd = [
        str(UVICORN_BIN),
        "backend.app.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
    ]
    log_file = tempfile.NamedTemporaryFile(
        mode="w+",
        encoding="utf-8",
        prefix="uvicorn_e2e_",
        suffix=".log",
        delete=False,
    )
    log_path = Path(log_file.name)
    proc = subprocess.Popen(
        cmd,
        cwd=str(REPO_ROOT),
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        wait_for_health(base_url, timeout=timeout, proc=proc, log_path=log_path)
        yield {"base_url": base_url, "port": port, "proc": proc}
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=8)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=4)
        log_file.close()
        log_path.unlink(missing_ok=True)


def _guess_mime_type(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    overrides = {
        ".js": "application/javascript; charset=utf-8",
        ".mjs": "application/javascript; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".html": "text/html; charset=utf-8",
        ".json": "application/json; charset=utf-8",
        ".svg": "image/svg+xml",
        ".png": "image/png",
        ".woff": "font/woff",
        ".woff2": "font/woff2",
        ".ttf": "font/ttf",
        ".eot": "application/vnd.ms-fontobject",
        ".ico": "image/x-icon",
    }
    if suffix in overrides:
        return overrides[suffix]
    guessed, _ = mimetypes.guess_type(str(file_path))
    return guessed or "application/octet-stream"


@contextmanager
def start_dist_proxy_server(
    backend_base_url: str,
    dist_dir: Path = FRONTEND_DIST_DIR,
) -> Iterator[str]:
    """Serve built frontend/dist static assets + SPA fallback and proxy /api/* and /health."""
    if not dist_dir.is_dir() or not (dist_dir / "index.html").is_file():
        raise RuntimeError(
            f"Built frontend/dist missing at {dist_dir}. Run `npm --prefix frontend run build`."
        )

    dist_root = dist_dir.resolve()
    hop_by_hop = {
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
        "content-length",
    }

    class DistProxyHandler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
            return

        def _proxy_request(self) -> None:
            target_url = f"{backend_base_url}{self.path}"
            content_length = int(self.headers.get("Content-Length", "0") or "0")
            req_body = self.rfile.read(content_length) if content_length > 0 else None

            forward_headers = {}
            for k, v in self.headers.items():
                lk = k.lower()
                if lk in {"host", "content-length", "connection"}:
                    continue
                forward_headers[k] = v

            with httpx.Client(timeout=60.0) as client:
                with client.stream(
                    method=self.command,
                    url=target_url,
                    headers=forward_headers,
                    content=req_body,
                ) as upstream:
                    upstream_te = upstream.headers.get("transfer-encoding", "")
                    is_chunked = "chunked" in upstream_te.lower()
                    upstream_cl = upstream.headers.get("content-length")

                    self.send_response(upstream.status_code)
                    for k, v in upstream.headers.items():
                        lk = k.lower()
                        if lk in hop_by_hop or lk in {"server", "date"}:
                            continue
                        self.send_header(k, v)

                    if is_chunked:
                        self.send_header("Transfer-Encoding", "chunked")
                    elif upstream_cl is not None:
                        self.send_header("Content-Length", upstream_cl)
                    else:
                        self.close_connection = True

                    self.end_headers()

                    if self.command != "HEAD":
                        for chunk in upstream.iter_raw():
                            if not chunk:
                                continue
                            if is_chunked:
                                frame = f"{len(chunk):x}\r\n".encode("ascii") + chunk + b"\r\n"
                                self.wfile.write(frame)
                            else:
                                self.wfile.write(chunk)
                            self.wfile.flush()
                        if is_chunked:
                            self.wfile.write(b"0\r\n\r\n")
                            self.wfile.flush()

        def _serve_static(self) -> None:
            parsed = urlsplit(self.path)
            rel_path = unquote(parsed.path).lstrip("/")
            candidate = (dist_root / rel_path).resolve()

            # Prevent directory traversal outside dist_root
            if dist_root not in candidate.parents and candidate != dist_root:
                self.send_response(403)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return

            if candidate.is_file():
                target_file = candidate
            elif rel_path == "" or "." not in Path(rel_path).name:
                # SPA fallback for / and /admin routes without file extension
                target_file = dist_root / "index.html"
            else:
                self.send_response(404)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return

            data = target_file.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", _guess_mime_type(target_file))
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(data)

        def _handle(self) -> None:
            parsed_path = urlsplit(self.path).path
            if parsed_path.startswith("/api/") or parsed_path == "/api" or parsed_path == "/health":
                self._proxy_request()
            else:
                self._serve_static()

        def do_GET(self) -> None:  # noqa: N802
            self._handle()

        def do_HEAD(self) -> None:  # noqa: N802
            self._handle()

        def do_POST(self) -> None:  # noqa: N802
            self._handle()

        def do_PUT(self) -> None:  # noqa: N802
            self._handle()

        def do_PATCH(self) -> None:  # noqa: N802
            self._handle()

        def do_DELETE(self) -> None:  # noqa: N802
            self._handle()

        def do_OPTIONS(self) -> None:  # noqa: N802
            self._handle()

    port = free_tcp_port()
    server = ThreadingHTTPServer(("127.0.0.1", port), DistProxyHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def build_minimal_citizen_payload(
    parroquia: str = "san_simon",
    client_submission_id: Optional[str] = None,
    **overrides: Any,
) -> Dict[str, Any]:
    """Build minimal valid FormioSubmissionIn payload."""
    data: Dict[str, Any] = {"parroquia": parroquia}
    data.update(overrides)
    return {
        "client_submission_id": client_submission_id or str(uuid.uuid4()),
        "data": data,
    }


def build_full_citizen_payload(
    cedula: Optional[str] = "18456789",
    parroquia: str = "alto_de_los_godos",
    client_submission_id: Optional[str] = None,
    include_all_pii: bool = True,
    mixed_case_nested_pii: bool = False,
    **overrides: Any,
) -> Dict[str, Any]:
    """Build full citizen OD survey payload including ViajesMobileCards trips,
    residentes, and all 11 PII fields when requested.
    """
    residente_1: Dict[str, Any] = {
        "persona_numero": 1,
        "nombres": "Ana Pérez",
        "nombre_apellido": "Ana Pérez",
        "nombres_apellidos": "Ana María Pérez",
        "nombre": "Ana",
        "apellido": "Pérez",
        "parentesco": "1",
        "parentesco_jefe_hogar": "jefe",
        "sexo": "2",
        "edad": 34,
        "sabe_leer_escribir": "si",
        "nivel_educativo": "universitario",
        "actividad_principal": "1",
        "ocupacion_principal": "Empleada pública",
        "medio_transporte_habitual": "6",
        "posee_licencia": "si",
        "tiene_vehiculo_disponible": "no",
    }
    if mixed_case_nested_pii:
        residente_1["Telefono"] = "0414-5550199"
        residente_1["Email"] = "ana.nested@ejemplo.ve"
        residente_1["Nombre_Apellido"] = "Ana Nested"

    data: Dict[str, Any] = {
        "schema_version": "1.0.0",
        "parroquia": parroquia,
        "comunidad_sector": "Los Godos Sector III",
        "zona_residencia_od": "Z-01",
        "tipo_vivienda": "casa",
        "total_cuartos_vivienda": 4,
        "grupos_gastos_separados": 1,
        "hogar_numero": 1,
        "cuartos_dormir_hogar": 3,
        "numero_personas_hogar": 1,
        "tenencia_vivienda": "propia_pagada",
        "residentes": [residente_1],
        "viajes": [
            {
                "viaje_numero": 1,
                "persona_numero": 1,
                "origen_direccion": "Av. Raúl Leoni, Casa 14",
                "zona_od_origen": parroquia,
                "destino_direccion": "Av. Bolívar, Alcaldía",
                "zona_od_destino": "san_simon",
                "hora_salida": "07:30 AM",
                "hora_llegada": "08:05 AM",
                "motivo_viaje": "1",
                "modo_principal": "6",
                "modo_secundario": "1",
                "tiempo_viaje_min": 35,
                "costo_viaje_bs": 15,
            },
            {
                "viaje_numero": 2,
                "persona_numero": 1,
                "origen_direccion": "Av. Bolívar, Alcaldía",
                "zona_od_origen": "san_simon",
                "destino_direccion": "Av. Raúl Leoni, Casa 14",
                "zona_od_destino": parroquia,
                "hora_salida": "04:30 PM",
                "hora_llegada": "05:05 PM",
                "motivo_viaje": "1",
                "modo_principal": "6",
                "tiempo_viaje_min": 35,
                "costo_viaje_bs": 0,
            },
        ],
        "rutas_tp_dia": 1,
        "tiempo_espera_paradas_min": 10,
        "km_residencia_parada": 0.4,
        "dificultades_acceso_tp": "no",
        "calificacion_servicio_tp": "bueno",
        "gasto_semanal_transporte_bs": 150,
        "acuerdo_rutas_directas": "de_acuerdo",
        "comentarios_transporte_maturin": "Mejorar frecuencia matutina.",
        "cambio_movilidad_5_anos": "no",
        "caminatas_mas_10min": "si",
        "usa_bicicleta": "no",
        "dias_camina_bici_semana": 5,
        "modo_actividades_centro": "transporte_publico",
        "aceras_adecuadas": "no",
        "seguridad_desplazamiento_centro": "neutral",
        "frecuencia_visita_parques": "semanal",
        "actividades_parques": ["caminar"],
        "caminatas_ciudad": "a_veces",
        "seguridad_parques_dia": "bastante_seguro",
        "seguridad_parques_noche": "poco_seguro",
        "limpieza_parques": "regular",
        "impedimentos_espacios": ["falta_tiempo"],
        "satisfaccion_centro": "neutral",
        "mejoras_prioritarias": ["iluminacion"],
        "parque_mejorar_primero": "Parque La Guaricha",
        "disposicion_participar_mejoras": "si",
        "sugerencias_esparcimiento": "Más iluminación nocturna.",
        "acera_comoda": "en_desacuerdo",
        "sectores_para_caminar": "Av. Bolívar",
        "facilidad_llegada_parques": "facil",
        "esparcimientos_faltantes": ["iluminacion"],
        "cruce_peatonal_todas": "si",
        "cruce_demarcado_visible": "no",
        "seguridad_cruzar_interseccion": "poco_seguro",
        "hay_semaforo_peatonal": "si",
        "mapas_senales_caminata": "no",
        "movilidad_reducida_sin_ayuda": "no",
        "nombres_calles_visibles": "si",
        "senalizacion_clara_sin_obstaculos": "no",
        "trayecto_pie_parada_seguro": "neutral",
        "aire_ruido_aceptables": "si",
        "conductores_ceden_paso": "no",
        "ciudad_prioriza_peaton": "no",
        "participacion_consultas_peatonales": "no",
        "planes_movilidad_peatonal_normativa": "no_sabe",
        "observaciones_generales": "Encuesta de prueba completa.",
        "acepta_declaracion": True,
    }

    if cedula is not None:
        data["cedula"] = cedula

    if include_all_pii:
        data.update(
            {
                "nombre_apellido": "Ana María Pérez",
                "nombres_apellidos": "Ana María Pérez Gómez",
                "nombre": "Ana",
                "apellido": "Pérez",
                "telefono": "0414-1234567",
                "correo": "ana.perez@ejemplo.ve",
                "email": "ana.alt@ejemplo.ve",
                "casa_apartamento": "Casa 14-B",
                "avenida_calle": "Av. Raúl Leoni",
                "direccion_exacta": "Av. Raúl Leoni, Casa 14-B, Sector III",
            }
        )

    data.update(overrides)
    return {
        "client_submission_id": client_submission_id or str(uuid.uuid4()),
        "data": data,
    }


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def frontend_dist_dir() -> Path:
    return FRONTEND_DIST_DIR


@pytest.fixture(scope="session")
def canonical_survey_id() -> str:
    return CANONICAL_SURVEY_ID


@pytest.fixture(scope="session")
def pii_fields() -> tuple[str, ...]:
    return PII_FIELDS


@pytest.fixture(scope="session")
def r3_baselines() -> Dict[str, int]:
    return R3_BASELINES


@pytest.fixture(scope="session")
def residual_files() -> Dict[str, Dict[str, Any]]:
    return RESIDUAL_FILES


@pytest.fixture()
def isolated_backend_server(tmp_path: Path) -> Iterator[Dict[str, Any]]:
    """Per-test ephemeral uvicorn server backed by temp SQLite files."""
    app_db = tmp_path / "app_test.db"
    fallback_db = tmp_path / "fallback_test.db"
    db_url = f"sqlite+aiosqlite:///{app_db}"
    fallback_url = f"sqlite+aiosqlite:///{fallback_db}"
    with launch_isolated_uvicorn(db_url, fallback_url) as server_info:
        yield {
            **server_info,
            "db_path": app_db,
            "fallback_db_path": fallback_db,
            "database_url": db_url,
            "fallback_url": fallback_url,
        }


@pytest.fixture()
def dist_proxy_server(
    isolated_backend_server: Dict[str, Any],
) -> Iterator[Dict[str, Any]]:
    """Per-test built frontend/dist static + /api reverse proxy backed by isolated uvicorn."""
    with start_dist_proxy_server(isolated_backend_server["base_url"]) as proxy_url:
        yield {
            "base_url": proxy_url,
            "backend_url": isolated_backend_server["base_url"],
            "db_path": isolated_backend_server["db_path"],
        }
