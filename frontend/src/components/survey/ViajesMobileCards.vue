<script setup lang="ts">
import { ref, computed, nextTick } from 'vue';
import { useToast } from 'primevue/usetoast';
import type { ViajeOD, Residente } from '@/types/survey';
import { formatParroquia } from '@/utils/validation';

const props = withDefaults(
  defineProps<{
    modelValue: ViajeOD[];
    zonaResidenciaDefault?: string;
    residentes?: Residente[];
  }>(),
  {
    modelValue: () => [],
    zonaResidenciaDefault: '',
    residentes: () => []
  }
);

const emit = defineEmits<{
  (e: 'update:modelValue', viajes: ViajeOD[]): void;
  (e: 'agregar-regreso', viajeRegreso: ViajeOD): void;
  (e: 'eliminar', index: number): void;
}>();

// Inyección segura de ToastService para notificaciones sutiles
let toast: ReturnType<typeof useToast> | null = null;
try {
  toast = useToast();
} catch {
  toast = null;
}

// Referencia al contenedor de la sección para scroll suave
const sectionRef = ref<HTMLElement | null>(null);

// Calcular origen inteligente: si hay viajes, el último destino; si no, la residencia
const sugerenciaOrigen = computed(() => {
  if (props.modelValue.length > 0) {
    const ultimo = props.modelValue[props.modelValue.length - 1];
    return formatParroquia(ultimo.zona_od_destino) || formatParroquia(props.zonaResidenciaDefault) || '';
  }
  return formatParroquia(props.zonaResidenciaDefault) || '';
});

function getNombreResidente(num: number): string {
  if (props.residentes && props.residentes.length > 0) {
    const r = props.residentes.find((item) => item.persona_numero === num);
    if (r) {
      return r.nombres || r.nombre_apellido || `Persona #${num}`;
    }
  }
  return `Persona #${num}`;
}

const MOTIVOS_VIAJE: Record<string, string> = {
  '1': 'Trabajo',
  '2': 'Estudio',
  '3': 'Compras',
  '4': 'Salud',
  '5': 'Recreación',
  '6': 'Trámites',
  '7': 'Visita Familiar',
  '8': 'Otro'
};

const MODOS_TRANSPORTE: Record<string, string> = {
  '1': 'A pie',
  '2': 'Bicicleta',
  '3': 'Motocicleta',
  '4': 'Automóvil Particular',
  '5': 'Taxi',
  '6': 'Transporte público (bus, buseta)',
  '7': 'Transporte informal (por puesto, mototaxi)',
  '8': 'Otro'
};

// R5: Estado inicial en blanco y sin valores predeterminados
const nuevoViaje = ref<Partial<ViajeOD>>({
  persona_numero: undefined,
  origen_direccion: '',
  zona_od_origen: sugerenciaOrigen.value,
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
});

// Horas y minutos para formato 12 horas (AM/PM)
const HORAS_12 = Array.from({ length: 12 }, (_, i) => String(i + 1).padStart(2, '0'));
const MINUTOS_LIST = ['00', '05', '10', '15', '20', '25', '30', '35', '40', '45', '50', '55'];

const horaSalidaH = ref<string>('');
const horaSalidaM = ref<string>('00');
const horaSalidaPeriodo = ref<'AM' | 'PM'>('AM');

const horaLlegadaH = ref<string>('');
const horaLlegadaM = ref<string>('00');
const horaLlegadaPeriodo = ref<'AM' | 'PM'>('AM');

function getHoraFormateada(hora: string, minuto: string, periodo: 'AM' | 'PM'): string {
  const h = hora.trim();
  if (!h) return '';
  const m = (minuto || '00').padStart(2, '0');
  return `${h}:${m} ${periodo}`;
}

const formError = ref<string>('');

function isBlankValue(value: unknown): boolean {
  return value === undefined || value === null || (typeof value === 'string' && value.trim().length === 0);
}

