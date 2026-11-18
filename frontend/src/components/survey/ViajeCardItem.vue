<script setup lang="ts">
import type { ViajeOD } from '@/types/survey';
import { formatParroquia } from '@/utils/validation';
import { MOTIVOS_VIAJE, MODOS_TRANSPORTE } from '@/utils/tripCatalogs';

defineProps<{
  viaje: ViajeOD;
  index: number;
  residenteNombre: string;
}>();

const emit = defineEmits<{
  (e: 'ver-detalles', viaje: ViajeOD): void;
  (e: 'agregar-regreso', viaje: ViajeOD): void;
  (e: 'eliminar', index: number): void;
}>();
</script>

<template>
  <article class="viaje-card" role="listitem">
    <div class="viaje-card-badge">
      <span>Viaje #{{ index + 1 }}</span>
      <span class="persona-tag">{{ residenteNombre }}</span>
    </div>

    <div class="viaje-route">
      <div class="route-point">
        <i class="pi pi-map-marker origin-icon" aria-hidden="true"></i>
        <span class="route-label">Origen:</span>
        <strong class="route-value">{{ formatParroquia(viaje.zona_od_origen) }}</strong>
      </div>
      <div class="route-arrow" aria-hidden="true">
        <i class="pi pi-arrow-down"></i>
      </div>
      <div class="route-point">
        <i class="pi pi-flag destination-icon" aria-hidden="true"></i>
        <span class="route-label">Destino:</span>
        <strong class="route-value">{{ formatParroquia(viaje.zona_od_destino) }}</strong>
      </div>
    </div>

    <div class="viaje-details">
      <span><i class="pi pi-compass" aria-hidden="true"></i> {{ MOTIVOS_VIAJE[viaje.motivo_viaje] || 'Otro' }}</span>
      <span><i class="pi pi-car" aria-hidden="true"></i> {{ MODOS_TRANSPORTE[viaje.modo_principal] || 'Transporte' }}</span>
      <span><i class="pi pi-clock" aria-hidden="true"></i> {{ viaje.tiempo_viaje_min }} min</span>
      <span v-if="viaje.costo_viaje_bs > 0"><i class="pi pi-money-bill" aria-hidden="true"></i> Bs. {{ viaje.costo_viaje_bs }}</span>
    </div>

    <div class="viaje-acciones">
      <button
        type="button"
        class="action-btn details-btn"
        :aria-label="`Ver todos los detalles del viaje ${index + 1}`"
        @click="emit('ver-detalles', viaje)"
      >
        <i class="pi pi-eye" aria-hidden="true"></i>
        <span>Ver más</span>
      </button>

      <button
        type="button"
        class="action-btn return-btn"
        :aria-label="`Agregar viaje de regreso a casa para el viaje ${index + 1} desde ${formatParroquia(viaje.zona_od_destino)}`"
        @click="emit('agregar-regreso', viaje)"
      >
        <i class="pi pi-refresh" aria-hidden="true"></i>
        <span>Agregar viaje de regreso a casa</span>
      </button>

      <button
        type="button"
        class="action-btn delete-btn"
        :aria-label="`Eliminar viaje ${index + 1} de ${formatParroquia(viaje.zona_od_origen)} a ${formatParroquia(viaje.zona_od_destino)}`"
        @click="emit('eliminar', index)"
      >
        <i class="pi pi-trash" aria-hidden="true"></i>
        <span>Eliminar</span>
      </button>
    </div>
  </article>
</template>

<style scoped>
.viaje-card {
  background-color: var(--surface-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-cards);
  padding: var(--spacing-16);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-12);
  box-shadow: var(--shadow-sm);
  box-sizing: border-box;
}

.viaje-card-badge {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: var(--text-caption);
  font-weight: var(--font-weight-bold);
  color: var(--color-royal-signal);
}

.persona-tag {
  background-color: var(--color-lavender-wash);
  color: var(--color-royal-signal);
  padding: 2px 8px;
  border-radius: var(--radius-buttons);
}

.viaje-route {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-6);
  background-color: var(--color-fog-surface);
  padding: var(--spacing-10);
  border-radius: var(--radius-cards);
}

.route-point {
  display: flex;
  align-items: center;
  gap: var(--spacing-6);
  font-size: var(--text-body-sm);
}

.origin-icon {
  color: var(--color-royal-signal);
}

.destination-icon {
  color: var(--color-coral-lost);
}

.route-arrow {
  padding-left: 20px;
  font-size: 0.75rem;
  color: var(--text-helper);
}

.viaje-details {
  display: flex;
  gap: var(--spacing-16);
  font-size: var(--text-body-sm);
  color: var(--text-muted);
}

.viaje-acciones {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-8);
  margin-top: var(--spacing-4);
}

@media (min-width: 480px) {
  .viaje-acciones {
    flex-direction: row;
    align-items: center;
  }
}

.action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-6);
  padding: 8px 14px;
  min-block-size: var(--min-touch-target);
  min-inline-size: var(--min-touch-target);
  border-radius: var(--radius-buttons);
  font-size: var(--text-body-sm);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  border: 1px solid var(--border-color);
  background-color: var(--surface-card);
  transition: all 0.15s ease;
}

.details-btn {
  background-color: var(--color-fog-surface);
  color: var(--color-midnight-ink);
  border-color: var(--border-color);
}

.details-btn:hover {
  background-color: #e2e8f0;
}

.return-btn {
  background-color: var(--color-lavender-wash);
  color: var(--color-royal-signal);
  border-color: #c7d7fe;
  flex: 1;
}

.return-btn:hover {
  background-color: #e0ebfe;
}

.delete-btn {
  color: var(--color-coral-lost);
  border-color: #fecaca;
  background-color: #fef2f2;
}

.delete-btn:hover {
  background-color: #fee2e2;
}
</style>
