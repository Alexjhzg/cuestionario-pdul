<script lang="ts">
// Asegura que solo exista un selector desplegable abierto a la vez
let activeCloseDropdown: (() => void) | null = null;
</script>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';

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
    searchPlaceholder: 'Buscar...',
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

const rootRef = ref<HTMLElement | null>(null);
const triggerRef = ref<HTMLButtonElement | null>(null);
const searchInputRef = ref<HTMLInputElement | null>(null);
const isOpen = ref(false);
const searchQuery = ref('');

function normalizeText(text: string): string {
  return text
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim();
}

const selectedOptionLabel = computed<string>(() => {
  const current =
    props.modelValue !== undefined && props.modelValue !== null ? String(props.modelValue) : '';
  if (!current) {
    return props.placeholderOption || 'Seleccione una opción';
  }
  const found = props.options.find((opt) => String(opt.value) === current);
  return found ? found.label : current;
});

const isPlaceholderActive = computed<boolean>(() => {
  const current =
    props.modelValue !== undefined && props.modelValue !== null ? String(props.modelValue) : '';
  return current === '';
});

const filteredOptions = computed<SearchableSelectOption[]>(() => {
  const q = normalizeText(searchQuery.value);
  if (!q) return [...props.options];

  return props.options.filter((opt) => normalizeText(opt.label).includes(q));
});

function closeDropdown(restoreFocus = false) {
  if (!isOpen.value) return;
  isOpen.value = false;
  searchQuery.value = '';
  if (activeCloseDropdown === closeFromOutside) {
    activeCloseDropdown = null;
  }
  if (restoreFocus) {
    triggerRef.value?.focus();
  }
}

function closeFromOutside() {
  closeDropdown(false);
}

async function openDropdown() {
  if (props.disabled) return;
  if (activeCloseDropdown && activeCloseDropdown !== closeFromOutside) {
    activeCloseDropdown();
  }
  activeCloseDropdown = closeFromOutside;
  isOpen.value = true;
  await nextTick();
  searchInputRef.value?.focus();
}

function toggleDropdown() {
  if (props.disabled) return;
  if (isOpen.value) {
    closeDropdown(false);
  } else {
    void openDropdown();
  }
}

function selectOption(value: string | number) {
  emit('update:modelValue', String(value));
  closeDropdown(true);
}

function onNativeSelectChange(event: Event) {
  const target = event.target as HTMLSelectElement;
  emit('update:modelValue', target.value);
}

function onSearchKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    event.preventDefault();
    closeDropdown(true);
    return;
  }
  if (event.key === 'Enter') {
    const enabledMatches = filteredOptions.value.filter((opt) => !opt.disabled);
    if (enabledMatches.length === 1) {
      event.preventDefault();
      selectOption(enabledMatches[0].value);
    }
  }
}

function onDocumentClick(event: MouseEvent) {
  if (!isOpen.value) return;
  const target = event.target as Node | null;
  if (target && rootRef.value && !rootRef.value.contains(target)) {
    closeDropdown(false);
  }
}

watch(
  () => props.disabled,
  (isDisabled) => {
    if (isDisabled) {
      closeDropdown(false);
    }
  }
);

onMounted(() => {
  document.addEventListener('click', onDocumentClick);
});

onBeforeUnmount(() => {
  if (activeCloseDropdown === closeFromOutside) {
    activeCloseDropdown = null;
  }
  document.removeEventListener('click', onDocumentClick);
});
</script>

