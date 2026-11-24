import {
  ref,
  computed,
  watch,
  onMounted,
  onBeforeUnmount,
  getCurrentInstance,
  toValue,
  type MaybeRefOrGetter,
  type Ref,
  type ComputedRef
} from 'vue';
import {
  fetchAdminEncuestas,
  fetchAdminMapaLevantamiento,
  fetchAdminRespuestaDetalle,
  type EncuestaAdminItem,
  type AdminRespuestaItem,
  type SurveyFieldMapPoint,
  type SurveyFieldMapSummary
} from '@/services/api';
import { usePiiMasking } from '@/composables/usePiiMasking';
import type { ResponseDisplayData } from '@/utils/responseFormatters';
import type { DetailViewMode } from '@/composables/useAdminResponses';

export type FieldMapViewMode = 'map' | 'table';

export interface UseAdminFieldMapReturn {
  surveys: Ref<EncuestaAdminItem[]>;
  selectedSurveyId: Ref<string>;
  loadingSurveys: Ref<boolean>;
  summary: Ref<SurveyFieldMapSummary | null>;
  isLoadingMap: Ref<boolean>;
  errorMessage: Ref<string | null>;
  parroquiaFilter: Ref<string>;
  deviceFilter: Ref<string>;
  onlyAlerts: Ref<boolean>;
  viewMode: Ref<FieldMapViewMode>;
  filteredPoints: ComputedRef<SurveyFieldMapPoint[]>;
  availableParroquias: ComputedRef<string[]>;
  showDetailModal: Ref<boolean>;
  selectedRespuesta: Ref<AdminRespuestaItem | null>;
  isLoadingDetail: Ref<boolean>;
  maskPii: Ref<boolean>;
  detailViewMode: Ref<DetailViewMode>;
  jsonCopied: Ref<boolean>;
  displayData: ComputedRef<ResponseDisplayData>;
  loadSurveysList: () => Promise<void>;
  loadFieldMap: () => Promise<void>;
  inspectPoint: (respuestaId: number) => Promise<void>;
  closeDetail: () => void;
  copyJson: () => Promise<void>;
  resetFilters: () => void;
}

function extractErrorMessage(err: unknown): string {
  if (err && typeof err === 'object') {
    const candidate = err as { problem?: { detail?: string }; message?: string };
    if (candidate.problem?.detail) return candidate.problem.detail;
    if (candidate.message) return candidate.message;
  }
  return String(err);
}

