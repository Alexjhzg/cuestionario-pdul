# Patrones UI/UX: Asistente Paso a Paso, Tarjetas Móviles O-D, Validación `:user-invalid` y Autoguardado Offline

## 1. CSS Base Nativo: Variables `:root` (`DESIGN.md`), Alcance `@formio/js`, Proximidad Gestalt y `:user-invalid`

```css
/* 1. Alcance de estilos para controles generados dinámicamente por @formio/js usando tokens de DESIGN.md */
.formio-local-wrapper :where(input:not([type="checkbox"]):not([type="radio"]), select, textarea) {
  font-family: var(--font-inter, 'Inter', system-ui, sans-serif);
  font-size: var(--text-body, 1rem);
  min-block-size: 48px;
  padding: 0.75rem 0.9375rem;
  border: 1px solid var(--color-stone-divider, #e2e8f0);
  border-radius: var(--radius-inputs, 12px);
  background-color: var(--surface-card, #ffffff);
  color: var(--color-graphite-body, #14141e);
  width: 100%;
  box-sizing: border-box;
}

/* Utilidad canónica para ocultar visualmente manteniendo accesibilidad y foco */
.visually-hidden:where(:not(:focus-within, :active)) {
  position: absolute !important;
  clip-path: inset(50%) !important;
  overflow: hidden !important;
  width: 1px !important;
  height: 1px !important;
  margin: -1px !important;
  padding: 0 !important;
  border: 0 !important;
  white-space: nowrap !important;
}

/* Regla de Proximidad de Gestalt + Tokens de DESIGN.md */
.survey-field {
  display: flex;
  flex-direction: column;
  margin-block-end: var(--spacing-24, 1.5rem);
  font-family: var(--font-inter, 'Inter', system-ui, sans-serif);
}

.survey-label {
  font-weight: var(--font-weight-semibold, 600);
  font-size: var(--text-body, 1rem);
  color: var(--color-graphite-body, #14141e);
  margin-block-end: var(--spacing-4, 0.25rem);
}

/* Las pistas (hints) van SIEMPRE arriba del input para que el teclado móvil no las tape */
.survey-hint {
  font-size: var(--text-body-sm, 0.875rem);
  color: var(--color-ash-helper, #6b7280);
  margin-block-end: var(--spacing-6, 0.375rem);
}

/* Controles con fuente >= 1rem (evita auto-zoom en iOS), radio 12px (DESIGN.md) y altura táctil >= 48px */
.survey-input,
.survey-select {
  font-family: var(--font-inter, 'Inter', system-ui, sans-serif);
  font-size: var(--text-body, 1rem);
  line-height: 1.5;
  padding: 0.75rem 0.9375rem;
  min-block-size: 48px;
  border: 1px solid var(--color-stone-divider, #e2e8f0);
  border-radius: var(--radius-inputs, 12px);
  background-color: var(--surface-card, #ffffff);
  color: var(--color-graphite-body, #14141e);
  box-sizing: border-box;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

@media (pointer: coarse) {
  .survey-input,
  .survey-select,
  .survey-radio-card {
    min-block-size: 52px;
  }
}

/* Foco de alto contraste usando --color-azure-focus (#0099ff) de DESIGN.md */
:where(.survey-input, .survey-select, .survey-btn, .survey-radio-input):focus-visible {
  outline: 3px solid var(--color-azure-focus, #0099ff);
  outline-offset: 2px;
}

/* Botones tipo píldora (9999px) con acento Royal Signal (#145aff) según DESIGN.md */
.survey-btn {
  border-radius: var(--radius-buttons, 9999px);
  padding: 14px 32px;
  font-weight: var(--font-weight-medium, 500);
  border: 1px solid var(--color-royal-signal, #145aff);
  color: var(--color-royal-signal, #145aff);
  background-color: var(--color-snow-canvas, #fcfcfc);
}

/* Validación tardía: solo muestra error DESPUÉS de que el usuario interactuó */
.survey-error-msg {
  display: none;
  color: #b91c1c;
  font-size: 0.875rem;
  font-weight: 500;
  margin-block-start: 0.375rem;
}

.survey-input:user-invalid,
.survey-input.user-invalid-fallback,
.survey-select:user-invalid,
.survey-select.user-invalid-fallback {
  border-color: #dc2626;
  background-color: #fef2f2;
}

.survey-input:user-invalid ~ .survey-error-msg,
.survey-input.user-invalid-fallback ~ .survey-error-msg,
.survey-select:user-invalid ~ .survey-error-msg,
.survey-select.user-invalid-fallback ~ .survey-error-msg {
  display: block;
}

.survey-input:required:user-valid {
  border-color: #15803d;
}
```

---

