<script setup lang="ts">
import { ref, shallowRef, watch, onMounted, onBeforeUnmount, nextTick } from 'vue';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import canonicalGeoJsonRaw from '@shared/geojson/maturin_parroquias.geojson?raw';
import type { SurveyFieldMapPoint, CalidadUbicacion } from '@/services/api';
import type { FieldMapViewMode } from '@/composables/useAdminFieldMap';
import {
  DISPOSITIVO_TIPO_LABELS,
  formatFecha,
  formatParroquia,
  humanLabel
} from '@/utils/responseFormatters';

const parsedCanonicalGeoJson = JSON.parse(canonicalGeoJsonRaw) as unknown as GeoJSON.FeatureCollection;

const MATURIN_CENTER: [number, number] = [9.7457, -63.1832];
const MATURIN_DEFAULT_ZOOM = 11;

const props = withDefaults(
  defineProps<{
    points: SurveyFieldMapPoint[];
    viewMode?: FieldMapViewMode;
    loading?: boolean;
  }>(),
  {
    points: () => [],
    viewMode: 'map',
    loading: false
  }
);

const emit = defineEmits<{
  (e: 'inspect-point', respuestaId: number): void;
}>();

const mapContainer = ref<HTMLElement | null>(null);
const mapInstance = shallowRef<L.Map | null>(null);
const baseGeoJsonLayer = shallowRef<L.GeoJSON | null>(null);
const markersLayer = shallowRef<L.LayerGroup | null>(null);
const precisionCircle = shallowRef<L.Circle | null>(null);
let resizeObserver: ResizeObserver | null = null;

const legendItems: { key: CalidadUbicacion; label: string; fill: string; stroke: string }[] = [
  { key: 'alta', label: 'Precisión alta (≤ 100 m)', fill: '#16ca2e', stroke: '#0f7a1c' },
  { key: 'media', label: 'Precisión media (101–500 m)', fill: '#ffa64d', stroke: '#b45309' },
  { key: 'alerta', label: 'Alerta (> 500 m o fuera de Maturín)', fill: '#f26052', stroke: '#991b1b' }
];

function getQualityStyle(calidad: CalidadUbicacion): { fillColor: string; color: string } {
  if (calidad === 'alta') return { fillColor: '#16ca2e', color: '#0f7a1c' };
  if (calidad === 'media') return { fillColor: '#ffa64d', color: '#b45309' };
  return { fillColor: '#f26052', color: '#991b1b' };
}

