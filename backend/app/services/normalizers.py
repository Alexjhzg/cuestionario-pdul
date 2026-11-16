import re
import unicodedata
from typing import Any, Dict, List, Optional, Set

PARROQUIAS_MATURIN: Set[str] = {
    "alto_de_los_godos",
    "boqueron",
    "las_cocuizas",
    "la_cruz",
    "san_simon",
    "santa_cruz",
    "el_corozo",
    "el_furrial",
    "jusepin",
    "la_pica",
    "san_vicente",
}

CEDULA_RE = re.compile(r"^[0-9]{6,9}$")

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


def strip_accents(text: str) -> str:
    """Remueve acentos y diacríticos de un texto."""
    nfkd_form = unicodedata.normalize("NFKD", text)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])


def normalize_parroquia(val: Any) -> str:
    """Normaliza la parroquia.

    La pregunta es abierta (igual que en el cuestionario en papel): si el texto coincide con una
    parroquia oficial de Maturín se devuelve su código interno; en caso contrario se conserva el
    texto escrito por el ciudadano. Solo se exige que no esté vacío.
    """
    if val is None or not str(val).strip():
        raise ValueError("La parroquia es requerida.")

    raw = str(val).strip()
    s = strip_accents(raw.lower())
    s = re.sub(r"[\s\-]+", "_", s)
    s = re.sub(r"[^a-z0-9_]", "", s)

    if s in PARROQUIAS_MATURIN:
        return s
    return raw


def normalize_cedula(val: Any) -> Optional[str]:
    """Normaliza y valida la cédula de identidad venezolana (6 a 9 dígitos numéricos)."""
    if val is None:
        return None

    raw_str = str(val).strip()
    if not raw_str:
        return None

    # Extraer únicamente los dígitos (elimina V-, E-, puntos, espacios, etc.)
    digits = re.sub(r"\D", "", raw_str)

    if not CEDULA_RE.match(digits):
        raise ValueError(
            "Escriba solo los números de su cédula (6 a 9 dígitos, sin puntos ni guiones)."
        )

    return digits


def sanitize_pii(data: Any) -> Any:
    """Recursivamente anonimiza campos de identificación personal (PII) en diccionarios y listas."""
    if isinstance(data, dict):
        sanitized = {}
        for k, v in data.items():
            k_lower = k.lower()
            if k_lower in PII_FIELDS:
                continue  # Excluir campos de PII en analítica y reportes
            sanitized[k] = sanitize_pii(v)
        return sanitized
    elif isinstance(data, list):
        return [sanitize_pii(item) for item in data]
    return data
