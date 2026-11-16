<script setup lang="ts">
import { ref } from 'vue';
import type * as echarts from 'echarts';
import { useECharts } from '@/composables/useECharts';

const props = withDefaults(
  defineProps<{
    option: echarts.EChartsOption | null;
    clearBeforeSet?: boolean;
    loading?: boolean;
    loadingColor?: string;
    height?: string;
    canvasClass?: string;
    ariaLabel?: string;
    role?: string;
    tabindex?: number;
    label?: string;
  }>(),
  {
    clearBeforeSet: false,
    loading: false,
    loadingColor: '#145aff',
    height: '340px',
    canvasClass: '',
    ariaLabel: undefined,
    role: undefined,
    tabindex: undefined,
    label: 'BaseChart'
  }
);

const chartContainer = ref<HTMLElement | null>(null);

const { chartInstance, resize, update } = useECharts(
  chartContainer,
  () =>
    props.option
      ? {
          option: props.option,
          clearBeforeSet: props.clearBeforeSet,
          notMerge: !props.clearBeforeSet
        }
      : null,
  {
    watchSources: [() => props.option, () => props.clearBeforeSet],
    loading: () => props.loading,
    loadingColor: props.loadingColor,
    label: props.label
  }
);

defineExpose({
  chartInstance,
  resize,
  update
});
</script>

<template>
  <div
    ref="chartContainer"
    class="chart-canvas"
    :class="canvasClass"
    :style="{ height, width: '100%' }"
    :role="role"
    :aria-label="ariaLabel"
    :tabindex="tabindex"
  ></div>
</template>

<style scoped>
.chart-canvas {
  min-height: 320px;
}

.chart-canvas:focus-visible {
  outline: 2px solid var(--focus-ring);
  outline-offset: -2px;
}
</style>

