<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, useId } from 'vue';

const props = withDefaults(
  defineProps<{
    text: string;
    questionLabel?: string;
  }>(),
  {
    questionLabel: 'esta pregunta'
  }
);

const isOpen = ref(false);
const rootRef = ref<HTMLElement | null>(null);
const triggerRef = ref<HTMLButtonElement | null>(null);
const tipId = `q-help-${useId()}`;

function toggle() {
  isOpen.value = !isOpen.value;
}

function close(restoreFocus = false) {
  if (!isOpen.value) return;
  isOpen.value = false;
  if (restoreFocus) {
    triggerRef.value?.focus();
  }
}

function onDocumentClick(event: MouseEvent) {
  if (!isOpen.value) return;
  const target = event.target as Node | null;
  if (target && rootRef.value && !rootRef.value.contains(target)) {
    close(false);
  }
}

function onDocumentKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape' && isOpen.value) {
    event.preventDefault();
    close(true);
  }
}

onMounted(() => {
  document.addEventListener('click', onDocumentClick);
  document.addEventListener('keydown', onDocumentKeydown);
});

onBeforeUnmount(() => {
  document.removeEventListener('click', onDocumentClick);
  document.removeEventListener('keydown', onDocumentKeydown);
});
</script>

<template>
  <span ref="rootRef" class="question-help-wrap" @click.stop>
    <button
      ref="triggerRef"
      type="button"
      class="question-help-btn"
      :class="{ 'is-open': isOpen }"
      :aria-expanded="isOpen"
      :aria-controls="tipId"
      :aria-label="`Ayuda explicativa sobre ${props.questionLabel}`"
      title="Ver explicación de la pregunta"
      data-testid="btn-question-help"
      @click.prevent="toggle"
    >
      <span aria-hidden="true">?</span>
    </button>

    <div
      v-if="isOpen"
      :id="tipId"
      role="tooltip"
      class="question-help-popover"
      data-testid="question-help-popover"
    >
      <p class="question-help-text">{{ text }}</p>
      <button
        type="button"
        class="question-help-close"
        aria-label="Cerrar descripción de ayuda"
        @click.prevent="close(true)"
      >
        <i class="pi pi-times" aria-hidden="true"></i>
      </button>
    </div>
  </span>
</template>

<style scoped>
.question-help-wrap {
  position: relative;
  display: inline-flex;
  align-items: center;
  vertical-align: middle;
  margin-inline-start: 6px;
}

.question-help-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  min-width: 24px;
  min-height: 24px;
  padding: 0;
  border-radius: 50%;
  border: 1.5px solid var(--color-royal-signal);
  background-color: var(--color-lavender-wash);
  color: var(--color-royal-signal);
  font-family: var(--font-inter);
  font-size: 0.8125rem;
  font-weight: var(--font-weight-bold);
  line-height: 1;
  cursor: pointer;
  transition: background-color 0.15s ease, color 0.15s ease, transform 0.12s ease;
}

.question-help-btn:hover,
.question-help-btn.is-open {
  background-color: var(--color-royal-signal);
  color: #ffffff;
}

.question-help-btn:focus-visible {
  outline: 2px solid var(--focus-ring);
  outline-offset: 2px;
}

.question-help-popover {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  z-index: 60;
  width: min(320px, 82vw);
  padding: 10px 32px 10px 12px;
  border-radius: var(--radius-cards);
  background-color: var(--color-midnight-ink);
  color: #ffffff;
  font-family: var(--font-inter);
  font-size: var(--text-body-sm);
  font-weight: var(--font-weight-normal);
  line-height: 1.45;
  box-shadow: 0 8px 24px rgba(2, 5, 32, 0.28);
  border: 1px solid rgba(255, 255, 255, 0.14);
}

.question-help-popover::before {
  content: '';
  position: absolute;
  top: -6px;
  left: 8px;
  width: 10px;
  height: 10px;
  background-color: var(--color-midnight-ink);
  border-left: 1px solid rgba(255, 255, 255, 0.14);
  border-top: 1px solid rgba(255, 255, 255, 0.14);
  transform: rotate(45deg);
}

.question-help-text {
  margin: 0;
  color: #f8fafc;
}

.question-help-close {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 24px;
  height: 24px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: #cbd5e1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 0.75rem;
}

.question-help-close:hover {
  color: #ffffff;
  background-color: rgba(255, 255, 255, 0.12);
}

@media (max-width: 640px) {
  .question-help-popover {
    position: fixed;
    top: auto;
    bottom: 16px;
    left: 16px;
    right: 16px;
    width: auto;
    max-width: none;
    padding: 14px 40px 14px 16px;
    box-shadow: 0 12px 32px rgba(2, 5, 32, 0.42);
  }

  .question-help-popover::before {
    display: none;
  }
}
</style>

