<script setup lang="ts">
import { computed } from 'vue';
import type {
  KpiMetrics,
  ParroquiaResultado,
  RepartoModalItem,
  MatrizODItem,
  PreguntaMetricaItem
} from '@/services/analyticsApi';

const props = withDefaults(
  defineProps<{
    kpis?: KpiMetrics | null;
    parroquias?: ParroquiaResultado[];
    repartoModal?: RepartoModalItem[];
    matrizOd?: MatrizODItem[];
    preguntas?: PreguntaMetricaItem[];
  }>(),
  {
    kpis: null,
    parroquias: () => [],
    repartoModal: () => [],
    matrizOd: () => [],
    preguntas: () => []
  }
);

const PARROQUIA_NOMBRES: Record<string, string> = {
  san_simon: 'San Simón',
  alto_de_los_godos: 'Alto de los Godos',
  boqueron: 'Boquerón',
  las_cocuizas: 'Las Cocuizas',
  santa_cruz: 'Santa Cruz',
  san_vicente: 'San Vicente',
  la_pica: 'La Pica',
  el_furrial: 'El Furrial',
  el_corozo: 'El Corozo',
  jusepin: 'Jusepín',
  la_cruz: 'La Cruz'
};

function formatParroquia(code: string): string {
  return PARROQUIA_NOMBRES[code] || code;
}

const totalRespuestasParroquias = computed<number>(() => {
  return props.parroquias.reduce((acc, p) => acc + p.total_respuestas, 0);
});

const totalViajesModal = computed<number>(() => {
  return props.repartoModal.reduce((acc, m) => acc + m.total_viajes, 0);
});

const totalViajesOd = computed<number>(() => {
  return props.matrizOd.reduce((acc, od) => acc + od.total_viajes, 0);
});
</script>

