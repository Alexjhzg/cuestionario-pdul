<script setup lang="ts">
import { ref, onMounted } from 'vue';
import {
  fetchAdminEncuestas,
  updateEncuestaEstado,
  exportarRespuestasAdmin,
  descargarBlob,
  type EncuestaAdminItem
} from '@/services/api';

const emit = defineEmits<{
  (e: 'create-survey'): void;
  (e: 'edit-survey', surveyId: string): void;
  (e: 'view-responses', surveyId: string): void;
}>();

const surveys = ref<EncuestaAdminItem[]>([]);
const isLoading = ref<boolean>(true);
const errorMessage = ref<string | null>(null);
const successMessage = ref<string | null>(null);

// Opción global para exportación con anonimización PII
const redactPii = ref<boolean>(true);

// Estado de confirmación de desactivación
const showConfirmModal = ref<boolean>(false);
const surveyToDeactivate = ref<EncuestaAdminItem | null>(null);
const isTogglingStatus = ref<string | null>(null);

// Estado de exportación en progreso por encuesta
const exportingSurveyId = ref<string | null>(null);

async function loadSurveys() {
  isLoading.value = true;
  errorMessage.value = null;
  try {
    surveys.value = await fetchAdminEncuestas();
  } catch (err: any) {
    errorMessage.value = err?.problem?.detail || err?.message || 'Error al cargar las encuestas.';
  } finally {
    isLoading.value = false;
  }
}

onMounted(() => {
  loadSurveys();
});

// Manejo del switch de estado activo/inactivo
function onToggleClick(survey: EncuestaAdminItem) {
  if (survey.activa) {
    // Si está activa y se desea desactivar, solicitar confirmación
    surveyToDeactivate.value = survey;
    showConfirmModal.value = true;
  } else {
    // Si está inactiva, reactivar directamente
    performToggle(survey, true);
  }
}

async function performToggle(survey: EncuestaAdminItem, newStatus: boolean) {
  isTogglingStatus.value = survey.id;
  errorMessage.value = null;
  const previousStatus = survey.activa;
  survey.activa = newStatus; // Optimista

  try {
    await updateEncuestaEstado(survey.id, newStatus);
    successMessage.value = `Estado de "${survey.titulo}" actualizado a ${newStatus ? 'Activa' : 'Inactiva'}.`;
    setTimeout(() => (successMessage.value = null), 3000);
  } catch (err: any) {
    survey.activa = previousStatus; // Rollback
    errorMessage.value = `Error al cambiar estado: ${err?.problem?.detail || err?.message || 'Error de red'}`;
  } finally {
    isTogglingStatus.value = null;
    showConfirmModal.value = false;
    surveyToDeactivate.value = null;
  }
}

function confirmDeactivation() {
  if (surveyToDeactivate.value) {
    performToggle(surveyToDeactivate.value, false);
  }
}

function cancelDeactivation() {
  showConfirmModal.value = false;
  surveyToDeactivate.value = null;
}

// Exportación masiva de respuestas
async function handleExport(survey: EncuestaAdminItem, format: 'csv' | 'json') {
  exportingSurveyId.value = `${survey.id}-${format}`;
  errorMessage.value = null;
  try {
    const blob = await exportarRespuestasAdmin(survey.id, format, redactPii.value);
    const filename = `${survey.slug}_respuestas_${redactPii.value ? 'anonimizado_' : ''}${new Date().toISOString().slice(0, 10)}.${format}`;
    descargarBlob(blob, filename);
    successMessage.value = `Exportación ${format.toUpperCase()} descargada exitosamente.`;
    setTimeout(() => (successMessage.value = null), 3000);
  } catch (err: any) {
    errorMessage.value = `Error al exportar respuestas: ${err?.problem?.detail || err?.message || err}`;
  } finally {
    exportingSurveyId.value = null;
  }
}

