<script setup lang="ts">
import { ref, shallowRef, onMounted, onBeforeUnmount, watch } from 'vue';
import { Formio } from '@formio/js';
import '@formio/js/dist/formio.full.min.css';

const props = withDefaults(
  defineProps<{
    modelValue?: Record<string, any>;
    displayMode?: 'form' | 'wizard';
    readOnly?: boolean;
  }>(),
  {
    modelValue: () => ({ display: 'form', components: [] }),
    displayMode: 'form',
    readOnly: false
  }
);

const emit = defineEmits<{
  (e: 'update:modelValue', value: Record<string, any>): void;
  (e: 'change', value: Record<string, any>): void;
  (e: 'error', error: string): void;
  (e: 'ready', instance: any): void;
}>();

const builderContainer = ref<HTMLElement | null>(null);
const builderInstance = shallowRef<any>(null);
const isInitializing = ref<boolean>(true);
const initError = ref<string | null>(null);
let isDestroyed = false;

/**
 * Neutraliza llamadas externas a servidores de Form.io para garantizar soberanía de datos
 */
function applySovereigntySettings() {
  try {
    if (typeof (Formio as any).setBaseUrl === 'function') {
      (Formio as any).setBaseUrl('');
    }
    if (typeof (Formio as any).setProjectUrl === 'function') {
      (Formio as any).setProjectUrl('');
    }
    if ((Formio as any).cdn && typeof (Formio as any).cdn.setBaseUrl === 'function') {
      (Formio as any).cdn.setBaseUrl('');
    }
  } catch {
    // Si no están disponibles en entornos simulados
  }
}

async function initBuilder() {
  if (!builderContainer.value) return;

  applySovereigntySettings();

  // Destruir instancia previa si existía
  if (builderInstance.value) {
    try {
      if (typeof builderInstance.value.off === 'function') {
        builderInstance.value.off('change');
      }
      if (typeof builderInstance.value.destroy === 'function') {
        builderInstance.value.destroy(true);
      }
    } catch {
      // Silenciar errores durante teardown previo
    }
    builderInstance.value = null;
  }

  isInitializing.value = true;
  initError.value = null;

  try {
    const rawSchema = props.modelValue || { display: props.displayMode, components: [] };
    const clonedSchema = JSON.parse(JSON.stringify(rawSchema));
    if (!clonedSchema.display) {
      clonedSchema.display = props.displayMode;
    }

    const builderOptions = {
      language: 'es',
      noAlerts: true,
      noSource: true,
      showFullJsonSchema: true,
      readOnly: props.readOnly,
      builder: {
        resource: false, // Deshabilita consultas a la nube de Form.io
        premium: false   // Deshabilita componentes de terceros
      }
    };

    if (typeof (Formio as any).builder === 'function') {
      const instance = await (Formio as any).builder(
        builderContainer.value,
        clonedSchema,
        builderOptions
      );

      if (isDestroyed) {
        instance?.destroy(true);
        return;
      }

      builderInstance.value = instance;

      if (instance && typeof instance.on === 'function') {
        instance.on('change', () => {
          const exported = instance.schema || instance.form || clonedSchema;
          emit('update:modelValue', exported);
          emit('change', exported);
        });
      }

      emit('ready', instance);
    }
  } catch (err: any) {
    const msg = err?.message || 'Error al inicializar el constructor Form.io';
    initError.value = msg;
    emit('error', msg);
  } finally {
    isInitializing.value = false;
  }
}

onMounted(() => {
  initBuilder();
});

onBeforeUnmount(() => {
  isDestroyed = true;
  if (builderInstance.value) {
    try {
      if (typeof builderInstance.value.off === 'function') {
        builderInstance.value.off('change');
      }
      if (typeof builderInstance.value.destroy === 'function') {
        builderInstance.value.destroy(true);
      }
    } catch {
      // Ignorar fallos de limpieza
    }
    builderInstance.value = null;
  }

  // Remueve modales huérfanos que Form.io cuelga directamente en document.body
  if (typeof document !== 'undefined') {
    const orphanModals = document.querySelectorAll('.formio-dialog');
    orphanModals.forEach((dialog) => dialog.remove());
    document.body.classList.remove('modal-open', 'formio-dialog-open');
  }
});

