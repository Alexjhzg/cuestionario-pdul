<script setup lang="ts">
import { ref, computed, watch, nextTick, onBeforeUnmount } from 'vue';
import { useToast } from 'primevue/usetoast';
import { SURVEY_STEPS, type Residente, type ViajeOD } from '@/types/survey';
import {
  calculateStepProgress,
  getStepValidationErrors,
  type StepValidationError
} from '@/utils/surveyStepValidation';
import { hasPublicTransitTrips } from '@/utils/tripCatalogs';
import ViajesMobileCards from './ViajesMobileCards.vue';
import ResidentesCards from './ResidentesCards.vue';
import Step1Ubicacion from './sections/Step1Ubicacion.vue';
import Step2Vivienda from './sections/Step2Vivienda.vue';
import Step3Hogar from './sections/Step3Hogar.vue';
import Step6TransportePublico from './sections/Step6TransportePublico.vue';
import Step7MovilidadActiva from './sections/Step7MovilidadActiva.vue';
import Step8Esparcimiento from './sections/Step8Esparcimiento.vue';
import Step9Peatones from './sections/Step9Peatones.vue';

let toast: ReturnType<typeof useToast> | null = null;
try {
  toast = useToast();
} catch {
  // Entorno de prueba unitaria sin Provide/Inject
}

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
    encuestaTitulo: 'Encuesta Origen-Destino Maturín (PDUL)'
  }
);

const emit = defineEmits<{
  (e: 'update:modelValue', data: Record<string, any>): void;
  (e: 'update:step', step: number): void;
  (e: 'submit', data: Record<string, any>): void;
}>();

const localStep = ref<number>(props.step);
const currentStepIndex = computed({
  get: () => (props.step !== undefined ? props.step : localStep.value),
  set: (val: number) => {
    localStep.value = val;
    emit('update:step', val);
  }
});

const totalSteps = SURVEY_STEPS.length;
const stepWeight = 100 / totalSteps;

const progressPercentage = computed(() => {
  const data = props.modelValue || {};
  const currentStep = currentStepIndex.value;
  const baseProgress = currentStep * stepWeight;
  const currentStepProgress = calculateStepProgress(currentStep, data) * stepWeight;
  return Math.min(100, Math.round((baseProgress + currentStepProgress) * 10) / 10);
});

const currentStepData = computed(() => SURVEY_STEPS[currentStepIndex.value] || SURVEY_STEPS[0]);
const stepErrorItems = ref<StepValidationError[]>([]);
const stepErrors = computed(() => stepErrorItems.value.map((item) => item.message));
const touchedFields = ref<Record<string, boolean>>({});
const residentesCardsRef = ref<{ resetDraft?: () => void } | null>(null);
const viajesCardsRef = ref<{ resetDraft?: () => void } | null>(null);
let highlightTimer: ReturnType<typeof setTimeout> | null = null;
let lastHighlightedEl: HTMLElement | null = null;

function clearFieldHighlight() {
  if (highlightTimer !== null) {
    clearTimeout(highlightTimer);
    highlightTimer = null;
  }
  if (lastHighlightedEl) {
    lastHighlightedEl.classList.remove('missing-field-highlight');
    lastHighlightedEl = null;
  }
}

