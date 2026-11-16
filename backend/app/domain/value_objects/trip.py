from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Trip:
    """Objeto de valor inmutable que representa un viaje Origen-Destino."""

    zona_od_origen: str
    zona_od_destino: str
    modo_principal: str
    motivo_viaje: Optional[str] = None
    tiempo_viaje_min: Optional[float] = None
    costo_viaje_bs: Optional[float] = None

    def __post_init__(self) -> None:
        if not self.zona_od_origen or not self.zona_od_origen.strip():
            raise ValueError("La zona OD de origen es requerida.")
        if not self.zona_od_destino or not self.zona_od_destino.strip():
            raise ValueError("La zona OD de destino es requerida.")
        if not self.modo_principal or not self.modo_principal.strip():
            raise ValueError("El modo principal de transporte es requerido.")
        if self.tiempo_viaje_min is not None and self.tiempo_viaje_min <= 0:
            raise ValueError("El tiempo de viaje debe ser mayor a 0 minutos.")
        if self.costo_viaje_bs is not None and self.costo_viaje_bs < 0:
            raise ValueError("El costo del viaje no puede ser negativo.")
