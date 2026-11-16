import { onBeforeUnmount, onMounted, shallowRef, watch, type Ref, type WatchSource } from 'vue';
import * as echarts from 'echarts';

/**
 * Paleta institucional compartida derivada de los tokens de diseño de la Alcaldía de Maturín.
 */
export const INSTITUTIONAL_CHART_PALETTE = [
  '#145aff', // Royal Signal
  '#16ca2e', // Mint Win
  '#3b82f6', // Cobalt Glow
  '#ffa64d', // Amber Pending
  '#f26052', // Coral Lost
  '#8b5cf6', // Violet
  '#06b6d4', // Cyan
  '#ec4899', // Pink
  '#64748b'  // Slate Neutral
] as const;

export const CHART_FONT_FAMILY = 'Inter, sans-serif';

export interface ChartRenderSpec {
  option: echarts.EChartsOption;
  clearBeforeSet?: boolean;
  notMerge?: boolean;
}

export interface UseEChartsOptions {
  watchSources?: WatchSource<unknown>[];
  loading?: Ref<boolean> | (() => boolean);
  loadingColor?: string;
  label?: string;
}

export function useECharts(
  containerRef: Ref<HTMLElement | null>,
  buildOption: () => ChartRenderSpec | echarts.EChartsOption | null,
  options: UseEChartsOptions = {}
) {
  const chartInstance = shallowRef<echarts.ECharts | null>(null);
  let resizeObserver: ResizeObserver | null = null;

  function update() {
    if (!chartInstance.value) return;
    const rawSpec = buildOption();
    if (!rawSpec) return;

    const spec: ChartRenderSpec =
      'option' in rawSpec
        ? (rawSpec as ChartRenderSpec)
        : { option: rawSpec as echarts.EChartsOption, notMerge: true };

    try {
      if (spec.clearBeforeSet && typeof chartInstance.value.clear === 'function') {
        chartInstance.value.clear();
      }
      if (spec.notMerge === false) {
        chartInstance.value.setOption(spec.option);
      } else if (spec.clearBeforeSet) {
        chartInstance.value.setOption(spec.option);
      } else {
        chartInstance.value.setOption(spec.option, true);
      }
    } catch (err) {
      console.warn(`ECharts ${options.label || 'chart'} setOption warning:`, err);
    }
  }

  function init() {
    if (!containerRef.value) return;
    try {
      chartInstance.value = echarts.init(containerRef.value);
      update();

      if (typeof ResizeObserver !== 'undefined') {
        resizeObserver = new ResizeObserver(() => {
          chartInstance.value?.resize();
        });
        resizeObserver.observe(containerRef.value);
      }
    } catch (err) {
      console.warn(`ECharts ${options.label || 'chart'} init warning:`, err);
    }
  }

  function resize() {
    chartInstance.value?.resize();
  }

  onMounted(() => {
    init();
  });

  if (options.watchSources && options.watchSources.length > 0) {
    watch(options.watchSources, () => update(), { deep: true });
  }

  if (options.loading !== undefined) {
    watch(
      options.loading,
      (isLoading) => {
        if (!chartInstance.value) return;
        if (isLoading) {
          if (typeof chartInstance.value.showLoading === 'function') {
            chartInstance.value.showLoading({
              text: 'Cargando datos...',
              color: options.loadingColor || '#145aff'
            });
          }
        } else {
          if (typeof chartInstance.value.hideLoading === 'function') {
            chartInstance.value.hideLoading();
          }
          update();
        }
      }
    );
  }

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

  return {
    chartInstance,
    update,
    resize
  };
}