function escapeHtml(raw: unknown): string {
  return String(raw ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function buildPopupHtml(point: SurveyFieldMapPoint): string {
  const parroquiaTxt = escapeHtml(formatParroquia(point.parroquia));
  const comunidadTxt = escapeHtml(point.comunidad_sector || 'No especificada');
  const zonaTxt = escapeHtml(point.zona_od || 'No especificada');
  const dispositivoTxt = escapeHtml(humanLabel(DISPOSITIVO_TIPO_LABELS, point.dispositivo_tipo));
  const precisionTxt =
    typeof point.precision_m === 'number'
      ? `±${Math.round(point.precision_m)} m`
      : 'No reportada';
  const fechaTxt = escapeHtml(formatFecha(point.fecha_registro));
  const alertaHtml = point.motivo_alerta
    ? `<p class="field-popup-alert"><strong>Alerta:</strong> ${escapeHtml(point.motivo_alerta)}</p>`
    : '';

  return `
    <div class="field-map-popup">
      <h4 class="field-popup-title">Encuesta #${point.id}</h4>
      <div class="field-popup-row"><span>Parroquia:</span> <strong>${parroquiaTxt}</strong></div>
      <div class="field-popup-row"><span>Comunidad:</span> <strong>${comunidadTxt}</strong></div>
      <div class="field-popup-row"><span>Zona O-D:</span> <strong>${zonaTxt}</strong></div>
      <div class="field-popup-row"><span>Dispositivo:</span> <strong>${dispositivoTxt}</strong></div>
      <div class="field-popup-row"><span>Precisión:</span> <strong>${precisionTxt}</strong></div>
      <div class="field-popup-row"><span>Fecha:</span> <strong>${fechaTxt}</strong></div>
      ${alertaHtml}
      <button type="button" class="popup-inspect-btn" data-respuesta-id="${point.id}">
        Inspeccionar respuesta
      </button>
    </div>
  `;
}

function clearPrecisionCircle() {
  if (precisionCircle.value && mapInstance.value) {
    precisionCircle.value.removeFrom(mapInstance.value);
  }
  precisionCircle.value = null;
}

function renderMarkers() {
  if (!mapInstance.value) return;

  if (markersLayer.value) {
    markersLayer.value.clearLayers();
  } else {
    markersLayer.value = L.layerGroup().addTo(mapInstance.value);
  }
  clearPrecisionCircle();

  const layerGroup = markersLayer.value;
  if (!layerGroup) return;

  for (const point of props.points) {
    const palette = getQualityStyle(point.calidad_ubicacion);
    const marker = L.circleMarker([point.latitud, point.longitud], {
      radius: point.calidad_ubicacion === 'alerta' ? 9 : 7,
      fillColor: palette.fillColor,
      color: palette.color,
      weight: 2,
      opacity: 1,
      fillOpacity: 0.88
    });

    marker.bindTooltip(
      `<strong>#${point.id}</strong> · ${escapeHtml(formatParroquia(point.parroquia))}`,
      { direction: 'top', opacity: 0.95 }
    );
    marker.bindPopup(buildPopupHtml(point), { maxWidth: 280 });

    marker.on('click', () => {
      clearPrecisionCircle();
      if (mapInstance.value && typeof point.precision_m === 'number' && point.precision_m > 0) {
        precisionCircle.value = L.circle([point.latitud, point.longitud], {
          radius: point.precision_m,
          color: palette.color,
          fillColor: palette.fillColor,
          fillOpacity: 0.14,
          weight: 1.5,
          dashArray: '4 4'
        }).addTo(mapInstance.value);
      }
    });

    marker.addTo(layerGroup);
  }
}

function initLeafletMap() {
  if (!mapContainer.value || mapInstance.value) return;

  try {
    const map = L.map(mapContainer.value, {
      center: MATURIN_CENTER,
      zoom: MATURIN_DEFAULT_ZOOM,
      minZoom: 4,
      maxZoom: 18,
      scrollWheelZoom: true
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors'
    }).addTo(map);

    baseGeoJsonLayer.value = L.geoJSON(parsedCanonicalGeoJson, {
      style: () => ({
        color: '#3b82f6',
        weight: 1.5,
        opacity: 0.7,
        fillColor: '#f0f4fe',
        fillOpacity: 0.12
      }),
      onEachFeature: (feature, layer) => {
        const nombre = feature?.properties?.nombre_parroquia || feature?.properties?.nombre;
        if (nombre) {
          layer.bindTooltip(String(nombre), { sticky: true });
        }
      }
    }).addTo(map);

    map.on('popupopen', (evt: L.PopupEvent) => {
      const popupEl = evt.popup.getElement();
      const btn = popupEl?.querySelector<HTMLButtonElement>('.popup-inspect-btn');
      if (btn) {
        btn.onclick = () => {
          const id = Number(btn.dataset.respuestaId);
          if (Number.isFinite(id) && id > 0) {
            emit('inspect-point', id);
          }
        };
      }
    });

    mapInstance.value = map;
    renderMarkers();

    if (typeof ResizeObserver !== 'undefined') {
      resizeObserver = new ResizeObserver(() => {
        mapInstance.value?.invalidateSize();
      });
      resizeObserver.observe(mapContainer.value);
    }
  } catch (err) {
    console.warn('No se pudo inicializar el mapa Leaflet en este entorno:', err);
  }
}

function centerOnMaturin() {
  clearPrecisionCircle();
  mapInstance.value?.setView(MATURIN_CENTER, MATURIN_DEFAULT_ZOOM);
}

function fitToPoints() {
  if (!mapInstance.value || props.points.length === 0) return;
  try {
    const bounds = L.latLngBounds(
      props.points.map((p) => [p.latitud, p.longitud] as [number, number])
    );
    mapInstance.value.fitBounds(bounds, { padding: [36, 36], maxZoom: 16 });
  } catch {
    centerOnMaturin();
  }
}

function invalidateSize() {
  mapInstance.value?.invalidateSize();
}

onMounted(() => {
  if (props.viewMode === 'map') {
    initLeafletMap();
  }
});

watch(
  () => props.points,
  () => {
    renderMarkers();
  },
  { deep: true }
);

watch(
  () => props.viewMode,
  async (newMode) => {
    if (newMode === 'map') {
      await nextTick();
      if (!mapInstance.value) {
        initLeafletMap();
      } else {
        invalidateSize();
      }
    }
  }
);

onBeforeUnmount(() => {
  resizeObserver?.disconnect();
  resizeObserver = null;
  clearPrecisionCircle();
  if (markersLayer.value) {
    markersLayer.value.clearLayers();
    markersLayer.value = null;
  }
  if (baseGeoJsonLayer.value) {
    baseGeoJsonLayer.value.clearLayers();
    baseGeoJsonLayer.value = null;
  }
  if (mapInstance.value) {
    mapInstance.value.remove();
    mapInstance.value = null;
  }
});

defineExpose({
  centerOnMaturin,
  fitToPoints,
  invalidateSize
});
</script>

<template>
  <figure class="field-map-card" aria-label="Mapa georreferenciado de encuestas levantadas">
    <div class="field-map-toolbar">
      <figcaption class="field-map-caption">
        Ubicación GPS capturada por encuesta sobre el mapa parroquial de Maturín (puntos rojos indican baja precisión o coordenada fuera del municipio).
      </figcaption>
      <div v-if="viewMode === 'map'" class="map-controls-group">
        <button
          type="button"
          class="map-control-btn"
          data-testid="btn-center-maturin"
          @click="centerOnMaturin"
        >
          <i class="pi pi-compass" aria-hidden="true"></i>
          <span>Centrar en Maturín</span>
        </button>
        <button
          type="button"
          class="map-control-btn"
          :disabled="points.length === 0"
          data-testid="btn-fit-points"
          @click="fitToPoints"
        >
          <i class="pi pi-arrows-alt" aria-hidden="true"></i>
          <span>Ajustar a encuestas ({{ points.length }})</span>
        </button>
      </div>
    </div>

    <div v-show="viewMode === 'map'" class="map-view-wrapper">
      <div
        ref="mapContainer"
        class="leaflet-map-canvas"
        role="application"
        aria-label="Mapa interactivo de puntos GPS de encuestas levantadas"
        tabindex="0"
        data-testid="admin-field-map-canvas"
      ></div>

      <div v-if="loading" class="map-loading-overlay" aria-live="polite">
        <i class="pi pi-spin pi-spinner" aria-hidden="true"></i>
        <span>Cargando puntos GPS...</span>
      </div>

      <div v-else-if="points.length === 0" class="map-empty-overlay" role="status">
        <i class="pi pi-map-marker" aria-hidden="true"></i>
        <span>No hay puntos GPS que coincidan con los filtros actuales.</span>
      </div>

      <aside class="map-legend" aria-label="Semáforo de calidad de ubicación GPS">
        <span class="legend-title">Calidad GPS</span>
        <ul class="legend-list">
          <li v-for="item in legendItems" :key="item.key" class="legend-item">
            <span
              class="legend-dot"
              :style="{ backgroundColor: item.fill, borderColor: item.stroke }"
              aria-hidden="true"
            ></span>
            <span class="legend-text">{{ item.label }}</span>
          </li>
        </ul>
      </aside>
    </div>

    <!-- Alternativa Tabular Accesible (WCAG AA) -->
    <div v-if="viewMode === 'table'" class="table-responsive-wrapper" data-testid="field-map-table-view">
      <table class="field-map-table">
        <caption>Listado georreferenciado de encuestas levantadas en campo</caption>
        <thead>
          <tr>
            <th scope="col">ID</th>
            <th scope="col">Parroquia</th>
            <th scope="col">Comunidad / Sector</th>
            <th scope="col">Zona O-D</th>
            <th scope="col">Dispositivo</th>
            <th scope="col">Coordenadas</th>
            <th scope="col">Calidad GPS</th>
            <th scope="col">Fecha</th>
            <th scope="col">Acción</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="points.length === 0">
            <td colspan="9" class="empty-table-cell">
              No hay puntos GPS registrados para los filtros seleccionados.
            </td>
          </tr>
          <tr v-for="pt in points" :key="pt.id">
            <td class="mono-cell">#{{ pt.id }}</td>
            <td>{{ formatParroquia(pt.parroquia) }}</td>
            <td>{{ pt.comunidad_sector || '—' }}</td>
            <td>{{ pt.zona_od || '—' }}</td>
            <td>{{ humanLabel(DISPOSITIVO_TIPO_LABELS, pt.dispositivo_tipo) }}</td>
            <td class="mono-cell">{{ pt.latitud.toFixed(5) }}, {{ pt.longitud.toFixed(5) }}</td>
            <td>
              <span class="quality-badge" :class="`quality-${pt.calidad_ubicacion}`">
                {{
                  pt.calidad_ubicacion === 'alta'
                    ? 'Alta'
                    : pt.calidad_ubicacion === 'media'
                      ? 'Media'
                      : 'Alerta'
                }}
                <template v-if="typeof pt.precision_m === 'number'">
                  (±{{ Math.round(pt.precision_m) }} m)
                </template>
              </span>
            </td>
            <td>{{ formatFecha(pt.fecha_registro) }}</td>
            <td>
              <button
                type="button"
                class="table-inspect-btn"
                :data-testid="`btn-inspect-point-${pt.id}`"
                @click="emit('inspect-point', pt.id)"
              >
                Ver respuesta
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </figure>
</template>

<style scoped>
.field-map-card {
  margin: 0;
  background-color: var(--surface-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-containers);
  padding: var(--spacing-20);
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-16);
}

.field-map-toolbar {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: var(--spacing-12);
}

.field-map-caption {
  font-size: var(--text-body-sm);
  color: var(--text-muted);
  margin: 0;
  flex: 1 1 280px;
}

.map-controls-group {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-8);
}

