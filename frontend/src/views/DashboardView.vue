<script setup lang="ts">
import type MaturinChoroplethMap from '@/components/dashboard/MaturinChoroplethMap.vue';
export type DashboardMapRef = InstanceType<typeof MaturinChoroplethMap>;
import KpiCardsGrid from '@/components/dashboard/KpiCardsGrid.vue';
import ModalSplitChart from '@/components/dashboard/ModalSplitChart.vue';
import OdFlowMatrixChart from '@/components/dashboard/OdFlowMatrixChart.vue';
import ParroquiasBarChart from '@/components/dashboard/ParroquiasBarChart.vue';
import CalificacionTpDonutChart from '@/components/dashboard/CalificacionTpDonutChart.vue';
import DificultadesTpBarChart from '@/components/dashboard/DificultadesTpBarChart.vue';
import SeguridadCentroDonutChart from '@/components/dashboard/SeguridadCentroDonutChart.vue';
import AccessibleDataFallback from '@/components/dashboard/AccessibleDataFallback.vue';
import DashboardHeader from '@/components/dashboard/DashboardHeader.vue';
import DashboardQuestionsSection from '@/components/dashboard/DashboardQuestionsSection.vue';
import { useDashboardData } from '@/composables/useDashboardData';

const {
  surveys,
  selectedSurveyId,
  isLoadingSurveys,
  viewMode,
  isExporting,
  isLoadingAnalytics,
  errorMessage,
  kpis,
  parroquias,
  repartoModal,
  matrizOd,
  hasData,
  mapComponentRef,
  currentSurvey,
  calificacionTpData,
  dificultadesTpData,
  seguridadCentroData,
  preguntasMetricas,
  isLoadingPreguntas,
  selectedSectionFilter,
  searchQuery,
  availableSections,
  filteredPreguntas,
  loadInitialSurveys,
  onSurveyChange,
  onRefreshClick,
  toggleViewMode,
  handleExportData
} = useDashboardData();

function resetQuestionFilters() {
  searchQuery.value = '';
  selectedSectionFilter.value = 'todas';
}

defineExpose({
  surveys,
  selectedSurveyId,
  isLoadingSurveys,
  viewMode,
  isExporting,
  isLoadingAnalytics,
  errorMessage,
  kpis,
  parroquias,
  repartoModal,
  matrizOd,
  hasData,
  mapComponentRef,
  currentSurvey,
  calificacionTpData,
  dificultadesTpData,
  seguridadCentroData,
  preguntasMetricas,
  isLoadingPreguntas,
  selectedSectionFilter,
  searchQuery,
  availableSections,
  filteredPreguntas,
  loadInitialSurveys,
  onSurveyChange,
  onRefreshClick,
  toggleViewMode,
  handleExportData
});
</script>

