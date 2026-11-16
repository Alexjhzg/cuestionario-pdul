import { ref, watch, getCurrentInstance, onMounted, onBeforeUnmount } from 'vue';
import { SURVEY_STEPS } from '@/types/survey';
import { parroquiaToKey } from '@/utils/validation';

export interface OfflineQueueItem {
  clientSubmissionId: string;
  encuestaId: string;
  data: Record<string, unknown>;
  createdAt: string;
}

const LEGACY_DRAFT_DATA_KEYS = new Set([
  'cedula',
  'parroquia',
  'comunidad_sector',
  'sector_barrio',
  'zona_residencia_od',
  'tipo_vivienda',
  'residentes',
  'viajes',
  'acepta_declaracion'
]);

function isPlainRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

export function normalizeDraftStep(rawStep: unknown, maxStep = SURVEY_STEPS.length - 1): number {
  if (typeof rawStep === 'number' && Number.isFinite(rawStep)) {
    return Math.min(maxStep, Math.max(0, Math.trunc(rawStep)));
  }
  if (typeof rawStep === 'string' && rawStep.trim() !== '') {
    const parsed = Number(rawStep);
    if (Number.isFinite(parsed)) {
      return Math.min(maxStep, Math.max(0, Math.trunc(parsed)));
    }
  }
  return 0;
}

function normalizeDraftData(
  rawData: Record<string, unknown>,
  initialData: Record<string, unknown>
): Record<string, unknown> {
  const merged: Record<string, unknown> = { ...rawData };

  // Garantiza valores iniciales faltantes o nulos (especialmente arrays residentes/viajes)
  for (const [key, fallbackVal] of Object.entries(initialData)) {
    const current = merged[key];
    if (current === undefined || (Array.isArray(fallbackVal) && !Array.isArray(current))) {
      merged[key] = Array.isArray(fallbackVal) ? [...fallbackVal] : fallbackVal;
    }
  }

  // Normaliza parroquias guardadas en formato de etiqueta humana en borradores legacy
  if (typeof merged.parroquia === 'string' && merged.parroquia.trim() !== '') {
    merged.parroquia = parroquiaToKey(merged.parroquia);
  }

  return merged;
}

export function parseStoredDraft(
  raw: string | null,
  initialData: Record<string, unknown> = {}
): { data: Record<string, unknown>; step: number; savedAt: string | null } | null {
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw);
    if (!isPlainRecord(parsed)) return null;

    let rawData: Record<string, unknown> | null = null;
    if (isPlainRecord(parsed.data)) {
      rawData = parsed.data;
    } else if (isPlainRecord(parsed.formData)) {
      rawData = parsed.formData;
    } else if (Object.keys(parsed).some((k) => LEGACY_DRAFT_DATA_KEYS.has(k))) {
      const { step: _s, savedAt: _sa, version: _v, ...rest } = parsed;
      rawData = rest;
    } else if (parsed.step !== undefined && normalizeDraftStep(parsed.step) >= 0) {
      rawData = {};
    }

    if (!rawData) return null;

    return {
      data: normalizeDraftData(rawData, initialData),
      step: normalizeDraftStep(parsed.step),
      savedAt: typeof parsed.savedAt === 'string' ? parsed.savedAt : null
    };
  } catch {
    return null;
  }
}

