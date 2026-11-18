<script setup lang="ts">
import { ref, computed, nextTick } from 'vue';
import { useToast } from 'primevue/usetoast';
import QuestionHelpTip from '@/components/common/QuestionHelpTip.vue';
import { QUESTION_HELP_TIPS } from '@/utils/questionHelpCatalog';
import type { ViajeOD, Residente } from '@/types/survey';
import { formatParroquia } from '@/utils/validation';
import { buildReturnTrip, getNombreResidente } from '@/utils/tripCatalogs';
import ViajeCardItem from './ViajeCardItem.vue';
import ViajeForm from './ViajeForm.vue';
import ViajeDetailModal from './ViajeDetailModal.vue';

const props = withDefaults(
  defineProps<{
    modelValue: ViajeOD[];
    zonaResidenciaDefault?: string;
    residentes?: Residente[];
  }>(),
  {
    modelValue: () => [],
    zonaResidenciaDefault: '',
    residentes: () => []
  }
);

const emit = defineEmits<{
  (e: 'update:modelValue', viajes: ViajeOD[]): void;
  (e: 'agregar-regreso', viajeRegreso: ViajeOD): void;
  (e: 'eliminar', index: number): void;
}>();

// Inyección segura de ToastService para notificaciones sutiles
let toast: ReturnType<typeof useToast> | null = null;
try {
  toast = useToast();
} catch {
  toast = null;
}

function notifySuccess(detail: string) {
  try {
    if (toast && typeof toast.add === 'function') {
      toast.add({
        severity: 'success',
        summary: 'Viaje Registrado',
        detail,
        life: 3000
      });
    }
  } catch {
    // Silencioso en modo headless
  }
}

// Referencia al contenedor de la sección para scroll suave
const sectionRef = ref<HTMLElement | null>(null);

async function scrollToSectionTop() {
  await nextTick();
  if (sectionRef.value && typeof sectionRef.value.scrollIntoView === 'function') {
    sectionRef.value.scrollIntoView({ behavior: 'smooth', block: 'start' });
  } else if (typeof window !== 'undefined' && typeof window.scrollTo === 'function') {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
}

// Calcular origen inteligente: si hay viajes, el último destino; si no, la residencia
const sugerenciaOrigen = computed(() => {
  if (props.modelValue.length > 0) {
    const ultimo = props.modelValue[props.modelValue.length - 1];
    return formatParroquia(ultimo.zona_od_destino) || formatParroquia(props.zonaResidenciaDefault) || '';
  }
  return formatParroquia(props.zonaResidenciaDefault) || '';
});

async function onViajeAgregado(viajeSinNumero: Omit<ViajeOD, 'viaje_numero'>) {
  const viaje: ViajeOD = {
    ...viajeSinNumero,
    viaje_numero: props.modelValue.length + 1
  };
  const actualizados = [...props.modelValue, viaje];
  emit('update:modelValue', actualizados);
  notifySuccess('Trayecto agregado correctamente.');
  await scrollToSectionTop();
}

async function agregarViajeRegreso(viajeIda: ViajeOD) {
  const regreso = buildReturnTrip(viajeIda, props.modelValue.length + 1, props.zonaResidenciaDefault);
  const actualizados = [...props.modelValue, regreso];
  emit('agregar-regreso', regreso);
  emit('update:modelValue', actualizados);
  notifySuccess('Viaje de regreso a casa agregado correctamente.');
  await scrollToSectionTop();
}

function eliminarViaje(index: number) {
  emit('eliminar', index);
  const actualizados = props.modelValue
    .filter((_, idx) => idx !== index)
    .map((v, i) => ({
      ...v,
      viaje_numero: i + 1
    }));
  emit('update:modelValue', actualizados);
}

// Modal para ver detalles completos del viaje
const viajeSeleccionado = ref<ViajeOD | null>(null);
const modalDetallesAbierto = ref<boolean>(false);

function verDetallesViaje(v: ViajeOD) {
  viajeSeleccionado.value = v;
  modalDetallesAbierto.value = true;
}

function cerrarModalDetalles() {
  modalDetallesAbierto.value = false;
  viajeSeleccionado.value = null;
}

const viajeFormRef = ref<{ resetDraft?: () => void } | null>(null);

function resetDraft() {
  viajeFormRef.value?.resetDraft?.();
}

defineExpose({ resetDraft });
</script>

<template>
  <div ref="sectionRef" class="viajes-section" aria-labelledby="titulo-viajes-od">
    <div class="viajes-header">
      <div class="survey-label-row">
        <h3 id="titulo-viajes-od" class="viajes-title">
          Registro de Viajes Cotidianos ({{ modelValue.length }})
        </h3>
        <QuestionHelpTip
          :text="QUESTION_HELP_TIPS.viajes"
          question-label="registro de viajes cotidianos"
        />
      </div>
      <p class="viajes-subtitle">
        SECCIÓN V: REGISTRO GENERAL DE VIAJES (Para todos los miembros del hogar mayores de 5 años)
      </p>
      <p class="viajes-desc">
        Instrucciones: Registrar los viajes realizados el día anterior (día laboral típico), entendiendo por viaje un desplazamiento de un punto de origen a un punto de destino con un propósito determinado.
      </p>
    </div>

    <!-- Lista de tarjetas resumidas adaptadas a móvil (360px sin overflow) -->
    <div v-if="modelValue.length > 0" class="viajes-list" role="list">
      <ViajeCardItem
        v-for="(v, idx) in modelValue"
        :key="v.viaje_numero"
        :viaje="v"
        :index="idx"
        :residente-nombre="getNombreResidente(residentes, v.persona_numero)"
        @ver-detalles="verDetallesViaje"
        @agregar-regreso="agregarViajeRegreso"
        @eliminar="eliminarViaje"
      />
    </div>

    <div v-else class="empty-state">
      <i class="pi pi-compass empty-icon" aria-hidden="true"></i>
      <p>Aún no se han registrado viajes. Use el formulario a continuación para agregar el primer trayecto.</p>
    </div>

    <!-- Formulario para agregar un nuevo viaje -->
    <ViajeForm
      ref="viajeFormRef"
      :residentes="residentes"
      :sugerencia-origen="sugerenciaOrigen"
      @agregar-viaje="onViajeAgregado"
    />

    <!-- Modal accesible con los detalles completos del viaje -->
    <ViajeDetailModal
      :open="modalDetallesAbierto"
      :viaje="viajeSeleccionado"
      :residente-nombre="viajeSeleccionado ? getNombreResidente(residentes, viajeSeleccionado.persona_numero) : ''"
      @close="cerrarModalDetalles"
    />
  </div>
</template>

<style scoped>
.viajes-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-16);
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
}

.viajes-title {
  font-size: var(--text-subheading);
  color: var(--color-midnight-ink);
  margin-block-end: var(--spacing-4);
}

.viajes-desc {
  font-size: var(--text-body-sm);
  color: var(--text-helper);
  line-height: 1.4;
}

.viajes-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-12);
  width: 100%;
}

.viajes-list :deep(.viaje-acciones) .action-btn,
.action-btn {
  min-block-size: var(--min-touch-target);
}

.empty-state {
  text-align: center;
  padding: var(--spacing-24);
  background-color: var(--color-fog-surface);
  border-radius: var(--radius-cards);
  color: var(--text-helper);
  font-size: var(--text-body-sm);
}

.empty-icon {
  font-size: 2rem;
  margin-block-end: var(--spacing-8);
  display: block;
  color: var(--text-helper);
}
</style>
