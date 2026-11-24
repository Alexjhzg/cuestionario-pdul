from datetime import datetime
from typing import List, Literal, Optional
import uuid

from pydantic import BaseModel, Field

CalidadUbicacion = Literal["alta", "media", "alerta"]


class FieldMapPointOut(BaseModel):
    """Punto georreferenciado no-PII de levantamiento de una encuesta en campo."""

    id: int
    latitud: float
    longitud: float
    precision_m: Optional[float] = None
    parroquia: str
    comunidad_sector: Optional[str] = None
    zona_od: Optional[str] = None
    dispositivo_tipo: str = "desconocido"
    fecha_registro: Optional[datetime] = None
    calidad_ubicacion: CalidadUbicacion
    motivo_alerta: Optional[str] = None


class FieldMapSummaryOut(BaseModel):
    """Resumen de cobertura GPS y puntos de levantamiento por encuesta."""

    encuesta_id: uuid.UUID
    total_respuestas: int = Field(default=0, ge=0)
    total_con_gps: int = Field(default=0, ge=0)
    total_sin_gps: int = Field(default=0, ge=0)
    porcentaje_cobertura_gps: float = Field(default=0.0, ge=0.0, le=100.0)
    total_alertas_ubicacion: int = Field(default=0, ge=0)
    puntos: List[FieldMapPointOut] = Field(default_factory=list)

