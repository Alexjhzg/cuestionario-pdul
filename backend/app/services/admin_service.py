import csv
import io
import json
import uuid
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status

from backend.app.models.encuesta import Encuesta
from backend.app.repositories.encuesta_repo import EncuestaRepository
from backend.app.repositories.survey_repo import SurveyRepository
from backend.app.schemas.encuesta import (
    EncuestaCreate,
    EncuestaListItem,
    EncuestaOut,
    EncuestaUpdate,
)
from backend.app.services.normalizers import sanitize_pii


class AdminService:
    def __init__(
        self,
        encuesta_repo: EncuestaRepository,
        survey_repo: SurveyRepository,
    ) -> None:
        self.encuesta_repo = encuesta_repo
        self.survey_repo = survey_repo

    async def list_surveys(self) -> List[EncuestaListItem]:
        rows = await self.encuesta_repo.list_all()
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
        enc = await self.encuesta_repo.get_by_id(encuesta_id)
        if not enc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Encuesta '{encuesta_id}' no encontrada.",
            )
        return EncuestaOut.model_validate(enc)

    async def create_survey(self, encuesta_in: EncuestaCreate) -> EncuestaOut:
        # Verificar si slug ya existe
        existing = await self.encuesta_repo.get_by_slug(encuesta_in.slug)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe una encuesta registrada con el slug '{encuesta_in.slug}'.",
            )

        enc = await self.encuesta_repo.create(encuesta_in)
        await self.encuesta_repo.session.commit()
        await self.encuesta_repo.session.refresh(enc)
        return EncuestaOut.model_validate(enc)

    async def update_survey(
        self, encuesta_id: uuid.UUID, encuesta_update: EncuestaUpdate
    ) -> EncuestaOut:
        enc = await self.encuesta_repo.get_by_id(encuesta_id)
        if not enc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Encuesta '{encuesta_id}' no encontrada.",
            )

        update_data = encuesta_update.model_dump(exclude_unset=True)
        updated = await self.encuesta_repo.update(enc, update_data)
        await self.encuesta_repo.session.commit()
        await self.encuesta_repo.session.refresh(updated)
        return EncuestaOut.model_validate(updated)

    async def toggle_status(
        self, encuesta_id: uuid.UUID, activa: bool
    ) -> EncuestaOut:
        enc = await self.encuesta_repo.update_status(encuesta_id, activa)
        if not enc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Encuesta '{encuesta_id}' no encontrada.",
            )
        await self.encuesta_repo.session.commit()
        await self.encuesta_repo.session.refresh(enc)
        return EncuestaOut.model_validate(enc)

    async def list_submissions(
        self, encuesta_id: uuid.UUID, skip: int = 0, limit: int = 50
    ) -> Dict[str, Any]:
        enc = await self.encuesta_repo.get_by_id(encuesta_id)
        if not enc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Encuesta '{encuesta_id}' no encontrada.",
            )

        total = await self.survey_repo.count_submissions(encuesta_id)
        subs = await self.survey_repo.list_submissions(encuesta_id, skip=skip, limit=limit)

        items = []
        for s in subs:
            items.append({
                "id": s.id,
                "encuesta_id": str(s.encuesta_id),
                "client_submission_id": str(s.client_submission_id) if s.client_submission_id else None,
                "parroquia": s.parroquia,
                "zona_od": s.zona_od,
                "fecha_registro": s.fecha_registro.isoformat() if s.fecha_registro else None,
                "datos": s.datos,
            })

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "items": items,
        }

    async def export_submissions(
        self,
        encuesta_id: uuid.UUID,
        formato: str = "json",
        redact_pii: bool = False,
    ) -> Any:
        enc = await self.encuesta_repo.get_by_id(encuesta_id)
        if not enc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Encuesta '{encuesta_id}' no encontrada.",
            )

        # Cargar todos los registros para exportación
        total = await self.survey_repo.count_submissions(encuesta_id)
        subs = await self.survey_repo.list_submissions(encuesta_id, skip=0, limit=total or 100000)

        cleaned_list: List[Dict[str, Any]] = []
        for s in subs:
            datos_export = sanitize_pii(s.datos) if redact_pii else dict(s.datos)
            row = {
                "id": s.id,
                "encuesta_id": str(s.encuesta_id),
                "parroquia": s.parroquia,
                "zona_od": s.zona_od,
                "fecha_registro": s.fecha_registro.isoformat() if s.fecha_registro else None,
            }
            if not redact_pii and s.cedula:
                row["cedula"] = s.cedula

            row["datos"] = datos_export
            cleaned_list.append(row)

        if formato.lower() == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            # Cabecera básica tabular
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
