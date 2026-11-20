<script setup lang="ts">
import { computed, ref } from 'vue';
import QuestionHelpTip from '@/components/common/QuestionHelpTip.vue';
import { QUESTION_HELP_TIPS } from '@/utils/questionHelpCatalog';
import {
  ACUERDO_RUTAS_DIRECTAS,
  CALIFICACION_TP,
  DIFICULTADES_ACCESO_TP,
  OPCIONES_SI_NO_SIN_TILDE,
  RUTAS_TRANSPORTE_COLECTIVO,
  RUTAS_TRANSPORTE_LABELS
} from '@/utils/surveyOptions';

const props = defineProps<{
  modelValue: Record<string, any>;
}>();

const emit = defineEmits<{
  (e: 'update-field', field: string, value: any): void;
  (e: 'toggle-multi', field: string, value: string): void;
}>();

const routeSearch = ref<string>('');

function normalizeSearchText(value: string): string {
  return value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim();
}

const isZeroRoutes = computed<boolean>(() => {
  const raw = props.modelValue.rutas_tp_dia;
  return (
    raw !== '' &&
    raw !== undefined &&
    raw !== null &&
    String(raw).trim() !== '' &&
    !Number.isNaN(Number(raw)) &&
    Number(raw) === 0
  );
});

const selectedRoutes = computed<string[]>(() => {
  const raw = props.modelValue.rutas_tp_utilizadas;
  if (Array.isArray(raw)) {
    return raw.map((item) => String(item)).filter(Boolean);
  }
  if (raw && typeof raw === 'object') {
    return Object.entries(raw as Record<string, unknown>)
      .filter(([, checked]) => Boolean(checked))
      .map(([key]) => key);
  }
  return [];
});

const filteredRoutes = computed(() => {
  const query = normalizeSearchText(routeSearch.value);
  if (!query) return RUTAS_TRANSPORTE_COLECTIVO;
  return RUTAS_TRANSPORTE_COLECTIVO.filter((ruta) => {
    const haystack = normalizeSearchText(
      `${ruta.nombre} ${ruta.modalidades.join(' ')} ${ruta.tipos_vehiculo.join(' ')}`
    );
    return haystack.includes(query);
  });
});

function isRouteSelected(code: string): boolean {
  return selectedRoutes.value.includes(code);
}

function getRouteDisplayLabel(code: string): string {
  if (code === 'otra') {
    const custom =
      typeof props.modelValue.rutas_tp_utilizadas_otra === 'string'
        ? props.modelValue.rutas_tp_utilizadas_otra.trim()
        : '';
    return custom ? `Otra: ${custom}` : 'Otra (especifique)';
  }
  return RUTAS_TRANSPORTE_LABELS[code] || code;
}

function onRutasDiaInput(event: Event) {
  const raw = (event.target as HTMLInputElement).value;
  const nextVal = raw === '' ? '' : Number(raw);
  emit('update-field', 'rutas_tp_dia', nextVal);
  if (raw !== '' && !Number.isNaN(Number(raw)) && Number(raw) === 0) {
    emit('update-field', 'rutas_tp_utilizadas', []);
    emit('update-field', 'rutas_tp_utilizadas_otra', '');
  }
}

function onToggleRoute(code: string) {
  const wasOtraChecked = isRouteSelected('otra');
  emit('toggle-multi', 'rutas_tp_utilizadas', code);
  if (code === 'otra' && wasOtraChecked) {
    emit('update-field', 'rutas_tp_utilizadas_otra', '');
  }
}
</script>

