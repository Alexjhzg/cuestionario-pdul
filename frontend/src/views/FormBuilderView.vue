<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import FormioBuilder from '../components/admin/FormioBuilder.vue';
import pdulCanonicalSchema from '../assets/schemas/pdul_origen_destino.json';
import {
  fetchAdminEncuestas,
  fetchAdminEncuesta,
  createAdminEncuesta,
  updateAdminEncuesta,
  triggerBlobDownload,
  type EncuestaAdminItem
} from '../services/api';
import { validateFormioSchema, type SchemaValidationResult } from '../utils/schemaValidator';

const props = defineProps<{
  initialSurveyId?: string | null;
}>();

const emit = defineEmits<{
  (e: 'survey-created', surveyId: string): void;
  (e: 'view-responses', surveyId: string): void;
}>();

const BLANK_SCHEMA: Record<string, any> = {
  display: 'form',
  title: 'Nueva Consulta Ciudadana',
  name: 'nueva_consulta',
  path: 'nueva-consulta',
  components: [
    {
      type: 'textfield',
      key: 'parroquia',
      label: 'Parroquia',
      placeholder: 'Indique la parroquia',
      required: true
    },
    {
      type: 'button',
      key: 'submit',
      label: 'Enviar Participación',
      action: 'submit',
      theme: 'primary',
      block: true
    }
  ]
};

// Formulario de Metadatos
const surveyId = ref<string | null>(props.initialSurveyId || null);
const titulo = ref('Encuesta de Participación Ciudadana');
const slug = ref('consulta_ciudadana');
const tipoInstrumento = ref('consulta_ciudadana');
const activa = ref(true);
const displayMode = ref<'form' | 'wizard'>('form');

// Esquema actual
const currentSchema = ref<Record<string, any>>(JSON.parse(JSON.stringify(BLANK_SCHEMA)));
const builderRef = ref<InstanceType<typeof FormioBuilder> | null>(null);

// Estados de carga y feedback
const isSaving = ref(false);
const isLoadingSurvey = ref(false);
const successMessage = ref<string | null>(null);
const errorMessage = ref<string | null>(null);
const validationModalVisible = ref(false);
const validationResults = ref<SchemaValidationResult | null>(null);

// Encuestas existentes para carga
const existingSurveys = ref<EncuestaAdminItem[]>([]);
const selectedExistingSurveyId = ref<string>('');

// Input de archivo oculto
const fileInputRef = ref<HTMLInputElement | null>(null);

// Normalizar slug
function generateSlug(text: string): string {
  return text
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9_]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .slice(0, 100);
}

function onTituloInput() {
  if (!surveyId.value) {
    slug.value = generateSlug(titulo.value);
  }
}

// Cargar esquemas predefinidos
function loadCanonicalPdul() {
  currentSchema.value = JSON.parse(JSON.stringify(pdulCanonicalSchema));
  titulo.value = 'Encuesta Origen-Destino PDUL Maturín';
  slug.value = 'pdul_origen_destino';
  tipoInstrumento.value = 'encuesta_od_pdul';
  displayMode.value = (currentSchema.value.display === 'wizard' ? 'wizard' : 'form');
  if (builderRef.value?.setSchema) {
    builderRef.value.setSchema(currentSchema.value);
  }
  successMessage.value = 'Esquema canónico PDUL cargado exitosamente.';
  errorMessage.value = null;
}

function loadBlankSchema() {
  currentSchema.value = JSON.parse(JSON.stringify(BLANK_SCHEMA));
  titulo.value = 'Nueva Consulta Ciudadana';
  slug.value = 'nueva_consulta';
  tipoInstrumento.value = 'consulta_ciudadana';
  displayMode.value = 'form';
  if (builderRef.value?.setSchema) {
    builderRef.value.setSchema(currentSchema.value);
  }
  successMessage.value = 'Esquema en blanco cargado.';
  errorMessage.value = null;
}

function triggerFileUpload() {
  fileInputRef.value?.click();
}

