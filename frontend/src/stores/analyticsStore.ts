import { computed, ref } from 'vue';
import {
  AnalyticsApiError,
  fetchAllAnalytics,
  type AnalyticsDataset,
  type KpiMetrics,
  type MatrizODItem,
  type ParroquiaResultado,
  type RepartoModalItem
} from '@/services/analyticsApi';

const currentSurveyId = ref<string | null>(null);
const isLoading = ref<boolean>(false);
const errorMessage = ref<string | null>(null);
const kpis = ref<KpiMetrics | null>(null);
const parroquias = ref<ParroquiaResultado[]>([]);
const repartoModal = ref<RepartoModalItem[]>([]);
const matrizOd = ref<MatrizODItem[]>([]);
const cacheBySurvey = new Map<string, AnalyticsDataset>();

export function useAnalyticsStore() {
  const hasData = computed<boolean>(() => {
    return (
      (kpis.value?.total_encuestas ?? 0) > 0 ||
      parroquias.value.length > 0 ||
      repartoModal.value.length > 0 ||
      matrizOd.value.length > 0
    );
  });

  function applyDataset(data: AnalyticsDataset) {
    kpis.value = data.kpis;
    parroquias.value = data.parroquias;
    repartoModal.value = data.repartoModal;
    matrizOd.value = data.matrizOd;
  }

  async function loadAnalytics(surveyId: string, forceRefresh = false) {
    if (!surveyId) return;
    const requestSurveyId = surveyId;
    currentSurveyId.value = surveyId;
    errorMessage.value = null;

    if (!forceRefresh && cacheBySurvey.has(surveyId)) {
      applyDataset(cacheBySurvey.get(surveyId)!);
      return;
    }

    isLoading.value = true;
    try {
      const data = await fetchAllAnalytics(surveyId);
      if (currentSurveyId.value !== requestSurveyId) return;
      cacheBySurvey.set(surveyId, data);
      applyDataset(data);
    } catch (err: any) {
      if (currentSurveyId.value !== requestSurveyId) return;
      errorMessage.value =
        err instanceof AnalyticsApiError
          ? err.message
          : err?.message || 'Error inesperado al cargar los datos analíticos.';
    } finally {
      if (currentSurveyId.value === requestSurveyId) {
        isLoading.value = false;
      }
    }
  }

  async function refresh() {
    if (currentSurveyId.value) {
      await loadAnalytics(currentSurveyId.value, true);
    }
  }

  function reset() {
    currentSurveyId.value = null;
    isLoading.value = false;
    errorMessage.value = null;
    kpis.value = null;
    parroquias.value = [];
    repartoModal.value = [];
    matrizOd.value = [];
    cacheBySurvey.clear();
  }

  return {
    currentSurveyId,
    isLoading,
    errorMessage,
    kpis,
    parroquias,
    repartoModal,
    matrizOd,
    hasData,
    loadAnalytics,
    refresh,
    reset
  };
}

