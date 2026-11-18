import { PARROQUIA_NOMBRES } from '@/utils/validation';

export interface ResponseResidentRecord {
  persona_numero?: number;
  nombres?: string;
  nombre_apellido?: string;
  parentesco?: string | number;
  sexo?: string | number;
  edad?: number | string;
  nivel_educativo?: string | number;
  actividad_principal?: string | number;
  ocupacion_principal?: string | number;
  medio_transporte_habitual?: string | number;
  [key: string]: unknown;
}

export interface ResponseTripRecord {
  viaje_numero?: number;
  modo_principal?: string | number;
  zona_od_origen?: string | null;
  zona_od_destino?: string | null;
  motivo_viaje?: string | number;
  proposito_viaje?: string | number;
  hora_salida?: string;
  hora_llegada?: string;
  tiempo_viaje_min?: number | string;
  costo_viaje_bs?: number | string | null;
  [key: string]: unknown;
}

export interface ResponseDisplayData {
  parroquia?: string | null;
  comunidad_sector?: string;
  zona_residencia_od?: string;
  avenida_calle?: string;
  casa_apartamento?: string;
  cedula?: string;
  tipo_vivienda?: string;
  tenencia_vivienda?: string;
  total_cuartos_vivienda?: number | string;
  cuartos_dormir_hogar?: number | string;
  numero_personas_hogar?: number | string;
  grupos_gastos_separados?: number | string;
  residentes?: ResponseResidentRecord[];
  viajes?: ResponseTripRecord[];
  calificacion_servicio_tp?: string;
  principal_dificultad_tp?: string;
  dificultades_acceso_tp?: string;
  tiempo_espera_paradas_min?: number | string;
  km_residencia_parada?: number | string;
  rutas_tp_dia?: number | string;
  gasto_semanal_transporte_bs?: number | string;
  acuerdo_rutas_directas?: string;
  seguridad_centro?: string;
  seguridad_desplazamiento_centro?: string;
  acuerdo_acera_comoda?: string;
  aceras_adecuadas?: string;
  dias_camina_bici_semana?: number | string;
  frecuencia_visita_parques?: string;
  limpieza_parques?: string;
  calificacion_limpieza_parques?: string;
  disposicion_participar?: string;
  disposicion_participar_mejoras?: string;
  observaciones_generales?: string;
  [key: string]: unknown;
}

export const TIPOS_VIVIENDA_LABELS: Record<string, string> = {
  quinta_casa_quinta: 'Quinta o Casa quinta',
  casa: 'Casa',
  apartamento_edificio: 'Apartamento en edificio',
  apartamento_quinta_casa: 'Apartamento en quinta o casa',
  casa_vecindad: 'Casa de vecindad',
  vivienda_rustica: 'Vivienda rústica (rancho)',
  otro: 'Otro tipo'
};

export const TENENCIA_VIVIENDA_LABELS: Record<string, string> = {
  propia_pagada: 'Propia pagada totalmente',
  propia_pagandose: 'Propia pagándose',
  alquilada: 'Alquilada',
  alquilada_parte: 'Alquilada parte de la vivienda',
  cedida_trabajo: 'Cedida por trabajo',
  cedida_familiar: 'Cedida por familiar o amigo',
  tomada_invadida: 'Tomada / Invadida',
  otra_forma: 'Otra forma'
};

export const PARENTESCO_LABELS: Record<string, string> = {
  '1': 'Jefe(a) de Hogar',
  '2': 'Cónyuge / Pareja',
  '3': 'Hijo(a) / Hijastro(a)',
  '4': 'Padre / Madre',
  '5': 'Hermano(a)',
  '6': 'Nieto(a)',
  '7': 'Otro familiar',
  '8': 'No familiar'
};

export const NIVEL_EDUCATIVO_LABELS: Record<string, string> = {
  '1': 'Ninguno',
  '2': 'Primaria',
  '3': 'Secundaria',
  '4': 'Universitario',
  '5': 'Postgrado',
  ninguno: 'Ninguno',
  primaria: 'Primaria',
  secundaria: 'Secundaria',
  tecnico: 'Técnico',
  universitario: 'Universitario',
  postgrado: 'Postgrado / Maestría',
  doctorado: 'Doctorado'
};

