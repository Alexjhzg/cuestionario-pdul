<script setup lang="ts">
import { useAdminFieldMap } from '@/composables/useAdminFieldMap';
import { formatParroquia } from '@/utils/responseFormatters';
import AdminSurveyFieldMap from '@/components/admin/AdminSurveyFieldMap.vue';
import AdminResponseDetailModal from '@/components/admin/AdminResponseDetailModal.vue';

const props = withDefaults(
  defineProps<{
    initialSurveyId?: string | null;
  }>(),
  {
    initialSurveyId: ''
  }
);

const {
  surveys,
  selectedSurveyId,
  loadingSurveys,
  summary,
  isLoadingMap,
  errorMessage,
  parroquiaFilter,
  deviceFilter,
  onlyAlerts,
  viewMode,
  filteredPoints,
  availableParroquias,
  showDetailModal,
  selectedRespuesta,
  maskPii,
  detailViewMode,
  jsonCopied,
  displayData,
  loadFieldMap,
  inspectPoint,
  closeDetail,
  copyJson
} = useAdminFieldMap(() => props.initialSurveyId);
</script>

<template>
  <div class="admin-field-map-view" role="main" aria-labelledby="field-map-title">
    <header class="field-map-header">
      <div class="header-titles">
        <h1 id="field-map-title" class="field-map-title">Mapa de Levantamiento en Campo</h1>
        <p class="field-map-subtitle">
          Seguimiento georreferenciado de dónde se está levantando cada encuesta, cobertura GPS y alertas de precisión o ubicación remota.
        </p>
      </div>

      <div class="header-actions">
        <div class="survey-selector-wrapper">
          <label for="field-map-survey-select" class="selector-label">Encuesta a Supervisar:</label>
          <select
            id="field-map-survey-select"
            v-model="selectedSurveyId"
            class="survey-select-input"
            :disabled="loadingSurveys"
            data-testid="select-survey-field-map"
          >
            <option value="" disabled>Seleccione una encuesta</option>
            <option v-for="s in surveys" :key="s.id" :value="s.id">
              {{ s.titulo }} ({{ s.total_respuestas }} respuestas)
            </option>
          </select>
        </div>

        <button
          type="button"
          class="refresh-map-btn"
          :disabled="isLoadingMap || !selectedSurveyId"
          data-testid="btn-refresh-field-map"
          @click="loadFieldMap"
        >
          <i :class="['pi', isLoadingMap ? 'pi-spin pi-spinner' : 'pi-refresh']" aria-hidden="true"></i>
          <span>Actualizar mapa</span>
        </button>
      </div>
    </header>

    <div v-if="errorMessage" class="feedback-alert error-alert" role="alert">
      <i class="pi pi-exclamation-triangle" aria-hidden="true"></i>
      <span>{{ errorMessage }}</span>
    </div>

    <!-- Tarjetas KPI de Cobertura GPS -->
    <section class="field-kpis-grid" aria-label="Indicadores de cobertura GPS" data-testid="field-map-kpis">
      <article class="kpi-card">
        <span class="kpi-label">Total Respuestas</span>
        <strong class="kpi-value">{{ summary?.total_respuestas ?? 0 }}</strong>
      </article>
      <article class="kpi-card">
        <span class="kpi-label">Con Punto GPS</span>
        <strong class="kpi-value">
          {{ summary?.total_con_gps ?? 0 }}
          <small class="kpi-sub">({{ (summary?.porcentaje_cobertura_gps ?? 0).toFixed(1) }}%)</small>
        </strong>
      </article>
      <article class="kpi-card">
        <span class="kpi-label">Sin Captura GPS</span>
        <strong class="kpi-value">{{ summary?.total_sin_gps ?? 0 }}</strong>
      </article>
      <article class="kpi-card kpi-alert">
        <span class="kpi-label">Alertas Geográficas / IP</span>
        <strong class="kpi-value">{{ summary?.total_alertas_ubicacion ?? 0 }}</strong>
      </article>
    </section>

    <!-- Barra de Filtros -->
    <section class="filters-bar" aria-label="Filtros del mapa de levantamiento">
      <div class="filter-group">
        <label for="filter-parroquia-map" class="filter-label">Parroquia:</label>
        <select
          id="filter-parroquia-map"
          v-model="parroquiaFilter"
          class="filter-select"
          data-testid="filter-parroquia-map"
        >
          <option value="todas">Todas las parroquias</option>
          <option v-for="par in availableParroquias" :key="par" :value="par">
            {{ formatParroquia(par) }}
          </option>
        </select>
      </div>

      <div class="filter-group">
        <label for="filter-device-map" class="filter-label">Dispositivo:</label>
        <select
          id="filter-device-map"
          v-model="deviceFilter"
          class="filter-select"
          data-testid="filter-device-map"
        >
          <option value="todos">Todos los dispositivos</option>
          <option value="movil">Teléfono móvil</option>
          <option value="tablet">Tablet</option>
          <option value="escritorio">Computadora / Escritorio</option>
          <option value="desconocido">Desconocido</option>
        </select>
      </div>

      <label class="alert-checkbox-label">
        <input
          v-model="onlyAlerts"
          type="checkbox"
          data-testid="checkbox-only-alerts"
        />
        <span>Solo alertas</span>
      </label>

      <button
        type="button"
        class="view-mode-btn"
        data-testid="btn-toggle-map-view-mode"
        @click="viewMode = viewMode === 'map' ? 'table' : 'map'"
      >
        <i :class="['pi', viewMode === 'map' ? 'pi-table' : 'pi-map']" aria-hidden="true"></i>
        <span>{{ viewMode === 'map' ? 'Ver tabla accesible' : 'Ver mapa' }}</span>
      </button>
    </section>

    <!-- Mapa GIS o Tabla Accesible -->
    <AdminSurveyFieldMap
      :points="filteredPoints"
      :view-mode="viewMode"
      :loading="isLoadingMap"
      @inspect-point="inspectPoint"
    />

    <!-- Modal de Inspección de Respuesta con Enmascaramiento PII -->
    <AdminResponseDetailModal
      :open="showDetailModal"
      :respuesta="selectedRespuesta"
      :display-data="displayData"
      v-model:mask-pii="maskPii"
      v-model:detail-view-mode="detailViewMode"
      :json-copied="jsonCopied"
      @close="closeDetail"
      @copy-json="copyJson"
    />
  </div>
