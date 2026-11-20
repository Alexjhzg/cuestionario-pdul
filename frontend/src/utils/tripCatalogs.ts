import motivosCatalog from '@shared/catalogs/motivos_viaje.json';
import modosCatalog from '@shared/catalogs/modos_transporte.json';
import type { CatalogOptionItem } from '@shared/types';
import type { Residente, ViajeOD } from '@/types/survey';

export type HoraPeriodo = 'AM' | 'PM';

export interface Hora12Input {
  hora: string;
  minuto: string;
  periodo: HoraPeriodo;
}

export interface TripFormValidationInput {
  draft: Partial<ViajeOD>;
  sugerenciaOrigen: string;
  horaSalidaH: string;
  horaLlegadaH: string;
}

export interface TripBuildInput {
  draft: Partial<ViajeOD>;
  sugerenciaOrigen: string;
  horaSalida: Hora12Input;
  horaLlegada: Hora12Input;
  viajeNumero: number;
}

export const MOTIVO_OPTIONS: readonly CatalogOptionItem[] = motivosCatalog as CatalogOptionItem[];
export const MODO_OPTIONS: readonly CatalogOptionItem[] = modosCatalog as CatalogOptionItem[];

export const MOTIVOS_VIAJE: Record<string, string> = Object.fromEntries(
  MOTIVO_OPTIONS.map((item) => [item.codigo, item.nombre])
);

export const MODOS_TRANSPORTE: Record<string, string> = Object.fromEntries(
  MODO_OPTIONS.map((item) => [item.codigo, item.nombre])
);

export const HORAS_12: readonly string[] = Array.from({ length: 12 }, (_, i) =>
  String(i + 1).padStart(2, '0')
);

export const MINUTOS_LIST: readonly string[] = [
  '00',
  '05',
  '10',
  '15',
  '20',
  '25',
  '30',
  '35',
  '40',
  '45',
  '50',
  '55'
];

export function isBlankValue(value: unknown): boolean {
  return value === undefined || value === null || (typeof value === 'string' && value.trim().length === 0);
}

export function getNombreResidente(residentes: readonly Residente[] | undefined, num: number): string {
  if (residentes && residentes.length > 0) {
    const r = residentes.find((item) => item.persona_numero === num);
    if (r) {
      return r.nombres || r.nombre_apellido || `Persona #${num}`;
    }
  }
  return `Persona #${num}`;
}

export function getHoraFormateada(hora: string, minuto: string, periodo: HoraPeriodo): string {
  const h = hora.trim();
  if (!h) return '';
  const m = (minuto || '00').padStart(2, '0');
  return `${h}:${m} ${periodo}`;
}

export function createEmptyTripDraft(
  zonaOrigen = '',
  personaNumero?: number,
  origenDireccion = ''
): Partial<ViajeOD> {
  return {
    persona_numero: personaNumero,
    origen_direccion: origenDireccion,
    zona_od_origen: zonaOrigen,
    destino_direccion: '',
    zona_od_destino: '',
    hora_salida: '',
    hora_llegada: '',
    motivo_viaje: '',
    motivo_viaje_otro: '',
    modo_principal: '',
    modo_principal_otro: '',
    modo_secundario: '',
    modo_secundario_otro: '',
    tiempo_viaje_min: undefined,
    costo_viaje_bs: undefined
  };
}

export function isVehiculoParticular(modo?: string | number): boolean {
  if (modo === undefined || modo === null) return false;
  const m = String(modo).toLowerCase().trim();
  return m === '4' || m === 'automovil' || m.includes('particular');
}

const COST_EXEMPT_MODE_CODES = new Set(['1', '2', '3', '4']);
const COST_EXEMPT_MODE_LABELS = new Set([
  'a pie',
  'a_pie',
  'caminata',
  'bicicleta',
  'motocicleta',
  'moto'
]);

export function isModoSinCosto(modo?: string | number): boolean {
  if (modo === undefined || modo === null) return false;
  if (isVehiculoParticular(modo)) return true;
  const m = String(modo).toLowerCase().trim();
  if (COST_EXEMPT_MODE_CODES.has(m)) return true;
  return COST_EXEMPT_MODE_LABELS.has(m);
}

