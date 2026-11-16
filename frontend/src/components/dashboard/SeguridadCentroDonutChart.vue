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
    titulo: 'Percepción de Seguridad en el Centro'
  }
);

const COLOR_MAP: Record<string, string> = {
  muy_seguro: '#16ca2e',
  seguro: '#3b82f6',
  neutral: '#ffa64d',
  inseguro: '#f97316',
  muy_inseguro: '#ef4444',
  'Sin respuesta': '#94a3b8'
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

const chartOption = computed<echarts.EChartsOption>(() => {
  const rawLabels = props.data?.labels || [];
  const rawValues = props.data?.values || [];

  const pieData = rawLabels
    .map((lbl, idx) => ({
      name: formatLabel(lbl),
      value: rawValues[idx] || 0,
      itemStyle: { color: COLOR_MAP[lbl] || '#64748b' }
    }))
    .filter((it) => it.value > 0);

  if (pieData.length === 0) {
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
      subtext: 'Pregunta: 8.- ¿Se siente seguro al desplazarse por el centro de la ciudad?',
      left: 'left',
      textStyle: { fontFamily: CHART_FONT_FAMILY, fontSize: 15, fontWeight: 'bold', color: '#020520' },
      subtextStyle: { fontFamily: CHART_FONT_FAMILY, fontSize: 12, color: '#64748b' }
    },
    tooltip: { trigger: 'item', formatter: '{b}: <strong>{c}</strong> ({d}%)' },
    legend: {
      orient: 'horizontal',
      bottom: '1%',
      left: 'center',
      textStyle: { fontFamily: CHART_FONT_FAMILY, fontSize: 11, color: '#475569' }
    },
    series: [
      {
        name: 'Percepción de Seguridad',
        type: 'pie',
        radius: ['36%', '58%'],
        center: ['50%', '57%'],
        avoidLabelOverlap: true,
        itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
        label: { show: false, position: 'center' },
        emphasis: {
          label: { show: true, fontSize: 15, fontWeight: 'bold', formatter: '{b}\n{d}%' }
        },
        labelLine: { show: false },
        data: pieData
      }
    ]
  };
});
</script>

<template>
  <div class="seguridad-chart-card survey-card">
    <BaseChart
      :option="chartOption"
      :loading="loading"
      loading-color="#16ca2e"
      height="380px"
      canvas-class="chart-container"
      label="SeguridadCentroDonutChart"
    />
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
</style>