// Formateador de fechas
function formatFecha(isoDate: string | null | undefined): string {
  if (!isoDate) return 'Sin fecha';
  try {
    const d = new Date(isoDate);
    if (isNaN(d.getTime())) return isoDate;
    return new Intl.DateTimeFormat('es-VE', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    }).format(d);
  } catch {
    return isoDate;
  }
}

function formatTipoInstrumento(tipo: string): string {
  switch (tipo) {
    case 'encuesta_od_pdul':
      return 'Origen-Destino (PDUL)';
    case 'consulta_ciudadana':
      return 'Consulta Ciudadana';
    case 'estudio_movilidad':
      return 'Estudio Movilidad';
    default:
      return tipo;
  }
}
</script>

<template>
  <div class="admin-survey-list-view" role="main" aria-labelledby="admin-title">
    <header class="admin-header">
      <div class="header-titles">
        <h1 id="admin-title" class="admin-title">Gestión de Encuestas</h1>
        <p class="admin-subtitle">
          Supervisión de instrumentos activos, recepción de respuestas ciudadanas y exportación masiva soberana.
        </p>
      </div>

      <div class="header-actions">
        <!-- Toggle de anonimización PII para descargas -->
        <label class="pii-export-control" for="pii-redact-checkbox">
          <input
            id="pii-redact-checkbox"
            v-model="redactPii"
            type="checkbox"
            class="pii-checkbox"
            data-testid="checkbox-redact-pii"
          />
          <span class="pii-label">
            <i class="pi pi-shield" aria-hidden="true"></i>
            Anonimizar datos personales (PII) al exportar
          </span>
        </label>

        <!-- Opción de Crear Encuesta (Oculta para prevenir creación no autorizada) -->
        <button
          type="button"
          class="admin-btn btn-primary"
          style="display: none;"
          @click="emit('create-survey')"
          aria-label="Crear una nueva encuesta en el constructor visual"
          data-testid="btn-create-new-survey"
        >
          <i class="pi pi-plus" aria-hidden="true"></i>
          <span>Nueva Encuesta</span>
        </button>
      </div>
    </header>

    <!-- Alertas de estado -->
    <div v-if="successMessage" class="feedback-alert success-alert" role="status" aria-live="polite">
      <i class="pi pi-check-circle" aria-hidden="true"></i>
      <span>{{ successMessage }}</span>
    </div>

    <div v-if="errorMessage" class="feedback-alert error-alert" role="alert">
      <i class="pi pi-exclamation-triangle" aria-hidden="true"></i>
      <span>{{ errorMessage }}</span>
    </div>

    <!-- Estado de carga -->
    <div v-if="isLoading" class="loading-state" role="status" aria-live="polite">
      <i class="pi pi-spin pi-spinner loading-spinner" aria-hidden="true"></i>
      <span>Cargando listado de encuestas registradas...</span>
    </div>

    <!-- Estado vacío -->
    <div v-else-if="surveys.length === 0" class="empty-state">
      <i class="pi pi-inbox empty-icon" aria-hidden="true"></i>
      <h2 class="empty-title">No hay encuestas registradas</h2>
      <p class="empty-desc">Crea tu primera encuesta utilizando el constructor visual Form.io.</p>
      <button
        type="button"
        class="admin-btn btn-primary"
        style="display: none;"
        @click="emit('create-survey')"
      >
        <i class="pi pi-plus" aria-hidden="true"></i>
        <span>Crear Encuesta</span>
      </button>
    </div>

    <!-- Contenedor con layout dual (Tabla en Desktop, Tarjetas en Móvil) -->
    <div v-else class="surveys-container">
      <!-- Layout Desktop: Tabla accesible -->
      <div class="desktop-table-wrapper" role="region" aria-label="Tabla de encuestas registradas" tabindex="0">
        <table class="admin-table">
          <caption class="sr-only">Listado de encuestas con estado y opciones de exportación</caption>
          <thead>
            <tr>
              <th scope="col">Título y Slug</th>
              <th scope="col">Tipo</th>
              <th scope="col">Fecha</th>
              <th scope="col">Respuestas</th>
              <th scope="col">Disponibilidad</th>
              <th scope="col">Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in surveys" :key="s.id" class="survey-row" :data-testid="`survey-row-${s.id}`">
              <td class="col-title">
                <span class="survey-title-text">{{ s.titulo }}</span>
                <code class="survey-slug-code">{{ s.slug }}</code>
              </td>
              <td>
                <span class="type-badge">{{ formatTipoInstrumento(s.tipo_instrumento) }}</span>
              </td>
              <td>
                <span class="date-text">{{ formatFecha(s.creado_en) }}</span>
              </td>
              <td>
                <span class="responses-count-badge" :data-testid="`total-respuestas-${s.id}`">
                  <i class="pi pi-users" aria-hidden="true"></i>
                  {{ s.total_respuestas }}
                </span>
              </td>
              <td>
                <div class="switch-cell">
                  <button
                    type="button"
                    role="switch"
                    :aria-checked="s.activa"
                    :disabled="isTogglingStatus === s.id"
                    class="accessible-switch"
                    :class="{ 'is-active': s.activa }"
                    :aria-label="`Alternar estado de ${s.titulo}. Actualmente ${s.activa ? 'activa' : 'inactiva'}`"
                    @click="onToggleClick(s)"
                    :data-testid="`switch-status-${s.id}`"
                  >
                    <span class="switch-thumb"></span>
                  </button>
                  <span class="status-label" :class="s.activa ? 'label-active' : 'label-inactive'">
                    {{ s.activa ? 'Activa' : 'Inactiva' }}
                  </span>
                </div>
              </td>
              <td>
                <div class="row-actions">
                  <button
                    type="button"
                    class="action-btn btn-view"
                    aria-label="Ver respuestas ciudadanas"
                    @click="emit('view-responses', s.id)"
                    :data-testid="`btn-view-responses-${s.id}`"
                  >
                    <i class="pi pi-table" aria-hidden="true"></i>
                    <span>Respuestas</span>
                  </button>

                  <button
                    type="button"
                    class="action-btn btn-edit"
                    aria-label="Abrir en Constructor"
                    @click="emit('edit-survey', s.id)"
                    :data-testid="`btn-edit-survey-${s.id}`"
                  >
                    <i class="pi pi-pencil" aria-hidden="true"></i>
                    <span>Constructor</span>
                  </button>

                  <button
                    type="button"
                    class="action-btn btn-export"
                    :disabled="exportingSurveyId === `${s.id}-csv`"
                    aria-label="Exportar respuestas en CSV"
                    @click="handleExport(s, 'csv')"
                    :data-testid="`btn-export-csv-${s.id}`"
                  >
                    <i v-if="exportingSurveyId === `${s.id}-csv`" class="pi pi-spin pi-spinner"></i>
                    <i v-else class="pi pi-file-excel"></i>
                    <span>CSV</span>
                  </button>

                  <button
                    type="button"
                    class="action-btn btn-export"
                    :disabled="exportingSurveyId === `${s.id}-json`"
                    aria-label="Exportar respuestas en JSON"
                    @click="handleExport(s, 'json')"
                    :data-testid="`btn-export-json-${s.id}`"
                  >
                    <i v-if="exportingSurveyId === `${s.id}-json`" class="pi pi-spin pi-spinner"></i>
                    <i v-else class="pi pi-file"></i>
                    <span>JSON</span>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Layout Móvil: Tarjetas responsivas -->
      <div class="mobile-cards-grid">
        <article
          v-for="s in surveys"
          :key="s.id"
          class="survey-card"
          :data-testid="`survey-card-${s.id}`"
        >
          <header class="card-header">
            <span class="type-badge">{{ formatTipoInstrumento(s.tipo_instrumento) }}</span>
            <span class="date-text">{{ formatFecha(s.creado_en) }}</span>
          </header>

          <h2 class="card-title">{{ s.titulo }}</h2>
          <code class="survey-slug-code">{{ s.slug }}</code>

          <div class="card-stats-row">
            <span class="responses-count-badge">
              <i class="pi pi-users" aria-hidden="true"></i>
              {{ s.total_respuestas }} respuestas
            </span>

            <div class="switch-cell">
              <button
                type="button"
                role="switch"
                :aria-checked="s.activa"
                :disabled="isTogglingStatus === s.id"
                class="accessible-switch"
                :class="{ 'is-active': s.activa }"
                @click="onToggleClick(s)"
              >
                <span class="switch-thumb"></span>
              </button>
              <span class="status-label" :class="s.activa ? 'label-active' : 'label-inactive'">
                {{ s.activa ? 'Activa' : 'Inactiva' }}
              </span>
            </div>
          </div>

          <div class="card-actions-grid">
            <button
              type="button"
              class="action-btn btn-view"
              @click="emit('view-responses', s.id)"
            >
              <i class="pi pi-table" aria-hidden="true"></i>
              <span>Respuestas</span>
            </button>

            <button
              type="button"
              class="action-btn btn-edit"
              @click="emit('edit-survey', s.id)"
            >
              <i class="pi pi-pencil" aria-hidden="true"></i>
              <span>Constructor</span>
            </button>

            <button
              type="button"
              class="action-btn btn-export"
              :disabled="exportingSurveyId === `${s.id}-csv`"
              @click="handleExport(s, 'csv')"
            >
              <i class="pi pi-file-excel" aria-hidden="true"></i>
              <span>CSV</span>
            </button>

            <button
              type="button"
              class="action-btn btn-export"
              :disabled="exportingSurveyId === `${s.id}-json`"
              @click="handleExport(s, 'json')"
            >
              <i class="pi pi-file" aria-hidden="true"></i>
              <span>JSON</span>
            </button>
          </div>
        </article>
      </div>
    </div>

    <!-- Diálogo de confirmación antes de desactivar encuesta -->
    <div
      v-if="showConfirmModal"
      class="modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-dialog-title"
      @keydown.esc="cancelDeactivation"
    >
      <div class="modal-dialog">
        <header class="modal-header">
          <h3 id="confirm-dialog-title" class="modal-title">¿Desactivar Encuesta?</h3>
          <button
            type="button"
            class="modal-close-btn"
            aria-label="Cerrar modal"
            @click="cancelDeactivation"
          >
            <i class="pi pi-times"></i>
          </button>
        </header>

        <div class="modal-body">
          <p class="modal-text">
            Está a punto de desactivar la encuesta:
          </p>
          <strong class="survey-name-highlight">{{ surveyToDeactivate?.titulo }}</strong>
          <p class="modal-warning">
            <i class="pi pi-exclamation-triangle" aria-hidden="true"></i>
            Mientras permanezca inactiva, los ciudadanos y encuestadores de campo no podrán enviar nuevas respuestas a este instrumento.
          </p>
        </div>

        <footer class="modal-footer">
          <button
            type="button"
            class="admin-btn btn-secondary"
            @click="cancelDeactivation"
            data-testid="btn-cancel-deactivation"
          >
            <span>Cancelar</span>
          </button>
          <button
            type="button"
            class="admin-btn btn-danger"
            @click="confirmDeactivation"
            data-testid="btn-confirm-deactivation"
          >
            <i class="pi pi-ban" aria-hidden="true"></i>
            <span>Sí, Desactivar Encuesta</span>
          </button>
        </footer>
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-survey-list-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--spacing-20);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-24);
}

