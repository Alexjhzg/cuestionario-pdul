<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { useToast } from 'primevue/usetoast';
import { isValidParroquia, PARROQUIAS_MATURIN, formatParroquia } from '@/utils/validation';
import ViajesMobileCards from './ViajesMobileCards.vue';
import ResidentesCards from './ResidentesCards.vue';

let toast: ReturnType<typeof useToast> | null = null;
try {
  toast = useToast();
} catch {
  // Entorno de prueba unitaria sin Provide/Inject
}

const TIPOS_VIVIENDA = [
  { value: 'quinta_casa_quinta', label: 'a.- Quinta o Casa quinta' },
  { value: 'casa', label: 'b.- Casa' },
  { value: 'apartamento_edificio', label: 'c.- Apartamento en edificio' },
  { value: 'apartamento_quinta_casa', label: 'd.- Apartamento en quinta, casa-quinta o casa' },
  { value: 'casa_vecindad', label: 'e.- Casa de vecindad' },
  { value: 'vivienda_rustica', label: 'f.- Vivienda rústica (rancho)' },
  { value: 'otro', label: 'g.- Otro tipo' }
] as const;

const TENENCIA_VIVIENDA = [
  { value: 'propia_pagada', label: 'a.- Propia pagada totalmente' },
  { value: 'propia_pagandose', label: 'b.- Propia pagándose' },
  { value: 'alquilada', label: 'c.- Alquilada' },
  { value: 'alquilada_parte', label: 'd.- Alquilada parte de la Vivienda' },
  { value: 'cedida_trabajo', label: 'e.- Cedida por razones de trabajo' },
  { value: 'cedida_familiar', label: 'f.- Cedida por familiar o amigo' },
  { value: 'tomada_invadida', label: 'g.- Tomada/Invadida' },
  { value: 'otra_forma', label: 'h.- Otra forma' }
] as const;

// Opciones de Sección VI: Características de Transporte Público
const DIFICULTADES_ACCESO_TP = [
  { value: 'frecuencia_baja', label: 'a.- Frecuencia baja' },
  { value: 'sobrecupo', label: 'b.- Sobrecupo' },
  { value: 'falta_de_rutas', label: 'c.- Falta de rutas' },
  { value: 'inseguridad', label: 'd.- Inseguridad' },
  { value: 'otro', label: 'e.- Otro' }
] as const;

const CALIFICACION_TP = [
  { value: 'muy_bueno', label: 'a.- Muy bueno' },
  { value: 'bueno', label: 'b.- Bueno' },
  { value: 'regular', label: 'c.- Regular' },
  { value: 'malo', label: 'd.- Malo' },
  { value: 'muy_malo', label: 'e.- Muy malo' }
] as const;

const ACUERDO_RUTAS_DIRECTAS = [
  { value: 'totalmente_de_acuerdo', label: 'a.- Totalmente de acuerdo' },
  { value: 'de_acuerdo', label: 'b.- De acuerdo' },
  { value: 'neutral', label: 'c.- Ni de acuerdo ni en desacuerdo (Neutral)' },
  { value: 'en_desacuerdo', label: 'd.- En desacuerdo' },
  { value: 'totalmente_en_desacuerdo', label: 'e.- Totalmente en desacuerdo' }
] as const;

// Opciones de Sección VII: Movilidad No Motorizada y Percepción
const MOTIVOS_CAMBIO_DESPLAZAMIENTO = [
  { value: 'cambio_trabajo', label: 'a.- Cambio de trabajo' },
  { value: 'cambio_residencia', label: 'b.- Cambio de residencia' },
  { value: 'falta_transporte', label: 'c.- Falta de transporte' },
  { value: 'costo', label: 'd.- Costo' },
  { value: 'otro', label: 'e.- Otro' }
] as const;

const MODO_CENTRO_ACTIVIDADES = [
  { value: 'camina', label: 'a.- Camina' },
  { value: 'transporte_publico', label: 'b.- Transporte público' }
] as const;

const SEGURIDAD_CENTRO = [
  { value: 'muy_seguro', label: 'a.- Muy seguro' },
  { value: 'seguro', label: 'b.- Seguro' },
  { value: 'neutral', label: 'c.- Neutral' },
  { value: 'inseguro', label: 'd.- Inseguro' },
  { value: 'muy_inseguro', label: 'e.- Muy Inseguro' }
] as const;

// Opciones de Sección VIII: Esparcimientos
const FRECUENCIA_VISITA_PARQUES = [
  { value: 'nunca', label: 'a.- Nunca' },
  { value: 'ocasionalmente', label: 'b.- Ocasionalmente' },
  { value: 'mensual', label: 'c.- Mensual' },
  { value: 'semanal', label: 'd.- Semanal' },
  { value: 'diario', label: 'e.- Diario' }
] as const;

const ACTIVIDADES_PARQUES = [
  { value: 'caminar', label: 'a.- Caminar' },
  { value: 'trotar_correr', label: 'b.- Trotar/Correr' },
  { value: 'recreacion_infantil', label: 'c.- Recreación Infantil' },
  { value: 'deporte', label: 'd.- Deporte' },
  { value: 'descanso', label: 'e.- Descanso' },
  { value: 'lectura', label: 'f.- Lectura' },
  { value: 'otras', label: 'g.- Otras' }
] as const;

const CAMINATAS_CIUDAD = [
  { value: 'si', label: 'a.- Sí' },
  { value: 'no', label: 'b.- No' },
  { value: 'a_veces', label: 'c.- A veces' }
] as const;

const ESCALA_SEGURIDAD_PARQUES = [
  { value: 'nada_seguro', label: 'a.- Nada Seguro(a)' },
  { value: 'poco_seguro', label: 'b.- Poco seguro(a)' },
  { value: 'neutral', label: 'c.- Ni seguro(a), ni inseguro(a)/neutral' },
  { value: 'bastante_seguro', label: 'd.- Algo seguro(a) / Bastante seguro(a)' },
  { value: 'muy_seguro', label: 'e.- Totalmente seguro(a) / Muy seguro(a)' }
] as const;

const CALIFICACION_LIMPIEZA = [
  { value: 'muy_buena', label: 'a.- Muy buena' },
  { value: 'buena', label: 'b.- Buena' },
  { value: 'regular', label: 'c.- Regular' },
  { value: 'mala', label: 'd.- Mala' },
  { value: 'muy_mala', label: 'e.- Muy mala' }
] as const;

const IMPEDIMENTOS_ESPACIOS = [
  { value: 'distancia', label: 'a.- Distancia' },
  { value: 'falta_tiempo', label: 'b.- Falta de tiempo' },
  { value: 'inseguridad', label: 'c.- Inseguridad' },
  { value: 'mala_accesibilidad', label: 'd.- Mala accesibilidad' },
  { value: 'falta_mantenimiento', label: 'e.- Falta de mantenimiento' },
  { value: 'otras', label: 'f.- Otras' }
] as const;

const SATISFACCION_CENTRO = [
  { value: 'muy_insatisfecho', label: 'a.- Muy insatisfecho(a)' },
  { value: 'insatisfecho', label: 'b.- Insatisfecho(a)' },
  { value: 'neutral', label: 'c.- Ni satisfecho(a) ni insatisfecho(a) / Neutral' },
  { value: 'satisfecho', label: 'd.- Satisfecho(a)' },
  { value: 'muy_satisfecho', label: 'e.- Muy satisfecho(a)' }
] as const;

const MEJORAS_PRIORITARIAS = [
  { value: 'mas_parques_plazas', label: 'a.- Crear más parques y plazas' },
  { value: 'mantenimiento_existentes', label: 'b.- Mejorar el mantenimiento de los parques y espacios existentes (limpieza, áreas verdes, bancas, iluminación)' },
  { value: 'rutas_peatonales_ciclovias', label: 'c.- Ampliar y mejorar las rutas peatonales y ciclovías' },
  { value: 'iluminacion', label: 'd.- Aumentar la iluminación en parques y rutas peatonales' },
  { value: 'seguridad_policial', label: 'e.- Mejorar la seguridad (vigilancia, cámaras, presencia policial)' },
  { value: 'mobiliario_urbano', label: 'f.- Instalar más mobiliario urbano (bancas, basureros, bebederos, sombras)' },
  { value: 'juegos_ninos', label: 'g.- Crear o mejorar áreas de juego para niños' },
  { value: 'espacios_deportivos', label: 'h.- Crear o mejorar espacios deportivos y recreativos (canchas, gimnasios al aire libre)' },
  { value: 'actividades_culturales', label: 'i.- Organizar más actividades culturales y recreativas (eventos, talleres, ferias)' },
  { value: 'accesibilidad_discapacidad', label: 'j.- Mejorar la accesibilidad para personas con discapacidad' },
  { value: 'recuperar_abandonados', label: 'k.- Recuperar espacios abandonados o subutilizados' },
  { value: 'participacion_ciudadana', label: 'l.- Promover la participación ciudadana en el diseño y cuidado de los espacios' },
  { value: 'otro', label: 'm.- Otro (especifique)' }
] as const;

const DISPOSICION_PARTICIPAR = [
  { value: 'si', label: 'a.- Sí' },
  { value: 'no', label: 'b.- No' },
  { value: 'tal_vez', label: 'c.- Tal vez' }
] as const;

const ACUERDO_ACERA_COMODA = [
  { value: 'totalmente_de_acuerdo', label: 'a.- Totalmente de acuerdo' },
  { value: 'de_acuerdo', label: 'b.- De acuerdo' },
  { value: 'neutral', label: 'c.- Ni de acuerdo ni en desacuerdo (Neutral)' },
  { value: 'en_desacuerdo', label: 'd.- En desacuerdo' },
  { value: 'totalmente_en_desacuerdo', label: 'e.- Totalmente en desacuerdo' }
] as const;

const FACILIDAD_LLEGADA = [
  { value: 'muy_facil', label: 'a.- Muy fácil' },
  { value: 'facil', label: 'b.- Fácil' },
  { value: 'regular', label: 'c.- Regular' },
  { value: 'dificil', label: 'd.- Difícil' },
  { value: 'muy_dificil', label: 'e.- Muy Difícil' }
] as const;

const ESPARCIMIENTOS_FALTANTES = [
  { value: 'bancas', label: 'a.- Bancas' },
  { value: 'sombra', label: 'b.- Sombra' },
  { value: 'iluminacion', label: 'c.- Iluminación' },
  { value: 'maquinas_ejercicios', label: 'd.- Maquinas de ejercicios' },
  { value: 'banos', label: 'e.- Baños' },
  { value: 'juegos', label: 'f.- Juegos' },
  { value: 'ciclovia', label: 'g.- Ciclovía' },
  { value: 'senalizacion', label: 'h.- Señalización' },
  { value: 'otros', label: 'i.- Otros' }
] as const;

const PLANES_MOVILIDAD_PESTONAL = [
  { value: 'si', label: 'a.- Sí' },
  { value: 'no', label: 'b.- No' },
  { value: 'no_sabe', label: 'c.- No Sabe/No responde' }
] as const;
import { SURVEY_STEPS, type Residente, type ViajeOD } from '@/types/survey';

const props = withDefaults(
  defineProps<{
    modelValue: Record<string, any>;
    step?: number;
    submitting?: boolean;
    encuestaTitulo?: string;
  }>(),
  {
    step: 0,
    submitting: false,
    encuestaTitulo: 'Cuestionario Origen-Destino (PDUL Maturín)'
  }
);

const emit = defineEmits<{
  (e: 'update:modelValue', data: Record<string, any>): void;
  (e: 'update:step', step: number): void;
  (e: 'submit', data: Record<string, any>): void;
}>();

// Estado local reactivo de paso si no se maneja externamente
const localStep = ref<number>(props.step);

const currentStepIndex = computed({
  get: () => (props.step !== undefined ? props.step : localStep.value),
  set: (val: number) => {
    localStep.value = val;
    emit('update:step', val);
  }
});

