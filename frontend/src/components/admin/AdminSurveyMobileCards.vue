<script setup lang="ts">
import type { EncuestaAdminItem } from '@/services/api';
import { formatFechaSurvey, formatTipoInstrumento } from '@/composables/useAdminSurveyList';

defineProps<{
  surveys: EncuestaAdminItem[];
  isTogglingStatus: string | null;
  exportingSurveyId: string | null;
}>();

const emit = defineEmits<{
  (e: 'toggle-status', survey: EncuestaAdminItem): void;
  (e: 'view-responses', surveyId: string): void;
  (e: 'edit-survey', surveyId: string): void;
  (e: 'export-survey', survey: EncuestaAdminItem, format: 'csv' | 'json'): void;
}>();
</script>

<template>
  <div class="mobile-cards-grid">
    <article
      v-for="s in surveys"
      :key="s.id"
      class="survey-card"
      :data-testid="`survey-card-${s.id}`"
    >
      <header class="card-header">
        <span class="type-badge">{{ formatTipoInstrumento(s.tipo_instrumento) }}</span>
        <span class="date-text">{{ formatFechaSurvey(s.creado_en) }}</span>
      </header>

      <h2 class="card-title">{{ s.titulo }}</h2>
      <code class="survey-slug-code">{{ s.slug }}</code>

      <div class="card-stats-row">
        <span class="responses-count-badge">
          <i class="pi pi-users" aria-hidden="true"></i>
          {{ s.total_respuestas }} respuestas
        </span>

        <div class="switch-cell">
          <button
            type="button"
            role="switch"
            :aria-checked="s.activa"
            :disabled="isTogglingStatus === s.id"
            class="accessible-switch"
            :class="{ 'is-active': s.activa }"
            @click="emit('toggle-status', s)"
          >
            <span class="switch-thumb"></span>
          </button>
          <span class="status-label" :class="s.activa ? 'label-active' : 'label-inactive'">
            {{ s.activa ? 'Activa' : 'Inactiva' }}
          </span>
        </div>
      </div>

      <div class="card-actions-grid">
        <button
          type="button"
          class="action-btn btn-view"
          @click="emit('view-responses', s.id)"
        >
          <i class="pi pi-table" aria-hidden="true"></i>
          <span>Respuestas</span>
        </button>

        <button
          type="button"
          class="action-btn btn-edit"
          @click="emit('edit-survey', s.id)"
        >
          <i class="pi pi-pencil" aria-hidden="true"></i>
          <span>Constructor</span>
        </button>

        <button
          type="button"
          class="action-btn btn-export"
          :disabled="exportingSurveyId === `${s.id}-csv`"
          @click="emit('export-survey', s, 'csv')"
        >
          <i class="pi pi-file-excel" aria-hidden="true"></i>
          <span>CSV</span>
        </button>

        <button
          type="button"
          class="action-btn btn-export"
          :disabled="exportingSurveyId === `${s.id}-json`"
          @click="emit('export-survey', s, 'json')"
        >
          <i class="pi pi-file" aria-hidden="true"></i>
          <span>JSON</span>
        </button>
      </div>
    </article>
  </div>
</template>

<style scoped>
.mobile-cards-grid {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-16);
}

@media (min-width: 768px) {
  .mobile-cards-grid {
    display: none;
  }
}

.survey-card {
  background-color: var(--surface-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-containers);
  padding: var(--spacing-16);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-12);
  box-shadow: var(--shadow-sm);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  margin: 0;
  font-size: var(--text-body);
  color: var(--color-midnight-ink);
  font-weight: var(--font-weight-bold);
}

.survey-slug-code {
  font-family: var(--font-roboto-mono);
  font-size: 0.75rem;
  color: var(--text-helper);
}

.type-badge {
  display: inline-block;
  background-color: var(--surface-subtle);
  color: var(--text-body-color);
  padding: var(--spacing-4) var(--spacing-8);
  border-radius: var(--radius-cards);
  font-size: var(--text-caption);
  font-weight: var(--font-weight-medium);
}

.date-text {
  color: var(--text-helper);
  font-size: var(--text-caption);
}

.responses-count-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-6);
  background-color: var(--color-lavender-wash);
  color: var(--color-royal-signal);
  font-weight: var(--font-weight-bold);
  padding: var(--spacing-4) var(--spacing-10);
  border-radius: var(--radius-pills);
  font-size: var(--text-caption);
}

.card-stats-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-8) 0;
  border-top: 1px solid var(--border-color);
  border-bottom: 1px solid var(--border-color);
}

.switch-cell {
  display: flex;
  align-items: center;
  gap: var(--spacing-8);
}

.accessible-switch {
  min-block-size: var(--min-touch-target);
  min-height: var(--min-touch-target);
  min-inline-size: var(--min-touch-target);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: var(--min-touch-target);
  background: transparent;
  border: none;
  padding: 0;
  cursor: pointer;
  position: relative;
  flex-shrink: 0;
}

.accessible-switch::before {
  content: '';
  position: absolute;
  width: 48px;
  height: 26px;
  border-radius: var(--radius-pills);
  background-color: var(--color-stone-divider);
  transition: background-color 0.2s ease;
}

.accessible-switch.is-active::before {
  background-color: var(--color-mint-win);
}

.accessible-switch:disabled {
  opacity: 0.5;
  cursor: wait;
}

.switch-thumb {
  position: relative;
  z-index: 1;
  display: block;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background-color: #ffffff;
  box-shadow: var(--shadow-sm);
  transition: transform 0.2s ease;
  transform: translateX(-11px);
}

.accessible-switch.is-active .switch-thumb {
  transform: translateX(11px);
}

.status-label {
  font-size: var(--text-caption);
  font-weight: var(--font-weight-semibold);
}

.label-active {
  color: #166534;
}

.label-inactive {
  color: var(--text-helper);
}

.card-actions-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-8);
}

.action-btn {
  min-block-size: var(--min-touch-target);
  min-height: var(--min-touch-target);
  padding: 0 var(--spacing-12);
  border-radius: var(--radius-cards);
  border: 1px solid var(--border-color);
  background-color: var(--surface-card);
  color: var(--color-midnight-ink);
  font-size: var(--text-caption);
  font-weight: var(--font-weight-semibold);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-6);
  cursor: pointer;
  transition: all 0.2s ease;
}
</style>

