<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue';
import {
  fetchAdminEncuestas,
  fetchAdminRespuestas,
  type EncuestaAdminItem,
  type AdminRespuestaItem
} from '@/services/api';
import { usePiiMasking } from '@/composables/usePiiMasking';

const props = withDefaults(
  defineProps<{
    initialSurveyId?: string | null;
  }>(),
  {
    initialSurveyId: ''
  }
);

// Lista de encuestas y encuesta seleccionada
const surveys = ref<EncuestaAdminItem[]>([]);
const selectedSurveyId = ref<string>(props.initialSurveyId || '');
const loadingSurveys = ref<boolean>(false);

// Respuestas paginadas
const items = ref<AdminRespuestaItem[]>([]);
const totalRespuestas = ref<number>(0);
const currentPage = ref<number>(1);
const pageSize = ref<number>(10);
const isLoadingResponses = ref<boolean>(false);
const errorMessage = ref<string | null>(null);

// Modal de detalle e inspección JSON
const showDetailModal = ref<boolean>(false);
const selectedRespuesta = ref<AdminRespuestaItem | null>(null);
const maskPii = ref<boolean>(true);
const jsonCopied = ref<boolean>(false);

// Utilidad centralizada de enmascaramiento de PII
const { maskPiiData } = usePiiMasking();

// Cálculos de paginación
const totalPages = computed(() => {
  return Math.ceil(totalRespuestas.value / pageSize.value) || 1;
});

const skip = computed(() => {
  return (currentPage.value - 1) * pageSize.value;
});

// Carga inicial de encuestas
async function loadSurveysList() {
  loadingSurveys.value = true;
  try {
    surveys.value = await fetchAdminEncuestas();
    if (!selectedSurveyId.value && surveys.value.length > 0) {
      selectedSurveyId.value = surveys.value[0].id;
    }
  } catch (err: any) {
    errorMessage.value = `Error al cargar encuestas: ${err?.problem?.detail || err?.message || err}`;
  } finally {
    loadingSurveys.value = false;
  }
}

// Carga de respuestas para la encuesta seleccionada
async function loadResponses() {
  if (!selectedSurveyId.value) {
    items.value = [];
    totalRespuestas.value = 0;
    return;
  }

  const limitNum = Number(pageSize.value) || 10;
  const skipNum = Number(skip.value) || 0;

  isLoadingResponses.value = true;
  errorMessage.value = null;

  try {
    const data = await fetchAdminRespuestas(
      selectedSurveyId.value,
      skipNum,
      limitNum
    );
    items.value = data.items || [];
    totalRespuestas.value = data.total || 0;
  } catch (err: any) {
    errorMessage.value = `Error al cargar respuestas: ${err?.problem?.detail || err?.message || err}`;
    items.value = [];
    totalRespuestas.value = 0;
  } finally {
    isLoadingResponses.value = false;
  }
}

// Observadores de cambios
watch(
  () => props.initialSurveyId,
  (newId) => {
    if (newId && newId !== selectedSurveyId.value) {
      selectedSurveyId.value = newId;
    }
  }
);

watch(selectedSurveyId, () => {
  currentPage.value = 1;
  loadResponses();
});

watch(pageSize, () => {
  currentPage.value = 1;
  loadResponses();
});

watch(currentPage, () => {
  loadResponses();
});

onMounted(async () => {
  await loadSurveysList();
  if (selectedSurveyId.value) {
    await loadResponses();
  }
});

// Navegación de páginas
function goToPreviousPage() {
  if (currentPage.value > 1) {
    currentPage.value--;
  }
}

function goToNextPage() {
  if (currentPage.value < totalPages.value) {
    currentPage.value++;
  }
}

// Apertura y cierre del modal de inspección
function openDetail(respuesta: AdminRespuestaItem) {
  selectedRespuesta.value = respuesta;
  maskPii.value = true;
  detailViewMode.value = 'grid'; // Ficha amigable estilo Grid por defecto
  jsonCopied.value = false;
  showDetailModal.value = true;
}

function closeDetail() {
  showDetailModal.value = false;
  selectedRespuesta.value = null;
}

// Datos formateados para el modal (con PII enmascarada de forma recursiva)
const displayData = computed<Record<string, any>>(() => {
  if (!selectedRespuesta.value) return {};
  const cloned = JSON.parse(JSON.stringify(selectedRespuesta.value.datos || {})) as Record<string, any>;
  return maskPiiData(cloned, maskPii.value);
});

// Copia segura al portapapeles
function copyJson() {
  navigator.clipboard.writeText(JSON.stringify(displayData.value, null, 2));
  jsonCopied.value = true;
  setTimeout(() => (jsonCopied.value = false), 2500);
}

// Formateadores auxiliares
function formatFecha(isoDate: string | null | undefined): string {
  if (!isoDate) return 'Fecha no registrada';
  try {
    const d = new Date(isoDate);
    if (isNaN(d.getTime())) return isoDate;
    return new Intl.DateTimeFormat('es-VE', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    }).format(d);
  } catch {
    return isoDate;
  }
}

function formatParroquia(key: string | null | undefined): string {
  if (!key) return 'No especificada';
  const mapping: Record<string, string> = {
    san_simon: 'San Simón',
    alto_de_los_godos: 'Alto de Los Godos',
    boqueron: 'Boquerón',
    las_cocuizas: 'Las Cocuizas',
    santa_cruz: 'Santa Cruz',
    la_cruz: 'La Cruz',
    san_vicente: 'San Vicente',
    el_corozo: 'El Corozo',
    el_furrial: 'El Furrial',
    jusepin: 'Jusepín',
    la_pica: 'La Pica'
  };
  return mapping[key.toLowerCase()] || key.replace(/_/g, ' ');
}

function truncateUuid(uuid: string | null | undefined): string {
  if (!uuid) return '—';
  return uuid.slice(0, 8);
}

