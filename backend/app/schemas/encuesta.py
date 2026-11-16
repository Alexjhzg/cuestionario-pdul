import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class EncuestaBase(BaseModel):
    titulo: str = Field(..., max_length=255, description="Título descriptivo de la encuesta")
    slug: str = Field(..., max_length=120, description="Identificador amigable único en URL")
    tipo_instrumento: str = Field(
        default="consulta_ciudadana",
        max_length=30,
        description="Tipo de instrumento (consulta_ciudadana, encuesta_od_pdul, etc.)",
    )
    activa: bool = Field(default=True, description="Estado de disponibilidad para recepción de envíos")


class EncuestaCreate(EncuestaBase):
    esquema_formio: Dict[str, Any] = Field(
        ..., description="Esquema JSON compatible con Form.io (@formio/js)"
    )


class EncuestaUpdate(BaseModel):
    titulo: Optional[str] = Field(default=None, max_length=255)
    tipo_instrumento: Optional[str] = Field(default=None, max_length=30)
    esquema_formio: Optional[Dict[str, Any]] = None
    activa: Optional[bool] = None


class EncuestaEstadoUpdate(BaseModel):
    activa: bool = Field(..., description="Nuevo estado activo (True/False)")


class EncuestaOut(EncuestaBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    esquema_formio: Dict[str, Any]
    creado_en: datetime


class EncuestaListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    titulo: str
    slug: str
    tipo_instrumento: str
    activa: bool
    creado_en: datetime
    total_respuestas: int = 0
