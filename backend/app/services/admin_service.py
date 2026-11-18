import csv
import io
import json
import uuid
from collections.abc import AsyncIterator
from typing import Any, Dict, List

from backend.app.domain.exceptions import DuplicateSlugError, SurveyNotFoundError
from backend.app.domain.interfaces.unit_of_work import AbstractUnitOfWork
from backend.app.schemas.encuesta import (
    EncuestaCreate,
    EncuestaListItem,
    EncuestaOut,
    EncuestaUpdate,
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
