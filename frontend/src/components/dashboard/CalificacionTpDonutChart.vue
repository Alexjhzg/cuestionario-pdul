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
    titulo: 'Evaluación del Transporte Público'
  }
);

const LABELS_MAP: Record<string, string> = {
  muy_bueno: 'Muy Bueno',
  bueno: 'Bueno',
  regular: 'Regular',
  malo: 'Malo',
  pesimo: 'Pésimo',
  muy_malo: 'Muy Malo',
  'Sin respuesta': 'Sin respuesta'
};

const COLOR_MAP: Record<string, string> = {
  muy_bueno: '#16ca2e',
  bueno: '#3b82f6',
  regular: '#ffa64d',
  malo: '#f26052',
  pesimo: '#b91c1c',
  muy_malo: '#b91c1c',
  'Sin respuesta': '#9ca3af'
};

function formatLabel(raw: string): string {
  return LABELS_MAP[raw] || raw.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
}

const chartOption = computed<echarts.EChartsOption>(() => {
  const rawLabels = props.data?.labels || [];
  const rawValues = props.data?.values || [];

  const pieData = rawLabels
    .map((lbl, idx) => ({
      name: formatLabel(lbl),
      value: rawValues[idx] || 0,
      itemStyle: { color: COLOR_MAP[lbl] || '#64748b' }
    }))
    .filter((item) => item.value > 0);

  if (pieData.length === 0) {
    return {
      title: {
        text: props.titulo,
        subtext: 'No se registran datos suficientes en esta consulta',
        left: 'center',
        top: 'middle',
        textStyle: { fontFamily: CHART_FONT_FAMILY, fontSize: 16, color: '#6b7280' },
        subtextStyle: { fontSize: 13, color: '#9ca3af' }
      }
    };
  }

  return {
    title: {
      text: props.titulo,
      subtext: 'Pregunta: 6.- ¿Considera que el servicio de transporte público es:',
      left: 'left',
      textStyle: { fontFamily: CHART_FONT_FAMILY, fontSize: 16, fontWeight: 600, color: '#111827' },
      subtextStyle: { fontSize: 12, color: '#6b7280' }
    },
    tooltip: { trigger: 'item', formatter: '{b}: <b>{c}</b> ({d}%)' },
    legend: {
      orient: 'horizontal',
      bottom: '1%',
      left: 'center',
      textStyle: { fontFamily: CHART_FONT_FAMILY, fontSize: 11, color: '#374151' }
    },
    series: [
      {
        name: 'Evaluación',
        type: 'pie',
        radius: ['36%', '58%'],
        center: ['50%', '57%'],
        avoidLabelOverlap: true,
        itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
        label: { show: false, position: 'center' },
        emphasis: {
          label: { show: true, fontSize: 16, fontWeight: 'bold', formatter: '{b}\n{d}%' }
        },
        labelLine: { show: false },
        data: pieData
      }
    ]
  };
});
</script>

<template>
  <div class="calificacion-chart-card survey-card">
    <BaseChart
      :option="chartOption"
      :loading="loading"
      height="380px"
      canvas-class="chart-container"
      label="CalificacionTpDonutChart"
    />
  </div>
</template>

<style scoped>
.calificacion-chart-card {
  width: 100%;
  padding: var(--spacing-16);
  background-color: var(--surface-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-containers);
}
</style>
