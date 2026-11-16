import { ref } from 'vue';
import {
  fetchAdminEncuestas,
  fetchAdminRespuestas,
  updateEncuestaEstado,
  type AdminRespuestaItem,
  type EncuestaAdminItem
} from '@/services/api';

const surveys = ref<EncuestaAdminItem[]>([]);
const selectedSurveyId = ref<string>('');
const responses = ref<AdminRespuestaItem[]>([]);
const totalResponses = ref<number>(0);
const isLoadingSurveys = ref<boolean>(false);
const isLoadingResponses = ref<boolean>(false);
const errorMessage = ref<string | null>(null);

export function useAdminStore() {
  async function loadSurveys() {
    isLoadingSurveys.value = true;
    errorMessage.value = null;
    try {
      surveys.value = await fetchAdminEncuestas();
      if (!selectedSurveyId.value && surveys.value.length > 0) {
        selectedSurveyId.value = surveys.value[0].id;
      }
    } catch (err: any) {
      errorMessage.value = err?.problem?.detail || err?.message || 'Error al cargar encuestas.';
    } finally {
      isLoadingSurveys.value = false;
    }
  }

  async function toggleStatus(surveyId: string, newStatus: boolean) {
    const target = surveys.value.find((s) => s.id === surveyId);
    const previousStatus = target?.activa;
    if (target) target.activa = newStatus;
    try {
      await updateEncuestaEstado(surveyId, newStatus);
    } catch (err) {
      if (target && previousStatus !== undefined) {
        target.activa = previousStatus;
      }
      throw err;
    }
  }

  async function loadResponses(surveyId: string, skip = 0, limit = 10) {
    if (!surveyId) return;
    isLoadingResponses.value = true;
    errorMessage.value = null;
    try {
      const res = await fetchAdminRespuestas(surveyId, skip, limit);
      responses.value = res.items;
      totalResponses.value = res.total;
    } catch (err: any) {
      errorMessage.value = err?.problem?.detail || err?.message || 'Error al cargar respuestas.';
    } finally {
      isLoadingResponses.value = false;
    }
  }

  function reset() {
    surveys.value = [];
    selectedSurveyId.value = '';
    responses.value = [];
    totalResponses.value = 0;
    isLoadingSurveys.value = false;
    isLoadingResponses.value = false;
    errorMessage.value = null;
  }

  return {
    surveys,
    selectedSurveyId,
    responses,
    totalResponses,
    isLoadingSurveys,
    isLoadingResponses,
    errorMessage,
    loadSurveys,
    toggleStatus,
    loadResponses,
    reset
  };
}

