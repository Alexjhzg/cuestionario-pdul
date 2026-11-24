import math
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.app.domain.value_objects import (
    normalize_cedula_value as normalize_cedula,
    normalize_parroquia_value as normalize_parroquia,
)


VALID_DEVICE_TYPES = {"movil", "tablet", "escritorio", "desconocido"}


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
        zona_clean = str(zona).strip() if zona else ""
        self.zona_od = zona_clean[:120] if zona_clean else None
        if self.zona_od:
            self.data["zona_od"] = self.zona_od

        # 4. Validar coordenadas GPS si fueron enviadas
        raw_lat = self.data.get("gps_latitud")
        raw_lng = self.data.get("gps_longitud")
        has_lat = raw_lat not in (None, "")
        has_lng = raw_lng not in (None, "")
        if has_lat or has_lng:
            if not (has_lat and has_lng):
                raise ValueError(
                    "Las coordenadas GPS deben incluir tanto latitud como longitud."
                )
            try:
                lat = float(raw_lat)
                lng = float(raw_lng)
            except (TypeError, ValueError):
                raise ValueError("Las coordenadas GPS deben ser valores numéricos válidos.")
            if not (math.isfinite(lat) and math.isfinite(lng)) or not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                raise ValueError(
                    "Las coordenadas GPS están fuera de rango válido (latitud -90..90, longitud -180..180)."
                )

        # 5. Validar residentes si existen en el payload
        residentes = self.data.get("residentes")
        if residentes is not None:
            if not isinstance(residentes, list):
                raise ValueError("El campo 'residentes' debe ser una lista.")
            for idx, res in enumerate(residentes):
                if not isinstance(res, dict):
                    continue
                edad_raw = res.get("edad")
                edad_num: Optional[float] = None
                if edad_raw not in (None, ""):
                    try:
                        edad_num = float(edad_raw)
                    except (TypeError, ValueError):
                        raise ValueError(
                            f"En el residente #{idx + 1}, la edad debe ser un número válido."
                        )
                    if not math.isfinite(edad_num) or edad_num < 0 or edad_num > 120:
                        raise ValueError(
                            f"En el residente #{idx + 1}, la edad debe estar entre 0 y 120 años."
                        )
                if edad_num is not None and edad_num < 16 and str(res.get("posee_licencia", "")).strip().lower() == "si":
                    raise ValueError(
                        f"En el residente #{idx + 1}, un menor de 16 años no puede registrar licencia de conducir."
                    )
                cant_veh_raw = res.get("cantidad_vehiculo")
                if cant_veh_raw not in (None, ""):
                    try:
                        cant_veh = float(cant_veh_raw)
                    except (TypeError, ValueError):
                        raise ValueError(
                            f"En el residente #{idx + 1}, la cantidad de vehículos debe ser un número válido."
                        )
                    if not math.isfinite(cant_veh) or cant_veh < 1:
                        raise ValueError(
                            f"En el residente #{idx + 1}, la cantidad de vehículos debe ser al menos 1."
                        )

        # 6. Validar viajes si existen en el payload
        viajes = self.data.get("viajes")
        if viajes is not None:
            if not isinstance(viajes, list):
                raise ValueError("El campo 'viajes' debe ser una lista.")
            for idx, viaje in enumerate(viajes):
                if isinstance(viaje, dict):
                    # Validar persona_numero si fue completado
                    persona_raw = viaje.get("persona_numero")
                    if persona_raw not in (None, ""):
                        try:
                            persona_num = float(persona_raw)
                        except (TypeError, ValueError):
                            raise ValueError(
                                f"En el viaje #{idx + 1}, el número de persona debe ser un número válido."
                            )
                        if not math.isfinite(persona_num) or persona_num < 1:
                            raise ValueError(
                                f"En el viaje #{idx + 1}, el número de persona debe ser mayor o igual a 1."
                            )

                    # Validar tiempo de viaje si fue completado
                    tiempo_raw = viaje.get("tiempo_viaje_min")
                    if tiempo_raw not in (None, ""):
                        try:
                            tiempo = float(tiempo_raw)
                            if not math.isfinite(tiempo) or tiempo <= 0:
                                raise ValueError(
                                    f"En el viaje #{idx + 1}, el tiempo de viaje debe ser mayor a 0 minutos."
                                )
                        except (TypeError, ValueError) as err:
                            if "mayor a 0" in str(err):
                                raise
                            raise ValueError(
                                f"En el viaje #{idx + 1}, el tiempo de viaje debe ser un número válido."
                            )

                    # Validar costo de viaje si fue completado
                    costo_raw = viaje.get("costo_viaje_bs")
                    if costo_raw not in (None, ""):
                        try:
                            costo = float(costo_raw)
                        except (TypeError, ValueError):
                            raise ValueError(
                                f"En el viaje #{idx + 1}, el costo del viaje debe ser un número válido."
                            )
                        if not math.isfinite(costo) or costo < 0:
                            raise ValueError(
                                f"En el viaje #{idx + 1}, el costo del viaje no puede ser negativo."
                            )

        # 7. Validar rutas_tp_dia / rutas_tp_utilizadas_dia si existen
        for tp_key in ("rutas_tp_dia", "rutas_tp_utilizadas_dia"):
            tp_raw = self.data.get(tp_key)
            if tp_raw not in (None, ""):
                try:
                    tp_val = float(tp_raw)
                except (TypeError, ValueError):
                    raise ValueError(
                        f"El campo '{tp_key}' debe ser un número válido."
                    )
                if not math.isfinite(tp_val) or tp_val < 0:
                    raise ValueError(
                        f"El campo '{tp_key}' no puede ser negativo."
                    )

        # 8. Normalizar tipo de dispositivo si fue enviado
        raw_device = self.data.get("dispositivo_tipo")
        if raw_device not in (None, ""):
            norm_device = str(raw_device).strip().lower()
            if norm_device in ("mobile", "phone", "smartphone", "celular"):
                norm_device = "movil"
            elif norm_device in ("desktop", "pc", "laptop"):
                norm_device = "escritorio"
            elif norm_device not in VALID_DEVICE_TYPES:
                norm_device = "desconocido"
            self.data["dispositivo_tipo"] = norm_device

        return self


class SubmissionReceiptOut(BaseModel):
    id: int = Field(..., description="Identificador único del registro en la base de datos")
    fecha_registro: datetime = Field(..., description="Marca temporal del registro")
    idempotent_replay: bool = Field(
        default=False,
        description="Indica si la respuesta fue recuperada de un envío idéntico previo",
    )
    mensaje: str = Field(..., description="Mensaje explicativo para el usuario o encuestador")
