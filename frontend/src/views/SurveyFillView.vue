<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useSurveyDraft } from '@/composables/useSurveyDraft';
import { submitRespuesta, fetchEncuesta, type RespuestaSubmissionResponse } from '@/services/api';
import { detectDeviceInfo } from '@/utils/deviceInfo';
import SurveyWizard from '@/components/survey/SurveyWizard.vue';
import DraftRestoreBanner from '@/components/common/DraftRestoreBanner.vue';
import OfflineSyncBadge from '@/components/common/OfflineSyncBadge.vue';

const props = withDefaults(
  defineProps<{
    encuestaSlug?: string;
  }>(),
  {
    encuestaSlug: 'cuestionario-od-maturin'
  }
);

const {
  formData,
  currentStep,
  hasRestorableDraft,
  lastSavedAt,
  isOnline,
  restoreDraft,
  clearDraft,
  getOfflineQueue,
  enqueueOfflineSubmission,
  clearOfflineQueueItem
} = useSurveyDraft(props.encuestaSlug, {
  cedula: '',
  parroquia: '',
  residentes: [],
  viajes: [],
  rutas_tp_utilizadas: [],
  rutas_tp_utilizadas_otra: '',
  acepta_declaracion: true
});

const encuestaId = ref<string>('00000000-0000-0000-0000-000000000001');
const encuestaTitulo = ref<string>('Encuesta Origen-Destino Maturín (PDUL)');
const submitting = ref<boolean>(false);
const submitSuccess = ref<boolean>(false);
const submissionReceipt = ref<RespuestaSubmissionResponse | null>(null);
const submissionOfflineStored = ref<boolean>(false);
const syncCount = ref<number>(getOfflineQueue().length);
const generalError = ref<string | null>(null);

async function loadEncuestaInfo() {
  try {
    const data = await fetchEncuesta(props.encuestaSlug);
    if (data.id) encuestaId.value = data.id;
    if (data.titulo) encuestaTitulo.value = data.titulo;
  } catch {
    // Si no hay conexión o falla, continúa con valores por defecto
  }
}

async function handleSubmit(data: Record<string, any>) {
  submitting.value = true;
  generalError.value = null;

  const enrichedData: Record<string, any> = {
    ...data,
    ...detectDeviceInfo()
  };

  try {
    if (!isOnline.value) {
      // Sin conexión: guardar en cola offline
      const subId = enqueueOfflineSubmission(encuestaId.value, enrichedData);
      submissionOfflineStored.value = true;
      submitSuccess.value = true;
      submissionReceipt.value = {
        id: 0,
        fecha_registro: new Date().toISOString(),
        idempotent_replay: false,
        mensaje: `Respuesta resguardada localmente (ID: ${subId}). Se transmitirá al reconectar.`
      };
      syncCount.value = getOfflineQueue().length;
      return;
    }

    // En línea: enviar a la API
    const clientSubmissionId = crypto.randomUUID ? crypto.randomUUID() : 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
      const r = (Math.random() * 16) | 0;
      return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16);
    });

    const res = await submitRespuesta(encuestaId.value, {
      client_submission_id: clientSubmissionId,
      data: enrichedData
    });

    submissionReceipt.value = res;
    submitSuccess.value = true;
    submissionOfflineStored.value = false;
    clearDraft();
  } catch (err: any) {
    if (!navigator.onLine || err.message?.includes('fetch') || err.message?.includes('Network')) {
      // Fallo de red inesperado durante el envío: encolar offline
      const subId = enqueueOfflineSubmission(encuestaId.value, enrichedData);
      submissionOfflineStored.value = true;
      submitSuccess.value = true;
      submissionReceipt.value = {
        id: 0,
        fecha_registro: new Date().toISOString(),
        idempotent_replay: false,
        mensaje: `Falla de red. Respuesta encolada localmente (ID: ${subId}).`
      };
      syncCount.value = getOfflineQueue().length;
    } else {
      generalError.value = err.message || 'Ocurrió un error al enviar la encuesta. Intente nuevamente.';
    }
  } finally {
    submitting.value = false;
  }
}