export const ACTIVIDAD_LABELS: Record<string, string> = {
  '1': 'Trabaja',
  '2': 'Estudia',
  '3': 'Oficios del hogar',
  '4': 'Jubilado / Pensionado',
  '5': 'Busca trabajo',
  '6': 'Otro',
  trabaja: 'Trabaja',
  estudia: 'Estudia',
  oficios_hogar: 'Oficios del hogar',
  jubilado: 'Jubilado / Pensionado',
  busca_trabajo: 'Busca trabajo',
  otro: 'Otro'
};

export const MODOS_TRANSPORTE_LABELS: Record<string, string> = {
  '1': 'A pie',
  '2': 'Bicicleta',
  '3': 'Motocicleta',
  '4': 'Automóvil Particular',
  '5': 'Taxi',
  '6': 'Transporte público (bus, buseta)',
  '7': 'Transporte informal (por puesto, mototaxi)',
  '8': 'Otro',
  '9': 'Transporte Institucional',
  a_pie: 'A pie',
  bicicleta: 'Bicicleta',
  motocicleta: 'Motocicleta',
  automovil: 'Automóvil Particular',
  institucional: 'Transporte Institucional',
  transporte_institucional: 'Transporte Institucional',
  taxi: 'Taxi',
  transporte_publico: 'Transporte público',
  otro: 'Otro'
};

export const MOTIVOS_VIAJE_LABELS: Record<string, string> = {
  '1': 'Trabajo',
  '2': 'Estudio',
  '3': 'Compras',
  '4': 'Salud',
  '5': 'Recreación',
  '6': 'Trámites',
  '7': 'Visita Familiar',
  '8': 'Otro',
  trabajo: 'Trabajo',
  estudio: 'Estudio',
  compras: 'Compras',
  salud: 'Salud',
  recreacion: 'Recreación',
  tramites: 'Trámites',
  visita_familiar: 'Visita Familiar',
  otro: 'Otro'
};

export const CALIFICACION_LABELS: Record<string, string> = {
  muy_bueno: 'Muy bueno',
  muy_buena: 'Muy buena',
  bueno: 'Bueno',
  buena: 'Buena',
  regular: 'Regular',
  malo: 'Malo',
  mala: 'Mala',
  muy_malo: 'Muy malo',
  muy_mala: 'Muy mala',
  muy_seguro: 'Muy seguro',
  seguro: 'Seguro',
  neutral: 'Neutral',
  inseguro: 'Inseguro',
  muy_inseguro: 'Muy inseguro',
  bastante_seguro: 'Bastante seguro',
  poco_seguro: 'Poco seguro',
  nada_seguro: 'Nada seguro'
};

export const ACUERDO_LABELS: Record<string, string> = {
  totalmente_de_acuerdo: 'Totalmente de acuerdo',
  de_acuerdo: 'De acuerdo',
  neutral: 'Neutral',
  en_desacuerdo: 'En desacuerdo',
  totalmente_en_desacuerdo: 'Totalmente en desacuerdo'
};

export const DIFICULTAD_TP_LABELS: Record<string, string> = {
  frecuencia_baja: 'Frecuencia baja de unidades',
  sobrecupo: 'Sobrecupo / Exceso de pasajeros',
  falta_de_rutas: 'Falta de rutas',
  inseguridad: 'Inseguridad en paradas o unidades',
  otro: 'Otro motivo'
};

export const FRECUENCIA_LABELS: Record<string, string> = {
  nunca: 'Nunca',
  ocasionalmente: 'Ocasionalmente',
  mensual: 'Mensual',
  semanal: 'Semanal',
  diario: 'Diario'
};

export function formatResponseDate(isoDate: string | null | undefined): string {
  if (!isoDate) return 'Fecha no registrada';
  try {
    const d = new Date(isoDate);
    if (isNaN(d.getTime())) return isoDate;
    return new Intl.DateTimeFormat('es-VE', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    }).format(d);
  } catch {
    return isoDate;
  }
}

export const formatFecha = formatResponseDate;

export function formatParroquia(key?: unknown): string {
  if (!key) return 'No especificada';
  const str = String(key);
  return PARROQUIA_NOMBRES[str.toLowerCase()] || str.replace(/_/g, ' ');
}

export function truncateUuid(uuid: string | null | undefined): string {
  if (!uuid) return '—';
  return uuid.slice(0, 8);
}

export function humanLabel(map: Readonly<Record<string, string>>, val: unknown): string {
  if (val === undefined || val === null || val === '') return '—';
  const raw = String(val);
  const lower = raw.toLowerCase();
  return map[lower] || map[raw] || raw.replace(/_/g, ' ');
}