// Modo de visualización del modal: 'grid' (Ficha amigable no técnica) o 'json' (Técnico)
const detailViewMode = ref<'grid' | 'json'>('grid');

const TIPOS_VIVIENDA_LABELS: Record<string, string> = {
  quinta_casa_quinta: 'Quinta o Casa quinta',
  casa: 'Casa',
  apartamento_edificio: 'Apartamento en edificio',
  apartamento_quinta_casa: 'Apartamento en quinta o casa',
  casa_vecindad: 'Casa de vecindad',
  vivienda_rustica: 'Vivienda rústica (rancho)',
  otro: 'Otro tipo'
};

const TENENCIA_VIVIENDA_LABELS: Record<string, string> = {
  propia_pagada: 'Propia pagada totalmente',
  propia_pagandose: 'Propia pagándose',
  alquilada: 'Alquilada',
  alquilada_parte: 'Alquilada parte de la vivienda',
  cedida_trabajo: 'Cedida por trabajo',
  cedida_familiar: 'Cedida por familiar o amigo',
  tomada_invadida: 'Tomada / Invadida',
  otra_forma: 'Otra forma'
};

const PARENTESCO_LABELS: Record<string, string> = {
  '1': 'Jefe(a) de Hogar',
  '2': 'Cónyuge / Pareja',
  '3': 'Hijo(a) / Hijastro(a)',
  '4': 'Padre / Madre',
  '5': 'Hermano(a)',
  '6': 'Nieto(a)',
  '7': 'Otro familiar',
  '8': 'No familiar'
};

const NIVEL_EDUCATIVO_LABELS: Record<string, string> = {
  '1': 'Ninguno',
  '2': 'Primaria',
  '3': 'Secundaria',
  '4': 'Universitario',
  '5': 'Postgrado',
  ninguno: 'Ninguno',
  primaria: 'Primaria',
  secundaria: 'Secundaria',
  tecnico: 'Técnico',
  universitario: 'Universitario',
  postgrado: 'Postgrado / Maestría',
  doctorado: 'Doctorado'
};

const ACTIVIDAD_LABELS: Record<string, string> = {
  '1': 'Trabaja',
  '2': 'Estudia',
  '3': 'Oficios del hogar',
  '4': 'Jubilado / Pensionado',
  '5': 'Busca trabajo',
  '6': 'Otro',
  trabaja: 'Trabaja',
  estudia: 'Estudia',
  oficios_hogar: 'Oficios del hogar',
  jubilado: 'Jubilado / Pensionado',
  busca_trabajo: 'Busca trabajo',
  otro: 'Otro'
};

const MODOS_TRANSPORTE_LABELS: Record<string, string> = {
  '1': 'A pie',
  '2': 'Bicicleta',
  '3': 'Motocicleta',
  '4': 'Automóvil Particular',
  '5': 'Taxi',
  '6': 'Transporte público (bus, buseta)',
  '7': 'Transporte informal (por puesto, mototaxi)',
  '8': 'Otro',
  a_pie: 'A pie',
  bicicleta: 'Bicicleta',
  motocicleta: 'Motocicleta',
  automovil: 'Automóvil Particular',
  taxi: 'Taxi',
  transporte_publico: 'Transporte público',
  otro: 'Otro'
};

const MOTIVOS_VIAJE_LABELS: Record<string, string> = {
  '1': 'Trabajo',
  '2': 'Estudio',
  '3': 'Compras',
  '4': 'Salud',
  '5': 'Recreación',
  '6': 'Trámites',
  '7': 'Visita Familiar',
  '8': 'Otro',
  trabajo: 'Trabajo',
  estudio: 'Estudio',
  compras: 'Compras',
  salud: 'Salud',
  recreacion: 'Recreación',
  tramites: 'Trámites',
  visita_familiar: 'Visita Familiar',
  otro: 'Otro'
};

const CALIFICACION_LABELS: Record<string, string> = {
  muy_bueno: 'Muy bueno',
  muy_buena: 'Muy buena',
  bueno: 'Bueno',
  buena: 'Buena',
  regular: 'Regular',
  malo: 'Malo',
  mala: 'Mala',
  muy_malo: 'Muy malo',
  muy_mala: 'Muy mala',
  muy_seguro: 'Muy seguro',
  seguro: 'Seguro',
  neutral: 'Neutral',
  inseguro: 'Inseguro',
  muy_inseguro: 'Muy inseguro',
  bastante_seguro: 'Bastante seguro',
  poco_seguro: 'Poco seguro',
  nada_seguro: 'Nada seguro'
};

const ACUERDO_LABELS: Record<string, string> = {
  totalmente_de_acuerdo: 'Totalmente de acuerdo',
  de_acuerdo: 'De acuerdo',
  neutral: 'Neutral',
  en_desacuerdo: 'En desacuerdo',
  totalmente_en_desacuerdo: 'Totalmente en desacuerdo'
};

const DIFICULTAD_TP_LABELS: Record<string, string> = {
  frecuencia_baja: 'Frecuencia baja de unidades',
  sobrecupo: 'Sobrecupo / Exceso de pasajeros',
  falta_de_rutas: 'Falta de rutas',
  inseguridad: 'Inseguridad en paradas o unidades',
  otro: 'Otro motivo'
};

const FRECUENCIA_LABELS: Record<string, string> = {
  nunca: 'Nunca',
  ocasionalmente: 'Ocasionalmente',
  mensual: 'Mensual',
  semanal: 'Semanal',
  diario: 'Diario'
};

function humanLabel(map: Record<string, string>, val: any): string {
  if (val === undefined || val === null || val === '') return '—';
  const str = String(val).toLowerCase();
  return map[str] || map[val] || String(val).replace(/_/g, ' ');
}
</script>