async function syncPendingQueue() {
  const queue = getOfflineQueue();
  if (queue.length === 0) return;

  for (const item of queue) {
    try {
      await submitRespuesta(item.encuestaId, {
        client_submission_id: item.clientSubmissionId,
        data: item.data
      });
      clearOfflineQueueItem(item.clientSubmissionId);
    } catch {
      // Detener si aún hay problemas de red
      break;
    }
  }
  syncCount.value = getOfflineQueue().length;
}

function getCleanInitialFormData(): Record<string, any> {
  return {
    cedula: '',
    parroquia: '',
    comunidad_sector: '',
    comunidad_codigo: '',
    zona_residencia_od: '',
    avenida_calle: '',
    casa_apartamento: '',
    tipo_vivienda: '',
    tipo_vivienda_otro: '',
    total_cuartos_vivienda: '',
    grupos_gastos_separados: '',
    hogar_numero: '',
    cuartos_dormir_hogar: '',
    numero_personas_hogar: '',
    tenencia_vivienda: '',
    tenencia_vivienda_otro: '',
    residentes: [],
    viajes: [],
    rutas_tp_dia: '',
    rutas_tp_utilizadas: [],
    rutas_tp_utilizadas_otra: '',
    tiempo_espera_paradas_min: '',
    km_residencia_parada: '',
    dificultades_acceso_tp: '',
    principal_dificultad_tp: '',
    principal_dificultad_tp_otro: '',
    calificacion_servicio_tp: '',
    gasto_semanal_transporte_bs: '',
    acuerdo_rutas_directas: '',
    comentarios_transporte_maturin: '',
    cambio_movilidad_5_anos: '',
    motivo_cambio_desplazamiento: '',
    motivo_cambio_desplazamiento_otro: '',
    caminatas_mas_10min: '',
    usa_bicicleta: '',
    dias_camina_bici_semana: '',
    modo_actividades_centro: '',
    aceras_adecuadas: '',
    seguridad_desplazamiento_centro: '',
    frecuencia_visita_parques: '',
    actividades_parques: [],
    actividades_parques_otras: '',
    caminatas_ciudad: '',
    seguridad_parques_dia: '',
    seguridad_parques_noche: '',
    limpieza_parques: '',
    impedimentos_espacios: [],
    impedimentos_espacios_otras: '',
    satisfaccion_centro: '',
    mejoras_prioritarias: [],
    mejoras_prioritarias_otro: '',
    parque_mejorar_primero: '',
    disposicion_participar_mejoras: '',
    sugerencias_esparcimiento: '',
    acera_comoda: '',
    sectores_para_caminar: '',
    facilidad_llegada_parques: '',
    esparcimientos_faltantes: [],
    esparcimientos_faltantes_otros: '',
    cruce_peatonal_todas: '',
    cruce_demarcado_visible: '',
    seguridad_cruzar_interseccion: '',
    hay_semaforo_peatonal: '',
    mapas_senales_caminata: '',
    movilidad_reducida_sin_ayuda: '',
    nombres_calles_visibles: '',
    senalizacion_clara_sin_obstaculos: '',
    trayecto_pie_parada_seguro: '',
    aire_ruido_aceptables: '',
    conductores_ceden_paso: '',
    ciudad_prioriza_peaton: '',
    participacion_consultas_peatonales: '',
    planes_movilidad_peatonal_normativa: '',
    observaciones_generales: '',
    acepta_declaracion: true
  };
}

function startNewSurvey() {
  submitSuccess.value = false;
  submissionReceipt.value = null;
  submissionOfflineStored.value = false;
  formData.value = getCleanInitialFormData();
  currentStep.value = 0;
  clearDraft();
}

onMounted(() => {
  loadEncuestaInfo();
  syncCount.value = getOfflineQueue().length;
});
</script>