</template>

<style scoped>
.admin-field-map-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--spacing-20);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-20);
}

.field-map-header {
  background-color: var(--surface-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-containers);
  padding: var(--spacing-20);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-16);
  box-shadow: var(--shadow-sm);
}

@media (min-width: 900px) {
  .field-map-header {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
  }
}

.field-map-title {
  font-size: var(--text-heading-sm);
  color: var(--color-midnight-ink);
  font-weight: var(--font-weight-bold);
  margin: 0 0 var(--spacing-4) 0;
}

.field-map-subtitle {
  font-size: var(--text-body-sm);
  color: var(--text-muted);
  margin: 0;
}

.header-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: var(--spacing-12);
}

.survey-selector-wrapper {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
  min-width: 240px;
}

.selector-label,
.filter-label {
  font-size: var(--text-caption);
  font-weight: var(--font-weight-semibold);
  color: var(--color-midnight-ink);
}

.survey-select-input,
.filter-select {
  min-block-size: var(--min-touch-target);
  min-height: var(--min-touch-target);
  padding: 0 var(--spacing-12);
  border-radius: var(--radius-inputs);
  border: 1px solid var(--border-color);
  background-color: #ffffff;
  font-size: var(--text-body-sm);
  color: var(--color-midnight-ink);
}

.refresh-map-btn,
.view-mode-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-8);
  min-block-size: var(--min-touch-target);
  min-height: var(--min-touch-target);
  padding: 0 var(--spacing-16);
  border-radius: var(--radius-inputs);
  border: 1px solid var(--color-royal-signal);
  background-color: var(--color-royal-signal);
  color: #ffffff;
  font-size: var(--text-body-sm);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
}

.view-mode-btn {
  background-color: #ffffff;
  color: var(--color-royal-signal);
  margin-left: auto;
}

.refresh-map-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.feedback-alert {
  display: flex;
  align-items: center;
  gap: var(--spacing-12);
  padding: var(--spacing-16);
  border-radius: var(--radius-inputs);
  font-size: var(--text-body-sm);
}

.error-alert {
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
}

.field-kpis-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
  gap: var(--spacing-16);
}

.kpi-card {
  background-color: var(--surface-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-cards);
  padding: var(--spacing-16);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
  box-shadow: var(--shadow-sm);
}

.kpi-alert {
  border-left: 4px solid #f26052;
}

.kpi-label {
  font-size: var(--text-caption);
  color: var(--text-muted);
  font-weight: var(--font-weight-semibold);
}

.kpi-value {
  font-size: 1.5rem;
  color: var(--color-midnight-ink);
  font-family: var(--font-mono);
}

.kpi-sub {
  font-size: var(--text-body-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-muted);
}

.filters-bar {
  background-color: var(--surface-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-containers);
  padding: var(--spacing-16);
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: var(--spacing-16);
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
  min-width: 200px;
}

.alert-checkbox-label {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-8);
  min-block-size: var(--min-touch-target);
  min-height: var(--min-touch-target);
  padding: 0 var(--spacing-12);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-inputs);
  font-size: var(--text-body-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-midnight-ink);
  cursor: pointer;
}
</style>

