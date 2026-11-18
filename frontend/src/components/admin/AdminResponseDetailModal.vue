<script setup lang="ts">
import { computed } from 'vue';
import type { AdminRespuestaItem } from '@/services/api';
import type { DetailViewMode } from '@/composables/useAdminResponses';
import {
  type ResponseDisplayData,
  formatFecha,
  formatParroquia
} from '@/utils/responseFormatters';
import AdminResponseDetailGrid from './AdminResponseDetailGrid.vue';

const props = defineProps<{
  open: boolean;
  respuesta: AdminRespuestaItem | null;
  displayData: ResponseDisplayData;
  maskPii: boolean;
  detailViewMode: DetailViewMode;
  jsonCopied: boolean;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'update:maskPii', value: boolean): void;
  (e: 'update:detailViewMode', value: DetailViewMode): void;
  (e: 'copy-json'): void;
}>();

const localMaskPii = computed<boolean>({
  get: () => props.maskPii,
  set: (val: boolean) => emit('update:maskPii', val)
});
</script>

<template>
  <!-- Modal de Inspección Detallada con Enmascaramiento PII -->
  <div
    v-if="open && respuesta"
    class="modal-backdrop"
    role="dialog"
    aria-modal="true"
    aria-labelledby="modal-detail-title"
    @keydown.esc="emit('close')"
  >
    <div class="modal-dialog">
      <header class="modal-header">
        <div class="modal-header-titles">
          <h3 id="modal-detail-title" class="modal-title">
            Detalle de Respuesta #{{ respuesta.id }}
          </h3>
          <span class="modal-subtitle">
            Parroquia: {{ formatParroquia(respuesta.parroquia) }} | Registrado: {{ formatFecha(respuesta.fecha_registro) }}
          </span>
        </div>

        <button
          type="button"
          class="modal-close-btn"
          aria-label="Cerrar modal de detalle"
          @click="emit('close')"
          data-testid="btn-modal-close"
        >
          <i class="pi pi-times"></i>
        </button>
      </header>

      <!-- Barra de control de PII y Selector de Modo de Visualización -->
      <div class="pii-protection-bar">
        <div class="pii-controls-group">
          <label class="pii-toggle-label" for="mask-pii-checkbox">
            <input
              id="mask-pii-checkbox"
              v-model="localMaskPii"
              type="checkbox"
              class="pii-toggle-input"
              data-testid="checkbox-mask-pii"
            />
            <span class="pii-toggle-text">
              Enmascarar datos personales (PII)
            </span>
          </label>

          <span class="pii-badge" :class="maskPii ? 'badge-protected' : 'badge-revealed'">
            <i :class="['pi', maskPii ? 'pi-shield' : 'pi-unlock']"></i>
            {{ maskPii ? 'PII Protegido' : 'Datos Visibles (Inspección Supervisada)' }}
          </span>
        </div>

        <!-- Selector de Modo de Visualización (Ficha Grid vs JSON) -->
        <div class="view-mode-selector" role="tablist" aria-label="Modo de visualización de la respuesta">
          <button
            type="button"
            role="tab"
            class="mode-switch-btn"
            :class="{ active: detailViewMode === 'grid' }"
            :aria-selected="detailViewMode === 'grid'"
            @click="emit('update:detailViewMode', 'grid')"
            data-testid="btn-view-mode-grid"
          >
            <i class="pi pi-th-large" aria-hidden="true"></i>
            <span>Ficha Grid</span>
          </button>
          <button
            type="button"
            role="tab"
            class="mode-switch-btn"
            :class="{ active: detailViewMode === 'json' }"
            :aria-selected="detailViewMode === 'json'"
            @click="emit('update:detailViewMode', 'json')"
            data-testid="btn-view-mode-json"
          >
            <i class="pi pi-code" aria-hidden="true"></i>
            <span>JSON Técnico</span>
          </button>
        </div>
      </div>

      <div v-if="!maskPii" class="pii-warning-banner" role="alert">
        <i class="pi pi-exclamation-triangle" aria-hidden="true"></i>
        <span>Advertencia: Los datos personales están visibles exclusivamente para fines de supervisión técnica.</span>
      </div>

      <div class="modal-body">
        <AdminResponseDetailGrid
          v-show="detailViewMode === 'grid'"
          :display-data="displayData"
          :mask-pii="maskPii"
        />

        <!-- VISTA 2: VISOR JSON FORMATEADO (Técnico) -->
        <div v-show="detailViewMode === 'json'" class="json-viewer-wrapper">
          <pre class="json-code-viewer" data-testid="json-detail-viewer"><code>{{ JSON.stringify(displayData, null, 2) }}</code></pre>
        </div>
      </div>

      <footer class="modal-footer">
        <button
          type="button"
          class="builder-btn btn-secondary btn-copy"
          @click="emit('copy-json')"
          data-testid="btn-copy-json"
        >
          <i :class="['pi', jsonCopied ? 'pi-check' : 'pi-copy']"></i>
          <span>{{ jsonCopied ? '¡Copiado!' : 'Copiar JSON' }}</span>
        </button>

        <button
          type="button"
          class="builder-btn btn-primary"
          @click="emit('close')"
        >
          <span>Cerrar</span>
        </button>
      </footer>
    </div>
  </div>