<template>
  <div class="survey-fill-view">
    <!-- Barra Superior de Estado y Conectividad (solo visible si sin conexión o con pendientes) -->
    <div v-if="!isOnline || (syncCount && syncCount > 0)" class="top-status-bar">
      <OfflineSyncBadge
        :is-online="isOnline"
        :pending-count="syncCount"
        @sync="syncPendingQueue"
      />
    </div>

    <!-- Banner para reanudar borrador si existe -->
    <DraftRestoreBanner
      :visible="hasRestorableDraft && !submitSuccess"
      :last-saved-at="lastSavedAt"
      :step="currentStep"
      @restore="restoreDraft"
      @discard="clearDraft"
    />

    <!-- Pantalla de Éxito / Confirmación de Envío -->
    <section v-if="submitSuccess" class="survey-card success-card" role="region" aria-label="Confirmación de envío">
      <div class="success-icon" aria-hidden="true">
        <i class="pi pi-check-circle"></i>
      </div>
      <h2 class="success-title">¡Encuesta Registrada Exitosamente!</h2>
      <p class="success-message">
        {{ submissionReceipt?.mensaje || 'Gracias por su participación en la formulación del Plan de Desarrollo Urbano Local de Maturín.' }}
      </p>

      <div class="receipt-box" v-if="submissionReceipt">
        <div class="receipt-item">
          <span class="receipt-label">Fecha de Registro:</span>
          <span class="receipt-value">{{ new Date(submissionReceipt.fecha_registro).toLocaleString('es-VE') }}</span>
        </div>
        <div class="receipt-item" v-if="submissionReceipt.id > 0">
          <span class="receipt-label">Folio / Número:</span>
          <span class="receipt-value">#{{ submissionReceipt.id }}</span>
        </div>
        <div class="receipt-item" v-if="submissionOfflineStored">
          <span class="receipt-label">Estado de Transmisión:</span>
          <span class="receipt-badge-offline">Resguardo Local Offline</span>
        </div>
      </div>

      <div class="success-actions">
        <button
          type="button"
          class="survey-btn survey-btn-primary"
          @click="startNewSurvey"
        >
          <i class="pi pi-plus" aria-hidden="true"></i>
          <span>Llenar otro cuestionario</span>
        </button>
      </div>
    </section>

    <!-- Asistente de la Encuesta -->
    <div v-else>
      <div v-if="generalError" class="general-error-banner" role="alert">
        <i class="pi pi-exclamation-triangle" aria-hidden="true"></i>
        <span>{{ generalError }}</span>
      </div>

      <SurveyWizard
        :model-value="formData"
        :step="currentStep"
        :submitting="submitting"
        :encuesta-titulo="encuestaTitulo"
        @update:model-value="formData = $event"
        @update:step="currentStep = $event"
        @submit="handleSubmit"
      />
    </div>
  </div>
</template>

<style scoped>
.survey-fill-view {
  width: 100%;
  max-width: 900px;
  margin: 0 auto;
  padding: var(--spacing-16);
  box-sizing: border-box;
}

@media (min-width: 768px) {
  .survey-fill-view {
    padding: var(--spacing-32) var(--spacing-20);
  }
}

.top-status-bar {
  display: flex;
  justify-content: flex-end;
  margin-block-end: var(--spacing-16);
}

.general-error-banner {
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  color: #b91c1c;
  padding: var(--spacing-12) var(--spacing-16);
  border-radius: var(--radius-cards);
  display: flex;
  align-items: center;
  gap: var(--spacing-10);
  margin-block-end: var(--spacing-16);
  font-size: var(--text-body-sm);
}

.success-card {
  text-align: center;
  padding: var(--spacing-40) var(--spacing-24);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-16);
}

.success-icon {
  font-size: 3.5rem;
  color: var(--color-mint-win);
}

.success-title {
  font-size: var(--text-subheading);
  color: var(--color-midnight-ink);
}

.success-message {
  font-size: var(--text-body);
  color: var(--color-slate-caption);
  max-width: 500px;
  line-height: 1.5;
}

.receipt-box {
  background-color: var(--color-fog-surface);
  border-radius: var(--radius-cards);
  padding: var(--spacing-16) var(--spacing-24);
  width: 100%;
  max-width: 450px;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-8);
  margin: var(--spacing-8) 0;
}

.receipt-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: var(--text-body-sm);
}

.receipt-label {
  color: var(--text-helper);
}

.receipt-value {
  font-weight: var(--font-weight-semibold);
  color: var(--color-midnight-ink);
  font-family: var(--font-roboto-mono);
}

.receipt-badge-offline {
  background-color: #fffbeb;
  color: #b45309;
  padding: 2px 8px;
  border-radius: var(--radius-buttons);
  font-size: var(--text-caption);
  font-weight: var(--font-weight-bold);
}

.success-actions {
  margin-top: var(--spacing-12);
}
</style>
