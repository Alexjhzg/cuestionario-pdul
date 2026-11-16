<script setup lang="ts">
import { ref, shallowRef, onMounted, onBeforeUnmount, watch } from 'vue';
import * as echarts from 'echarts';
import { formatParroquia } from '@/utils/validation';
import type { ParroquiaResultado } from '@/services/analyticsApi';

const props = withDefaults(
  defineProps<{
    items?: ParroquiaResultado[];
    loading?: boolean;
    titulo?: string;
  }>(),
  {
    items: () => [],
    loading: false,
    titulo: 'Distribución de Encuestas por Parroquia'
  }
);

const chartContainer = ref<HTMLElement | null>(null);
const chartInstance = shallowRef<echarts.ECharts | null>(null);
let resizeObserver: ResizeObserver | null = null;

function updateChart() {
  if (!chartInstance.value) return;

  const validItems = props.items.filter((it) => it.total_respuestas > 0);

  if (validItems.length === 0) {
    chartInstance.value.clear();
    chartInstance.value.setOption({
      title: {
        text: props.titulo,
        subtext: 'No se registran respuestas en la encuesta seleccionada',
        left: 'center',
        top: 'middle',
        textStyle: { fontFamily: 'Inter, sans-serif', fontSize: 16, color: '#6b7280' },
        subtextStyle: { fontSize: 13, color: '#9ca3af' }
      }
    });
    return;
  }

  // Ordenar de mayor a menor para una barra horizontal clara
  const sorted = [...validItems].sort((a, b) => a.total_respuestas - b.total_respuestas);
  const categories = sorted.map((it) => formatParroquia(it.parroquia));
  const values = sorted.map((it) => it.total_respuestas);
  const percentages = sorted.map((it) => it.porcentaje);

  const option: echarts.EChartsOption = {
    title: {
      text: props.titulo,
      subtext: 'Pregunta: 1.- Parroquia (Sección I: Identificación de la Unidad Residencial)',
      left: 'left',
      textStyle: { fontFamily: 'Inter, sans-serif', fontSize: 16, fontWeight: 600, color: '#111827' },
      subtextStyle: { fontSize: 12, color: '#6b7280' }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params: any) => {
        const p = Array.isArray(params) ? params[0] : params;
        const idx = p.dataIndex;
        return `<strong>${p.name}</strong><br/>Encuestas: <b>${p.value}</b> (${percentages[idx]}%)`;
      }
    },
    grid: {
      top: 60,
      left: 10,
      right: 40,
      bottom: 20,
      containLabel: true
    },
    xAxis: {
      type: 'value',
      minInterval: 1,
      axisLabel: { color: '#6b7280' },
      splitLine: { lineStyle: { color: '#f3f4f6' } }
    },
    yAxis: {
      type: 'category',
      data: categories,
      axisLabel: { color: '#374151', fontSize: 13, fontWeight: 500 },
      axisLine: { lineStyle: { color: '#e5e7eb' } }
    },
    series: [
      {
        name: 'Encuestas',
        type: 'bar',
        data: values,
        itemStyle: {
          color: '#145aff',
          borderRadius: [0, 4, 4, 0]
        },
        label: {
          show: true,
          position: 'right',
          formatter: '{c}',
          color: '#374151',
          fontWeight: 600
        }
      }
    ]
  };

  try {
    chartInstance.value.setOption(option, true);
  } catch (err) {
    console.warn('ECharts ParroquiasBarChart setOption warning:', err);
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
      console.warn('ECharts ParroquiasBarChart init warning:', err);
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

watch(() => props.items, () => updateChart(), { deep: true });
watch(() => props.loading, (loading) => {
  if (!chartInstance.value) return;
  if (loading) {
    if (typeof chartInstance.value.showLoading === 'function') {
      chartInstance.value.showLoading({ text: 'Cargando datos...', color: '#145aff' });
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
  <div class="parroquias-chart-card survey-card">
    <div ref="chartContainer" class="chart-container" style="height: 340px; width: 100%;"></div>
  </div>
</template>

<style scoped>
.parroquias-chart-card {
  width: 100%;
  padding: var(--spacing-16);
  background-color: var(--surface-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-containers);
}
.chart-container {
  min-height: 320px;
}
</style>
