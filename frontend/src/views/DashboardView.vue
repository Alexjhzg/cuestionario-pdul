<script setup lang="ts">
import { ref, onMounted, computed, nextTick } from 'vue';
import { exportarRespuestasAdmin, descargarBlob } from '@/services/api';
import {
  fetchEncuestas,
  fetchMetricasCampo,
  fetchPreguntasMetricas,
  type EncuestaItem,
  type EChartsSeriesData,
  type PreguntaMetricaItem
} from '@/services/analyticsApi';
import { useAnalytics } from '@/composables/useAnalytics';
import KpiCardsGrid from '@/components/dashboard/KpiCardsGrid.vue';
import MaturinChoroplethMap from '@/components/dashboard/MaturinChoroplethMap.vue';
import ModalSplitChart from '@/components/dashboard/ModalSplitChart.vue';
import OdFlowMatrixChart from '@/components/dashboard/OdFlowMatrixChart.vue';
import ParroquiasBarChart from '@/components/dashboard/ParroquiasBarChart.vue';
import CalificacionTpDonutChart from '@/components/dashboard/CalificacionTpDonutChart.vue';
import DificultadesTpBarChart from '@/components/dashboard/DificultadesTpBarChart.vue';
import SeguridadCentroDonutChart from '@/components/dashboard/SeguridadCentroDonutChart.vue';
import QuestionChartCard from '@/components/dashboard/QuestionChartCard.vue';
import AccessibleDataFallback from '@/components/dashboard/AccessibleDataFallback.vue';

type ViewMode = 'visual' | 'accessible';

const surveys = ref<EncuestaItem[]>([]);
const selectedSurveyId = ref<string>('');
const isLoadingSurveys = ref<boolean>(true);
const viewMode = ref<ViewMode>('visual');
const isExporting = ref<boolean>(false);

const {
  isLoading: isLoadingAnalytics,
  errorMessage,
  kpis,
  parroquias,
  repartoModal,
  matrizOd,
  hasData,
  loadAnalytics,
  refresh
} = useAnalytics();

const mapComponentRef = ref<InstanceType<typeof MaturinChoroplethMap> | null>(null);

const currentSurvey = computed<EncuestaItem | undefined>(() => {
  return surveys.value.find((s) => s.id === selectedSurveyId.value);
});

const calificacionTpData = ref<EChartsSeriesData | null>(null);
const dificultadesTpData = ref<EChartsSeriesData | null>(null);
const seguridadCentroData = ref<EChartsSeriesData | null>(null);

const preguntasMetricas = ref<PreguntaMetricaItem[]>([]);
const isLoadingPreguntas = ref<boolean>(false);
const selectedSectionFilter = ref<string>('todas');
const searchQuery = ref<string>('');

const availableSections = computed<string[]>(() => {
  const set = new Set<string>();
  preguntasMetricas.value.forEach((p) => {
    if (p.seccion) set.add(p.seccion);
  });
  return Array.from(set);
});

const filteredPreguntas = computed<PreguntaMetricaItem[]>(() => {
  let list = preguntasMetricas.value;
  if (selectedSectionFilter.value !== 'todas') {
    list = list.filter((p) => p.seccion === selectedSectionFilter.value);
  }
  const q = searchQuery.value.trim().toLowerCase();
  if (q) {
    list = list.filter(
      (p) =>
        p.pregunta.toLowerCase().includes(q) ||
        p.seccion.toLowerCase().includes(q) ||
        p.clave.toLowerCase().includes(q)
    );
  }
  return list;
});

async function loadPreguntasMetricas(surveyId: string) {
  isLoadingPreguntas.value = true;
  try {
    preguntasMetricas.value = await fetchPreguntasMetricas(surveyId);
  } catch (err) {
    console.warn('No se pudieron cargar métricas de todas las preguntas:', err);
    preguntasMetricas.value = [];
  } finally {
    isLoadingPreguntas.value = false;
  }
}

async function loadExtraMetrics(surveyId: string) {
  try {
    const [calif, dif, seg] = await Promise.allSettled([
      fetchMetricasCampo(surveyId, 'calificacion_servicio_tp'),
      fetchMetricasCampo(surveyId, 'dificultades_acceso_tp'),
      fetchMetricasCampo(surveyId, 'seguridad_centro')
    ]);
    calificacionTpData.value = calif.status === 'fulfilled' ? calif.value : null;
    dificultadesTpData.value = dif.status === 'fulfilled' ? dif.value : null;
    seguridadCentroData.value = seg.status === 'fulfilled' ? seg.value : null;
  } catch (err) {
    console.warn('No se pudieron cargar métricas complementarias:', err);
    calificacionTpData.value = null;
    dificultadesTpData.value = null;
    seguridadCentroData.value = null;
  }
}

