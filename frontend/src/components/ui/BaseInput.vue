<script setup lang="ts">
import { computed, ref } from 'vue';

const props = withDefaults(
  defineProps<{
    id: string;
    label: string;
    modelValue?: string | number | null;
    type?: string;
    placeholder?: string;
    hint?: string;
    errorMessage?: string;
    required?: boolean;
    disabled?: boolean;
    inputmode?: 'text' | 'numeric' | 'decimal' | 'tel' | 'email';
    min?: number | string;
    max?: number | string;
    step?: number | string;
    autocomplete?: string;
  }>(),
  {
    modelValue: '',
    type: 'text',
    placeholder: '',
    hint: undefined,
    errorMessage: 'Revise este campo.',
    required: false,
    disabled: false,
    inputmode: undefined,
    min: undefined,
    max: undefined,
    step: undefined,
    autocomplete: undefined
  }
);

const emit = defineEmits<{
  (e: 'update:modelValue', value: string | number): void;
  (e: 'blur'): void;
}>();

const inputEl = ref<HTMLInputElement | null>(null);
const isInvalidAfterInteraction = ref(false);

const hintId = computed(() => (props.hint ? `${props.id}-hint` : undefined));
const errorId = computed(() => `${props.id}-error`);

const describedBy = computed(() => {
  const ids: string[] = [];
  if (hintId.value) ids.push(hintId.value);
  if (isInvalidAfterInteraction.value) ids.push(errorId.value);
  return ids.length ? ids.join(' ') : undefined;
});

function syncValidity(afterBlurOrInvalid: boolean) {
  const el = inputEl.value;
  if (!el) return;
  if (afterBlurOrInvalid) {
    isInvalidAfterInteraction.value = !el.validity.valid;
  } else if (isInvalidAfterInteraction.value && el.validity.valid) {
    isInvalidAfterInteraction.value = false;
  }
}

function onInput(event: Event) {
  const target = event.target as HTMLInputElement;
  const raw = target.value;
  if (props.type === 'number') {
    emit('update:modelValue', raw === '' ? '' : Number(raw));
  } else {
    emit('update:modelValue', raw);
  }
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
    <input
      :id="id"
      ref="inputEl"
      :type="type"
      :value="modelValue ?? ''"
      :placeholder="placeholder"
      :required="required"
      :disabled="disabled"
      :inputmode="inputmode"
      :min="min"
      :max="max"
      :step="step"
      :autocomplete="autocomplete"
      :aria-invalid="isInvalidAfterInteraction ? 'true' : 'false'"
      :aria-describedby="describedBy"
      :data-error="errorId"
      class="survey-input"
      :class="{ 'user-invalid-fallback': isInvalidAfterInteraction }"
      @input="onInput"
      @blur="onBlur"
      @invalid="syncValidity(true)"
    />
    <span :id="errorId" class="survey-error-msg">
      <i class="pi pi-times-circle" aria-hidden="true"></i>
      {{ errorMessage }}
    </span>
  </div>
</template>