<template>
  <div class="admin-responses-view" role="main" aria-labelledby="responses-title">
    <header class="responses-header">
      <div class="header-titles">
        <h1 id="responses-title" class="responses-title">Respuestas Ciudadanas Recibidas</h1>
        <p class="responses-subtitle">
          Supervisión de envíos en tiempo real, auditoría de completitud y protección integral de datos personales.
        </p>
      </div>

      <!-- Selector de encuesta a inspeccionar -->
      <div class="survey-selector-wrapper">
        <label for="survey-inspect-select" class="selector-label">Encuesta a Supervisar:</label>
        <select
          id="survey-inspect-select"
          v-model="selectedSurveyId"
          class="survey-select-input"
          :disabled="loadingSurveys"
          data-testid="select-survey-inspect"
        >
          <option value="" disabled>Seleccione una encuesta</option>
          <option v-for="s in surveys" :key="s.id" :value="s.id">
            {{ s.titulo }} ({{ s.total_respuestas }} respuestas)
          </option>
        </select>
      </div>
    </header>

    <!-- Alertas -->
    <div v-if="errorMessage" class="feedback-alert error-alert" role="alert">
      <i class="pi pi-exclamation-triangle" aria-hidden="true"></i>
      <span>{{ errorMessage }}</span>
    </div>

    <!-- Contenido principal -->
    <div class="responses-table-card">
      <!-- Barra superior de metainformación y tamaño de página -->
      <div class="table-top-bar">
        <div class="pagination-info" role="status" aria-live="polite">
          <span class="info-text" data-testid="pagination-info-text">
            Página {{ currentPage }} de {{ totalPages }} (Total: {{ totalRespuestas }} respuestas)
          </span>
        </div>

        <div class="page-size-selector">
          <label for="page-size-select" class="page-size-label">Filas por página:</label>
          <select
            id="page-size-select"
            v-model.number="pageSize"
            class="page-size-select"
            data-testid="select-page-size"
          >
            <option value="10">10</option>
            <option value="25">25</option>
            <option value="50">50</option>
          </select>
        </div>
      </div>

      <!-- Estado de carga -->
      <div v-if="isLoadingResponses" class="loading-state" role="status" aria-live="polite">
        <i class="pi pi-spin pi-spinner loading-spinner" aria-hidden="true"></i>
        <span>Cargando respuestas ciudadanas...</span>
      </div>

      <!-- Estado sin respuestas -->
      <div v-else-if="items.length === 0" class="empty-state">
        <i class="pi pi-inbox empty-icon" aria-hidden="true"></i>
        <h2 class="empty-title">Sin respuestas registradas</h2>
        <p class="empty-desc">
          Esta encuesta aún no ha recibido participaciones de ciudadanos ni encuestadores.
        </p>
      </div>

      <!-- Tabla accesible de respuestas -->
      <div v-else class="table-responsive-wrapper" role="region" aria-label="Tabla de respuestas ciudadanas" tabindex="0">
        <table class="responses-table">
          <caption>Listado paginado de respuestas recibidas con datos demográficos y movilidad</caption>
          <thead>
            <tr>
              <th scope="col">#</th>
              <th scope="col">Fecha de Registro</th>
              <th scope="col">Parroquia</th>
              <th scope="col">Zona O-D</th>
              <th scope="col">Residentes</th>
              <th scope="col">Viajes</th>
              <th scope="col">ID Cliente</th>
              <th scope="col">Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in items"
              :key="item.id"
              class="response-row"
              :data-testid="`response-row-${item.id}`"
            >
              <td class="col-id">#{{ item.id }}</td>
              <td class="col-date">{{ formatFecha(item.fecha_registro) }}</td>
              <td class="col-parroquia">
                <span class="parroquia-badge">{{ formatParroquia(item.parroquia) }}</span>
              </td>
              <td class="col-zona">{{ item.zona_od || 'No especificada' }}</td>
              <td class="col-count">
                <span class="count-pill">
                  <i class="pi pi-user" aria-hidden="true"></i>
                  {{ Array.isArray(item.datos?.residentes) ? item.datos.residentes.length : 0 }}
                </span>
              </td>
              <td class="col-count">
                <span class="count-pill">
                  <i class="pi pi-car" aria-hidden="true"></i>
                  {{ Array.isArray(item.datos?.viajes) ? item.datos.viajes.length : 0 }}
                </span>
              </td>
              <td class="col-uuid">
                <code class="client-id-code" :title="item.client_submission_id || ''">
                  {{ truncateUuid(item.client_submission_id) }}
                </code>
              </td>
              <td class="col-actions">
                <button
                  type="button"
                  class="btn-detail"
                  :aria-label="`Ver detalle de respuesta #${item.id}`"
                  @click="openDetail(item)"
                  :data-testid="`btn-detail-${item.id}`"
                >
                  <i class="pi pi-eye" aria-hidden="true"></i>
                  <span>Ver Detalle</span>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Controles inferiores de paginación -->
      <footer class="pagination-footer">
        <button
          type="button"
          class="page-btn"
          :disabled="currentPage <= 1 || isLoadingResponses"
          aria-label="Página anterior"
          @click="goToPreviousPage"
          data-testid="btn-prev-page"
        >
          <i class="pi pi-chevron-left" aria-hidden="true"></i>
          <span>Anterior</span>
        </button>

        <span class="current-page-badge" aria-current="page">
          Página {{ currentPage }} de {{ totalPages }}
        </span>

        <button
          type="button"
          class="page-btn"
          :disabled="currentPage >= totalPages || isLoadingResponses"
          aria-label="Página siguiente"
          @click="goToNextPage"
          data-testid="btn-next-page"
        >
          <span>Siguiente</span>
          <i class="pi pi-chevron-right" aria-hidden="true"></i>
        </button>
      </footer>
    </div>

    <!-- Modal de Inspección Detallada con Enmascaramiento PII -->
    <div
      v-if="showDetailModal && selectedRespuesta"
      class="modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-detail-title"
      @keydown.esc="closeDetail"
    >
      <div class="modal-dialog">
        <header class="modal-header">
          <div class="modal-header-titles">
            <h3 id="modal-detail-title" class="modal-title">
              Detalle de Respuesta #{{ selectedRespuesta.id }}
            </h3>
            <span class="modal-subtitle">
              Parroquia: {{ formatParroquia(selectedRespuesta.parroquia) }} | Registrado: {{ formatFecha(selectedRespuesta.fecha_registro) }}
            </span>
          </div>

          <button
            type="button"
            class="modal-close-btn"
            aria-label="Cerrar modal de detalle"
            @click="closeDetail"
            data-testid="btn-modal-close"
          >
            <i class="pi pi-times"></i>
          </button>
        </header>

        <!-- Barra de control de PII y Selector de Modo de Visualización -->
        <div class="pii-protection-bar">
          <div class="pii-controls-group">
            <label class="pii-toggle-label" for="mask-pii-checkbox">
              <input
                id="mask-pii-checkbox"
                v-model="maskPii"
                type="checkbox"
                class="pii-toggle-input"
                data-testid="checkbox-mask-pii"
              />
              <span class="pii-toggle-text">
                Enmascarar datos personales (PII)
              </span>
            </label>

            <span class="pii-badge" :class="maskPii ? 'badge-protected' : 'badge-revealed'">
              <i :class="['pi', maskPii ? 'pi-shield' : 'pi-unlock']"></i>
              {{ maskPii ? 'PII Protegido' : 'Datos Visibles (Inspección Supervisada)' }}
            </span>
          </div>

          <!-- Selector de Modo de Visualización (Ficha Grid vs JSON) -->
          <div class="view-mode-selector" role="tablist" aria-label="Modo de visualización de la respuesta">
            <button
              type="button"
              role="tab"
              class="mode-switch-btn"
              :class="{ active: detailViewMode === 'grid' }"
              :aria-selected="detailViewMode === 'grid'"
              @click="detailViewMode = 'grid'"
              data-testid="btn-view-mode-grid"
            >
              <i class="pi pi-th-large" aria-hidden="true"></i>
              <span>Ficha Grid</span>
            </button>
            <button
              type="button"
              role="tab"
              class="mode-switch-btn"
              :class="{ active: detailViewMode === 'json' }"
              :aria-selected="detailViewMode === 'json'"
              @click="detailViewMode = 'json'"
              data-testid="btn-view-mode-json"
            >
              <i class="pi pi-code" aria-hidden="true"></i>
              <span>JSON Técnico</span>
            </button>
          </div>
        </div>

        <div v-if="!maskPii" class="pii-warning-banner" role="alert">
          <i class="pi pi-exclamation-triangle" aria-hidden="true"></i>
          <span>Advertencia: Los datos personales están visibles exclusivamente para fines de supervisión técnica.</span>
        </div>

        <div class="modal-body">
          <!-- VISTA 1: FICHA INFORMATIVA EN GRID (Predeterminada para personal no técnico) -->
          <div v-show="detailViewMode === 'grid'" class="grid-detail-container" data-testid="grid-detail-viewer">
            <!-- 1. Identificación y Ubicación -->
            <section class="detail-grid-card">
              <header class="detail-card-header">
                <i class="pi pi-map-marker icon-header" aria-hidden="true"></i>
                <h4 class="card-section-title">I. Identificación y Ubicación de la Residencia</h4>
              </header>
              <div class="detail-fields-grid">
                <div class="detail-field">
                  <span class="field-title">Parroquia</span>
                  <span class="field-content highlight-badge">{{ formatParroquia(displayData.parroquia) }}</span>
                </div>
                <div class="detail-field">
                  <span class="field-title">Comunidad / Sector</span>
                  <span class="field-content">{{ displayData.comunidad_sector || 'No especificado' }}</span>
                </div>
                <div class="detail-field">
                  <span class="field-title">Zona O-D Residencia</span>
                  <span class="field-content">{{ displayData.zona_residencia_od || 'No especificada' }}</span>
                </div>
                <div class="detail-field">
                  <span class="field-title">Avenida / Calle</span>
                  <span class="field-content" :class="{ 'is-masked': maskPii && displayData.avenida_calle === '[PROTEGIDO / PII]' }">
                    {{ displayData.avenida_calle || '—' }}
                  </span>
                </div>
                <div class="detail-field">
                  <span class="field-title">Casa / Apartamento</span>
                  <span class="field-content" :class="{ 'is-masked': maskPii && displayData.casa_apartamento === '[PROTEGIDO / PII]' }">
                    {{ displayData.casa_apartamento || '—' }}
                  </span>
                </div>
                <div class="detail-field">
                  <span class="field-title">Cédula de Identidad</span>
                  <span class="field-content" :class="{ 'is-masked': maskPii && displayData.cedula === '[PROTEGIDO / PII]' }">
                    {{ displayData.cedula || 'No requerida / Anónimo' }}
                  </span>
                </div>
              </div>
            </section>

            <!-- 2. Vivienda y Condiciones del Hogar -->
            <section class="detail-grid-card">
              <header class="detail-card-header">
                <i class="pi pi-home icon-header" aria-hidden="true"></i>
                <h4 class="card-section-title">II. Vivienda y Condiciones del Hogar</h4>
              </header>
              <div class="detail-fields-grid">
                <div class="detail-field">
                  <span class="field-title">Tipo de Vivienda</span>
                  <span class="field-content font-bold">{{ humanLabel(TIPOS_VIVIENDA_LABELS, displayData.tipo_vivienda) }}</span>
                </div>
                <div class="detail-field">
                  <span class="field-title">Régimen de Tenencia</span>
                  <span class="field-content">{{ humanLabel(TENENCIA_VIVIENDA_LABELS, displayData.tenencia_vivienda) }}</span>
                </div>
                <div class="detail-field">
                  <span class="field-title">Total Cuartos de la Vivienda</span>
                  <span class="field-content">{{ displayData.total_cuartos_vivienda ?? '—' }}</span>
                </div>
                <div class="detail-field">
                  <span class="field-title">Cuartos para Dormir</span>
                  <span class="field-content">{{ displayData.cuartos_dormir_hogar ?? '—' }}</span>
                </div>
                <div class="detail-field">
                  <span class="field-title">Integrantes del Hogar</span>
                  <span class="field-content font-bold highlight-badge">{{ displayData.numero_personas_hogar ?? (displayData.residentes?.length || '—') }} personas</span>
                </div>
                <div class="detail-field">
                  <span class="field-title">Grupos de Gastos Separados</span>
                  <span class="field-content">{{ displayData.grupos_gastos_separados ?? '1' }}</span>
                </div>
              </div>
            </section>

            <!-- 3. Composición del Hogar (Residentes) -->
            <section class="detail-grid-card">
              <header class="detail-card-header">
                <i class="pi pi-users icon-header" aria-hidden="true"></i>
                <h4 class="card-section-title">III. Miembros del Hogar Registrados ({{ displayData.residentes?.length || 0 }})</h4>
              </header>
              
              <div v-if="displayData.residentes && displayData.residentes.length > 0" class="subgrid-cards">
                <article
                  v-for="(res, rIdx) in displayData.residentes"
                  :key="rIdx"
                  class="subgrid-item-card"
                >
                  <div class="subgrid-card-top">
                    <span class="subgrid-badge">Persona #{{ res.persona_numero || rIdx + 1 }}</span>
                    <strong class="subgrid-name" :class="{ 'is-masked': maskPii && (res.nombres === '[PROTEGIDO / PII]' || res.nombre_apellido === '[PROTEGIDO / PII]') }">
                      {{ res.nombres || res.nombre_apellido || `Integrante #${rIdx + 1}` }}
                    </strong>
                  </div>
                  <div class="subgrid-details">
                    <div><strong>Parentesco:</strong> {{ humanLabel(PARENTESCO_LABELS, res.parentesco) }}</div>
                    <div><strong>Sexo / Edad:</strong> {{ res.sexo === '1' ? 'Hombre' : res.sexo === '2' ? 'Mujer' : (res.sexo || '—') }} • {{ res.edad }} años</div>
                    <div><strong>Educación:</strong> {{ humanLabel(NIVEL_EDUCATIVO_LABELS, res.nivel_educativo) }}</div>
                    <div><strong>Actividad:</strong> {{ humanLabel(ACTIVIDAD_LABELS, res.actividad_principal || res.ocupacion_principal) }}</div>
                    <div v-if="res.medio_transporte_habitual">
                      <strong>Transporte habitual:</strong> {{ humanLabel(MODOS_TRANSPORTE_LABELS, res.medio_transporte_habitual) }}
                    </div>
                  </div>
                </article>
              </div>
              <p v-else class="empty-subtext">No se registraron integrantes adicionales.</p>
            </section>

            <!-- 4. Registro de Viajes Cotidianos -->
            <section class="detail-grid-card">
              <header class="detail-card-header">
                <i class="pi pi-send icon-header" aria-hidden="true"></i>
                <h4 class="card-section-title">IV. Registro de Viajes Realizados ({{ displayData.viajes?.length || 0 }})</h4>
              </header>

              <div v-if="displayData.viajes && displayData.viajes.length > 0" class="subgrid-cards">
                <article
                  v-for="(v, vIdx) in displayData.viajes"
                  :key="vIdx"
                  class="subgrid-item-card trip-subgrid-card"
                >
                  <div class="subgrid-card-top">
                    <span class="subgrid-badge trip-badge">Viaje #{{ v.viaje_numero || vIdx + 1 }}</span>
                    <span class="trip-mode-tag">{{ humanLabel(MODOS_TRANSPORTE_LABELS, v.modo_principal) }}</span>
                  </div>

                  <div class="trip-od-route">
                    <div class="od-step">
                      <i class="pi pi-circle-fill od-origin-dot" aria-hidden="true"></i>
                      <span><strong>Origen:</strong> {{ formatParroquia(v.zona_od_origen) }}</span>
                    </div>
                    <div class="od-arrow" aria-hidden="true"><i class="pi pi-arrow-down"></i></div>
                    <div class="od-step">
                      <i class="pi pi-map-marker od-dest-dot" aria-hidden="true"></i>
                      <span><strong>Destino:</strong> {{ formatParroquia(v.zona_od_destino) }}</span>
                    </div>
                  </div>

                  <div class="subgrid-details trip-meta-grid">
                    <div><strong>Motivo:</strong> {{ humanLabel(MOTIVOS_VIAJE_LABELS, v.motivo_viaje || v.proposito_viaje) }}</div>
                    <div><strong>Horario:</strong> {{ v.hora_salida || '—' }} ➔ {{ v.hora_llegada || '—' }}</div>
                    <div><strong>Duración:</strong> {{ v.tiempo_viaje_min ? `${v.tiempo_viaje_min} min` : '—' }}</div>
                    <div><strong>Costo:</strong> {{ v.costo_viaje_bs !== undefined && v.costo_viaje_bs !== null ? `Bs. ${v.costo_viaje_bs}` : 'Gratis / N/A' }}</div>
                  </div>
                </article>
              </div>
              <p v-else class="empty-subtext">No se registraron viajes para este hogar el día anterior.</p>
            </section>

            <!-- 5. Transporte Público -->
            <section class="detail-grid-card">
              <header class="detail-card-header">
                <i class="pi pi-car icon-header" aria-hidden="true"></i>
                <h4 class="card-section-title">V. Características de Transporte Público</h4>
              </header>
              <div class="detail-fields-grid">
                <div class="detail-field">
                  <span class="field-title">Calificación del Servicio</span>
                  <span class="field-content font-bold">{{ humanLabel(CALIFICACION_LABELS, displayData.calificacion_servicio_tp) }}</span>
                </div>
                <div class="detail-field">
                  <span class="field-title">Dificultad Principal</span>
                  <span class="field-content">{{ humanLabel(DIFICULTAD_TP_LABELS, displayData.principal_dificultad_tp || displayData.dificultades_acceso_tp) }}</span>
                </div>
                <div class="detail-field">
                  <span class="field-title">Tiempo de Espera en Parada</span>
                  <span class="field-content">{{ displayData.tiempo_espera_paradas_min !== undefined ? `${displayData.tiempo_espera_paradas_min} min` : '—' }}</span>
                </div>
                <div class="detail-field">
                  <span class="field-title">Distancia a la Parada</span>
                  <span class="field-content">{{ displayData.km_residencia_parada !== undefined ? `${displayData.km_residencia_parada} km` : '—' }}</span>
                </div>
                <div class="detail-field">
                  <span class="field-title">Rutas Utilizadas al Día</span>
                  <span class="field-content">{{ displayData.rutas_tp_dia ?? '0' }}</span>
                </div>
                <div class="detail-field">
                  <span class="field-title">Gasto Semanal Familiar</span>
                  <span class="field-content font-bold highlight-badge">{{ displayData.gasto_semanal_transporte_bs !== undefined ? `Bs. ${displayData.gasto_semanal_transporte_bs}` : '—' }}</span>
                </div>
                <div class="detail-field full-width">
                  <span class="field-title">¿De acuerdo con Rutas Directas?</span>
                  <span class="field-content">{{ humanLabel(ACUERDO_LABELS, displayData.acuerdo_rutas_directas) }}</span>
                </div>
              </div>
            </section>

            <!-- 6. Movilidad Activa y Percepción Urbana -->
            <section class="detail-grid-card">
              <header class="detail-card-header">
                <i class="pi pi-compass icon-header" aria-hidden="true"></i>
                <h4 class="card-section-title">VI. Movilidad Activa, Esparcimiento y Urbanismo</h4>
              </header>
              <div class="detail-fields-grid">
                <div class="detail-field">
                  <span class="field-title">Seguridad al Desplazarse en el Centro</span>
                  <span class="field-content">{{ humanLabel(CALIFICACION_LABELS, displayData.seguridad_centro || displayData.seguridad_desplazamiento_centro) }}</span>
                </div>
                <div class="detail-field">
                  <span class="field-title">Aceras Cómodas / Adecuadas</span>
                  <span class="field-content">{{ humanLabel(ACUERDO_LABELS, displayData.acuerdo_acera_comoda || displayData.aceras_adecuadas) }}</span>
                </div>
                <div class="detail-field">
                  <span class="field-title">Días que Camina / Usa Bicicleta</span>
                  <span class="field-content">{{ displayData.dias_camina_bici_semana !== undefined ? `${displayData.dias_camina_bici_semana} días/semana` : '—' }}</span>
                </div>
                <div class="detail-field">
                  <span class="field-title">Frecuencia Visita Parques / Plazas</span>
                  <span class="field-content">{{ humanLabel(FRECUENCIA_LABELS, displayData.frecuencia_visita_parques) }}</span>
                </div>
                <div class="detail-field">
                  <span class="field-title">Limpieza y Conservación</span>
                  <span class="field-content">{{ humanLabel(CALIFICACION_LABELS, displayData.limpieza_parques || displayData.calificacion_limpieza_parques) }}</span>
                </div>
                <div class="detail-field">
                  <span class="field-title">Disposición a Participar</span>
                  <span class="field-content font-bold">{{ displayData.disposicion_participar === 'si' || displayData.disposicion_participar_mejoras === 'si' ? 'Sí' : (displayData.disposicion_participar || displayData.disposicion_participar_mejoras || '—') }}</span>
                </div>
                <div v-if="displayData.observaciones_generales" class="detail-field full-width">
                  <span class="field-title">Observaciones / Propuestas del Ciudadano</span>
                  <p class="field-observations">{{ displayData.observaciones_generales }}</p>
                </div>
              </div>
            </section>
          </div>

          <!-- VISTA 2: VISOR JSON FORMATEADO (Técnico) -->
          <div v-show="detailViewMode === 'json'" class="json-viewer-wrapper">
            <pre class="json-code-viewer" data-testid="json-detail-viewer"><code>{{ JSON.stringify(displayData, null, 2) }}</code></pre>
          </div>
        </div>

        <footer class="modal-footer">
          <button
            type="button"
            class="builder-btn btn-secondary btn-copy"
            @click="copyJson"
            data-testid="btn-copy-json"
          >
            <i :class="['pi', jsonCopied ? 'pi-check' : 'pi-copy']"></i>
            <span>{{ jsonCopied ? '¡Copiado!' : 'Copiar JSON' }}</span>
          </button>

          <button
            type="button"
            class="builder-btn btn-primary"
            @click="closeDetail"
          >
            <span>Cerrar</span>
          </button>
        </footer>
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-responses-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--spacing-20);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-24);
}