<template>
  <div class="dashboard-page">
    <div class="dashboard-container">
      <DashboardHeader
        :surveys="surveys"
        v-model:selected-survey-id="selectedSurveyId"
        :is-loading-surveys="isLoadingSurveys"
        :is-loading-analytics="isLoadingAnalytics"
        :view-mode="viewMode"
        :is-exporting="isExporting"
        :has-data="hasData"
        @survey-change="onSurveyChange"
        @refresh="onRefreshClick"
        @toggle-view="toggleViewMode"
        @export-data="handleExportData"
      />

      <section
        v-if="errorMessage"
        class="dashboard-error-banner"
        role="alert"
        aria-live="assertive"
      >
        <div class="error-content">
          <i class="pi pi-exclamation-triangle error-icon" aria-hidden="true"></i>
          <div class="error-text">
            <strong class="error-title">No fue posible actualizar las métricas analíticas</strong>
            <p class="error-detail">{{ errorMessage }}</p>
          </div>
        </div>
        <button
          type="button"
          class="btn-retry"
          @click="onRefreshClick"
          aria-label="Reintentar consulta de métricas"
        >
          <i class="pi pi-replay" aria-hidden="true"></i>
          Reintentar
        </button>
      </section>

      <section class="section-kpis" aria-label="Tarjetas de indicadores ejecutivos">
        <KpiCardsGrid
          :kpis="kpis"
          :parroquias="parroquias"
          :reparto-modal="repartoModal"
          :matriz-od="matrizOd"
          :loading="isLoadingAnalytics"
        />
      </section>

      <section
        v-if="viewMode === 'visual'"
        class="dashboard-visual-layout"
        aria-label="Visualizaciones gráficas y matrices de movilidad"
      >
        <div class="grid-two-columns">
          <div class="column-chart">
            <ParroquiasBarChart
              :items="parroquias"
              :loading="isLoadingAnalytics"
            />
          </div>

          <div class="column-chart">
            <CalificacionTpDonutChart
              :data="calificacionTpData"
              :loading="isLoadingAnalytics"
            />
          </div>
        </div>

        <div class="grid-two-columns">
          <div class="column-chart">
            <DificultadesTpBarChart
              :data="dificultadesTpData"
              :loading="isLoadingAnalytics"
            />
          </div>

          <div class="column-chart">
            <SeguridadCentroDonutChart
              :data="seguridadCentroData"
              :loading="isLoadingAnalytics"
            />
          </div>
        </div>

        <div class="grid-full-width">
          <ModalSplitChart
            :items="repartoModal"
            :loading="isLoadingAnalytics"
          />
        </div>

        <div class="grid-full-width">
          <OdFlowMatrixChart
            :items="matrizOd"
            :loading="isLoadingAnalytics"
          />
        </div>

        <DashboardQuestionsSection
          :preguntas-metricas="preguntasMetricas"
          :filtered-preguntas="filteredPreguntas"
          :available-sections="availableSections"
          v-model:selected-section-filter="selectedSectionFilter"
          v-model:search-query="searchQuery"
          :is-loading-preguntas="isLoadingPreguntas"
          @reset-filters="resetQuestionFilters"
        />
      </section>

      <section
        v-else
        class="dashboard-accessible-layout"
        aria-label="Tablas semánticas accesibles de datos"
      >
        <AccessibleDataFallback
          :kpis="kpis"
          :parroquias="parroquias"
          :reparto-modal="repartoModal"
          :matriz-od="matrizOd"
          :preguntas="preguntasMetricas"
        />
      </section>
    </div>
  </div>
</template>

<style scoped>
.dashboard-page {
  width: 100%;
  background-color: var(--surface-ground);
  padding: 0 var(--spacing-16);
}

.dashboard-container {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-24);
  padding-bottom: var(--spacing-40);
}

.dashboard-error-banner {
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: var(--radius-cards);
  padding: var(--spacing-16);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--spacing-12);
}

.error-content {
  display: flex;
  align-items: center;
  gap: var(--spacing-12);
}

.error-icon {
  font-size: 1.5rem;
  color: var(--color-coral-lost);
}

.error-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.error-title {
  font-size: var(--text-body-sm);
  color: #991b1b;
}

.error-detail {
  font-size: var(--text-caption);
  color: #b91c1c;
  margin: 0;
}

.btn-retry {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-6);
  min-height: var(--min-touch-target);
  min-block-size: var(--min-touch-target);
  padding: 0 var(--spacing-16);
  background-color: #fee2e2;
  border: 1px solid #fca5a5;
  border-radius: var(--radius-buttons);
  font-family: var(--font-inter);
  font-size: var(--text-caption);
  font-weight: var(--font-weight-bold);
  color: #991b1b;
  cursor: pointer;
}

.btn-retry:hover {
  background-color: #fecaca;
}

.section-kpis,
.grid-full-width,
.dashboard-accessible-layout {
  width: 100%;
}

.dashboard-visual-layout {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-24);
}

.grid-two-columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-24);
}

.column-map,
.column-chart {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

@media (max-width: 1024px) {
  .grid-two-columns,
  .grid-questions-cards {
    grid-template-columns: 1fr;
  }
}

.survey-dropdown { min-height: var(--min-touch-target); min-block-size: var(--min-touch-target); }
.btn-dashboard { min-height: var(--min-touch-target); min-block-size: var(--min-touch-target); }
.questions-search-input { min-height: var(--min-touch-target); min-block-size: var(--min-touch-target); }
.btn-reset-filters { min-height: var(--min-touch-target); min-block-size: var(--min-touch-target); }

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