async function loadInitialSurveys() {
  isLoadingSurveys.value = true;
  try {
    const list = await fetchEncuestas();
    surveys.value = list;

    if (list.length > 0) {
      // Priorizar la encuesta activa o la primera de la lista
      const active = list.find((s) => s.activa);
      selectedSurveyId.value = active ? active.id : list[0].id;
      await Promise.all([
        loadAnalytics(selectedSurveyId.value),
        loadExtraMetrics(selectedSurveyId.value),
        loadPreguntasMetricas(selectedSurveyId.value)
      ]);
    }
  } catch (err: any) {
    console.error('Error al cargar encuestas para el dashboard:', err);
  } finally {
    isLoadingSurveys.value = false;
  }
}

async function onSurveyChange() {
  if (selectedSurveyId.value) {
    await Promise.all([
      loadAnalytics(selectedSurveyId.value),
      loadExtraMetrics(selectedSurveyId.value),
      loadPreguntasMetricas(selectedSurveyId.value)
    ]);
    await nextTick();
    mapComponentRef.value?.invalidateSize();
  }
}

async function onRefreshClick() {
  await Promise.all([
    refresh(),
    selectedSurveyId.value ? loadExtraMetrics(selectedSurveyId.value) : Promise.resolve(),
    selectedSurveyId.value ? loadPreguntasMetricas(selectedSurveyId.value) : Promise.resolve()
  ]);
  await nextTick();
  mapComponentRef.value?.invalidateSize();
}

function toggleViewMode() {
  viewMode.value = viewMode.value === 'visual' ? 'accessible' : 'visual';
  if (viewMode.value === 'visual') {
    nextTick(() => {
      mapComponentRef.value?.invalidateSize();
    });
  }
}

async function handleExportData(formato: 'csv' | 'json') {
  if (!selectedSurveyId.value) return;
  isExporting.value = true;
  try {
    const blob = await exportarRespuestasAdmin(selectedSurveyId.value, formato, true);
    const slug = currentSurvey.value?.slug || 'encuesta';
    const filename = `${slug}_analitica_pdul_${new Date().toISOString().slice(0, 10)}.${formato}`;
    descargarBlob(blob, filename);
  } catch (err) {
    console.error('Error al exportar respuestas:', err);
  } finally {
    isExporting.value = false;
  }
}

onMounted(() => {
  loadInitialSurveys();
});
</script>

