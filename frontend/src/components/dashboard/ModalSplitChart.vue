<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import type * as echarts from 'echarts';
import BaseChart from '@/components/dashboard/BaseChart.vue';
import { CHART_FONT_FAMILY } from '@/composables/useECharts';
import type { RepartoModalItem } from '@/services/analyticsApi';

const props = withDefaults(
  defineProps<{
    items?: RepartoModalItem[];
    loading?: boolean;
    titulo?: string;
    tipoGrafico?: 'donut' | 'bar';
  }>(),
  {
    items: () => [],
    loading: false,
    titulo: 'Reparto Modal de Viajes',
    tipoGrafico: 'donut'
  }
);

const activeType = ref<'donut' | 'bar'>(props.tipoGrafico);
const baseChartRef = ref<InstanceType<typeof BaseChart> | null>(null);
const chartInstance = computed(() => baseChartRef.value?.chartInstance ?? null);

const PALETA_MODAL = [
  '#145aff', // Royal Signal
  '#3b82f6', // Cobalt Glow
  '#16ca2e', // Mint Win
  '#ffa64d', // Amber Pending
  '#f26052', // Coral Lost
  '#8b5cf6', // Violet
  '#06b6d4', // Cyan
  '#64748b'  // Slate
];

function setChartType(type: 'donut' | 'bar') {
  activeType.value = type;
}

const validItems = computed(() => props.items.filter((it) => it.total_viajes > 0));
const isEmpty = computed(() => validItems.value.length === 0);