const totalSteps = SURVEY_STEPS.length;
const stepWeight = 100 / totalSteps; // 12.5% por cada uno de los 8 pasos

/**
 * Calcula la fracción de preguntas respondidas en el paso actual (de 0.0 a 1.0)
 * para reflejar el progreso de avance en tiempo real a medida que el usuario interactúa.
 */
function calculateStepProgress(stepIdx: number, data: Record<string, any>): number {
  if (!data) return 0;
  switch (stepIdx) {
    case 0: { // Paso 1: Ubicación y Caracterización del Hogar
      let score = 0;
      if (data.parroquia && String(data.parroquia).trim().length > 0) score += 1.0;
      if (data.comunidad_sector && String(data.comunidad_sector).trim().length > 0) score = Math.min(1, score + 0.1);
      return Math.min(1, score);
    }
    case 1: { // Paso 2: Datos de la Vivienda
      let filled = 0;
      if (data.tipo_vivienda) filled++;
      if (data.total_cuartos_vivienda !== undefined && data.total_cuartos_vivienda !== null && data.total_cuartos_vivienda !== '') filled++;
      return filled > 0 ? filled / 2 : 0.25;
    }
    case 2: { // Paso 3: Datos del Hogar
      let filled = 0;
      if (data.grupos_gastos_separados !== undefined && data.grupos_gastos_separados !== null && data.grupos_gastos_separados !== '') filled++;
      if (data.hogar_numero !== undefined && data.hogar_numero !== null && data.hogar_numero !== '') filled++;
      if (data.cuartos_dormir_hogar !== undefined && data.cuartos_dormir_hogar !== null && data.cuartos_dormir_hogar !== '') filled++;
      if (data.numero_personas_hogar !== undefined && data.numero_personas_hogar !== null && data.numero_personas_hogar !== '') filled++;
      if (data.tenencia_vivienda) filled++;
      return filled > 0 ? filled / 5 : 0.25;
    }
    case 3: { // Paso 4: Composición del Hogar y Residentes Habituales
      return Array.isArray(data.residentes) && data.residentes.length > 0 ? 1 : 0.3;
    }
    case 4: { // Paso 5: Movilidad Cotidiana y Registro de Viajes
      return Array.isArray(data.viajes) && data.viajes.length > 0 ? 1 : 0.3;
    }
    case 5: { // Paso 6: Características de Transporte Público
      let filled = 0;
      if (data.rutas_tp_dia !== undefined && data.rutas_tp_dia !== null && data.rutas_tp_dia !== '') filled++;
      if (data.tiempo_espera_paradas_min !== undefined && data.tiempo_espera_paradas_min !== null && data.tiempo_espera_paradas_min !== '') filled++;
      if (data.km_residencia_parada !== undefined && data.km_residencia_parada !== null && data.km_residencia_parada !== '') filled++;
      if (data.dificultades_acceso_tp) filled++;
      if (data.calificacion_servicio_tp) filled++;
      if (data.gasto_semanal_transporte_bs !== undefined && data.gasto_semanal_transporte_bs !== null && data.gasto_semanal_transporte_bs !== '') filled++;
      if (data.acuerdo_rutas_directas) filled++;
      return filled > 0 ? filled / 7 : 0.25;
    }
    case 6: { // Paso 7: SECCIÓN VII: MOVILIDAD NO MOTORIZADA Y PERCEPCIÓN
      let filled = 0;
      if (data.cambio_movilidad_5_anos) filled++;
      if (data.caminatas_mas_10min) filled++;
      if (data.usa_bicicleta) filled++;
      if (data.dias_camina_bici_semana !== undefined && data.dias_camina_bici_semana !== null && data.dias_camina_bici_semana !== '') filled++;
      if (data.modo_actividades_centro) filled++;
      if (data.aceras_adecuadas) filled++;
      if (data.seguridad_desplazamiento_centro) filled++;
      return filled > 0 ? filled / 7 : 0.25;
    }
    case 7: { // Paso 8: SECCIÓN VIII: ESPARCIMIENTOS Y CIERRE
      let filled = 0;
      if (data.frecuencia_visita_parques) filled++;
      if (data.caminatas_ciudad) filled++;
      if (data.seguridad_parques_dia) filled++;
      if (data.seguridad_parques_noche) filled++;
      if (data.limpieza_parques) filled++;
      if (data.satisfaccion_centro) filled++;
      if (data.acera_comoda) filled++;
      if (data.facilidad_llegada_parques) filled++;
      if (data.cruce_peatonal_todas) filled++;
      if (data.observaciones_generales && String(data.observaciones_generales).trim().length > 0) filled++;
      if (data.acepta_declaracion !== false) filled++;
      return filled > 0 ? filled / 11 : 0.25;
    }
    default:
      return 0;
  }
}

// Porcentaje de avance en tiempo real pregunta por pregunta
const progressPercentage = computed(() => {
  const data = props.modelValue || {};
  const currentStep = currentStepIndex.value;

  // Base por pasos completados previamente
  const baseProgress = currentStep * stepWeight;
  // Fracción ganada por preguntas respondidas en el paso actual
  const currentStepFraction = calculateStepProgress(currentStep, data);
  const currentStepProgress = currentStepFraction * stepWeight;

  const total = baseProgress + currentStepProgress;
  return Math.min(100, Math.round(total * 10) / 10);
});

const currentStepData = computed(() => SURVEY_STEPS[currentStepIndex.value] || SURVEY_STEPS[0]);

// Errores de validación por paso
const stepErrors = ref<string[]>([]);

watch(
  () => props.modelValue,
  () => {
    if (stepErrors.value.length > 0) {
      stepErrors.value = [];
    }
  },
  { deep: true }
);
const touchedFields = ref<Record<string, boolean>>({});

function markTouched(fieldName: string) {
  touchedFields.value[fieldName] = true;
}

function updateField(field: string, value: any) {
  const updated = { ...props.modelValue, [field]: value };
  emit('update:modelValue', updated);
}

function updateResidentes(residentes: Residente[]) {
  updateField('residentes', residentes);
}

function updateViajes(viajes: ViajeOD[]) {
  updateField('viajes', viajes);
}

function toggleMultiSelect(field: string, val: string) {
  const current: string[] = Array.isArray(props.modelValue[field]) ? [...props.modelValue[field]] : [];
  const idx = current.indexOf(val);
  if (idx >= 0) {
    current.splice(idx, 1);
  } else {
    current.push(val);
  }
  updateField(field, current);
}

function isBlankValue(value: unknown): boolean {
  if (value === undefined || value === null) return true;
  if (typeof value === 'string') return value.trim().length === 0;
  if (Array.isArray(value)) return value.length === 0;
  return false;
}

function isNumericValue(value: unknown): boolean {
  if (isBlankValue(value)) return false;
  return !isNaN(Number(value));
}

/**
 * Obtiene los errores de una sección. Los ciudadanos deben completar todas las
 * preguntas visibles de cada sección antes de avanzar o finalizar la encuesta.
 */
