from dataclasses import dataclass
import re
from typing import Any, Optional

CEDULA_RE = re.compile(r"^[0-9]{6,9}$")


def normalize_cedula_value(val: Any) -> Optional[str]:
    """Normaliza y valida la cédula venezolana (6 a 9 dígitos numéricos)."""
    if val is None:
        return None

    raw_str = str(val).strip()
    if not raw_str:
        return None

    digits = re.sub(r"\D", "", raw_str)
    if not CEDULA_RE.match(digits):
        raise ValueError(
            "Escriba solo los números de su cédula (6 a 9 dígitos, sin puntos ni guiones)."
        )
    return digits


@dataclass(frozen=True)
class Cedula:
    """Objeto de valor inmutable para la cédula de identidad ciudadana."""

    value: str

    def __post_init__(self) -> None:
        normalized = normalize_cedula_value(self.value)
        if normalized is None:
            raise ValueError("La cédula es requerida para construir el objeto Cedula.")
        object.__setattr__(self, "value", normalized)

    @classmethod
    def from_optional(cls, raw: Any) -> Optional["Cedula"]:
        normalized = normalize_cedula_value(raw)
        if normalized is None:
            return None
        return cls(normalized)

    def __str__(self) -> str:
        return self.value
