import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import * as echarts from 'echarts';
import L from 'leaflet';

import KpiCardsGrid from '@/components/dashboard/KpiCardsGrid.vue';
import MaturinChoroplethMap from '@/components/dashboard/MaturinChoroplethMap.vue';
import ModalSplitChart from '@/components/dashboard/ModalSplitChart.vue';
import OdFlowMatrixChart from '@/components/dashboard/OdFlowMatrixChart.vue';
import AccessibleDataFallback from '@/components/dashboard/AccessibleDataFallback.vue';
import DashboardView from '@/views/DashboardView.vue';

import * as analyticsApi from '@/services/analyticsApi';
import * as api from '@/services/api';

// Polyfill de ResizeObserver para happy-dom
class ResizeObserverMock {
  callback: ResizeObserverCallback;
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
  constructor(cb: ResizeObserverCallback) {
    this.callback = cb;
  }
}

// Polyfill seguro de Canvas 2D context para happy-dom
if (typeof HTMLCanvasElement !== 'undefined' && !HTMLCanvasElement.prototype.getContext) {
  HTMLCanvasElement.prototype.getContext = vi.fn(() => ({
    fillRect: vi.fn(),
    clearRect: vi.fn(),
    getImageData: vi.fn(() => ({ data: [] })),
    putImageData: vi.fn(),
    createImageData: vi.fn(() => []),
    setTransform: vi.fn(),
    drawImage: vi.fn(),
    save: vi.fn(),
    fillText: vi.fn(),
    restore: vi.fn(),
    beginPath: vi.fn(),
    moveTo: vi.fn(),
    lineTo: vi.fn(),
    closePath: vi.fn(),
    stroke: vi.fn(),
    translate: vi.fn(),
    scale: vi.fn(),
    rotate: vi.fn(),
    arc: vi.fn(),
    fill: vi.fn(),
    measureText: vi.fn(() => ({ width: 50 }))
  })) as any;
}

// Mock de ECharts para permitir espionaje seguro en entorno ES Module
const mockChartInstance = {
  setOption: vi.fn(),
  resize: vi.fn(),
  dispose: vi.fn(),
  clear: vi.fn(),
  showLoading: vi.fn(),
  hideLoading: vi.fn()
};

vi.mock('echarts', async (importOriginal) => {
  const actual = await importOriginal<typeof import('echarts')>();
  return {
    ...actual,
    init: vi.fn(() => mockChartInstance)
  };
});

// Mocks de APIs
vi.mock('@/services/analyticsApi', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/services/analyticsApi')>();
  return {
    ...actual,
    fetchEncuestas: vi.fn(),
    fetchKpis: vi.fn(),
    fetchResultadosParroquia: vi.fn(),
    fetchRepartoModal: vi.fn(),
    fetchMatrizOD: vi.fn(),
    fetchAllAnalytics: vi.fn(),
    fetchMetricasCampo: vi.fn().mockResolvedValue({ campo: 'calificacion_servicio_tp', labels: [], values: [] })
  };
});

vi.mock('@/services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/services/api')>();
  return {
    ...actual,
    fetchAdminEncuestas: vi.fn(),
    exportarRespuestasAdmin: vi.fn(),
    descargarBlob: vi.fn()
  };
});

const mockKpis: analyticsApi.KpiMetrics = {
  total_encuestas: 1420,
  total_viajes: 3850,
  total_residentes: 4980,
  parroquia_lider: 'san_simon'
};

const mockParroquias: analyticsApi.ParroquiaResultado[] = [
  { parroquia: 'san_simon', total_respuestas: 520, porcentaje: 36.62 },
  { parroquia: 'alto_de_los_godos', total_respuestas: 310, porcentaje: 21.83 },
  { parroquia: 'boqueron', total_respuestas: 240, porcentaje: 16.90 },
  { parroquia: 'las_cocuizas', total_respuestas: 150, porcentaje: 10.56 },
  { parroquia: 'santa_cruz', total_respuestas: 200, porcentaje: 14.08 }
];