async function onAgregarViaje() {
  formError.value = '';
  const origen = (nuevoViaje.value.zona_od_origen || sugerenciaOrigen.value).trim();
  const destino = (nuevoViaje.value.zona_od_destino || '').trim();
  const origenDireccion = (nuevoViaje.value.origen_direccion || '').trim();
  const destinoDireccion = (nuevoViaje.value.destino_direccion || '').trim();

  if (isBlankValue(nuevoViaje.value.persona_numero) || Number(nuevoViaje.value.persona_numero) < 1) {
    formError.value = 'Por favor seleccione la persona que realizó el viaje.';
    return;
  }
  if (!origenDireccion) {
    formError.value = 'Por favor indique la dirección o referencia de origen.';
    return;
  }
  if (!origen) {
    formError.value = 'Por favor indique la zona o parroquia de origen.';
    return;
  }
  if (!destinoDireccion) {
    formError.value = 'Por favor indique la dirección o referencia de destino.';
    return;
  }
  if (!destino) {
    formError.value = 'Por favor indique la zona o parroquia de destino.';
    return;
  }
  if (!horaSalidaH.value) {
    formError.value = 'Por favor indique la hora de salida.';
    return;
  }
  if (!horaLlegadaH.value) {
    formError.value = 'Por favor indique la hora de llegada.';
    return;
  }
  if (!nuevoViaje.value.motivo_viaje) {
    formError.value = 'Por favor seleccione el motivo del viaje.';
    return;
  }
  if (nuevoViaje.value.motivo_viaje === '8' && !String(nuevoViaje.value.motivo_viaje_otro || '').trim()) {
    formError.value = 'Por favor especifique el otro motivo del viaje.';
    return;
  }
  if (!nuevoViaje.value.modo_principal) {
    formError.value = 'Por favor seleccione el modo de transporte principal.';
    return;
  }
  if (nuevoViaje.value.modo_principal === '8' && !String(nuevoViaje.value.modo_principal_otro || '').trim()) {
    formError.value = 'Por favor especifique el otro modo de transporte principal.';
    return;
  }
  if (nuevoViaje.value.modo_secundario === '8' && !String(nuevoViaje.value.modo_secundario_otro || '').trim()) {
    formError.value = 'Por favor especifique el otro modo de transporte secundario.';
    return;
  }
  if (
    isBlankValue(nuevoViaje.value.tiempo_viaje_min) ||
    isNaN(Number(nuevoViaje.value.tiempo_viaje_min)) ||
    Number(nuevoViaje.value.tiempo_viaje_min) < 1
  ) {
    formError.value = 'Por favor indique el tiempo de viaje en minutos.';
    return;
  }
  if (
    isBlankValue(nuevoViaje.value.costo_viaje_bs) ||
    isNaN(Number(nuevoViaje.value.costo_viaje_bs)) ||
    Number(nuevoViaje.value.costo_viaje_bs) < 0
  ) {
    formError.value = 'Por favor indique el costo del viaje (puede ser 0).';
    return;
  }

  const horaSalidaFinal = getHoraFormateada(horaSalidaH.value, horaSalidaM.value, horaSalidaPeriodo.value);
  const horaLlegadaFinal = getHoraFormateada(horaLlegadaH.value, horaLlegadaM.value, horaLlegadaPeriodo.value);

  const viaje: ViajeOD = {
    viaje_numero: props.modelValue.length + 1,
    persona_numero: Number(nuevoViaje.value.persona_numero),
    origen_direccion: origenDireccion,
    zona_od_origen: origen,
    destino_direccion: destinoDireccion,
    zona_od_destino: destino,
    hora_salida: horaSalidaFinal,
    hora_llegada: horaLlegadaFinal,
    motivo_viaje: String(nuevoViaje.value.motivo_viaje),
    motivo_viaje_otro: nuevoViaje.value.motivo_viaje === '8' ? (nuevoViaje.value.motivo_viaje_otro || '').trim() : undefined,
    modo_principal: String(nuevoViaje.value.modo_principal),
    modo_principal_otro: nuevoViaje.value.modo_principal === '8' ? (nuevoViaje.value.modo_principal_otro || '').trim() : undefined,
    modo_secundario: nuevoViaje.value.modo_secundario ? String(nuevoViaje.value.modo_secundario) : undefined,
    modo_secundario_otro: nuevoViaje.value.modo_secundario === '8' ? (nuevoViaje.value.modo_secundario_otro || '').trim() : undefined,
    tiempo_viaje_min: Number(nuevoViaje.value.tiempo_viaje_min),
    costo_viaje_bs: Number(nuevoViaje.value.costo_viaje_bs)
  };

  const actualizados = [...props.modelValue, viaje];
  emit('update:modelValue', actualizados);

  // R2: Disparo de notificación Toast sutil superior
  try {
    if (toast && typeof toast.add === 'function') {
      toast.add({
        severity: 'success',
        summary: 'Viaje Registrado',
        detail: 'Trayecto agregado correctamente.',
        life: 3000
      });
    }
  } catch {
    // Silencioso en modo headless
  }

  // R3: Desplazamiento automático al inicio de la sección de viajes
  await nextTick();
  if (sectionRef.value && typeof sectionRef.value.scrollIntoView === 'function') {
    sectionRef.value.scrollIntoView({ behavior: 'smooth', block: 'start' });
  } else if (typeof window !== 'undefined' && typeof window.scrollTo === 'function') {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // Reset de horas
  horaSalidaH.value = '';
  horaSalidaM.value = '00';
  horaSalidaPeriodo.value = 'AM';
  horaLlegadaH.value = '';
  horaLlegadaM.value = '00';
  horaLlegadaPeriodo.value = 'AM';

  // Encadenar siguiente viaje: origen = destino recién agregado y campos vacíos
  nuevoViaje.value = {
    persona_numero: viaje.persona_numero,
    origen_direccion: viaje.destino_direccion || '',
    zona_od_origen: viaje.zona_od_destino,
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

async function agregarViajeRegreso(viajeIda: ViajeOD) {
  const regreso: ViajeOD = {
    viaje_numero: props.modelValue.length + 1,
    persona_numero: viajeIda.persona_numero,
    zona_od_origen: viajeIda.zona_od_destino,
    zona_od_destino: props.zonaResidenciaDefault || viajeIda.zona_od_origen,
    motivo_viaje: viajeIda.motivo_viaje,
    modo_principal: viajeIda.modo_principal,
    tiempo_viaje_min: viajeIda.tiempo_viaje_min,
    costo_viaje_bs: viajeIda.costo_viaje_bs
  };

  if (viajeIda.destino_direccion) regreso.origen_direccion = viajeIda.destino_direccion;
  if (viajeIda.origen_direccion) regreso.destino_direccion = viajeIda.origen_direccion;
  if (viajeIda.hora_salida) regreso.hora_salida = viajeIda.hora_salida;
  if (viajeIda.hora_llegada) regreso.hora_llegada = viajeIda.hora_llegada;
  if (viajeIda.motivo_viaje_otro) regreso.motivo_viaje_otro = viajeIda.motivo_viaje_otro;
  if (viajeIda.modo_principal_otro) regreso.modo_principal_otro = viajeIda.modo_principal_otro;
  if (viajeIda.modo_secundario) regreso.modo_secundario = viajeIda.modo_secundario;
  if (viajeIda.modo_secundario_otro) regreso.modo_secundario_otro = viajeIda.modo_secundario_otro;

  const actualizados = [...props.modelValue, regreso];
  emit('agregar-regreso', regreso);
  emit('update:modelValue', actualizados);

  // R2: Disparo de notificación Toast sutil superior
  try {
    if (toast && typeof toast.add === 'function') {
      toast.add({
        severity: 'success',
        summary: 'Viaje Registrado',
        detail: 'Viaje de regreso a casa agregado correctamente.',
        life: 3000
      });
    }
  } catch {
    // Silencioso en modo headless
  }

  // R3: Desplazamiento automático al inicio de la sección de viajes
  await nextTick();
  if (sectionRef.value && typeof sectionRef.value.scrollIntoView === 'function') {
    sectionRef.value.scrollIntoView({ behavior: 'smooth', block: 'start' });
  } else if (typeof window !== 'undefined' && typeof window.scrollTo === 'function') {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
}

function eliminarViaje(index: number) {
  emit('eliminar', index);
  const actualizados = props.modelValue.filter((_, idx) => idx !== index).map((v, i) => ({
    ...v,
    viaje_numero: i + 1
  }));
  emit('update:modelValue', actualizados);
}

// Modal para ver detalles completos del viaje
const viajeSeleccionado = ref<ViajeOD | null>(null);
const modalDetallesAbierto = ref<boolean>(false);

function verDetallesViaje(v: ViajeOD) {
  viajeSeleccionado.value = v;
  modalDetallesAbierto.value = true;
}

function cerrarModalDetalles() {
  modalDetallesAbierto.value = false;
  viajeSeleccionado.value = null;
}
</script>

<template>
  <div ref="sectionRef" class="viajes-section" aria-labelledby="titulo-viajes-od">
    <div class="viajes-header">
      <h3 id="titulo-viajes-od" class="viajes-title">
        Registro de Viajes Cotidianos ({{ modelValue.length }})
      </h3>
      <p class="viajes-subtitle">
        SECCIÓN V: REGISTRO GENERAL DE VIAJES (Para todos los miembros del hogar mayores de 5 años)
      </p>
      <p class="viajes-desc">
        Instrucciones: Registrar los viajes realizados el día anterior (día laboral típico), entendiendo por viaje un desplazamiento de un punto de origen a un punto de destino con un propósito determinado.
      </p>
    </div>

    <!-- Lista de tarjetas resumidas adaptadas a móvil (360px sin overflow) -->
    <div v-if="modelValue.length > 0" class="viajes-list" role="list">
      <article
        v-for="(v, idx) in modelValue"
        :key="v.viaje_numero"
        class="viaje-card"
        role="listitem"
      >
        <div class="viaje-card-badge">
          <span>Viaje #{{ idx + 1 }}</span>
          <span class="persona-tag">{{ getNombreResidente(v.persona_numero) }}</span>
        </div>

        <div class="viaje-route">
          <div class="route-point">
            <i class="pi pi-map-marker origin-icon" aria-hidden="true"></i>
            <span class="route-label">Origen:</span>
            <strong class="route-value">{{ formatParroquia(v.zona_od_origen) }}</strong>
          </div>
          <div class="route-arrow" aria-hidden="true">
            <i class="pi pi-arrow-down"></i>
          </div>
          <div class="route-point">
            <i class="pi pi-flag destination-icon" aria-hidden="true"></i>
            <span class="route-label">Destino:</span>
            <strong class="route-value">{{ formatParroquia(v.zona_od_destino) }}</strong>
          </div>
        </div>

        <div class="viaje-details">
          <span><i class="pi pi-compass" aria-hidden="true"></i> {{ MOTIVOS_VIAJE[v.motivo_viaje] || 'Otro' }}</span>
          <span><i class="pi pi-car" aria-hidden="true"></i> {{ MODOS_TRANSPORTE[v.modo_principal] || 'Transporte' }}</span>
          <span><i class="pi pi-clock" aria-hidden="true"></i> {{ v.tiempo_viaje_min }} min</span>
          <span v-if="v.costo_viaje_bs > 0"><i class="pi pi-money-bill" aria-hidden="true"></i> Bs. {{ v.costo_viaje_bs }}</span>
        </div>

        <div class="viaje-acciones">
          <button
            type="button"
            class="action-btn details-btn"
            :aria-label="`Ver todos los detalles del viaje ${idx + 1}`"
            @click="verDetallesViaje(v)"
          >
            <i class="pi pi-eye" aria-hidden="true"></i>
            <span>Ver más</span>
          </button>

          <button
            type="button"
            class="action-btn return-btn"
            :aria-label="`Agregar viaje de regreso a casa para el viaje ${idx + 1} desde ${formatParroquia(v.zona_od_destino)}`"
            @click="agregarViajeRegreso(v)"
          >
            <i class="pi pi-refresh" aria-hidden="true"></i>
            <span>Agregar viaje de regreso a casa</span>
          </button>

          <button
            type="button"
            class="action-btn delete-btn"
            :aria-label="`Eliminar viaje ${idx + 1} de ${formatParroquia(v.zona_od_origen)} a ${formatParroquia(v.zona_od_destino)}`"
            @click="eliminarViaje(idx)"
          >
            <i class="pi pi-trash" aria-hidden="true"></i>
            <span>Eliminar</span>
          </button>
        </div>
      </article>
    </div>

    <div v-else class="empty-state">
      <i class="pi pi-compass empty-icon" aria-hidden="true"></i>
      <p>Aún no se han registrado viajes. Use el formulario a continuación para agregar el primer trayecto.</p>
    </div>

    <!-- Formulario para agregar un nuevo viaje -->
    <fieldset class="nuevo-viaje-form">
      <legend class="nuevo-viaje-legend">
        <i class="pi pi-plus-circle" aria-hidden="true"></i>
        <span>Agregar Nuevo Trayecto</span>
      </legend>

      <div v-if="formError" class="form-error-banner" role="alert">
        <i class="pi pi-exclamation-triangle" aria-hidden="true"></i>
        <span>{{ formError }}</span>
      </div>

      <div class="grid-inputs">
        <div class="survey-field field-persona">
          <label class="survey-label" for="viaje-persona">
            Persona (N°):
          </label>
          <select
            v-if="residentes && residentes.length > 0"
            id="viaje-persona"
            v-model.number="nuevoViaje.persona_numero"
            class="survey-select"
          >
            <option :value="undefined" disabled selected>-- Seleccione el residente que viajó --</option>
            <option
              v-for="r in residentes"
              :key="r.persona_numero"
              :value="r.persona_numero"
            >
              Persona #{{ r.persona_numero }}: {{ r.nombres || r.nombre_apellido || 'Residente' }}
            </option>
          </select>
          <input
            v-else
            id="viaje-persona"
            v-model.number="nuevoViaje.persona_numero"
            type="number"
            min="1"
            class="survey-input"
            placeholder="Ej: 1 (número del residente que viajó)"
          />
        </div>

        <div class="survey-field">
          <label class="survey-label" for="viaje-origen-dir">
            Origen (Dirección o referencia):
          </label>
          <input
            id="viaje-origen-dir"
            v-model="nuevoViaje.origen_direccion"
            type="text"
            class="survey-input"
            placeholder="Ej: Av. Bolívar, frente a la plaza"
          />
        </div>

        <div class="survey-field">
          <label class="survey-label" for="viaje-origen">
            Zona O-D origen:
          </label>
          <span id="hint-origen" class="survey-hint">Prellenado automáticamente</span>
          <input
            id="viaje-origen"
            v-model="nuevoViaje.zona_od_origen"
            type="text"
            aria-describedby="hint-origen"
            class="survey-input"
            :placeholder="sugerenciaOrigen ? formatParroquia(sugerenciaOrigen) : 'Ej: Alto de Los Godos'"
          />
        </div>

        <div class="survey-field">
          <label class="survey-label" for="viaje-destino-dir">
            Destino (Dirección referencia):
          </label>
          <input
            id="viaje-destino-dir"
            v-model="nuevoViaje.destino_direccion"
            type="text"
            class="survey-input"
            placeholder="Ej: Calle Monagas, C.C. Petroriente"
          />
        </div>

        <div class="survey-field">
          <label class="survey-label" for="viaje-destino">
            Zona O-D destino:
            <span class="required-indicator" aria-hidden="true">*</span>
          </label>
          <span id="hint-destino" class="survey-hint">Indique la zona o sector de llegada</span>
          <input
            id="viaje-destino"
            v-model="nuevoViaje.zona_od_destino"
            type="text"
            required
            aria-describedby="hint-destino"
            class="survey-input"
            placeholder="Ej: San Simón"
          />
        </div>

        <div class="horarios-grid-row">
          <div class="survey-field">
            <label class="survey-label" for="viaje-hora-salida-h">
              Hora de salida:
            </label>
            <div class="hora-input-group">
              <select
                id="viaje-hora-salida-h"
                v-model="horaSalidaH"
                class="survey-select hora-num-select"
                aria-label="Hora de salida"
              >
                <option value="" disabled selected>Hora</option>
                <option v-for="h in HORAS_12" :key="`sh-${h}`" :value="h">{{ h }}</option>
              </select>
              <span class="hora-colon" aria-hidden="true">:</span>
              <select
                id="viaje-hora-salida-m"
                v-model="horaSalidaM"
                class="survey-select hora-num-select"
                aria-label="Minutos de salida"
              >
                <option v-for="m in MINUTOS_LIST" :key="`sm-${m}`" :value="m">{{ m }}</option>
              </select>
              <select
                id="viaje-hora-salida-periodo"
                v-model="horaSalidaPeriodo"
                class="survey-select hora-periodo-select"
                aria-label="Período de salida"
              >
                <option value="AM">AM</option>
                <option value="PM">PM</option>
              </select>
            </div>
          </div>

          <div class="survey-field">
            <label class="survey-label" for="viaje-hora-llegada-h">
              Hora de llegada:
            </label>
            <div class="hora-input-group">
              <select
                id="viaje-hora-llegada-h"
                v-model="horaLlegadaH"
                class="survey-select hora-num-select"
                aria-label="Hora de llegada"
              >
                <option value="" disabled selected>Hora</option>
                <option v-for="h in HORAS_12" :key="`lh-${h}`" :value="h">{{ h }}</option>
              </select>
              <span class="hora-colon" aria-hidden="true">:</span>
              <select
                id="viaje-hora-llegada-m"
                v-model="horaLlegadaM"
                class="survey-select hora-num-select"
                aria-label="Minutos de llegada"
              >
                <option v-for="m in MINUTOS_LIST" :key="`lm-${m}`" :value="m">{{ m }}</option>
              </select>
              <select
                id="viaje-hora-llegada-periodo"
                v-model="horaLlegadaPeriodo"
                class="survey-select hora-periodo-select"
                aria-label="Período de llegada"
              >
                <option value="AM">AM</option>
                <option value="PM">PM</option>
              </select>
            </div>
          </div>
        </div>

        <div class="survey-field">
          <label class="survey-label" for="viaje-motivo">
            Motivo del viaje:
          </label>
          <select id="viaje-motivo" v-model="nuevoViaje.motivo_viaje" class="survey-select">
            <option value="" disabled selected>-- Seleccione el motivo del viaje --</option>
            <option value="1">Trabajo</option>
            <option value="2">Estudio</option>
            <option value="3">Compras</option>
            <option value="4">Salud</option>
            <option value="5">Recreación</option>
            <option value="6">Trámites</option>
            <option value="7">Visita Familiar</option>
            <option value="8">Otro</option>
          </select>
        </div>

        <div v-if="nuevoViaje.motivo_viaje === '8'" class="survey-field">
          <label class="survey-label" for="viaje-motivo-otro">
            Especifique otro motivo:
          </label>
          <input
            id="viaje-motivo-otro"
            v-model="nuevoViaje.motivo_viaje_otro"
            type="text"
            class="survey-input"
            placeholder="Escriba el motivo del viaje"
          />
        </div>

        <div class="survey-field">
          <label class="survey-label" for="viaje-modo">
            Modo principal:
          </label>
          <select id="viaje-modo" v-model="nuevoViaje.modo_principal" class="survey-select">
            <option value="" disabled selected>-- Seleccione el modo de transporte principal --</option>
            <option value="1">A pie</option>
            <option value="2">Bicicleta</option>
            <option value="3">Motocicleta</option>
            <option value="4">Automóvil Particular</option>
            <option value="5">Taxi</option>
            <option value="6">Transporte público (bus, buseta)</option>
            <option value="7">Transporte informal (por puesto, mototaxi)</option>
            <option value="8">Otro</option>
          </select>
        </div>

        <div v-if="nuevoViaje.modo_principal === '8'" class="survey-field">
          <label class="survey-label" for="viaje-modo-otro">
            Especifique otro modo principal:
          </label>
          <input
            id="viaje-modo-otro"
            v-model="nuevoViaje.modo_principal_otro"
            type="text"
            class="survey-input"
            placeholder="Escriba el modo de transporte principal"
          />
        </div>

        <div class="survey-field">
          <label class="survey-label" for="viaje-modo-sec">
            Modo secundario:
          </label>
          <select id="viaje-modo-sec" v-model="nuevoViaje.modo_secundario" class="survey-select">
            <option value="" selected>Ninguno / No aplica</option>
            <option value="1">A pie</option>
            <option value="2">Bicicleta</option>
            <option value="3">Motocicleta</option>
            <option value="4">Automóvil Particular</option>
            <option value="5">Taxi</option>
            <option value="6">Transporte público (bus, buseta)</option>
            <option value="7">Transporte informal (por puesto, mototaxi)</option>
            <option value="8">Otro</option>
          </select>
        </div>

        <div v-if="nuevoViaje.modo_secundario === '8'" class="survey-field">
          <label class="survey-label" for="viaje-modo-sec-otro">
            Especifique otro modo secundario:
          </label>
          <input
            id="viaje-modo-sec-otro"
            v-model="nuevoViaje.modo_secundario_otro"
            type="text"
            class="survey-input"
            placeholder="Escriba el modo de transporte secundario"
          />
        </div>

        <div class="survey-field">
          <label class="survey-label" for="viaje-tiempo">
            Tiempo de viaje (min):
          </label>
          <input
            id="viaje-tiempo"
            v-model.number="nuevoViaje.tiempo_viaje_min"
            type="number"
            min="1"
            class="survey-input"
            placeholder="Ej: 30 (duración en minutos)"
          />
        </div>

        <div class="survey-field">
          <label class="survey-label" for="viaje-costo">
            Costo del Viaje (Bs):
          </label>
          <input
            id="viaje-costo"
            v-model.number="nuevoViaje.costo_viaje_bs"
            type="number"
            min="0"
            step="0.5"
            class="survey-input"
            placeholder="0 si no posee o no aplica"
          />
        </div>
      </div>

      <button
        type="button"
        class="survey-btn survey-btn-primary add-viaje-btn"
        @click="onAgregarViaje"
      >
        <i class="pi pi-plus" aria-hidden="true"></i>
        <span>Agregar este viaje</span>
      </button>
    </fieldset>

    <!-- Modal accesible con los detalles completos del viaje -->
    <div
      v-if="modalDetallesAbierto && viajeSeleccionado"
      class="modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-viaje-title"
      @click.self="cerrarModalDetalles"
      @keydown.esc="cerrarModalDetalles"
    >
      <div class="modal-card">
        <header class="modal-header">
          <h4 id="modal-viaje-title" class="modal-title">
            Detalles del Viaje #{{ viajeSeleccionado.viaje_numero }}
          </h4>
          <button
            type="button"
            class="modal-close-btn"
            aria-label="Cerrar modal de detalles"
            @click="cerrarModalDetalles"
          >
            <i class="pi pi-times" aria-hidden="true"></i>
          </button>
        </header>

        <div class="modal-body">
          <div class="detail-row">
            <span class="detail-label">Residente:</span>
            <span class="detail-value">{{ getNombreResidente(viajeSeleccionado.persona_numero) }}</span>
          </div>

          <div class="detail-divider"></div>

          <div class="detail-row">
            <span class="detail-label">Zona O-D Origen:</span>
            <strong class="detail-value">{{ formatParroquia(viajeSeleccionado.zona_od_origen) }}</strong>
          </div>
          <div v-if="viajeSeleccionado.origen_direccion" class="detail-row">
            <span class="detail-label">Dirección origen:</span>
            <span class="detail-value">{{ viajeSeleccionado.origen_direccion }}</span>
          </div>

          <div class="detail-divider"></div>

          <div class="detail-row">
            <span class="detail-label">Zona O-D Destino:</span>
            <strong class="detail-value">{{ formatParroquia(viajeSeleccionado.zona_od_destino) }}</strong>
          </div>
          <div v-if="viajeSeleccionado.destino_direccion" class="detail-row">
            <span class="detail-label">Dirección destino:</span>
            <span class="detail-value">{{ viajeSeleccionado.destino_direccion }}</span>
          </div>

          <div class="detail-divider"></div>

          <div class="detail-row detail-horarios-row">
            <div class="horario-col">
              <span class="detail-label">Hora de salida:</span>
              <strong class="detail-value">{{ viajeSeleccionado.hora_salida || 'No especificada' }}</strong>
            </div>
            <div class="horario-arrow" aria-hidden="true">➔</div>
            <div class="horario-col">
              <span class="detail-label">Hora de llegada:</span>
              <strong class="detail-value">{{ viajeSeleccionado.hora_llegada || 'No especificada' }}</strong>
            </div>
          </div>

          <div class="detail-divider"></div>

          <div class="detail-row">
            <span class="detail-label">Motivo del viaje:</span>
            <span class="detail-value">
              {{ MOTIVOS_VIAJE[viajeSeleccionado.motivo_viaje] || 'Otro' }}
              <span v-if="viajeSeleccionado.motivo_viaje_otro"> ({{ viajeSeleccionado.motivo_viaje_otro }})</span>
            </span>
          </div>

          <div class="detail-row">
            <span class="detail-label">Modo principal:</span>
            <span class="detail-value">
              {{ MODOS_TRANSPORTE[viajeSeleccionado.modo_principal] || 'Otro' }}
              <span v-if="viajeSeleccionado.modo_principal_otro"> ({{ viajeSeleccionado.modo_principal_otro }})</span>
            </span>
          </div>

          <div v-if="viajeSeleccionado.modo_secundario" class="detail-row">
            <span class="detail-label">Modo secundario:</span>
            <span class="detail-value">
              {{ MODOS_TRANSPORTE[viajeSeleccionado.modo_secundario] || 'Otro' }}
              <span v-if="viajeSeleccionado.modo_secundario_otro"> ({{ viajeSeleccionado.modo_secundario_otro }})</span>
            </span>
          </div>

          <div class="detail-divider"></div>

          <div class="detail-row">
            <span class="detail-label">Tiempo de viaje:</span>
            <span class="detail-value">{{ viajeSeleccionado.tiempo_viaje_min }} minutos</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Costo del viaje:</span>
            <span class="detail-value">Bs. {{ viajeSeleccionado.costo_viaje_bs }}</span>
          </div>
        </div>

        <footer class="modal-footer">
          <button
            type="button"
            class="survey-btn survey-btn-secondary"
            @click="cerrarModalDetalles"
          >
            Cerrar
          </button>
        </footer>
      </div>
    </div>
  </div>
</template>

<style scoped>
.viajes-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-16);
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
}

.viajes-title {
  font-size: var(--text-subheading);
  color: var(--color-midnight-ink);
  margin-block-end: var(--spacing-4);
}

.viajes-desc {
  font-size: var(--text-body-sm);
  color: var(--text-helper);
  line-height: 1.4;
}

.viajes-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-12);
  width: 100%;
}

