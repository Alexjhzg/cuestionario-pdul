<script setup lang="ts">
import { ref, shallowRef, computed, onMounted, onBeforeUnmount, watch } from 'vue';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import canonicalGeoJsonRaw from '@/assets/geojson/maturin_parroquias.geojson?raw';
import type { ParroquiaResultado } from '@/services/analyticsApi';

const parsedCanonicalGeoJson = JSON.parse(canonicalGeoJsonRaw) as unknown as GeoJSON.FeatureCollection;

const props = withDefaults(
  defineProps<{
    metricas?: ParroquiaResultado[];
    geojson?: GeoJSON.FeatureCollection | null;
    loading?: boolean;
    titulo?: string;
  }>(),
  {
    metricas: () => [],
    geojson: null,
    loading: false,
    titulo: 'Distribución Cartográfica por Parroquias (Maturín)'
  }
);

const activeGeoJson = computed<GeoJSON.FeatureCollection>(() => {
  return props.geojson || parsedCanonicalGeoJson;
});

const emit = defineEmits<{
  (e: 'select-parroquia', codigo: string): void;
}>();

const mapContainer = ref<HTMLElement | null>(null);
const mapInstance = shallowRef<L.Map | null>(null);
const geoJsonLayer = shallowRef<L.GeoJSON | null>(null);
const selectedParroquia = ref<string | null>(null);

const legendThresholds = [
  { label: '> 25%', color: '#800026' },
  { label: '18% – 25%', color: '#BD0026' },
  { label: '12% – 18%', color: '#E31A1C' },
  { label: '6% – 12%', color: '#FD8D3C' },
  { label: '2% – 6%', color: '#FEB24C' },
  { label: '0.1% – 2%', color: '#FED976' },
  { label: '0% / Sin datos', color: '#FFFFCC' }
];

function getColorByPercentage(pct: number): string {
  return pct > 25 ? '#800026' :
         pct > 18 ? '#BD0026' :
         pct > 12 ? '#E31A1C' :
         pct > 6  ? '#FD8D3C' :
         pct > 2  ? '#FEB24C' :
         pct > 0  ? '#FED976' :
                    '#FFFFCC';
}

function getStyle(feature: any): L.PathOptions {
  const cod = feature?.properties?.codigo_parroquia ?? '';
  const lookup = new Map(props.metricas.map((m) => [m.parroquia, m]));
  const metrica = lookup.get(cod);
  const pct = metrica?.porcentaje ?? 0;
  const isSelected = selectedParroquia.value === cod;

  return {
    fillColor: getColorByPercentage(pct),
    weight: isSelected ? 3 : 1.5,
    opacity: 1,
    color: isSelected ? '#145aff' : '#334155',
    dashArray: isSelected ? '' : '1',
    fillOpacity: isSelected ? 0.9 : 0.75
  };
}

function renderChoropleth() {
  if (!mapInstance.value) return;

  if (geoJsonLayer.value) {
    geoJsonLayer.value.clearLayers();
    geoJsonLayer.value.remove();
    geoJsonLayer.value = null;
  }

  const lookup = new Map(props.metricas.map((m) => [m.parroquia, m]));

  try {
    geoJsonLayer.value = L.geoJSON(activeGeoJson.value, {
      style: (feature) => getStyle(feature),
      onEachFeature: (feature, layer) => {
        const cod = feature?.properties?.codigo_parroquia ?? '';
        const nombre = feature?.properties?.nombre_parroquia || feature?.properties?.nombre || cod;
        const metrica = lookup.get(cod);
        const total = metrica?.total_respuestas ?? 0;
        const pct = metrica?.porcentaje ?? 0;

        layer.bindTooltip(
          `<div class="map-tooltip-content">
            <strong class="tooltip-title">${nombre}</strong>
            <div class="tooltip-row"><span>Respuestas / Viajes:</span> <strong>${total.toLocaleString('es-VE')}</strong></div>
            <div class="tooltip-row"><span>Participación:</span> <strong>${pct.toFixed(1)}%</strong></div>
          </div>`,
          {
            sticky: true,
            className: 'custom-map-tooltip',
            direction: 'auto'
          }
        );

        layer.bindPopup(
          `<div class="map-popup-content">
            <h4 class="popup-title">${nombre}</h4>
            <p class="popup-row"><span>Total respuestas / viajes:</span> <strong>${total.toLocaleString('es-VE')}</strong></p>
            <p class="popup-row"><span>Participación:</span> <strong>${pct.toFixed(1)}%</strong></p>
          </div>`,
          { className: 'custom-map-popup' }
        );

        layer.on({
          mouseover: (e: L.LeafletMouseEvent) => {
            const target = e.target;
            target.setStyle({
              weight: 3,
              color: '#020520',
              fillOpacity: 0.95
            });
            if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) {
              target.bringToFront();
            }
          },
          mouseout: (e: L.LeafletMouseEvent) => {
            if (geoJsonLayer.value) {
              geoJsonLayer.value.resetStyle(e.target);
            }
          },
          click: () => {
            selectedParroquia.value = cod;
            layer.openPopup();
            emit('select-parroquia', cod);
          }
        });
      }
    }).addTo(mapInstance.value);
  } catch (err) {
    // Manejo seguro en entornos de prueba con DOM simplificado
    console.warn('Error al renderizar capa GeoJSON:', err);
  }
}