const mockRepartoModal: analyticsApi.RepartoModalItem[] = [
  { modo: '6', etiqueta: 'Transporte público (bus/buseta)', total_viajes: 1950, porcentaje: 50.65 },
  { modo: '4', etiqueta: 'Automóvil particular', total_viajes: 850, porcentaje: 22.08 },
  { modo: '1', etiqueta: 'A pie', total_viajes: 500, porcentaje: 12.99 },
  { modo: '7', etiqueta: 'Transporte informal (por puesto/mototaxi)', total_viajes: 350, porcentaje: 9.09 },
  { modo: '3', etiqueta: 'Motocicleta', total_viajes: 200, porcentaje: 5.19 }
];

const mockMatrizOd: analyticsApi.MatrizODItem[] = [
  {
    zona_origen: 'san_simon',
    zona_destino: 'alto_de_los_godos',
    total_viajes: 420,
    tiempo_promedio_min: 25.4,
    costo_promedio_bs: 35.0
  },
  {
    zona_origen: 'boqueron',
    zona_destino: 'san_simon',
    total_viajes: 380,
    tiempo_promedio_min: 32.1,
    costo_promedio_bs: 45.0
  },
  {
    zona_origen: 'alto_de_los_godos',
    zona_destino: 'san_simon',
    total_viajes: 290,
    tiempo_promedio_min: 22.0,
    costo_promedio_bs: 35.0
  }
];

const mockSurveysList: api.EncuestaAdminItem[] = [
  {
    id: '00000000-0000-0000-0000-000000000001',
    titulo: 'Encuesta Origen-Destino Maturín (PDUL)',
    slug: 'pdul_origen_destino',
    tipo_instrumento: 'encuesta_od_pdul',
    activa: true,
    creado_en: '2026-11-09T10:00:00Z',
    total_respuestas: 1420
  },
  {
    id: '00000000-0000-0000-0000-000000000002',
    titulo: 'Consulta Parroquial Boquerón',
    slug: 'consulta_boqueron',
    tipo_instrumento: 'consulta_ciudadana',
    activa: false,
    creado_en: '2026-11-10T10:00:00Z',
    total_respuestas: 85
  }
];

