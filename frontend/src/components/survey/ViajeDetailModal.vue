<script setup lang="ts">
import { nextTick, onBeforeUnmount, ref, watch } from 'vue';
import type { ViajeOD } from '@/types/survey';
import { formatParroquia } from '@/utils/validation';
import { MOTIVOS_VIAJE, MODOS_TRANSPORTE } from '@/utils/tripCatalogs';

const props = defineProps<{
  open: boolean;
  viaje: ViajeOD | null;
  residenteNombre: string;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
}>();

const backdropRef = ref<HTMLElement | null>(null);
let previousFocused: HTMLElement | null = null;

function handleDocumentKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape' && props.open && props.viaje) {
    emit('close');
  }
}

watch(
  () => props.open && !!props.viaje,
  async (isOpen) => {
    if (isOpen) {
      previousFocused = typeof document !== 'undefined' ? (document.activeElement as HTMLElement | null) : null;
      if (typeof document !== 'undefined') {
        document.addEventListener('keydown', handleDocumentKeydown);
      }
      await nextTick();
      if (backdropRef.value && typeof backdropRef.value.focus === 'function') {
        backdropRef.value.focus();
      }
    } else {
      if (typeof document !== 'undefined') {
        document.removeEventListener('keydown', handleDocumentKeydown);
      }
      if (previousFocused && typeof previousFocused.focus === 'function') {
        previousFocused.focus();
      }
      previousFocused = null;
    }
  },
  { immediate: true }
);

onBeforeUnmount(() => {
  if (typeof document !== 'undefined') {
    document.removeEventListener('keydown', handleDocumentKeydown);
  }
});
</script>

<template>
  <div
    v-if="open && viaje"
    ref="backdropRef"
    class="modal-backdrop"
    role="dialog"
    aria-modal="true"
    aria-labelledby="modal-viaje-title"
    tabindex="-1"
    @click.self="emit('close')"
    @keydown.esc.stop="emit('close')"
  >
    <div class="modal-card">
      <header class="modal-header">
        <h4 id="modal-viaje-title" class="modal-title">
          Detalles del Viaje #{{ viaje.viaje_numero }}
        </h4>
        <button
          type="button"
          class="modal-close-btn"
          aria-label="Cerrar modal de detalles"
          @click="emit('close')"
        >
          <i class="pi pi-times" aria-hidden="true"></i>
        </button>
      </header>

      <div class="modal-body">
        <div class="detail-row">
          <span class="detail-label">Residente:</span>
          <span class="detail-value">{{ residenteNombre }}</span>
        </div>

        <div class="detail-divider"></div>

        <div class="detail-row">
          <span class="detail-label">Zona O-D Origen:</span>
          <strong class="detail-value">{{ formatParroquia(viaje.zona_od_origen) }}</strong>
        </div>
        <div v-if="viaje.origen_direccion" class="detail-row">
          <span class="detail-label">Dirección origen:</span>
          <span class="detail-value">{{ viaje.origen_direccion }}</span>
        </div>

        <div class="detail-divider"></div>

        <div class="detail-row">
          <span class="detail-label">Zona O-D Destino:</span>
          <strong class="detail-value">{{ formatParroquia(viaje.zona_od_destino) }}</strong>
        </div>
        <div v-if="viaje.destino_direccion" class="detail-row">
          <span class="detail-label">Dirección destino:</span>
          <span class="detail-value">{{ viaje.destino_direccion }}</span>
        </div>

        <div class="detail-divider"></div>

        <div class="detail-row detail-horarios-row">
          <div class="horario-col">
            <span class="detail-label">Hora de salida:</span>
            <strong class="detail-value">{{ viaje.hora_salida || 'No especificada' }}</strong>
          </div>
          <div class="horario-arrow" aria-hidden="true">➔</div>
          <div class="horario-col">
            <span class="detail-label">Hora de llegada:</span>
            <strong class="detail-value">{{ viaje.hora_llegada || 'No especificada' }}</strong>
          </div>
        </div>

        <div class="detail-divider"></div>

        <div class="detail-row">
          <span class="detail-label">Motivo del viaje:</span>
          <span class="detail-value">
            {{ MOTIVOS_VIAJE[viaje.motivo_viaje] || 'Otro' }}
            <span v-if="viaje.motivo_viaje_otro"> ({{ viaje.motivo_viaje_otro }})</span>
          </span>
        </div>

        <div class="detail-row">
          <span class="detail-label">Modo principal:</span>
          <span class="detail-value">
            {{ MODOS_TRANSPORTE[viaje.modo_principal] || 'Otro' }}
            <span v-if="viaje.modo_principal_otro"> ({{ viaje.modo_principal_otro }})</span>
          </span>
        </div>

        <div v-if="viaje.modo_secundario" class="detail-row">
          <span class="detail-label">Modo secundario:</span>
          <span class="detail-value">
            {{ MODOS_TRANSPORTE[viaje.modo_secundario] || 'Otro' }}
            <span v-if="viaje.modo_secundario_otro"> ({{ viaje.modo_secundario_otro }})</span>
          </span>
        </div>

        <div class="detail-divider"></div>

        <div class="detail-row">
          <span class="detail-label">Tiempo de viaje:</span>
          <span class="detail-value">{{ viaje.tiempo_viaje_min }} minutos</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Costo del viaje:</span>
          <span class="detail-value">Bs. {{ viaje.costo_viaje_bs }}</span>
        </div>
      </div>

      <footer class="modal-footer">
        <button
          type="button"
          class="survey-btn survey-btn-secondary"
          @click="emit('close')"
        >
          Cerrar
        </button>
      </footer>
    </div>
  </div>
