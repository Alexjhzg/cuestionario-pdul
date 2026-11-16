from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ProblemDetailOut(BaseModel):
    """Estructura de error estándar RFC 7807 amigable con citizen-survey-ux."""

    code: str = Field(..., description="Código máquina del error")
    title: str = Field(..., description="Título legible del error")
    status: int = Field(..., description="Código de estado HTTP")
    detail: str = Field(..., description="Detalle del error")
    field: Optional[str] = Field(default=None, description="Campo del formulario afectado si aplica")
    errors: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Lista detallada de errores de validación de campos"
    )