.admin-header {
  background-color: var(--surface-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-containers);
  padding: var(--spacing-20);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-16);
  box-shadow: var(--shadow-sm);
}

@media (min-width: 768px) {
  .admin-header {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
  }
}

.admin-title {
  font-size: var(--text-heading-sm);
  color: var(--color-midnight-ink);
  font-weight: var(--font-weight-bold);
  margin: 0 0 var(--spacing-4) 0;
}

.admin-subtitle {
  font-size: var(--text-body-sm);
  color: var(--text-muted);
  margin: 0;
}

.header-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--spacing-16);
}

.pii-export-control {
  display: flex;
  align-items: center;
  gap: var(--spacing-8);
  min-block-size: var(--min-touch-target);
  cursor: pointer;
  padding: 0 var(--spacing-8);
  border-radius: var(--radius-cards);
}

.pii-checkbox {
  width: 20px;
  height: 20px;
  accent-color: var(--color-royal-signal);
  cursor: pointer;
}

.pii-label {
  font-size: var(--text-caption);
  color: var(--text-body-color);
  font-weight: var(--font-weight-medium);
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-4);
}

/* Botones principales */
.admin-btn {
  min-block-size: var(--min-touch-target);
  min-height: var(--min-touch-target);
  padding: 0 var(--spacing-20);
  border-radius: var(--radius-cards);
  font-size: var(--text-body-sm);
  font-weight: var(--font-weight-semibold);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-8);
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.2s ease;
}

