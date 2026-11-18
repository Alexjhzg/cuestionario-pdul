<script setup lang="ts">
import type { EncuestaItem } from '@/services/analyticsApi';
import type { DashboardViewMode } from '@/composables/useDashboardData';

defineProps<{
  surveys: EncuestaItem[];
  selectedSurveyId: string;
  isLoadingSurveys: boolean;
  isLoadingAnalytics: boolean;
  viewMode: DashboardViewMode;
  isExporting: boolean;
  hasData: boolean;
}>();

const emit = defineEmits<{
  (e: 'update:selectedSurveyId', id: string): void;
  (e: 'survey-change'): void;
  (e: 'refresh'): void;
  (e: 'toggle-view'): void;
  (e: 'export-data', formato: 'csv' | 'json'): void;
}>();
</script>

<template>
  <header class="dashboard-header">
    <div class="header-main-info">
      <div class="header-badge">
        <i class="pi pi-chart-bar" aria-hidden="true"></i>
        <span>Dashboard Analítico</span>
      </div>
      <h1 class="header-title">Dashboard de Movilidad Urbana y Participación Ciudadana</h1>
      <p class="header-description">
        Monitoreo en tiempo real de indicadores del Plan de Desarrollo Urbano Local (PDUL Maturín),
        cobertura parroquial, reparto modal y matrices de flujo Origen-Destino.
      </p>
    </div>

    <div class="dashboard-controls" role="toolbar" aria-label="Controles del dashboard">
      <div class="control-group">
        <label for="survey-select" class="control-label">Encuesta a Analizar:</label>
        <div class="select-wrapper">
          <select
            id="survey-select"
            :value="selectedSurveyId"
            class="survey-dropdown"
            :disabled="isLoadingSurveys || isLoadingAnalytics"
            @change="
              emit('update:selectedSurveyId', ($event.target as HTMLSelectElement).value);
              emit('survey-change');
            "
            aria-label="Seleccionar encuesta para visualizar sus indicadores"
          >
            <option v-if="surveys.length === 0" value="" disabled>
              {{ isLoadingSurveys ? 'Cargando encuestas...' : 'No hay encuestas registradas' }}
            </option>
            <option
              v-for="s in surveys"
              :key="s.id"
              :value="s.id"
            >
              {{ s.titulo }} ({{ s.total_respuestas }} respuestas) {{ s.activa ? '• [Activa]' : '• [Inactiva]' }}
            </option>
          </select>
        </div>
      </div>

      <div class="action-buttons">
        <button
          type="button"
          class="btn-dashboard btn-refresh"
          :disabled="isLoadingAnalytics || !selectedSurveyId"
          @click="emit('refresh')"
          aria-label="Actualizar datos del dashboard"
        >
          <i
            class="pi pi-refresh"
            :class="{ 'pi-spin': isLoadingAnalytics }"
            aria-hidden="true"
          ></i>
          <span>Actualizar</span>
        </button>

        <button
          type="button"
          class="btn-dashboard btn-toggle-view"
          :class="{ active: viewMode === 'accessible' }"
          @click="emit('toggle-view')"
          :aria-pressed="viewMode === 'accessible'"
          :aria-label="viewMode === 'visual' ? 'Cambiar a modo de vista tabular accesible' : 'Cambiar a modo de gráficos interactivos'"
        >
          <i
            :class="viewMode === 'visual' ? 'pi pi-table' : 'pi pi-chart-pie'"
            aria-hidden="true"
          ></i>
          <span>{{ viewMode === 'visual' ? 'Ver Tablas Accesibles' : 'Ver Gráficos y Mapas' }}</span>
        </button>

        <button
          type="button"
          class="btn-dashboard btn-export"
          :disabled="isExporting || !hasData"
          @click="emit('export-data', 'csv')"
          aria-label="Descargar datos en formato CSV anonimizado"
        >
          <i class="pi pi-download" aria-hidden="true"></i>
          <span>Exportar CSV</span>
        </button>
      </div>
    </div>
  </header>