function findFieldElement(field: string): HTMLElement | null {
  if (typeof document === 'undefined' || !field) return null;

  if (field === 'comunidad_sector') {
    const otherInput = document.getElementById('comunidad_sector_otro');
    if (otherInput) return otherInput;
  }
  if (field === 'gps_ubicacion') {
    return document.querySelector<HTMLElement>('[data-testid="gps-location-capture"]');
  }
  if (field === 'residentes') {
    return (
      document.getElementById('residente-nombre') ||
      document.querySelector<HTMLElement>('.residentes-cards')
    );
  }
  if (field === 'viajes') {
    return (
      document.getElementById('viaje-persona') ||
      document.querySelector<HTMLElement>('.viajes-mobile-cards')
    );
  }

  const byId = document.getElementById(field);
  if (byId) return byId;

  const escaped =
    typeof CSS !== 'undefined' && typeof CSS.escape === 'function'
      ? CSS.escape(field)
      : field.replace(/"/g, '\\"');
  return document.querySelector<HTMLElement>(`[name="${escaped}"]`);
}

async function focusMissingQuestion(field: string) {
  await nextTick();
  const target = findFieldElement(field);
  if (!target) return;

  const container =
    (target.closest('.survey-field, fieldset, .gps-capture-container') as HTMLElement | null) ||
    target;

  if (typeof container.scrollIntoView === 'function') {
    container.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  clearFieldHighlight();
  container.classList.add('missing-field-highlight');
  lastHighlightedEl = container;
  highlightTimer = setTimeout(() => {
    clearFieldHighlight();
  }, 2400);

  if (typeof target.focus === 'function') {
    try {
      target.focus({ preventScroll: true });
    } catch {
      target.focus();
    }
  }
}

onBeforeUnmount(() => {
  clearFieldHighlight();
});

watch(
  () => props.modelValue,
  () => {
    if (stepErrorItems.value.length > 0) stepErrorItems.value = [];
  },
  { deep: true }
);

function markTouched(fieldName: string) {
  touchedFields.value[fieldName] = true;
}

let pendingModelPatch: Record<string, any> | null = null;

function updateField(field: string, value: any) {
  const base = pendingModelPatch ?? props.modelValue;
  pendingModelPatch = { ...base, [field]: value };
  emit('update:modelValue', pendingModelPatch);
  queueMicrotask(() => {
    pendingModelPatch = null;
  });
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
  if (idx >= 0) current.splice(idx, 1);
  else current.push(val);
  updateField(field, current);
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
  stepErrorItems.value = getStepValidationErrors(currentStepIndex.value, props.modelValue || {});
  if (stepErrorItems.value.length > 0) {
    showValidationErrors(stepErrors.value);
    void focusMissingQuestion(stepErrorItems.value[0].field);
    return false;
  }
  return true;
}

const isStep6Applicable = computed<boolean>(() => {
  const data = props.modelValue || {};
  const trips = Array.isArray(data.viajes) ? data.viajes : [];
  if (trips.length === 0) return true;
  return hasPublicTransitTrips(trips);
});

const visibleSteps = computed(() => {
  return SURVEY_STEPS;
});

function cleanCurrentStepTransientFields() {
  if (currentStepIndex.value === 3) {
    residentesCardsRef.value?.resetDraft?.();
  } else if (currentStepIndex.value === 4) {
    viajesCardsRef.value?.resetDraft?.();
  }
}

function nextStep() {
  if (validateCurrentStep() && currentStepIndex.value < totalSteps - 1) {
    cleanCurrentStepTransientFields();
    let nextIdx = currentStepIndex.value + 1;
    // Opción A: Si el paso siguiente es la Sección VI (índice 5) y no aplica por no haber usado transporte público, saltar al paso 6
    if (nextIdx === 5 && !isStep6Applicable.value) {
      nextIdx = 6;
    }
    currentStepIndex.value = Math.min(nextIdx, totalSteps - 1);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
}

function prevStep() {
  if (currentStepIndex.value > 0) {
    stepErrorItems.value = [];
    let prevIdx = currentStepIndex.value - 1;
    // Si al retroceder llegamos a la Sección VI (índice 5) y no aplica, retroceder directo al paso 4 (Viajes)
    if (prevIdx === 5 && !isStep6Applicable.value) {
      prevIdx = 4;
    }
    currentStepIndex.value = Math.max(0, prevIdx);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
}

function goToStep(targetIndex: number) {
  if (targetIndex < currentStepIndex.value) {
    stepErrorItems.value = [];
    if (targetIndex === 5 && !isStep6Applicable.value) {
      targetIndex = 4;
    }
    currentStepIndex.value = targetIndex;
  } else if (targetIndex === currentStepIndex.value + 1) {
    nextStep();
  }
}

const STEP6_PUBLIC_TRANSIT_FIELDS = [
  'rutas_tp_dia',
  'rutas_tp_utilizadas',
  'rutas_tp_utilizadas_otra',
  'tiempo_espera_paradas_min',
  'km_residencia_parada',
  'dificultades_acceso_tp',
  'principal_dificultad_tp',
  'principal_dificultad_tp_otro',
  'calificacion_servicio_tp',
  'gasto_semanal_transporte_bs',
  'acuerdo_rutas_directas',
  'comentarios_transporte_maturin'
] as const;

async function onSubmit() {
  const data = props.modelValue || {};
  for (let idx = 0; idx < totalSteps; idx++) {
    const errors = getStepValidationErrors(idx, data);
    if (errors.length > 0) {
      stepErrorItems.value = errors;
      if (currentStepIndex.value !== idx) {
        currentStepIndex.value = idx;
      }
      showValidationErrors(
        errors.map((e) => e.message),
        'Complete todas las preguntas de la encuesta'
      );
      await focusMissingQuestion(errors[0].field);
      return;
    }
  }
  stepErrorItems.value = [];
  const payload: Record<string, any> = { ...data };
  if (!isStep6Applicable.value) {
    for (const field of STEP6_PUBLIC_TRANSIT_FIELDS) {
      delete payload[field];
    }
  }
  emit('submit', payload);
}
</script>

<template>
  <div class="survey-wizard">
    <header class="wizard-header">
      <h1 class="wizard-title">{{ encuestaTitulo }}</h1>
    </header>

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

      <ol class="steps-indicators" role="list">
        <li
          v-for="(st, idx) in visibleSteps"
          :key="st.id"
          class="step-indicator-item"
          :class="{
            'is-active': idx === currentStepIndex,
            'is-completed': idx < currentStepIndex,
            'is-skipped': idx === 5 && !isStep6Applicable
          }"
          :aria-current="idx === currentStepIndex ? 'step' : undefined"
        >
          <button
            type="button"
            class="step-indicator-btn"
            :disabled="idx > currentStepIndex || (idx === 5 && !isStep6Applicable)"
            :aria-label="`Paso ${idx + 1}: ${st.title}${idx === 5 && !isStep6Applicable ? ' (no aplica)' : idx < currentStepIndex ? ' (completado)' : ''}`"
            @click="goToStep(idx)"
          >
            <span class="step-num">{{ idx + 1 }}</span>
            <span class="step-short-name">
              {{ st.shortTitle }}
              <small v-if="idx === 5 && !isStep6Applicable" class="step-tag-na">(N/A)</small>
            </span>
          </button>
        </li>
      </ol>
    </nav>

    <main class="wizard-step-content survey-card" :aria-labelledby="`step-title-${currentStepData.id}`">
      <div class="step-header">
        <h2 :id="`step-title-${currentStepData.id}`" class="step-title">
          {{ currentStepData.title }}
        </h2>
      </div>

      <div v-if="stepErrorItems.length > 0" class="wizard-error-banner" role="alert">
        <i class="pi pi-exclamation-circle error-banner-icon" aria-hidden="true"></i>
        <div class="error-banner-body">
          <strong>Debe completar todas las preguntas de esta sección para continuar (pulse cualquiera para ir directo):</strong>
          <ul class="error-jump-list">
            <li v-for="(err, idx) in stepErrorItems" :key="`${err.field}-${idx}`">
              <button
                type="button"
                class="error-jump-btn"
                data-testid="btn-jump-missing-field"
                @click="focusMissingQuestion(err.field)"
              >
                <span>{{ err.message }}</span>
                <i class="pi pi-arrow-down-right error-jump-icon" aria-hidden="true"></i>
              </button>
            </li>
          </ul>
        </div>
      </div>

      <section v-if="currentStepIndex === 0" class="step-form-section">
        <Step1Ubicacion :model-value="modelValue" @update-field="updateField" @mark-touched="markTouched" />
      </section>

      <section v-else-if="currentStepIndex === 1" class="step-form-section">
        <Step2Vivienda :model-value="modelValue" @update-field="updateField" />
      </section>

      <section v-else-if="currentStepIndex === 2" class="step-form-section">
        <Step3Hogar :model-value="modelValue" @update-field="updateField" />
      </section>

      <section v-else-if="currentStepIndex === 3" class="step-form-section">
        <ResidentesCards
          ref="residentesCardsRef"
          :model-value="modelValue.residentes || []"
          :numero-personas-declarado="modelValue.numero_personas_hogar ? Number(modelValue.numero_personas_hogar) : undefined"
          @update:model-value="updateResidentes"
        />
      </section>

      <section v-else-if="currentStepIndex === 4" class="step-form-section">
        <ViajesMobileCards
          ref="viajesCardsRef"
          :model-value="modelValue.viajes || []"
          :zona-residencia-default="modelValue.zona_residencia_od || modelValue.parroquia || ''"
          :residentes="modelValue.residentes || []"
          @update:model-value="updateViajes"
        />
      </section>

      <section v-else-if="currentStepIndex === 5" class="step-form-section">
        <Step6TransportePublico
          :model-value="modelValue"
          @update-field="updateField"
          @toggle-multi="toggleMultiSelect"
        />
      </section>

      <section v-else-if="currentStepIndex === 6" class="step-form-section">
        <Step7MovilidadActiva :model-value="modelValue" @update-field="updateField" />
      </section>

      <section v-else-if="currentStepIndex === 7" class="step-form-section">
        <Step8Esparcimiento
          :model-value="modelValue"
          @update-field="updateField"
          @toggle-multi="toggleMultiSelect"
        />
      </section>

      <section v-else-if="currentStepIndex === 8" class="step-form-section">
        <Step9Peatones
          :model-value="modelValue"
          @update-field="updateField"
        />
      </section>

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
          <span>{{ submitting ? 'Enviando encuesta...' : 'Enviar Encuesta' }}</span>
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

.error-banner-body ul.error-jump-list {
  list-style: none;
  margin: var(--spacing-8) 0 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.error-jump-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  width: 100%;
  text-align: left;
  padding: 0.35rem 0.5rem;
  border: 1px solid rgba(185, 28, 28, 0.22);
  border-radius: 6px;
  background-color: rgba(255, 255, 255, 0.72);
  color: #991b1b;
  font-family: inherit;
  font-size: var(--text-body-sm);
  cursor: pointer;
  transition: background-color 0.15s ease, border-color 0.15s ease;
}

.error-jump-btn:hover {
  background-color: #ffffff;
  border-color: #dc2626;
  text-decoration: underline;
}

.error-jump-btn:focus-visible {
  outline: 3px solid var(--color-azure-focus, #0099ff);
  outline-offset: 2px;
}

.error-jump-icon {
  font-size: 0.75rem;
  margin-left: auto;
  flex-shrink: 0;
}

:deep(.missing-field-highlight) {
  border-radius: var(--radius-cards, 10px);
  box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.45);
  background-color: rgba(254, 242, 242, 0.55);
  transition: box-shadow 0.25s ease, background-color 0.25s ease;
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

.step-form-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-16);
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
</style>
