import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, Optional

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base
from backend.app.models.encuesta import GUID, UniversalJSON

if TYPE_CHECKING:
    from backend.app.models.comunidad import ComunidadCatalogo
    from backend.app.models.encuesta import Encuesta


class RespuestaCiudadana(Base):
    __tablename__ = "respuestas_ciudadanas"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    encuesta_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("encuestas.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    client_submission_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        unique=True,
        nullable=True,
        index=True,
    )
    cedula: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    parroquia: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    comunidad_codigo: Mapped[Optional[str]] = mapped_column(
        String(20),
        ForeignKey("catalogo_comunidades.codigo", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    zona_od: Mapped[Optional[str]] = mapped_column(String(30), nullable=True, index=True)
    datos: Mapped[Dict[str, Any]] = mapped_column(UniversalJSON(), nullable=False)
    fecha_registro: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
    )

    encuesta: Mapped["Encuesta"] = relationship("Encuesta", back_populates="respuestas")
    comunidad_rel: Mapped[Optional["ComunidadCatalogo"]] = relationship("ComunidadCatalogo")

    __table_args__ = (
        UniqueConstraint("encuesta_id", "cedula", name="uq_voto_ciudadano"),
    )