.map-control-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-6);
  min-block-size: var(--min-touch-target);
  min-height: var(--min-touch-target);
  padding: 0 var(--spacing-12);
  border-radius: var(--radius-inputs);
  border: 1px solid var(--border-color);
  background-color: #ffffff;
  color: var(--color-midnight-ink);
  font-size: var(--text-caption);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
  transition: border-color 0.2s ease, background-color 0.2s ease;
}

.map-control-btn:hover:not(:disabled) {
  border-color: var(--color-royal-signal);
  background-color: var(--color-blue-wash);
}

.map-control-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.map-view-wrapper {
  position: relative;
  width: 100%;
  height: 500px;
  border-radius: var(--radius-cards);
  overflow: hidden;
  border: 1px solid var(--border-color);
}

.leaflet-map-canvas {
  width: 100%;
  height: 100%;
  background-color: #f8fafc;
}

.map-loading-overlay,
.map-empty-overlay {
  position: absolute;
  top: var(--spacing-16);
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-8);
  padding: var(--spacing-8) var(--spacing-16);
  background-color: rgba(255, 255, 255, 0.96);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-cards);
  box-shadow: var(--shadow-sm);
  font-size: var(--text-body-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-midnight-ink);
}

.map-legend {
  position: absolute;
  bottom: var(--spacing-16);
  right: var(--spacing-16);
  z-index: 1000;
  background-color: rgba(255, 255, 255, 0.96);
  padding: var(--spacing-12);
  border-radius: var(--radius-cards);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-sm);
}

