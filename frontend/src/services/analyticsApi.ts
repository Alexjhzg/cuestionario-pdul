/**
 * Servicio de API para Analítica Municipal, GIS y KPIs (Milestone 5)
 * Conexión tipada con los endpoints de analítica de FastAPI:
 * - GET /api/v1/encuestas
 * - GET /api/v1/encuestas/{id}/kpis
 * - GET /api/v1/encuestas/{id}/resultados-parroquia
 * - GET /api/v1/encuestas/{id}/reparto-modal
 * - GET /api/v1/encuestas/{id}/matriz-od
 * - GET /api/v1/encuestas/{id}/metricas?campo=...
 */

export const MATURIN_PARROQUIAS_OFICIALES = [
  'alto_de_los_godos',
  'boqueron',
  'las_cocuizas',
  'la_cruz',
  'san_simon',
  'santa_cruz',
  'el_corozo',
  'el_furrial',
  'jusepin',
  'la_pica',
  'san_vicente'
] as const;

export interface EncuestaItem {
  id: string;
  titulo: string;
  slug: string;
  tipo_instrumento: string;
  activa: boolean;
  creado_en?: string;
  total_respuestas?: number;
}

export interface ParroquiaResultado {
  parroquia: string;
  total_respuestas: number;
  porcentaje: number;
}

export interface RepartoModalItem {
  modo: string;
  etiqueta: string;
  total_viajes: number;
  porcentaje: number;
}

export interface MatrizODItem {
  zona_origen: string;
  zona_destino: string;
  total_viajes: number;
  tiempo_promedio_min: number | null;
  costo_promedio_bs: number | null;
}

export interface KpiMetrics {
  total_encuestas: number;
  total_viajes: number;
  total_residentes: number;
  parroquia_lider: string | null;
}

export interface EChartsSeriesData {
  campo: string;
  labels: string[];
  values: number[];
}

export interface PreguntaMetricaItem {
  seccion: string;
  clave: string;
  pregunta: string;
  tipo_grafico: 'donut' | 'bar';
  total_respuestas: number;
  labels: string[];
  values: number[];
}

export interface AnalyticsDataset {
  kpis: KpiMetrics;
  parroquias: ParroquiaResultado[];
  repartoModal: RepartoModalItem[];
  matrizOd: MatrizODItem[];
}

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export class AnalyticsApiError extends Error {
  status: number;
  detail?: string;

  constructor(status: number, message: string, detail?: string) {
    super(message);
    this.name = 'AnalyticsApiError';
    this.status = status;
    this.detail = detail;
  }
}

async function handleResponse<T>(res: Response, endpointDesc: string): Promise<T> {
  if (!res.ok) {
    let detail: string | undefined;
    try {
      const json = await res.json();
      detail = json?.detail || json?.message;
    } catch {
      // Ignorar si no es JSON válido
    }
    throw new AnalyticsApiError(
      res.status,
      `Error al consultar ${endpointDesc} (HTTP ${res.status}): ${detail || 'Error en servidor'}`,
      detail
    );
  }
  return res.json();
}

/**
 * Consulta el listado de encuestas disponibles para el selector del dashboard
 * GET /api/v1/encuestas
 */
export async function fetchEncuestas(): Promise<EncuestaItem[]> {
  try {
    const res = await fetch(`${BASE_URL}/encuestas`, {
      headers: { Accept: 'application/json' }
    });
    return await handleResponse<EncuestaItem[]>(res, 'listado de encuestas');
  } catch (err) {
    try {
      const resAdmin = await fetch(`${BASE_URL}/admin/encuestas`, {
        headers: { Accept: 'application/json' }
      });
      return await handleResponse<EncuestaItem[]>(resAdmin, 'listado de encuestas (admin)');
    } catch {
      throw err;
    }
  }
}

/**
 * Consulta indicadores ejecutivos agregados del levantamiento
 * GET /api/v1/encuestas/{id}/kpis
 */
export async function fetchKpis(encuestaId: string): Promise<KpiMetrics> {
  const res = await fetch(`${BASE_URL}/encuestas/${encuestaId}/kpis`, {
    headers: { Accept: 'application/json' }
  });
  return handleResponse<KpiMetrics>(res, 'KPIs ejecutivos');
}

