import { ref, computed } from 'vue';
import {
  fetchAllAnalytics,
  type KpiMetrics,
  type ParroquiaResultado,
  type RepartoModalItem,
  type MatrizODItem,
  AnalyticsApiError
} from '@/services/analyticsApi';

export function useAnalytics() {
  const currentSurveyId = ref<string | null>(null);
  const isLoading = ref<boolean>(false);
  const errorMessage = ref<string | null>(null);

  const kpis = ref<KpiMetrics | null>(null);
  const parroquias = ref<ParroquiaResultado[]>([]);
  const repartoModal = ref<RepartoModalItem[]>([]);
  const matrizOd = ref<MatrizODItem[]>([]);

  const hasData = computed<boolean>(() => {
    return (
      (kpis.value?.total_encuestas ?? 0) > 0 ||
      parroquias.value.length > 0 ||
      repartoModal.value.length > 0 ||
      matrizOd.value.length > 0
    );
  });

  async function loadAnalytics(surveyId: string) {
    if (!surveyId) return;
    const requestSurveyId = surveyId;
    currentSurveyId.value = surveyId;
    isLoading.value = true;
    errorMessage.value = null;

    try {
      const data = await fetchAllAnalytics(surveyId);
      // Evitar race conditions si el usuario cambió de encuesta mientras la petición estaba en vuelo
      if (currentSurveyId.value !== requestSurveyId) return;
      kpis.value = data.kpis;
      parroquias.value = data.parroquias;
      repartoModal.value = data.repartoModal;
      matrizOd.value = data.matrizOd;
    } catch (err: any) {
      if (currentSurveyId.value !== requestSurveyId) return;
      if (err instanceof AnalyticsApiError) {
        errorMessage.value = err.message;
      } else {
        errorMessage.value = err?.message || 'Error inesperado al cargar los datos analíticos.';
      }
    } finally {
      if (currentSurveyId.value === requestSurveyId) {
        isLoading.value = false;
      }
    }
  }

  async function refresh() {
    if (currentSurveyId.value) {
      await loadAnalytics(currentSurveyId.value);
    }
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
    refresh
  };
}
