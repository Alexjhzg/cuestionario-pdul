import { ref, onMounted } from 'vue';
import {
  fetchAdminEncuestas,
  updateEncuestaEstado,
  exportarRespuestasAdmin,
  descargarBlob,
  type EncuestaAdminItem
} from '@/services/api';

export function formatFechaSurvey(isoDate: string | null | undefined): string {
  if (!isoDate) return 'Sin fecha';
  try {
    const d = new Date(isoDate);
    if (isNaN(d.getTime())) return isoDate;
    return new Intl.DateTimeFormat('es-VE', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    }).format(d);
  } catch {
    return isoDate;
  }
}

export function formatTipoInstrumento(tipo: string): string {
  switch (tipo) {
    case 'encuesta_od_pdul':
      return 'Origen-Destino (PDUL)';
    case 'consulta_ciudadana':
      return 'Consulta Ciudadana';
    case 'estudio_movilidad':
      return 'Estudio Movilidad';
    default:
      return tipo;
  }
}

export function useAdminSurveyList() {
  const surveys = ref<EncuestaAdminItem[]>([]);
  const isLoading = ref<boolean>(true);
  const errorMessage = ref<string | null>(null);
  const successMessage = ref<string | null>(null);
  const redactPii = ref<boolean>(true);

  const showConfirmModal = ref<boolean>(false);
  const surveyToDeactivate = ref<EncuestaAdminItem | null>(null);
  const isTogglingStatus = ref<string | null>(null);
  const exportingSurveyId = ref<string | null>(null);

  async function loadSurveys() {
    isLoading.value = true;
    errorMessage.value = null;
    try {
      surveys.value = await fetchAdminEncuestas();
    } catch (err: any) {
      errorMessage.value = err?.problem?.detail || err?.message || 'Error al cargar las encuestas.';
    } finally {
      isLoading.value = false;
    }
  }

  onMounted(() => {
    loadSurveys();
  });

  function onToggleClick(survey: EncuestaAdminItem) {
    if (survey.activa) {
      surveyToDeactivate.value = survey;
      showConfirmModal.value = true;
    } else {
      performToggle(survey, true);
    }
  }

  async function performToggle(survey: EncuestaAdminItem, newStatus: boolean) {
    isTogglingStatus.value = survey.id;
    errorMessage.value = null;
    const previousStatus = survey.activa;
    survey.activa = newStatus;

    try {
      await updateEncuestaEstado(survey.id, newStatus);
      successMessage.value = `Estado de "${survey.titulo}" actualizado a ${newStatus ? 'Activa' : 'Inactiva'}.`;
      setTimeout(() => (successMessage.value = null), 3000);
    } catch (err: any) {
      survey.activa = previousStatus;
      errorMessage.value = `Error al cambiar estado: ${err?.problem?.detail || err?.message || 'Error de red'}`;
    } finally {
      isTogglingStatus.value = null;
      showConfirmModal.value = false;
      surveyToDeactivate.value = null;
    }
  }

  function confirmDeactivation() {
    if (surveyToDeactivate.value) {
      performToggle(surveyToDeactivate.value, false);
    }
  }

  function cancelDeactivation() {
    showConfirmModal.value = false;
    surveyToDeactivate.value = null;
  }

  async function handleExport(survey: EncuestaAdminItem, format: 'csv' | 'json') {
    exportingSurveyId.value = `${survey.id}-${format}`;
    errorMessage.value = null;
    try {
      const blob = await exportarRespuestasAdmin(survey.id, format, redactPii.value);
      const filename = `${survey.slug}_respuestas_${redactPii.value ? 'anonimizado_' : ''}${new Date().toISOString().slice(0, 10)}.${format}`;
      descargarBlob(blob, filename);
      successMessage.value = `Exportación ${format.toUpperCase()} descargada exitosamente.`;
      setTimeout(() => (successMessage.value = null), 3000);
    } catch (err: any) {
      errorMessage.value = `Error al exportar respuestas: ${err?.problem?.detail || err?.message || err}`;
    } finally {
      exportingSurveyId.value = null;
    }
  }

  return {
    surveys,
    isLoading,
    errorMessage,
    successMessage,
    redactPii,
    showConfirmModal,
    surveyToDeactivate,
    isTogglingStatus,
    exportingSurveyId,
    loadSurveys,
    onToggleClick,
    performToggle,
    confirmDeactivation,
    cancelDeactivation,
    handleExport,
    formatFecha: formatFechaSurvey,
    formatTipoInstrumento
  };
}