function getStepErrors(stepIdx: number, data: Record<string, any>): string[] {
  const errors: string[] = [];
  const source = data || {};

  const requireField = (field: string, label: string) => {
    if (isBlankValue(source[field])) {
      errors.push(label);
    }
  };

  const requireNumber = (field: string, label: string, min: number) => {
    if (!isNumericValue(source[field]) || Number(source[field]) < min) {
      errors.push(label);
    }
  };

  const requireMulti = (field: string, label: string) => {
    if (!Array.isArray(source[field]) || source[field].length === 0) {
      errors.push(label);
    }
  };

  switch (stepIdx) {
    case 0: {
      if (!source.parroquia || !isValidParroquia(source.parroquia)) {
        errors.push('1.- Seleccione su parroquia.');
      }
      requireField('comunidad_sector', '2.- Indique su comunidad o sector.');
      requireField('zona_residencia_od', '3.- Indique su zona de residencia (zonificación O-D).');
      requireField('avenida_calle', '4.- Indique la avenida o calle.');
      requireField('casa_apartamento', '5.- Indique la casa o apartamento.');
      break;
    }

    case 1: {
      requireField('tipo_vivienda', '1.- Seleccione el tipo de vivienda.');
      if (source.tipo_vivienda === 'otro') {
        requireField('tipo_vivienda_otro', '1.g.- Especifique el otro tipo de vivienda.');
      }
      requireNumber('total_cuartos_vivienda', '2.- Indique el total de cuartos de la vivienda.', 1);
      break;
    }

    case 2: {
      requireNumber('grupos_gastos_separados', '1.- Indique cuántos grupos mantienen gastos separados.', 1);
      requireNumber('hogar_numero', 'Hogar N°: indique el número de hogar.', 1);
      requireNumber('cuartos_dormir_hogar', '2.- Indique cuántos cuartos para dormir utiliza el hogar.', 1);
      requireNumber('numero_personas_hogar', '3.- Indique el número de personas que residen en el hogar.', 1);
      requireField('tenencia_vivienda', '4.- Seleccione la forma de tenencia de la vivienda.');
      if (source.tenencia_vivienda === 'otra_forma') {
        requireField('tenencia_vivienda_otro', '4.h.- Especifique la otra forma de tenencia.');
      }
      break;
    }

    case 3: {
      const residentes: Residente[] = Array.isArray(source.residentes) ? source.residentes : [];
      const esperado = Number(source.numero_personas_hogar);

      if (residentes.length === 0) {
        errors.push('Registre al menos un residente en el hogar.');
      } else if (!isNaN(esperado) && esperado > 0 && residentes.length < esperado) {
        errors.push(
          `Ha registrado ${residentes.length} de ${esperado} integrantes declarados en la Sección III (Pregunta 3). Debe completar los datos de todos los miembros de la familia.`
        );
      }

      residentes.forEach((r, idx) => {
        const prefix = `Residente #${idx + 1}:`;
        if (isBlankValue(r.nombres) && isBlankValue(r.nombre_apellido)) {
          errors.push(`${prefix} indique el nombre y apellido.`);
        }
        if (isBlankValue(r.parentesco) && isBlankValue(r.parentesco_jefe_hogar)) {
          errors.push(`${prefix} seleccione el parentesco con el jefe de hogar.`);
        }
        if (isBlankValue(r.sexo)) {
          errors.push(`${prefix} seleccione el sexo.`);
        }
        if (!isNumericValue(r.edad) || Number(r.edad) < 0 || Number(r.edad) > 120) {
          errors.push(`${prefix} indique una edad válida (0 a 120 años).`);
        }
        if (isBlankValue(r.sabe_leer_escribir)) {
          errors.push(`${prefix} indique si sabe leer y escribir.`);
        }
        if (isBlankValue(r.nivel_educativo)) {
          errors.push(`${prefix} seleccione el nivel educativo.`);
        }
        if (isBlankValue(r.actividad_principal) && isBlankValue(r.ocupacion_principal)) {
          errors.push(`${prefix} seleccione la ocupación o actividad principal.`);
        }
        if (isBlankValue(r.medio_transporte_habitual)) {
          errors.push(`${prefix} seleccione el medio de transporte habitual.`);
        }
        if (isBlankValue(r.posee_licencia)) {
          errors.push(`${prefix} indique si posee licencia de conducir.`);
        }
        if (isBlankValue(r.tiene_vehiculo_disponible)) {
          errors.push(`${prefix} indique si tiene algún vehículo disponible.`);
        } else if (r.tiene_vehiculo_disponible === 'si') {
          if (isBlankValue(r.tipo_vehiculo)) {
            errors.push(`${prefix} seleccione el tipo de vehículo.`);
          }
          if (!isNumericValue(r.cantidad_vehiculo) || Number(r.cantidad_vehiculo) < 1) {
            errors.push(`${prefix} indique la cantidad de vehículos.`);
          }
        }
      });
      break;
    }

    case 4: {
      const viajes: ViajeOD[] = Array.isArray(source.viajes) ? source.viajes : [];

      if (viajes.length === 0) {
        errors.push('Registre al menos un viaje realizado.');
      }

      viajes.forEach((v, idx) => {
        const prefix = `Viaje #${idx + 1}:`;
        if (!isNumericValue(v.persona_numero) || Number(v.persona_numero) < 1) {
          errors.push(`${prefix} seleccione la persona que realizó el viaje.`);
        }
        if (isBlankValue(v.origen_direccion)) {
          errors.push(`${prefix} indique la dirección o referencia de origen.`);
        }
        if (isBlankValue(v.zona_od_origen)) {
          errors.push(`${prefix} indique la zona O-D de origen.`);
        }
        if (isBlankValue(v.destino_direccion)) {
          errors.push(`${prefix} indique la dirección o referencia de destino.`);
        }
        if (isBlankValue(v.zona_od_destino)) {
          errors.push(`${prefix} indique la zona O-D de destino.`);
        }
        if (isBlankValue(v.hora_salida)) {
          errors.push(`${prefix} indique la hora de salida.`);
        }
        if (isBlankValue(v.hora_llegada)) {
          errors.push(`${prefix} indique la hora de llegada.`);
        }
        if (isBlankValue(v.motivo_viaje)) {
          errors.push(`${prefix} seleccione el motivo del viaje.`);
        } else if (v.motivo_viaje === '8' && isBlankValue(v.motivo_viaje_otro)) {
          errors.push(`${prefix} especifique el otro motivo del viaje.`);
        }
        if (isBlankValue(v.modo_principal)) {
          errors.push(`${prefix} seleccione el modo de transporte principal.`);
        } else if (v.modo_principal === '8' && isBlankValue(v.modo_principal_otro)) {
          errors.push(`${prefix} especifique el otro modo de transporte principal.`);
        }
        if (v.modo_secundario === '8' && isBlankValue(v.modo_secundario_otro)) {
          errors.push(`${prefix} especifique el otro modo de transporte secundario.`);
        }
        if (!isNumericValue(v.tiempo_viaje_min) || Number(v.tiempo_viaje_min) < 1) {
          errors.push(`${prefix} indique el tiempo de viaje en minutos.`);
        }
        if (!isNumericValue(v.costo_viaje_bs) || Number(v.costo_viaje_bs) < 0) {
          errors.push(`${prefix} indique el costo del viaje (puede ser 0).`);
        }
      });
      break;
    }

    case 5: {
      requireNumber('rutas_tp_dia', '1.- Indique cuántas rutas de transporte público utilizó.', 0);
      requireNumber('tiempo_espera_paradas_min', '2.- Indique el tiempo total de espera en paradas.', 0);
      requireNumber('km_residencia_parada', '3.- Indique los kilómetros desde su residencia hasta la parada.', 0);
      requireField('dificultades_acceso_tp', '4.- Indique si ha tenido dificultades para acceder al transporte público.');
      if (source.dificultades_acceso_tp === 'si') {
        requireField('principal_dificultad_tp', '5.- Seleccione la principal dificultad de acceso.');
        if (source.principal_dificultad_tp === 'otro') {
          requireField('principal_dificultad_tp_otro', '5.e.- Especifique la otra dificultad.');
        }
      }
      requireField('calificacion_servicio_tp', '6.- Califique el servicio de transporte público.');
      requireNumber('gasto_semanal_transporte_bs', '7.- Indique el gasto semanal en transporte.', 0);
      requireField('acuerdo_rutas_directas', '8.- Indique su acuerdo con la creación de rutas directas.');
      requireField('comentarios_transporte_maturin', '9.- Escriba un comentario o sugerencia sobre el transporte en Maturín.');
      break;
    }

    case 6: {
      requireField('cambio_movilidad_5_anos', '1.- Indique si ha cambiado su forma de desplazarse en los últimos 5 años.');
      if (source.cambio_movilidad_5_anos === 'si') {
        requireField('motivo_cambio_desplazamiento', '2.- Seleccione el motivo del cambio de desplazamiento.');
        if (source.motivo_cambio_desplazamiento === 'otro') {
          requireField('motivo_cambio_desplazamiento_otro', '2.e.- Especifique el otro motivo.');
        }
      }
      requireField('caminatas_mas_10min', '3.- Indique si realiza caminatas de más de 10 minutos.');
      requireField('usa_bicicleta', '4.- Indique si utiliza bicicleta como medio de transporte.');
      requireNumber('dias_camina_bici_semana', '5.- Indique cuántos días a la semana camina o usa bicicleta.', 0);
      requireField('modo_actividades_centro', '6.- Indique cómo se desplaza en el centro de la ciudad.');
      requireField('aceras_adecuadas', '7.- Indique si las aceras y espacios peatonales son adecuados.');
      requireField('seguridad_desplazamiento_centro', '8.- Indique qué tan seguro se siente al desplazarse por el centro.');
      break;
    }

    case 7: {
      requireField('frecuencia_visita_parques', '1.- Indique con qué frecuencia visita parques y plazas.');
      requireMulti('actividades_parques', '2.- Seleccione al menos una actividad que realiza en estos espacios.');
      if (Array.isArray(source.actividades_parques) && source.actividades_parques.includes('otras')) {
        requireField('actividades_parques_otras', '2.g.- Especifique las otras actividades.');
      }
      requireField('caminatas_ciudad', '3.- Indique si suele hacer caminatas por la ciudad.');
      requireField('seguridad_parques_dia', '7.- Indique qué tan seguro se siente en parques y rutas peatonales durante el día.');
      requireField('seguridad_parques_noche', '8.- Indique qué tan seguro se siente en parques y rutas peatonales durante la noche.');
      requireField('limpieza_parques', '9.- Califique la limpieza y conservación de las áreas de esparcimiento.');
      requireMulti('impedimentos_espacios', '10.- Seleccione al menos un impedimento para usar estos espacios.');
      if (Array.isArray(source.impedimentos_espacios) && source.impedimentos_espacios.includes('otras')) {
        requireField('impedimentos_espacios_otras', '10.f.- Especifique los otros impedimentos.');
      }
      requireField('satisfaccion_centro', '11.- Indique su satisfacción con las áreas de esparcimiento del centro.');
      requireMulti('mejoras_prioritarias', '12.- Seleccione al menos una mejora prioritaria.');
      if (Array.isArray(source.mejoras_prioritarias) && source.mejoras_prioritarias.includes('otro')) {
        requireField('mejoras_prioritarias_otro', '12.m.- Especifique la otra mejora prioritaria.');
      }
      requireField('parque_mejorar_primero', '13.- Indique qué parque, plaza o ruta debe mejorarse primero.');
      requireField('disposicion_participar_mejoras', '14.- Indique si estaría dispuesto a participar en las mejoras.');
      requireField('sugerencias_esparcimiento', '15.- Escriba una sugerencia para mejorar las áreas de esparcimiento y caminatas.');
      requireField('acera_comoda', '16.- Indique si la acera es suficiente y cómoda para caminar.');
      requireField('sectores_para_caminar', '17.- Indique qué sectores utiliza para caminar.');
      requireField('facilidad_llegada_parques', '18.- Indique qué tan fácil es llegar a las áreas de esparcimiento.');
      requireMulti('esparcimientos_faltantes', '19.- Seleccione al menos un esparcimiento faltante.');
      if (Array.isArray(source.esparcimientos_faltantes) && source.esparcimientos_faltantes.includes('otros')) {
        requireField('esparcimientos_faltantes_otros', '19.i.- Especifique los otros esparcimientos faltantes.');
      }
      requireField('cruce_peatonal_todas', '20.- Indique si existe cruce peatonal en todas las intersecciones.');
      if (source.cruce_peatonal_todas === 'si') {
        requireField('cruce_demarcado_visible', '21.- Indique si el cruce peatonal está demarcado y visible.');
      }
      requireField('seguridad_cruzar_interseccion', '22.- Indique si se siente seguro al cruzar la intersección.');
      requireField('hay_semaforo_peatonal', '23.- Indique si hay semáforo peatonal.');
      requireField('mapas_senales_caminata', '24.- Indique si existen mapas o señales de caminata.');
      requireField('movilidad_reducida_sin_ayuda', '25.- Indique si una persona con movilidad reducida puede desplazarse sin ayuda.');
      requireField('nombres_calles_visibles', '26.- Indique si las señalizaciones de nombres de calles son visibles.');
      requireField('senalizacion_clara_sin_obstaculos', '27.- Indique si la señalización es clara y sin obstáculos.');
      requireField('trayecto_pie_parada_seguro', '28.- Indique si el trayecto a pie hasta la parada es seguro.');
      requireField('aire_ruido_aceptables', '29.- Indique si el aire y el ruido son aceptables para caminar.');
      requireField('conductores_ceden_paso', '30.- Indique si los conductores ceden el paso a los peatones.');
      requireField('ciudad_prioriza_peaton', '31.- Indique si la ciudad prioriza al peatón sobre el automóvil.');
      requireField('participacion_consultas_peatonales', '32.- Indique si ha participado en consultas sobre espacios peatonales.');
      requireField('planes_movilidad_peatonal_normativa', '33.- Indique si existen planes, presupuesto o normativa de movilidad peatonal.');
      requireField('observaciones_generales', 'Observaciones: escriba sus observaciones o propuestas adicionales.');
      if (source.acepta_declaracion === false) {
        errors.push('Debe confirmar la veracidad de la información para enviar.');
      }
      break;
    }

    default:
      break;
  }

  return errors;
}

function showValidationErrors(errors: string[], summary = 'Datos requeridos') {
  try {
    if (toast && typeof toast.add === 'function' && errors.length > 0) {
      const shown = errors.slice(0, 3).join(' ');
      const remaining = errors.length - 3;
      toast.add({
        severity: 'warn',
        summary,
        detail: remaining > 0 ? `${shown} Y ${remaining} pregunta(s) más por completar.` : shown,
        life: 5000
      });
    }
  } catch {
    // Modo headless
  }
}

function validateCurrentStep(): boolean {
  stepErrors.value = getStepErrors(currentStepIndex.value, props.modelValue || {});

  if (stepErrors.value.length > 0) {
    showValidationErrors(stepErrors.value);
    return false;
  }

  return true;
}

