<script setup lang="ts">
import { computed } from 'vue';
import type * as echarts from 'echarts';
import BaseChart from '@/components/dashboard/BaseChart.vue';
import { CHART_FONT_FAMILY, INSTITUTIONAL_CHART_PALETTE } from '@/composables/useECharts';
import type { PreguntaMetricaItem } from '@/services/analyticsApi';

const props = withDefaults(
  defineProps<{
    item: PreguntaMetricaItem;
    loading?: boolean;
  }>(),
  {
    loading: false
  }
);

const chartOption = computed<echarts.EChartsOption>(() => {
  const rawLabels = props.item.labels || [];
  const rawValues = props.item.values || [];

  if (rawLabels.length === 0 || rawValues.length === 0 || props.item.total_respuestas === 0) {
    return {
      title: {
        text: 'Sin datos registrados',
        subtext: 'Aún no se registran respuestas para esta pregunta',
        left: 'center',
        top: 'middle',
        textStyle: { fontFamily: CHART_FONT_FAMILY, fontSize: 14, color: '#6b7280' },
        subtextStyle: { fontSize: 12, color: '#9ca3af' }
      }
    };
  }

  if (props.item.tipo_grafico === 'donut') {
    const pieData = rawLabels.map((lbl, idx) => ({
      name: lbl,
      value: rawValues[idx] || 0,
      itemStyle: { color: INSTITUTIONAL_CHART_PALETTE[idx % INSTITUTIONAL_CHART_PALETTE.length] }
    }));

    return {
      tooltip: {
        trigger: 'item',
        formatter: '{b}: <b>{c}</b> ({d}%)',
        backgroundColor: 'rgba(2, 5, 32, 0.95)',
        borderColor: '#334155',
        textStyle: { color: '#ffffff', fontSize: 13 }
      },
      legend: {
        orient: 'horizontal',
        bottom: '1%',
        left: 'center',
        type: rawLabels.length > 5 ? 'scroll' : 'plain',
        textStyle: { fontFamily: CHART_FONT_FAMILY, fontSize: 11, color: '#374151' }
      },
      toolbox: {
        show: true,
        feature: {
          saveAsImage: { title: 'Descargar Gráfico', pixelRatio: 2 },
          dataView: { title: 'Ver Datos', readOnly: true, lang: ['Datos de la Pregunta', 'Cerrar', 'Actualizar'] }
        }
      },
      series: [
        {
          name: props.item.pregunta,
          type: 'pie',
          radius: ['36%', '58%'],
          center: ['50%', '52%'],
          avoidLabelOverlap: true,
          itemStyle: { borderRadius: 6, borderColor: '#ffffff', borderWidth: 2 },
          label: { show: false, position: 'center' },
          emphasis: {
            label: { show: true, fontSize: 14, fontWeight: 'bold', formatter: '{b}\n{d}%' }
          },
          labelLine: { show: false },
          data: pieData
        }
      ]
    };
  }

  const total = props.item.total_respuestas || rawValues.reduce((a, b) => a + b, 0);
  const categories = [...rawLabels].reverse();
  const values = [...rawValues].reverse();

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(2, 5, 32, 0.95)',
      borderColor: '#334155',
      textStyle: { color: '#ffffff', fontSize: 13 },
      formatter: (params: any) => {
        const p = Array.isArray(params) ? params[0] : params;
        const val = Number(p.value) || 0;
        const pct = total > 0 ? ((val / total) * 100).toFixed(1) : '0';
        return `<strong>${p.name}</strong><br/>Menciones: <b>${val}</b> (${pct}%)`;
      }
    },
    toolbox: {
      show: true,
      feature: {
        saveAsImage: { title: 'Descargar Gráfico', pixelRatio: 2 },
        dataView: { title: 'Ver Datos', readOnly: true, lang: ['Datos de la Pregunta', 'Cerrar', 'Actualizar'] }
      }
    },
    grid: { top: 25, left: 10, right: 45, bottom: 15, containLabel: true },
    xAxis: {
      type: 'value',
      minInterval: 1,
      axisLabel: { color: '#6b7280', fontFamily: CHART_FONT_FAMILY, fontSize: 11 },
      splitLine: { lineStyle: { color: '#f3f4f6', type: 'dashed' } }
    },
    yAxis: {
      type: 'category',
      data: categories,
      axisLabel: {
        color: '#374151',
        fontSize: 11,
        fontWeight: 500,
        fontFamily: CHART_FONT_FAMILY,
        formatter: (value: string) => (value.length > 25 ? value.slice(0, 23) + '...' : value)
      },
      axisLine: { lineStyle: { color: '#e5e7eb' } }
    },
    series: [
      {
        name: props.item.pregunta,
        type: 'bar',
        data: values,
        itemStyle: { color: '#145aff', borderRadius: [0, 4, 4, 0] },
        label: { show: true, position: 'right', formatter: '{c}', color: '#374151', fontWeight: 600, fontSize: 11 }
      }
    ]
  };
});
</script>

<template>
  <div
    class="question-chart-card survey-card"
    role="region"
    :aria-label="`Gráfico estadístico para: ${item.pregunta}`"
  >
    <div class="question-header">
      <div class="header-badges">
        <span class="section-tag">
          <i class="pi pi-bookmark" aria-hidden="true"></i>
          {{ item.seccion }}
        </span>
        <span class="total-tag">
          <i class="pi pi-users" aria-hidden="true"></i>
          {{ item.total_respuestas }} respuestas
        </span>
      </div>
      <h3 class="question-title">{{ item.pregunta }}</h3>
    </div>

    <BaseChart
      :option="chartOption"
      :loading="loading"
      height="340px"
      :clear-before-set="item.total_respuestas === 0"
      :label="`QuestionChartCard(${item.clave})`"
    />
  </div>
</template>

<style scoped>
.question-chart-card {
  width: 100%;
  padding: var(--spacing-16);
  background-color: var(--surface-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-containers);
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-12);
  transition: transform var(--transition-base), box-shadow var(--transition-base);
}

.question-chart-card:hover {
  box-shadow: var(--shadow-md);
}

.question-header {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-6);
  border-bottom: 1px solid var(--border-color);
  padding-bottom: var(--spacing-10);
}

.header-badges {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-8);
  flex-wrap: wrap;
}

.section-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.72rem;
  font-weight: var(--font-weight-bold);
  color: var(--color-royal-signal);
  background-color: var(--color-lavender-wash);
  padding: 2px 8px;
  border-radius: var(--radius-pills);
  text-transform: uppercase;
  letter-spacing: 0.4px;
}

.total-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.72rem;
  font-weight: var(--font-weight-medium);
  color: var(--text-muted);
  background-color: var(--surface-ground);
  padding: 2px 8px;
  border-radius: var(--radius-pills);
}

.question-title {
  font-size: 0.95rem;
  font-weight: var(--font-weight-bold);
  color: var(--color-midnight-ink);
  line-height: 1.35;
  margin: 0;
}
</style>
