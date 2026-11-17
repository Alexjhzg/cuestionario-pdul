/**
 * Cliente API REST para la comunicación con FastAPI del Cuestionario PDUL
 */

export interface EncuestaPublica {
  id: string;
  titulo: string;
  slug: string;
  activa: boolean;
  tipo_instrumento?: string;
  esquema_formio?: Record<string, unknown>;
}

export interface RespuestaSubmissionPayload {
  client_submission_id: string;
  data: Record<string, unknown>;
}

export interface RespuestaSubmissionResponse {
  id: number;
  fecha_registro: string;
  idempotent_replay: boolean;
  mensaje: string;
}

export interface ProblemDetail {
  code?: string;
  title: string;
  status: number;
  detail: string;
  errors?: Array<{ loc: string[]; msg: string; type: string }>;
}

// --- Modelos Administrativos ---

export interface EncuestaAdminItem {
  id: string;
  titulo: string;
  slug: string;
  tipo_instrumento: string;
  activa: boolean;
  creado_en: string;
  total_respuestas: number;
}

export interface EncuestaCreatePayload {
  titulo: string;
  slug: string;
  tipo_instrumento?: string;
  activa?: boolean;
  esquema_formio: Record<string, unknown>;
}

export interface EncuestaUpdatePayload {
  titulo?: string;
  tipo_instrumento?: string;
  esquema_formio?: Record<string, unknown>;
  activa?: boolean;
}

export interface EncuestaEstadoUpdatePayload {
  activa: boolean;
}

export interface EncuestaOut {
  id: string;
  titulo: string;
  slug: string;
  tipo_instrumento: string;
  activa: boolean;
  esquema_formio: Record<string, unknown>;
  creado_en: string;
}

export interface AdminRespuestaItem {
  id: number;
  encuesta_id: string;
  client_submission_id: string | null;
  parroquia: string;
  zona_od: string | null;
  fecha_registro: string | null;
  datos: Record<string, unknown>;
}

export interface AdminRespuestasResponse {
  total: number;
  skip: number;
  limit: number;
  items: AdminRespuestaItem[];
}

const resolveBaseUrl = (): string => {
  const raw = import.meta.env.VITE_API_BASE_URL;
  if (!raw) return '/api/v1';
  const trimmed = raw.replace(/\/+$/, '');
  return trimmed.endsWith('/api/v1') ? trimmed : `${trimmed}/api/v1`;
};

const BASE_URL = resolveBaseUrl();

export class ApiError extends Error {
  status: number;
  problem?: ProblemDetail;

  constructor(status: number, message: string, problem?: ProblemDetail) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.problem = problem;
  }
}

// --- Endpoints Públicos ---

export async function fetchEncuesta(slug: string): Promise<EncuestaPublica> {
  const response = await fetch(`${BASE_URL}/encuestas/${slug}`, {
    headers: {
      Accept: 'application/json'
    }
  });

  if (!response.ok) {
    let problem: ProblemDetail | undefined;
    try {
      problem = await response.json();
    } catch {
      // Ignorar si no es json
    }
    throw new ApiError(
      response.status,
      problem?.detail || `Error al obtener la encuesta (${response.status})`,
      problem
    );
  }

  return response.json();
}

export async function submitRespuesta(
  encuestaId: string,
  payload: RespuestaSubmissionPayload
): Promise<RespuestaSubmissionResponse> {
  const response = await fetch(`${BASE_URL}/encuestas/${encuestaId}/respuestas`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json'
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    let problem: ProblemDetail | undefined;
    try {
      problem = await response.json();
    } catch {
      // Ignorar si no es json
    }
    throw new ApiError(
      response.status,
      problem?.detail || `Error al enviar la respuesta (${response.status})`,
      problem
    );
  }

  return response.json();
}

// --- Endpoints Administrativos ---

/**
 * Obtiene el listado completo de encuestas para el panel de administración
 */
export async function fetchAdminEncuestas(): Promise<EncuestaAdminItem[]> {
  const response = await fetch(`${BASE_URL}/admin/encuestas`, {
    headers: {
      Accept: 'application/json'
    }
  });

  if (!response.ok) {
    let problem: ProblemDetail | undefined;
    try {
      problem = await response.json();
    } catch {
      // Ignorar si no es json
    }
    throw new ApiError(
      response.status,
      problem?.detail || `Error al obtener la lista de encuestas (${response.status})`,
      problem
    );
  }

  return response.json();
}

/**
 * Obtiene el detalle completo de una encuesta por su ID
 */