<template>
  <div class="dashboard-page">
    <div class="dashboard-container">
      <!-- Barra Superior de Encabezado y Controles -->
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

        <!-- Barra de Herramientas y Filtros -->
        <div class="dashboard-controls" role="toolbar" aria-label="Controles del dashboard">
          <!-- Selector de Encuesta -->
          <div class="control-group">
            <label for="survey-select" class="control-label">Encuesta a Analizar:</label>
            <div class="select-wrapper">
              <select
                id="survey-select"
                v-model="selectedSurveyId"
                class="survey-dropdown"
                :disabled="isLoadingSurveys || isLoadingAnalytics"
                @change="onSurveyChange"
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

          <!-- Botones de Acción -->
          <div class="action-buttons">
            <!-- Botón Refrescar -->
            <button
              type="button"
              class="btn-dashboard btn-refresh"
              :disabled="isLoadingAnalytics || !selectedSurveyId"
              @click="onRefreshClick"
              aria-label="Actualizar datos del dashboard"
            >
              <i
                class="pi pi-refresh"
                :class="{ 'pi-spin': isLoadingAnalytics }"
                aria-hidden="true"
              ></i>
              <span>Actualizar</span>
            </button>

            <!-- Botón Alternar Vista Accesible / Gráfica -->
            <button
              type="button"
              class="btn-dashboard btn-toggle-view"
              :class="{ active: viewMode === 'accessible' }"
              @click="toggleViewMode"
              :aria-pressed="viewMode === 'accessible'"
              :aria-label="viewMode === 'visual' ? 'Cambiar a modo de vista tabular accesible' : 'Cambiar a modo de gráficos interactivos'"
            >
              <i
                :class="viewMode === 'visual' ? 'pi pi-table' : 'pi pi-chart-pie'"
                aria-hidden="true"
              ></i>
              <span>{{ viewMode === 'visual' ? 'Ver Tablas Accesibles' : 'Ver Gráficos y Mapas' }}</span>
            </button>

            <!-- Botón Exportar CSV -->
            <button
              type="button"
              class="btn-dashboard btn-export"
              :disabled="isExporting || !hasData"
              @click="handleExportData('csv')"
              aria-label="Descargar datos en formato CSV anonimizado"
            >
              <i class="pi pi-download" aria-hidden="true"></i>
              <span>Exportar CSV</span>
            </button>
          </div>
        </div>
      </header>

      <!-- Mensaje de Error si la consulta falla -->
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

      <!-- 1. Cuadrícula de Tarjetas Ejecutivas de KPIs (F57) -->
      <section class="section-kpis" aria-label="Tarjetas de indicadores ejecutivos">
        <KpiCardsGrid
          :kpis="kpis"
          :parroquias="parroquias"
          :reparto-modal="repartoModal"
          :matriz-od="matrizOd"
          :loading="isLoadingAnalytics"
        />
      </section>

      <!-- 2. Contenido Principal: Gráficos Interactivos vs Tablas Accesibles -->
      <!-- Vista 2A: Gráficos Interactivos -->
      <section
        v-if="viewMode === 'visual'"
        class="dashboard-visual-layout"
        aria-label="Visualizaciones gráficas y matrices de movilidad"
      >
        <!-- Fila de Distribución Parroquial y Calidad de Transporte -->
        <div class="grid-two-columns">
          <!-- Distribución de Encuestas por Parroquia -->
          <div class="column-chart">
            <ParroquiasBarChart
              :items="parroquias"
              :loading="isLoadingAnalytics"
            />
          </div>

          <!-- Percepción / Evaluación del Transporte Público -->
          <div class="column-chart">
            <CalificacionTpDonutChart
              :data="calificacionTpData"
              :loading="isLoadingAnalytics"
            />
          </div>
        </div>

        <!-- Fila de Dificultades de Transporte y Percepción de Seguridad -->
        <div class="grid-two-columns">
          <!-- Dificultades de Acceso al Transporte Público -->
          <div class="column-chart">
            <DificultadesTpBarChart
              :data="dificultadesTpData"
              :loading="isLoadingAnalytics"
            />
          </div>

          <!-- Percepción de Seguridad en el Centro -->
          <div class="column-chart">
            <SeguridadCentroDonutChart
              :data="seguridadCentroData"
              :loading="isLoadingAnalytics"
            />
          </div>
        </div>

        <!-- Gráfico de Reparto Modal -->
        <div class="grid-full-width">
          <ModalSplitChart
            :items="repartoModal"
            :loading="isLoadingAnalytics"
          />
        </div>

        <!-- Matriz de Flujos Origen-Destino -->
        <div class="grid-full-width">
          <OdFlowMatrixChart
            :items="matrizOd"
            :loading="isLoadingAnalytics"
          />
        </div>

        <!-- 3. Sección de Análisis Gráfico por Cada Pregunta del Cuestionario -->
        <section class="section-all-questions" aria-label="Análisis gráfico pregunta por pregunta">
          <div class="questions-section-header">
            <div class="questions-title-block">
              <div class="header-badge">
                <i class="pi pi-chart-pie" aria-hidden="true"></i>
                <span>Cuestionario Completo</span>
              </div>
              <h2 class="questions-section-title">Análisis Estadístico por Cada Pregunta</h2>
              <p class="questions-section-desc">
                Gráficos individuales que representan textualmente la pregunta exacta formulada en cada una de las 8 secciones técnicas del Cuestionario PDUL Maturín.
              </p>
            </div>

            <!-- Barra de Filtros y Búsqueda Interactiva -->
            <div class="questions-filter-toolbar">
              <!-- Búsqueda en tiempo real -->
              <div class="search-input-wrapper">
                <i class="pi pi-search search-icon" aria-hidden="true"></i>
                <input
                  type="text"
                  v-model="searchQuery"
                  placeholder="Filtrar por texto de pregunta o clave..."
                  class="questions-search-input"
                  aria-label="Filtrar preguntas por texto"
                />
                <button
                  v-if="searchQuery"
                  type="button"
                  class="btn-clear-search"
                  @click="searchQuery = ''"
                  aria-label="Limpiar filtro de búsqueda"
                >
                  <i class="pi pi-times" aria-hidden="true"></i>
                </button>
              </div>

              <!-- Selector de Secciones por Botones Tipo Pill -->
              <div class="section-pills-list" role="group" aria-label="Filtrar preguntas por sección">
                <button
                  type="button"
                  class="section-pill-btn"
                  :class="{ active: selectedSectionFilter === 'todas' }"
                  @click="selectedSectionFilter = 'todas'"
                  :aria-pressed="selectedSectionFilter === 'todas'"
                >
                  Todas ({{ preguntasMetricas.length }})
                </button>
                <button
                  v-for="sec in availableSections"
                  :key="sec"
                  type="button"
                  class="section-pill-btn"
                  :class="{ active: selectedSectionFilter === sec }"
                  @click="selectedSectionFilter = sec"
                  :aria-pressed="selectedSectionFilter === sec"
                >
                  {{ sec.split(':')[0] }}
                </button>
              </div>
            </div>
          </div>

          <!-- Cuadrícula de Gráficos de Preguntas -->
          <div v-if="filteredPreguntas.length > 0" class="grid-questions-cards">
            <QuestionChartCard
              v-for="item in filteredPreguntas"
              :key="item.clave"
              :item="item"
              :loading="isLoadingPreguntas"
            />
          </div>

          <!-- Estado Vacío cuando no hay coincidencias de búsqueda -->
          <div v-else-if="!isLoadingPreguntas" class="empty-questions-state">
            <i class="pi pi-search-minus empty-icon" aria-hidden="true"></i>
            <p class="empty-text">No se encontraron preguntas que coincidan con "{{ searchQuery }}".</p>
            <button
              type="button"
              class="btn-reset-filters"
              @click="searchQuery = ''; selectedSectionFilter = 'todas'"
            >
              Restablecer filtros
            </button>
          </div>
        </section>
      </section>

      <!-- Vista 2B: Tablas de Datos Accesibles (WCAG AA - F61) -->
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

