from dataclasses import dataclass
import re
from typing import Any, Set
import unicodedata

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


def strip_accents(text: str) -> str:
    """Remueve acentos y diacríticos de un texto."""
    nfkd_form = unicodedata.normalize("NFKD", text)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])


def normalize_parroquia_value(val: Any) -> str:
    """Normaliza la parroquia contra el catálogo oficial o conserva la entrada libre no vacía."""
    if val is None or not str(val).strip():
        raise ValueError("La parroquia es requerida.")

    raw = str(val).strip()
    s = strip_accents(raw.lower())
    s = re.sub(r"[\s\-]+", "_", s)
    s = re.sub(r"[^a-z0-9_]", "", s)

    if s in PARROQUIAS_MATURIN:
        return s
    return raw


@dataclass(frozen=True)
class Parroquia:
    """Objeto de valor inmutable para la parroquia de residencia o consulta."""

    code_or_label: str

    def __post_init__(self) -> None:
        normalized = normalize_parroquia_value(self.code_or_label)
        object.__setattr__(self, "code_or_label", normalized)

    @property
    def is_official(self) -> bool:
        return self.code_or_label in PARROQUIAS_MATURIN

    def __str__(self) -> str:
        return self.code_or_label
