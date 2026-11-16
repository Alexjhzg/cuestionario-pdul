import { ref, watch, getCurrentInstance, onMounted, onBeforeUnmount } from 'vue';

export interface OfflineQueueItem {
  clientSubmissionId: string;
  encuestaId: string;
  data: Record<string, unknown>;
  createdAt: string;
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
    const raw = localStorage.getItem(storageKey);
    if (raw) {
      try {
        const parsed = JSON.parse(raw);
        if (parsed && (parsed.data || parsed.step !== undefined)) {
          hasRestorableDraft.value = true;
          lastSavedAt.value = parsed.savedAt ?? null;
        }
      } catch {
        hasRestorableDraft.value = false;
      }
    } else {
      hasRestorableDraft.value = false;
    }
  }

  function restoreDraft() {
    if (typeof localStorage === 'undefined') return;
    const raw = localStorage.getItem(storageKey);
    if (!raw) return;
    try {
      const parsed = JSON.parse(raw);
      if (parsed) {
        formData.value = parsed.data ?? {};
        currentStep.value = parsed.step ?? 0;
        lastSavedAt.value = parsed.savedAt ?? null;
      }
    } catch {
      // Ignorar json corrupto
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
      return Array.isArray(parsed) ? parsed : [];
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