export function generateUUID(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

export function useSurveyDraft(encuestaSlug: string, initialData: Record<string, unknown> = {}) {
  const storageKey = `pdul_draft_${encuestaSlug}`;
  const queueKey = `pdul_offline_queue`;

  const formData = ref<Record<string, unknown>>({ ...initialData });
  const currentStep = ref<number>(0);
  const hasRestorableDraft = ref<boolean>(false);
  const lastSavedAt = ref<string | null>(null);
  const isOnline = ref<boolean>(typeof navigator !== 'undefined' ? navigator.onLine : true);

  function checkExistingDraft() {
    if (typeof localStorage === 'undefined') return;
    const restored = parseStoredDraft(localStorage.getItem(storageKey), initialData);
    if (restored) {
      hasRestorableDraft.value = true;
      lastSavedAt.value = restored.savedAt;
    } else {
      hasRestorableDraft.value = false;
    }
  }

  function restoreDraft() {
    if (typeof localStorage === 'undefined') return;
    const restored = parseStoredDraft(localStorage.getItem(storageKey), initialData);
    if (restored) {
      formData.value = restored.data;
      currentStep.value = restored.step;
      lastSavedAt.value = restored.savedAt;
    }
    hasRestorableDraft.value = false;
  }

  function clearDraft() {
    if (typeof localStorage !== 'undefined') {
      localStorage.removeItem(storageKey);
    }
    hasRestorableDraft.value = false;
    lastSavedAt.value = null;
  }

  function saveToLocalStorage() {
    if (typeof localStorage === 'undefined') return;
    const now = new Date().toLocaleTimeString('es-VE', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    localStorage.setItem(
      storageKey,
      JSON.stringify({
        data: formData.value,
        step: currentStep.value,
        savedAt: now
      })
    );
    lastSavedAt.value = now;
  }

  // Vigilar cambios en los datos y en el paso para guardar de inmediato
  watch(
    [formData, currentStep],
    () => {
      saveToLocalStorage();
    },
    { deep: true }
  );

  function getOfflineQueue(): OfflineQueueItem[] {
    if (typeof localStorage === 'undefined') return [];
    const rawQueue = localStorage.getItem(queueKey);
    if (!rawQueue) return [];
    try {
      const parsed = JSON.parse(rawQueue);
      if (!Array.isArray(parsed)) return [];
      return parsed
        .filter((item): item is Record<string, unknown> => isPlainRecord(item))
        .map((item) => {
          const clientSubmissionId = String(item.clientSubmissionId ?? item.client_submission_id ?? '');
          const encuestaId = String(item.encuestaId ?? item.encuesta_id ?? '');
          const data = isPlainRecord(item.data) ? item.data : {};
          const createdAt = String(item.createdAt ?? item.created_at ?? new Date().toISOString());
          return { clientSubmissionId, encuestaId, data, createdAt };
        })
        .filter((item) => Boolean(item.clientSubmissionId && item.encuestaId));
    } catch {
      return [];
    }
  }

  function enqueueOfflineSubmission(encuestaId: string, payload: Record<string, unknown>): string {
    const clientSubmissionId = generateUUID();
    const queue = getOfflineQueue();
    queue.push({
      clientSubmissionId,
      encuestaId,
      data: { ...payload, client_submission_id: clientSubmissionId },
      createdAt: new Date().toISOString()
    });
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(queueKey, JSON.stringify(queue));
    }
    clearDraft();
    return clientSubmissionId;
  }

  function clearOfflineQueueItem(clientSubmissionId: string) {
    if (typeof localStorage === 'undefined') return;
    const queue = getOfflineQueue().filter(item => item.clientSubmissionId !== clientSubmissionId);
    localStorage.setItem(queueKey, JSON.stringify(queue));
  }

  const updateOnlineStatus = () => {
    isOnline.value = typeof navigator !== 'undefined' ? navigator.onLine : true;
  };

  // Inicializar detección de borrador al crear el composable (aplica tanto en test como en browser)
  checkExistingDraft();

  if (typeof window !== 'undefined' && getCurrentInstance()) {
    onMounted(() => {
      checkExistingDraft();
      window.addEventListener('online', updateOnlineStatus);
      window.addEventListener('offline', updateOnlineStatus);
    });

    onBeforeUnmount(() => {
      window.removeEventListener('online', updateOnlineStatus);
      window.removeEventListener('offline', updateOnlineStatus);
    });
  }

  return {
    formData,
    currentStep,
    hasRestorableDraft,
    lastSavedAt,
    isOnline,
    checkExistingDraft,
    restoreDraft,
    clearDraft,
    saveToLocalStorage,
    getOfflineQueue,
    enqueueOfflineSubmission,
    clearOfflineQueueItem
  };
}