function nextStep() {
  if (validateCurrentStep()) {
    if (currentStepIndex.value < totalSteps - 1) {
      currentStepIndex.value++;
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }
}

function prevStep() {
  if (currentStepIndex.value > 0) {
    stepErrors.value = [];
    currentStepIndex.value--;
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
}

function goToStep(targetIndex: number) {
  if (targetIndex < currentStepIndex.value) {
    stepErrors.value = [];
    currentStepIndex.value = targetIndex;
  } else if (targetIndex === currentStepIndex.value + 1) {
    nextStep();
  }
}

function onSubmit() {
  const data = props.modelValue || {};

  // Al finalizar se revalidan TODAS las secciones, no solo la última.
  for (let idx = 0; idx < totalSteps; idx++) {
    const errors = getStepErrors(idx, data);
    if (errors.length > 0) {
      stepErrors.value = errors;
      if (currentStepIndex.value !== idx) {
        currentStepIndex.value = idx;
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
      showValidationErrors(errors, 'Complete todas las preguntas de la encuesta');
      return;
    }
  }

  stepErrors.value = [];
  emit('submit', data);
}
</script>

<template>
  <div class="survey-wizard">
    <!-- Encabezado de la Encuesta -->
    <header class="wizard-header">
      <h1 class="wizard-title">{{ encuestaTitulo }}</h1>
    </header>

    <!-- Barra de progreso semántica con <nav> accesible -->
    <nav aria-label="Progreso de la encuesta" class="progress-nav">
      <div class="progress-info">
        <span class="progress-step-text">
          <strong>Paso {{ currentStepIndex + 1 }} de {{ totalSteps }}:</strong>
          {{ currentStepData.title }}
        </span>
        <span class="progress-percentage">{{ progressPercentage }}% completado</span>
      </div>

      <div
        class="progress-bar-track"
        role="progressbar"
        :aria-valuenow="progressPercentage"
        aria-valuemin="0"
        aria-valuemax="100"
        :aria-valuetext="`${progressPercentage}% completado. Paso ${currentStepIndex + 1} de ${totalSteps}`"
      >
        <div class="progress-bar-fill" :style="{ width: `${progressPercentage}%` }"></div>
      </div>

      <!-- Pasos resumidos interactivos en desktop -->
      <ol class="steps-indicators" role="list">
        <li
          v-for="(st, idx) in SURVEY_STEPS"
          :key="st.id"
          class="step-indicator-item"
          :class="{
            'is-active': idx === currentStepIndex,
            'is-completed': idx < currentStepIndex
          }"
          :aria-current="idx === currentStepIndex ? 'step' : undefined"
        >
          <button
            type="button"
            class="step-indicator-btn"
            :disabled="idx > currentStepIndex"
            :aria-label="`Paso ${idx + 1}: ${st.title}${idx < currentStepIndex ? ' (completado)' : ''}`"
            @click="goToStep(idx)"
          >
            <span class="step-num">{{ idx + 1 }}</span>
            <span class="step-short-name">{{ st.shortTitle }}</span>
          </button>
        </li>
      </ol>
    </nav>

    <!-- Contenido del Paso Activo -->
    <main class="wizard-step-content survey-card" :aria-labelledby="`step-title-${currentStepData.id}`">
      <div class="step-header">
        <h2 :id="`step-title-${currentStepData.id}`" class="step-title">
          {{ currentStepData.title }}
        </h2>
      </div>

      <div v-if="stepErrors.length > 0" class="wizard-error-banner" role="alert">
        <i class="pi pi-exclamation-circle error-banner-icon" aria-hidden="true"></i>
        <div class="error-banner-body">
          <strong>Debe completar todas las preguntas de esta sección para continuar:</strong>
          <ul>
            <li v-for="err in stepErrors" :key="err">{{ err }}</li>
          </ul>
        </div>
      </div>

      <!-- PASO 1: Ubicación y Caracterización del Hogar -->
      <section v-if="currentStepIndex === 0" class="step-form-section">
        <div class="survey-field">
          <label for="parroquia" class="survey-label">
            1.- Parroquia:
            <span class="required-indicator" aria-hidden="true">*</span>
          </label>
          <select
            id="parroquia"
            :value="modelValue.parroquia || ''"
            required
            class="survey-select"
            @blur="markTouched('parroquia')"
            @change="updateField('parroquia', ($event.target as HTMLSelectElement).value)"
          >
            <option value="" disabled selected>Seleccione su parroquia</option>
            <option v-for="p in PARROQUIAS_MATURIN" :key="p" :value="p">
              {{ formatParroquia(p) }}
            </option>
          </select>
          <span class="survey-error-msg">
            <i class="pi pi-times-circle" aria-hidden="true"></i>
            Seleccione su parroquia.
          </span>
        </div>

        <div class="survey-field">
          <label for="comunidad_sector" class="survey-label">2.- Comunidad/Sector:</label>
          <input
            id="comunidad_sector"
            :value="modelValue.comunidad_sector || ''"
            type="text"
            class="survey-input"
            placeholder="Escriba el nombre de su comunidad o sector"
            @input="updateField('comunidad_sector', ($event.target as HTMLInputElement).value)"
          />
        </div>

        <div class="survey-field">
          <label for="zona_residencia_od" class="survey-label">
            3.- Zona de residencia (según zonificación O-D):
          </label>
          <input
            id="zona_residencia_od"
            :value="modelValue.zona_residencia_od || ''"
            type="text"
            class="survey-input"
            placeholder="Escriba la zona de residencia según la zonificación O-D"
            @input="updateField('zona_residencia_od', ($event.target as HTMLInputElement).value)"
          />
        </div>

        <div class="survey-field">
          <label for="avenida_calle" class="survey-label">4.- Avenida/Calle:</label>
          <input
            id="avenida_calle"
            :value="modelValue.avenida_calle || ''"
            type="text"
            class="survey-input"
            placeholder="Escriba el nombre de la avenida o calle"
            @input="updateField('avenida_calle', ($event.target as HTMLInputElement).value)"
          />
        </div>

        <div class="survey-field">
          <label for="casa_apartamento" class="survey-label">5.- Casa/Apartamento:</label>
          <input
            id="casa_apartamento"
            :value="modelValue.casa_apartamento || ''"
            type="text"
            class="survey-input"
            placeholder="Escriba el número o nombre de la casa o apartamento"
            @input="updateField('casa_apartamento', ($event.target as HTMLInputElement).value)"
          />
        </div>
      </section>

      <!-- PASO 2: Sección II - Datos de la Vivienda -->
      <section v-else-if="currentStepIndex === 1" class="step-form-section">
        <fieldset class="survey-field survey-radio-fieldset">
          <legend class="survey-label">1.- Tipo de vivienda:</legend>
          <label v-for="op in TIPOS_VIVIENDA" :key="op.value" class="survey-radio-option">
            <input
              type="radio"
              name="tipo_vivienda"
              :value="op.value"
              :checked="modelValue.tipo_vivienda === op.value"
              @change="updateField('tipo_vivienda', op.value)"
            />
            <span>{{ op.label }}</span>
          </label>
          <div v-if="modelValue.tipo_vivienda === 'otro'" class="survey-field">
            <label for="tipo_vivienda_otro" class="survey-label">g.- Otro tipo:</label>
            <input
              id="tipo_vivienda_otro"
              :value="modelValue.tipo_vivienda_otro || ''"
              type="text"
              class="survey-input"
              placeholder="Escriba qué otro tipo de vivienda es"
              @input="updateField('tipo_vivienda_otro', ($event.target as HTMLInputElement).value)"
            />
          </div>
        </fieldset>

        <div class="survey-field">
          <label for="total_cuartos_vivienda" class="survey-label">
            2.- Contando sala, comedor, cuartos para dormir y otros cuartos ¿Cuántos cuartos tiene en total esta vivienda?
          </label>
          <span id="hint-total-cuartos" class="survey-hint">
            (No incluye baños, pasillos, balcones, cocina, ni lavaderos)
          </span>
          <input
            id="total_cuartos_vivienda"
            :value="modelValue.total_cuartos_vivienda ?? ''"
            type="number"
            inputmode="numeric"
            min="1"
            aria-describedby="hint-total-cuartos"
            class="survey-input"
            placeholder="Escriba la cantidad total de cuartos"
            @input="updateField('total_cuartos_vivienda', ($event.target as HTMLInputElement).value === '' ? '' : Number(($event.target as HTMLInputElement).value))"
          />
        </div>
      </section>

      <!-- PASO 3: Sección III - Datos del Hogar -->
      <section v-else-if="currentStepIndex === 2" class="step-form-section">
        <div class="survey-field">
          <label for="grupos_gastos_separados" class="survey-label">
            1.- ¿Cuántos grupos de personas de esta vivienda mantienen gastos separados para la comida?
          </label>
          <input
            id="grupos_gastos_separados"
            :value="modelValue.grupos_gastos_separados ?? ''"
            type="number"
            inputmode="numeric"
            min="1"
            max="20"
            class="survey-input"
            placeholder="Escriba la cantidad de grupos"
            @input="updateField('grupos_gastos_separados', ($event.target as HTMLInputElement).value === '' ? '' : Number(($event.target as HTMLInputElement).value))"
          />
        </div>

        <div class="survey-field">
          <label for="hogar_numero" class="survey-label">
            Hogar N°:
          </label>
          <input
            id="hogar_numero"
            :value="modelValue.hogar_numero ?? ''"
            type="number"
            inputmode="numeric"
            min="1"
            max="20"
            class="survey-input"
            placeholder="Escriba el número de hogar"
            @input="updateField('hogar_numero', ($event.target as HTMLInputElement).value === '' ? '' : Number(($event.target as HTMLInputElement).value))"
          />
        </div>

        <div class="survey-field">
          <label for="cuartos_dormir_hogar" class="survey-label">
            2.- ¿Cuántos cuartos para dormir utiliza este hogar?
          </label>
          <input
            id="cuartos_dormir_hogar"
            :value="modelValue.cuartos_dormir_hogar ?? ''"
            type="number"
            inputmode="numeric"
            min="1"
            max="20"
            class="survey-input"
            placeholder="Escriba la cantidad de cuartos para dormir"
            @input="updateField('cuartos_dormir_hogar', ($event.target as HTMLInputElement).value === '' ? '' : Number(($event.target as HTMLInputElement).value))"
          />
        </div>

        <div class="survey-field">
          <label for="numero_personas_hogar" class="survey-label">
            3.- Número de personas que residen en este hogar:
          </label>
          <input
            id="numero_personas_hogar"
            :value="modelValue.numero_personas_hogar ?? ''"
            type="number"
            inputmode="numeric"
            min="1"
            max="30"
            class="survey-input"
            placeholder="Escriba el número de personas que residen en este hogar"
            @input="updateField('numero_personas_hogar', ($event.target as HTMLInputElement).value === '' ? '' : Number(($event.target as HTMLInputElement).value))"
          />
        </div>

        <fieldset class="survey-field survey-radio-fieldset">
          <legend class="survey-label">4.- Para este hogar la vivienda es:</legend>
          <label v-for="op in TENENCIA_VIVIENDA" :key="op.value" class="survey-radio-option">
            <input
              type="radio"
              name="tenencia_vivienda"
              :value="op.value"
              :checked="modelValue.tenencia_vivienda === op.value"
              @change="updateField('tenencia_vivienda', op.value)"
            />
            <span>{{ op.label }}</span>
          </label>
          <div v-if="modelValue.tenencia_vivienda === 'otra_forma'" class="survey-field">
            <label for="tenencia_vivienda_otro" class="survey-label">h.- Otra forma (especifique):</label>
            <input
              id="tenencia_vivienda_otro"
              :value="modelValue.tenencia_vivienda_otro || ''"
              type="text"
              class="survey-input"
              placeholder="Escriba otra forma de tenencia"
              @input="updateField('tenencia_vivienda_otro', ($event.target as HTMLInputElement).value)"
            />
          </div>
        </fieldset>
      </section>

      <!-- PASO 4: Composición del Hogar y Residentes Habituales -->
      <section v-else-if="currentStepIndex === 3" class="step-form-section">
        <ResidentesCards
          :model-value="modelValue.residentes || []"
          :numero-personas-declarado="modelValue.numero_personas_hogar ? Number(modelValue.numero_personas_hogar) : undefined"
          @update:model-value="updateResidentes"
        />
      </section>

      <!-- PASO 5: Movilidad Cotidiana y Registro de Viajes -->
      <section v-else-if="currentStepIndex === 4" class="step-form-section">
        <ViajesMobileCards
          :model-value="modelValue.viajes || []"
          :zona-residencia-default="modelValue.zona_residencia_od || modelValue.parroquia || ''"
          :residentes="modelValue.residentes || []"
          @update:model-value="updateViajes"
        />
      </section>

      <!-- PASO 6: SECCIÓN VI: CARACTERÍSTICAS DE TRANSPORTE PÚBLICO -->
      <section v-else-if="currentStepIndex === 5" class="step-form-section">
        <h2 class="step-section-heading">SECCIÓN VI: CARACTERÍSTICAS DE TRANSPORTE PÚBLICO (SI SE UTILIZÓ EN ALGÚN VIAJE)</h2>

        <!-- Pregunta 1 -->
        <div class="survey-field">
          <label for="rutas_tp_dia" class="survey-label">
            1.- ¿Cuántas rutas de transporte público diferentes utilizó en el día?
          </label>
          <input
            id="rutas_tp_dia"
            :value="modelValue.rutas_tp_dia ?? ''"
            type="number"
            inputmode="numeric"
            min="0"
            max="20"
            class="survey-input"
            placeholder="0 si no utilizó o cantidad de rutas"
            @input="updateField('rutas_tp_dia', ($event.target as HTMLInputElement).value === '' ? '' : Number(($event.target as HTMLInputElement).value))"
          />
        </div>

        <!-- Pregunta 2 -->
        <div class="survey-field">
          <label for="tiempo_espera_paradas_min" class="survey-label">
            2.- Tiempo total de espera en las paradas (suma de todos los viajes, colocar el tiempo en minutos):
          </label>
          <input
            id="tiempo_espera_paradas_min"
            :value="modelValue.tiempo_espera_paradas_min ?? ''"
            type="number"
            inputmode="numeric"
            min="0"
            max="600"
            class="survey-input"
            placeholder="0 si no esperó o tiempo en minutos"
            @input="updateField('tiempo_espera_paradas_min', ($event.target as HTMLInputElement).value === '' ? '' : Number(($event.target as HTMLInputElement).value))"
          />
        </div>

        <!-- Pregunta 3 -->
        <div class="survey-field">
          <label for="km_residencia_parada" class="survey-label">
            3.- ¿Cuánto kilómetros aproximadamente recorrió desde su residencia hasta la parada para tomar el transporte público?
          </label>
          <input
            id="km_residencia_parada"
            :value="modelValue.km_residencia_parada ?? ''"
            type="number"
            inputmode="decimal"
            step="0.1"
            min="0"
            max="100"
            class="survey-input"
            placeholder="0 si vive al lado o distancia en kilómetros (ej. 0.5)"
            @input="updateField('km_residencia_parada', ($event.target as HTMLInputElement).value === '' ? '' : Number(($event.target as HTMLInputElement).value))"
          />
        </div>

        <!-- Pregunta 4 -->
        <fieldset class="survey-field survey-radio-fieldset">
          <legend class="survey-label">4.- ¿Ha tenido dificultades para acceder al transporte público en su zona?</legend>
          <div class="survey-radio-group horizontal">
            <label class="survey-radio-option">
              <input
                type="radio"
                name="dificultades_acceso_tp"
                value="si"
                :checked="modelValue.dificultades_acceso_tp === 'si'"
                @change="updateField('dificultades_acceso_tp', 'si')"
              />
              <span>a.- Si</span>
            </label>
            <label class="survey-radio-option">
              <input
                type="radio"
                name="dificultades_acceso_tp"
                value="no"
                :checked="modelValue.dificultades_acceso_tp === 'no'"
                @change="updateField('dificultades_acceso_tp', 'no')"
              />
              <span>b.- No</span>
            </label>
          </div>
        </fieldset>

        <!-- Pregunta 5 (Condicional si marcó 'Si' en Pregunta 4) -->
        <fieldset v-if="modelValue.dificultades_acceso_tp === 'si'" class="survey-field survey-radio-fieldset">
          <legend class="survey-label">5.- Si marcó Si, indique la principal dificultad:</legend>
          <label v-for="op in DIFICULTADES_ACCESO_TP" :key="op.value" class="survey-radio-option">
            <input
              type="radio"
              name="principal_dificultad_tp"
              :value="op.value"
              :checked="modelValue.principal_dificultad_tp === op.value"
              @change="updateField('principal_dificultad_tp', op.value)"
            />
            <span>{{ op.label }}</span>
          </label>
          <div v-if="modelValue.principal_dificultad_tp === 'otro'" class="survey-field nested-field">
            <label for="principal_dificultad_tp_otro" class="survey-label">e.- Otro (especifique):</label>
            <input
              id="principal_dificultad_tp_otro"
              :value="modelValue.principal_dificultad_tp_otro || ''"
              type="text"
              class="survey-input"
              placeholder="Describa la principal dificultad"
              @input="updateField('principal_dificultad_tp_otro', ($event.target as HTMLInputElement).value)"
            />
          </div>
        </fieldset>

        <!-- Pregunta 6 -->
        <fieldset class="survey-field survey-radio-fieldset">
          <legend class="survey-label">6.- ¿Considera que el servicio de transporte público es:</legend>
          <label v-for="op in CALIFICACION_TP" :key="op.value" class="survey-radio-option">
            <input
              type="radio"
              name="calificacion_servicio_tp"
              :value="op.value"
              :checked="modelValue.calificacion_servicio_tp === op.value"
              @change="updateField('calificacion_servicio_tp', op.value)"
            />
            <span>{{ op.label }}</span>
          </label>
        </fieldset>

        <!-- Pregunta 7 -->
        <div class="survey-field">
          <label for="gasto_semanal_transporte_bs" class="survey-label">
            7.- ¿Cuánto gasta semanalmente en transporte (todos los miembros del hogar)? (en bolívares):
          </label>
          <input
            id="gasto_semanal_transporte_bs"
            :value="modelValue.gasto_semanal_transporte_bs ?? ''"
            type="number"
            inputmode="numeric"
            min="0"
            class="survey-input"
            placeholder="0 si no posee o monto en Bs."
            @input="updateField('gasto_semanal_transporte_bs', ($event.target as HTMLInputElement).value === '' ? '' : Number(($event.target as HTMLInputElement).value))"
          />
        </div>

        <!-- Pregunta 8 -->
        <fieldset class="survey-field survey-radio-fieldset">
          <legend class="survey-label">8.- ¿Estaría usted de acuerdo en que se crean rutas directas desde su origen a su destino final?</legend>
          <label v-for="op in ACUERDO_RUTAS_DIRECTAS" :key="op.value" class="survey-radio-option">
            <input
              type="radio"
              name="acuerdo_rutas_directas"
              :value="op.value"
              :checked="modelValue.acuerdo_rutas_directas === op.value"
              @change="updateField('acuerdo_rutas_directas', op.value)"
            />
            <span>{{ op.label }}</span>
          </label>
        </fieldset>

        <!-- Pregunta 9 -->
        <div class="survey-field">
          <label for="comentarios_transporte_maturin" class="survey-label">
            9.- ¿Tiene algún comentario o sugerencia sobre el transporte en Maturín?
          </label>
          <textarea
            id="comentarios_transporte_maturin"
            :value="modelValue.comentarios_transporte_maturin || ''"
            class="survey-input survey-textarea"
            rows="3"
            placeholder="Escriba aquí sus comentarios o sugerencias..."
            @input="updateField('comentarios_transporte_maturin', ($event.target as HTMLTextAreaElement).value)"
          ></textarea>
        </div>
      </section>

      <!-- PASO 7: SECCIÓN VII: MOVILIDAD NO MOTORIZADA Y PERCEPCIÓN -->
      <section v-else-if="currentStepIndex === 6" class="step-form-section">
        <h2 class="step-section-heading">SECCIÓN VII: MOVILIDAD NO MOTORIZADA Y PERCEPCIÓN</h2>

        <!-- Pregunta 1 -->
        <fieldset class="survey-field survey-radio-fieldset">
          <legend class="survey-label">1.- ¿Ha cambiado su forma de desplazarse en los últimos 5 años?</legend>
          <div class="survey-radio-group horizontal">
            <label class="survey-radio-option">
              <input
                type="radio"
                name="cambio_movilidad_5_anos"
                value="si"
                :checked="modelValue.cambio_movilidad_5_anos === 'si'"
                @change="updateField('cambio_movilidad_5_anos', 'si')"
              />
              <span>a.- Si</span>
            </label>
            <label class="survey-radio-option">
              <input
                type="radio"
                name="cambio_movilidad_5_anos"
                value="no"
                :checked="modelValue.cambio_movilidad_5_anos === 'no'"
                @change="updateField('cambio_movilidad_5_anos', 'no')"
              />
              <span>b.- No</span>
            </label>
          </div>
        </fieldset>

        <!-- Pregunta 2 (Condicional si marcó 'Si' en Pregunta 1) -->
        <fieldset v-if="modelValue.cambio_movilidad_5_anos === 'si'" class="survey-field survey-radio-fieldset">
          <legend class="survey-label">2.- Si marcó Sí, ¿por qué motivo?</legend>
          <label v-for="op in MOTIVOS_CAMBIO_DESPLAZAMIENTO" :key="op.value" class="survey-radio-option">
            <input
              type="radio"
              name="motivo_cambio_desplazamiento"
              :value="op.value"
              :checked="modelValue.motivo_cambio_desplazamiento === op.value"
              @change="updateField('motivo_cambio_desplazamiento', op.value)"
            />
            <span>{{ op.label }}</span>
          </label>
          <div v-if="modelValue.motivo_cambio_desplazamiento === 'otro'" class="survey-field nested-field">
            <label for="motivo_cambio_desplazamiento_otro" class="survey-label">e.- Otro (especifique):</label>
            <input
              id="motivo_cambio_desplazamiento_otro"
              :value="modelValue.motivo_cambio_desplazamiento_otro || ''"
              type="text"
              class="survey-input"
              placeholder="Describa el motivo"
              @input="updateField('motivo_cambio_desplazamiento_otro', ($event.target as HTMLInputElement).value)"
            />
          </div>
        </fieldset>

        <!-- Pregunta 3 -->
        <fieldset class="survey-field survey-radio-fieldset">
          <legend class="survey-label">3.- ¿Realiza caminatas de más de 10 minutos como parte de sus desplazamientos?</legend>
          <div class="survey-radio-group horizontal">
            <label class="survey-radio-option">
              <input
                type="radio"
                name="caminatas_mas_10min"
                value="si"
                :checked="modelValue.caminatas_mas_10min === 'si'"
                @change="updateField('caminatas_mas_10min', 'si')"
              />
              <span>a.- Si</span>
            </label>
            <label class="survey-radio-option">
              <input
                type="radio"
                name="caminatas_mas_10min"
                value="no"
                :checked="modelValue.caminatas_mas_10min === 'no'"
                @change="updateField('caminatas_mas_10min', 'no')"
              />
              <span>b.- No</span>
            </label>
          </div>
        </fieldset>

        <!-- Pregunta 4 -->
        <fieldset class="survey-field survey-radio-fieldset">
          <legend class="survey-label">4.- ¿Utiliza bicicleta como medio de transporte?</legend>
          <div class="survey-radio-group horizontal">
            <label class="survey-radio-option">
              <input
                type="radio"
                name="usa_bicicleta"
                value="si"
                :checked="modelValue.usa_bicicleta === 'si'"
                @change="updateField('usa_bicicleta', 'si')"
              />
              <span>a.- Si</span>
            </label>
            <label class="survey-radio-option">
              <input
                type="radio"
                name="usa_bicicleta"
                value="no"
                :checked="modelValue.usa_bicicleta === 'no'"
                @change="updateField('usa_bicicleta', 'no')"
              />
              <span>b.- No</span>
            </label>
          </div>
        </fieldset>

        <!-- Pregunta 5 -->
        <div class="survey-field">
          <label for="dias_camina_bici_semana" class="survey-label">
            5.- ¿Cuántos días a la semana camina o usa bicicleta para desplazarse?
          </label>
          <input
            id="dias_camina_bici_semana"
            :value="modelValue.dias_camina_bici_semana ?? ''"
            type="number"
            inputmode="numeric"
            min="0"
            max="7"
            class="survey-input"
            placeholder="0 si nunca o cantidad de días (0 a 7)"
            @input="updateField('dias_camina_bici_semana', ($event.target as HTMLInputElement).value === '' ? '' : Number(($event.target as HTMLInputElement).value))"
          />
        </div>

        <!-- Pregunta 6 -->
        <fieldset class="survey-field survey-radio-fieldset">
          <legend class="survey-label">6.- ¿Realiza desplazamiento en el centro de la ciudad para hacer sus actividades o utiliza el transporte público?</legend>
          <label v-for="op in MODO_CENTRO_ACTIVIDADES" :key="op.value" class="survey-radio-option">
            <input
              type="radio"
              name="modo_actividades_centro"
              :value="op.value"
              :checked="modelValue.modo_actividades_centro === op.value"
              @change="updateField('modo_actividades_centro', op.value)"
            />
            <span>{{ op.label }}</span>
          </label>
        </fieldset>

        <!-- Pregunta 7 -->
        <fieldset class="survey-field survey-radio-fieldset">
          <legend class="survey-label">7.- ¿Considera que las aceras y espacios peatonales son adecuados?</legend>
          <div class="survey-radio-group horizontal">
            <label class="survey-radio-option">
              <input
                type="radio"
                name="aceras_adecuadas"
                value="si"
                :checked="modelValue.aceras_adecuadas === 'si'"
                @change="updateField('aceras_adecuadas', 'si')"
              />
              <span>a.- Si</span>
            </label>
            <label class="survey-radio-option">
              <input
                type="radio"
                name="aceras_adecuadas"
                value="no"
                :checked="modelValue.aceras_adecuadas === 'no'"
                @change="updateField('aceras_adecuadas', 'no')"
              />
              <span>b.- No</span>
            </label>
          </div>
        </fieldset>

        <!-- Pregunta 8 -->
        <fieldset class="survey-field survey-radio-fieldset">
          <legend class="survey-label">8.- ¿Se siente seguro al desplazarse por el centro de la ciudad?</legend>
          <label v-for="op in SEGURIDAD_CENTRO" :key="op.value" class="survey-radio-option">
            <input
              type="radio"
              name="seguridad_desplazamiento_centro"
              :value="op.value"
              :checked="modelValue.seguridad_desplazamiento_centro === op.value"
              @change="updateField('seguridad_desplazamiento_centro', op.value)"
            />
            <span>{{ op.label }}</span>
          </label>
        </fieldset>
      </section>

      <!-- PASO 8: SECCIÓN VIII: ESPARCIMIENTOS Y CIERRE -->
      <section v-else-if="currentStepIndex === 7" class="step-form-section">
        <h2 class="step-section-heading">SECCIÓN VIII: ESPARCIMIENTOS</h2>

        <!-- BLOQUE A: Parques y Espacios de Recreación -->
        <div class="survey-subsection-card">
          <h3 class="survey-subsection-title">A. Uso y Percepción de Parques y Plazas</h3>

          <!-- Pregunta 1 -->
          <fieldset class="survey-field survey-radio-fieldset">
            <legend class="survey-label">1.- ¿Con qué frecuencia visita parques, plazas u otras áreas de esparcimientos?</legend>
            <label v-for="op in FRECUENCIA_VISITA_PARQUES" :key="op.value" class="survey-radio-option">
              <input
                type="radio"
                name="frecuencia_visita_parques"
                :value="op.value"
                :checked="modelValue.frecuencia_visita_parques === op.value"
                @change="updateField('frecuencia_visita_parques', op.value)"
              />
              <span>{{ op.label }}</span>
            </label>
          </fieldset>

          <!-- Pregunta 2 (Múltiple) -->
          <fieldset class="survey-field survey-radio-fieldset">
            <legend class="survey-label">2.- ¿Qué actividad realiza principalmente en estos espacios? (admite respuestas múltiples):</legend>
            <label v-for="op in ACTIVIDADES_PARQUES" :key="op.value" class="survey-checkbox-option">
              <input
                type="checkbox"
                name="actividades_parques"
                :value="op.value"
                :checked="Array.isArray(modelValue.actividades_parques) && modelValue.actividades_parques.includes(op.value)"
                @change="toggleMultiSelect('actividades_parques', op.value)"
              />
              <span>{{ op.label }}</span>
            </label>
            <div v-if="Array.isArray(modelValue.actividades_parques) && modelValue.actividades_parques.includes('otras')" class="survey-field nested-field">
              <label for="actividades_parques_otras" class="survey-label">g.- Otras actividades (especifique):</label>
              <input
                id="actividades_parques_otras"
                :value="modelValue.actividades_parques_otras || ''"
                type="text"
                class="survey-input"
                placeholder="Especifique qué otra actividad realiza"
                @input="updateField('actividades_parques_otras', ($event.target as HTMLInputElement).value)"
              />
            </div>
          </fieldset>

          <!-- Pregunta 3 -->
          <fieldset class="survey-field survey-radio-fieldset">
            <legend class="survey-label">3.- ¿Suele hacer caminatas por la ciudad?</legend>
            <div class="survey-radio-group horizontal">
              <label v-for="op in CAMINATAS_CIUDAD" :key="op.value" class="survey-radio-option">
                <input
                  type="radio"
                  name="caminatas_ciudad"
                  :value="op.value"
                  :checked="modelValue.caminatas_ciudad === op.value"
                  @change="updateField('caminatas_ciudad', op.value)"
                />
                <span>{{ op.label }}</span>
              </label>
            </div>
          </fieldset>

          <!-- Pregunta 7 -->
          <fieldset class="survey-field survey-radio-fieldset">
            <legend class="survey-label">7.- ¿Qué tan seguro(a) se siente en parques y rutas peatonales durante el día?</legend>
            <label v-for="op in ESCALA_SEGURIDAD_PARQUES" :key="op.value" class="survey-radio-option">
              <input
                type="radio"
                name="seguridad_parques_dia"
                :value="op.value"
                :checked="modelValue.seguridad_parques_dia === op.value"
                @change="updateField('seguridad_parques_dia', op.value)"
              />
              <span>{{ op.label }}</span>
            </label>
          </fieldset>

          <!-- Pregunta 8 -->
          <fieldset class="survey-field survey-radio-fieldset">
            <legend class="survey-label">8.- ¿Qué tan seguro(a) se siente en parques y rutas peatonales durante la noche?</legend>
            <label v-for="op in ESCALA_SEGURIDAD_PARQUES" :key="op.value" class="survey-radio-option">
              <input
                type="radio"
                name="seguridad_parques_noche"
                :value="op.value"
                :checked="modelValue.seguridad_parques_noche === op.value"
                @change="updateField('seguridad_parques_noche', op.value)"
              />
              <span>{{ op.label }}</span>
            </label>
          </fieldset>

          <!-- Pregunta 9 -->
          <fieldset class="survey-field survey-radio-fieldset">
            <legend class="survey-label">9.- ¿Cómo califica la limpieza y conservación de las áreas de esparcimiento?</legend>
            <label v-for="op in CALIFICACION_LIMPIEZA" :key="op.value" class="survey-radio-option">
              <input
                type="radio"
                name="limpieza_parques"
                :value="op.value"
                :checked="modelValue.limpieza_parques === op.value"
                @change="updateField('limpieza_parques', op.value)"
              />
              <span>{{ op.label }}</span>
            </label>
          </fieldset>

          <!-- Pregunta 10 (Múltiple) -->
          <fieldset class="survey-field survey-radio-fieldset">
            <legend class="survey-label">10.- ¿Qué le impide usar más estos espacios? (admite respuestas múltiples):</legend>
            <label v-for="op in IMPEDIMENTOS_ESPACIOS" :key="op.value" class="survey-checkbox-option">
              <input
                type="checkbox"
                name="impedimentos_espacios"
                :value="op.value"
                :checked="Array.isArray(modelValue.impedimentos_espacios) && modelValue.impedimentos_espacios.includes(op.value)"
                @change="toggleMultiSelect('impedimentos_espacios', op.value)"
              />
              <span>{{ op.label }}</span>
            </label>
            <div v-if="Array.isArray(modelValue.impedimentos_espacios) && modelValue.impedimentos_espacios.includes('otras')" class="survey-field nested-field">
              <label for="impedimentos_espacios_otras" class="survey-label">f.- Otras (especifique):</label>
              <input
                id="impedimentos_espacios_otras"
                :value="modelValue.impedimentos_espacios_otras || ''"
                type="text"
                class="survey-input"
                placeholder="Especifique qué otra razón le impide usarlos"
                @input="updateField('impedimentos_espacios_otras', ($event.target as HTMLInputElement).value)"
              />
            </div>
          </fieldset>

          <!-- Pregunta 11 -->
          <fieldset class="survey-field survey-radio-fieldset">
            <legend class="survey-label">11.- ¿Qué tan satisfecho(a) está con la cantidad y calidad de áreas de esparcimiento y caminata que hay en el centro de la ciudad?</legend>
            <label v-for="op in SATISFACCION_CENTRO" :key="op.value" class="survey-radio-option">
              <input
                type="radio"
                name="satisfaccion_centro"
                :value="op.value"
                :checked="modelValue.satisfaccion_centro === op.value"
                @change="updateField('satisfaccion_centro', op.value)"
              />
              <span>{{ op.label }}</span>
            </label>
          </fieldset>

          <!-- Pregunta 12 (Múltiple) -->
          <fieldset class="survey-field survey-radio-fieldset">
            <legend class="survey-label">12.- ¿Qué mejoras deberían priorizarse? (admite respuestas múltiples):</legend>
            <label v-for="op in MEJORAS_PRIORITARIAS" :key="op.value" class="survey-checkbox-option">
              <input
                type="checkbox"
                name="mejoras_prioritarias"
                :value="op.value"
                :checked="Array.isArray(modelValue.mejoras_prioritarias) && modelValue.mejoras_prioritarias.includes(op.value)"
                @change="toggleMultiSelect('mejoras_prioritarias', op.value)"
              />
              <span>{{ op.label }}</span>
            </label>
            <div v-if="Array.isArray(modelValue.mejoras_prioritarias) && modelValue.mejoras_prioritarias.includes('otro')" class="survey-field nested-field">
              <label for="mejoras_prioritarias_otro" class="survey-label">m.- Otro (especifique):</label>
              <input
                id="mejoras_prioritarias_otro"
                :value="modelValue.mejoras_prioritarias_otro || ''"
                type="text"
                class="survey-input"
                placeholder="Describa qué otra mejora priorizar"
                @input="updateField('mejoras_prioritarias_otro', ($event.target as HTMLInputElement).value)"
              />
            </div>
          </fieldset>

          <!-- Pregunta 13 -->
          <div class="survey-field">
            <label for="parque_mejorar_primero" class="survey-label">
              13.- ¿Qué parque, plaza o ruta de esparcimiento considera que debe mejorarse primero?
            </label>
            <input
              id="parque_mejorar_primero"
              :value="modelValue.parque_mejorar_primero || ''"
              type="text"
              class="survey-input"
              placeholder="Indique el nombre del parque, plaza o sector prioritario"
              @input="updateField('parque_mejorar_primero', ($event.target as HTMLInputElement).value)"
            />
          </div>

          <!-- Pregunta 14 -->
          <fieldset class="survey-field survey-radio-fieldset">
            <legend class="survey-label">14.- ¿Estaría dispuesto(a) a participar en actividades de mejoras de estos espacios?</legend>
            <div class="survey-radio-group horizontal">
              <label v-for="op in DISPOSICION_PARTICIPAR" :key="op.value" class="survey-radio-option">
                <input
                  type="radio"
                  name="disposicion_participar_mejoras"
                  :value="op.value"
                  :checked="modelValue.disposicion_participar_mejoras === op.value"
                  @change="updateField('disposicion_participar_mejoras', op.value)"
                />
                <span>{{ op.label }}</span>
              </label>
            </div>
          </fieldset>

          <!-- Pregunta 15 -->
          <div class="survey-field">
            <label for="sugerencias_esparcimiento" class="survey-label">
              15.- ¿Qué sugerencia daría para mejorar las áreas de esparcimiento y caminatas de la ciudad?
            </label>
            <textarea
              id="sugerencias_esparcimiento"
              :value="modelValue.sugerencias_esparcimiento || ''"
              class="survey-input survey-textarea"
              rows="3"
              placeholder="Escriba aquí sus sugerencias..."
              @input="updateField('sugerencias_esparcimiento', ($event.target as HTMLTextAreaElement).value)"
            ></textarea>
          </div>
        </div>

        <!-- BLOQUE B: Aceras y Rutas de Caminata -->
        <div class="survey-subsection-card">
          <h3 class="survey-subsection-title">B. Infraestructura y Rutas de Caminata</h3>

          <!-- Pregunta 16 -->
          <fieldset class="survey-field survey-radio-fieldset">
            <legend class="survey-label">16.- ¿Considera que la acera es suficiente y cómoda para caminar?</legend>
            <label v-for="op in ACUERDO_ACERA_COMODA" :key="op.value" class="survey-radio-option">
              <input
                type="radio"
                name="acera_comoda"
                :value="op.value"
                :checked="modelValue.acera_comoda === op.value"
                @change="updateField('acera_comoda', op.value)"
              />
              <span>{{ op.label }}</span>
            </label>
          </fieldset>

          <!-- Pregunta 17 -->
          <div class="survey-field">
            <label for="sectores_para_caminar" class="survey-label">
              17.- ¿Qué sector o sectores utiliza para caminar? (Colocar los sectores):
            </label>
            <input
              id="sectores_para_caminar"
              :value="modelValue.sectores_para_caminar || ''"
              type="text"
              class="survey-input"
              placeholder="Ej: Av. Bolívar, Casco Central, Plaza Rómulo Gallegos..."
              @input="updateField('sectores_para_caminar', ($event.target as HTMLInputElement).value)"
            />
          </div>

          <!-- Pregunta 18 -->
          <fieldset class="survey-field survey-radio-fieldset">
            <legend class="survey-label">18.- ¿Qué tan fácil es llegar desde su hogar a las áreas de esparcimiento o ruta de caminata?</legend>
            <label v-for="op in FACILIDAD_LLEGADA" :key="op.value" class="survey-radio-option">
              <input
                type="radio"
                name="facilidad_llegada_parques"
                :value="op.value"
                :checked="modelValue.facilidad_llegada_parques === op.value"
                @change="updateField('facilidad_llegada_parques', op.value)"
              />
              <span>{{ op.label }}</span>
            </label>
          </fieldset>

          <!-- Pregunta 19 (Múltiple) -->
          <fieldset class="survey-field survey-radio-fieldset">
            <legend class="survey-label">19.- ¿Qué esparcimientos considera que faltan en estos espacios? (admite respuestas múltiples):</legend>
            <label v-for="op in ESPARCIMIENTOS_FALTANTES" :key="op.value" class="survey-checkbox-option">
              <input
                type="checkbox"
                name="esparcimientos_faltantes"
                :value="op.value"
                :checked="Array.isArray(modelValue.esparcimientos_faltantes) && modelValue.esparcimientos_faltantes.includes(op.value)"
                @change="toggleMultiSelect('esparcimientos_faltantes', op.value)"
              />
              <span>{{ op.label }}</span>
            </label>
            <div v-if="Array.isArray(modelValue.esparcimientos_faltantes) && modelValue.esparcimientos_faltantes.includes('otros')" class="survey-field nested-field">
              <label for="esparcimientos_faltantes_otros" class="survey-label">i.- Otros (especifique):</label>
              <input
                id="esparcimientos_faltantes_otros"
                :value="modelValue.esparcimientos_faltantes_otros || ''"
                type="text"
                class="survey-input"
                placeholder="Especifique qué otro elemento o servicio falta"
                @input="updateField('esparcimientos_faltantes_otros', ($event.target as HTMLInputElement).value)"
              />
            </div>
          </fieldset>
        </div>

        <!-- BLOQUE C: Cruces Peatonales e Intersecciones -->
        <div class="survey-subsection-card">
          <h3 class="survey-subsection-title">C. Cruces Peatonales e Intersecciones</h3>

          <!-- Pregunta 20 -->
          <fieldset class="survey-field survey-radio-fieldset">
            <legend class="survey-label">20.- ¿Existe cruce peatonal en todas las intersecciones?</legend>
            <div class="survey-radio-group horizontal">
              <label class="survey-radio-option">
                <input
                  type="radio"
                  name="cruce_peatonal_todas"
                  value="si"
                  :checked="modelValue.cruce_peatonal_todas === 'si'"
                  @change="updateField('cruce_peatonal_todas', 'si')"
                />
                <span>a.- Sí</span>
              </label>
              <label class="survey-radio-option">
                <input
                  type="radio"
                  name="cruce_peatonal_todas"
                  value="no"
                  :checked="modelValue.cruce_peatonal_todas === 'no'"
                  @change="updateField('cruce_peatonal_todas', 'no')"
                />
                <span>b.- No</span>
              </label>
            </div>
          </fieldset>

          <!-- Pregunta 21 (Si respondió Sí en P20) -->
          <fieldset v-if="modelValue.cruce_peatonal_todas === 'si'" class="survey-field survey-radio-fieldset">
            <legend class="survey-label">21.- ¿Está demarcado y visible?</legend>
            <div class="survey-radio-group horizontal">
              <label class="survey-radio-option">
                <input
                  type="radio"
                  name="cruce_demarcado_visible"
                  value="si"
                  :checked="modelValue.cruce_demarcado_visible === 'si'"
                  @change="updateField('cruce_demarcado_visible', 'si')"
                />
                <span>a.- Sí</span>
              </label>
              <label class="survey-radio-option">
                <input
                  type="radio"
                  name="cruce_demarcado_visible"
                  value="no"
                  :checked="modelValue.cruce_demarcado_visible === 'no'"
                  @change="updateField('cruce_demarcado_visible', 'no')"
                />
                <span>b.- No</span>
              </label>
            </div>
          </fieldset>

          <!-- Pregunta 22 -->
          <fieldset class="survey-field survey-radio-fieldset">
            <legend class="survey-label">22.- ¿Se siente seguro al cruzar esta intersección?</legend>
            <label v-for="op in ESCALA_SEGURIDAD_PARQUES" :key="op.value" class="survey-radio-option">
              <input
                type="radio"
                name="seguridad_cruzar_interseccion"
                :value="op.value"
                :checked="modelValue.seguridad_cruzar_interseccion === op.value"
                @change="updateField('seguridad_cruzar_interseccion', op.value)"
              />
              <span>{{ op.label }}</span>
            </label>
          </fieldset>

          <!-- Pregunta 23 -->
          <fieldset class="survey-field survey-radio-fieldset">
            <legend class="survey-label">23.- ¿Hay semáforo peatonal?</legend>
            <div class="survey-radio-group horizontal">
              <label class="survey-radio-option">
                <input
                  type="radio"
                  name="hay_semaforo_peatonal"
                  value="si"
                  :checked="modelValue.hay_semaforo_peatonal === 'si'"
                  @change="updateField('hay_semaforo_peatonal', 'si')"
                />
                <span>a.- Sí</span>
              </label>
              <label class="survey-radio-option">
                <input
                  type="radio"
                  name="hay_semaforo_peatonal"
                  value="no"
                  :checked="modelValue.hay_semaforo_peatonal === 'no'"
                  @change="updateField('hay_semaforo_peatonal', 'no')"
                />
                <span>b.- No</span>
              </label>
            </div>
          </fieldset>
        </div>

        <!-- BLOQUE D: Señalización, Accesibilidad y Entorno -->
        <div class="survey-subsection-card">
          <h3 class="survey-subsection-title">D. Señalización, Accesibilidad y Entorno Urbano</h3>

          <!-- Pregunta 24 -->
          <fieldset class="survey-field survey-radio-fieldset">
            <legend class="survey-label">24.- ¿Existen mapas peatonales, señales de destino o de caminata?</legend>
            <div class="survey-radio-group horizontal">
              <label class="survey-radio-option">
                <input
                  type="radio"
                  name="mapas_senales_caminata"
                  value="si"
                  :checked="modelValue.mapas_senales_caminata === 'si'"
                  @change="updateField('mapas_senales_caminata', 'si')"
                />
                <span>a.- Sí</span>
              </label>
              <label class="survey-radio-option">
                <input
                  type="radio"
                  name="mapas_senales_caminata"
                  value="no"
                  :checked="modelValue.mapas_senales_caminata === 'no'"
                  @change="updateField('mapas_senales_caminata', 'no')"
                />
                <span>b.- No</span>
              </label>
            </div>
          </fieldset>

          <!-- Pregunta 25 -->
          <fieldset class="survey-field survey-radio-fieldset">
            <legend class="survey-label">25.- ¿Puede una persona con movilidad reducida desplazarse sin ayuda por el centro de la ciudad?</legend>
            <div class="survey-radio-group horizontal">
              <label class="survey-radio-option">
                <input
                  type="radio"
                  name="movilidad_reducida_sin_ayuda"
                  value="si"
                  :checked="modelValue.movilidad_reducida_sin_ayuda === 'si'"
                  @change="updateField('movilidad_reducida_sin_ayuda', 'si')"
                />
                <span>a.- Sí</span>
              </label>
              <label class="survey-radio-option">
                <input
                  type="radio"
                  name="movilidad_reducida_sin_ayuda"
                  value="no"
                  :checked="modelValue.movilidad_reducida_sin_ayuda === 'no'"
                  @change="updateField('movilidad_reducida_sin_ayuda', 'no')"
                />
                <span>b.- No</span>
              </label>
            </div>
          </fieldset>

          <!-- Pregunta 26 -->
          <fieldset class="survey-field survey-radio-fieldset">
            <legend class="survey-label">26.- ¿Hay señalizaciones de nombres de calles visibles?</legend>
            <div class="survey-radio-group horizontal">
              <label class="survey-radio-option">
                <input
                  type="radio"
                  name="nombres_calles_visibles"
                  value="si"
                  :checked="modelValue.nombres_calles_visibles === 'si'"
                  @change="updateField('nombres_calles_visibles', 'si')"
                />
                <span>a.- Sí</span>
              </label>
              <label class="survey-radio-option">
                <input
                  type="radio"
                  name="nombres_calles_visibles"
                  value="no"
                  :checked="modelValue.nombres_calles_visibles === 'no'"
                  @change="updateField('nombres_calles_visibles', 'no')"
                />
                <span>b.- No</span>
              </label>
            </div>
          </fieldset>

          <!-- Pregunta 27 -->
          <fieldset class="survey-field survey-radio-fieldset">
            <legend class="survey-label">27.- ¿La señalización es clara y sin obstáculos?</legend>
            <div class="survey-radio-group horizontal">
              <label class="survey-radio-option">
                <input
                  type="radio"
                  name="senalizacion_clara_sin_obstaculos"
                  value="si"
                  :checked="modelValue.senalizacion_clara_sin_obstaculos === 'si'"
                  @change="updateField('senalizacion_clara_sin_obstaculos', 'si')"
                />
                <span>a.- Sí</span>
              </label>
              <label class="survey-radio-option">
                <input
                  type="radio"
                  name="senalizacion_clara_sin_obstaculos"
                  value="no"
                  :checked="modelValue.senalizacion_clara_sin_obstaculos === 'no'"
                  @change="updateField('senalizacion_clara_sin_obstaculos', 'no')"
                />
                <span>b.- No</span>
              </label>
            </div>
          </fieldset>

          <!-- Pregunta 28 -->
          <fieldset class="survey-field survey-radio-fieldset">
            <legend class="survey-label">28.- ¿El trayecto a pie hasta la parada es seguro?</legend>
            <label v-for="op in ESCALA_SEGURIDAD_PARQUES" :key="op.value" class="survey-radio-option">
              <input
                type="radio"
                name="trayecto_pie_parada_seguro"
                :value="op.value"
                :checked="modelValue.trayecto_pie_parada_seguro === op.value"
                @change="updateField('trayecto_pie_parada_seguro', op.value)"
              />
              <span>{{ op.label }}</span>
            </label>
          </fieldset>

          <!-- Pregunta 29 -->
          <fieldset class="survey-field survey-radio-fieldset">
            <legend class="survey-label">29.- ¿El aire y el ruido son aceptables para caminar?</legend>
            <div class="survey-radio-group horizontal">
              <label class="survey-radio-option">
                <input
                  type="radio"
                  name="aire_ruido_aceptables"
                  value="si"
                  :checked="modelValue.aire_ruido_aceptables === 'si'"
                  @change="updateField('aire_ruido_aceptables', 'si')"
                />
                <span>a.- Sí</span>
              </label>
              <label class="survey-radio-option">
                <input
                  type="radio"
                  name="aire_ruido_aceptables"
                  value="no"
                  :checked="modelValue.aire_ruido_aceptables === 'no'"
                  @change="updateField('aire_ruido_aceptables', 'no')"
                />
                <span>b.- No</span>
              </label>
            </div>
          </fieldset>

          <!-- Pregunta 30 -->
          <fieldset class="survey-field survey-radio-fieldset">
            <legend class="survey-label">30.- ¿Los conductores ceden el paso a los peatones?</legend>
            <div class="survey-radio-group horizontal">
              <label class="survey-radio-option">
                <input
                  type="radio"
                  name="conductores_ceden_paso"
                  value="si"
                  :checked="modelValue.conductores_ceden_paso === 'si'"
                  @change="updateField('conductores_ceden_paso', 'si')"
                />
                <span>a.- Sí</span>
              </label>
              <label class="survey-radio-option">
                <input
                  type="radio"
                  name="conductores_ceden_paso"
                  value="no"
                  :checked="modelValue.conductores_ceden_paso === 'no'"
                  @change="updateField('conductores_ceden_paso', 'no')"
                />
                <span>b.- No</span>
              </label>
            </div>
          </fieldset>

          <!-- Pregunta 31 -->
          <fieldset class="survey-field survey-radio-fieldset">
            <legend class="survey-label">31.- ¿Considera que la ciudad prioriza al peatón sobre el automóvil?</legend>
            <div class="survey-radio-group horizontal">
              <label class="survey-radio-option">
                <input
                  type="radio"
                  name="ciudad_prioriza_peaton"
                  value="si"
                  :checked="modelValue.ciudad_prioriza_peaton === 'si'"
                  @change="updateField('ciudad_prioriza_peaton', 'si')"
                />
                <span>a.- Sí</span>
              </label>
              <label class="survey-radio-option">
                <input
                  type="radio"
                  name="ciudad_prioriza_peaton"
                  value="no"
                  :checked="modelValue.ciudad_prioriza_peaton === 'no'"
                  @change="updateField('ciudad_prioriza_peaton', 'no')"
                />
                <span>b.- No</span>
              </label>
            </div>
          </fieldset>

          <!-- Pregunta 32 -->
          <fieldset class="survey-field survey-radio-fieldset">
            <legend class="survey-label">32.- ¿Ha participado en consultas sobre espacios peatonales?</legend>
            <div class="survey-radio-group horizontal">
              <label class="survey-radio-option">
                <input
                  type="radio"
                  name="participacion_consultas_peatonales"
                  value="si"
                  :checked="modelValue.participacion_consultas_peatonales === 'si'"
                  @change="updateField('participacion_consultas_peatonales', 'si')"
                />
                <span>a.- Sí</span>
              </label>
              <label class="survey-radio-option">
                <input
                  type="radio"
                  name="participacion_consultas_peatonales"
                  value="no"
                  :checked="modelValue.participacion_consultas_peatonales === 'no'"
                  @change="updateField('participacion_consultas_peatonales', 'no')"
                />
                <span>b.- No</span>
              </label>
            </div>
          </fieldset>

          <!-- Pregunta 33 -->
          <fieldset class="survey-field survey-radio-fieldset">
            <legend class="survey-label">33.- ¿Existen planes de movilidad peatonal, presupuesto o normativa de prioridad peatonal?</legend>
            <label v-for="op in PLANES_MOVILIDAD_PESTONAL" :key="op.value" class="survey-radio-option">
              <input
                type="radio"
                name="planes_movilidad_peatonal_normativa"
                :value="op.value"
                :checked="modelValue.planes_movilidad_peatonal_normativa === op.value"
                @change="updateField('planes_movilidad_peatonal_normativa', op.value)"
              />
              <span>{{ op.label }}</span>
            </label>
          </fieldset>
        </div>

        <!-- Observaciones Generales y Cierre -->
        <div class="survey-subsection-card">
          <h3 class="survey-subsection-title">E. Observaciones Finales y Declaración</h3>

          <div class="survey-field">
            <label for="observaciones_generales" class="survey-label">
              Observaciones o Propuestas Adicionales de Movilidad y Espacio Público:
            </label>
            <span id="hint-obs" class="survey-hint">Aporte sus comentarios para el Plan de Desarrollo Urbano Local (PDUL) de Maturín.</span>
            <textarea
              id="observaciones_generales"
              :value="modelValue.observaciones_generales || ''"
              rows="4"
              aria-describedby="hint-obs"
              class="survey-textarea"
              placeholder="Escriba aquí cualquier sugerencia de rutas, paradas, señalización o vialidad..."
              @input="updateField('observaciones_generales', ($event.target as HTMLTextAreaElement).value)"
            ></textarea>
          </div>

          <div class="survey-field declaration-field">
            <label class="declaration-label">
              <input
                type="checkbox"
                :checked="modelValue.acepta_declaracion !== false"
                @change="updateField('acepta_declaracion', ($event.target as HTMLInputElement).checked)"
              />
              <span>Declaro que la información suministrada es verídica y autorizo su tratamiento estadístico anónimo para el Plan de Desarrollo Urbano Local (PDUL) de Maturín.</span>
            </label>
          </div>
        </div>
      </section>

      <!-- Barra de Botones de Navegación del Asistente -->
      <footer class="wizard-nav-actions">
        <button
          type="button"
          class="survey-btn survey-btn-secondary"
          :disabled="currentStepIndex === 0 || submitting"
          @click="prevStep"
        >
          <i class="pi pi-arrow-left" aria-hidden="true"></i>
          <span>Anterior</span>
        </button>

        <button
          v-if="currentStepIndex < totalSteps - 1"
          type="button"
          class="survey-btn survey-btn-primary"
          :disabled="submitting"
          @click="nextStep"
        >
          <span>Siguiente</span>
          <i class="pi pi-arrow-right" aria-hidden="true"></i>
        </button>

        <button
          v-else
          type="button"
          class="survey-btn survey-btn-primary submit-final-btn"
          :disabled="submitting"
          @click="onSubmit"
        >
          <i v-if="submitting" class="pi pi-spin pi-spinner" aria-hidden="true"></i>
          <i v-else class="pi pi-check" aria-hidden="true"></i>
          <span>{{ submitting ? 'Enviando encuesta...' : 'Finalizar y Enviar Encuesta' }}</span>
        </button>
      </footer>
    </main>
  </div>
</template>

<style scoped>
.survey-wizard {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-20);
  width: 100%;
  max-width: 800px;
  margin: 0 auto;
}

.wizard-header {
  text-align: center;
  margin-block-end: var(--spacing-8);
}

.wizard-title {
  font-size: var(--text-heading-sm);
  color: var(--color-midnight-ink);
  margin: 0;
}

@media (min-width: 640px) {
  .wizard-title {
    font-size: var(--text-subheading);
  }
}

.progress-nav {
  position: sticky;
  top: 0;
  z-index: 90;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-8);
  background-color: var(--surface-card);
  padding: var(--spacing-12) var(--spacing-16);
  border-bottom: 1px solid var(--border-color);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border-radius: 0 0 var(--radius-cards) var(--radius-cards);
}