export function useAdminFieldMap(
  initialSurveyId?: MaybeRefOrGetter<string | null | undefined>
): UseAdminFieldMapReturn {
  const surveys = ref<EncuestaAdminItem[]>([]);
  const selectedSurveyId = ref<string>(toValue(initialSurveyId) || '');
  const loadingSurveys = ref<boolean>(false);

  const summary = ref<SurveyFieldMapSummary | null>(null);
  const isLoadingMap = ref<boolean>(false);
  const errorMessage = ref<string | null>(null);

  const parroquiaFilter = ref<string>('todas');
  const deviceFilter = ref<string>('todos');
  const onlyAlerts = ref<boolean>(false);
  const viewMode = ref<FieldMapViewMode>('map');

  const showDetailModal = ref<boolean>(false);
  const selectedRespuesta = ref<AdminRespuestaItem | null>(null);
  const isLoadingDetail = ref<boolean>(false);
  const maskPii = ref<boolean>(true);
  const detailViewMode = ref<DetailViewMode>('grid');
  const jsonCopied = ref<boolean>(false);

  let copyTimer: ReturnType<typeof setTimeout> | null = null;

  function clearCopyTimer() {
    if (copyTimer !== null) {
      clearTimeout(copyTimer);
      copyTimer = null;
    }
  }

  const { maskPiiData } = usePiiMasking();

  const availableParroquias = computed<string[]>(() => {
    const pts = summary.value?.puntos || [];
    const set = new Set<string>();
    for (const p of pts) {
      if (p.parroquia) set.add(p.parroquia);
    }
    return Array.from(set).sort();
  });

  const filteredPoints = computed<SurveyFieldMapPoint[]>(() => {
    const pts = summary.value?.puntos || [];
    return pts.filter((p) => {
      if (parroquiaFilter.value !== 'todas' && p.parroquia !== parroquiaFilter.value) {
        return false;
      }
      if (deviceFilter.value !== 'todos' && p.dispositivo_tipo !== deviceFilter.value) {
        return false;
      }
      if (onlyAlerts.value && p.calidad_ubicacion !== 'alerta') {
        return false;
      }
      return true;
    });
  });

  async function loadSurveysList(): Promise<void> {
    loadingSurveys.value = true;
    try {
      surveys.value = await fetchAdminEncuestas();
      if (!selectedSurveyId.value && surveys.value.length > 0) {
        selectedSurveyId.value = surveys.value[0].id;
      }
    } catch (err: unknown) {
      errorMessage.value = `Error al cargar encuestas: ${extractErrorMessage(err)}`;
    } finally {
      loadingSurveys.value = false;
    }
  }

  async function loadFieldMap(): Promise<void> {
    if (!selectedSurveyId.value) {
      summary.value = null;
      return;
    }
    isLoadingMap.value = true;
    errorMessage.value = null;
    try {
      summary.value = await fetchAdminMapaLevantamiento(selectedSurveyId.value);
    } catch (err: unknown) {
      errorMessage.value = `Error al cargar el mapa de levantamiento: ${extractErrorMessage(err)}`;
      summary.value = null;
    } finally {
      isLoadingMap.value = false;
    }
  }

  async function inspectPoint(respuestaId: number): Promise<void> {
    if (!selectedSurveyId.value) return;
    isLoadingDetail.value = true;
    errorMessage.value = null;
    try {
      const detail = await fetchAdminRespuestaDetalle(selectedSurveyId.value, respuestaId);
      selectedRespuesta.value = detail;
      maskPii.value = true;
      detailViewMode.value = 'grid';
      jsonCopied.value = false;
      showDetailModal.value = true;
    } catch (err: unknown) {
      errorMessage.value = `No se pudo cargar el detalle de la encuesta #${respuestaId}: ${extractErrorMessage(err)}`;
    } finally {
      isLoadingDetail.value = false;
    }
  }

  function closeDetail() {
    clearCopyTimer();
    jsonCopied.value = false;
    showDetailModal.value = false;
    selectedRespuesta.value = null;
  }

  const displayData = computed<ResponseDisplayData>(() => {
    if (!selectedRespuesta.value) return {};
    const cloned = JSON.parse(
      JSON.stringify(selectedRespuesta.value.datos || {})
    ) as ResponseDisplayData;
    return maskPiiData(cloned, maskPii.value);
  });

  async function copyJson(): Promise<void> {
    const serialized = JSON.stringify(displayData.value, null, 2);
    if (typeof navigator !== 'undefined' && navigator.clipboard?.writeText) {
      try {
        await navigator.clipboard.writeText(serialized);
        jsonCopied.value = true;
        clearCopyTimer();
        copyTimer = setTimeout(() => {
          jsonCopied.value = false;
          copyTimer = null;
        }, 2500);
      } catch {
        jsonCopied.value = false;
      }
    }
  }

  function resetFilters() {
    parroquiaFilter.value = 'todas';
    deviceFilter.value = 'todos';
    onlyAlerts.value = false;
  }

  watch(
    () => toValue(initialSurveyId),
    (newId) => {
      if (newId && newId !== selectedSurveyId.value) {
        selectedSurveyId.value = newId;
      }
    }
  );

  watch(selectedSurveyId, () => {
    resetFilters();
    loadFieldMap();
  });

  if (getCurrentInstance()) {
    onMounted(async () => {
      await loadSurveysList();
      if (selectedSurveyId.value) {
        await loadFieldMap();
      }
    });

    onBeforeUnmount(() => {
      clearCopyTimer();
    });
  }

  return {
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
    isLoadingDetail,
    maskPii,
    detailViewMode,
    jsonCopied,
    displayData,
    loadSurveysList,
    loadFieldMap,
    inspectPoint,
    closeDetail,
    copyJson,
    resetFilters
  };
}

