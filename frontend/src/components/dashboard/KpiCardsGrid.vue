<script setup lang="ts">
import { computed } from 'vue';
import type {
  KpiMetrics,
  ParroquiaResultado,
  RepartoModalItem,
  MatrizODItem
} from '@/services/analyticsApi';

const props = withDefaults(
  defineProps<{
    kpis?: KpiMetrics | null;
    parroquias?: ParroquiaResultado[];
    repartoModal?: RepartoModalItem[];
    matrizOd?: MatrizODItem[];
    loading?: boolean;
  }>(),
  {
    kpis: null,
    parroquias: () => [],
    repartoModal: () => [],
    matrizOd: () => [],
    loading: false
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

const totalEncuestas = computed<number>(() => {
  return props.kpis?.total_encuestas ?? 0;
});

const totalViajes = computed<number>(() => {
  return props.kpis?.total_viajes ?? 0;
});

const totalResidentes = computed<number>(() => {
  return props.kpis?.total_residentes ?? 0;
});

const completitudEstimada = computed<{
  porcentaje: number;
  parroquiasConDatos: number;
  detalle: string;
}>(() => {
  if (!props.parroquias || props.parroquias.length === 0) {
    if (totalEncuestas.value > 0) {
      return {
        porcentaje: 100,
        parroquiasConDatos: 1,
        detalle: 'Respuestas registradas'
      };
    }
    return {
      porcentaje: 0,
      parroquiasConDatos: 0,
      detalle: 'Sin datos registrados'
    };
  }

  const conDatos = props.parroquias.filter((p) => p.total_respuestas > 0).length;
  const pct = (conDatos / 11) * 100;
  return {
    porcentaje: pct,
    parroquiasConDatos: conDatos,
    detalle: `${conDatos} de 11 parroquias con datos`
  };
});

const parroquiaLiderInfo = computed<{ nombre: string; porcentaje: number }>(() => {
  if (!props.parroquias || props.parroquias.length === 0) {
    if (props.kpis?.parroquia_lider) {
      const cod = props.kpis.parroquia_lider;
      return {
        nombre: PARROQUIA_NOMBRES[cod] || cod,
        porcentaje: 0
      };
    }
    return { nombre: 'Sin datos', porcentaje: 0 };
  }

  if (props.kpis?.parroquia_lider) {
    const cod = props.kpis.parroquia_lider;
    const match = props.parroquias.find((p) => p.parroquia === cod);
    if (match) {
      return {
        nombre: PARROQUIA_NOMBRES[match.parroquia] || match.parroquia,
        porcentaje: match.porcentaje
      };
    }
  }

  const sorted = [...props.parroquias].sort((a, b) => b.total_respuestas - a.total_respuestas);
  const best = sorted[0];
  if (best && best.total_respuestas > 0) {
    return {
      nombre: PARROQUIA_NOMBRES[best.parroquia] || best.parroquia,
      porcentaje: best.porcentaje
    };
  }

  return { nombre: 'Sin datos', porcentaje: 0 };
});

const modoPredominanteInfo = computed<{ etiqueta: string; porcentaje: number }>(() => {
  if (!props.repartoModal || props.repartoModal.length === 0) {
    return { etiqueta: 'Sin datos', porcentaje: 0 };
  }

  const sorted = [...props.repartoModal].sort((a, b) => b.total_viajes - a.total_viajes);
  const best = sorted[0];
  if (best && best.total_viajes > 0) {
    return {
      etiqueta: best.etiqueta,
      porcentaje: best.porcentaje
    };
  }

  return { etiqueta: 'Sin datos', porcentaje: 0 };
});

const tiempoCostoPromedio = computed<{
  tiempoStr: string;
  costoStr: string;
  displayStr: string;
  subtext: string;
}>(() => {
  if (!props.matrizOd || props.matrizOd.length === 0) {
    if (modoPredominanteInfo.value.etiqueta !== 'Sin datos') {
      return {
        tiempoStr: 'N/D',
        costoStr: 'N/D',
        displayStr: modoPredominanteInfo.value.etiqueta,
        subtext: `${modoPredominanteInfo.value.porcentaje.toFixed(1)}% modo predominante`
      };
    }
    return {
      tiempoStr: 'N/D',
      costoStr: 'N/D',
      displayStr: 'Sin datos',
      subtext: 'Sin trayectos reportados'
    };
  }

  let totalViajesPond = 0;
  let sumTiempo = 0;
  let countTiempo = 0;
  let sumCosto = 0;
  let countCosto = 0;

  for (const it of props.matrizOd) {
    const v = it.total_viajes;
    if (v > 0) {
      totalViajesPond += v;
      if (it.tiempo_promedio_min !== null && it.tiempo_promedio_min !== undefined) {
        sumTiempo += it.tiempo_promedio_min * v;
        countTiempo += v;
      }
      if (it.costo_promedio_bs !== null && it.costo_promedio_bs !== undefined) {
        sumCosto += it.costo_promedio_bs * v;
        countCosto += v;
      }
    }
  }

  const tProm = countTiempo > 0 ? sumTiempo / countTiempo : null;
  const cProm = countCosto > 0 ? sumCosto / countCosto : null;

  const tStr = tProm !== null ? `${tProm.toFixed(1)} min` : 'N/D';
  const cStr = cProm !== null ? `${cProm.toFixed(1)} Bs` : 'N/D';

  let display = 'Sin datos';
  if (tProm !== null && cProm !== null) {
    display = `${tStr} / ${cStr}`;
  } else if (tProm !== null) {
    display = tStr;
  } else if (cProm !== null) {
    display = cStr;
  }

  return {
    tiempoStr: tStr,
    costoStr: cStr,
    displayStr: display,
    subtext: totalViajesPond > 0 ? `${totalViajesPond.toLocaleString('es-VE')} viajes analizados` : 'Promedio ponderado'
  };
});
</script>

<template>
  <section
    class="kpi-cards-grid"
    aria-label="Indicadores clave de rendimiento del levantamiento"
  >
    <!-- Tarjeta 1: Total de Encuestas -->
    <article
      class="kpi-card"
      tabindex="0"
      aria-labelledby="kpi-encuestas-title"
      data-kpi="total_encuestas"
    >
      <div class="kpi-header">
        <span id="kpi-encuestas-title" class="kpi-title">Total de Encuestas</span>
        <div class="kpi-icon-wrap icon-encuestas" aria-hidden="true">
          <i class="pi pi-file-edit"></i>
        </div>
      </div>

      <div v-if="loading" class="kpi-skeleton-wrap" aria-busy="true">
        <div class="skeleton-line skeleton-value"></div>
        <div class="skeleton-line skeleton-sub"></div>
        <span class="sr-only">Cargando total de encuestas...</span>
      </div>
      <div v-else class="kpi-body">
        <span class="kpi-value">{{ totalEncuestas.toLocaleString('es-VE') }}</span>
        <span class="kpi-subtitle">
          <i class="pi pi-check-circle subtitle-icon" aria-hidden="true"></i>
          {{ totalResidentes > 0 ? `${totalResidentes.toLocaleString('es-VE')} residentes censados` : 'Respuestas validadas' }}
        </span>
      </div>
    </article>

    <!-- Tarjeta 2: Parroquia con Mayor Participación / % Completitud Estimada -->
    <article
      class="kpi-card"
      tabindex="0"
      aria-labelledby="kpi-parroquia-title"
      data-kpi="completitud_estimada"
    >
      <div class="kpi-header">
        <span id="kpi-parroquia-title" class="kpi-title">Parroquia con Mayor Participación</span>
        <div class="kpi-icon-wrap icon-parroquia" aria-hidden="true">
          <i class="pi pi-map-marker"></i>
        </div>
      </div>

      <div v-if="loading" class="kpi-skeleton-wrap" aria-busy="true">
        <div class="skeleton-line skeleton-value"></div>
        <div class="skeleton-line skeleton-sub"></div>
        <span class="sr-only">Cargando parroquia con mayor participación...</span>
      </div>
      <div v-else class="kpi-body">
        <span class="kpi-value text-accent" :title="parroquiaLiderInfo.nombre">
          {{ parroquiaLiderInfo.nombre }}
        </span>
        <span class="kpi-subtitle">
          <span class="kpi-badge badge-blue">
            {{ parroquiaLiderInfo.porcentaje.toFixed(1) }}%
          </span>
          del total de respuestas • Cobertura: {{ completitudEstimada.porcentaje.toFixed(1) }}%
        </span>
      </div>
    </article>

    <!-- Tarjeta 3: Total de Viajes Registrados -->
    <article
      class="kpi-card"
      tabindex="0"
      aria-labelledby="kpi-viajes-title"
      data-kpi="total_viajes"
    >
      <div class="kpi-header">
        <span id="kpi-viajes-title" class="kpi-title">Total de Viajes Registrados</span>
        <div class="kpi-icon-wrap icon-viajes" aria-hidden="true">
          <i class="pi pi-send"></i>
        </div>
      </div>

      <div v-if="loading" class="kpi-skeleton-wrap" aria-busy="true">
        <div class="skeleton-line skeleton-value"></div>
        <div class="skeleton-line skeleton-sub"></div>
        <span class="sr-only">Cargando total de viajes...</span>
      </div>
      <div v-else class="kpi-body">
        <span class="kpi-value">{{ totalViajes.toLocaleString('es-VE') }}</span>
        <span class="kpi-subtitle">
          <i class="pi pi-directions subtitle-icon" aria-hidden="true"></i>
          Trayectos urbanos e interurbanos
        </span>
      </div>
    </article>

    <!-- Tarjeta 4: Modo Predominante / Tiempo y Costo Promedio -->
    <article
      class="kpi-card"
      tabindex="0"
      aria-labelledby="kpi-modo-title"
      data-kpi="tiempo_costo_promedio"
    >
      <div class="kpi-header">
        <span id="kpi-modo-title" class="kpi-title">Modo Predominante</span>
        <div class="kpi-icon-wrap icon-modo" aria-hidden="true">
          <i class="pi pi-ticket"></i>
        </div>
      </div>

      <div v-if="loading" class="kpi-skeleton-wrap" aria-busy="true">
        <div class="skeleton-line skeleton-value"></div>
        <div class="skeleton-line skeleton-sub"></div>
        <span class="sr-only">Cargando modo predominante...</span>
      </div>
      <div v-else class="kpi-body">
        <span class="kpi-value text-accent" :title="modoPredominanteInfo.etiqueta">
          {{ modoPredominanteInfo.etiqueta }}
        </span>
        <span class="kpi-subtitle">
          <span class="kpi-badge badge-amber">
            {{ modoPredominanteInfo.porcentaje.toFixed(1) }}%
          </span>
          del reparto modal • Promedio: {{ tiempoCostoPromedio.displayStr }}
        </span>
      </div>
    </article>
  </section>
</template>

<style scoped>
.kpi-cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: var(--spacing-16);
  width: 100%;
}

.kpi-card {
  background-color: var(--surface-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-cards);
  padding: var(--spacing-20);
  box-shadow: var(--shadow-card);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: var(--spacing-12);
  transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
  min-height: 140px;
  min-block-size: var(--min-touch-target);
  color: var(--text-color);
}

.kpi-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-sm-2);
  border-color: var(--color-cobalt-glow);
}

