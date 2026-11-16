export interface SurveyStep {
  id: number;
  title: string;
  shortTitle: string;
  estimatedTime: string;
}

export const SURVEY_STEPS: SurveyStep[] = [
  { id: 1, title: 'Ubicación y Caracterización del Hogar', shortTitle: 'Ubicación', estimatedTime: '2 min' },
  { id: 2, title: 'Datos de la Vivienda', shortTitle: 'Vivienda', estimatedTime: '2 min' },
  { id: 3, title: 'Datos del Hogar', shortTitle: 'Hogar', estimatedTime: '2 min' },
  { id: 4, title: 'Composición del Hogar y Residentes Habituales', shortTitle: 'Residentes', estimatedTime: '3 min' },
  { id: 5, title: 'Movilidad Cotidiana y Registro de Viajes', shortTitle: 'Viajes', estimatedTime: '4 min' },
  { id: 6, title: 'Calidad de los Servicios de Transporte', shortTitle: 'Transporte Público', estimatedTime: '2 min' },
  { id: 7, title: 'Movilidad Activa y Espacio Público', shortTitle: 'Espacio Público', estimatedTime: '2 min' },
  { id: 8, title: 'Observaciones y Cierre', shortTitle: 'Cierre', estimatedTime: '1 min' }
];

export interface Residente {
  persona_numero: number;
  nombres?: string;
  nombre_apellido?: string;
  parentesco: string;
  parentesco_jefe_hogar?: string;
  sexo: string;
  edad: number;
  sabe_leer_escribir?: string;
  nivel_educativo?: string;
  actividad_principal?: string;
  ocupacion_principal?: string;
  medio_transporte_habitual?: string;
  posee_licencia?: string;
  tiene_vehiculo_disponible?: string;
  tipo_vehiculo?: string;
  cantidad_vehiculo?: number;
}

export interface ViajeOD {
  viaje_numero: number;
  persona_numero: number;
  origen_direccion?: string;
  zona_od_origen: string;
  destino_direccion?: string;
  zona_od_destino: string;
  hora_salida?: string;
  hora_llegada?: string;
  motivo_viaje: string;
  motivo_viaje_otro?: string;
  modo_principal: string;
  modo_principal_otro?: string;
  modo_secundario?: string;
  modo_secundario_otro?: string;
  tiempo_viaje_min: number;
  costo_viaje_bs: number;
}
