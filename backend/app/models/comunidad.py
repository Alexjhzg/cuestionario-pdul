from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.database import Base


class ComunidadCatalogo(Base):
    """Catálogo oficial de comunidades del Municipio Maturín (1608) para selección en cascada."""

    __tablename__ = "catalogo_comunidades"

    codigo: Mapped[str] = mapped_column(String(20), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    xpar: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    parroquia: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    municipio_codigo: Mapped[str] = mapped_column(String(10), nullable=False, default="1608")
    municipio: Mapped[str] = mapped_column(String(60), nullable=False, default="MATURIN")
