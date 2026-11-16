<script setup lang="ts">
defineProps<{
  isOnline: boolean;
  pendingCount?: number;
}>();

const emit = defineEmits<{
  (e: 'sync'): void;
}>();
</script>

<template>
  <div v-if="!isOnline || (pendingCount && pendingCount > 0)" class="sync-badge-container" role="status" aria-live="polite">
    <div
      v-if="!isOnline"
      class="sync-badge is-offline"
    >
      <span class="status-dot" aria-hidden="true"></span>
      <span class="status-label">
        Sin conexión
      </span>
    </div>

    <div
      v-if="pendingCount && pendingCount > 0"
      class="pending-badge"
    >
      <i class="pi pi-cloud-upload" aria-hidden="true"></i>
      <span>{{ pendingCount }} pendiente{{ pendingCount > 1 ? 's' : '' }}</span>
      <button
        v-if="isOnline"
        type="button"
        class="sync-btn"
        aria-label="Sincronizar respuestas pendientes ahora"
        @click="emit('sync')"
      >
        Sincronizar
      </button>
    </div>
  </div>
</template>

<style scoped>
.sync-badge-container {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-8);
  font-size: var(--text-caption);
  font-family: var(--font-inter);
}

.sync-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-6);
  padding: 4px 10px;
  border-radius: var(--radius-buttons);
  font-weight: var(--font-weight-medium);
  border: 1px solid var(--border-color);
  background-color: var(--surface-card);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.is-online .status-dot {
  background-color: var(--color-mint-win);
  box-shadow: 0 0 6px rgba(22, 202, 46, 0.4);
}

.is-online .status-label {
  color: #15803d;
}

.is-offline .status-dot {
  background-color: var(--color-coral-lost);
  box-shadow: 0 0 6px rgba(242, 96, 82, 0.4);
}

.is-offline .status-label {
  color: #b91c1c;
}

.pending-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-6);
  padding: 4px 10px;
  border-radius: var(--radius-buttons);
  background-color: #fffbeb;
  border: 1px solid #fef3c7;
  color: #b45309;
  font-weight: var(--font-weight-medium);
}

.sync-btn {
  background: none;
  border: none;
  color: var(--accent-primary);
  text-decoration: underline;
  cursor: pointer;
  padding: 0 var(--spacing-4);
  min-block-size: var(--min-touch-target);
  display: inline-flex;
  align-items: center;
  font-size: inherit;
  font-family: inherit;
  font-weight: var(--font-weight-bold);
}
</style>