@media (max-width: 767px) {
  .progress-nav {
    top: 0;
    padding: var(--spacing-8) var(--spacing-16);
    margin-left: calc(-1 * var(--spacing-16));
    margin-right: calc(-1 * var(--spacing-16));
    border-radius: 0;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
  }

  .progress-step-text {
    font-size: 0.8125rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 70%;
  }

  .progress-percentage {
    font-size: 0.8125rem;
    white-space: nowrap;
  }
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  font-size: var(--text-body-sm);
  color: var(--text-muted);
}

.progress-step-text {
  color: var(--color-midnight-ink);
}

.progress-percentage {
  font-weight: var(--font-weight-bold);
  color: var(--color-royal-signal);
  font-family: var(--font-roboto-mono);
}

.progress-bar-track {
  width: 100%;
  height: 8px;
  background-color: var(--color-stone-divider);
  border-radius: var(--radius-buttons);
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background-color: var(--color-royal-signal);
  border-radius: var(--radius-buttons);
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.steps-indicators {
  display: none;
  list-style: none;
  grid-template-columns: repeat(8, 1fr);
  gap: var(--spacing-4);
  margin-top: var(--spacing-8);
}

@media (min-width: 768px) {
  .steps-indicators {
    display: grid;
  }
}

.step-indicator-item {
  display: flex;
}

.step-indicator-btn {
  width: 100%;
  min-block-size: var(--min-touch-target);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  background: none;
  border: 1px solid transparent;
  padding: 4px;
  cursor: pointer;
  border-radius: var(--radius-cards);
  transition: all 0.15s ease;
}

.step-num {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background-color: var(--color-fog-surface);
  color: var(--text-helper);
  font-size: 0.75rem;
  font-weight: var(--font-weight-bold);
  display: flex;
  align-items: center;
  justify-content: center;
}

.step-short-name {
  font-size: 0.7rem;
  color: var(--text-helper);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 80px;
}

.step-indicator-item.is-active .step-num {
  background-color: var(--color-royal-signal);
  color: #ffffff;
}

.step-indicator-item.is-active .step-short-name {
  color: var(--color-royal-signal);
  font-weight: var(--font-weight-bold);
}

.step-indicator-item.is-completed .step-num {
  background-color: #dbeafe;
  color: var(--color-royal-signal);
}

.wizard-error-banner {
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: var(--radius-cards);
  padding: var(--spacing-12) var(--spacing-16);
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-12);
  color: #b91c1c;
  font-size: var(--text-body-sm);
}