.btn-primary {
  background-color: var(--color-royal-signal);
  color: #ffffff;
}

.btn-primary:hover {
  background-color: var(--color-cobalt-glow);
}

.btn-secondary {
  background-color: var(--surface-card);
  border-color: var(--border-color);
  color: var(--color-midnight-ink);
}

.btn-secondary:hover {
  background-color: var(--color-lavender-wash);
}

.btn-danger {
  background-color: var(--color-coral-lost);
  color: #ffffff;
}

.btn-danger:hover {
  background-color: #dc2626;
}

/* Alertas */
.feedback-alert {
  display: flex;
  align-items: center;
  gap: var(--spacing-12);
  padding: var(--spacing-16);
  border-radius: var(--radius-inputs);
  font-size: var(--text-body-sm);
}

.success-alert {
  background-color: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #166534;
}

.error-alert {
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
}

/* Estados de carga y vacío */
.loading-state,
.empty-state {
  background-color: var(--surface-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-containers);
  padding: var(--spacing-40);
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-16);
}

.loading-spinner {
  font-size: 2rem;
  color: var(--color-royal-signal);
}

.empty-icon {
  font-size: 3rem;
  color: var(--text-helper);
}

.empty-title {
  margin: 0;
  font-size: var(--text-subheading);
  color: var(--color-midnight-ink);
}

