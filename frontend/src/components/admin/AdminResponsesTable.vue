<script setup lang="ts">
import { computed } from 'vue';
import type { AdminRespuestaItem } from '@/services/api';
import {
  formatFecha,
  formatParroquia,
  truncateUuid
} from '@/utils/responseFormatters';

const props = defineProps<{
  items: AdminRespuestaItem[];
  isLoading: boolean;
  currentPage: number;
  totalPages: number;
  totalRespuestas: number;
  pageSize: number;
}>();

const emit = defineEmits<{
  (e: 'update:pageSize', value: number): void;
  (e: 'prev-page'): void;
  (e: 'next-page'): void;
  (e: 'open-detail', item: AdminRespuestaItem): void;
}>();

const localPageSize = computed<number>({
  get: () => props.pageSize,
  set: (val: number) => emit('update:pageSize', Number(val))
});
</script>

<template>
  <div class="responses-table-card">
    <!-- Barra superior de metainformación y tamaño de página -->
    <div class="table-top-bar">
      <div class="pagination-info" role="status" aria-live="polite">
        <span class="info-text" data-testid="pagination-info-text">
          Página {{ currentPage }} de {{ totalPages }} (Total: {{ totalRespuestas }} respuestas)
        </span>
      </div>

      <div class="page-size-selector">
        <label for="page-size-select" class="page-size-label">Filas por página:</label>
        <select
          id="page-size-select"
          v-model.number="localPageSize"
          class="page-size-select"
          data-testid="select-page-size"
        >
          <option value="10">10</option>
          <option value="25">25</option>
          <option value="50">50</option>
        </select>
      </div>
    </div>

    <!-- Estado de carga -->
    <div v-if="isLoading" class="loading-state" role="status" aria-live="polite">
      <i class="pi pi-spin pi-spinner loading-spinner" aria-hidden="true"></i>
      <span>Cargando respuestas ciudadanas...</span>
    </div>

    <!-- Estado sin respuestas -->
    <div v-else-if="items.length === 0" class="empty-state">
      <i class="pi pi-inbox empty-icon" aria-hidden="true"></i>
      <h2 class="empty-title">Sin respuestas registradas</h2>
      <p class="empty-desc">
        Esta encuesta aún no ha recibido participaciones de ciudadanos ni encuestadores.
      </p>
    </div>

    <!-- Tabla accesible de respuestas -->
    <div v-else class="table-responsive-wrapper" role="region" aria-label="Tabla de respuestas ciudadanas" tabindex="0">
      <table class="responses-table">
        <caption>Listado paginado de respuestas recibidas con datos demográficos y movilidad</caption>
        <thead>
          <tr>
            <th scope="col">#</th>
            <th scope="col">Fecha de Registro</th>
            <th scope="col">Parroquia</th>
            <th scope="col">Zona O-D</th>
            <th scope="col">Residentes</th>
            <th scope="col">Viajes</th>
            <th scope="col">ID Cliente</th>
            <th scope="col">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="item in items"
            :key="item.id"
            class="response-row"
            :data-testid="`response-row-${item.id}`"
          >
            <td class="col-id">#{{ item.id }}</td>
            <td class="col-date">{{ formatFecha(item.fecha_registro) }}</td>
            <td class="col-parroquia">
              <span class="parroquia-badge">{{ formatParroquia(item.parroquia) }}</span>
            </td>
            <td class="col-zona">{{ item.zona_od || 'No especificada' }}</td>
            <td class="col-count">
              <span class="count-pill">
                <i class="pi pi-user" aria-hidden="true"></i>
                {{ Array.isArray(item.datos?.residentes) ? item.datos.residentes.length : 0 }}
              </span>
            </td>
            <td class="col-count">
              <span class="count-pill">
                <i class="pi pi-car" aria-hidden="true"></i>
                {{ Array.isArray(item.datos?.viajes) ? item.datos.viajes.length : 0 }}
              </span>
            </td>
            <td class="col-uuid">
              <code class="client-id-code" :title="item.client_submission_id || ''">
                {{ truncateUuid(item.client_submission_id) }}
              </code>
            </td>
            <td class="col-actions">
              <button
                type="button"
                class="btn-detail"
                :aria-label="`Ver detalle de respuesta #${item.id}`"
                @click="emit('open-detail', item)"
                :data-testid="`btn-detail-${item.id}`"
              >
                <i class="pi pi-eye" aria-hidden="true"></i>
                <span>Ver Detalle</span>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Controles inferiores de paginación -->
    <footer class="pagination-footer">
      <button
        type="button"
        class="page-btn"
        :disabled="currentPage <= 1 || isLoading"
        aria-label="Página anterior"
        @click="emit('prev-page')"
        data-testid="btn-prev-page"
      >
        <i class="pi pi-chevron-left" aria-hidden="true"></i>
        <span>Anterior</span>
      </button>

      <span class="current-page-badge" aria-current="page">
        Página {{ currentPage }} de {{ totalPages }}
      </span>

      <button
        type="button"
        class="page-btn"
        :disabled="currentPage >= totalPages || isLoading"
        aria-label="Página siguiente"
        @click="emit('next-page')"
        data-testid="btn-next-page"
      >
        <span>Siguiente</span>
        <i class="pi pi-chevron-right" aria-hidden="true"></i>
      </button>
    </footer>
  </div>