.responses-header {
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
  .responses-header {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
  }
}

.responses-title {
  font-size: var(--text-heading-sm);
  color: var(--color-midnight-ink);
  font-weight: var(--font-weight-bold);
  margin: 0 0 var(--spacing-4) 0;
}

.responses-subtitle {
  font-size: var(--text-body-sm);
  color: var(--text-muted);
  margin: 0;
}

.survey-selector-wrapper {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
  min-width: 0;
  width: 100%;
  max-width: 360px;
}

.selector-label {
  font-size: var(--text-caption);
  font-weight: var(--font-weight-semibold);
  color: var(--color-midnight-ink);
}

.survey-select-input {
  min-block-size: var(--min-touch-target);
  min-height: var(--min-touch-target);
  padding: 0 var(--spacing-12);
  border-radius: var(--radius-inputs);
  border: 1px solid var(--border-color);
  background-color: #ffffff;
  font-size: var(--text-body-sm);
  color: var(--color-midnight-ink);
}

.survey-select-input:focus {
  outline: none;
  border-color: var(--color-royal-signal);
  box-shadow: 0 0 0 3px rgba(20, 90, 255, 0.15);
}

/* Tarjeta contenedora de tabla */
.responses-table-card {
  background-color: var(--surface-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-containers);
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.table-top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-16) var(--spacing-20);
  border-bottom: 1px solid var(--border-color);
  background-color: var(--surface-subtle);
  flex-wrap: wrap;
  gap: var(--spacing-12);
}

