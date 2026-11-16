<script setup lang="ts">
withDefaults(
  defineProps<{
    modelValue: boolean;
    label: string;
    disabled?: boolean;
    ariaLabel?: string;
  }>(),
  {
    disabled: false,
    ariaLabel: undefined
  }
);

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void;
  (e: 'toggle'): void;
}>();

function onClick(current: boolean) {
  emit('update:modelValue', !current);
  emit('toggle');
}
</script>

<template>
  <button
    type="button"
    role="switch"
    class="base-switch"
    :class="{ 'is-checked': modelValue }"
    :aria-checked="modelValue"
    :aria-label="ariaLabel || label"
    :disabled="disabled"
    @click="onClick(modelValue)"
  >
    <span class="base-switch-track" aria-hidden="true">
      <span class="base-switch-thumb"></span>
    </span>
    <span class="base-switch-label">{{ label }}</span>
  </button>
</template>

<style scoped>
.base-switch {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-8);
  min-block-size: var(--min-touch-target);
  min-inline-size: var(--min-touch-target);
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--radius-buttons);
  padding: 4px 8px;
  cursor: pointer;
  font-family: var(--font-inter);
  font-size: var(--text-body-sm);
  color: var(--text-body-color);
}

.base-switch:focus-visible {
  outline: 3px solid var(--focus-ring);
  outline-offset: 2px;
}

.base-switch-track {
  inline-size: 44px;
  block-size: 24px;
  border-radius: 9999px;
  background-color: var(--color-stone-divider);
  padding: 2px;
  display: inline-flex;
  align-items: center;
  transition: background-color 0.15s ease;
}

.base-switch.is-checked .base-switch-track {
  background-color: var(--accent-primary);
}

.base-switch-thumb {
  inline-size: 20px;
  block-size: 20px;
  border-radius: 50%;
  background-color: #ffffff;
  transform: translateX(0);
  transition: transform 0.15s ease;
}

.base-switch.is-checked .base-switch-thumb {
  transform: translateX(20px);
}
</style>