## 2. Sincronizador de `aria-invalid` y Fallback con `WeakMap`

```typescript
/**
 * Sincroniza el estado visual :user-invalid con aria-invalid="true" para lectores de pantalla
 * y provee fallback limpio basado en WeakMap si el navegador no soporta :user-invalid.
 */
export function initAccessibleFormValidation(formEl: HTMLFormElement): () => void {
  const dirtyState = new WeakMap<Element, { interacted: boolean; blurred: boolean }>();
  const supportsUserInvalid =
    typeof CSS !== 'undefined' && CSS.supports('selector(:user-invalid)');

  const syncControlState = (control: HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement) => {
    if (typeof control.checkValidity !== 'function') return;
    const isInvalid = supportsUserInvalid
      ? control.matches(':user-invalid')
      : !control.checkValidity();

    if (!supportsUserInvalid) {
      control.classList.toggle('user-invalid-fallback', isInvalid);
    }

    if (isInvalid) {
      control.setAttribute('aria-invalid', 'true');
    } else {
      control.removeAttribute('aria-invalid');
    }
  };

  const onBlur = (e: Event) => {
    const target = e.target as HTMLInputElement;
    if (!target || typeof target.checkValidity !== 'function') return;
    const st = dirtyState.get(target) ?? { interacted: false, blurred: false };
    st.blurred = true;
    dirtyState.set(target, st);
    if (supportsUserInvalid || st.interacted) {
      syncControlState(target);
    }
  };

  const onInput = (e: Event) => {
    const target = e.target as HTMLInputElement;
    if (!target || typeof target.checkValidity !== 'function') return;
    const st = dirtyState.get(target) ?? { interacted: false, blurred: false };
    st.interacted = true;
    dirtyState.set(target, st);
    if (target.hasAttribute('aria-invalid') || st.blurred) {
      syncControlState(target);
    }
  };

  const onSubmit = (e: Event) => {
    const controls = formEl.querySelectorAll<HTMLInputElement>('input, select, textarea');
    controls.forEach((ctrl) => {
      if (!ctrl.checkValidity()) {
        ctrl.classList.add('user-invalid-fallback');
        ctrl.setAttribute('aria-invalid', 'true');
      }
    });
  };

  formEl.addEventListener('blur', onBlur, true);
  formEl.addEventListener('input', onInput);
  formEl.addEventListener('change', onInput);
  formEl.addEventListener('submit', onSubmit);

  return () => {
    formEl.removeEventListener('blur', onBlur, true);
    formEl.removeEventListener('input', onInput);
    formEl.removeEventListener('change', onInput);
    formEl.removeEventListener('submit', onSubmit);
  };
}
```

---

## 3. Composable de Autoguardado Local e Idempotencia Offline (`useSurveyDraft.ts`)

```typescript
import { ref, watch, onMounted, onBeforeUnmount } from 'vue';

export interface OfflineQueueItem {
  clientSubmissionId: string;
  encuestaId: string;
  data: Record<string, unknown>;
  createdAt: string;
}

export function useSurveyDraft(encuestaSlug: string, initialData: Record<string, unknown> = {}) {
  const storageKey = `pdul_draft_${encuestaSlug}`;
  const queueKey = `pdul_offline_queue`;

  const formData = ref<Record<string, unknown>>({ ...initialData });
  const currentStep = ref<number>(0);
  const hasRestorableDraft = ref<boolean>(false);
  const lastSavedAt = ref<string | null>(null);
  const isOnline = ref<boolean>(typeof navigator !== 'undefined' ? navigator.onLine : true);

  function checkExistingDraft() {
    const raw = localStorage.getItem(storageKey);
    if (raw) {
      hasRestorableDraft.value = true;
    }
  }

  function restoreDraft() {
    const raw = localStorage.getItem(storageKey);
    if (!raw) return;
    const parsed = JSON.parse(raw);
    formData.value = parsed.data ?? {};
    currentStep.value = parsed.step ?? 0;
    lastSavedAt.value = parsed.savedAt ?? null;
    hasRestorableDraft.value = false;
  }

  function clearDraft() {
    localStorage.removeItem(storageKey);
    hasRestorableDraft.value = false;
    lastSavedAt.value = null;
  }

  watch(
    [formData, currentStep],
    ([newData, newStep]) => {
      const now = new Date().toLocaleTimeString('es-VE', { hour: '2-digit', minute: '2-digit' });
      localStorage.setItem(
        storageKey,
        JSON.stringify({ data: newData, step: newStep, savedAt: now })
      );
      lastSavedAt.value = now;
    },
    { deep: true }
  );

  function enqueueOfflineSubmission(encuestaId: string, payload: Record<string, unknown>): string {
    const clientSubmissionId = crypto.randomUUID();
    const rawQueue = localStorage.getItem(queueKey);
    const queue: OfflineQueueItem[] = rawQueue ? JSON.parse(rawQueue) : [];
    queue.push({
      clientSubmissionId,
      encuestaId,
      data: { ...payload, client_submission_id: clientSubmissionId },
      createdAt: new Date().toISOString()
    });
    localStorage.setItem(queueKey, JSON.stringify(queue));
    clearDraft();
    return clientSubmissionId;
  }

  const updateOnlineStatus = () => {
    isOnline.value = navigator.onLine;
  };

  onMounted(() => {
    checkExistingDraft();
    window.addEventListener('online', updateOnlineStatus);
    window.addEventListener('offline', updateOnlineStatus);
  });

  onBeforeUnmount(() => {
    window.removeEventListener('online', updateOnlineStatus);
    window.removeEventListener('offline', updateOnlineStatus);
  });

  return {
    formData,
    currentStep,
    hasRestorableDraft,
    lastSavedAt,
    isOnline,
    restoreDraft,
    clearDraft,
    enqueueOfflineSubmission
  };
}
```

