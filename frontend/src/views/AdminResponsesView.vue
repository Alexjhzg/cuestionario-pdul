<script setup lang="ts">
import { useAdminResponses } from '@/composables/useAdminResponses';
import AdminResponsesTable from '@/components/admin/AdminResponsesTable.vue';
import AdminResponseDetailModal from '@/components/admin/AdminResponseDetailModal.vue';

const props = withDefaults(
  defineProps<{
    initialSurveyId?: string | null;
  }>(),
  {
    initialSurveyId: ''
  }
);

const {
  surveys,
  selectedSurveyId,
  loadingSurveys,
  items,
  totalRespuestas,
  currentPage,
  pageSize,
  isLoadingResponses,
  errorMessage,
  showDetailModal,
  selectedRespuesta,
  maskPii,
  detailViewMode,
  jsonCopied,
  totalPages,
  displayData,
  goToPreviousPage,
  goToNextPage,
  openDetail,
  closeDetail,
  copyJson
} = useAdminResponses(() => props.initialSurveyId);
</script>

<template>
  <div class="admin-responses-view" role="main" aria-labelledby="responses-title">
    <header class="responses-header">
      <div class="header-titles">
        <h1 id="responses-title" class="responses-title">Respuestas Ciudadanas Recibidas</h1>
        <p class="responses-subtitle">
          Supervisión de envíos en tiempo real, auditoría de completitud y protección integral de datos personales.
        </p>
      </div>

      <!-- Selector de encuesta a inspeccionar -->
      <div class="survey-selector-wrapper">
        <label for="survey-inspect-select" class="selector-label">Encuesta a Supervisar:</label>
        <select
          id="survey-inspect-select"
          v-model="selectedSurveyId"
          class="survey-select-input"
          :disabled="loadingSurveys"
          data-testid="select-survey-inspect"
        >
          <option value="" disabled>Seleccione una encuesta</option>
          <option v-for="s in surveys" :key="s.id" :value="s.id">
            {{ s.titulo }} ({{ s.total_respuestas }} respuestas)
          </option>
        </select>
      </div>
    </header>

    <!-- Alertas -->
    <div v-if="errorMessage" class="feedback-alert error-alert" role="alert">
      <i class="pi pi-exclamation-triangle" aria-hidden="true"></i>
      <span>{{ errorMessage }}</span>
    </div>

    <!-- Contenido principal -->
    <AdminResponsesTable
      :items="items"
      :is-loading="isLoadingResponses"
      :current-page="currentPage"
      :total-pages="totalPages"
      :total-respuestas="totalRespuestas"
      v-model:page-size="pageSize"
      @prev-page="goToPreviousPage"
      @next-page="goToNextPage"
      @open-detail="openDetail"
    />

    <!-- Modal de Inspección Detallada con Enmascaramiento PII -->
    <AdminResponseDetailModal
      :open="showDetailModal"
      :respuesta="selectedRespuesta"
      :display-data="displayData"
      v-model:mask-pii="maskPii"
      v-model:detail-view-mode="detailViewMode"
      :json-copied="jsonCopied"
      @close="closeDetail"
      @copy-json="copyJson"
    />
  </div>
</template>

<style scoped>
.admin-responses-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--spacing-20);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-24);
}

.responses-header {
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
  .responses-header {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
  }
}

.responses-title {
  font-size: var(--text-heading-sm);
  color: var(--color-midnight-ink);
  font-weight: var(--font-weight-bold);
  margin: 0 0 var(--spacing-4) 0;
}

.responses-subtitle {
  font-size: var(--text-body-sm);
  color: var(--text-muted);
  margin: 0;
}

.survey-selector-wrapper {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
  min-width: 0;
  width: 100%;
  max-width: 360px;
}

.selector-label {
  font-size: var(--text-caption);
  font-weight: var(--font-weight-semibold);
  color: var(--color-midnight-ink);
}

.survey-select-input {
  min-block-size: var(--min-touch-target);
  min-height: var(--min-touch-target);
  padding: 0 var(--spacing-12);
  border-radius: var(--radius-inputs);
  border: 1px solid var(--border-color);
  background-color: #ffffff;
  font-size: var(--text-body-sm);
  color: var(--color-midnight-ink);
}

.survey-select-input:focus {
  outline: none;
  border-color: var(--color-royal-signal);
  box-shadow: 0 0 0 3px rgba(20, 90, 255, 0.15);
}

/* Alertas y estados */
.feedback-alert {
  display: flex;
  align-items: center;
  gap: var(--spacing-12);
  padding: var(--spacing-16);
  border-radius: var(--radius-inputs);
  font-size: var(--text-body-sm);
}

.error-alert {
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
}

.page-size-select { min-block-size: var(--min-touch-target); min-height: var(--min-touch-target); }
.page-btn { min-block-size: var(--min-touch-target); min-height: var(--min-touch-target); }
.inspect-btn { min-block-size: var(--min-touch-target); min-height: var(--min-touch-target); }
.btn-detail { min-block-size: var(--min-touch-target); min-height: var(--min-touch-target); }
.modal-close-btn { min-block-size: var(--min-touch-target); min-height: var(--min-touch-target); }
.pii-toggle-label { min-block-size: var(--min-touch-target); }
.mode-switch-btn { min-block-size: var(--min-touch-target); min-height: var(--min-touch-target); }
.copy-btn { min-block-size: var(--min-touch-target); min-height: var(--min-touch-target); }
.admin-btn { min-block-size: var(--min-touch-target); min-height: var(--min-touch-target); }
.builder-btn { min-block-size: var(--min-touch-target); min-height: var(--min-touch-target); }
.table-responsive-wrapper { overflow-x: auto; width: 100%; }
</style>
