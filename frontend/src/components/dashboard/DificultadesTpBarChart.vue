<script setup lang="ts">
import { computed } from 'vue';
import type * as echarts from 'echarts';
import BaseChart from '@/components/dashboard/BaseChart.vue';
import { CHART_FONT_FAMILY } from '@/composables/useECharts';
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

const chartOption = computed<echarts.EChartsOption>(() => {
  const rawLabels = props.data?.labels || [];
  const rawValues = props.data?.values || [];

  const items = rawLabels
    .map((lbl, idx) => ({
      raw: lbl,
      label: formatLabel(lbl),
      value: rawValues[idx] || 0
    }))
    .filter((it) => it.value > 0)
    .sort((a, b) => a.value - b.value);

  if (items.length === 0) {
    return {
      title: {
        text: props.titulo,
        subtext: 'No hay respuestas registradas para este indicador',
        left: 'center',
        top: 'middle',
        textStyle: { fontFamily: CHART_FONT_FAMILY, fontSize: 15, color: '#6b7280' },
        subtextStyle: { fontSize: 13, color: '#9ca3af' }
      }
    };
  }

  return {
    title: {
      text: props.titulo,
      subtext: 'Pregunta: 5.- Si marcó Sí, indique la principal dificultad:',
      left: 'left',
      textStyle: { fontFamily: CHART_FONT_FAMILY, fontSize: 15, fontWeight: 'bold', color: '#020520' },
      subtextStyle: { fontFamily: CHART_FONT_FAMILY, fontSize: 12, color: '#64748b' }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params: any) => {
        const p = Array.isArray(params) ? params[0] : params;
        return `<strong>${p.name}</strong><br/>Menciones: <strong>${p.value}</strong>`;
      }
    },
    grid: { left: '4%', right: '8%', bottom: '5%', top: '20%', containLabel: true },
    xAxis: {
      type: 'value',
      minInterval: 1,
      axisLabel: { color: '#64748b', fontFamily: CHART_FONT_FAMILY },
      splitLine: { lineStyle: { color: '#e2e8f0', type: 'dashed' } }
    },
    yAxis: {
      type: 'category',
      data: items.map((it) => it.label),
      axisLabel: { color: '#1e293b', fontFamily: CHART_FONT_FAMILY, fontSize: 12, width: 140, overflow: 'truncate' },
      axisTick: { show: false }
    },
    series: [
      {
        name: 'Respuestas',
        type: 'bar',
        data: items.map((it) => it.value),
        itemStyle: { color: '#f97316', borderRadius: [0, 6, 6, 0] },
        label: { show: true, position: 'right', fontFamily: CHART_FONT_FAMILY, fontWeight: 'bold', color: '#334155' }
      }
    ]
  };
});
</script>

<template>
  <div class="dificultades-chart-card survey-card">
    <BaseChart
      :option="chartOption"
      :loading="loading"
      loading-color="#f97316"
      height="340px"
      canvas-class="chart-container"
      label="DificultadesTpBarChart"
    />
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
</style>
