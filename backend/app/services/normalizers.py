from typing import Any, Dict, Optional, Set

from backend.app.domain.value_objects.cedula import (
    CEDULA_RE,
    normalize_cedula_value,
)
from backend.app.domain.value_objects.parroquia import (
    PARROQUIAS_MATURIN,
    normalize_parroquia_value,
    strip_accents,
)

PII_FIELDS: Set[str] = {
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
}


def normalize_parroquia(val: Any) -> str:
    """Delega al objeto de valor Parroquia preservando compatibilidad de firma."""
    return normalize_parroquia_value(val)


def normalize_cedula(val: Any) -> Optional[str]:
    """Delega al objeto de valor Cedula preservando compatibilidad de firma."""
    return normalize_cedula_value(val)


def sanitize_pii(data: Any) -> Any:
    """Recursivamente anonimiza campos de identificación personal (PII) en diccionarios y listas."""
    if isinstance(data, dict):
        sanitized: Dict[str, Any] = {}
        for k, v in data.items():
            k_lower = k.lower()
            if k_lower in PII_FIELDS:
                continue  # Excluir campos de PII en analítica y reportes
            sanitized[k] = sanitize_pii(v)
        return sanitized
    elif isinstance(data, list):
        return [sanitize_pii(item) for item in data]
    return data