---

## 4. Componente Móvil de Tarjetas de Viajes O-D con "Viaje de Regreso en 1 Toque" (`ViajesMobileCards.vue`)

```vue
<script setup lang="ts">
import { ref } from 'vue';
import Button from 'primevue/button';

export interface ViajeOD {
  viaje_numero: number;
  persona_numero: number;
  zona_od_origen: string;
  zona_od_destino: string;
  motivo_viaje: string;
  modo_principal: string;
  tiempo_viaje_min: number;
  costo_viaje_bs: number;
}

const props = defineProps<{
  zonaResidenciaDefault: string;
  modelValue: ViajeOD[];
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', viajes: ViajeOD[]): void;
}>();

const nuevoViaje = ref<ViajeOD>({
  viaje_numero: 1,
  persona_numero: 1,
  zona_od_origen: props.zonaResidenciaDefault,
  zona_od_destino: '',
  motivo_viaje: '1',
  modo_principal: '6',
  tiempo_viaje_min: 30,
  costo_viaje_bs: 0
});

function agregarViaje() {
  const actualizados = [
    ...props.modelValue,
    { ...nuevoViaje.value, viaje_numero: props.modelValue.length + 1 }
  ];
  emit('update:modelValue', actualizados);
  // Pre-llenar el siguiente origen con el destino anterior para encadenar viajes
  nuevoViaje.value.zona_od_origen = nuevoViaje.value.zona_od_destino;
  nuevoViaje.value.zona_od_destino = '';
}

function agregarViajeRegreso(viajeIda: ViajeOD) {
  const regreso: ViajeOD = {
    viaje_numero: props.modelValue.length + 1,
    persona_numero: viajeIda.persona_numero,
    zona_od_origen: viajeIda.zona_od_destino,
    zona_od_destino: props.zonaResidenciaDefault || viajeIda.zona_od_origen,
    motivo_viaje: viajeIda.motivo_viaje,
    modo_principal: viajeIda.modo_principal,
    tiempo_viaje_min: viajeIda.tiempo_viaje_min,
    costo_viaje_bs: viajeIda.costo_viaje_bs
  };
  emit('update:modelValue', [...props.modelValue, regreso]);
}

function eliminarViaje(index: number) {
  const copia = props.modelValue.filter((_, idx) => idx !== index);
  emit('update:modelValue', copia);
}
</script>

<template>
  <section aria-labelledby="titulo-viajes-od">
    <h3 id="titulo-viajes-od">Viajes Registrados ({{ modelValue.length }})</h3>

    <!-- Lista de tarjetas resumidas adaptadas a móvil -->
    <div v-for="(v, idx) in modelValue" :key="v.viaje_numero" class="viaje-card">
      <div class="viaje-resumen">
        <strong>Viaje {{ idx + 1 }} (Persona N° {{ v.persona_numero }})</strong>
        <p>{{ v.zona_od_origen }} → {{ v.zona_od_destino }} ({{ v.tiempo_viaje_min }} min)</p>
      </div>
      <div class="viaje-acciones">
        <Button
          type="button"
          severity="secondary"
          label="🔄 Agregar regreso a casa"
          :aria-label="`Agregar viaje de regreso a casa para el viaje ${idx + 1} desde ${v.zona_od_destino}`"
          @click="agregarViajeRegreso(v)"
        />
        <Button
          type="button"
          severity="danger"
          text
          label="Eliminar"
          :aria-label="`Eliminar viaje ${idx + 1} de ${v.zona_od_origen} a ${v.zona_od_destino}`"
          @click="eliminarViaje(idx)"
        />
      </div>
    </div>
  </section>
</template>
```