</template>

<style scoped>
/* Modal */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background-color: rgba(2, 5, 32, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-20);
  z-index: 9999;
}

.modal-dialog {
  background-color: #ffffff;
  border-radius: var(--radius-containers);
  width: 95%;
  max-width: 960px;
  max-height: 88vh;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-xl);
}

.modal-header {
  padding: var(--spacing-16) var(--spacing-20);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-title {
  margin: 0;
  font-size: var(--text-subheading);
  color: var(--color-midnight-ink);
}

.modal-subtitle {
  font-size: var(--text-caption);
  color: var(--text-helper);
}

.modal-close-btn {
  min-block-size: var(--min-touch-target);
  min-height: var(--min-touch-target);
  width: 48px;
  height: 48px;
  background: none;
  border: none;
  border-radius: var(--radius-cards);
  color: var(--text-muted);
  font-size: 1.25rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-close-btn:hover {
  background-color: var(--surface-subtle);
  color: var(--color-midnight-ink);
}

.pii-protection-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-12) var(--spacing-20);
  background-color: var(--surface-subtle);
  border-bottom: 1px solid var(--border-color);
  flex-wrap: wrap;
  gap: var(--spacing-12);
}

.pii-controls-group {
  display: flex;
  align-items: center;
  gap: var(--spacing-16);
  flex-wrap: wrap;
}

.pii-toggle-label {
  display: flex;
  align-items: center;
  gap: var(--spacing-8);
  cursor: pointer;
  min-block-size: var(--min-touch-target);
}

.pii-toggle-input {
  width: 20px;
  height: 20px;
  accent-color: var(--color-royal-signal);
  cursor: pointer;
}

.pii-toggle-text {
  font-size: var(--text-caption);
  font-weight: var(--font-weight-semibold);
  color: var(--color-midnight-ink);
}

.pii-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-6);
  padding: var(--spacing-4) var(--spacing-10);
  border-radius: var(--radius-pills);
  font-size: var(--text-caption);
  font-weight: var(--font-weight-bold);
}

.badge-protected {
  background-color: #f0fdf4;
  color: #166534;
  border: 1px solid #bbf7d0;
}

.badge-revealed {
  background-color: #fffbeb;
  color: #92400e;
  border: 1px solid #fde68a;
}

/* Selector de Modo de Visualización (Ficha Grid vs JSON) */
.view-mode-selector {
  display: flex;
  gap: var(--spacing-4);
  background-color: #ffffff;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-inputs);
  padding: 3px;
}

.mode-switch-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-6);
  padding: 6px 12px;
  border-radius: var(--radius-cards);
  border: none;
  background: transparent;
  color: var(--text-muted);
  font-size: var(--text-caption);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
  transition: all 0.2s ease;
  min-block-size: var(--min-touch-target);
}

.mode-switch-btn:hover {
  color: var(--color-midnight-ink);
}

.mode-switch-btn.active {
  background-color: var(--color-royal-signal);
  color: #ffffff;
}

.pii-warning-banner {
  display: flex;
  align-items: center;
  gap: var(--spacing-8);
  padding: var(--spacing-10) var(--spacing-20);
  background-color: #fef2f2;
  border-bottom: 1px solid #fecaca;
  color: #991b1b;
  font-size: var(--text-caption);
}

.modal-body {
  padding: var(--spacing-20);
  overflow-y: auto;
  overscroll-behavior: contain;
  flex: 1;
}

.json-viewer-wrapper {
  display: flex;
  flex-direction: column;
}

.json-code-viewer {
  background-color: var(--surface-subtle);
  padding: var(--spacing-16);
  border-radius: var(--radius-inputs);
  font-family: var(--font-roboto-mono);
  font-size: 0.85rem;
  overflow-x: auto;
  margin: 0;
  border: 1px solid var(--border-color);
}

.modal-footer {
  padding: var(--spacing-16) var(--spacing-20);
  border-top: 1px solid var(--border-color);
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-12);
}

.builder-btn {
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
}

.btn-primary {
  background-color: var(--color-royal-signal);
  color: #ffffff;
}

.btn-secondary {
  background-color: var(--surface-card);
  border-color: var(--border-color);
  color: var(--color-midnight-ink);
}

.btn-copy {
  min-block-size: var(--min-touch-target);
}
</style>