.kpi-card:focus-visible {
  outline: 2px solid var(--primary-color);
  outline-offset: 2px;
}

.kpi-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--spacing-8);
  min-height: var(--min-touch-target);
  min-block-size: var(--min-touch-target);
}

.kpi-title {
  font-size: var(--text-body-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-color);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.kpi-icon-wrap {
  width: 48px;
  height: 48px;
  min-width: var(--min-touch-target);
  min-height: var(--min-touch-target);
  min-block-size: var(--min-touch-target);
  border-radius: var(--radius-cards);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  flex-shrink: 0;
}

.icon-encuestas {
  background-color: var(--color-lavender-wash);
  color: var(--primary-color);
}

.icon-parroquia {
  background-color: #e0f2fe;
  color: #0284c7;
}

.icon-viajes {
  background-color: #dcfce7;
  color: var(--color-mint-win);
}

.icon-modo {
  background-color: #fef3c7;
  color: #d97706;
}

.kpi-body {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-6);
}

.kpi-value {
  font-size: 1.75rem;
  font-weight: var(--font-weight-bold);
  color: var(--text-color);
  line-height: 1.2;
  word-break: break-word;
}

.kpi-value.text-accent {
  font-size: 1.35rem;
  line-height: 1.3;
}

.kpi-subtitle {
  font-size: var(--text-caption);
  color: var(--text-helper);
  display: flex;
  align-items: center;
  gap: var(--spacing-6);
  flex-wrap: wrap;
}

.subtitle-icon {
  font-size: 0.85rem;
  color: var(--color-mint-win);
}

.kpi-badge {
  font-size: 0.75rem;
  font-weight: var(--font-weight-bold);
  padding: 2px 6px;
  border-radius: var(--radius-pills);
}

.badge-blue {
  background-color: var(--color-lavender-wash);
  color: var(--primary-color);
}

.badge-amber {
  background-color: #fef3c7;
  color: #b45309;
}

/* Skeleton Loading */
.kpi-skeleton-wrap {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-8);
  padding: var(--spacing-4) 0;
}

.skeleton-line {
  background: linear-gradient(
    90deg,
    var(--surface-subtle) 25%,
    var(--border-color) 50%,
    var(--surface-subtle) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
}

.skeleton-value {
  height: 28px;
  width: 60%;
}

.skeleton-sub {
  height: 14px;
  width: 80%;
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
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
  border: 0;
}
</style>
