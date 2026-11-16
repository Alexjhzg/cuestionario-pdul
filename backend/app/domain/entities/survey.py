from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
import uuid

from backend.app.domain.exceptions import SurveyInactiveError


@dataclass
class Survey:
    """Entidad de dominio que representa un instrumento de encuesta ciudadana o PDUL."""

    id: uuid.UUID
    titulo: str
    slug: str
    tipo_instrumento: str
    esquema_formio: Dict[str, Any] = field(default_factory=dict)
    activa: bool = True
    creado_en: Optional[datetime] = None

    def ensure_accepts_submissions(self) -> None:
        if not self.activa:
            raise SurveyInactiveError()
