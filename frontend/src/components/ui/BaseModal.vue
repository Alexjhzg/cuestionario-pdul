<script setup lang="ts">
import { nextTick, onBeforeUnmount, ref, watch } from 'vue';

const props = withDefaults(
  defineProps<{
    open: boolean;
    titleId: string;
    title: string;
    closeOnBackdrop?: boolean;
  }>(),
  {
    closeOnBackdrop: true
  }
);

const emit = defineEmits<{
  (e: 'close'): void;
}>();

const dialogRef = ref<HTMLElement | null>(null);
let previousFocused: HTMLElement | null = null;

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape' && props.open) {
    emit('close');
  }
}

watch(
  () => props.open,
  async (isOpen) => {
    if (isOpen) {
      previousFocused = document.activeElement as HTMLElement | null;
      document.addEventListener('keydown', handleKeydown);
      await nextTick();
      dialogRef.value?.focus();
    } else {
      document.removeEventListener('keydown', handleKeydown);
      previousFocused?.focus?.();
      previousFocused = null;
    }
  },
  { immediate: true }
);

onBeforeUnmount(() => {
  document.removeEventListener('keydown', handleKeydown);
});
</script>

<template>
  <div
    v-if="open"
    class="base-modal-backdrop"
    @click.self="closeOnBackdrop && emit('close')"
  >
    <div
      ref="dialogRef"
      role="dialog"
      aria-modal="true"
      :aria-labelledby="titleId"
      tabindex="-1"
      class="base-modal-panel"
    >
      <header class="base-modal-header">
        <h2 :id="titleId" class="base-modal-title">{{ title }}</h2>
        <button
          type="button"
          class="base-modal-close"
          aria-label="Cerrar diálogo"
          @click="emit('close')"
        >
          <i class="pi pi-times" aria-hidden="true"></i>
        </button>
      </header>
      <div class="base-modal-body">
        <slot />
      </div>
      <footer v-if="$slots.footer" class="base-modal-footer">
        <slot name="footer" />
      </footer>
    </div>
  </div>
</template>

<style scoped>
.base-modal-backdrop {
  position: fixed;
  inset: 0;
  background-color: rgba(2, 5, 32, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-16);
  z-index: 9000;
}

.base-modal-panel {
  width: 100%;
  max-width: 640px;
  max-height: 90vh;
  overflow-y: auto;
  overscroll-behavior: contain;
  background-color: var(--surface-card);
  border-radius: var(--radius-containers);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-dropdown);
  padding: var(--spacing-24);
}

.base-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-12);
  margin-block-end: var(--spacing-16);
}

.base-modal-title {
  margin: 0;
  font-size: var(--text-subheading);
  color: var(--color-midnight-ink);
}

.base-modal-close {
  min-block-size: var(--min-touch-target);
  min-inline-size: var(--min-touch-target);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-interactive);
  background: var(--surface-card);
  cursor: pointer;
}

.base-modal-close:focus-visible {
  outline: 3px solid var(--focus-ring);
  outline-offset: 2px;
}

.base-modal-footer {
  margin-block-start: var(--spacing-16);
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-12);
  flex-wrap: wrap;
}
</style>