.error-banner-icon {
  font-size: 1.25rem;
  flex-shrink: 0;
  padding-top: 2px;
}

.error-banner-body ul {
  margin-left: var(--spacing-16);
  margin-top: var(--spacing-4);
}

.wizard-step-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-20);
}

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: var(--spacing-12);
}

.step-title {
  font-size: var(--text-subheading);
  color: var(--color-midnight-ink);
}

.step-estimated-time {
  font-size: var(--text-caption);
  color: var(--text-helper);
  display: flex;
  align-items: center;
  gap: 4px;
}

.step-form-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-16);
}

.declaration-field {
  background-color: var(--color-fog-surface);
  padding: var(--spacing-12);
  border-radius: var(--radius-cards);
}

.declaration-label {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-8);
  font-size: var(--text-body-sm);
  color: var(--color-graphite-body);
  cursor: pointer;
}

.declaration-label input {
  margin-top: 3px;
  width: 18px;
  height: 18px;
}

.wizard-nav-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid var(--border-color);
  padding-top: var(--spacing-16);
  margin-top: var(--spacing-8);
}

.submit-final-btn {
  background-color: var(--color-mint-win);
  border-color: var(--color-mint-win);
}

.submit-final-btn:hover:not(:disabled) {
  background-color: #12a826;
  border-color: #12a826;
}