.info-text {
  font-size: var(--text-body-sm);
  color: var(--text-body-color);
  font-weight: var(--font-weight-medium);
}

.page-size-selector {
  display: flex;
  align-items: center;
  gap: var(--spacing-8);
}

.page-size-label {
  font-size: var(--text-caption);
  color: var(--text-muted);
}

.page-size-select {
  min-block-size: var(--min-touch-target);
  min-height: var(--min-touch-target);
  padding: 0 var(--spacing-12);
  border-radius: var(--radius-cards);
  border: 1px solid var(--border-color);
  background-color: #ffffff;
  font-size: var(--text-caption);
  color: var(--color-midnight-ink);
}

/* Tabla */
.table-responsive-wrapper {
  overflow-x: auto;
  width: 100%;
}

.responses-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.responses-table caption {
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

.responses-table th {
  background-color: #ffffff;
  padding: var(--spacing-16);
  font-size: var(--text-caption);
  text-transform: uppercase;
  color: var(--text-muted);
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0.5px;
  border-bottom: 2px solid var(--border-color);
}

.responses-table td {
  padding: var(--spacing-16);
  border-bottom: 1px solid var(--border-color);
  font-size: var(--text-body-sm);
  vertical-align: middle;
}

.response-row:hover {
  background-color: var(--color-lavender-wash);
}

.col-id {
  font-family: var(--font-roboto-mono);
  font-weight: var(--font-weight-bold);
  color: var(--color-royal-signal);
}

.col-date {
  color: var(--text-body-color);
  font-size: var(--text-caption);
}

.parroquia-badge {
  display: inline-block;
  background-color: var(--surface-subtle);
  color: var(--color-midnight-ink);
  padding: var(--spacing-4) var(--spacing-8);
  border-radius: var(--radius-cards);
  font-size: var(--text-caption);
  font-weight: var(--font-weight-semibold);
}

.count-pill {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-4);
  background-color: var(--surface-subtle);
  padding: var(--spacing-4) var(--spacing-8);
  border-radius: var(--radius-pills);
  font-size: var(--text-caption);
  font-weight: var(--font-weight-medium);
}