<template>
  <h2 class="step-section-heading">SECCIÓN VI: CARACTERÍSTICAS DE TRANSPORTE PÚBLICO (SI SE UTILIZÓ EN ALGÚN VIAJE)</h2>

  <div class="survey-field">
    <div class="survey-label-row">
      <label for="rutas_tp_dia" class="survey-label">
        1.- ¿Cuántas rutas de transporte público diferentes utilizó en el día?
      </label>
      <QuestionHelpTip
        :text="QUESTION_HELP_TIPS.rutas_tp_dia"
        question-label="cantidad de rutas de transporte público utilizadas"
      />
    </div>
    <input
      id="rutas_tp_dia"
      :value="modelValue.rutas_tp_dia ?? ''"
      type="number"
      inputmode="numeric"
      min="0"
      max="20"
      class="survey-input"
      placeholder="0 si no utilizó o cantidad de rutas"
      @input="onRutasDiaInput"
    />
  </div>

  <fieldset
    v-if="!isZeroRoutes"
    id="rutas_tp_utilizadas"
    tabindex="-1"
    class="survey-field survey-radio-fieldset"
  >
    <legend class="survey-label">
      <span>1.b.- ¿Qué rutas o líneas de transporte colectivo utilizó? (admite respuestas múltiples):</span>
      <QuestionHelpTip
        :text="QUESTION_HELP_TIPS.rutas_tp_utilizadas"
        question-label="rutas de transporte colectivo utilizadas"
      />
    </legend>
    <span id="rutas_tp_utilizadas_hint" class="survey-hint">
      Puede buscar por número o nombre de línea y marcar una o varias opciones. Si no está en la lista, marque «Otra».
    </span>

    <label for="rutas_tp_utilizadas_search" class="visually-hidden">
      Buscar ruta de transporte colectivo
    </label>
    <input
      id="rutas_tp_utilizadas_search"
      v-model="routeSearch"
      type="search"
      class="survey-input routes-search-input"
      aria-describedby="rutas_tp_utilizadas_hint"
      placeholder="Buscar ruta (ej. Ruta 04, Boquerón, Guaritos...)"
    />

    <div
      v-if="selectedRoutes.length > 0"
      class="selected-routes-chips"
      aria-live="polite"
      data-testid="selected-routes-chips"
    >
      <span v-for="code in selectedRoutes" :key="code" class="route-chip">
        <span class="route-chip-label">{{ getRouteDisplayLabel(code) }}</span>
        <button
          type="button"
          class="route-chip-remove"
          :aria-label="`Quitar ruta ${getRouteDisplayLabel(code)}`"
          @click="onToggleRoute(code)"
        >
          <span aria-hidden="true">×</span>
        </button>
      </span>
    </div>

    <div
      class="routes-checkbox-list"
      role="group"
      aria-label="Catálogo de rutas de transporte colectivo de Maturín"
    >
      <label
        v-for="ruta in filteredRoutes"
        :key="ruta.codigo"
        class="survey-checkbox-option route-checkbox-option"
      >
        <input
          type="checkbox"
          name="rutas_tp_utilizadas"
          :value="ruta.codigo"
          :checked="isRouteSelected(ruta.codigo)"
          @change="onToggleRoute(ruta.codigo)"
        />
        <span class="route-option-text">
          <span class="route-option-name">{{ ruta.nombre }}</span>
          <span v-if="ruta.modalidades.length > 0" class="route-option-meta">
            {{ ruta.modalidades.join(' · ') }}
          </span>
        </span>
      </label>

      <p v-if="filteredRoutes.length === 0" class="routes-empty-msg">
        No se encontraron rutas en el catálogo que coincidan con «{{ routeSearch }}». Puede marcar «Otra (especifique)» abajo.
      </p>
    </div>

    <label class="survey-checkbox-option route-otra-option">
      <input
        type="checkbox"
        name="rutas_tp_utilizadas"
        value="otra"
        :checked="isRouteSelected('otra')"
        @change="onToggleRoute('otra')"
      />
      <span>Otra (especifique)</span>
    </label>

    <div v-if="isRouteSelected('otra')" class="survey-field nested-field">
      <label for="rutas_tp_utilizadas_otra" class="survey-label">
        Especifique la otra ruta de transporte utilizada:
      </label>
      <input
        id="rutas_tp_utilizadas_otra"
        :value="modelValue.rutas_tp_utilizadas_otra || ''"
        type="text"
        class="survey-input"
        placeholder="Ej: Ruta hacia El Corozo / Línea vecinal"
        @input="emit('update-field', 'rutas_tp_utilizadas_otra', ($event.target as HTMLInputElement).value)"
      />
    </div>
  </fieldset>

  <div class="survey-field">
    <div class="survey-label-row">
      <label for="tiempo_espera_paradas_min" class="survey-label">
        2.- Tiempo total de espera en las paradas (suma de todos los viajes, colocar el tiempo en minutos):
      </label>
      <QuestionHelpTip
        :text="QUESTION_HELP_TIPS.tiempo_espera_paradas_min"
        question-label="tiempo total de espera en paradas"
      />
    </div>
    <input
      id="tiempo_espera_paradas_min"
      :value="modelValue.tiempo_espera_paradas_min ?? ''"
      type="number"
      inputmode="numeric"
      min="0"
      max="600"
      class="survey-input"
      placeholder="0 si no esperó o tiempo en minutos"
      @input="emit('update-field', 'tiempo_espera_paradas_min', ($event.target as HTMLInputElement).value === '' ? '' : Number(($event.target as HTMLInputElement).value))"
    />
  </div>

  <div class="survey-field">
    <div class="survey-label-row">
      <label for="km_residencia_parada" class="survey-label">
        3.- ¿Cuánto kilómetros aproximadamente recorrió desde su residencia hasta la parada para tomar el transporte público?
      </label>
      <QuestionHelpTip
        :text="QUESTION_HELP_TIPS.km_residencia_parada"
        question-label="distancia en kilómetros hasta la parada"
      />
    </div>
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
      @input="emit('update-field', 'km_residencia_parada', ($event.target as HTMLInputElement).value === '' ? '' : Number(($event.target as HTMLInputElement).value))"
    />
  </div>

  <fieldset class="survey-field survey-radio-fieldset">
    <legend class="survey-label">
      <span>4.- ¿Ha tenido dificultades para acceder al transporte público en su zona?</span>
      <QuestionHelpTip
        :text="QUESTION_HELP_TIPS.dificultades_acceso_tp"
        question-label="dificultades para acceder al transporte público"
      />
    </legend>
    <div class="survey-radio-group horizontal">
      <label v-for="op in OPCIONES_SI_NO_SIN_TILDE" :key="op.value" class="survey-radio-option">
        <input
          type="radio"
          name="dificultades_acceso_tp"
          :value="op.value"
          :checked="modelValue.dificultades_acceso_tp === op.value"
          @change="emit('update-field', 'dificultades_acceso_tp', op.value)"
        />
        <span>{{ op.label }}</span>
      </label>
    </div>
  </fieldset>

  <fieldset v-if="modelValue.dificultades_acceso_tp === 'si'" class="survey-field survey-radio-fieldset">
    <legend class="survey-label">
      <span>5.- Si marcó Si, indique la principal dificultad:</span>
      <QuestionHelpTip
        :text="QUESTION_HELP_TIPS.principal_dificultad_tp"
        question-label="principal dificultad de acceso al transporte público"
      />
    </legend>
    <label v-for="op in DIFICULTADES_ACCESO_TP" :key="op.value" class="survey-radio-option">
      <input
        type="radio"
        name="principal_dificultad_tp"
        :value="op.value"
        :checked="modelValue.principal_dificultad_tp === op.value"
        @change="emit('update-field', 'principal_dificultad_tp', op.value)"
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
        @input="emit('update-field', 'principal_dificultad_tp_otro', ($event.target as HTMLInputElement).value)"
      />
    </div>
  </fieldset>

  <fieldset class="survey-field survey-radio-fieldset">
    <legend class="survey-label">
      <span>6.- ¿Considera que el servicio de transporte público es:</span>
      <QuestionHelpTip
        :text="QUESTION_HELP_TIPS.calificacion_servicio_tp"
        question-label="calificación del servicio de transporte público"
      />
    </legend>
    <label v-for="op in CALIFICACION_TP" :key="op.value" class="survey-radio-option">
      <input
        type="radio"
        name="calificacion_servicio_tp"
        :value="op.value"
        :checked="modelValue.calificacion_servicio_tp === op.value"
        @change="emit('update-field', 'calificacion_servicio_tp', op.value)"
      />
      <span>{{ op.label }}</span>
    </label>
  </fieldset>

  <div class="survey-field">
    <div class="survey-label-row">
      <label for="gasto_semanal_transporte_bs" class="survey-label">
        7.- ¿Cuánto gasta semanalmente en transporte (todos los miembros del hogar)? (en bolívares):
      </label>
      <QuestionHelpTip
        :text="QUESTION_HELP_TIPS.gasto_semanal_transporte_bs"
        question-label="gasto semanal en transporte público"
      />
    </div>
    <input
      id="gasto_semanal_transporte_bs"
      :value="modelValue.gasto_semanal_transporte_bs ?? ''"
      type="number"
      inputmode="numeric"
      min="0"
      class="survey-input"
      placeholder="0 si no posee o monto en Bs."
      @input="emit('update-field', 'gasto_semanal_transporte_bs', ($event.target as HTMLInputElement).value === '' ? '' : Number(($event.target as HTMLInputElement).value))"
    />
  </div>

  <fieldset class="survey-field survey-radio-fieldset">
    <legend class="survey-label">
      <span>8.- ¿Estaría usted de acuerdo en que se crean rutas directas desde su origen a su destino final?</span>
      <QuestionHelpTip
        :text="QUESTION_HELP_TIPS.acuerdo_rutas_directas"
        question-label="acuerdo con rutas directas de transporte público"
      />
    </legend>
    <label v-for="op in ACUERDO_RUTAS_DIRECTAS" :key="op.value" class="survey-radio-option">
      <input
        type="radio"
        name="acuerdo_rutas_directas"
        :value="op.value"
        :checked="modelValue.acuerdo_rutas_directas === op.value"
        @change="emit('update-field', 'acuerdo_rutas_directas', op.value)"
      />
      <span>{{ op.label }}</span>
    </label>
  </fieldset>

  <div class="survey-field">
    <div class="survey-label-row">
      <label for="comentarios_transporte_maturin" class="survey-label">
        9.- ¿Tiene algún comentario o sugerencia sobre el transporte en Maturín?
      </label>
      <QuestionHelpTip
        :text="QUESTION_HELP_TIPS.comentarios_transporte_maturin"
        question-label="comentarios sobre el transporte en Maturín"
      />
    </div>
    <textarea
      id="comentarios_transporte_maturin"
      :value="modelValue.comentarios_transporte_maturin || ''"
      class="survey-input survey-textarea"
      rows="3"
      placeholder="Escriba aquí sus comentarios o sugerencias..."
      @input="emit('update-field', 'comentarios_transporte_maturin', ($event.target as HTMLTextAreaElement).value)"
    ></textarea>
  </div>
