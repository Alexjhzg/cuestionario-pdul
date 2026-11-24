import csv
import io
import json
import math
import uuid
from collections.abc import AsyncIterator
from typing import Any, Dict, List, Optional

from backend.app.domain.exceptions import (
    DuplicateSlugError,
    SubmissionNotFoundError,
    SurveyNotFoundError,
)
from backend.app.domain.interfaces.unit_of_work import AbstractUnitOfWork
from backend.app.schemas.encuesta import (
    EncuestaCreate,
    EncuestaListItem,
    EncuestaOut,
    EncuestaUpdate,
)
from backend.app.schemas.field_map import (
    CalidadUbicacion,
    FieldMapPointOut,
    FieldMapSummaryOut,
)
from backend.app.services.normalizers import sanitize_pii


class AdminService:
    """Servicio de aplicación para gestión administrativa de encuestas y exportaciones."""

    def __init__(self, uow: AbstractUnitOfWork) -> None:
        self.uow = uow

    async def _require_survey(self, encuesta_id: uuid.UUID) -> Any:
        enc = await self.uow.surveys.get_by_id(encuesta_id)
        if not enc:
            raise SurveyNotFoundError(
                str(encuesta_id),
                f"Encuesta '{encuesta_id}' no encontrada.",
            )
        return enc

    async def list_surveys(self) -> List[EncuestaListItem]:
        rows = await self.uow.surveys.list_all()
        return [
            EncuestaListItem(
                id=enc.id,
                titulo=enc.titulo,
                slug=enc.slug,
                tipo_instrumento=enc.tipo_instrumento,
                activa=enc.activa,
                creado_en=enc.creado_en,
                total_respuestas=count,
            )
            for enc, count in rows
        ]

    async def get_survey(self, encuesta_id: uuid.UUID) -> EncuestaOut:
        enc = await self._require_survey(encuesta_id)
        return EncuestaOut.model_validate(enc)

    async def create_survey(self, encuesta_in: EncuestaCreate) -> EncuestaOut:
        existing = await self.uow.surveys.get_by_slug(encuesta_in.slug)
        if existing:
            raise DuplicateSlugError(encuesta_in.slug)

        enc = await self.uow.surveys.create(encuesta_in)
        await self.uow.commit()
        return EncuestaOut.model_validate(enc)

    async def update_survey(
        self, encuesta_id: uuid.UUID, encuesta_update: EncuestaUpdate
    ) -> EncuestaOut:
        enc = await self._require_survey(encuesta_id)
        update_data = encuesta_update.model_dump(exclude_unset=True)
        updated = await self.uow.surveys.update(enc, update_data)
        await self.uow.commit()
        return EncuestaOut.model_validate(updated)

    async def toggle_status(
        self, encuesta_id: uuid.UUID, activa: bool
    ) -> EncuestaOut:
        enc = await self.uow.surveys.update_status(encuesta_id, activa)
        if not enc:
            raise SurveyNotFoundError(
                str(encuesta_id),
                f"Encuesta '{encuesta_id}' no encontrada.",
            )
        await self.uow.commit()
        return EncuestaOut.model_validate(enc)

    async def list_submissions(
        self, encuesta_id: uuid.UUID, skip: int = 0, limit: int = 50
    ) -> Dict[str, Any]:
        await self._require_survey(encuesta_id)

        total = await self.uow.submissions.count_submissions(encuesta_id)
        subs = await self.uow.submissions.list_submissions(
            encuesta_id, skip=skip, limit=limit
        )

        items = [
            {
                "id": s.id,
                "encuesta_id": str(s.encuesta_id),
                "client_submission_id": (
                    str(s.client_submission_id) if s.client_submission_id else None
                ),
                "parroquia": s.parroquia,
                "zona_od": s.zona_od,
                "fecha_registro": (
                    s.fecha_registro.isoformat() if s.fecha_registro else None
                ),
                "datos": s.datos,
            }
            for s in subs
        ]

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "items": items,
        }

    async def get_submission_detail(
        self, encuesta_id: uuid.UUID, respuesta_id: int
    ) -> Dict[str, Any]:
        await self._require_survey(encuesta_id)
        sub = await self.uow.submissions.get_submission_by_id(
            encuesta_id, respuesta_id
        )
        if not sub:
            raise SubmissionNotFoundError(str(respuesta_id))

        return {
            "id": sub.id,
            "encuesta_id": str(sub.encuesta_id),
            "client_submission_id": (
                str(sub.client_submission_id) if sub.client_submission_id else None
            ),
            "parroquia": sub.parroquia,
            "zona_od": sub.zona_od,
            "fecha_registro": (
                sub.fecha_registro.isoformat() if sub.fecha_registro else None
            ),
            "datos": sub.datos,
        }

    @staticmethod
    def _parse_finite_float(raw: Any) -> Optional[float]:
        if raw in (None, "") or isinstance(raw, bool):
            return None
        try:
            val = float(raw)
        except (TypeError, ValueError):
            return None
        return val if math.isfinite(val) else None

    @staticmethod
    def _classify_gps_quality(
        lat: float, lng: float, precision_m: Optional[float]
    ) -> tuple[CalidadUbicacion, Optional[str]]:
        in_monagas_bbox = (8.3 <= lat <= 10.6) and (-64.2 <= lng <= -62.0)
        if not in_monagas_bbox:
            return (
                "alerta",
                "Coordenada fuera del ámbito geográfico de Maturín / Monagas",
            )
        if precision_m is not None and precision_m > 500:
            return (
                "alerta",
                f"Baja precisión (±{round(precision_m)} m, posible ubicación por red/IP)",
            )
        if precision_m is None or precision_m > 100:
            return ("media", None)
        return ("alta", None)

    async def get_field_map_summary(
        self, encuesta_id: uuid.UUID
    ) -> FieldMapSummaryOut:
        await self._require_survey(encuesta_id)
        rows = await self.uow.submissions.list_field_map_rows(encuesta_id)
        total_respuestas = len(rows)
        puntos: List[FieldMapPointOut] = []
        total_alertas = 0

        for row in rows:
            row_id, parroquia, zona_od_col, fecha_registro, datos = row
            datos_dict = datos if isinstance(datos, dict) else {}

            lat = self._parse_finite_float(datos_dict.get("gps_latitud"))
            lng = self._parse_finite_float(datos_dict.get("gps_longitud"))
            if lat is None or lng is None or not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                continue

            precision_raw = self._parse_finite_float(datos_dict.get("gps_precision"))
            precision_m = precision_raw if (precision_raw is not None and precision_raw >= 0) else None

            calidad, motivo_alerta = self._classify_gps_quality(lat, lng, precision_m)
            if calidad == "alerta":
                total_alertas += 1

            comunidad = str(datos_dict.get("comunidad_sector") or "").strip() or None
            zona_od_val = (
                str(zona_od_col or datos_dict.get("zona_residencia_od") or "").strip()
                or None
            )
            dispositivo = (
                str(datos_dict.get("dispositivo_tipo") or "desconocido").strip().lower()
                or "desconocido"
            )

            puntos.append(
                FieldMapPointOut(
                    id=int(row_id),
                    latitud=lat,
                    longitud=lng,
                    precision_m=precision_m,
                    parroquia=str(parroquia or ""),
                    comunidad_sector=comunidad,
                    zona_od=zona_od_val,
                    dispositivo_tipo=dispositivo,
                    fecha_registro=fecha_registro,
                    calidad_ubicacion=calidad,
                    motivo_alerta=motivo_alerta,
                )
            )

        total_con_gps = len(puntos)
        total_sin_gps = max(0, total_respuestas - total_con_gps)
        porcentaje_cobertura = (
            round((total_con_gps / total_respuestas) * 100, 1)
            if total_respuestas > 0
            else 0.0
        )

        return FieldMapSummaryOut(
            encuesta_id=encuesta_id,
            total_respuestas=total_respuestas,
            total_con_gps=total_con_gps,
            total_sin_gps=total_sin_gps,
            porcentaje_cobertura_gps=porcentaje_cobertura,
            total_alertas_ubicacion=total_alertas,
            puntos=puntos,
        )

    @staticmethod
    def _format_export_row(s: Any, redact_pii: bool) -> Dict[str, Any]:
        datos_export = sanitize_pii(s.datos) if redact_pii else dict(s.datos)
        row: Dict[str, Any] = {
            "id": s.id,
            "encuesta_id": str(s.encuesta_id),
            "parroquia": s.parroquia,
            "zona_od": s.zona_od,
            "fecha_registro": (
                s.fecha_registro.isoformat() if s.fecha_registro else None
            ),
        }
        if not redact_pii and s.cedula:
            row["cedula"] = s.cedula
        row["datos"] = datos_export
        return row

    @staticmethod
    def _format_csv_line(values: List[str]) -> str:
        buf = io.StringIO()
        csv.writer(buf).writerow(values)
        return buf.getvalue()

    async def stream_export_submissions(
        self,
        encuesta_id: uuid.UUID,
        formato: str = "json",
        redact_pii: bool = False,
        batch_size: int = 200,
    ) -> AsyncIterator[str]:
        """Generador asíncrono que transmite respuestas en fragmentos CSV o JSON sin cargar todo en RAM."""
        fmt = formato.lower()
        if fmt == "csv":
            headers = ["id", "parroquia", "zona_od", "fecha_registro"]
            if not redact_pii:
                headers.append("cedula")
            headers.append("datos_json")
            yield self._format_csv_line(headers)

            offset = 0
            while True:
                batch = await self.uow.submissions.list_submissions(
                    encuesta_id, skip=offset, limit=batch_size
                )
                if not batch:
                    break
                for s in batch:
                    item = self._format_export_row(s, redact_pii)
                    row_vals = [
                        str(item["id"]),
                        item.get("parroquia", ""),
                        item.get("zona_od", "") or "",
                        item.get("fecha_registro", "") or "",
                    ]
                    if not redact_pii:
                        row_vals.append(item.get("cedula", "") or "")
                    row_vals.append(
                        json.dumps(item.get("datos", {}), ensure_ascii=False)
                    )
                    yield self._format_csv_line(row_vals)
                if len(batch) < batch_size:
                    break
                offset += batch_size
            return

        # Formato JSON por streaming incremental
        yield "["
        first = True
        offset = 0
        while True:
            batch = await self.uow.submissions.list_submissions(
                encuesta_id, skip=offset, limit=batch_size
            )
            if not batch:
                break
            for s in batch:
                item = self._format_export_row(s, redact_pii)
                prefix = "" if first else ","
                first = False
                yield f"{prefix}{json.dumps(item, ensure_ascii=False)}"
            if len(batch) < batch_size:
                break
            offset += batch_size
        yield "]"

    async def export_submissions(
        self,
        encuesta_id: uuid.UUID,
        formato: str = "json",
        redact_pii: bool = False,
    ) -> Any:
        await self._require_survey(encuesta_id)

        total = await self.uow.submissions.count_submissions(encuesta_id)
        subs = await self.uow.submissions.list_submissions(
            encuesta_id, skip=0, limit=total or 100000
        )

        cleaned_list: List[Dict[str, Any]] = [
            self._format_export_row(s, redact_pii) for s in subs
        ]

        if formato.lower() == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            headers = ["id", "parroquia", "zona_od", "fecha_registro"]
            if not redact_pii:
                headers.append("cedula")
            headers.append("datos_json")
            writer.writerow(headers)

            for item in cleaned_list:
                row_vals = [
                    str(item["id"]),
                    item.get("parroquia", ""),
                    item.get("zona_od", "") or "",
                    item.get("fecha_registro", ""),
                ]
                if not redact_pii:
                    row_vals.append(item.get("cedula", "") or "")
                row_vals.append(json.dumps(item.get("datos", {}), ensure_ascii=False))
                writer.writerow(row_vals)

            return output.getvalue()

        return cleaned_list