.viaje-card {
  background-color: var(--surface-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-cards);
  padding: var(--spacing-16);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-12);
  box-shadow: var(--shadow-sm);
  box-sizing: border-box;
}

.viaje-card-badge {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: var(--text-caption);
  font-weight: var(--font-weight-bold);
  color: var(--color-royal-signal);
}

.persona-tag {
  background-color: var(--color-lavender-wash);
  color: var(--color-royal-signal);
  padding: 2px 8px;
  border-radius: var(--radius-buttons);
}

.viaje-route {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-6);
  background-color: var(--color-fog-surface);
  padding: var(--spacing-10);
  border-radius: var(--radius-cards);
}

.route-point {
  display: flex;
  align-items: center;
  gap: var(--spacing-6);
  font-size: var(--text-body-sm);
}

.origin-icon {
  color: var(--color-royal-signal);
}

.destination-icon {
  color: var(--color-coral-lost);
}

.route-arrow {
  padding-left: 20px;
  font-size: 0.75rem;
  color: var(--text-helper);
}

.viaje-details {
  display: flex;
  gap: var(--spacing-16);
  font-size: var(--text-body-sm);
  color: var(--text-muted);
}

.viaje-acciones {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-8);
  margin-top: var(--spacing-4);
}

@media (min-width: 480px) {
  .viaje-acciones {
    flex-direction: row;
    align-items: center;
  }
}

