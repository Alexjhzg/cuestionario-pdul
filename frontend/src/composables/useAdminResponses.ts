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
  fetchAdminRespuestas,
  type EncuestaAdminItem,
  type AdminRespuestaItem
} from '@/services/api';
import { usePiiMasking } from '@/composables/usePiiMasking';
import type { ResponseDisplayData } from '@/utils/responseFormatters';

export type DetailViewMode = 'grid' | 'json';

export interface UseAdminResponsesReturn {
  surveys: Ref<EncuestaAdminItem[]>;
  selectedSurveyId: Ref<string>;
  loadingSurveys: Ref<boolean>;
  items: Ref<AdminRespuestaItem[]>;
  totalRespuestas: Ref<number>;
  currentPage: Ref<number>;
  pageSize: Ref<number>;
  isLoadingResponses: Ref<boolean>;
  errorMessage: Ref<string | null>;
  showDetailModal: Ref<boolean>;
  selectedRespuesta: Ref<AdminRespuestaItem | null>;
  maskPii: Ref<boolean>;
  detailViewMode: Ref<DetailViewMode>;
  jsonCopied: Ref<boolean>;
  totalPages: ComputedRef<number>;
  skip: ComputedRef<number>;
  displayData: ComputedRef<ResponseDisplayData>;
  MASKED_PLACEHOLDER: string;
  loadSurveysList: () => Promise<void>;
  loadResponses: () => Promise<void>;
  goToPreviousPage: () => void;
  goToNextPage: () => void;
  openDetail: (respuesta: AdminRespuestaItem) => void;
  closeDetail: () => void;
  copyJson: () => Promise<void>;
}

function extractErrorMessage(err: unknown): string {
  if (err && typeof err === 'object') {
    const candidate = err as { problem?: { detail?: string }; message?: string };
    if (candidate.problem?.detail) return candidate.problem.detail;
    if (candidate.message) return candidate.message;
  }
  return String(err);
}

export function useAdminResponses(
  initialSurveyId?: MaybeRefOrGetter<string | null | undefined>
): UseAdminResponsesReturn {
  // Lista de encuestas y encuesta seleccionada
  const surveys = ref<EncuestaAdminItem[]>([]);
  const selectedSurveyId = ref<string>(toValue(initialSurveyId) || '');
  const loadingSurveys = ref<boolean>(false);

  // Respuestas paginadas
  const items = ref<AdminRespuestaItem[]>([]);
  const totalRespuestas = ref<number>(0);
  const currentPage = ref<number>(1);
  const pageSize = ref<number>(10);
  const isLoadingResponses = ref<boolean>(false);
  const errorMessage = ref<string | null>(null);

  // Modal de detalle e inspección JSON
  const showDetailModal = ref<boolean>(false);
  const selectedRespuesta = ref<AdminRespuestaItem | null>(null);
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

  // Utilidad centralizada de enmascaramiento de PII
  const { maskPiiData, MASKED_PLACEHOLDER } = usePiiMasking();

  // Cálculos de paginación
  const totalPages = computed(() => {
    return Math.ceil(totalRespuestas.value / (Number(pageSize.value) || 10)) || 1;
  });

  const skip = computed(() => {
    return (currentPage.value - 1) * pageSize.value;
  });

  // Carga inicial de encuestas
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

  // Carga de respuestas para la encuesta seleccionada
  async function loadResponses(): Promise<void> {
    if (!selectedSurveyId.value) {
      items.value = [];
      totalRespuestas.value = 0;
      return;
    }

    const limitNum = Number(pageSize.value) || 10;
    const skipNum = Number(skip.value) || 0;

    isLoadingResponses.value = true;
    errorMessage.value = null;

    try {
      const data = await fetchAdminRespuestas(
        selectedSurveyId.value,
        skipNum,
        limitNum
      );
      items.value = data.items || [];
      totalRespuestas.value = data.total || 0;
    } catch (err: unknown) {
      errorMessage.value = `Error al cargar respuestas: ${extractErrorMessage(err)}`;
      items.value = [];
      totalRespuestas.value = 0;
    } finally {
      isLoadingResponses.value = false;
    }
  }

  // Observadores de cambios
  watch(
    () => toValue(initialSurveyId),
    (newId) => {
      if (newId && newId !== selectedSurveyId.value) {
        selectedSurveyId.value = newId;
      }
    }
  );

  watch(selectedSurveyId, () => {
    currentPage.value = 1;
    loadResponses();
  });

  watch(pageSize, () => {
    currentPage.value = 1;
    loadResponses();
  });

  watch(currentPage, () => {
    loadResponses();
  });

  if (getCurrentInstance()) {
    onMounted(async () => {
      await loadSurveysList();
      if (selectedSurveyId.value) {
        await loadResponses();
      }
    });

    onBeforeUnmount(() => {
      clearCopyTimer();
    });
  }

  // Navegación de páginas
  function goToPreviousPage() {
    if (currentPage.value > 1) {
      currentPage.value--;
    }
  }

  function goToNextPage() {
    if (currentPage.value < totalPages.value) {
      currentPage.value++;
    }
  }

  // Apertura y cierre del modal de inspección
  function openDetail(respuesta: AdminRespuestaItem) {
    selectedRespuesta.value = respuesta;
    maskPii.value = true;
    detailViewMode.value = 'grid'; // Ficha amigable estilo Grid por defecto
    jsonCopied.value = false;
    showDetailModal.value = true;
  }

  function closeDetail() {
    clearCopyTimer();
    jsonCopied.value = false;
    showDetailModal.value = false;
    selectedRespuesta.value = null;
  }

  // Datos formateados para el modal (con PII enmascarada de forma recursiva)
  const displayData = computed<ResponseDisplayData>(() => {
    if (!selectedRespuesta.value) return {};
    const cloned = JSON.parse(
      JSON.stringify(selectedRespuesta.value.datos || {})
    ) as ResponseDisplayData;
    return maskPiiData(cloned, maskPii.value);
  });

  // Copia segura al portapapeles
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

  return {
    surveys,
    selectedSurveyId,
    loadingSurveys,
    items,
    totalRespuestas,
    currentPage,
    pageSize,
    isLoadingResponses,
    errorMessage,
    showDetailModal,
    selectedRespuesta,
    maskPii,
    detailViewMode,
    jsonCopied,
    totalPages,
    skip,
    displayData,
    MASKED_PLACEHOLDER,
    loadSurveysList,
    loadResponses,
    goToPreviousPage,
    goToNextPage,
    openDetail,
    closeDetail,
    copyJson
  };
}