.survey-radio-fieldset {
  border: none;
  padding: 0;
  margin: 0;
  min-inline-size: 0;
}

.survey-radio-option {
  display: flex;
  align-items: center;
  gap: var(--spacing-12);
  min-block-size: var(--min-touch-target);
  padding: var(--spacing-8) var(--spacing-12);
  cursor: pointer;
}

.survey-radio-option input[type='radio'] {
  inline-size: 22px;
  block-size: 22px;
  flex-shrink: 0;
  accent-color: var(--color-royal-signal);
}

.survey-checkbox-option {
  display: flex;
  align-items: center;
  gap: var(--spacing-12);
  min-block-size: var(--min-touch-target);
  padding: var(--spacing-8) var(--spacing-12);
  cursor: pointer;
  border-radius: var(--radius-interactive);
}

.survey-checkbox-option:hover {
  background-color: var(--color-fog-surface);
}

.survey-checkbox-option input[type='checkbox'] {
  inline-size: 22px;
  block-size: 22px;
  flex-shrink: 0;
  accent-color: var(--color-royal-signal);
}

.survey-subsection-card {
  background-color: #ffffff;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-cards);
  padding: var(--spacing-16);
  margin-block-end: var(--spacing-20);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-16);
}

.survey-subsection-title {
  font-size: var(--text-heading-sm);
  color: var(--color-royal-signal);
  margin: 0;
  padding-block-end: var(--spacing-8);
  border-bottom: 2px solid var(--color-fog-surface);
}
</style>