.action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-6);
  padding: 8px 14px;
  min-block-size: var(--min-touch-target);
  min-inline-size: var(--min-touch-target);
  border-radius: var(--radius-buttons);
  font-size: var(--text-body-sm);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  border: 1px solid var(--border-color);
  background-color: var(--surface-card);
  transition: all 0.15s ease;
}

.details-btn {
  background-color: var(--color-fog-surface);
  color: var(--color-midnight-ink);
  border-color: var(--border-color);
}

.details-btn:hover {
  background-color: #e2e8f0;
}

.return-btn {
  background-color: var(--color-lavender-wash);
  color: var(--color-royal-signal);
  border-color: #c7d7fe;
  flex: 1;
}

.return-btn:hover {
  background-color: #e0ebfe;
}

.delete-btn {
  color: var(--color-coral-lost);
  border-color: #fecaca;
  background-color: #fef2f2;
}

.delete-btn:hover {
  background-color: #fee2e2;
}

.empty-state {
  text-align: center;
  padding: var(--spacing-24);
  background-color: var(--color-fog-surface);
  border-radius: var(--radius-cards);
  color: var(--text-helper);
  font-size: var(--text-body-sm);
}

.empty-icon {
  font-size: 2rem;
  margin-block-end: var(--spacing-8);
  display: block;
  color: var(--text-helper);
}

