import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.domain.interfaces.survey_repository import AbstractSurveyRepository
from backend.app.models.encuesta import Encuesta
from backend.app.models.respuesta import RespuestaCiudadana

if TYPE_CHECKING:
    from backend.app.schemas.encuesta import EncuestaCreate


class EncuestaRepository(AbstractSurveyRepository):
    """Repositorio SQLAlchemy para instrumentos de encuesta."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, encuesta_id: uuid.UUID) -> Optional[Encuesta]:
        stmt = select(Encuesta).where(Encuesta.id == encuesta_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[Encuesta]:
        stmt = select(Encuesta).where(Encuesta.slug == slug)
        result = await self.session.execute(stmt)
        encuesta = result.scalar_one_or_none()
        if not encuesta:
            # Alias fallback between canonical and legacy survey slugs
            alias = None
            if slug == "cuestionario-od-maturin":
                alias = "pdul_origen_destino"
            elif slug == "pdul_origen_destino":
                alias = "cuestionario-od-maturin"
            if alias:
                stmt_alias = select(Encuesta).where(Encuesta.slug == alias)
                result_alias = await self.session.execute(stmt_alias)
                encuesta = result_alias.scalar_one_or_none()
        return encuesta

    async def list_all(self) -> List[Tuple[Encuesta, int]]:
        """Lista todas las encuestas junto con el conteo total de respuestas recibidas."""
        stmt = (
            select(Encuesta, func.count(RespuestaCiudadana.id).label("total_respuestas"))
            .outerjoin(RespuestaCiudadana, Encuesta.id == RespuestaCiudadana.encuesta_id)
            .group_by(Encuesta.id)
            .order_by(Encuesta.creado_en.desc())
        )
        result = await self.session.execute(stmt)
        return [(row[0], int(row[1])) for row in result.all()]

    async def create(self, encuesta_in: "EncuestaCreate") -> Encuesta:
        encuesta = Encuesta(
            titulo=encuesta_in.titulo,
            slug=encuesta_in.slug,
            tipo_instrumento=encuesta_in.tipo_instrumento,
            esquema_formio=encuesta_in.esquema_formio,
            activa=encuesta_in.activa,
        )
        self.session.add(encuesta)
        await self.session.flush()
        return encuesta

    async def update(self, encuesta: Encuesta, update_data: Dict[str, Any]) -> Encuesta:
        for key, value in update_data.items():
            if value is not None and hasattr(encuesta, key):
                setattr(encuesta, key, value)
        await self.session.flush()
        return encuesta

    async def update_status(self, encuesta_id: uuid.UUID, activa: bool) -> Optional[Encuesta]:
        encuesta = await self.get_by_id(encuesta_id)
        if not encuesta:
            return None
        encuesta.activa = activa
        await self.session.flush()
        return encuesta
