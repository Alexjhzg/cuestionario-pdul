import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.app.services.normalizers import (
    normalize_cedula,
    normalize_parroquia,
)


class FormioSubmissionIn(BaseModel):
    """Valida tanto un payload envuelto en {'data': {...}} como el objeto directo."""

    model_config = ConfigDict(extra="ignore")

    data: Dict[str, Any] = Field(..., description="Datos del formulario enviados por @formio/js")
    client_submission_id: Optional[UUID] = Field(
        default=None,
        description="UUID v4 generado en el cliente para garantizar idempotencia offline.",
    )
    cedula_limpia: Optional[str] = None
    parroquia: str = ""
    zona_od: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def unwrap_formio_payload(cls, values: Any) -> Dict[str, Any]:
        if not isinstance(values, dict):
            return {"data": {}}

        # Si no viene envuelto en 'data', envolver todo en 'data'
        if "data" not in values:
            client_sub_id = values.get("client_submission_id")
            # Extraer de values si viene directo
            return {
                "data": values,
                "client_submission_id": client_sub_id,
            }

        # Si viene envuelto en 'data'
        data_content = values.get("data")
        if not isinstance(data_content, dict):
            data_content = {}
            values["data"] = data_content

        client_sub_id = values.get("client_submission_id")
        if not client_sub_id and "client_submission_id" in data_content:
            client_sub_id = data_content.get("client_submission_id")

        if client_sub_id:
            try:
                if isinstance(client_sub_id, str):
                    values["client_submission_id"] = UUID(client_sub_id)
                elif isinstance(client_sub_id, UUID):
                    values["client_submission_id"] = client_sub_id
            except (ValueError, TypeError):
                # Dejar que la validación estándar de tipo maneje o ignore
                pass

        return values

    @model_validator(mode="after")
    def validate_and_extract_indexed_fields(self) -> "FormioSubmissionIn":
        # 1. Cédula
        raw_cedula = self.data.get("cedula")
        self.cedula_limpia = normalize_cedula(raw_cedula)
        if self.cedula_limpia is not None:
            self.data["cedula"] = self.cedula_limpia

        # 2. Parroquia (obligatoria)
        raw_parroquia = self.data.get("parroquia")
        self.parroquia = normalize_parroquia(raw_parroquia)
        self.data["parroquia"] = self.parroquia

        # 3. Zona OD (residencia)
        zona = self.data.get("zona_residencia_od") or self.data.get("zona_od")
        self.zona_od = str(zona).strip() if zona else None
        if self.zona_od:
            self.data["zona_od"] = self.zona_od

        # 4. Validar viajes si existen en el payload
        viajes = self.data.get("viajes")
        if isinstance(viajes, list):
            for idx, viaje in enumerate(viajes):
                if isinstance(viaje, dict):
                    # Validar tiempo de viaje si fue completado
                    tiempo_raw = viaje.get("tiempo_viaje_min")
                    if tiempo_raw not in (None, ""):
                        try:
                            tiempo = float(tiempo_raw)
                            if tiempo <= 0:
                                raise ValueError(
                                    f"En el viaje #{idx + 1}, el tiempo de viaje debe ser mayor a 0 minutos."
                                )
                        except (TypeError, ValueError) as err:
                            if "mayor a 0" in str(err):
                                raise
                            raise ValueError(
                                f"En el viaje #{idx + 1}, el tiempo de viaje debe ser un número válido."
                            )

        return self


class SubmissionReceiptOut(BaseModel):
    id: int = Field(..., description="Identificador único del registro en la base de datos")
    fecha_registro: datetime = Field(..., description="Marca temporal del registro")
    idempotent_replay: bool = Field(
        default=False,
        description="Indica si la respuesta fue recuperada de un envío idéntico previo",
    )
    mensaje: str = Field(..., description="Mensaje explicativo para el usuario o encuestador")