.nuevo-viaje-form {
  border: 1px solid var(--border-color);
  border-radius: var(--radius-containers);
  padding: var(--spacing-16);
  background-color: var(--surface-card);
  margin-top: var(--spacing-8);
}

.nuevo-viaje-legend {
  font-weight: var(--font-weight-bold);
  font-size: var(--text-body);
  color: var(--color-midnight-ink);
  padding: 0 var(--spacing-8);
  display: flex;
  align-items: center;
  gap: var(--spacing-6);
}

.grid-inputs {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--spacing-12);
  margin-top: var(--spacing-12);
}

@media (min-width: 600px) {
  .grid-inputs {
    grid-template-columns: repeat(2, 1fr);
  }

  .field-persona {
    grid-column: 1 / -1;
  }
}

.horarios-grid-row {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-12);
  align-items: start;
  width: 100%;
}

.horarios-grid-row .survey-field {
  margin-block-end: 0;
}

.horarios-grid-row .survey-label {
  min-height: 1.5rem;
  display: flex;
  align-items: center;
}

.form-error-banner {
  background-color: #fef2f2;
  color: #b91c1c;
  padding: var(--spacing-8) var(--spacing-12);
  border-radius: var(--radius-cards);
  font-size: var(--text-body-sm);
  display: flex;
  align-items: center;
  gap: var(--spacing-8);
  margin-block-end: var(--spacing-12);
}

