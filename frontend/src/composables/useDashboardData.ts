import { ref, computed, nextTick, onMounted } from 'vue';
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
import type MaturinChoroplethMap from '@/components/dashboard/MaturinChoroplethMap.vue';

export type DashboardViewMode = 'visual' | 'accessible';

export function useDashboardData() {
  const surveys = ref<EncuestaItem[]>([]);
  const selectedSurveyId = ref<string>('');
  const isLoadingSurveys = ref<boolean>(true);
  const viewMode = ref<DashboardViewMode>('visual');
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

  return {
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
  };
}

