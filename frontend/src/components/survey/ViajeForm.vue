<script setup lang="ts">
import { ref, watch } from 'vue';
import type { Residente, ViajeOD } from '@/types/survey';
import { formatParroquia } from '@/utils/validation';
import {
  HORAS_12,
  MINUTOS_LIST,
  MOTIVO_OPTIONS,
  MODO_OPTIONS,
  createEmptyTripDraft,
  validateNewTripForm,
  buildTripFromDraft,
  type HoraPeriodo
} from '@/utils/tripCatalogs';

const props = withDefaults(
  defineProps<{
    residentes?: Residente[];
    sugerenciaOrigen?: string;
  }>(),
  {
    residentes: () => [],
    sugerenciaOrigen: ''
  }
);

const emit = defineEmits<{
  (e: 'agregar-viaje', viaje: Omit<ViajeOD, 'viaje_numero'>): void;
}>();

const nuevoViaje = ref<Partial<ViajeOD>>(createEmptyTripDraft(props.sugerenciaOrigen));

const horaSalidaH = ref<string>('');
const horaSalidaM = ref<string>('00');
const horaSalidaPeriodo = ref<HoraPeriodo>('AM');

const horaLlegadaH = ref<string>('');
const horaLlegadaM = ref<string>('00');
const horaLlegadaPeriodo = ref<HoraPeriodo>('AM');

const formError = ref<string>('');

watch(
  () => props.sugerenciaOrigen,
  (newVal) => {
    if (!nuevoViaje.value.zona_od_origen && newVal) {
      nuevoViaje.value.zona_od_origen = newVal;
    }
  }
);

function onAgregarViaje() {
  formError.value = '';
  const error = validateNewTripForm({
    draft: nuevoViaje.value,
    sugerenciaOrigen: props.sugerenciaOrigen,
    horaSalidaH: horaSalidaH.value,
    horaLlegadaH: horaLlegadaH.value
  });
  if (error) {
    formError.value = error;
    return;
  }

  const built = buildTripFromDraft({
    draft: nuevoViaje.value,
    sugerenciaOrigen: props.sugerenciaOrigen,
    horaSalida: {
      hora: horaSalidaH.value,
      minuto: horaSalidaM.value,
      periodo: horaSalidaPeriodo.value
    },
    horaLlegada: {
      hora: horaLlegadaH.value,
      minuto: horaLlegadaM.value,
      periodo: horaLlegadaPeriodo.value
    },
    viajeNumero: 0
  });

  const viajePayload: Omit<ViajeOD, 'viaje_numero'> = {
    persona_numero: built.persona_numero,
    origen_direccion: built.origen_direccion,
    zona_od_origen: built.zona_od_origen,
    destino_direccion: built.destino_direccion,
    zona_od_destino: built.zona_od_destino,
    hora_salida: built.hora_salida,
    hora_llegada: built.hora_llegada,
    motivo_viaje: built.motivo_viaje,
    motivo_viaje_otro: built.motivo_viaje_otro,
    modo_principal: built.modo_principal,
    modo_principal_otro: built.modo_principal_otro,
    modo_secundario: built.modo_secundario,
    modo_secundario_otro: built.modo_secundario_otro,
    tiempo_viaje_min: built.tiempo_viaje_min,
    costo_viaje_bs: built.costo_viaje_bs
  };

  emit('agregar-viaje', viajePayload);

  // Reset de horas
  horaSalidaH.value = '';
  horaSalidaM.value = '00';
  horaSalidaPeriodo.value = 'AM';
  horaLlegadaH.value = '';
  horaLlegadaM.value = '00';
  horaLlegadaPeriodo.value = 'AM';

  // Encadenar siguiente viaje: origen = destino recién agregado y campos vacíos
  nuevoViaje.value = createEmptyTripDraft(
    viajePayload.zona_od_destino,
    viajePayload.persona_numero,
    viajePayload.destino_direccion || ''
  );
}
</script>

<template>
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
          <option v-for="opt in MOTIVO_OPTIONS" :key="`motivo-${opt.codigo}`" :value="opt.codigo">
            {{ opt.nombre }}
          </option>
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
          <option v-for="opt in MODO_OPTIONS" :key="`modo-${opt.codigo}`" :value="opt.codigo">
            {{ opt.nombre }}
          </option>
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
          <option v-for="opt in MODO_OPTIONS" :key="`modosec-${opt.codigo}`" :value="opt.codigo">
            {{ opt.nombre }}
          </option>
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
</template>

<style scoped>
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
</style>