export function validateNewTripForm(input: TripFormValidationInput): string | null {
  const { draft, sugerenciaOrigen, horaSalidaH, horaLlegadaH } = input;
  const origen = (draft.zona_od_origen || sugerenciaOrigen).trim();
  const destino = (draft.zona_od_destino || '').trim();
  const origenDireccion = (draft.origen_direccion || '').trim();
  const destinoDireccion = (draft.destino_direccion || '').trim();

  if (isBlankValue(draft.persona_numero) || Number(draft.persona_numero) < 1) {
    return 'Por favor seleccione la persona que realizó el viaje.';
  }
  if (!origenDireccion) {
    return 'Por favor indique la dirección o referencia de origen.';
  }
  if (!origen) {
    return 'Por favor indique la zona o parroquia de origen.';
  }
  if (!destinoDireccion) {
    return 'Por favor indique la dirección o referencia de destino.';
  }
  if (!destino) {
    return 'Por favor indique la zona o parroquia de destino.';
  }
  if (!horaSalidaH) {
    return 'Por favor indique la hora de salida.';
  }
  if (!horaLlegadaH) {
    return 'Por favor indique la hora de llegada.';
  }
  if (!draft.motivo_viaje) {
    return 'Por favor seleccione el motivo del viaje.';
  }
  if (draft.motivo_viaje === '8' && !String(draft.motivo_viaje_otro || '').trim()) {
    return 'Por favor especifique el otro motivo del viaje.';
  }
  if (!draft.modo_principal) {
    return 'Por favor seleccione el modo de transporte principal.';
  }
  if (draft.modo_principal === '8' && !String(draft.modo_principal_otro || '').trim()) {
    return 'Por favor especifique el otro modo de transporte principal.';
  }
  if (!isVehiculoParticular(draft.modo_principal)) {
    if (draft.modo_secundario === '8' && !String(draft.modo_secundario_otro || '').trim()) {
      return 'Por favor especifique el otro modo de transporte secundario.';
    }
  }
  if (
    isBlankValue(draft.tiempo_viaje_min) ||
    isNaN(Number(draft.tiempo_viaje_min)) ||
    Number(draft.tiempo_viaje_min) < 1
  ) {
    return 'Por favor indique el tiempo de viaje en minutos.';
  }
  if (!isModoSinCosto(draft.modo_principal)) {
    if (
      isBlankValue(draft.costo_viaje_bs) ||
      isNaN(Number(draft.costo_viaje_bs)) ||
      Number(draft.costo_viaje_bs) < 0
    ) {
      return 'Por favor indique el costo del viaje (puede ser 0).';
    }
  }

  return null;
}

export function buildTripFromDraft(input: TripBuildInput): ViajeOD {
  const { draft, sugerenciaOrigen, horaSalida, horaLlegada, viajeNumero } = input;
  const origen = (draft.zona_od_origen || sugerenciaOrigen).trim();
  const destino = (draft.zona_od_destino || '').trim();
  const origenDireccion = (draft.origen_direccion || '').trim();
  const destinoDireccion = (draft.destino_direccion || '').trim();

  const horaSalidaFinal = getHoraFormateada(horaSalida.hora, horaSalida.minuto, horaSalida.periodo);
  const horaLlegadaFinal = getHoraFormateada(horaLlegada.hora, horaLlegada.minuto, horaLlegada.periodo);
  const esParticular = isVehiculoParticular(draft.modo_principal);
  const sinCosto = isModoSinCosto(draft.modo_principal);

  return {
    viaje_numero: viajeNumero,
    persona_numero: Number(draft.persona_numero),
    origen_direccion: origenDireccion,
    zona_od_origen: origen,
    destino_direccion: destinoDireccion,
    zona_od_destino: destino,
    hora_salida: horaSalidaFinal,
    hora_llegada: horaLlegadaFinal,
    motivo_viaje: String(draft.motivo_viaje),
    motivo_viaje_otro: draft.motivo_viaje === '8' ? (draft.motivo_viaje_otro || '').trim() : undefined,
    modo_principal: String(draft.modo_principal),
    modo_principal_otro: draft.modo_principal === '8' ? (draft.modo_principal_otro || '').trim() : undefined,
    modo_secundario: !esParticular && draft.modo_secundario ? String(draft.modo_secundario) : undefined,
    modo_secundario_otro: !esParticular && draft.modo_secundario === '8' ? (draft.modo_secundario_otro || '').trim() : undefined,
    tiempo_viaje_min: Number(draft.tiempo_viaje_min),
    costo_viaje_bs: sinCosto ? 0 : Number(draft.costo_viaje_bs ?? 0)
  };
}

export function buildReturnTrip(
  viajeIda: ViajeOD,
  viajeNumero: number,
  zonaResidenciaDefault = ''
): ViajeOD {
  const esParticular = isVehiculoParticular(viajeIda.modo_principal);
  const sinCosto = isModoSinCosto(viajeIda.modo_principal);
  const regreso: ViajeOD = {
    viaje_numero: viajeNumero,
    persona_numero: viajeIda.persona_numero,
    zona_od_origen: viajeIda.zona_od_destino,
    zona_od_destino: zonaResidenciaDefault || viajeIda.zona_od_origen,
    motivo_viaje: viajeIda.motivo_viaje,
    modo_principal: viajeIda.modo_principal,
    tiempo_viaje_min: viajeIda.tiempo_viaje_min,
    costo_viaje_bs: sinCosto ? 0 : viajeIda.costo_viaje_bs
  };

  if (viajeIda.destino_direccion) regreso.origen_direccion = viajeIda.destino_direccion;
  if (viajeIda.origen_direccion) regreso.destino_direccion = viajeIda.origen_direccion;
  if (viajeIda.hora_salida) regreso.hora_salida = viajeIda.hora_salida;
  if (viajeIda.hora_llegada) regreso.hora_llegada = viajeIda.hora_llegada;
  if (viajeIda.motivo_viaje_otro) regreso.motivo_viaje_otro = viajeIda.motivo_viaje_otro;
  if (viajeIda.modo_principal_otro) regreso.modo_principal_otro = viajeIda.modo_principal_otro;
  if (!esParticular && viajeIda.modo_secundario) regreso.modo_secundario = viajeIda.modo_secundario;
  if (!esParticular && viajeIda.modo_secundario_otro) regreso.modo_secundario_otro = viajeIda.modo_secundario_otro;

  return regreso;
}
