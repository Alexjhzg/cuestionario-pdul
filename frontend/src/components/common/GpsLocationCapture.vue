<script setup lang="ts">
import { computed } from 'vue';
import { useGeolocation } from '@/composables/useGeolocation';
import QuestionHelpTip from '@/components/common/QuestionHelpTip.vue';
import { QUESTION_HELP_TIPS } from '@/utils/questionHelpCatalog';

export interface GpsPayload {
  latitude: number | null;
  longitude: number | null;
  accuracy: number | null;
  capturedAt: string | null;
}

const props = defineProps<{
  latitude?: number | null;
  longitude?: number | null;
  accuracy?: number | null;
  capturedAt?: string | null;
}>();

const emit = defineEmits<{
  (e: 'update-gps', payload: GpsPayload): void;
}>();

const { isLoading, error, getCurrentLocation, clearLocation } = useGeolocation();

const hasCoordinates = computed<boolean>(() => {
  return (
    typeof props.latitude === 'number' &&
    Number.isFinite(props.latitude) &&
    typeof props.longitude === 'number' &&
    Number.isFinite(props.longitude)
  );
});

const formattedCoords = computed<string>(() => {
  if (!hasCoordinates.value) return '';
  return `${props.latitude!.toFixed(6)}, ${props.longitude!.toFixed(6)}`;
});

const precisionBadge = computed<{ label: string; level: 'high' | 'medium' | 'low' } | null>(() => {
  if (typeof props.accuracy !== 'number' || !Number.isFinite(props.accuracy)) return null;
  const meters = Math.round(props.accuracy);
  if (meters <= 15) {
    return { label: `Excelente precisión: ±${meters} m`, level: 'high' };
  }
  if (meters <= 50) {
    return { label: `Buena precisión: ±${meters} m`, level: 'medium' };
  }
  return { label: `Precisión aproximada: ±${meters} m`, level: 'low' };
});

const openStreetMapUrl = computed<string>(() => {
  if (!hasCoordinates.value) return '#';
  const lat = props.latitude!.toFixed(6);
  const lng = props.longitude!.toFixed(6);
  return `https://www.openstreetmap.org/?mlat=${lat}&mlon=${lng}#map=17/${lat}/${lng}`;
});

const liveAnnouncement = computed<string>(() => {
  if (isLoading.value) return 'Obteniendo coordenadas satelitales GPS...';
  if (hasCoordinates.value) {
    const accText = precisionBadge.value ? `, ${precisionBadge.value.label}` : '';
    return `Ubicación GPS capturada: ${formattedCoords.value}${accText}.`;
  }
  return '';
});

async function handleCapture() {
  const result = await getCurrentLocation();
  if (result) {
    emit('update-gps', {
      latitude: result.latitude,
      longitude: result.longitude,
      accuracy: result.accuracy,
      capturedAt: result.timestamp
    });
  }
}

function handleClear() {
  clearLocation();
  emit('update-gps', {
    latitude: null,
    longitude: null,
    accuracy: null,
    capturedAt: null
  });
}
</script>

<template>
  <div class="gps-capture-container" data-testid="gps-location-capture">
    <div class="survey-label-row">
      <span class="survey-label gps-section-label">
        6.- Punto GPS de la vivienda <span class="optional-tag">(Opcional)</span>
      </span>
      <QuestionHelpTip
        :text="QUESTION_HELP_TIPS.gps_ubicacion"
        question-label="captura de coordenadas GPS de la vivienda"
      />
    </div>

    <div class="visually-hidden" role="status" aria-live="polite">
      {{ liveAnnouncement }}
    </div>

    <div v-if="!hasCoordinates" class="gps-initial-box">
      <button
        type="button"
        class="btn-gps-capture"
        :disabled="isLoading"
        data-testid="btn-gps-capture"
        @click="handleCapture"
      >
        <i
          :class="['pi', isLoading ? 'pi-spin pi-spinner' : 'pi-map-marker']"
          aria-hidden="true"
        ></i>
        <span>
          {{ isLoading ? 'Obteniendo coordenadas GPS...' : 'Capturar ubicación GPS de la vivienda' }}
        </span>
      </button>
    </div>

    <div v-else class="gps-result-card" data-testid="gps-result-card">
      <div class="gps-result-header">
        <div class="gps-coords-block">
          <span class="gps-status-dot" aria-hidden="true"></span>
          <span class="gps-coords-label">Coordenadas registradas:</span>
          <code class="gps-coords-value" data-testid="gps-coords-value">{{ formattedCoords }}</code>
        </div>

        <span
          v-if="precisionBadge"
          class="gps-precision-badge"
          :class="`precision-${precisionBadge.level}`"
          data-testid="gps-precision-badge"
        >
          <i class="pi pi-compass" aria-hidden="true"></i>
          {{ precisionBadge.label }}
        </span>
      </div>

      <div class="gps-actions-row">
        <a
          :href="openStreetMapUrl"
          target="_blank"
          rel="noopener noreferrer"
          class="gps-action-btn gps-action-link"
          data-testid="link-gps-map"
        >
          <i class="pi pi-external-link" aria-hidden="true"></i>
          <span>Ver en mapa</span>
        </a>

        <button
          type="button"
          class="gps-action-btn gps-action-recalc"
          :disabled="isLoading"
          data-testid="btn-gps-recalculate"
          @click="handleCapture"
        >
          <i
            :class="['pi', isLoading ? 'pi-spin pi-spinner' : 'pi-refresh']"
            aria-hidden="true"
          ></i>
          <span>{{ isLoading ? 'Recalculando...' : 'Recalcular' }}</span>
        </button>

        <button
          type="button"
          class="gps-action-btn gps-action-clear"
          data-testid="btn-gps-clear"
          @click="handleClear"
        >
          <i class="pi pi-trash" aria-hidden="true"></i>
          <span>Quitar</span>
        </button>
      </div>
    </div>

    <div v-if="error" class="gps-error-alert" role="alert" data-testid="gps-error-alert">
      <i class="pi pi-exclamation-triangle" aria-hidden="true"></i>
      <span>{{ error }}</span>
    </div>
  </div>