.hora-input-group {
  display: flex;
  gap: var(--spacing-4);
  align-items: center;
  width: 100%;
}

.hora-num-select {
  flex: 1 1 0;
  min-width: 0;
  padding: 0.5rem 0.25rem;
  text-align: center;
}

.hora-colon {
  font-weight: bold;
  color: var(--color-midnight-ink);
  flex-shrink: 0;
  margin: 0 1px;
}

.hora-periodo-select {
  flex: 0 0 54px;
  min-width: 48px;
  padding: 0.5rem 0.25rem;
  text-align: center;
}

@media (max-width: 480px) {
  .horarios-grid-row {
    gap: var(--spacing-8);
  }

  .hora-input-group {
    gap: 2px;
  }

  .hora-num-select,
  .hora-periodo-select {
    padding: 0.5rem 2px;
    font-size: var(--text-body-sm);
  }

  .hora-periodo-select {
    flex: 0 0 46px;
    min-width: 42px;
  }
}

.add-viaje-btn {
  width: 100%;
  margin-top: var(--spacing-12);
}

/* Modal de detalles de viaje */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: var(--spacing-16);
  box-sizing: border-box;
}

.modal-card {
  background-color: var(--surface-card);
  border-radius: var(--radius-containers);
  width: 100%;
  max-width: 520px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-md);
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-16) var(--spacing-20);
  border-bottom: 1px solid var(--border-color);
  background-color: var(--color-fog-surface);
}