function initMap() {
  if (!mapContainer.value) return;

  // Centro oficial en Municipio Maturín, Monagas: [9.7457, -63.1832], zoom 11
  try {
    mapInstance.value = L.map(mapContainer.value, {
      center: [9.7457, -63.1832],
      zoom: 11,
      minZoom: 9,
      maxZoom: 16,
      scrollWheelZoom: false
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors'
    }).addTo(mapInstance.value);

    renderChoropleth();
  } catch (err) {
    console.warn('Leaflet map init warning:', err);
  }
}

function invalidateSize() {
  if (mapInstance.value) {
    mapInstance.value.invalidateSize();
  }
}

defineExpose({
  invalidateSize,
  mapInstance,
  geoJsonLayer
});

onMounted(() => {
  initMap();
});

watch(
  () => props.metricas,
  () => {
    renderChoropleth();
  },
  { deep: true }
);

watch(
  () => props.geojson,
  () => {
    renderChoropleth();
  },
  { deep: true }
);

onBeforeUnmount(() => {
  if (geoJsonLayer.value) {
    geoJsonLayer.value.clearLayers();
    geoJsonLayer.value.remove();
    geoJsonLayer.value = null;
  }
  if (mapInstance.value) {
    mapInstance.value.remove();
    mapInstance.value = null;
  }
});
</script>

<template>
  <div class="map-card" role="region" aria-label="Mapa coroplético municipal de Maturín">
    <div class="map-card-header">
      <div class="header-titles">
        <h3 class="map-title">{{ titulo }}</h3>
        <span class="map-subtitle">Pregunta: 1.- Parroquia (Sección I: Identificación de la Unidad Residencial)</span>
      </div>
      <div v-if="loading" class="map-loading-indicator" aria-live="polite">
        <i class="pi pi-spin pi-spinner" aria-hidden="true"></i>
        <span>Actualizando mapa...</span>
      </div>
    </div>

    <!-- Contenedor del Mapa Leaflet -->
    <div class="map-view-wrapper">
      <div
        ref="mapContainer"
        class="leaflet-map-canvas"
        role="application"
        aria-label="Mapa interactivo de las 11 parroquias de Maturín con escala coroplética"
        tabindex="0"
      ></div>

      <!-- Leyenda Accesible Integrada -->
      <aside class="map-legend" aria-label="Escala de porcentaje de participación">
        <span class="legend-title">Participación (%)</span>
        <ul class="legend-list">
          <li
            v-for="item in legendThresholds"
            :key="item.label"
            class="legend-item"
          >
            <span
              class="legend-swatch"
              :style="{ backgroundColor: item.color }"
              aria-hidden="true"
            ></span>
            <span class="legend-text">{{ item.label }}</span>
          </li>
        </ul>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.map-card {
  background-color: var(--surface-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-cards);
  box-shadow: var(--shadow-card);
  padding: var(--spacing-20);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-16);
  position: relative;
  overflow: hidden;
}

.map-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: var(--spacing-8);
}

.header-titles {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
}

.map-title {
  font-size: var(--text-subheading);
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
  margin: 0;
}

.map-subtitle {
  font-size: var(--text-caption);
  color: var(--text-helper);
}

.map-loading-indicator {
  display: flex;
  align-items: center;
  gap: var(--spacing-6);
  font-size: var(--text-caption);
  color: var(--color-royal-signal);
  font-weight: var(--font-weight-medium);
}

.map-view-wrapper {
  position: relative;
  width: 100%;
  height: 480px;
  border-radius: var(--radius-cards);
  overflow: hidden;
  border: 1px solid var(--border-color);
}

.leaflet-map-canvas {
  width: 100%;
  height: 100%;
  background-color: #f8fafc;
}

.leaflet-map-canvas:focus-visible {
  outline: 2px solid var(--focus-ring);
  outline-offset: -2px;
}

/* Leyenda integrada superpuesta */
.map-legend {
  position: absolute;
  bottom: var(--spacing-16);
  right: var(--spacing-16);
  background-color: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(4px);
  padding: var(--spacing-12);
  border-radius: var(--radius-cards);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-sm-2);
  z-index: 1000;
  max-width: 180px;
}

.legend-title {
  display: block;
  font-size: 0.72rem;
  font-weight: var(--font-weight-bold);
  color: var(--color-midnight-ink);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: var(--spacing-6);
}

.legend-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-8);
  font-size: 0.75rem;
  color: var(--color-slate-caption);
}

.legend-swatch {
  width: 16px;
  height: 12px;
  border-radius: 2px;
  border: 1px solid rgba(0, 0, 0, 0.2);
  flex-shrink: 0;
}

.legend-text {
  font-weight: var(--font-weight-medium);
}

/* Estilos de Tooltip Leaflet Global */
:deep(.custom-map-tooltip) {
  background-color: var(--color-midnight-ink);
  color: #ffffff;
  border: none;
  border-radius: 6px;
  padding: var(--spacing-8) var(--spacing-12);
  font-family: var(--font-inter);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

:deep(.custom-map-tooltip::before) {
  border-top-color: var(--color-midnight-ink);
}

:deep(.map-tooltip-content) {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

:deep(.tooltip-title) {
  font-size: 0.85rem;
  color: #ffffff;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  padding-bottom: 2px;
  margin-bottom: 2px;
}

:deep(.tooltip-row) {
  font-size: 0.75rem;
  color: #cbd5e1;
  display: flex;
  justify-content: space-between;
  gap: var(--spacing-8);
}

:deep(.tooltip-row strong) {
  color: #ffffff;
}

@media (max-width: 640px) {
  .map-view-wrapper {
    height: 360px;
  }

  .map-legend {
    bottom: var(--spacing-8);
    right: var(--spacing-8);
    padding: var(--spacing-8);
    font-size: 0.7rem;
  }
}
</style>