.empty-desc {
  margin: 0;
  color: var(--text-muted);
  font-size: var(--text-body-sm);
}

/* Tabla Desktop */
.desktop-table-wrapper {
  display: none;
  background-color: var(--surface-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-containers);
  box-shadow: var(--shadow-sm);
  overflow-x: auto;
}

@media (min-width: 768px) {
  .desktop-table-wrapper {
    display: block;
  }
}

.admin-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.admin-table th {
  background-color: var(--surface-subtle);
  padding: var(--spacing-16);
  font-size: var(--text-caption);
  text-transform: uppercase;
  color: var(--text-muted);
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0.5px;
  border-bottom: 1px solid var(--border-color);
}

.admin-table td {
  padding: var(--spacing-16);
  border-bottom: 1px solid var(--border-color);
  font-size: var(--text-body-sm);
  vertical-align: middle;
}

.survey-row:hover {
  background-color: var(--color-lavender-wash);
}

.col-title {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
  max-width: 320px;
}

.survey-title-text {
  font-weight: var(--font-weight-semibold);
  color: var(--color-midnight-ink);
}

.survey-slug-code {
  font-family: var(--font-roboto-mono);
  font-size: 0.75rem;
  color: var(--text-helper);
}

.type-badge {
  display: inline-block;
  background-color: var(--surface-subtle);
  color: var(--text-body-color);
  padding: var(--spacing-4) var(--spacing-8);
  border-radius: var(--radius-cards);
  font-size: var(--text-caption);
  font-weight: var(--font-weight-medium);
}

.date-text {
  color: var(--text-helper);
  font-size: var(--text-caption);
}

.responses-count-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-6);
  background-color: var(--color-lavender-wash);
  color: var(--color-royal-signal);
  font-weight: var(--font-weight-bold);
  padding: var(--spacing-4) var(--spacing-10);
  border-radius: var(--radius-pills);
  font-size: var(--text-caption);
}

