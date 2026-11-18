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
  <div class="desktop-table-wrapper" role="region" aria-label="Tabla de encuestas registradas" tabindex="0">
    <table class="admin-table">
      <caption class="sr-only">Listado de encuestas con estado y opciones de exportación</caption>
      <thead>
        <tr>
          <th scope="col">Título y Slug</th>
          <th scope="col">Tipo</th>
          <th scope="col">Fecha</th>
          <th scope="col">Respuestas</th>
          <th scope="col">Disponibilidad</th>
          <th scope="col">Acciones</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="s in surveys" :key="s.id" class="survey-row" :data-testid="`survey-row-${s.id}`">
          <td class="col-title">
            <span class="survey-title-text">{{ s.titulo }}</span>
            <code class="survey-slug-code">{{ s.slug }}</code>
          </td>
          <td>
            <span class="type-badge">{{ formatTipoInstrumento(s.tipo_instrumento) }}</span>
          </td>
          <td>
            <span class="date-text">{{ formatFechaSurvey(s.creado_en) }}</span>
          </td>
          <td>
            <span class="responses-count-badge" :data-testid="`total-respuestas-${s.id}`">
              <i class="pi pi-users" aria-hidden="true"></i>
              {{ s.total_respuestas }}
            </span>
          </td>
          <td>
            <div class="switch-cell">
              <button
                type="button"
                role="switch"
                :aria-checked="s.activa"
                :disabled="isTogglingStatus === s.id"
                class="accessible-switch"
                :class="{ 'is-active': s.activa }"
                :aria-label="`Alternar estado de ${s.titulo}. Actualmente ${s.activa ? 'activa' : 'inactiva'}`"
                @click="emit('toggle-status', s)"
                :data-testid="`switch-status-${s.id}`"
              >
                <span class="switch-thumb"></span>
              </button>
              <span class="status-label" :class="s.activa ? 'label-active' : 'label-inactive'">
                {{ s.activa ? 'Activa' : 'Inactiva' }}
              </span>
            </div>
          </td>
          <td>
            <div class="row-actions">
              <button
                type="button"
                class="action-btn btn-view"
                aria-label="Ver respuestas ciudadanas"
                @click="emit('view-responses', s.id)"
                :data-testid="`btn-view-responses-${s.id}`"
              >
                <i class="pi pi-table" aria-hidden="true"></i>
                <span>Respuestas</span>
              </button>

              <button
                type="button"
                class="action-btn btn-edit"
                aria-label="Abrir en Constructor"
                @click="emit('edit-survey', s.id)"
                :data-testid="`btn-edit-survey-${s.id}`"
              >
                <i class="pi pi-pencil" aria-hidden="true"></i>
                <span>Constructor</span>
              </button>

              <button
                type="button"
                class="action-btn btn-export"
                :disabled="exportingSurveyId === `${s.id}-csv`"
                aria-label="Exportar respuestas en CSV"
                @click="emit('export-survey', s, 'csv')"
                :data-testid="`btn-export-csv-${s.id}`"
              >
                <i v-if="exportingSurveyId === `${s.id}-csv`" class="pi pi-spin pi-spinner"></i>
                <i v-else class="pi pi-file-excel"></i>
                <span>CSV</span>
              </button>

              <button
                type="button"
                class="action-btn btn-export"
                :disabled="exportingSurveyId === `${s.id}-json`"
                aria-label="Exportar respuestas en JSON"
                @click="emit('export-survey', s, 'json')"
                :data-testid="`btn-export-json-${s.id}`"
              >
                <i v-if="exportingSurveyId === `${s.id}-json`" class="pi pi-spin pi-spinner"></i>
                <i v-else class="pi pi-file"></i>
                <span>JSON</span>
              </button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.desktop-table-wrapper {
  display: none;
  background-color: var(--surface-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-containers);
  box-shadow: var(--shadow-sm);
  overflow-x: auto;
}

@media (min-width: 768px) {
  .desktop-table-wrapper {
    display: block;
  }
}

.admin-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.admin-table th {
  background-color: var(--surface-subtle);
  padding: var(--spacing-16);
  font-size: var(--text-caption);
  text-transform: uppercase;
  color: var(--text-muted);
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0.5px;
  border-bottom: 1px solid var(--border-color);
}

.admin-table td {
  padding: var(--spacing-16);
  border-bottom: 1px solid var(--border-color);
  font-size: var(--text-body-sm);
  vertical-align: middle;
}

.survey-row:hover {
  background-color: var(--color-lavender-wash);
}

.col-title {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
  max-width: 320px;
}

.survey-title-text {
  font-weight: var(--font-weight-semibold);
  color: var(--color-midnight-ink);
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

.row-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-8);
  flex-wrap: wrap;
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
  gap: var(--spacing-6);
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn:hover:not(:disabled) {
  background-color: var(--color-lavender-wash);
  border-color: var(--color-royal-signal);
  color: var(--color-royal-signal);
}

.action-btn:disabled {
  opacity: 0.6;
  cursor: wait;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}
</style>

