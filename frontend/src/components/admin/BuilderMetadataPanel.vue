<script setup lang="ts">
import { ref } from 'vue';
import type { EncuestaAdminItem } from '@/services/api';

defineProps<{
  titulo: string;
  slug: string;
  tipoInstrumento: string;
  displayMode: 'form' | 'wizard';
  activa: boolean;
  existingSurveys: EncuestaAdminItem[];
  selectedExistingSurveyId: string;
}>();

const emit = defineEmits<{
  (e: 'update:titulo', val: string): void;
  (e: 'update:slug', val: string): void;
  (e: 'update:tipoInstrumento', val: string): void;
  (e: 'update:displayMode', val: 'form' | 'wizard'): void;
  (e: 'update:activa', val: boolean): void;
  (e: 'update:selectedExistingSurveyId', val: string): void;
  (e: 'titulo-input'): void;
  (e: 'load-canonical'): void;
  (e: 'load-blank'): void;
  (e: 'file-selected', event: Event): void;
  (e: 'load-existing'): void;
}>();

const localFileInputRef = ref<HTMLInputElement | null>(null);

function triggerLocalFileUpload() {
  localFileInputRef.value?.click();
}
</script>

<template>
  <section class="survey-card builder-config-panel" aria-labelledby="config-panel-title">
    <h2 id="config-panel-title" class="panel-title">Metadatos de la Encuesta</h2>

    <div class="config-grid">
      <div class="survey-field">
        <label for="survey-title" class="survey-label">
          <span>Título de la Encuesta</span>
          <span class="required-indicator" aria-hidden="true">*</span>
        </label>
        <input
          id="survey-title"
          :value="titulo"
          type="text"
          class="survey-input"
          required
          maxlength="255"
          placeholder="Ej. Cuestionario de Movilidad PDUL"
          @input="
            emit('update:titulo', ($event.target as HTMLInputElement).value);
            emit('titulo-input');
          "
          data-testid="input-survey-title"
        />
      </div>

      <div class="survey-field">
        <label for="survey-slug" class="survey-label">
          <span>Slug Identificador (URL)</span>
          <span class="required-indicator" aria-hidden="true">*</span>
        </label>
        <input
          id="survey-slug"
          :value="slug"
          type="text"
          class="survey-input"
          required
          maxlength="120"
          placeholder="ej. cuestionario_movilidad_pdul"
          @input="emit('update:slug', ($event.target as HTMLInputElement).value)"
          data-testid="input-survey-slug"
        />
      </div>

      <div class="survey-field">
        <label for="survey-type" class="survey-label">
          <span>Tipo de Instrumento</span>
        </label>
        <select
          id="survey-type"
          :value="tipoInstrumento"
          class="survey-select"
          @change="emit('update:tipoInstrumento', ($event.target as HTMLSelectElement).value)"
          data-testid="select-survey-tipo"
        >
          <option value="consulta_ciudadana">Consulta Ciudadana</option>
          <option value="encuesta_od_pdul">Encuesta Origen-Destino PDUL</option>
          <option value="censo_comunal">Censo Comunal</option>
          <option value="otro">Otro Instrumento Municipal</option>
        </select>
      </div>

      <div class="config-toggle-group">
        <div class="survey-field">
          <label for="survey-display-mode" class="survey-label">
            <span>Modo de Visualización</span>
          </label>
          <select
            id="survey-display-mode"
            :value="displayMode"
            class="survey-select"
            @change="emit('update:displayMode', ($event.target as HTMLSelectElement).value as 'form' | 'wizard')"
          >
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
              :checked="activa"
              type="checkbox"
              class="visually-hidden custom-switch-input"
              @change="emit('update:activa', ($event.target as HTMLInputElement).checked)"
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

    <div class="presets-toolbar">
      <span class="presets-label">Plantillas y Carga:</span>
      <div class="presets-buttons">
        <button
          type="button"
          class="survey-btn survey-btn-secondary preset-btn"
          @click="emit('load-canonical')"
          data-testid="btn-load-canonical"
        >
          <i class="pi pi-bookmark" aria-hidden="true"></i>
          <span>Cargar Canónico PDUL</span>
        </button>

        <button
          type="button"
          class="survey-btn survey-btn-secondary preset-btn"
          @click="emit('load-blank')"
          data-testid="btn-load-blank"
        >
          <i class="pi pi-file" aria-hidden="true"></i>
          <span>Esquema en Blanco</span>
        </button>

        <button
          type="button"
          class="survey-btn survey-btn-secondary preset-btn"
          @click="triggerLocalFileUpload"
          data-testid="btn-upload-json"
        >
          <i class="pi pi-upload" aria-hidden="true"></i>
          <span>Subir Archivo JSON</span>
        </button>

        <input
          ref="localFileInputRef"
          type="file"
          accept=".json,application/json"
          class="visually-hidden"
          aria-label="Cargar archivo JSON de esquema"
          @change="emit('file-selected', $event)"
        />

        <div class="existing-survey-selector">
          <label for="select-existing-survey" class="visually-hidden">Cargar desde encuesta existente</label>
          <select
            id="select-existing-survey"
            :value="selectedExistingSurveyId"
            class="survey-select existing-select"
            @change="
              emit('update:selectedExistingSurveyId', ($event.target as HTMLSelectElement).value);
              emit('load-existing');
            "
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
</template>

<style scoped>
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

@media (max-width: 768px) {
  .presets-buttons {
    width: 100%;
  }

  .presets-buttons .preset-btn,
  .existing-survey-selector {
    width: 100%;
  }
}
</style>

