from typing import List, Optional
from pydantic import BaseModel, Field


class ParroquiaCountOut(BaseModel):
    """Conteo de respuestas agregadas por parroquia para mapas GIS coropléticos."""

    parroquia: str = Field(..., description="Código snake_case de la parroquia")
    total_respuestas: int = Field(..., description="Cantidad total de encuestas registradas")
    porcentaje: float = Field(..., description="Porcentaje relativo sobre el total de la encuesta")


class EChartsSeriesOut(BaseModel):
    """Estructura normalizada para alimentar gráficos de Apache ECharts."""

    campo: str = Field(..., description="Nombre del campo analizado")
    labels: List[str] = Field(..., description="Etiquetas de categorías o valores")
    values: List[int] = Field(..., description="Frecuencias o conteos de cada categoría")


class MatrizODRowOut(BaseModel):
    """Fila agregada de interacción entre pares de zonas Origen-Destino."""

    zona_origen: str = Field(..., description="Código de la zona origen")
    zona_destino: str = Field(..., description="Código de la zona destino")
    total_viajes: int = Field(..., description="Total de viajes entre origen y destino")
    tiempo_promedio_min: Optional[float] = Field(
        default=None, description="Tiempo promedio de viaje en minutos"
    )
    costo_promedio_bs: Optional[float] = Field(
        default=None, description="Costo monetario promedio del trayecto en Bolívares"
    )


class RepartoModalRowOut(BaseModel):
    """Frecuencia y proporción de viajes según el modo de transporte."""

    modo: str = Field(..., description="Código numérico o identificador del modo de transporte")
    etiqueta: str = Field(..., description="Etiqueta legible del modo de transporte")
    total_viajes: int = Field(..., description="Conteo de viajes en este modo")
    porcentaje: float = Field(..., description="Porcentaje respecto al total de viajes registrados")


class KpiMetricsOut(BaseModel):
    """Métricas ejecutivas de resumen del levantamiento para el dashboard municipal."""

    total_encuestas: int = Field(..., description="Total de encuestas válidas")
    total_viajes: int = Field(..., description="Total de viajes registrados en la grilla")
    total_residentes: int = Field(..., description="Total de residentes censados en los hogares")
    parroquia_lider: Optional[str] = Field(
        default=None, description="Parroquia con mayor número de participaciones"
    )


class PreguntaMetricaOut(BaseModel):
    """Métricas agregadas para una pregunta específica del cuestionario."""

    seccion: str = Field(..., description="Nombre de la sección del cuestionario")
    clave: str = Field(..., description="Identificador o clave de la pregunta")
    pregunta: str = Field(..., description="Texto exacto de la pregunta en el cuestionario")
    tipo_grafico: str = Field("bar", description="Tipo de gráfico recomendado ('donut' | 'bar')")
    total_respuestas: int = Field(0, description="Total de respuestas válidas para esta pregunta")
    labels: List[str] = Field(default_factory=list, description="Etiquetas legibles de las categorías")
    values: List[int] = Field(default_factory=list, description="Conteos de cada categoría")