export async function fetchAdminEncuesta(encuestaId: string): Promise<EncuestaOut> {
  const response = await fetch(`${BASE_URL}/admin/encuestas/${encuestaId}`, {
    headers: {
      Accept: 'application/json'
    }
  });

  if (!response.ok) {
    let problem: ProblemDetail | undefined;
    try {
      problem = await response.json();
    } catch {
      // Ignorar si no es json
    }
    throw new ApiError(
      response.status,
      problem?.detail || `Error al obtener el detalle de la encuesta (${response.status})`,
      problem
    );
  }

  return response.json();
}

/**
 * Crea una nueva encuesta en el sistema
 */
export async function createAdminEncuesta(
  payload: EncuestaCreatePayload
): Promise<EncuestaOut> {
  const response = await fetch(`${BASE_URL}/admin/encuestas`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json'
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    let problem: ProblemDetail | undefined;
    try {
      problem = await response.json();
    } catch {
      // Ignorar si no es json
    }
    throw new ApiError(
      response.status,
      problem?.detail || `Error al crear la encuesta (${response.status})`,
      problem
    );
  }

  return response.json();
}

/**
 * Actualiza los metadatos o esquema de una encuesta existente
 */
export async function updateAdminEncuesta(
  encuestaId: string,
  payload: EncuestaUpdatePayload
): Promise<EncuestaOut> {
  const response = await fetch(`${BASE_URL}/admin/encuestas/${encuestaId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json'
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    let problem: ProblemDetail | undefined;
    try {
      problem = await response.json();
    } catch {
      // Ignorar si no es json
    }
    throw new ApiError(
      response.status,
      problem?.detail || `Error al actualizar la encuesta (${response.status})`,
      problem
    );
  }

  return response.json();
}

/**
 * Alterna el estado activa/inactiva de una encuesta
 */
export async function updateEncuestaEstado(
  encuestaId: string,
  activa: boolean
): Promise<EncuestaOut> {
  const response = await fetch(`${BASE_URL}/admin/encuestas/${encuestaId}/estado`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json'
    },
    body: JSON.stringify({ activa })
  });

  if (!response.ok) {
    let problem: ProblemDetail | undefined;
    try {
      problem = await response.json();
    } catch {
      // Ignorar si no es json
    }
    throw new ApiError(
      response.status,
      problem?.detail || `Error al actualizar el estado de la encuesta (${response.status})`,
      problem
    );
  }

  return response.json();
}

// Alias para compatibilidad de nomenclatura
export const toggleAdminEncuestaEstado = updateEncuestaEstado;

/**
 * Obtiene la lista paginada de respuestas ciudadanas recibidas para una encuesta
 */
export async function fetchAdminRespuestas(
  encuestaId: string,
  skip = 0,
  limit = 50
): Promise<AdminRespuestasResponse> {
  const response = await fetch(
    `${BASE_URL}/admin/encuestas/${encuestaId}/respuestas?skip=${skip}&limit=${limit}`,
    {
      headers: {
        Accept: 'application/json'
      }
    }
  );

  if (!response.ok) {
    let problem: ProblemDetail | undefined;
    try {
      problem = await response.json();
    } catch {
      // Ignorar si no es json
    }
    throw new ApiError(
      response.status,
      problem?.detail || `Error al obtener las respuestas (${response.status})`,
      problem
    );
  }

  return response.json();
}

/**
 * Descarga las respuestas en formato CSV o JSON como Blob y dispara la descarga en el navegador
 */
export async function exportarRespuestasAdmin(
  encuestaId: string,
  formato: 'csv' | 'json' = 'json',
  redactPii = false
): Promise<Blob> {
  const response = await fetch(
    `${BASE_URL}/admin/encuestas/${encuestaId}/exportar?formato=${formato}&redact_pii=${redactPii}`,
    {
      headers: {
        Accept: formato === 'csv' ? 'text/csv' : 'application/json'
      }
    }
  );

  if (!response.ok) {
    let problem: ProblemDetail | undefined;
    try {
      problem = await response.json();
    } catch {
      // Ignorar si no es json
    }
    throw new ApiError(
      response.status,
      problem?.detail || `Error al exportar respuestas (${response.status})`,
      problem
    );
  }

  const blob = await response.blob();
  return blob;
}

/**
 * Dispara la descarga de un Blob en el navegador con un nombre de archivo específico
 */
export function triggerBlobDownload(blob: Blob, filename: string): void {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.style.display = 'none';
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => {
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  }, 100);
}

export const descargarBlob = triggerBlobDownload;