function onFileSelected(event: Event) {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = (e) => {
    try {
      const content = e.target?.result as string;
      const parsed = JSON.parse(content);
      if (!parsed || typeof parsed !== 'object') {
        throw new Error('El archivo no contiene un objeto JSON válido');
      }
      currentSchema.value = parsed;
      if (parsed.title) titulo.value = parsed.title;
      if (parsed.name) slug.value = generateSlug(parsed.name);
      displayMode.value = (parsed.display === 'wizard' ? 'wizard' : 'form');
      if (builderRef.value?.setSchema) {
        builderRef.value.setSchema(parsed);
      }
      successMessage.value = `Esquema cargado exitosamente desde "${file.name}".`;
      errorMessage.value = null;
    } catch (err: any) {
      errorMessage.value = `Error al leer archivo JSON: ${err.message || 'Formato inválido'}`;
      successMessage.value = null;
    }
  };
  reader.readAsText(file);
  target.value = '';
}

async function loadFromExistingSurvey() {
  if (!selectedExistingSurveyId.value) return;
  isLoadingSurvey.value = true;
  errorMessage.value = null;
  try {
    const survey = await fetchAdminEncuesta(selectedExistingSurveyId.value);
    surveyId.value = survey.id;
    titulo.value = survey.titulo;
    slug.value = survey.slug;
    tipoInstrumento.value = survey.tipo_instrumento;
    activa.value = survey.activa;
    if (survey.esquema_formio) {
      currentSchema.value = survey.esquema_formio;
      displayMode.value = (survey.esquema_formio.display === 'wizard' ? 'wizard' : 'form');
      if (builderRef.value?.setSchema) {
        builderRef.value.setSchema(survey.esquema_formio);
      }
    }
    successMessage.value = `Encuesta "${survey.titulo}" cargada para edición.`;
  } catch (err: any) {
    errorMessage.value = `Error al cargar encuesta: ${err.message || 'Fallo de red'}`;
  } finally {
    isLoadingSurvey.value = false;
  }
}

// Validar esquema
function validateCurrentSchema() {
  const exported = builderRef.value?.getSchema?.() || currentSchema.value;
  validationResults.value = validateFormioSchema(exported, { requireSubmit: true });
  validationModalVisible.value = true;
}

// Descargar esquema JSON
function exportSchemaJson() {
  const exported = builderRef.value?.getSchema?.() || currentSchema.value;
  const fileName = `${slug.value || 'esquema_encuesta'}.json`;
  const blob = new Blob([JSON.stringify(exported, null, 2)], {
    type: 'application/json'
  });
  triggerBlobDownload(blob, fileName);
  successMessage.value = `Esquema exportado como "${fileName}".`;
}

// Guardar en la base de datos
async function saveSurvey(asNew = false) {
  errorMessage.value = null;
  successMessage.value = null;

  if (!titulo.value.trim()) {
    errorMessage.value = 'El título de la encuesta es obligatorio.';
    return;
  }
  if (!slug.value.trim()) {
    errorMessage.value = 'El slug identificador es obligatorio.';
    return;
  }

  const exportedSchema = builderRef.value?.getSchema?.() || currentSchema.value;
  exportedSchema.title = titulo.value;
  exportedSchema.display = displayMode.value;

  isSaving.value = true;
  try {
    if (surveyId.value && !asNew) {
      // Actualizar encuesta existente
      const updated = await updateAdminEncuesta(surveyId.value, {
        titulo: titulo.value,
        tipo_instrumento: tipoInstrumento.value,
        activa: activa.value,
        esquema_formio: exportedSchema
      });
      successMessage.value = `Encuesta "${updated.titulo}" actualizada exitosamente.`;
      emit('survey-created', updated.id);
    } else {
      // Crear nueva encuesta
      const created = await createAdminEncuesta({
        titulo: titulo.value,
        slug: slug.value,
        tipo_instrumento: tipoInstrumento.value,
        activa: activa.value,
        esquema_formio: exportedSchema
      });
      surveyId.value = created.id;
      successMessage.value = `Nueva encuesta "${created.titulo}" guardada exitosamente en la base de datos.`;
      emit('survey-created', created.id);
    }
  } catch (err: any) {
    errorMessage.value = err.message || 'Error al persistir la encuesta en el servidor';
  } finally {
    isSaving.value = false;
  }
}