</template>

<style scoped>
.routes-search-input {
  margin-block-end: var(--spacing-8);
}

.selected-routes-chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-8);
  margin-block-end: var(--spacing-12);
}

.route-chip {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-6);
  background-color: var(--color-lavender-wash);
  border: 1px solid var(--color-royal-signal);
  color: var(--color-midnight-ink);
  border-radius: var(--radius-buttons);
  padding: 2px 4px 2px var(--spacing-12);
  font-size: var(--text-body-sm);
  max-width: 100%;
  box-sizing: border-box;
}

.route-chip-label {
  word-break: break-word;
  overflow-wrap: anywhere;
}

.route-chip-remove {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-inline-size: var(--min-touch-target);
  min-block-size: var(--min-touch-target);
  border: none;
  border-radius: var(--radius-buttons);
  background: transparent;
  color: var(--color-royal-signal);
  font-size: 1.25rem;
  font-weight: var(--font-weight-bold);
  cursor: pointer;
  flex-shrink: 0;
}

.route-chip-remove:hover {
  background-color: rgba(20, 90, 255, 0.12);
}

.routes-checkbox-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
  max-height: 280px;
  overflow-y: auto;
  overscroll-behavior: contain;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-inputs);
  padding: var(--spacing-8);
  background-color: var(--surface-card);
  width: 100%;
  box-sizing: border-box;
}

.route-checkbox-option {
  align-items: flex-start;
}

.route-option-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.route-option-name {
  font-size: var(--text-body-sm);
  color: var(--color-midnight-ink);
  word-break: break-word;
}

.route-option-meta {
  font-size: var(--text-caption);
  color: var(--text-helper);
}

.routes-empty-msg {
  padding: var(--spacing-12);
  font-size: var(--text-body-sm);
  color: var(--text-helper);
  margin: 0;
}

.route-otra-option {
  margin-block-start: var(--spacing-8);
  border: 1px dashed var(--border-color);
  background-color: var(--color-fog-surface);
}
</style>