</template>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: var(--spacing-16);
  box-sizing: border-box;
}

.modal-card {
  background-color: var(--surface-card);
  border-radius: var(--radius-containers);
  width: 100%;
  max-width: 520px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-md);
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-16) var(--spacing-20);
  border-bottom: 1px solid var(--border-color);
  background-color: var(--color-fog-surface);
}

.modal-title {
  font-size: var(--text-body);
  font-weight: var(--font-weight-bold);
  color: var(--color-midnight-ink);
  margin: 0;
}

.modal-close-btn {
  background: transparent;
  border: none;
  font-size: 1.125rem;
  color: var(--text-helper);
  cursor: pointer;
  padding: var(--spacing-6);
  border-radius: var(--radius-buttons);
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-close-btn:hover {
  background-color: rgba(0, 0, 0, 0.05);
  color: var(--color-midnight-ink);
}

.modal-body {
  padding: var(--spacing-20);
  overflow-y: auto;
  overscroll-behavior: contain;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-10);
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--spacing-12);
  font-size: var(--text-body-sm);
}

.detail-horarios-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--spacing-8);
  background-color: var(--color-fog-surface);
  padding: var(--spacing-8) var(--spacing-12);
  border-radius: var(--radius-buttons);
}

.horario-col {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.horario-col .detail-label {
  font-size: var(--text-caption);
  color: var(--text-helper);
}

.horario-col .detail-value {
  font-weight: var(--font-weight-bold);
  color: var(--color-midnight-ink);
  text-align: left;
}

.horario-arrow {
  color: var(--color-royal-signal);
  font-size: 1.1rem;
  font-weight: bold;
}

.detail-label {
  color: var(--text-helper);
  flex-shrink: 0;
}

.detail-value {
  color: var(--color-midnight-ink);
  text-align: right;
  word-break: break-word;
}

.detail-divider {
  height: 1px;
  background-color: var(--border-color);
  margin: var(--spacing-4) 0;
}

.modal-footer {
  padding: var(--spacing-12) var(--spacing-20);
  border-top: 1px solid var(--border-color);
  display: flex;
  justify-content: flex-end;
  background-color: var(--color-fog-surface);
}
</style>