// Al montar, cargar encuestas para selector
onMounted(async () => {
  try {
    existingSurveys.value = await fetchAdminEncuestas();
  } catch {
    // Si falla la lista de encuestas, no es bloqueante
  }

  if (props.initialSurveyId) {
    selectedExistingSurveyId.value = props.initialSurveyId;
    loadFromExistingSurvey();
  }
});

watch(
  () => props.initialSurveyId,
  (newId) => {
    if (newId && newId !== surveyId.value) {
      selectedExistingSurveyId.value = newId;
      loadFromExistingSurvey();
    }
  }
);
</script>

<template>
  <div class="form-builder-view">
    <!-- Encabezado de la Vista -->
    <header class="builder-header">
      <div class="header-titles">
        <h1 class="view-title">Constructor Visual de Encuestas</h1>
        <p class="view-subtitle">
          Diseño y parametrización soberana de instrumentos de consulta Form.io para la Alcaldía de Maturín.
        </p>
      </div>

      <!-- Barra de Acciones Principales -->
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

    <!-- Alertas de Estado -->
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

    <!-- Panel de Configuración y Metadatos -->
    <section class="survey-card builder-config-panel" aria-labelledby="config-panel-title">
      <h2 id="config-panel-title" class="panel-title">Metadatos de la Encuesta</h2>

      <div class="config-grid">
        <!-- Título -->
        <div class="survey-field">
          <label for="survey-title" class="survey-label">
            <span>Título de la Encuesta</span>
            <span class="required-indicator" aria-hidden="true">*</span>
          </label>
          <input
            id="survey-title"
            v-model="titulo"
            type="text"
            class="survey-input"
            required
            maxlength="255"
            placeholder="Ej. Cuestionario de Movilidad PDUL"
            @input="onTituloInput"
            data-testid="input-survey-title"
          />
        </div>

        <!-- Slug -->
        <div class="survey-field">
          <label for="survey-slug" class="survey-label">
            <span>Slug Identificador (URL)</span>
            <span class="required-indicator" aria-hidden="true">*</span>
          </label>
          <input
            id="survey-slug"
            v-model="slug"
            type="text"
            class="survey-input"
            required
            maxlength="120"
            placeholder="ej. cuestionario_movilidad_pdul"
            data-testid="input-survey-slug"
          />
        </div>

        <!-- Tipo de Instrumento -->
        <div class="survey-field">
          <label for="survey-type" class="survey-label">
            <span>Tipo de Instrumento</span>
          </label>
          <select id="survey-type" v-model="tipoInstrumento" class="survey-select" data-testid="select-survey-tipo">
            <option value="consulta_ciudadana">Consulta Ciudadana</option>
            <option value="encuesta_od_pdul">Encuesta Origen-Destino PDUL</option>
            <option value="censo_comunal">Censo Comunal</option>
            <option value="otro">Otro Instrumento Municipal</option>
          </select>
        </div>

        <!-- Modo de Visualización y Disponibilidad -->
        <div class="config-toggle-group">
          <div class="survey-field">
            <label for="survey-display-mode" class="survey-label">
              <span>Modo de Visualización</span>
            </label>
            <select id="survey-display-mode" v-model="displayMode" class="survey-select">
              <option value="form">Formulario Continuo (Scroll)</option>
              <option value="wizard">Asistente por Pasos (Wizard)</option>
            </select>
          </div>

          <div class="survey-field switch-field">
            <label class="survey-label" for="survey-active-toggle">
              <span>Disponibilidad</span>
            </label>
            <label class="custom-switch-label" for="survey-active-toggle">
              <input
                id="survey-active-toggle"
                v-model="activa"
                type="checkbox"
                class="visually-hidden custom-switch-input"
                data-testid="switch-survey-activa"
              />
              <span class="custom-switch-track" aria-hidden="true">
                <span class="custom-switch-thumb"></span>
              </span>
              <span class="switch-status-text">
                {{ activa ? 'Activa para respuestas' : 'Inactiva (Borrador)' }}
              </span>
            </label>
          </div>
        </div>
      </div>

      <!-- Barra de Carga de Esquemas Preestablecidos -->
      <div class="presets-toolbar">
        <span class="presets-label">Plantillas y Carga:</span>
        <div class="presets-buttons">
          <button
            type="button"
            class="survey-btn survey-btn-secondary preset-btn"
            @click="loadCanonicalPdul"
            data-testid="btn-load-canonical"
          >
            <i class="pi pi-bookmark" aria-hidden="true"></i>
            <span>Cargar Canónico PDUL</span>
          </button>

          <button
            type="button"
            class="survey-btn survey-btn-secondary preset-btn"
            @click="loadBlankSchema"
            data-testid="btn-load-blank"
          >
            <i class="pi pi-file" aria-hidden="true"></i>
            <span>Esquema en Blanco</span>
          </button>

          <button
            type="button"
            class="survey-btn survey-btn-secondary preset-btn"
            @click="triggerFileUpload"
            data-testid="btn-upload-json"
          >
            <i class="pi pi-upload" aria-hidden="true"></i>
            <span>Subir Archivo JSON</span>
          </button>

          <input
            ref="fileInputRef"
            type="file"
            accept=".json,application/json"
            class="visually-hidden"
            aria-label="Cargar archivo JSON de esquema"
            @change="onFileSelected"
          />

          <!-- Selector de Encuesta Existente -->
          <div class="existing-survey-selector">
            <label for="select-existing-survey" class="visually-hidden">Cargar desde encuesta existente</label>
            <select
              id="select-existing-survey"
              v-model="selectedExistingSurveyId"
              class="survey-select existing-select"
              @change="loadFromExistingSurvey"
              data-testid="select-existing-survey"
            >
              <option value="">-- Cargar desde encuesta existente --</option>
              <option v-for="s in existingSurveys" :key="s.id" :value="s.id">
                {{ s.titulo }} ({{ s.slug }})
              </option>
            </select>
          </div>
        </div>
      </div>
    </section>

    <!-- Constructor Visual -->
    <section class="builder-section" aria-label="Lienzo de diseño visual de componentes">
      <FormioBuilder
        ref="builderRef"
        v-model="currentSchema"
        :display-mode="displayMode"
      />
    </section>

    <!-- Diálogo / Modal Accesible de Validación -->
    <div
      v-if="validationModalVisible"
      class="modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-labelledby="validation-dialog-title"
      @keydown.esc="validationModalVisible = false"
    >
      <div class="modal-card">
        <header class="modal-header">
          <h3 id="validation-dialog-title" class="modal-title">
            <i
              :class="[
                'pi',
                validationResults?.valid ? 'pi-check-circle modal-icon-success' : 'pi-exclamation-circle modal-icon-error'
              ]"
              aria-hidden="true"
            ></i>
            <span>{{ validationResults?.valid ? 'Esquema Válido' : 'Observaciones de Validación' }}</span>
          </h3>
          <button
            type="button"
            class="modal-close-btn"
            aria-label="Cerrar diálogo de validación"
            @click="validationModalVisible = false"
          >
            <i class="pi pi-times" aria-hidden="true"></i>
          </button>
        </header>

        <div class="modal-body">
          <p v-if="validationResults?.valid" class="validation-summary-success">
            El esquema cumple con todas las especificaciones de soberanía de datos, nomenclatura snake_case y contiene el botón de envío correspondiente.
          </p>
          <div v-else class="validation-errors-list">
            <p class="errors-intro">Se detectaron las siguientes discrepancias en el esquema actual:</p>
            <ul>
              <li v-for="(err, index) in validationResults?.errors" :key="index" class="error-item">
                <i class="pi pi-times-circle error-bullet" aria-hidden="true"></i>
                <span>{{ err }}</span>
              </li>
            </ul>
          </div>
        </div>

        <footer class="modal-footer">
          <button
            type="button"
            class="survey-btn survey-btn-primary"
            @click="validationModalVisible = false"
          >
            Entendido
          </button>
        </footer>
      </div>
    </div>
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

