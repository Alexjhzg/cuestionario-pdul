<script setup lang="ts">
import { computed, ref, watch } from 'vue';

export interface SearchableSelectOption {
  value: string | number;
  label: string;
  disabled?: boolean;
}

const props = withDefaults(
  defineProps<{
    id: string;
    modelValue?: string | number | null;
    options: readonly SearchableSelectOption[];
    placeholderOption?: string;
    allowClearEmptyOption?: boolean;
    searchPlaceholder?: string;
    searchAriaLabel?: string;
    disabled?: boolean;
    required?: boolean;
    selectTestId?: string;
  }>(),
  {
    modelValue: '',
    placeholderOption: undefined,
    allowClearEmptyOption: false,
    searchPlaceholder: 'Buscar opción...',
    searchAriaLabel: undefined,
    disabled: false,
    required: false,
    selectTestId: undefined
  }
);

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void;
  (e: 'blur', event: FocusEvent): void;
}>();

const searchQuery = ref('');

function normalizeText(text: string): string {
  return text
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim();
}

const filteredOptions = computed<SearchableSelectOption[]>(() => {
  const q = normalizeText(searchQuery.value);
  if (!q) return [...props.options];

  const currentStr =
    props.modelValue !== undefined && props.modelValue !== null ? String(props.modelValue) : '';

  return props.options.filter((opt) => {
    if (currentStr && String(opt.value) === currentStr) return true;
    return normalizeText(opt.label).includes(q);
  });
});

watch(
  () => props.disabled,
  (isDisabled) => {
    if (isDisabled) {
      searchQuery.value = '';
    }
  }
);

watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal === '' || newVal === null || newVal === undefined) {
      searchQuery.value = '';
    }
  }
);

function onSelectChange(event: Event) {
  const target = event.target as HTMLSelectElement;
  emit('update:modelValue', target.value);
}

function onSearchKeydown(event: KeyboardEvent) {
  if (event.key !== 'Enter') return;
  const enabledMatches = filteredOptions.value.filter((opt) => !opt.disabled);
  if (enabledMatches.length === 1) {
    event.preventDefault();
    emit('update:modelValue', String(enabledMatches[0].value));
  }
}

function clearSearch() {
  searchQuery.value = '';
}
</script>

<template>
  <div class="searchable-select-wrap" :class="{ 'is-disabled': disabled }">
    <div class="searchable-search-box">
      <i class="pi pi-search searchable-search-icon" aria-hidden="true"></i>
      <input
        :id="`${id}-search`"
        v-model="searchQuery"
        type="search"
        class="survey-input searchable-search-input"
        :disabled="disabled"
        :placeholder="searchPlaceholder"
        :aria-label="searchAriaLabel || `Buscar en ${placeholderOption || id}`"
        autocomplete="off"
        @keydown="onSearchKeydown"
      />
      <button
        v-if="searchQuery"
        type="button"
        class="searchable-clear-btn"
        aria-label="Limpiar búsqueda"
        @click="clearSearch"
      >
        <i class="pi pi-times" aria-hidden="true"></i>
      </button>
    </div>

    <select
      :id="id"
      :value="modelValue ?? ''"
      :required="required"
      :disabled="disabled"
      :data-testid="selectTestId"
      class="survey-select"
      @change="onSelectChange"
      @blur="emit('blur', $event)"
    >
      <option
        v-if="placeholderOption"
        value=""
        :disabled="!allowClearEmptyOption"
      >
        {{ placeholderOption }}
      </option>
      <option
        v-if="searchQuery && filteredOptions.length === 0"
        value=""
        disabled
      >
        Sin coincidencias para «{{ searchQuery }}»
      </option>
      <option
        v-for="opt in filteredOptions"
        :key="String(opt.value)"
        :value="opt.value"
        :disabled="opt.disabled"
      >
        {{ opt.label }}
      </option>
    </select>
  </div>
</template>

<style scoped>
.searchable-select-wrap {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  width: 100%;
}

.searchable-search-box {
  position: relative;
  display: flex;
  align-items: center;
}

.searchable-search-icon {
  position: absolute;
  left: 0.75rem;
  color: var(--color-ash-helper, #6b7280);
  font-size: 0.875rem;
  pointer-events: none;
}

.searchable-search-input {
  width: 100%;
  padding-left: 2.25rem;
  padding-right: 2.25rem;
  min-block-size: 42px;
  font-size: 0.9375rem;
  background-color: var(--color-snow-canvas, #fcfcfc);
}

.searchable-clear-btn {
  position: absolute;
  right: 0.4rem;
  width: 30px;
  height: 30px;
  border: none;
  border-radius: 50%;
  background: transparent;
  color: var(--color-slate-caption, #374151);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.searchable-clear-btn:hover {
  background-color: var(--color-fog-surface, #f1f5f9);
}

.searchable-select-wrap.is-disabled .searchable-search-box {
  opacity: 0.65;
}
</style>