.modal-title {
  font-size: var(--text-body);
  font-weight: var(--font-weight-bold);
  color: var(--color-midnight-ink);
  margin: 0;
}

.modal-close-btn {
  background: transparent;
  border: none;
  font-size: 1.125rem;
  color: var(--text-helper);
  cursor: pointer;
  padding: var(--spacing-6);
  border-radius: var(--radius-buttons);
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-close-btn:hover {
  background-color: rgba(0, 0, 0, 0.05);
  color: var(--color-midnight-ink);
}

.modal-body {
  padding: var(--spacing-20);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-10);
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--spacing-12);
  font-size: var(--text-body-sm);
}

.detail-horarios-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--spacing-8);
  background-color: var(--color-fog-surface);
  padding: var(--spacing-8) var(--spacing-12);
  border-radius: var(--radius-buttons);
}

.horario-col {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.horario-col .detail-label {
  font-size: var(--text-caption);
  color: var(--text-helper);
}

.horario-col .detail-value {
  font-weight: var(--font-weight-bold);
  color: var(--color-midnight-ink);
  text-align: left;
}

.horario-arrow {
  color: var(--color-royal-signal);
  font-size: 1.1rem;
  font-weight: bold;
}

.detail-label {
  color: var(--text-helper);
  flex-shrink: 0;
}

.detail-value {
  color: var(--color-midnight-ink);
  text-align: right;
  word-break: break-word;
}

.detail-divider {
  height: 1px;
  background-color: var(--border-color);
  margin: var(--spacing-4) 0;
}

.modal-footer {
  padding: var(--spacing-12) var(--spacing-20);
  border-top: 1px solid var(--border-color);
  display: flex;
  justify-content: flex-end;
  background-color: var(--color-fog-surface);
}
</style>
