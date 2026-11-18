<script setup lang="ts">
import FormioBuilder from '../components/admin/FormioBuilder.vue';
import BuilderMetadataPanel from '../components/admin/BuilderMetadataPanel.vue';
import SchemaValidationModal from '../components/admin/SchemaValidationModal.vue';
import { useFormBuilder } from '../composables/useFormBuilder';

const props = defineProps<{
  initialSurveyId?: string | null;
}>();

const emit = defineEmits<{
  (e: 'survey-created', surveyId: string): void;
  (e: 'view-responses', surveyId: string): void;
}>();

const {
  surveyId,
  titulo,
  slug,
  tipoInstrumento,
  activa,
  displayMode,
  currentSchema,
  builderRef,
  isSaving,
  isLoadingSurvey,
  successMessage,
  errorMessage,
  validationModalVisible,
  validationResults,
  existingSurveys,
  selectedExistingSurveyId,
  fileInputRef,
  onTituloInput,
  loadCanonicalPdul,
  loadBlankSchema,
  triggerFileUpload,
  onFileSelected,
  loadFromExistingSurvey,
  validateCurrentSchema,
  exportSchemaJson,
  saveSurvey
} = useFormBuilder(
  () => props.initialSurveyId,
  (id) => emit('survey-created', id)
);

defineExpose({
  surveyId,
  titulo,
  slug,
  tipoInstrumento,
  activa,
  displayMode,
  currentSchema,
  builderRef,
  isSaving,
  isLoadingSurvey,
  successMessage,
  errorMessage,
  validationModalVisible,
  validationResults,
  existingSurveys,
  selectedExistingSurveyId,
  fileInputRef,
  onTituloInput,
  loadCanonicalPdul,
  loadBlankSchema,
  triggerFileUpload,
  onFileSelected,
  loadFromExistingSurvey,
  validateCurrentSchema,
  exportSchemaJson,
  saveSurvey
});
</script>

<template>
  <div class="form-builder-view">
    <header class="builder-header">
      <div class="header-titles">
        <h1 class="view-title">Constructor Visual de Encuestas</h1>
        <p class="view-subtitle">
          Diseño y parametrización soberana de instrumentos de consulta Form.io para la Alcaldía de Maturín.
        </p>
      </div>

      <div class="header-actions">
        <button
          type="button"
          class="survey-btn survey-btn-secondary"
          @click="validateCurrentSchema"
          title="Verificar cumplimiento de reglas de soberanía y sintaxis"
          data-testid="btn-validate-schema"
        >
          <i class="pi pi-check-circle" aria-hidden="true"></i>
          <span>Validar Esquema</span>
        </button>

        <button
          type="button"
          class="survey-btn survey-btn-secondary"
          @click="exportSchemaJson"
          title="Descargar archivo JSON local"
          data-testid="btn-export-json"
        >
          <i class="pi pi-download" aria-hidden="true"></i>
          <span>Exportar JSON</span>
        </button>

        <button
          type="button"
          class="survey-btn survey-btn-primary"
          :disabled="isSaving"
          @click="() => saveSurvey(false)"
          data-testid="btn-save-survey"
        >
          <i v-if="isSaving" class="pi pi-spin pi-spinner" aria-hidden="true"></i>
          <i v-else class="pi pi-save" aria-hidden="true"></i>
          <span>{{ surveyId ? 'Actualizar Encuesta' : 'Guardar en Base de Datos' }}</span>
        </button>

        <button
          v-if="surveyId"
          type="button"
          class="survey-btn survey-btn-secondary"
          :disabled="isSaving"
          @click="() => saveSurvey(true)"
          title="Guardar como un nuevo registro con nuevo slug"
          data-testid="btn-save-as-new"
        >
          <i class="pi pi-plus" aria-hidden="true"></i>
          <span>Guardar como Nueva</span>
        </button>
      </div>
    </header>

    <div v-if="successMessage" class="alert-banner alert-success" role="status" aria-live="polite">
      <i class="pi pi-check" aria-hidden="true"></i>
      <span>{{ successMessage }}</span>
      <button type="button" class="close-alert-btn" aria-label="Cerrar notificación" @click="successMessage = null">
        <i class="pi pi-times" aria-hidden="true"></i>
      </button>
    </div>

    <div v-if="errorMessage" class="alert-banner alert-error" role="alert">
      <i class="pi pi-exclamation-triangle" aria-hidden="true"></i>
      <span>{{ errorMessage }}</span>
      <button type="button" class="close-alert-btn" aria-label="Cerrar alerta" @click="errorMessage = null">
        <i class="pi pi-times" aria-hidden="true"></i>
      </button>
    </div>

    <BuilderMetadataPanel
      v-model:titulo="titulo"
      v-model:slug="slug"
      v-model:tipo-instrumento="tipoInstrumento"
      v-model:display-mode="displayMode"
      v-model:activa="activa"
      v-model:selected-existing-survey-id="selectedExistingSurveyId"
      :existing-surveys="existingSurveys"
      @titulo-input="onTituloInput"
      @load-canonical="loadCanonicalPdul"
      @load-blank="loadBlankSchema"
      @file-selected="onFileSelected"
      @load-existing="loadFromExistingSurvey"
    />

    <section class="builder-section" aria-label="Lienzo de diseño visual de componentes">
      <FormioBuilder
        ref="builderRef"
        v-model="currentSchema"
        :display-mode="displayMode"
      />
    </section>

    <SchemaValidationModal
      :visible="validationModalVisible"
      :validation-results="validationResults"
      @close="validationModalVisible = false"
    />
  </div>
</template>

<style scoped>
.form-builder-view {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-24);
  width: 100%;
  max-width: 1400px;
  margin: 0 auto;
  padding: var(--spacing-16);
}

.builder-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-16);
  padding-block-end: var(--spacing-16);
  border-block-end: 1px solid var(--border-color);
}

.view-title {
  font-size: var(--text-heading-sm);
  color: var(--text-primary);
  margin-bottom: var(--spacing-4);
}

.view-subtitle {
  font-size: var(--text-body-sm);
  color: var(--text-muted);
}

.header-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-12);
  align-items: center;
}

.alert-banner {
  display: flex;
  align-items: center;
  gap: var(--spacing-12);
  padding: var(--spacing-12) var(--spacing-16);
  border-radius: var(--radius-inputs);
  font-size: var(--text-body);
}

.alert-success {
  background-color: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #166534;
}

.alert-error {
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
}

.close-alert-btn {
  min-block-size: var(--min-touch-target);
  min-height: var(--min-touch-target);
  min-inline-size: var(--min-touch-target);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-left: auto;
  background: transparent;
  border: none;
  color: inherit;
  cursor: pointer;
  padding: var(--spacing-4);
  font-size: 1rem;
}

.custom-switch-label { min-block-size: var(--min-touch-target); }
.preset-btn { min-block-size: var(--min-touch-target); }
.existing-select { min-block-size: var(--min-touch-target); }
.modal-close-btn { min-block-size: var(--min-touch-target); min-inline-size: var(--min-touch-target); }

.builder-section {
  width: 100%;
}

@media (max-width: 768px) {
  .header-actions {
    width: 100%;
  }

  .header-actions .survey-btn {
    flex: 1 1 100%;
  }

  .presets-buttons {
    width: 100%;
  }

  .presets-buttons .preset-btn,
  .existing-survey-selector {
    width: 100%;
  }
}
</style>