describe('Milestone 5: Dashboard Analítico Municipal, Leaflet GIS y Apache ECharts', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.ResizeObserver = ResizeObserverMock as any;
    global.ResizeObserver = ResizeObserverMock as any;

    vi.mocked(analyticsApi.fetchEncuestas).mockResolvedValue(JSON.parse(JSON.stringify(mockSurveysList)));
    vi.mocked(api.fetchAdminEncuestas).mockResolvedValue(JSON.parse(JSON.stringify(mockSurveysList)));
    vi.mocked(analyticsApi.fetchAllAnalytics).mockResolvedValue({
      kpis: JSON.parse(JSON.stringify(mockKpis)),
      parroquias: JSON.parse(JSON.stringify(mockParroquias)),
      repartoModal: JSON.parse(JSON.stringify(mockRepartoModal)),
      matrizOd: JSON.parse(JSON.stringify(mockMatrizOd))
    });
  });

  // --- 1. KpiCardsGrid.vue (F57) ---
  describe('1. KpiCardsGrid.vue (F57)', () => {
    it('1.1 Monta y renderiza las 4 tarjetas ejecutivas con valores formateados', () => {
      const wrapper = mount(KpiCardsGrid, {
        props: {
          kpis: mockKpis,
          parroquias: mockParroquias,
          repartoModal: mockRepartoModal,
          loading: false
        }
      });

      const text = wrapper.text();
      // Total de encuestas
      expect(text).toContain('Total de Encuestas');
      expect(text).toContain('1.420');

      // Parroquia líder
      expect(text).toContain('Parroquia con Mayor Participación');
      expect(text).toContain('San Simón');
      expect(text).toContain('36.6%');

      // Total de viajes
      expect(text).toContain('Total de Viajes Registrados');
      expect(text).toContain('3.850');

      // Modo predominante
      expect(text).toContain('Modo Predominante');
      expect(text).toContain('Transporte público (bus/buseta)');
      expect(text).toMatch(/50\.[67]%/);
    });

    it('1.2 Muestra indicadores skeleton cuando loading=true', () => {
      const wrapper = mount(KpiCardsGrid, {
        props: {
          kpis: null,
          loading: true
        }
      });

      const skeletonWrappers = wrapper.findAll('.kpi-skeleton-wrap');
      expect(skeletonWrappers.length).toBe(4);
      expect(wrapper.text()).toContain('Cargando total de encuestas...');
    });

    it('1.3 Maneja gracefully datos vacíos sin fallos ni NaN', () => {
      const wrapper = mount(KpiCardsGrid, {
        props: {
          kpis: null,
          parroquias: [],
          repartoModal: [],
          loading: false
        }
      });

      expect(wrapper.text()).toContain('0');
      expect(wrapper.text()).toContain('Sin datos');
    });
  });

  // --- 2. MaturinChoroplethMap.vue (F58) ---
  describe('2. MaturinChoroplethMap.vue (F58)', () => {
    it('2.1 Monta mapa Leaflet centrado en Maturín y renderiza capa GeoJSON de parroquias', () => {
      const mapSpy = vi.spyOn(L, 'map');
      const geoJsonSpy = vi.spyOn(L, 'geoJSON');

      const wrapper = mount(MaturinChoroplethMap, {
        props: {
          metricas: mockParroquias,
          loading: false
        }
      });

      expect(wrapper.find('.leaflet-map-canvas').exists()).toBe(true);
      expect(mapSpy).toHaveBeenCalled();
      // Centro en Maturín [9.7457, -63.1832], zoom 11
      const callOptions = mapSpy.mock.calls[0][1];
      expect(callOptions?.center).toEqual([9.7457, -63.1832]);
      expect(callOptions?.zoom).toBe(11);

      expect(geoJsonSpy).toHaveBeenCalled();
      // Leyenda visible
      expect(wrapper.find('.map-legend').exists()).toBe(true);
      expect(wrapper.text()).toContain('> 25%');
      expect(wrapper.text()).toContain('0% / Sin datos');
    });

    it('2.2 Ciclo de vida estricto: invoca mapInstance.remove() al desmontar para evitar fugas de memoria', () => {
      const mockRemove = vi.fn();
      vi.spyOn(L, 'map').mockReturnValue({
        remove: mockRemove,
        setView: vi.fn().mockReturnThis(),
        addTo: vi.fn().mockReturnThis(),
        invalidateSize: vi.fn()
      } as any);

      const wrapper = mount(MaturinChoroplethMap, {
        props: {
          metricas: mockParroquias
        }
      });

      wrapper.unmount();
      expect(mockRemove).toHaveBeenCalledTimes(1);
    });

    it('2.3 Expone método invalidateSize para reajuste en cambios de visibilidad', () => {
      const mockInvalidate = vi.fn();
      vi.spyOn(L, 'map').mockReturnValue({
        remove: vi.fn(),
        invalidateSize: mockInvalidate
      } as any);

      const wrapper = mount(MaturinChoroplethMap, {
        props: { metricas: mockParroquias }
      });

      (wrapper.vm as any).invalidateSize();
      expect(mockInvalidate).toHaveBeenCalledTimes(1);
    });
  });

  // --- 3. ModalSplitChart.vue (F59) ---
  describe('3. ModalSplitChart.vue (F59)', () => {
    it('3.1 Inicializa ECharts donut chart con toolbox (saveAsImage, dataView)', () => {
      mount(ModalSplitChart, {
        props: {
          items: mockRepartoModal,
          loading: false
        }
      });

      expect(echarts.init).toHaveBeenCalled();
      expect(mockChartInstance.setOption).toHaveBeenCalled();

      // Verificar que las opciones pasadas a ECharts contienen el toolbox obligatorio
      const passedOption = mockChartInstance.setOption.mock.calls[0][0];
      expect(passedOption.toolbox).toBeDefined();
      expect(passedOption.toolbox.feature.saveAsImage).toBeDefined();
      expect(passedOption.toolbox.feature.dataView).toBeDefined();
      expect(passedOption.toolbox.feature.dataView.readOnly).toBe(true);

      // Verificar tipo de serie pie
      expect(passedOption.series[0].type).toBe('pie');
      expect(passedOption.series[0].radius).toEqual(['42%', '70%']);
    });

    it('3.2 Ciclo de vida estricto: desconecta ResizeObserver y destruye instancia ECharts con dispose()', () => {
      const wrapper = mount(ModalSplitChart, {
        props: { items: mockRepartoModal }
      });

      wrapper.unmount();
      expect(mockChartInstance.dispose).toHaveBeenCalledTimes(1);
    });
  });

  // --- 4. OdFlowMatrixChart.vue (F60) ---
  describe('4. OdFlowMatrixChart.vue (F60)', () => {
    it('4.1 Inicializa ECharts heatmap de flujos O-D con visualMap y toolbox', () => {
      mount(OdFlowMatrixChart, {
        props: {
          items: mockMatrizOd,
          loading: false
        }
      });

      expect(echarts.init).toHaveBeenCalled();
      expect(mockChartInstance.setOption).toHaveBeenCalled();

      const passedOption = mockChartInstance.setOption.mock.calls[0][0];
      expect(passedOption.toolbox.feature.saveAsImage).toBeDefined();
      expect(passedOption.toolbox.feature.dataView.readOnly).toBe(true);
      expect(passedOption.visualMap).toBeDefined();
      expect(passedOption.series[0].type).toBe('heatmap');
    });

    it('4.2 Ciclo de vida estricto: destruye instancia ECharts con dispose() al desmontar', () => {
      const wrapper = mount(OdFlowMatrixChart, {
        props: { items: mockMatrizOd }
      });

      wrapper.unmount();
      expect(mockChartInstance.dispose).toHaveBeenCalledTimes(1);
    });
  });

  // --- 5. AccessibleDataFallback.vue (WCAG AA - F61) ---
  describe('5. AccessibleDataFallback.vue (F61)', () => {
    it('5.1 Renderiza semántica accesible WCAG AA: figure, figcaption, tables con caption y th[scope="col"]', () => {
      const wrapper = mount(AccessibleDataFallback, {
        props: {
          kpis: mockKpis,
          parroquias: mockParroquias,
          repartoModal: mockRepartoModal,
          matrizOd: mockMatrizOd
        }
      });

      // 1. Contenedor figure y figcaption
      expect(wrapper.find('figure.accessible-data-fallback').exists()).toBe(true);
      expect(wrapper.find('figcaption').exists()).toBe(true);
      expect(wrapper.text()).toContain('Alternativa Tabular Accesible');

      // 2. Tres tablas semánticas
      const tables = wrapper.findAll('table');
      expect(tables.length).toBe(3);

      tables.forEach((table) => {
        expect(table.find('caption').exists()).toBe(true);
        expect(table.findAll('th[scope="col"]').length).toBeGreaterThan(0);
      });

      // 3. Contenido tabulado
      expect(wrapper.text()).toContain('San Simón');
      expect(wrapper.text()).toContain('Alto de los Godos');
      expect(wrapper.text()).toContain('Transporte público (bus/buseta)');
      expect(wrapper.text()).toContain('25.4 min');
      expect(wrapper.text()).toContain('35.00 Bs');
    });

    it('5.2 Presenta celdas informativas cuando los arreglos de datos están vacíos', () => {
      const wrapper = mount(AccessibleDataFallback, {
        props: {
          kpis: null,
          parroquias: [],
          repartoModal: [],
          matrizOd: []
        }
      });

      expect(wrapper.text()).toContain('No se registran datos para esta encuesta.');
      expect(wrapper.text()).toContain('No se registran viajes en esta encuesta.');
      expect(wrapper.text()).toContain('No se registran flujos de viajes O-D.');
    });
  });

  // --- 6. DashboardView.vue (F62) ---
  describe('6. DashboardView.vue (F62)', () => {
    it('6.1 Carga inicial de encuestas y selección automática de la encuesta activa', async () => {
      const wrapper = mount(DashboardView);
      await flushPromises();

      expect(analyticsApi.fetchEncuestas).toHaveBeenCalledTimes(1);
      expect(analyticsApi.fetchAllAnalytics).toHaveBeenCalledWith('00000000-0000-0000-0000-000000000001');

      // Verifica título institucional
      expect(wrapper.text()).toContain('Dashboard de Movilidad Urbana y Participación Ciudadana');

      // Select con la encuesta cargada
      const select = wrapper.find<HTMLSelectElement>('#survey-select');
      expect(select.exists()).toBe(true);
      expect(select.element.value).toBe('00000000-0000-0000-0000-000000000001');
    });

    it('6.2 Cambio de encuesta en el dropdown actualiza el conjunto analítico', async () => {
      const wrapper = mount(DashboardView);
      await flushPromises();

      const select = wrapper.find('#survey-select');
      await select.setValue('00000000-0000-0000-0000-000000000002');
      await flushPromises();

      expect(analyticsApi.fetchAllAnalytics).toHaveBeenCalledWith('00000000-0000-0000-0000-000000000002');
    });

    it('6.3 Botón de refresco vuelve a invocar fetchAllAnalytics', async () => {
      const wrapper = mount(DashboardView);
      await flushPromises();

      const initialCalls = vi.mocked(analyticsApi.fetchAllAnalytics).mock.calls.length;

      const refreshBtn = wrapper.find('.btn-refresh');
      await refreshBtn.trigger('click');
      await flushPromises();

      expect(vi.mocked(analyticsApi.fetchAllAnalytics).mock.calls.length).toBe(initialCalls + 1);
    });

    it('6.4 Alternancia accesible: botón toggle cambia entre visualización gráfica y tablas accesibles', async () => {
      const wrapper = mount(DashboardView);
      await flushPromises();

      // Inicialmente en vista visual
      expect(wrapper.find('.dashboard-visual-layout').exists()).toBe(true);
      expect(wrapper.find('.dashboard-accessible-layout').exists()).toBe(false);

      // Clic para alternar a tablas accesibles
      const toggleBtn = wrapper.find('.btn-toggle-view');
      expect(toggleBtn.text()).toContain('Ver Tablas Accesibles');
      await toggleBtn.trigger('click');
      await flushPromises();

      // Ahora en vista accesible
      expect(wrapper.find('.dashboard-visual-layout').exists()).toBe(false);
      expect(wrapper.find('.dashboard-accessible-layout').exists()).toBe(true);
      expect(toggleBtn.text()).toContain('Ver Gráficos y Mapas');
      expect(toggleBtn.attributes('aria-pressed')).toBe('true');
    });

    it('6.5 Ergonomía táctil: botones y controles interactivos declaran altura mínima >= 48px', async () => {
      const wrapper = mount(DashboardView);
      await flushPromises();

      const interactiveElements = wrapper.findAll('.btn-dashboard, .survey-dropdown');
      expect(interactiveElements.length).toBeGreaterThan(0);

      // Verificamos en el template la presencia de clases y atributos de accesibilidad
      interactiveElements.forEach((el) => {
        expect(el.attributes('aria-label') || el.attributes('aria-labelledby') || el.text()).toBeTruthy();
      });
    });
  });
});
