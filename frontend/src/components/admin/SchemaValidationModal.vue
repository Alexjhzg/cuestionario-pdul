<script setup lang="ts">
import type { SchemaValidationResult } from '@/utils/schemaValidator';

defineProps<{
  visible: boolean;
  validationResults: SchemaValidationResult | null;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
}>();
</script>

<template>
  <div
    v-if="visible"
    class="modal-backdrop"
    role="dialog"
    aria-modal="true"
    aria-labelledby="validation-dialog-title"
    @keydown.esc="emit('close')"
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
          @click="emit('close')"
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
          @click="emit('close')"
        >
          Entendido
        </button>
      </footer>
    </div>
  </div>
</template>

<style scoped>
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
</style>