.client-id-code {
  font-family: var(--font-roboto-mono);
  font-size: 0.75rem;
  color: var(--text-helper);
  background-color: var(--surface-subtle);
  padding: 2px 6px;
  border-radius: 4px;
}

.btn-detail {
  min-block-size: var(--min-touch-target);
  min-height: var(--min-touch-target);
  padding: 0 var(--spacing-16);
  border-radius: var(--radius-cards);
  border: 1px solid var(--border-color);
  background-color: #ffffff;
  color: var(--color-midnight-ink);
  font-size: var(--text-caption);
  font-weight: var(--font-weight-semibold);
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-6);
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-detail:hover {
  background-color: var(--color-lavender-wash);
  border-color: var(--color-royal-signal);
  color: var(--color-royal-signal);
}

/* Paginación */
.pagination-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-16) var(--spacing-20);
  background-color: var(--surface-subtle);
  border-top: 1px solid var(--border-color);
}

.page-btn {
  min-block-size: var(--min-touch-target);
  min-height: var(--min-touch-target);
  padding: 0 var(--spacing-16);
  border-radius: var(--radius-cards);
  border: 1px solid var(--border-color);
  background-color: #ffffff;
  color: var(--color-midnight-ink);
  font-size: var(--text-body-sm);
  font-weight: var(--font-weight-semibold);
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-6);
  cursor: pointer;
  transition: all 0.2s ease;
}