</template>

<style scoped>
.dashboard-header {
  background-color: var(--surface-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-containers);
  padding: var(--spacing-24);
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-20);
}

.header-main-info {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-8);
}

.header-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-6);
  background-color: var(--color-lavender-wash);
  color: var(--color-royal-signal);
  font-size: var(--text-caption);
  font-weight: var(--font-weight-bold);
  padding: 4px 12px;
  border-radius: var(--radius-pills);
  width: fit-content;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.header-title {
  font-size: var(--text-heading-sm);
  font-weight: var(--font-weight-bold);
  color: var(--color-midnight-ink);
  margin: 0;
  line-height: 1.3;
}

.header-description {
  font-size: var(--text-body-sm);
  color: var(--text-muted);
  margin: 0;
  line-height: 1.5;
  max-width: 900px;
}

.dashboard-controls {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  flex-wrap: wrap;
  gap: var(--spacing-16);
  padding-top: var(--spacing-16);
  border-top: 1px solid var(--border-color);
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-6);
  min-width: 320px;
  flex: 1;
}

.control-label {
  font-size: var(--text-caption);
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.select-wrapper {
  position: relative;
  width: 100%;
}

.survey-dropdown {
  width: 100%;
  min-height: var(--min-touch-target);
  min-block-size: var(--min-touch-target);
  padding: var(--spacing-10) var(--spacing-16);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-inputs);
  background-color: var(--surface-card);
  font-family: var(--font-inter);
  font-size: var(--text-body-sm);
  color: var(--color-midnight-ink);
  appearance: none;
  background-image: url("data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2212%22%20height%3D%2212%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22%23374151%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpolyline%20points%3D%226%209%2012%2015%2018%209%22%3E%3C%2Fpolyline%3E%3C%2Fsvg%3E");
  background-repeat: no-repeat;
  background-position: right 16px center;
  padding-right: 40px;
  cursor: pointer;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.survey-dropdown:focus {
  outline: none;
  border-color: var(--focus-ring);
  box-shadow: 0 0 0 3px rgba(20, 90, 255, 0.15);
}

.survey-dropdown:disabled {
  background-color: var(--surface-subtle);
  color: var(--text-helper);
  cursor: not-allowed;
}

.action-buttons {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--spacing-10);
}

.btn-dashboard {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-8);
  min-height: var(--min-touch-target);
  min-block-size: var(--min-touch-target);
  padding: 0 var(--spacing-16);
  border-radius: var(--radius-buttons);
  font-family: var(--font-inter);
  font-size: var(--text-body-sm);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.15s ease;
  user-select: none;
  white-space: nowrap;
}

.btn-dashboard:focus-visible {
  outline: 2px solid var(--focus-ring);
  outline-offset: 2px;
}

.btn-refresh {
  background-color: var(--surface-subtle);
  border-color: var(--border-color);
  color: var(--color-midnight-ink);
}

.btn-refresh:hover:not(:disabled) {
  background-color: var(--color-stone-divider);
}

.btn-toggle-view {
  background-color: var(--color-lavender-wash);
  color: var(--color-royal-signal);
  border-color: rgba(20, 90, 255, 0.2);
}

.btn-toggle-view:hover:not(:disabled) {
  background-color: #e0ebff;
}

.btn-toggle-view.active {
  background-color: var(--color-royal-signal);
  color: #ffffff;
}

.btn-export {
  background-color: var(--surface-card);
  border-color: var(--border-color);
  color: var(--color-slate-caption);
}

.btn-export:hover:not(:disabled) {
  border-color: var(--color-royal-signal);
  color: var(--color-royal-signal);
}

.btn-dashboard:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .control-group {
    min-width: 100%;
  }

  .dashboard-controls {
    flex-direction: column;
    align-items: stretch;
  }

  .action-buttons {
    width: 100%;
    justify-content: stretch;
  }

  .btn-dashboard {
    flex: 1;
  }
}
</style>