/**
 * Consulta conteo y porcentaje de respuestas por cada parroquia
 * GET /api/v1/encuestas/{id}/resultados-parroquia
 */
export async function fetchResultadosParroquia(encuestaId: string): Promise<ParroquiaResultado[]> {
  const res = await fetch(`${BASE_URL}/encuestas/${encuestaId}/resultados-parroquia`, {
    headers: { Accept: 'application/json' }
  });
  return handleResponse<ParroquiaResultado[]>(res, 'resultados por parroquia');
}

/**
 * Consulta distribución modal de viajes (1..8)
 * GET /api/v1/encuestas/{id}/reparto-modal
 */
export async function fetchRepartoModal(encuestaId: string): Promise<RepartoModalItem[]> {
  const res = await fetch(`${BASE_URL}/encuestas/${encuestaId}/reparto-modal`, {
    headers: { Accept: 'application/json' }
  });
  return handleResponse<RepartoModalItem[]>(res, 'reparto modal');
}

/**
 * Consulta matriz de pares de flujo Origen - Destino
 * GET /api/v1/encuestas/{id}/matriz-od
 */
export async function fetchMatrizOD(encuestaId: string): Promise<MatrizODItem[]> {
  const res = await fetch(`${BASE_URL}/encuestas/${encuestaId}/matriz-od`, {
    headers: { Accept: 'application/json' }
  });
  return handleResponse<MatrizODItem[]>(res, 'matriz Origen-Destino');
}

/**
 * Consulta frecuencias genéricas de un campo específico para ECharts
 * GET /api/v1/encuestas/{id}/metricas?campo=...
 */
export async function fetchMetricasCampo(
  encuestaId: string,
  campo: string
): Promise<EChartsSeriesData> {
  const res = await fetch(
    `${BASE_URL}/encuestas/${encuestaId}/metricas?campo=${encodeURIComponent(campo)}`,
    {
      headers: { Accept: 'application/json' }
    }
  );
  return handleResponse<EChartsSeriesData>(res, `métricas del campo ${campo}`);
}

/**
 * Consulta métricas agregadas pregunta por pregunta para el dashboard
 * GET /api/v1/encuestas/{id}/preguntas-metricas
 */
export async function fetchPreguntasMetricas(encuestaId: string): Promise<PreguntaMetricaItem[]> {
  const res = await fetch(`${BASE_URL}/encuestas/${encuestaId}/preguntas-metricas`, {
    headers: { Accept: 'application/json' }
  });
  return handleResponse<PreguntaMetricaItem[]>(res, 'métricas de todas las preguntas');
}

/**
 * Genera un conjunto canónico de datos de respaldo (fallback) con las 11 parroquias oficiales
 */
export function getFallbackDataset(): AnalyticsDataset {
  return {
    kpis: {
      total_encuestas: 0,
      total_viajes: 0,
      total_residentes: 0,
      parroquia_lider: null
    },
    parroquias: MATURIN_PARROQUIAS_OFICIALES.map((p) => ({
      parroquia: p,
      total_respuestas: 0,
      porcentaje: 0
    })),
    repartoModal: [],
    matrizOd: []
  };
}

/**
 * Consulta en paralelo todo el paquete analítico para el dashboard municipal
 * Permite activar fallback de datos ante fallos de red.
 */
export async function fetchAllAnalytics(
  encuestaId: string,
  options?: { fallbackOnError?: boolean }
): Promise<AnalyticsDataset> {
  try {
    const [kpis, parroquias, repartoModal, matrizOd] = await Promise.all([
      fetchKpis(encuestaId),
      fetchResultadosParroquia(encuestaId),
      fetchRepartoModal(encuestaId),
      fetchMatrizOD(encuestaId)
    ]);

    return {
      kpis,
      parroquias,
      repartoModal,
      matrizOd
    };
  } catch (err) {
    if (options?.fallbackOnError) {
      return getFallbackDataset();
    }
    throw err;
  }
}