const chartOption = computed<echarts.EChartsOption>(() => {
  if (isEmpty.value) {
    return {
      title: {
        text: props.titulo,
        subtext: 'No se registran viajes en la encuesta seleccionada',
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

  const isBar = activeType.value === 'bar';

  const baseOption: echarts.EChartsOption = {
    title: {
      text: props.titulo,
      subtext: 'Pregunta: Modo principal (Sección V: Registro de Viajes)',
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
    tooltip: isBar
      ? {
          trigger: 'axis',
          axisPointer: { type: 'shadow' },
          backgroundColor: 'rgba(2, 5, 32, 0.95)',
          borderColor: '#334155',
          textStyle: { color: '#ffffff', fontSize: 13 },
          formatter: (params: any) => {
            const p = Array.isArray(params) ? params[0] : params;
            return `<strong>${p.name}</strong><br/>Viajes: <strong>${Number(p.value).toLocaleString('es-VE')}</strong>`;
          }
        }
      : {
          trigger: 'item',
          backgroundColor: 'rgba(2, 5, 32, 0.95)',
          borderColor: '#334155',
          textStyle: { color: '#ffffff', fontSize: 13 },
          formatter: (params: any) => {
            return `<strong>${params.name}</strong><br/>
                    Viajes: <strong>${Number(params.value).toLocaleString('es-VE')}</strong><br/>
                    Reparto: <strong>${params.percent}%</strong>`;
          }
        },
    toolbox: {
      show: true,
      feature: {
        saveAsImage: {
          title: 'Descargar Gráfico',
          pixelRatio: 2
        },
        dataView: {
          title: 'Ver Datos',
          readOnly: true,
          lang: ['Vista de Datos - Reparto Modal', 'Cerrar', 'Actualizar']
        }
      }
    },
    color: PALETA_MODAL
  };

  if (isBar) {
    baseOption.grid = {
      left: '4%',
      right: '4%',
      bottom: '12%',
      top: '20%',
      containLabel: true
    };
    baseOption.xAxis = {
      type: 'category',
      data: validItems.value.map((it) => it.etiqueta),
      axisLabel: {
        interval: 0,
        rotate: 20,
        fontSize: 11
      }
    };
    baseOption.yAxis = {
      type: 'value',
      name: 'Viajes',
      axisLabel: {
        formatter: '{value}'
      }
    };
    baseOption.series = [
      {
        name: 'Total Viajes',
        type: 'bar',
        data: validItems.value.map((it) => it.total_viajes),
        itemStyle: {
          borderRadius: [4, 4, 0, 0]
        }
      }
    ];
  } else {
    baseOption.legend = {
      orient: 'horizontal',
      bottom: '2%',
      left: 'center',
      type: 'scroll',
      textStyle: {
        color: '#374151',
        fontSize: 12
      }
    };
    baseOption.series = [
      {
        name: 'Modo de Transporte',
        type: 'pie',
        radius: ['42%', '70%'],
        center: ['50%', '52%'],
        avoidLabelOverlap: true,
        itemStyle: {
          borderRadius: 6,
          borderColor: '#ffffff',
          borderWidth: 2
        },
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 14,
            fontWeight: 'bold',
            formatter: '{b}\n{d}%',
            color: '#020520'
          }
        },
        labelLine: {
          show: false
        },
        data: validItems.value.map((it) => ({
          name: it.etiqueta,
          value: it.total_viajes
        }))
      }
    ];
  }

  return baseOption;
});

function resize() {
  baseChartRef.value?.resize();
}

watch(
  () => props.tipoGrafico,
  (newType) => {
    if (newType) {
      activeType.value = newType;
    }
  }
);

defineExpose({
  chartInstance,
  activeType,
  setChartType,
  resize
});
</script>

<template>
  <div
    class="chart-card"
    role="region"
    aria-label="Gráfico de reparto modal de transporte"
  >
    <div class="chart-header-actions">
      <div class="chart-type-toggle" role="group" aria-label="Alternar tipo de gráfico">
        <button
          type="button"
          class="toggle-btn"
          :class="{ active: activeType === 'donut' }"
          @click="setChartType('donut')"
          aria-label="Visualizar como gráfico donut"
        >
          <i class="pi pi-chart-pie" aria-hidden="true"></i>
          <span>Donut</span>
        </button>
        <button
          type="button"
          class="toggle-btn"
          :class="{ active: activeType === 'bar' }"
          @click="setChartType('bar')"
          aria-label="Visualizar como gráfico de barras"
        >
          <i class="pi pi-chart-bar" aria-hidden="true"></i>
          <span>Barras</span>
        </button>
      </div>
    </div>

    <div v-if="loading" class="chart-loading-overlay" aria-live="polite">
      <i class="pi pi-spin pi-spinner" aria-hidden="true"></i>
      <span>Cargando reparto modal...</span>
    </div>

    <BaseChart
      ref="baseChartRef"
      :option="chartOption"
      :clear-before-set="isEmpty"
      height="380px"
      canvas-class="echarts-container"
      role="img"
      :aria-label="activeType === 'donut' ? 'Gráfico de anillo de distribución modal de viajes' : 'Gráfico de barras de distribución modal de viajes'"
      :tabindex="0"
      label="ModalSplitChart"
    />
  </div>
</template>

<style scoped>
.chart-card {
  background-color: var(--surface-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-cards);
  box-shadow: var(--shadow-card);
  padding: var(--spacing-20);
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
  min-height: 420px;
}

.chart-header-actions {
  display: flex;
  justify-content: flex-end;
  margin-bottom: var(--spacing-8);
}

.chart-type-toggle {
  display: inline-flex;
  background-color: var(--surface-subtle);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-buttons);
  padding: 2px;
  gap: 2px;
}

.toggle-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-6);
  min-height: var(--min-touch-target);
  min-block-size: var(--min-touch-target);
  padding: 0 var(--spacing-12);
  border-radius: var(--radius-buttons);
  border: none;
  background: transparent;
  color: var(--text-color);
  font-family: var(--font-inter);
  font-size: var(--text-caption);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all 0.15s ease;
}

.toggle-btn.active {
  background-color: var(--surface-card);
  color: var(--primary-color);
  font-weight: var(--font-weight-bold);
  box-shadow: var(--shadow-sm);
}

.toggle-btn:focus-visible {
  outline: 2px solid var(--primary-color);
  outline-offset: 2px;
}

.echarts-container {
  width: 100%;
  height: 380px;
}

.echarts-container:focus-visible {
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
  color: var(--primary-color);
  font-weight: var(--font-weight-medium);
  z-index: 10;
}
</style>