/* Alertas */
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

/* Panel de Configuración */
.builder-config-panel {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-20);
}

.panel-title {
  font-size: var(--text-subheading);
  color: var(--text-primary);
  margin-bottom: var(--spacing-8);
}

.config-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--spacing-20);
}

.config-toggle-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-16);
}

.switch-field {
  margin-block-end: 0;
}

.custom-switch-label {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-12);
  cursor: pointer;
  min-block-size: var(--min-touch-target);
}

.custom-switch-track {
  width: 52px;
  height: 28px;
  background-color: var(--border-color);
  border-radius: 9999px;
  position: relative;
  transition: background-color 0.2s ease;
  display: flex;
  align-items: center;
  padding: 2px;
}

.custom-switch-thumb {
  width: 24px;
  height: 24px;
  background-color: #ffffff;
  border-radius: 50%;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  transition: transform 0.2s ease;
}

.custom-switch-input:checked + .custom-switch-track {
  background-color: var(--color-mint-win);
}

.custom-switch-input:checked + .custom-switch-track .custom-switch-thumb {
  transform: translateX(24px);
}

.custom-switch-input:focus-visible + .custom-switch-track {
  outline: 3px solid var(--focus-ring);
  outline-offset: 2px;
}

.switch-status-text {
  font-size: var(--text-body);
  font-weight: var(--font-weight-medium);
  color: var(--text-body-color);
}