<template>
  <figure
    class="accessible-data-fallback"
    role="region"
    aria-label="Presentación tabular accesible de los datos del levantamiento municipal"
  >
    <figcaption class="accessible-caption">
      <div class="caption-header">
        <i class="pi pi-info-circle caption-icon" aria-hidden="true"></i>
        <h3 class="caption-title">Alternativa Tabular Accesible (Norma WCAG 2.1 Nivel AA)</h3>
      </div>
      <p class="caption-desc">
        Esta sección proporciona la totalidad de las métricas, repartos modales y flujos
        Origen-Destino en formato de tablas HTML semánticas estructuradas, legibles para lectores
        de pantalla y tecnologías de asistencia.
      </p>
    </figcaption>

    <!-- Resumen de Indicadores Ejecutivos -->
    <div v-if="kpis" class="accessible-summary-box" role="region" aria-label="Resumen de indicadores">
      <h4 class="table-section-title">Indicadores Generales</h4>
      <dl class="summary-list">
        <div class="summary-item">
          <dt>Total de encuestas registradas:</dt>
          <dd><strong>{{ kpis.total_encuestas.toLocaleString('es-VE') }}</strong></dd>
        </div>
        <div class="summary-item">
          <dt>Total de viajes registrados:</dt>
          <dd><strong>{{ kpis.total_viajes.toLocaleString('es-VE') }}</strong></dd>
        </div>
        <div class="summary-item">
          <dt>Total de residentes censados:</dt>
          <dd><strong>{{ kpis.total_residentes.toLocaleString('es-VE') }}</strong></dd>
        </div>
        <div class="summary-item">
          <dt>Parroquia con mayor participación:</dt>
          <dd><strong>{{ formatParroquia(kpis.parroquia_lider || 'Sin datos') }}</strong></dd>
        </div>
      </dl>
    </div>

    <!-- Tabla 1: Resultados por Parroquia -->
    <section class="table-section" aria-labelledby="table-parroquias-caption">
      <table class="accessible-table">
        <caption id="table-parroquias-caption" class="sr-caption">
          Distribución de respuestas ciudadanas recibidas por parroquia en el Municipio Maturín
        </caption>
        <thead>
          <tr>
            <th scope="col" class="text-left">Parroquia</th>
            <th scope="col" class="text-right">Total de Respuestas</th>
            <th scope="col" class="text-right">Porcentaje (%)</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="parroquias.length === 0">
            <td colspan="3" class="text-center empty-cell">No se registran datos para esta encuesta.</td>
          </tr>
          <tr
            v-for="p in parroquias"
            :key="p.parroquia"
          >
            <th scope="row" class="text-left row-header">{{ formatParroquia(p.parroquia) }}</th>
            <td class="text-right">{{ p.total_respuestas.toLocaleString('es-VE') }}</td>
            <td class="text-right">{{ p.porcentaje.toFixed(2) }}%</td>
          </tr>
        </tbody>
        <tfoot v-if="parroquias.length > 0">
          <tr>
            <th scope="row" class="text-left">Total Acumulado</th>
            <td class="text-right font-bold">{{ totalRespuestasParroquias.toLocaleString('es-VE') }}</td>
            <td class="text-right font-bold">100.00%</td>
          </tr>
        </tfoot>
      </table>
    </section>

    <!-- Tabla 2: Reparto Modal -->
    <section class="table-section" aria-labelledby="table-modal-caption">
      <table class="accessible-table">
        <caption id="table-modal-caption" class="sr-caption">
          Distribución de viajes registrados según el modo de transporte principal
        </caption>
        <thead>
          <tr>
            <th scope="col" class="text-left">Modo de Transporte</th>
            <th scope="col" class="text-right">Total de Viajes</th>
            <th scope="col" class="text-right">Porcentaje del Reparto (%)</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="repartoModal.length === 0">
            <td colspan="3" class="text-center empty-cell">No se registran viajes en esta encuesta.</td>
          </tr>
          <tr
            v-for="m in repartoModal"
            :key="m.modo"
          >
            <th scope="row" class="text-left row-header">{{ m.etiqueta }}</th>
            <td class="text-right">{{ m.total_viajes.toLocaleString('es-VE') }}</td>
            <td class="text-right">{{ m.porcentaje.toFixed(2) }}%</td>
          </tr>
        </tbody>
        <tfoot v-if="repartoModal.length > 0">
          <tr>
            <th scope="row" class="text-left">Total de Viajes</th>
            <td class="text-right font-bold">{{ totalViajesModal.toLocaleString('es-VE') }}</td>
            <td class="text-right font-bold">100.00%</td>
          </tr>
        </tfoot>
      </table>
    </section>

    <!-- Tabla 3: Matriz Origen - Destino -->
    <section class="table-section" aria-labelledby="table-od-caption">
      <table class="accessible-table">
        <caption id="table-od-caption" class="sr-caption">
          Matriz de pares de flujo Origen - Destino con tiempos y costos promedios
        </caption>
        <thead>
          <tr>
            <th scope="col" class="text-left">Zona Origen</th>
            <th scope="col" class="text-left">Zona Destino</th>
            <th scope="col" class="text-right">Total de Viajes</th>
            <th scope="col" class="text-right">Tiempo Promedio (min)</th>
            <th scope="col" class="text-right">Costo Promedio (Bs)</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="matrizOd.length === 0">
            <td colspan="5" class="text-center empty-cell">No se registran flujos de viajes O-D.</td>
          </tr>
          <tr
            v-for="(od, index) in matrizOd"
            :key="`${od.zona_origen}_${od.zona_destino}_${index}`"
          >
            <th scope="row" class="text-left row-header">{{ formatParroquia(od.zona_origen) }}</th>
            <td class="text-left">{{ formatParroquia(od.zona_destino) }}</td>
            <td class="text-right">{{ od.total_viajes.toLocaleString('es-VE') }}</td>
            <td class="text-right">
              {{ od.tiempo_promedio_min !== null ? `${od.tiempo_promedio_min.toFixed(1)} min` : 'N/D' }}
            </td>
            <td class="text-right">
              {{ od.costo_promedio_bs !== null ? `${od.costo_promedio_bs.toFixed(2)} Bs` : 'N/D' }}
            </td>
          </tr>
        </tbody>
        <tfoot v-if="matrizOd.length > 0">
          <tr>
            <th scope="row" colspan="2" class="text-left">Total General de Flujos</th>
            <td class="text-right font-bold">{{ totalViajesOd.toLocaleString('es-VE') }}</td>
            <td colspan="2" class="text-right">—</td>
          </tr>
        </tfoot>
      </table>
    </section>

    <!-- Tabla 4: Desglose Accesible por Cada Pregunta del Cuestionario -->
    <section v-if="preguntas && preguntas.length > 0" class="table-section" aria-labelledby="table-preguntas-caption">
      <h4 id="table-preguntas-caption" class="table-section-title">
        Desglose Tabular por Cada Pregunta del Cuestionario
      </h4>
      <div v-for="q in preguntas" :key="q.clave" class="question-table-group">
        <h5 class="question-item-title">{{ q.pregunta }} <span class="question-item-sec">({{ q.seccion }})</span></h5>
        <table class="accessible-table">
          <thead>
            <tr>
              <th scope="col" class="text-left">Opción / Categoría</th>
              <th scope="col" class="text-right">Respuestas</th>
              <th scope="col" class="text-right">Porcentaje</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="q.labels.length === 0">
              <td colspan="3" class="text-center empty-cell">No se registran datos para esta pregunta.</td>
            </tr>
            <tr v-for="(lbl, idx) in q.labels" :key="lbl">
              <th scope="row" class="text-left row-header">{{ lbl }}</th>
              <td class="text-right">{{ (q.values[idx] || 0).toLocaleString('es-VE') }}</td>
              <td class="text-right">
                {{ q.total_respuestas > 0 ? (((q.values[idx] || 0) / q.total_respuestas) * 100).toFixed(1) : '0' }}%
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </figure>
</template>

