# Patrones de Integración Vue 3 (`<script setup>`) + PrimeVue v3 + Form.io + Leaflet + ECharts

## 1. Renderizador Local de Encuestas con `@formio/js` y PrimeVue Card

```vue
<script setup lang="ts">
import { ref, shallowRef, onMounted, onBeforeUnmount } from 'vue';
import { Formio } from '@formio/js';
import Card from 'primevue/card';
import Message from 'primevue/message';

const props = defineProps<{
  schema: Record<string, unknown>;
  submitUrl: string;
}>();

const emit = defineEmits<{
  (e: 'submitted', payload: Record<string, unknown>): void;
}>();

const formContainer = ref<HTMLElement | null>(null);
const formInstance = shallowRef<any>(null);
const errorMsg = ref<string | null>(null);
const successMsg = ref<string | null>(null);

onMounted(async () => {
  if (!formContainer.value) return;
  formInstance.value = await Formio.createForm(formContainer.value, props.schema, {
    noAlerts: true,
    language: 'es'
  });

  formInstance.value.on('submit', async (submission: { data: Record<string, unknown> }) => {
    errorMsg.value = null;
    try {
      const response = await fetch(props.submitUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data: submission.data })
      });
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Error al registrar la participación.');
      }
      successMsg.value = 'Su participación fue registrada exitosamente.';
      formInstance.value.emit('submitDone', submission);
      emit('submitted', submission.data);
    } catch (e: any) {
      errorMsg.value = e.message;
      formInstance.value.emit('submitError', e);
    }
  });
});

onBeforeUnmount(() => {
  if (formInstance.value) {
    formInstance.value.destroy(true);
    formInstance.value = null;
  }
});
</script>

<template>
  <Card>
    <template #content>
      <Message v-if="errorMsg" severity="error" :closable="false">{{ errorMsg }}</Message>
      <Message v-if="successMsg" severity="success" :closable="false">{{ successMsg }}</Message>
      <div ref="formContainer" class="formio-local-wrapper"></div>
    </template>
  </Card>
</template>
```

---

## 2. Mapa Coroplético Municipal con `leaflet` y `shallowRef`

```vue
<script setup lang="ts">
import { ref, shallowRef, onMounted, onBeforeUnmount, watch } from 'vue';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

interface ParroquiaMetrica {
  parroquia: string;
  total_respuestas: number;
  porcentaje: number;
}

const props = defineProps<{
  geojsonParroquias: GeoJSON.FeatureCollection;
  metricas: ParroquiaMetrica[];
}>();

const mapContainer = ref<HTMLElement | null>(null);
const mapInstance = shallowRef<L.Map | null>(null);
const geoJsonLayer = shallowRef<L.GeoJSON | null>(null);

function getColorByPercentage(pct: number): string {
  return pct > 25 ? '#800026' :
         pct > 18 ? '#BD0026' :
         pct > 12 ? '#E31A1C' :
         pct > 6  ? '#FD8D3C' :
         pct > 2  ? '#FEB24C' :
                    '#FFEDA0';
}

function renderChoropleth() {
  if (!mapInstance.value) return;
  if (geoJsonLayer.value) {
    geoJsonLayer.value.remove();
  }
  const lookup = new Map(props.metricas.map((m) => [m.parroquia, m]));

  geoJsonLayer.value = L.geoJSON(props.geojsonParroquias, {
    style: (feature) => {
      const cod = feature?.properties?.codigo_parroquia ?? '';
      const metrica = lookup.get(cod);
      return {
        fillColor: getColorByPercentage(metrica?.porcentaje ?? 0),
        weight: 1.5,
        opacity: 1,
        color: '#334155',
        fillOpacity: 0.75
      };
    },
    onEachFeature: (feature, layer) => {
      const cod = feature?.properties?.codigo_parroquia ?? '';
      const nombre = feature?.properties?.nombre ?? cod;
      const metrica = lookup.get(cod);
      layer.bindTooltip(
        `<strong>${nombre}</strong><br/>Respuestas: ${metrica?.total_respuestas ?? 0} (${metrica?.porcentaje ?? 0}%)`
      );
    }
  }).addTo(mapInstance.value);
}

onMounted(() => {
  if (!mapContainer.value) return;
  // Centro en Municipio Maturín, Estado Monagas
  mapInstance.value = L.map(mapContainer.value).setView([9.7457, -63.1832], 11);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap contributors'
  }).addTo(mapInstance.value);

  renderChoropleth();
});

watch(() => props.metricas, renderChoropleth, { deep: true });

onBeforeUnmount(() => {
  if (mapInstance.value) {
    mapInstance.value.remove();
    mapInstance.value = null;
  }
});
</script>

<template>
  <div ref="mapContainer" style="width: 100%; height: 480px; border-radius: 8px;"></div>
</template>
```

---

## 3. Gráfico Estadístico con `echarts`, `toolbox` y `ResizeObserver`

```vue
<script setup lang="ts">
import { ref, shallowRef, onMounted, onBeforeUnmount, watch } from 'vue';
import * as echarts from 'echarts';

const props = defineProps<{
  titulo: string;
  labels: string[];
  values: number[];
}>();

const chartContainer = ref<HTMLElement | null>(null);
const chartInstance = shallowRef<echarts.ECharts | null>(null);
let resizeObserver: ResizeObserver | null = null;

function updateChart() {
  if (!chartInstance.value) return;
  chartInstance.value.setOption({
    title: { text: props.titulo, left: 'center' },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    toolbox: {
      feature: {
        saveAsImage: { title: 'Descargar Gráfico', pixelRatio: 2 },
        dataView: { title: 'Ver Datos', readOnly: true }
      }
    },
    grid: { left: '3%', right: '4%', bottom: '8%', containLabel: true },
    xAxis: { type: 'category', data: props.labels, axisLabel: { rotate: 25 } },
    yAxis: { type: 'value' },
    series: [
      {
        name: 'Respuestas',
        type: 'bar',
        data: props.values,
        itemStyle: { borderRadius: [4, 4, 0, 0] }
      }
    ]
  });
}

onMounted(() => {
  if (!chartContainer.value) return;
  chartInstance.value = echarts.init(chartContainer.value);
  updateChart();

  resizeObserver = new ResizeObserver(() => {
    chartInstance.value?.resize();
  });
  resizeObserver.observe(chartContainer.value);
});

watch(() => [props.labels, props.values], updateChart, { deep: true });

onBeforeUnmount(() => {
  resizeObserver?.disconnect();
  resizeObserver = null;
  chartInstance.value?.dispose();
  chartInstance.value = null;
});
</script>

<template>
  <div ref="chartContainer" style="width: 100%; height: 380px;"></div>
</template>
```

