<script setup lang="ts">
import { computed, ref } from 'vue';

export interface SelectOptionItem {
  value: string | number;
  label: string;
}

const props = withDefaults(
  defineProps<{
    id: string;
    label: string;
    modelValue?: string | number | null;
    options: readonly SelectOptionItem[];
    placeholderOption?: string;
    hint?: string;
    errorMessage?: string;
    required?: boolean;
    disabled?: boolean;
  }>(),
  {
    modelValue: '',
    placeholderOption: undefined,
    hint: undefined,
    errorMessage: 'Seleccione una opción.',
    required: false,
    disabled: false
  }
);

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void;
  (e: 'blur'): void;
}>();

const selectEl = ref<HTMLSelectElement | null>(null);
const isInvalidAfterInteraction = ref(false);

const hintId = computed(() => (props.hint ? `${props.id}-hint` : undefined));
const errorId = computed(() => `${props.id}-error`);
const describedBy = computed(() => {
  const ids: string[] = [];
  if (hintId.value) ids.push(hintId.value);
  if (isInvalidAfterInteraction.value) ids.push(errorId.value);
  return ids.length ? ids.join(' ') : undefined;
});

function syncValidity(afterCommit: boolean) {
  const el = selectEl.value;
  if (!el) return;
  if (afterCommit) {
    isInvalidAfterInteraction.value = !el.validity.valid;
  } else if (el.validity.valid) {
    isInvalidAfterInteraction.value = false;
  }
}

function onChange(event: Event) {
  const target = event.target as HTMLSelectElement;
  emit('update:modelValue', target.value);
  syncValidity(false);
}

function onBlur() {
  syncValidity(true);
  emit('blur');
}
</script>

<template>
  <div class="survey-field">
    <label :for="id" class="survey-label">
      {{ label }}
      <span v-if="required" class="required-indicator" aria-hidden="true">*</span>
    </label>
    <span v-if="hint" :id="hintId" class="survey-hint">{{ hint }}</span>
    <select
      :id="id"
      ref="selectEl"
      :value="modelValue ?? ''"
      :required="required"
      :disabled="disabled"
      :aria-invalid="isInvalidAfterInteraction ? 'true' : 'false'"
      :aria-describedby="describedBy"
      :data-error="errorId"
      class="survey-select"
      :class="{ 'user-invalid-fallback': isInvalidAfterInteraction }"
      @change="onChange"
      @blur="onBlur"
      @invalid="syncValidity(true)"
    >
      <option v-if="placeholderOption" value="" disabled>{{ placeholderOption }}</option>
      <option v-for="opt in options" :key="String(opt.value)" :value="opt.value">
        {{ opt.label }}
      </option>
    </select>
    <span :id="errorId" class="survey-error-msg">
      <i class="pi pi-times-circle" aria-hidden="true"></i>
      {{ errorMessage }}
    </span>
  </div>
</template>

