from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
import uuid


@dataclass
class CitizenSubmission:
    """Entidad de dominio que representa una respuesta ciudadana registrada."""

    encuesta_id: uuid.UUID
    parroquia: str
    datos: Dict[str, Any] = field(default_factory=dict)
    client_submission_id: Optional[uuid.UUID] = None
    cedula: Optional[str] = None
    zona_od: Optional[str] = None
    id: Optional[int] = None
    fecha_registro: Optional[datetime] = None