</template>

<style scoped>
/* Tarjeta contenedora de tabla */
.responses-table-card {
  background-color: var(--surface-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-containers);
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.table-top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-16) var(--spacing-20);
  border-bottom: 1px solid var(--border-color);
  background-color: var(--surface-subtle);
  flex-wrap: wrap;
  gap: var(--spacing-12);
}

.info-text {
  font-size: var(--text-body-sm);
  color: var(--text-body-color);
  font-weight: var(--font-weight-medium);
}

.page-size-selector {
  display: flex;
  align-items: center;
  gap: var(--spacing-8);
}

.page-size-label {
  font-size: var(--text-caption);
  color: var(--text-muted);
}

.page-size-select {
  min-block-size: var(--min-touch-target);
  min-height: var(--min-touch-target);
  padding: 0 var(--spacing-12);
  border-radius: var(--radius-cards);
  border: 1px solid var(--border-color);
  background-color: #ffffff;
  font-size: var(--text-caption);
  color: var(--color-midnight-ink);
}

/* Tabla */
.table-responsive-wrapper {
  overflow-x: auto;
  width: 100%;
}

.responses-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.responses-table caption {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}

.responses-table th {
  background-color: #ffffff;
  padding: var(--spacing-16);
  font-size: var(--text-caption);
  text-transform: uppercase;
  color: var(--text-muted);
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0.5px;
  border-bottom: 2px solid var(--border-color);
}

.responses-table td {
  padding: var(--spacing-16);
  border-bottom: 1px solid var(--border-color);
  font-size: var(--text-body-sm);
  vertical-align: middle;
}

.response-row:hover {
  background-color: var(--color-lavender-wash);
}

.col-id {
  font-family: var(--font-roboto-mono);
  font-weight: var(--font-weight-bold);
  color: var(--color-royal-signal);
}

.col-date {
  color: var(--text-body-color);
  font-size: var(--text-caption);
}

.parroquia-badge {
  display: inline-block;
  background-color: var(--surface-subtle);
  color: var(--color-midnight-ink);
  padding: var(--spacing-4) var(--spacing-8);
  border-radius: var(--radius-cards);
  font-size: var(--text-caption);
  font-weight: var(--font-weight-semibold);
}

.count-pill {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-4);
  background-color: var(--surface-subtle);
  padding: var(--spacing-4) var(--spacing-8);
  border-radius: var(--radius-pills);
  font-size: var(--text-caption);
  font-weight: var(--font-weight-medium);
}

.client-id-code {
  font-family: var(--font-roboto-mono);
  font-size: 0.75rem;
  color: var(--text-helper);
  background-color: var(--surface-subtle);
  padding: 2px 6px;
  border-radius: 4px;
}

.btn-detail {
  min-block-size: var(--min-touch-target);
  min-height: var(--min-touch-target);
  padding: 0 var(--spacing-16);
  border-radius: var(--radius-cards);
  border: 1px solid var(--border-color);
  background-color: #ffffff;
  color: var(--color-midnight-ink);
  font-size: var(--text-caption);
  font-weight: var(--font-weight-semibold);
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-6);
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-detail:hover {
  background-color: var(--color-lavender-wash);
  border-color: var(--color-royal-signal);
  color: var(--color-royal-signal);
}

/* Paginación */
.pagination-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-16) var(--spacing-20);
  background-color: var(--surface-subtle);
  border-top: 1px solid var(--border-color);
}

.page-btn {
  min-block-size: var(--min-touch-target);
  min-height: var(--min-touch-target);
  padding: 0 var(--spacing-16);
  border-radius: var(--radius-cards);
  border: 1px solid var(--border-color);
  background-color: #ffffff;
  color: var(--color-midnight-ink);
  font-size: var(--text-body-sm);
  font-weight: var(--font-weight-semibold);
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-6);
  cursor: pointer;
  transition: all 0.2s ease;
}

.page-btn:hover:not(:disabled) {
  background-color: var(--color-lavender-wash);
  border-color: var(--color-royal-signal);
  color: var(--color-royal-signal);
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.current-page-badge {
  font-size: var(--text-body-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-body-color);
}

.loading-state,
.empty-state {
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
