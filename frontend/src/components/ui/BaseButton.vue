<script setup lang="ts">
withDefaults(
  defineProps<{
    type?: 'button' | 'submit' | 'reset';
    variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
    disabled?: boolean;
    loading?: boolean;
    ariaLabel?: string;
  }>(),
  {
    type: 'button',
    variant: 'primary',
    disabled: false,
    loading: false,
    ariaLabel: undefined
  }
);
</script>

<template>
  <button
    :type="type"
    class="base-btn"
    :class="`base-btn--${variant}`"
    :disabled="disabled || loading"
    :aria-busy="loading || undefined"
    :aria-label="ariaLabel"
  >
    <i v-if="loading" class="pi pi-spin pi-spinner" aria-hidden="true"></i>
    <slot />
  </button>
</template>

<style scoped>
.base-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-8);
  min-block-size: var(--min-touch-target);
  min-inline-size: var(--min-touch-target);
  padding: 0.75rem 1.25rem;
  border-radius: var(--radius-buttons);
  font-family: var(--font-inter);
  font-size: var(--text-body);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
  border: 1px solid transparent;
  transition: background-color 0.15s ease, border-color 0.15s ease, transform 0.05s ease;
}

.base-btn:focus-visible {
  outline: 3px solid var(--focus-ring);
  outline-offset: 2px;
}

.base-btn--primary {
  background-color: var(--accent-primary);
  color: #ffffff;
  border-color: var(--accent-primary);
}

.base-btn--primary:hover:not(:disabled) {
  background-color: #0f44c4;
}

.base-btn--secondary {
  background-color: var(--surface-card);
  color: var(--text-body-color);
  border-color: var(--border-color);
}

.base-btn--secondary:hover:not(:disabled) {
  background-color: var(--surface-subtle);
}

.base-btn--danger {
  background-color: var(--color-coral-lost);
  color: #ffffff;
  border-color: var(--color-coral-lost);
}

.base-btn--ghost {
  background-color: transparent;
  color: var(--text-body-color);
  border-color: transparent;
}

.base-btn--ghost:hover:not(:disabled) {
  background-color: var(--surface-subtle);
}

.base-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>

