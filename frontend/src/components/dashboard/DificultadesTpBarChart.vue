<script setup lang="ts">
import { ref, shallowRef, onMounted, onBeforeUnmount, watch } from 'vue';
import * as echarts from 'echarts';
import type { EChartsSeriesData } from '@/services/analyticsApi';

const props = withDefaults(
  defineProps<{
    data?: EChartsSeriesData | null;
    loading?: boolean;
    titulo?: string;
  }>(),
  {
    data: null,
    loading: false,
    titulo: 'Principales Dificultades en Transporte Público'
  }
);

const chartContainer = ref<HTMLElement | null>(null);
const chartInstance = shallowRef<echarts.ECharts | null>(null);
let resizeObserver: ResizeObserver | null = null;

const LABELS_MAP: Record<string, string> = {
  frecuencia_baja: 'Frecuencia baja',
  sobrecupo: 'Sobrecupo / Aglomeración',
  falta_de_rutas: 'Falta de rutas',
  inseguridad: 'Inseguridad en paradas/unidades',
  costo: 'Costo del pasaje',
  mal_estado: 'Mal estado de unidades',
  otro: 'Otros motivos',
  'Sin respuesta': 'Sin respuesta'
};

function formatLabel(val: string): string {
  return LABELS_MAP[val] || val.replace(/_/g, ' ');
}

function updateChart() {
  if (!chartInstance.value) return;

  const rawLabels = props.data?.labels || [];
  const rawValues = props.data?.values || [];

  // Filtrar entradas con valor > 0
  const items = rawLabels
    .map((lbl, idx) => ({
      raw: lbl,
      label: formatLabel(lbl),
      value: rawValues[idx] || 0
    }))
    .filter((it) => it.value > 0);

  // Ordenar ascendente para que la barra más larga quede arriba en eje Y inverso
  items.sort((a, b) => a.value - b.value);

  if (items.length === 0) {
    chartInstance.value.clear();
    chartInstance.value.setOption({
      title: {
        text: props.titulo,
        subtext: 'No hay respuestas registradas para este indicador',
        left: 'center',
        top: 'middle',
        textStyle: {
          fontFamily: 'Inter, sans-serif',
          fontSize: 15,
          color: '#6b7280'
        },
        subtextStyle: {
          fontSize: 13,
          color: '#9ca3af'
        }
      }
    });
    return;
  }

  const option: echarts.EChartsOption = {
    title: {
      text: props.titulo,
      subtext: 'Pregunta: 5.- Si marcó Sí, indique la principal dificultad:',
      left: 'left',
      textStyle: {
        fontFamily: 'Inter, sans-serif',
        fontSize: 15,
        fontWeight: 'bold',
        color: '#020520'
      },
      subtextStyle: {
        fontFamily: 'Inter, sans-serif',
        fontSize: 12,
        color: '#64748b'
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params: any) => {
        const p = Array.isArray(params) ? params[0] : params;
        return `<strong>${p.name}</strong><br/>Menciones: <strong>${p.value}</strong>`;
      }
    },
    grid: {
      left: '4%',
      right: '8%',
      bottom: '5%',
      top: '20%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      minInterval: 1,
      axisLabel: {
        color: '#64748b',
        fontFamily: 'Inter, sans-serif'
      },
      splitLine: {
        lineStyle: {
          color: '#e2e8f0',
          type: 'dashed'
        }
      }
    },
    yAxis: {
      type: 'category',
      data: items.map((it) => it.label),
      axisLabel: {
        color: '#1e293b',
        fontFamily: 'Inter, sans-serif',
        fontSize: 12,
        width: 140,
        overflow: 'truncate'
      },
      axisTick: { show: false }
    },
    series: [
      {
        name: 'Respuestas',
        type: 'bar',
        data: items.map((it) => it.value),
        itemStyle: {
          color: '#f97316',
          borderRadius: [0, 6, 6, 0]
        },
        label: {
          show: true,
          position: 'right',
          fontFamily: 'Inter, sans-serif',
          fontWeight: 'bold',
          color: '#334155'
        }
      }
    ]
  };

  try {
    chartInstance.value.setOption(option, true);
  } catch (err) {
    console.warn('ECharts DificultadesTpBarChart setOption warning:', err);
  }
}

onMounted(() => {
  if (chartContainer.value) {
    try {
      chartInstance.value = echarts.init(chartContainer.value);
      updateChart();

      if (typeof ResizeObserver !== 'undefined') {
        resizeObserver = new ResizeObserver(() => {
          chartInstance.value?.resize();
        });
        resizeObserver.observe(chartContainer.value);
      }
    } catch (err) {
      console.warn('ECharts DificultadesTpBarChart init warning:', err);
    }
  }
});

onBeforeUnmount(() => {
  if (resizeObserver) {
    resizeObserver.disconnect();
    resizeObserver = null;
  }
  if (chartInstance.value) {
    chartInstance.value.dispose();
    chartInstance.value = null;
  }
});

watch(() => props.data, () => updateChart(), { deep: true });
watch(() => props.loading, (loading) => {
  if (!chartInstance.value) return;
  if (loading) {
    if (typeof chartInstance.value.showLoading === 'function') {
      chartInstance.value.showLoading({ text: 'Cargando datos...', color: '#f97316' });
    }
  } else {
    if (typeof chartInstance.value.hideLoading === 'function') {
      chartInstance.value.hideLoading();
    }
    updateChart();
  }
});
</script>

<template>
  <div class="dificultades-chart-card survey-card">
    <div ref="chartContainer" class="chart-container" style="height: 340px; width: 100%;"></div>
  </div>
</template>

<style scoped>
.dificultades-chart-card {
  width: 100%;
  padding: var(--spacing-16);
  background-color: var(--surface-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-containers);
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
}

.chart-container {
  min-height: 320px;
}
</style>