</template>

<style scoped>
.gps-capture-container {
  margin-top: var(--spacing-16, 1rem);
  padding: var(--spacing-16, 1rem);
  background-color: var(--color-lavender-wash, #f0f4fe);
  border: 1px solid rgba(20, 90, 255, 0.16);
  border-radius: var(--radius-cards, 12px);
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
}

.gps-section-label {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  font-weight: var(--font-weight-semibold, 600);
  color: var(--color-midnight-ink, #020520);
}

.optional-tag {
  font-size: 0.8125rem;
  font-weight: var(--font-weight-normal, 400);
  color: var(--color-slate-caption, #374151);
}

.gps-helper-text {
  margin: 0;
  font-size: var(--text-body-sm, 0.875rem);
  color: var(--color-slate-caption, #374151);
  line-height: 1.45;
}

.gps-initial-box {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-top: 0.25rem;
}

.btn-gps-capture {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  min-block-size: var(--min-touch-target, 48px);
  padding: 0 1.25rem;
  border-radius: var(--radius-buttons, 9999px);
  border: 1.5px solid var(--color-royal-signal, #145aff);
  background-color: var(--color-royal-signal, #145aff);
  color: #ffffff;
  font-family: var(--font-inter, inherit);
  font-size: var(--text-body-sm, 0.9375rem);
  font-weight: var(--font-weight-semibold, 600);
  cursor: pointer;
  transition: background-color 0.15s ease, transform 0.1s ease;
}

.btn-gps-capture:hover:not(:disabled) {
  background-color: #0e46d3;
}

.btn-gps-capture:focus-visible {
  outline: 3px solid var(--color-azure-focus, #0099ff);
  outline-offset: 2px;
}

.btn-gps-capture:disabled {
  opacity: 0.72;
  cursor: wait;
}

.gps-result-card {
  background-color: var(--surface-card, #ffffff);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: var(--radius-cards, 10px);
  padding: 0.875rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.gps-result-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.gps-coords-block {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.gps-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--color-mint-win, #16ca2e);
  flex-shrink: 0;
}

.gps-coords-label {
  font-size: var(--text-body-sm, 0.875rem);
  color: var(--color-slate-caption, #374151);
  font-weight: 500;
}

.gps-coords-value {
  font-family: var(--font-roboto-mono, monospace);
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--color-midnight-ink, #020520);
  background-color: var(--color-fog-surface, #f1f5f9);
  padding: 0.15rem 0.5rem;
  border-radius: 6px;
}

.gps-precision-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.25rem 0.65rem;
  border-radius: 9999px;
  font-size: 0.8125rem;
  font-weight: 600;
}

.precision-high {
  background-color: #f0fdf4;
  color: #166534;
  border: 1px solid #bbf7d0;
}

.precision-medium {
  background-color: #eff6ff;
  color: #1d4ed8;
  border: 1px solid #bfdbfe;
}

.precision-low {
  background-color: #fffbeb;
  color: #92400e;
  border: 1px solid #fde68a;
}

.gps-actions-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.gps-action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  min-block-size: var(--min-touch-target, 48px);
  padding: 0 1rem;
  border-radius: var(--radius-buttons, 9999px);
  font-family: var(--font-inter, inherit);
  font-size: 0.875rem;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
  border: 1px solid var(--border-color, #cbd5e1);
  background-color: #ffffff;
  color: var(--color-midnight-ink, #020520);
  transition: background-color 0.15s ease, border-color 0.15s ease;
}

.gps-action-btn:hover:not(:disabled) {
  background-color: var(--color-fog-surface, #f1f5f9);
}

.gps-action-btn:focus-visible {
  outline: 3px solid var(--color-azure-focus, #0099ff);
  outline-offset: 2px;
}

.gps-action-link {
  color: var(--color-royal-signal, #145aff);
  border-color: rgba(20, 90, 255, 0.3);
}

.gps-action-clear {
  color: #b91c1c;
  border-color: rgba(185, 28, 28, 0.28);
}

.gps-action-clear:hover {
  background-color: #fef2f2;
}

.gps-error-alert {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  padding: 0.75rem 0.875rem;
  border-radius: var(--radius-cards, 8px);
  background-color: #fffbeb;
  border: 1px solid #fde68a;
  color: #92400e;
  font-size: var(--text-body-sm, 0.875rem);
  line-height: 1.4;
}

.gps-error-alert i {
  margin-top: 2px;
  flex-shrink: 0;
}

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip-path: inset(50%);
  white-space: nowrap;
  border: 0;
}
</style>

