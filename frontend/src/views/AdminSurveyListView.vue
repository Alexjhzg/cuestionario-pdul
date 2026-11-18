<script setup lang="ts">
import { useAdminSurveyList } from '@/composables/useAdminSurveyList';
import AdminSurveyTable from '@/components/admin/AdminSurveyTable.vue';
import AdminSurveyMobileCards from '@/components/admin/AdminSurveyMobileCards.vue';
import AdminDeactivateSurveyModal from '@/components/admin/AdminDeactivateSurveyModal.vue';

const emit = defineEmits<{
  (e: 'create-survey'): void;
  (e: 'edit-survey', surveyId: string): void;
  (e: 'view-responses', surveyId: string): void;
}>();

const {
  surveys,
  isLoading,
  errorMessage,
  successMessage,
  redactPii,
  showConfirmModal,
  surveyToDeactivate,
  isTogglingStatus,
  exportingSurveyId,
  onToggleClick,
  confirmDeactivation,
  cancelDeactivation,
  handleExport
} = useAdminSurveyList();
</script>

<template>
  <div class="admin-survey-list-view" role="main" aria-labelledby="admin-title">
    <header class="admin-header">
      <div class="header-titles">
        <h1 id="admin-title" class="admin-title">Gestión de Encuestas</h1>
        <p class="admin-subtitle">
          Supervisión de instrumentos activos, recepción de respuestas ciudadanas y exportación masiva soberana.
        </p>
      </div>

      <div class="header-actions">
        <label class="pii-export-control" for="pii-redact-checkbox">
          <input
            id="pii-redact-checkbox"
            v-model="redactPii"
            type="checkbox"
            class="pii-checkbox"
            data-testid="checkbox-redact-pii"
          />
          <span class="pii-label">
            <i class="pi pi-shield" aria-hidden="true"></i>
            Anonimizar datos personales (PII) al exportar
          </span>
        </label>

        <button
          type="button"
          class="admin-btn btn-primary"
          style="display: none;"
          @click="emit('create-survey')"
          aria-label="Crear una nueva encuesta en el constructor visual"
          data-testid="btn-create-new-survey"
        >
          <i class="pi pi-plus" aria-hidden="true"></i>
          <span>Nueva Encuesta</span>
        </button>
      </div>
    </header>

    <div v-if="successMessage" class="feedback-alert success-alert" role="status" aria-live="polite">
      <i class="pi pi-check-circle" aria-hidden="true"></i>
      <span>{{ successMessage }}</span>
    </div>

    <div v-if="errorMessage" class="feedback-alert error-alert" role="alert">
      <i class="pi pi-exclamation-triangle" aria-hidden="true"></i>
      <span>{{ errorMessage }}</span>
    </div>

    <div v-if="isLoading" class="loading-state" role="status" aria-live="polite">
      <i class="pi pi-spin pi-spinner loading-spinner" aria-hidden="true"></i>
      <span>Cargando listado de encuestas registradas...</span>
    </div>

    <div v-else-if="surveys.length === 0" class="empty-state">
      <i class="pi pi-inbox empty-icon" aria-hidden="true"></i>
      <h2 class="empty-title">No hay encuestas registradas</h2>
      <p class="empty-desc">Crea tu primera encuesta utilizando el constructor visual Form.io.</p>
      <button
        type="button"
        class="admin-btn btn-primary"
        style="display: none;"
        @click="emit('create-survey')"
      >
        <i class="pi pi-plus" aria-hidden="true"></i>
        <span>Crear Encuesta</span>
      </button>
    </div>

    <div v-else class="surveys-container">
      <AdminSurveyTable
        :surveys="surveys"
        :is-toggling-status="isTogglingStatus"
        :exporting-survey-id="exportingSurveyId"
        @toggle-status="onToggleClick"
        @view-responses="(id) => emit('view-responses', id)"
        @edit-survey="(id) => emit('edit-survey', id)"
        @export-survey="handleExport"
      />

      <AdminSurveyMobileCards
        :surveys="surveys"
        :is-toggling-status="isTogglingStatus"
        :exporting-survey-id="exportingSurveyId"
        @toggle-status="onToggleClick"
        @view-responses="(id) => emit('view-responses', id)"
        @edit-survey="(id) => emit('edit-survey', id)"
        @export-survey="handleExport"
      />
    </div>

    <AdminDeactivateSurveyModal
      :open="showConfirmModal"
      :survey="surveyToDeactivate"
      @cancel="cancelDeactivation"
      @confirm="confirmDeactivation"
    />
  </div>
</template>

<style scoped>
.admin-survey-list-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--spacing-20);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-24);
}

.admin-header {
  background-color: var(--surface-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-containers);
  padding: var(--spacing-20);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-16);
  box-shadow: var(--shadow-sm);
}

@media (min-width: 768px) {
  .admin-header {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
  }
}

.admin-title {
  font-size: var(--text-heading-sm);
  color: var(--color-midnight-ink);
  font-weight: var(--font-weight-bold);
  margin: 0 0 var(--spacing-4) 0;
}

.admin-subtitle {
  font-size: var(--text-body-sm);
  color: var(--text-muted);
  margin: 0;
}

.header-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--spacing-16);
}

.pii-export-control {
  display: flex;
  align-items: center;
  gap: var(--spacing-8);
  min-block-size: var(--min-touch-target);
  cursor: pointer;
  padding: 0 var(--spacing-8);
  border-radius: var(--radius-cards);
}

.pii-checkbox {
  width: 20px;
  height: 20px;
  accent-color: var(--color-royal-signal);
  cursor: pointer;
}

.pii-label {
  font-size: var(--text-caption);
  color: var(--text-body-color);
  font-weight: var(--font-weight-medium);
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-4);
}

.admin-btn {
  min-block-size: var(--min-touch-target);
  min-height: var(--min-touch-target);
  padding: 0 var(--spacing-20);
  border-radius: var(--radius-cards);
  font-size: var(--text-body-sm);
  font-weight: var(--font-weight-semibold);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-8);
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.2s ease;
}

.accessible-switch { min-block-size: var(--min-touch-target); min-height: var(--min-touch-target); min-inline-size: var(--min-touch-target); }
.action-btn { min-block-size: var(--min-touch-target); min-height: var(--min-touch-target); }
.modal-close-btn { min-block-size: var(--min-touch-target); min-height: var(--min-touch-target); }
.desktop-table-wrapper { display: none; overflow-x: auto; }
.mobile-cards-grid { display: flex; flex-direction: column; gap: var(--spacing-16); }
@media (min-width: 768px) {
  .desktop-table-wrapper { display: block; }
}
@media (min-width: 768px) {
  .mobile-cards-grid { display: none; }
}

.btn-primary {
  background-color: var(--color-royal-signal);
  color: #ffffff;
}

.feedback-alert {
  display: flex;
  align-items: center;
  gap: var(--spacing-12);
  padding: var(--spacing-16);
  border-radius: var(--radius-inputs);
  font-size: var(--text-body-sm);
}

.success-alert {
  background-color: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #166534;
}

.error-alert {
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
}

.loading-state,
.empty-state {
  background-color: var(--surface-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-containers);
  padding: var(--spacing-40);
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-16);
}

.loading-spinner {
  font-size: 2rem;
  color: var(--color-royal-signal);
}

.empty-icon {
  font-size: 3rem;
  color: var(--text-helper);
}

.empty-title {
  margin: 0;
  font-size: var(--text-subheading);
  color: var(--color-midnight-ink);
}

.empty-desc {
  margin: 0;
  color: var(--text-muted);
  font-size: var(--text-body-sm);
}
</style>