/* Encabezado */
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

/* Controles de Dashboard */
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

/* Banner de Error */
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

/* Sección KPIs */
.section-kpis {
  width: 100%;
}

/* Layout de Visualizaciones */
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

.grid-full-width {
  width: 100%;
}

/* Layout Accesible */
.dashboard-accessible-layout {
  width: 100%;
}

/* Responsividad */
/* Sección de Todas las Preguntas */
.section-all-questions {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-20);
  margin-top: var(--spacing-16);
  padding-top: var(--spacing-24);
  border-top: 2px dashed var(--border-color);
}

.questions-section-header {
  background-color: var(--surface-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-containers);
  padding: var(--spacing-20);
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-16);
}

.questions-title-block {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-8);
}

.questions-section-title {
  font-size: var(--text-heading-sm);
  font-weight: var(--font-weight-bold);
  color: var(--color-midnight-ink);
  margin: 0;
}

.questions-section-desc {
  font-size: var(--text-body-sm);
  color: var(--text-muted);
  margin: 0;
  line-height: 1.5;
  max-width: 900px;
}

.questions-filter-toolbar {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-12);
  padding-top: var(--spacing-12);
  border-top: 1px solid var(--border-color);
}

.search-input-wrapper {
  position: relative;
  width: 100%;
  max-width: 600px;
}

.search-icon {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-slate-caption);
  pointer-events: none;
}

.questions-search-input {
  width: 100%;
  min-height: var(--min-touch-target);
  padding: var(--spacing-10) var(--spacing-36) var(--spacing-10) 40px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-inputs);
  background-color: var(--surface-card);
  font-family: var(--font-inter);
  font-size: var(--text-body-sm);
  color: var(--color-midnight-ink);
  transition: border-color var(--transition-base), box-shadow var(--transition-base);
}

.questions-search-input:focus {
  outline: none;
  border-color: var(--color-royal-signal);
  box-shadow: 0 0 0 3px rgba(20, 90, 255, 0.15);
}

.btn-clear-search {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: var(--color-slate-caption);
  cursor: pointer;
  padding: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-clear-search:hover {
  color: var(--color-midnight-ink);
}

.section-pills-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-8);
}

.section-pill-btn {
  display: inline-flex;
  align-items: center;
  min-height: 40px;
  padding: 6px 14px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-pills);
  background-color: var(--surface-card);
  color: var(--text-primary);
  font-family: var(--font-inter);
  font-size: 0.8rem;
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all var(--transition-base);
}

.section-pill-btn:hover {
  border-color: var(--color-royal-signal);
  color: var(--color-royal-signal);
}

.section-pill-btn.active {
  background-color: var(--color-royal-signal);
  border-color: var(--color-royal-signal);
  color: #ffffff;
  font-weight: var(--font-weight-bold);
}

.grid-questions-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-20);
}

.empty-questions-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-12);
  padding: var(--spacing-40) var(--spacing-20);
  background-color: var(--surface-card);
  border: 1px dashed var(--border-color);
  border-radius: var(--radius-containers);
  text-align: center;
}

.empty-icon {
  font-size: 2.5rem;
  color: var(--color-slate-caption);
}

.empty-text {
  font-size: var(--text-body);
  color: var(--text-muted);
  max-width: 500px;
  margin: 0;
}

.btn-reset-filters {
  min-height: var(--min-touch-target);
  padding: 0 var(--spacing-20);
  background-color: var(--color-royal-signal);
  color: #ffffff;
  border: none;
  border-radius: var(--radius-buttons);
  font-family: var(--font-inter);
  font-size: var(--text-body-sm);
  font-weight: var(--font-weight-bold);
  cursor: pointer;
}

@media (max-width: 1024px) {
  .grid-two-columns,
  .grid-questions-cards {
    grid-template-columns: 1fr;
  }
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