/* Barra de Presets */
.presets-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--spacing-12);
  padding-block-start: var(--spacing-16);
  border-block-start: 1px dashed var(--border-color);
}

.presets-label {
  font-weight: var(--font-weight-semibold);
  font-size: var(--text-body-sm);
  color: var(--text-muted);
}

.presets-buttons {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--spacing-12);
  flex: 1;
}

.preset-btn {
  font-size: var(--text-body-sm);
  padding: 0.5rem 1rem;
  min-block-size: var(--min-touch-target);
}

.existing-survey-selector {
  min-width: 260px;
}

.existing-select {
  font-size: var(--text-body-sm);
  padding: 0.5rem 0.75rem;
  min-block-size: var(--min-touch-target);
}

/* Sección de Constructor */
.builder-section {
  width: 100%;
}

/* Modal */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background-color: rgba(2, 5, 32, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: var(--spacing-16);
}

.modal-card {
  background-color: var(--surface-card);
  border-radius: var(--radius-containers);
  width: 100%;
  max-width: 600px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-20);
  border-block-end: 1px solid var(--border-color);
}

.modal-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-8);
  font-size: var(--text-subheading);
  color: var(--text-primary);
}

.modal-icon-success {
  color: var(--color-mint-win);
}

.modal-icon-error {
  color: var(--color-coral-lost);
}

.modal-close-btn {
  min-block-size: var(--min-touch-target);
  min-inline-size: var(--min-touch-target);
  background: transparent;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  color: var(--text-muted);
}

.modal-body {
  padding: var(--spacing-20);
  max-height: 400px;
  overflow-y: auto;
}

.validation-summary-success {
  color: #166534;
  font-size: var(--text-body);
}

.errors-intro {
  font-weight: var(--font-weight-medium);
  margin-bottom: var(--spacing-12);
  color: var(--text-primary);
}

.validation-errors-list ul {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-8);
}

.error-item {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-8);
  font-size: var(--text-body-sm);
  color: #991b1b;
}

.error-bullet {
  margin-top: 3px;
  flex-shrink: 0;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  padding: var(--spacing-16) var(--spacing-20);
  border-block-start: 1px solid var(--border-color);
  background-color: var(--surface-subtle);
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