// Si cambia el esquema externamente de forma drástica, se actualiza el constructor
watch(
  () => props.modelValue,
  (newVal) => {
    if (builderInstance.value && newVal && typeof builderInstance.value.setForm === 'function') {
      try {
        builderInstance.value.setForm(JSON.parse(JSON.stringify(newVal)));
      } catch {
        // Ignorar si el builder está en proceso de redibujado
      }
    }
  },
  { deep: false }
);

defineExpose({
  getSchema: () => builderInstance.value?.schema || builderInstance.value?.form || props.modelValue,
  setSchema: (newSchema: Record<string, any>) => {
    if (builderInstance.value && typeof builderInstance.value.setForm === 'function') {
      builderInstance.value.setForm(JSON.parse(JSON.stringify(newSchema)));
    }
  },
  builderInstance
});
</script>

<template>
  <div class="formio-builder-wrapper">
    <div v-if="isInitializing" class="builder-loading" role="status" aria-live="polite">
      <i class="pi pi-spin pi-spinner loading-icon" aria-hidden="true"></i>
      <span>Cargando constructor visual soberano...</span>
    </div>

    <div v-if="initError" class="builder-error-alert" role="alert">
      <i class="pi pi-exclamation-triangle" aria-hidden="true"></i>
      <div class="error-content">
        <strong>Error en constructor visual:</strong>
        <span>{{ initError }}</span>
      </div>
    </div>

    <div
      ref="builderContainer"
      class="formio-builder-canvas"
      :class="{ 'is-empty': !modelValue?.components?.length }"
      data-testid="formio-builder-canvas"
    ></div>
  </div>
</template>

<style scoped>
.formio-builder-wrapper {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-16);
  width: 100%;
}

.builder-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-12);
  padding: var(--spacing-32);
  background-color: var(--surface-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-containers);
  color: var(--text-muted);
  font-size: var(--text-body);
}

.loading-icon {
  font-size: 1.5rem;
  color: var(--color-royal-signal);
}

.builder-error-alert {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-12);
  padding: var(--spacing-16);
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: var(--radius-inputs);
  color: #991b1b;
  font-size: var(--text-body-sm);
}

.error-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
}

.formio-builder-canvas {
  min-height: 520px;
  background-color: var(--surface-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-containers);
  padding: var(--spacing-20);
  box-shadow: var(--shadow-sm);
  overflow-x: auto;
}

/* Ergonomía táctil para componentes generados por Form.io */
:deep(.formcomponents) {
  min-width: 260px;
}

:deep(.formcomponent) {
  min-block-size: var(--min-touch-target);
  border-radius: var(--radius-cards);
  display: flex;
  align-items: center;
  padding: var(--spacing-8) var(--spacing-12);
  margin-bottom: var(--spacing-8);
  cursor: grab;
  border: 1px solid var(--border-color);
  background-color: var(--surface-subtle);
  font-weight: var(--font-weight-medium);
  transition: all 0.2s ease;
}

:deep(.formcomponent:hover) {
  border-color: var(--color-royal-signal);
  background-color: var(--color-lavender-wash);
}

:deep(.btn) {
  min-block-size: var(--min-touch-target);
  min-height: var(--min-touch-target);
  border-radius: var(--radius-cards);
  padding: 0 var(--spacing-16);
  font-weight: var(--font-weight-semibold);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-8);
}

:deep(.nav-tabs .nav-link) {
  min-block-size: var(--min-touch-target);
  display: inline-flex;
  align-items: center;
  padding: var(--spacing-10) var(--spacing-16);
  font-weight: var(--font-weight-medium);
}
</style>