.legend-title {
  display: block;
  font-size: 0.72rem;
  font-weight: var(--font-weight-bold);
  color: var(--color-midnight-ink);
  text-transform: uppercase;
  margin-bottom: var(--spacing-6);
}

.legend-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-8);
  font-size: 0.76rem;
  color: var(--color-midnight-ink);
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid;
  flex-shrink: 0;
}

:deep(.field-map-popup) {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-family: var(--font-inter);
  min-width: 210px;
}

:deep(.field-popup-title) {
  margin: 0 0 4px 0;
  font-size: 0.95rem;
  color: var(--color-midnight-ink);
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 4px;
}

:deep(.field-popup-row) {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  font-size: 0.8rem;
  color: var(--text-muted);
}

:deep(.field-popup-row strong) {
  color: var(--color-midnight-ink);
  text-align: right;
}

:deep(.field-popup-alert) {
  margin: 4px 0 0 0;
  padding: 6px 8px;
  border-radius: 6px;
  background-color: #fef2f2;
  color: #991b1b;
  font-size: 0.76rem;
}

:deep(.popup-inspect-btn) {
  margin-top: 6px;
  min-block-size: 40px;
  min-height: 40px;
  padding: 6px 12px;
  border: none;
  border-radius: 6px;
  background-color: var(--color-royal-signal);
  color: #ffffff;
  font-weight: 600;
  font-size: 0.82rem;
  cursor: pointer;
}

.table-responsive-wrapper {
  overflow-x: auto;
  width: 100%;
}

.field-map-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--text-body-sm);
}

.field-map-table caption {
  text-align: left;
  font-weight: var(--font-weight-semibold);
  color: var(--color-midnight-ink);
  margin-bottom: var(--spacing-8);
}

.field-map-table th,
.field-map-table td {
  text-align: left;
  padding: var(--spacing-12);
  border-bottom: 1px solid var(--border-color);
}

.field-map-table th {
  font-size: var(--text-caption);
  text-transform: uppercase;
  color: var(--text-muted);
  background-color: #f8fafc;
}

.mono-cell {
  font-family: var(--font-mono);
  font-size: 0.82rem;
}

.quality-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: var(--font-weight-semibold);
}

.quality-alta {
  background-color: #dcfce7;
  color: #166534;
}

.quality-media {
  background-color: #ffedd5;
  color: #9a3412;
}

.quality-alerta {
  background-color: #fee2e2;
  color: #991b1b;
}

.table-inspect-btn {
  min-block-size: var(--min-touch-target);
  min-height: var(--min-touch-target);
  padding: 0 var(--spacing-12);
  border-radius: var(--radius-inputs);
  border: 1px solid var(--color-royal-signal);
  background-color: var(--color-blue-wash);
  color: var(--color-royal-signal);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
}

.empty-table-cell {
  text-align: center;
  color: var(--text-muted);
  padding: var(--spacing-24);
}
</style>
