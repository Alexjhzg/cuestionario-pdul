<script setup lang="ts">
import { computed } from 'vue';
import type * as echarts from 'echarts';
import BaseChart from '@/components/dashboard/BaseChart.vue';
import { CHART_FONT_FAMILY } from '@/composables/useECharts';
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

const chartOption = computed<echarts.EChartsOption>(() => {
  const validItems = props.items.filter((it) => it.total_respuestas > 0);
  if (validItems.length === 0) {
    return {
      title: {
        text: props.titulo,
        subtext: 'No se registran respuestas en la encuesta seleccionada',
        left: 'center',
        top: 'middle',
        textStyle: { fontFamily: CHART_FONT_FAMILY, fontSize: 16, color: '#6b7280' },
        subtextStyle: { fontSize: 13, color: '#9ca3af' }
      }
    };
  }

  const sorted = [...validItems].sort((a, b) => a.total_respuestas - b.total_respuestas);
  const categories = sorted.map((it) => formatParroquia(it.parroquia));
  const values = sorted.map((it) => it.total_respuestas);
  const percentages = sorted.map((it) => it.porcentaje);

  return {
    title: {
      text: props.titulo,
      subtext: 'Pregunta: 1.- Parroquia (Sección I: Identificación de la Unidad Residencial)',
      left: 'left',
      textStyle: { fontFamily: CHART_FONT_FAMILY, fontSize: 16, fontWeight: 600, color: '#111827' },
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
    grid: { top: 60, left: 10, right: 40, bottom: 20, containLabel: true },
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
        itemStyle: { color: '#145aff', borderRadius: [0, 4, 4, 0] },
        label: { show: true, position: 'right', formatter: '{c}', color: '#374151', fontWeight: 600 }
      }
    ]
  };
});
</script>

<template>
  <div class="parroquias-chart-card survey-card">
    <BaseChart
      :option="chartOption"
      :loading="loading"
      height="340px"
      canvas-class="chart-container"
      label="ParroquiasBarChart"
    />
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
</style>
