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
    titulo: 'Percepción de Seguridad en el Centro'
  }
);

const chartContainer = ref<HTMLElement | null>(null);
const chartInstance = shallowRef<echarts.ECharts | null>(null);
let resizeObserver: ResizeObserver | null = null;

const COLOR_MAP: Record<string, string> = {
  muy_seguro: '#16ca2e', // Mint Win / Verde
  seguro: '#3b82f6',     // Cobalt Glow / Azul
  neutral: '#ffa64d',    // Amber Pending / Ámbar
  inseguro: '#f97316',   // Coral Orange
  muy_inseguro: '#ef4444', // Red Danger
  'Sin respuesta': '#94a3b8' // Slate
};

const LABELS_MAP: Record<string, string> = {
  muy_seguro: 'Muy seguro(a)',
  seguro: 'Seguro(a)',
  neutral: 'Ni seguro ni inseguro',
  inseguro: 'Inseguro(a)',
  muy_inseguro: 'Muy inseguro(a)',
  'Sin respuesta': 'Sin especificar'
};

function formatLabel(val: string): string {
  return LABELS_MAP[val] || val.replace(/_/g, ' ');
}

function updateChart() {
  if (!chartInstance.value) return;

  const rawLabels = props.data?.labels || [];
  const rawValues = props.data?.values || [];

  const pieData = rawLabels
    .map((lbl, idx) => ({
      name: formatLabel(lbl),
      value: rawValues[idx] || 0,
      itemStyle: {
        color: COLOR_MAP[lbl] || '#64748b'
      }
    }))
    .filter((it) => it.value > 0);

  if (pieData.length === 0) {
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
      subtext: 'Pregunta: 8.- ¿Se siente seguro al desplazarse por el centro de la ciudad?',
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
      trigger: 'item',
      formatter: '{b}: <strong>{c}</strong> ({d}%)'
    },
    legend: {
      orient: 'horizontal',
      bottom: '1%',
      left: 'center',
      textStyle: {
        fontFamily: 'Inter, sans-serif',
        fontSize: 11,
        color: '#475569'
      }
    },
    series: [
      {
        name: 'Percepción de Seguridad',
        type: 'pie',
        radius: ['36%', '58%'],
        center: ['50%', '57%'],
        avoidLabelOverlap: true,
        itemStyle: {
          borderRadius: 6,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 15,
            fontWeight: 'bold',
            formatter: '{b}\n{d}%'
          }
        },
        labelLine: { show: false },
        data: pieData
      }
    ]
  };

  try {
    chartInstance.value.setOption(option, true);
  } catch (err) {
    console.warn('ECharts SeguridadCentroDonutChart setOption warning:', err);
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
      console.warn('ECharts SeguridadCentroDonutChart init warning:', err);
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
      chartInstance.value.showLoading({ text: 'Cargando datos...', color: '#16ca2e' });
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
  <div class="seguridad-chart-card survey-card">
    <div ref="chartContainer" class="chart-container" style="height: 380px; width: 100%;"></div>
  </div>
</template>

<style scoped>
.seguridad-chart-card {
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

