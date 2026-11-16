import { onBeforeUnmount, onMounted, shallowRef, watch, type Ref, type WatchSource } from 'vue';
import L from 'leaflet';

export interface UseLeafletMapOptions {
  center?: [number, number];
  zoom?: number;
  minZoom?: number;
  maxZoom?: number;
  watchSources?: WatchSource<unknown>[];
  renderLayer: (map: L.Map) => L.GeoJSON | null;
}

export function useLeafletMap(
  containerRef: Ref<HTMLElement | null>,
  options: UseLeafletMapOptions
) {
  const mapInstance = shallowRef<L.Map | null>(null);
  const geoJsonLayer = shallowRef<L.GeoJSON | null>(null);

  function render() {
    if (!mapInstance.value) return;
    if (geoJsonLayer.value) {
      geoJsonLayer.value.clearLayers();
      geoJsonLayer.value.remove();
      geoJsonLayer.value = null;
    }
    try {
      geoJsonLayer.value = options.renderLayer(mapInstance.value);
    } catch (err) {
      console.warn('Error al renderizar capa GeoJSON:', err);
    }
  }

  function initMap() {
    if (!containerRef.value) return;
    try {
      mapInstance.value = L.map(containerRef.value, {
        center: options.center || [9.7457, -63.1832],
        zoom: options.zoom ?? 11,
        minZoom: options.minZoom ?? 9,
        maxZoom: options.maxZoom ?? 16,
        scrollWheelZoom: false
      });

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution:
          '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors'
      }).addTo(mapInstance.value);

      render();
    } catch (err) {
      console.warn('Leaflet map init warning:', err);
    }
  }

  function invalidateSize() {
    mapInstance.value?.invalidateSize();
  }

  onMounted(() => {
    initMap();
  });

  if (options.watchSources && options.watchSources.length > 0) {
    watch(options.watchSources, () => render(), { deep: true });
  }

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

  return {
    mapInstance,
    geoJsonLayer,
    render,
    invalidateSize
  };
}