.page-btn:hover:not(:disabled) {
  background-color: var(--color-lavender-wash);
  border-color: var(--color-royal-signal);
  color: var(--color-royal-signal);
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.current-page-badge {
  font-size: var(--text-body-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-body-color);
}

/* Alertas y estados */
.feedback-alert {
  display: flex;
  align-items: center;
  gap: var(--spacing-12);
  padding: var(--spacing-16);
  border-radius: var(--radius-inputs);
  font-size: var(--text-body-sm);
}

.error-alert {
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
}

.loading-state,
.empty-state {
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
  width: 95%;
  max-width: 960px;
  max-height: 88vh;
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

.modal-subtitle {
  font-size: var(--text-caption);
  color: var(--text-helper);
}

.modal-close-btn {
  min-block-size: var(--min-touch-target);
  min-height: var(--min-touch-target);
  width: 48px;
  height: 48px;
  background: none;
  border: none;
  border-radius: var(--radius-cards);
  color: var(--text-muted);
  font-size: 1.25rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-close-btn:hover {
  background-color: var(--surface-subtle);
  color: var(--color-midnight-ink);
}

.pii-protection-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-12) var(--spacing-20);
  background-color: var(--surface-subtle);
  border-bottom: 1px solid var(--border-color);
  flex-wrap: wrap;
  gap: var(--spacing-12);
}

.pii-controls-group {
  display: flex;
  align-items: center;
  gap: var(--spacing-16);
  flex-wrap: wrap;
}

.pii-toggle-label {
  display: flex;
  align-items: center;
  gap: var(--spacing-8);
  cursor: pointer;
  min-block-size: var(--min-touch-target);
}

.pii-toggle-input {
  width: 20px;
  height: 20px;
  accent-color: var(--color-royal-signal);
  cursor: pointer;
}

.pii-toggle-text {
  font-size: var(--text-caption);
  font-weight: var(--font-weight-semibold);
  color: var(--color-midnight-ink);
}

.pii-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-6);
  padding: var(--spacing-4) var(--spacing-10);
  border-radius: var(--radius-pills);
  font-size: var(--text-caption);
  font-weight: var(--font-weight-bold);
}