/* Switch */
.switch-cell {
  display: flex;
  align-items: center;
  gap: var(--spacing-8);
}

.accessible-switch {
  min-block-size: var(--min-touch-target);
  min-height: var(--min-touch-target);
  min-inline-size: var(--min-touch-target);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: var(--min-touch-target);
  background: transparent;
  border: none;
  padding: 0;
  cursor: pointer;
  position: relative;
  flex-shrink: 0;
}

.accessible-switch::before {
  content: '';
  position: absolute;
  width: 48px;
  height: 26px;
  border-radius: var(--radius-pills);
  background-color: var(--color-stone-divider);
  transition: background-color 0.2s ease;
}

.accessible-switch.is-active::before {
  background-color: var(--color-mint-win);
}

.accessible-switch:disabled {
  opacity: 0.5;
  cursor: wait;
}

.switch-thumb {
  position: relative;
  z-index: 1;
  display: block;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background-color: #ffffff;
  box-shadow: var(--shadow-sm);
  transition: transform 0.2s ease;
  transform: translateX(-11px);
}

.accessible-switch.is-active .switch-thumb {
  transform: translateX(11px);
}

.status-label {
  font-size: var(--text-caption);
  font-weight: var(--font-weight-semibold);
}

.label-active {
  color: #166534;
}

.label-inactive {
  color: var(--text-helper);
}

/* Botones de acción en fila */
.row-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-8);
  flex-wrap: wrap;
}

.action-btn {
  min-block-size: var(--min-touch-target);
  min-height: var(--min-touch-target);
  padding: 0 var(--spacing-12);
  border-radius: var(--radius-cards);
  border: 1px solid var(--border-color);
  background-color: var(--surface-card);
  color: var(--color-midnight-ink);
  font-size: var(--text-caption);
  font-weight: var(--font-weight-semibold);
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-6);
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn:hover:not(:disabled) {
  background-color: var(--color-lavender-wash);
  border-color: var(--color-royal-signal);
  color: var(--color-royal-signal);
}

.action-btn:disabled {
  opacity: 0.6;
  cursor: wait;
}

/* Layout Móvil */
.mobile-cards-grid {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-16);
}

@media (min-width: 768px) {
  .mobile-cards-grid {
    display: none;
  }
}

.survey-card {
  background-color: var(--surface-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-containers);
  padding: var(--spacing-16);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-12);
  box-shadow: var(--shadow-sm);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  margin: 0;
  font-size: var(--text-body);
  color: var(--color-midnight-ink);
  font-weight: var(--font-weight-bold);
}

.card-stats-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-8) 0;
  border-top: 1px solid var(--border-color);
  border-bottom: 1px solid var(--border-color);
}

.card-actions-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-8);
}

/* Modal */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background-color: rgba(2, 5, 32, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-20);
  z-index: 9999;
}

.modal-dialog {
  background-color: #ffffff;
  border-radius: var(--radius-containers);
  width: 100%;
  max-width: 500px;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-xl);
}

.modal-header {
  padding: var(--spacing-16) var(--spacing-20);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-title {
  margin: 0;
  font-size: var(--text-subheading);
  color: var(--color-midnight-ink);
}

.modal-close-btn {
  min-block-size: var(--min-touch-target);
  min-height: var(--min-touch-target);
  width: 48px;
  height: 48px;
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-body {
  padding: var(--spacing-20);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-12);
}

.modal-text {
  margin: 0;
  color: var(--text-body-color);
}

.survey-name-highlight {
  color: var(--color-midnight-ink);
  font-size: var(--text-body);
}

.modal-warning {
  margin: 0;
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
  padding: var(--spacing-12);
  border-radius: var(--radius-cards);
  font-size: var(--text-caption);
  display: flex;
  gap: var(--spacing-8);
  align-items: flex-start;
}

.modal-footer {
  padding: var(--spacing-16) var(--spacing-20);
  border-top: 1px solid var(--border-color);
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-12);
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}
</style>