<style scoped>
.accessible-data-fallback {
  margin: 0;
  padding: var(--spacing-24);
  background-color: var(--surface-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-cards);
  box-shadow: var(--shadow-card);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-28);
}

.accessible-caption {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-8);
  border-bottom: 2px solid var(--color-lavender-wash);
  padding-bottom: var(--spacing-16);
}

.caption-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-8);
}

.caption-icon {
  font-size: 1.25rem;
  color: var(--color-royal-signal);
}

.caption-title {
  font-size: var(--text-subheading);
  font-weight: var(--font-weight-bold);
  color: var(--color-midnight-ink);
  margin: 0;
}

.caption-desc {
  font-size: var(--text-body-sm);
  color: var(--text-muted);
  line-height: 1.5;
  margin: 0;
}

/* Resumen */
.accessible-summary-box {
  background-color: var(--surface-subtle);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-cards);
  padding: var(--spacing-16);
}

.table-section-title {
  font-size: var(--text-body);
  font-weight: var(--font-weight-bold);
  color: var(--color-midnight-ink);
  margin: 0 0 var(--spacing-12) 0;
}

.summary-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: var(--spacing-12);
  margin: 0;
  padding: 0;
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.summary-item dt {
  font-size: var(--text-caption);
  color: var(--text-helper);
}

.summary-item dd {
  font-size: var(--text-body);
  color: var(--color-midnight-ink);
  margin: 0;
}

/* Tablas Semánticas */
.table-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-8);
  overflow-x: auto;
}

.accessible-table {
  width: 100%;
  border-collapse: collapse;
  font-family: var(--font-inter);
  font-size: var(--text-body-sm);
}

.accessible-table th,
.accessible-table td {
  padding: var(--spacing-12) var(--spacing-16);
  border-bottom: 1px solid var(--border-color);
}

.accessible-table thead th {
  background-color: var(--color-lavender-wash);
  color: var(--color-midnight-ink);
  font-weight: var(--font-weight-bold);
  border-top: 1px solid var(--border-color);
  border-bottom: 2px solid var(--border-color);
}

.accessible-table tbody tr:nth-child(even) {
  background-color: var(--surface-ground);
}

.accessible-table tbody tr:hover {
  background-color: var(--surface-subtle);
}

.accessible-table tfoot th,
.accessible-table tfoot td {
  background-color: var(--surface-subtle);
  border-top: 2px solid var(--border-color);
  color: var(--color-midnight-ink);
}

.row-header {
  font-weight: var(--font-weight-medium);
  color: var(--color-midnight-ink);
}

.text-left {
  text-align: left;
}

.text-right {
  text-align: right;
}

.text-center {
  text-align: center;
}

.font-bold {
  font-weight: var(--font-weight-bold);
}

.empty-cell {
  padding: var(--spacing-24) !important;
  color: var(--text-helper);
  font-style: italic;
}

.sr-caption {
  caption-side: top;
  text-align: left;
  font-size: var(--text-body);
  font-weight: var(--font-weight-bold);
  color: var(--color-midnight-ink);
  padding-bottom: var(--spacing-8);
}

.question-table-group {
  margin-top: var(--spacing-16);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-8);
}

.question-item-title {
  font-size: 0.95rem;
  font-weight: var(--font-weight-bold);
  color: var(--color-midnight-ink);
  margin: 0;
}

.question-item-sec {
  font-size: 0.8rem;
  font-weight: var(--font-weight-normal);
  color: var(--color-royal-signal);
}
</style>
