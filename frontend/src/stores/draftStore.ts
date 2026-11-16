import { computed, ref } from 'vue';

export interface OfflineQueueItem {
  client_submission_id: string;
  encuesta_id: string;
  data: Record<string, any>;
  queued_at: string;
}

const isOnline = ref<boolean>(typeof navigator !== 'undefined' ? navigator.onLine : true);
const lastSavedAt = ref<string | null>(null);
const hasRestorableDraft = ref<boolean>(false);
const offlineQueue = ref<OfflineQueueItem[]>([]);

export function useDraftStore() {
  const pendingCount = computed(() => offlineQueue.value.length);

  function setOnlineStatus(online: boolean) {
    isOnline.value = online;
  }

  function setLastSavedAt(timestamp: string | null) {
    lastSavedAt.value = timestamp;
  }

  function setRestorableDraft(flag: boolean) {
    hasRestorableDraft.value = flag;
  }

  function setQueue(items: OfflineQueueItem[]) {
    offlineQueue.value = [...items];
  }

  function enqueueItem(item: OfflineQueueItem) {
    offlineQueue.value = [...offlineQueue.value, item];
  }

  function removeQueueItem(clientSubmissionId: string) {
    offlineQueue.value = offlineQueue.value.filter(
      (it) => it.client_submission_id !== clientSubmissionId
    );
  }

  function reset() {
    lastSavedAt.value = null;
    hasRestorableDraft.value = false;
    offlineQueue.value = [];
  }

  return {
    isOnline,
    lastSavedAt,
    hasRestorableDraft,
    offlineQueue,
    pendingCount,
    setOnlineStatus,
    setLastSavedAt,
    setRestorableDraft,
    setQueue,
    enqueueItem,
    removeQueueItem,
    reset
  };
}

