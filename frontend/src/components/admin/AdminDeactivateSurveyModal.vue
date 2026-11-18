<script setup lang="ts">
import type { EncuestaAdminItem } from '@/services/api';

defineProps<{
  open: boolean;
  survey: EncuestaAdminItem | null;
}>();

const emit = defineEmits<{
  (e: 'cancel'): void;
  (e: 'confirm'): void;
}>();
</script>

<template>
  <div
    v-if="open"
    class="modal-backdrop"
    role="dialog"
    aria-modal="true"
    aria-labelledby="confirm-dialog-title"
    @keydown.esc="emit('cancel')"
  >
    <div class="modal-dialog">
      <header class="modal-header">
        <h3 id="confirm-dialog-title" class="modal-title">¿Desactivar Encuesta?</h3>
        <button
          type="button"
          class="modal-close-btn"
          aria-label="Cerrar modal"
          @click="emit('cancel')"
        >
          <i class="pi pi-times"></i>
        </button>
      </header>

      <div class="modal-body">
        <p class="modal-text">
          Está a punto de desactivar la encuesta:
        </p>
        <strong class="survey-name-highlight">{{ survey?.titulo }}</strong>
        <p class="modal-warning">
          <i class="pi pi-exclamation-triangle" aria-hidden="true"></i>
          Mientras permanezca inactiva, los ciudadanos y encuestadores de campo no podrán enviar nuevas respuestas a este instrumento.
        </p>
      </div>

      <footer class="modal-footer">
        <button
          type="button"
          class="admin-btn btn-secondary"
          @click="emit('cancel')"
          data-testid="btn-cancel-deactivation"
        >
          <span>Cancelar</span>
        </button>
        <button
          type="button"
          class="admin-btn btn-danger"
          @click="emit('confirm')"
          data-testid="btn-confirm-deactivation"
        >
          <i class="pi pi-ban" aria-hidden="true"></i>
          <span>Sí, Desactivar Encuesta</span>
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
  padding: var(--spacing-20);
  z-index: 9999;
}

.modal-dialog {
  background-color: #ffffff;
  border-radius: var(--radius-containers);
  width: 100%;
  max-width: 500px;
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

.modal-close-btn {
  min-block-size: var(--min-touch-target);
  min-height: var(--min-touch-target);
  width: 48px;
  height: 48px;
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-body {
  padding: var(--spacing-20);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-12);
}

.modal-text {
  margin: 0;
  color: var(--text-body-color);
}

.survey-name-highlight {
  color: var(--color-midnight-ink);
  font-size: var(--text-body);
}

.modal-warning {
  margin: 0;
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
  padding: var(--spacing-12);
  border-radius: var(--radius-cards);
  font-size: var(--text-caption);
  display: flex;
  gap: var(--spacing-8);
  align-items: flex-start;
}

.modal-footer {
  padding: var(--spacing-16) var(--spacing-20);
  border-top: 1px solid var(--border-color);
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-12);
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

.btn-secondary {
  background-color: var(--surface-card);
  border-color: var(--border-color);
  color: var(--color-midnight-ink);
}

.btn-danger {
  background-color: var(--color-coral-lost);
  color: #ffffff;
}
</style>