<template>
  <div
    ref="rootRef"
    class="searchable-select-wrap"
    :class="{ 'is-open': isOpen, 'is-disabled': disabled }"
  >
    <div class="searchable-trigger-shell">
      <!-- Select nativo sincronizado para validación HTML5, accesibilidad y compatibilidad de pruebas -->
      <select
        :id="id"
        :value="modelValue ?? ''"
        :required="required"
        :disabled="disabled"
        :data-testid="selectTestId"
        tabindex="-1"
        aria-hidden="true"
        class="survey-select native-sync-select"
        @change="onNativeSelectChange"
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
          v-for="opt in options"
          :key="`native-${String(opt.value)}`"
          :value="opt.value"
          :disabled="opt.disabled"
        >
          {{ opt.label }}
        </option>
      </select>

      <button
        ref="triggerRef"
        type="button"
        class="survey-select searchable-trigger-btn"
        :class="{ 'is-placeholder': isPlaceholderActive }"
        :disabled="disabled"
        aria-haspopup="listbox"
        :aria-expanded="isOpen"
        :aria-controls="`${id}-listbox`"
        :data-testid="`${id}-trigger`"
        @click="toggleDropdown"
      >
        <span class="searchable-trigger-text">{{ selectedOptionLabel }}</span>
        <i
          :class="['pi', isOpen ? 'pi-chevron-up' : 'pi-chevron-down', 'searchable-chevron']"
          aria-hidden="true"
        ></i>
      </button>
    </div>

    <div
      v-if="isOpen"
      :id="`${id}-listbox`"
      class="searchable-dropdown-panel"
      role="listbox"
      :aria-label="searchAriaLabel || placeholderOption || id"
      data-testid="searchable-dropdown-panel"
    >
      <div class="searchable-panel-header">
        <div class="searchable-search-box">
          <i class="pi pi-search searchable-search-icon" aria-hidden="true"></i>
          <input
            :id="`${id}-search`"
            ref="searchInputRef"
            v-model="searchQuery"
            type="search"
            class="survey-input searchable-search-input"
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
            @click="searchQuery = ''"
          >
            <i class="pi pi-times" aria-hidden="true"></i>
          </button>
        </div>
      </div>

      <ul class="searchable-options-list">
        <li v-if="allowClearEmptyOption && placeholderOption">
          <button
            type="button"
            role="option"
            class="searchable-option-item"
            :class="{ 'is-selected': isPlaceholderActive }"
            :aria-selected="isPlaceholderActive"
            @click="selectOption('')"
          >
            {{ placeholderOption }}
          </button>
        </li>

        <li v-if="filteredOptions.length === 0" class="searchable-empty-item">
          Sin coincidencias para «{{ searchQuery }}»
        </li>

        <li v-for="opt in filteredOptions" :key="String(opt.value)">
          <button
            type="button"
            role="option"
            class="searchable-option-item"
            :class="{
              'is-selected': String(opt.value) === String(modelValue ?? ''),
              'is-disabled': opt.disabled
            }"
            :disabled="opt.disabled"
            :aria-selected="String(opt.value) === String(modelValue ?? '')"
            @click="selectOption(opt.value)"
          >
            <span>{{ opt.label }}</span>
            <i
              v-if="String(opt.value) === String(modelValue ?? '')"
              class="pi pi-check searchable-check-icon"
              aria-hidden="true"
            ></i>
          </button>
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.searchable-select-wrap {
  position: relative;
  width: 100%;
}

.searchable-trigger-shell {
  position: relative;
  width: 100%;
}

.native-sync-select {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  pointer-events: none;
  z-index: 0;
}

.searchable-trigger-btn {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  width: 100%;
  text-align: left;
  cursor: pointer;
  background-image: none;
  padding-right: 0.875rem;
}

.searchable-trigger-btn.is-placeholder {
  color: var(--color-ash-helper, #6b7280);
}

.searchable-trigger-btn:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

.searchable-trigger-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.searchable-chevron {
  font-size: 0.85rem;
  color: var(--color-slate-caption, #374151);
  flex-shrink: 0;
}

.searchable-dropdown-panel {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  z-index: 80;
  background-color: var(--surface-card, #ffffff);
  border: 1px solid var(--border-color, #cbd5e1);
  border-radius: var(--radius-cards, 10px);
  box-shadow: 0 12px 28px rgba(2, 5, 32, 0.16);
  overflow: hidden;
}

.searchable-panel-header {
  padding: 0.5rem;
  background-color: var(--color-fog-surface, #f1f5f9);
  border-bottom: 1px solid var(--border-color, #e2e8f0);
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
  min-block-size: 40px;
  font-size: 0.9375rem;
  background-color: #ffffff;
}

.searchable-clear-btn {
  position: absolute;
  right: 0.35rem;
  width: 28px;
  height: 28px;
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

.searchable-options-list {
  list-style: none;
  margin: 0;
  padding: 0.25rem 0;
  max-height: 250px;
  overflow-y: auto;
  overscroll-behavior: contain;
}

.searchable-option-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  width: 100%;
  text-align: left;
  padding: 0.625rem 0.875rem;
  min-block-size: 44px;
  border: none;
  background: transparent;
  color: var(--color-midnight-ink, #020520);
  font-family: inherit;
  font-size: var(--text-body-sm, 0.9375rem);
  cursor: pointer;
  transition: background-color 0.12s ease;
}

.searchable-option-item:hover:not(:disabled) {
  background-color: var(--color-lavender-wash, #f0f4fe);
}

.searchable-option-item.is-selected {
  background-color: rgba(20, 90, 255, 0.1);
  color: var(--color-royal-signal, #145aff);
  font-weight: 600;
}

.searchable-option-item.is-disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.searchable-check-icon {
  font-size: 0.8rem;
  flex-shrink: 0;
}

.searchable-empty-item {
  padding: 0.875rem 1rem;
  font-size: var(--text-body-sm, 0.875rem);
  color: var(--color-ash-helper, #6b7280);
  text-align: center;
}
</style>