.badge-protected {
  background-color: #f0fdf4;
  color: #166534;
  border: 1px solid #bbf7d0;
}

.badge-revealed {
  background-color: #fffbeb;
  color: #92400e;
  border: 1px solid #fde68a;
}

/* Selector de Modo de Visualización (Ficha Grid vs JSON) */
.view-mode-selector {
  display: flex;
  gap: var(--spacing-4);
  background-color: #ffffff;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-inputs);
  padding: 3px;
}

.mode-switch-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-6);
  padding: 6px 12px;
  border-radius: var(--radius-cards);
  border: none;
  background: transparent;
  color: var(--text-muted);
  font-size: var(--text-caption);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
  transition: all 0.2s ease;
  min-block-size: var(--min-touch-target);
}

.mode-switch-btn:hover {
  color: var(--color-midnight-ink);
}

.mode-switch-btn.active {
  background-color: var(--color-royal-signal);
  color: #ffffff;
}

.pii-warning-banner {
  display: flex;
  align-items: center;
  gap: var(--spacing-8);
  padding: var(--spacing-10) var(--spacing-20);
  background-color: #fef2f2;
  border-bottom: 1px solid #fecaca;
  color: #991b1b;
  font-size: var(--text-caption);
}

.modal-body {
  padding: var(--spacing-20);
  overflow-y: auto;
  flex: 1;
}

/* Estilos de la Ficha Modal estilo Grid */
.grid-detail-container {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-16);
}

.detail-grid-card {
  background-color: #ffffff;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-cards);
  padding: var(--spacing-16);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-12);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.detail-card-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-8);
  border-bottom: 1px solid var(--border-color);
  padding-bottom: var(--spacing-8);
}

.detail-card-header .card-section-title {
  margin: 0;
  font-size: var(--text-body-sm);
  font-weight: var(--font-weight-bold);
  color: var(--color-midnight-ink);
}

.detail-card-header .icon-header {
  color: var(--color-royal-signal);
  font-size: 1.1rem;
}

.detail-fields-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-12);
}

.detail-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  background-color: var(--surface-subtle);
  padding: var(--spacing-8) var(--spacing-12);
  border-radius: var(--radius-inputs);
  border: 1px solid rgba(0, 0, 0, 0.03);
}

.detail-field.full-width {
  grid-column: 1 / -1;
}

.field-title {
  font-size: var(--text-caption);
  font-weight: var(--font-weight-semibold);
  color: var(--text-muted);
}

.field-content {
  font-size: var(--text-body-sm);
  color: var(--color-midnight-ink);
  word-break: break-word;
}

.field-content.font-bold {
  font-weight: var(--font-weight-bold);
}

.field-content.highlight-badge {
  color: var(--color-royal-signal);
  font-weight: var(--font-weight-bold);
}

.field-content.is-masked {
  color: #b45309;
  font-style: italic;
  font-family: var(--font-roboto-mono);
}

.subgrid-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--spacing-12);
}

.subgrid-item-card {
  background-color: var(--surface-subtle);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-cards);
  padding: var(--spacing-12);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-8);
}

.subgrid-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-8);
}

.subgrid-badge {
  background-color: var(--color-royal-signal);
  color: #ffffff;
  padding: 2px 8px;
  border-radius: var(--radius-pills);
  font-size: var(--text-caption);
  font-weight: var(--font-weight-bold);
}

.subgrid-name {
  font-size: var(--text-body-sm);
  color: var(--color-midnight-ink);
}

.subgrid-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: var(--text-caption);
  color: var(--text-body-color);
}

.trip-subgrid-card {
  border-left: 3px solid var(--color-royal-signal);
}

.trip-badge {
  background-color: var(--color-lavender-wash);
  color: var(--color-royal-signal);
  border: 1px solid var(--color-royal-signal);
}

.trip-mode-tag {
  font-size: var(--text-caption);
  font-weight: var(--font-weight-bold);
  color: var(--color-royal-signal);
}

.trip-od-route {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: var(--text-caption);
  background-color: #ffffff;
  padding: var(--spacing-8);
  border-radius: var(--radius-inputs);
  border: 1px solid var(--border-color);
}

.od-step {
  display: flex;
  align-items: center;
  gap: 6px;
}

.od-origin-dot {
  color: #16a34a;
  font-size: 0.5rem;
}

.od-dest-dot {
  color: #dc2626;
  font-size: 0.75rem;
}

.od-arrow {
  margin-left: 2px;
  color: var(--text-muted);
  font-size: 0.65rem;
}

.trip-meta-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px;
}

.empty-subtext {
  font-size: var(--text-caption);
  color: var(--text-muted);
  font-style: italic;
  margin: 0;
}

.field-observations {
  margin: 0;
  font-size: var(--text-body-sm);
  line-height: 1.5;
  color: var(--color-midnight-ink);
}

.json-viewer-wrapper {
  display: flex;
  flex-direction: column;
}

.json-code-viewer {
  background-color: var(--surface-subtle);
  padding: var(--spacing-16);
  border-radius: var(--radius-inputs);
  font-family: var(--font-roboto-mono);
  font-size: 0.85rem;
  overflow-x: auto;
  margin: 0;
  border: 1px solid var(--border-color);
}

.modal-footer {
  padding: var(--spacing-16) var(--spacing-20);
  border-top: 1px solid var(--border-color);
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-12);
}

.builder-btn {
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
}

.btn-primary {
  background-color: var(--color-royal-signal);
  color: #ffffff;
}

.btn-secondary {
  background-color: var(--surface-card);
  border-color: var(--border-color);
  color: var(--color-midnight-ink);
}

.btn-copy {
  min-block-size: var(--min-touch-target);
}
</style>
