<script setup lang="ts">
import { computed, ref } from 'vue';
import type * as echarts from 'echarts';
import BaseChart from '@/components/dashboard/BaseChart.vue';
import { CHART_FONT_FAMILY } from '@/composables/useECharts';
import { PARROQUIA_CANONICAL_LABELS } from '@/utils/validation';
import type { MatrizODItem } from '@/services/analyticsApi';

const props = withDefaults(
  defineProps<{
    items?: MatrizODItem[];
    loading?: boolean;
    titulo?: string;
  }>(),
  {
    items: () => [],
    loading: false,
    titulo: 'Matriz de Interacción de Viajes Origen – Destino'
  }
);

const baseChartRef = ref<InstanceType<typeof BaseChart> | null>(null);
const chartInstance = computed(() => baseChartRef.value?.chartInstance ?? null);

function formatZone(code: string): string {
  return PARROQUIA_CANONICAL_LABELS[code] || code;
}

const validItems = computed(() => props.items.filter((it) => it.total_viajes > 0));
const isEmpty = computed(() => validItems.value.length === 0);

const chartOption = computed<echarts.EChartsOption>(() => {
  if (isEmpty.value) {
    return {
      title: {
        text: props.titulo,
        subtext: 'No se registran viajes para generar la matriz Origen-Destino',
        left: 'center',
        top: 'middle',
        textStyle: {
          fontFamily: CHART_FONT_FAMILY,
          fontSize: 16,
          color: '#6b7280'
        },
        subtextStyle: {
          fontSize: 13,
          color: '#9ca3af'
        }
      }
    };
  }

  // Obtener zonas únicas presentes en los datos
  const originsSet = new Set<string>();
  const destsSet = new Set<string>();

  validItems.value.forEach((it) => {
    originsSet.add(it.zona_origen);
    destsSet.add(it.zona_destino);
  });

  const origins = Array.from(originsSet);
  const dests = Array.from(destsSet);

  const xLabels = dests.map(formatZone);
  const yLabels = origins.map(formatZone);

  // Mapa rápido de búsqueda
  const lookup = new Map<string, MatrizODItem>();
  let maxTrips = 1;

  validItems.value.forEach((it) => {
    lookup.set(`${it.zona_origen}__${it.zona_destino}`, it);
    if (it.total_viajes > maxTrips) {
      maxTrips = it.total_viajes;
    }
  });

  const matrixData: Array<[number, number, number, number | null, number | null]> = [];

  origins.forEach((orig, yIdx) => {
    dests.forEach((dest, xIdx) => {
      const match = lookup.get(`${orig}__${dest}`);
      const val = match?.total_viajes ?? 0;
      const tiempo = match?.tiempo_promedio_min ?? null;
      const costo = match?.costo_promedio_bs ?? null;
      matrixData.push([xIdx, yIdx, val, tiempo, costo]);
    });
  });

  return {
    title: {
      text: props.titulo,
      subtext: 'Pregunta: Zona O-D origen → Zona O-D destino (Sección V: Registro de Viajes)',
      left: 'left',
      textStyle: {
        fontFamily: CHART_FONT_FAMILY,
        fontSize: 16,
        fontWeight: 'bold',
        color: '#020520'
      },
      subtextStyle: {
        fontSize: 12,
        color: '#6b7280'
      }
    },
    tooltip: {
      position: 'top',
      backgroundColor: 'rgba(2, 5, 32, 0.95)',
      borderColor: '#334155',
      textStyle: { color: '#ffffff', fontSize: 13 },
      formatter: (params: any) => {
        const [xIdx, yIdx, val, tiempo, costo] = params.data;
        const orig = yLabels[yIdx];
        const dest = xLabels[xIdx];
        let html = `<strong>${orig} &rarr; ${dest}</strong><br/>`;
        html += `Total de viajes: <strong>${val}</strong>`;
        if (tiempo !== null && tiempo !== undefined) {
          html += `<br/>Tiempo promedio: <strong>${tiempo} min</strong>`;
        }
        if (costo !== null && costo !== undefined) {
          html += `<br/>Costo promedio: <strong>${costo} Bs</strong>`;
        }
        return html;
      }
    },
    grid: {
      top: '18%',
      bottom: '16%',
      left: '12%',
      right: '6%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: xLabels,
      name: 'Zona Destino',
      nameLocation: 'middle',
      nameGap: 36,
      splitArea: { show: true },
      axisLabel: {
        rotate: 30,
        interval: 0,
        fontSize: 11
      }
    },
    yAxis: {
      type: 'category',
      data: yLabels,
      name: 'Zona Origen',
      nameLocation: 'middle',
      nameGap: 60,
      splitArea: { show: true },
      axisLabel: {
        fontSize: 11
      }
    },
    visualMap: {
      min: 0,
      max: maxTrips,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: '0%',
      inRange: {
        color: ['#f0f4fe', '#93c5fd', '#3b82f6', '#145aff', '#020520']
      },
      text: ['Alto', 'Bajo'],
      textStyle: {
        color: '#374151'
      }
    },
    toolbox: {
      show: true,
      feature: {
        saveAsImage: {
          title: 'Descargar Matriz O-D',
          pixelRatio: 2
        },
        dataView: {
          title: 'Ver Datos',
          readOnly: true,
          lang: ['Vista de Datos - Matriz Origen-Destino', 'Cerrar', 'Actualizar']
        }
      }
    },
    series: [
      {
        name: 'Viajes O-D',
        type: 'heatmap',
        data: matrixData,
        label: {
          show: true,
          formatter: (p: any) => {
            const v = p.data[2];
            return v > 0 ? String(v) : '';
          },
          fontSize: 11,
          color: '#ffffff'
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  };
});

function resize() {
  baseChartRef.value?.resize();
}

defineExpose({
  chartInstance,
  resize
});
</script>

<template>
  <div
    class="matrix-card"
    role="region"
    aria-label="Matriz de flujos de viajes Origen y Destino"
  >
    <div v-if="loading" class="chart-loading-overlay" aria-live="polite">
      <i class="pi pi-spin pi-spinner" aria-hidden="true"></i>
      <span>Cargando matriz O-D...</span>
    </div>

    <BaseChart
      ref="baseChartRef"
      :option="chartOption"
      :clear-before-set="isEmpty"
      height="440px"
      canvas-class="echarts-matrix-container"
      role="img"
      aria-label="Mapa de calor que representa la cantidad de viajes entre cada par de zonas de origen y destino"
      :tabindex="0"
      label="OdFlowMatrixChart"
    />
  </div>
</template>

<style scoped>
.matrix-card {
  background-color: var(--surface-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-cards);
  box-shadow: var(--shadow-card);
  padding: var(--spacing-20);
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
  min-height: 480px;
}

.echarts-matrix-container {
  width: 100%;
  height: 440px;
}

.echarts-matrix-container:focus-visible {
  outline: 2px solid var(--focus-ring);
  outline-offset: -2px;
}

.chart-loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-8);
  font-size: var(--text-body-sm);
  color: var(--color-royal-signal);
  font-weight: var(--font-weight-medium);
  z-index: 10;
}
</style>
