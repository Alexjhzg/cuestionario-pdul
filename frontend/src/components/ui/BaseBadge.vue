<script setup lang="ts">
withDefaults(
  defineProps<{
    variant?: 'success' | 'danger' | 'info' | 'warning' | 'neutral';
  }>(),
  {
    variant: 'neutral'
  }
);
</script>

<template>
  <span class="base-badge" :class="`base-badge--${variant}`">
    <slot />
  </span>
</template>

<style scoped>
.base-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 9999px;
  font-size: var(--text-caption);
  font-weight: var(--font-weight-semibold);
}

.base-badge--success {
  background-color: #dcfce7;
  color: #166534;
}

.base-badge--danger {
  background-color: #fee2e2;
  color: #991b1b;
}

.base-badge--info {
  background-color: #dbeafe;
  color: #1e40af;
}

.base-badge--warning {
  background-color: #fef3c7;
  color: #92400e;
}

.base-badge--neutral {
  background-color: var(--color-fog-surface);
  color: var(--text-body-color);
}
</style>

