import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import fs from 'fs';
import path from 'path';

import AccessibleDataFallback from '@/components/dashboard/AccessibleDataFallback.vue';
import KpiCardsGrid from '@/components/dashboard/KpiCardsGrid.vue';
import DashboardView from '@/views/DashboardView.vue';
import type {
  KpiMetrics,
  ParroquiaResultado,
  RepartoModalItem,
  MatrizODItem
} from '@/services/analyticsApi';

// Mock ECharts & Leaflet for happy-dom
const mockChartInstance = {
  setOption: vi.fn(),
  resize: vi.fn(),
  dispose: vi.fn(),
  clear: vi.fn()
};

vi.mock('echarts', () => ({
  init: vi.fn(() => mockChartInstance)
}));

// Mocks de APIs para DashboardView
const mockSurveys = [
  {
    id: '00000000-0000-0000-0000-000000000001',
    titulo: 'Encuesta Origen-Destino Maturín (PDUL)',
    slug: 'pdul_origen_destino',
    tipo_instrumento: 'encuesta_od_pdul',
    activa: true,
    creado_en: '2026-11-09T10:00:00Z',
    total_respuestas: 1420
  }
];

const mockAnalytics = {
  kpis: {
    total_encuestas: 1420,
    total_viajes: 3850,
    total_residentes: 4980,
    parroquia_lider: 'san_simon'
  },
  parroquias: [
    { parroquia: 'san_simon', total_respuestas: 520, porcentaje: 36.62 },
    { parroquia: 'alto_de_los_godos', total_respuestas: 310, porcentaje: 21.83 },
    { parroquia: 'boqueron', total_respuestas: 240, porcentaje: 16.90 }
  ],
  repartoModal: [
    { modo: '6', etiqueta: 'Transporte público (bus/buseta)', total_viajes: 1950, porcentaje: 50.65 },
    { modo: '4', etiqueta: 'Automóvil particular', total_viajes: 850, porcentaje: 22.08 }
  ],
  matrizOd: [
    {
      zona_origen: 'san_simon',
      zona_destino: 'alto_de_los_godos',
      total_viajes: 420,
      tiempo_promedio_min: 25.4,
      costo_promedio_bs: 35.0
    }
  ]
};

vi.mock('@/services/api', () => ({
  fetchAdminEncuestas: vi.fn().mockImplementation(() => Promise.resolve(mockSurveys)),
  exportarRespuestasAdmin: vi.fn().mockResolvedValue(new Blob(['test'])),
  descargarBlob: vi.fn()
}));

vi.mock('@/services/analyticsApi', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/services/analyticsApi')>();
  return {
    ...actual,
    fetchEncuestas: vi.fn().mockImplementation(() => Promise.resolve(mockSurveys)),
    fetchAllAnalytics: vi.fn().mockImplementation(() => Promise.resolve(mockAnalytics)),
    fetchMetricasCampo: vi.fn().mockResolvedValue({ campo: 'calificacion_servicio_tp', labels: [], values: [] })
  };
});

describe('Challenger M5-2: Auditoría Empírica de Ergonomía Táctil, Responsividad 360px y Fidelidad Accesible', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // =========================================================================
  // 1. AUDITORÍA DE ERGONOMÍA TÁCTIL (OBJETIVOS >= 48px)
  // =========================================================================
  describe('1. Ergonomía Táctil (Objetivos >= 48px)', () => {
    it('1.1 tokens.css y main.css definen formalmente el token --min-touch-target: 48px y 52px en coarse', () => {
      const tokensCssPath = path.resolve(__dirname, '../../src/assets/styles/tokens.css');
      const tokensCss = fs.readFileSync(tokensCssPath, 'utf-8');

      expect(tokensCss).toMatch(/--min-touch-target:\s*48px;/);
      expect(tokensCss).toMatch(/@media\s*\(\s*pointer:\s*coarse\s*\)/);
      expect(tokensCss).toMatch(/--min-touch-target:\s*52px;/);
    });

    it('1.2 DashboardView.vue define altura mínima >= 48px en botones de acción y dropdown', () => {
      const dashboardVuePath = path.resolve(__dirname, '../../src/views/DashboardView.vue');
      const dashboardVue = fs.readFileSync(dashboardVuePath, 'utf-8');

      // Botones de dashboard (.btn-dashboard)
      expect(dashboardVue).toMatch(/\.btn-dashboard\s*\{[^}]*min-height:\s*var\(--min-touch-target\)/s);
      expect(dashboardVue).toMatch(/\.btn-dashboard\s*\{[^}]*min-block-size:\s*var\(--min-touch-target\)/s);

      // Selector de encuesta (.survey-dropdown)
      expect(dashboardVue).toMatch(/\.survey-dropdown\s*\{[^}]*min-height:\s*var\(--min-touch-target\)/s);

      // Botón de reintento (.btn-retry)
      expect(dashboardVue).toMatch(/\.btn-retry\s*\{[^}]*min-height:\s*var\(--min-touch-target\)/s);
    });

    it('1.3 KpiCardsGrid.vue garantiza min-height o min-block-size >= 48px en tarjetas e iconos', () => {
      const kpisVuePath = path.resolve(__dirname, '../../src/components/dashboard/KpiCardsGrid.vue');
      const kpisVue = fs.readFileSync(kpisVuePath, 'utf-8');

      // Tarjeta KPI
      expect(kpisVue).toMatch(/\.kpi-card\s*\{[^}]*min-block-size:\s*var\(--min-touch-target\)/s);
      // Header y contenedores de icono
      expect(kpisVue).toMatch(/\.kpi-header\s*\{[^}]*min-height:\s*var\(--min-touch-target\)/s);
      expect(kpisVue).toMatch(/\.kpi-icon-wrap\s*\{[^}]*min-width:\s*var\(--min-touch-target\)/s);
      expect(kpisVue).toMatch(/\.kpi-icon-wrap\s*\{[^}]*min-height:\s*var\(--min-touch-target\)/s);
    });

    it('1.4 Los elementos interactivos montados en DashboardView poseen clases que activan min-height >= 48px', async () => {
      const wrapper = mount(DashboardView);
      await flushPromises();

      const refreshBtn = wrapper.find('.btn-refresh');
      const toggleBtn = wrapper.find('.btn-toggle-view');
      const exportBtn = wrapper.find('.btn-export');
      const surveyDropdown = wrapper.find('.survey-dropdown');

      expect(refreshBtn.exists()).toBe(true);
      expect(refreshBtn.classes()).toContain('btn-dashboard');

      expect(toggleBtn.exists()).toBe(true);
      expect(toggleBtn.classes()).toContain('btn-dashboard');

      expect(exportBtn.exists()).toBe(true);
      expect(exportBtn.classes()).toContain('btn-dashboard');

      expect(surveyDropdown.exists()).toBe(true);
      expect(surveyDropdown.classes()).toContain('survey-dropdown');
    });
  });

  // =========================================================================
  // 2. RESPONSIVIDAD EN VIEWPORTS MÓVILES DE 360px (SIN DESBORDAMIENTO HORIZONTAL)
  // =========================================================================
  describe('2. Responsividad en Viewports Móviles de 360px', () => {
    it('2.1 KpiCardsGrid usa minmax(260px, 1fr) que entra holgadamente en el ancho disponible de 360px (328px neto)', () => {
      const kpisVuePath = path.resolve(__dirname, '../../src/components/dashboard/KpiCardsGrid.vue');
      const kpisVue = fs.readFileSync(kpisVuePath, 'utf-8');

      expect(kpisVue).toMatch(/grid-template-columns:\s*repeat\(auto-fit,\s*minmax\(260px,\s*1fr\)\);/);
      // 360px - 32px (padding 16px lateral) = 328px disponible. 260px < 328px -> Columna única sin desborde.
    });

    it('2.2 DashboardView.vue aplica reglas @media (max-width: 768px) para adaptar controles a 100% de ancho', () => {
      const dashboardVuePath = path.resolve(__dirname, '../../src/views/DashboardView.vue');
      const dashboardVue = fs.readFileSync(dashboardVuePath, 'utf-8');

      expect(dashboardVue).toMatch(/@media\s*\(max-width:\s*768px\)/);
      expect(dashboardVue).toMatch(/\.control-group\s*\{[^}]*min-width:\s*100%/s);
      expect(dashboardVue).toMatch(/\.action-buttons\s*\{[^}]*width:\s*100%/s);
      expect(dashboardVue).toMatch(/\.btn-dashboard\s*\{[^}]*flex:\s*1/s);
    });

    it('2.3 AccessibleDataFallback.vue contiene .table-section con overflow-x: auto evitando scroll horizontal del documento', () => {
      const fallbackVuePath = path.resolve(__dirname, '../../src/components/dashboard/AccessibleDataFallback.vue');
      const fallbackVue = fs.readFileSync(fallbackVuePath, 'utf-8');

      expect(fallbackVue).toMatch(/\.table-section\s*\{[^}]*overflow-x:\s*auto;/s);
    });

    it('2.4 KpiCardsGrid.vue declara word-break: break-word en valores KPI para evitar desborde con cifras grandes', () => {
      const kpisVuePath = path.resolve(__dirname, '../../src/components/dashboard/KpiCardsGrid.vue');
      const kpisVue = fs.readFileSync(kpisVuePath, 'utf-8');

      expect(kpisVue).toMatch(/\.kpi-value\s*\{[^}]*word-break:\s*break-word;/s);
    });
  });

  // =========================================================================
  // 3. FIDELIDAD Y PARIDAD DE DATOS EN AccessibleDataFallback.vue
  // =========================================================================
  describe('3. Fidelidad y Paridad de Datos en AccessibleDataFallback.vue', () => {
    const kpisPrueba: KpiMetrics = {
      total_encuestas: 2450,
      total_viajes: 6120,
      total_residentes: 8340,
      parroquia_lider: 'alto_de_los_godos'
    };

    const parroquiasPrueba: ParroquiaResultado[] = [
      { parroquia: 'alto_de_los_godos', total_respuestas: 1100, porcentaje: 44.90 },
      { parroquia: 'san_simon', total_respuestas: 850, porcentaje: 34.69 },
      { parroquia: 'boqueron', total_respuestas: 500, porcentaje: 20.41 }
    ];

    const repartoModalPrueba: RepartoModalItem[] = [
      { modo: '6', etiqueta: 'Transporte público (bus/buseta)', total_viajes: 3672, porcentaje: 60.00 },
      { modo: '4', etiqueta: 'Automóvil particular', total_viajes: 1530, porcentaje: 25.00 },
      { modo: '1', etiqueta: 'A pie', total_viajes: 918, porcentaje: 15.00 }
    ];

    const matrizOdPrueba: MatrizODItem[] = [
      {
        zona_origen: 'alto_de_los_godos',
        zona_destino: 'san_simon',
        total_viajes: 2400,
        tiempo_promedio_min: 28.5,
        costo_promedio_bs: 40.0
      },
      {
        zona_origen: 'boqueron',
        zona_destino: 'san_simon',
        total_viajes: 1800,
        tiempo_promedio_min: 35.0,
        costo_promedio_bs: null // Caso sin costo reportado
      }
    ];

    it('3.1 Fidelidad de Indicadores Ejecutivos (KPIs): coincidencia exacta de cifras y nombres', () => {
      const wrapper = mount(AccessibleDataFallback, {
        props: {
          kpis: kpisPrueba,
          parroquias: parroquiasPrueba,
          repartoModal: repartoModalPrueba,
          matrizOd: matrizOdPrueba
        }
      });

      const summaryBox = wrapper.find('.accessible-summary-box');
      expect(summaryBox.exists()).toBe(true);

      const text = summaryBox.text();
      expect(text).toContain('2.450'); // total_encuestas con separador es-VE
      expect(text).toContain('6.120'); // total_viajes
      expect(text).toContain('8.340'); // total_residentes
      expect(text).toContain('Alto de los Godos'); // formato canónico de parroquia
    });

    it('3.2 Fidelidad de Tabla 1 (Parroquias): nombres canónicos, conteos, porcentajes y suma acumulada en tfoot', () => {
      const wrapper = mount(AccessibleDataFallback, {
        props: {
          kpis: kpisPrueba,
          parroquias: parroquiasPrueba,
          repartoModal: repartoModalPrueba,
          matrizOd: matrizOdPrueba
        }
      });

      const table = wrapper.findAll('.accessible-table')[0];
      expect(table.exists()).toBe(true);

      // Verificar cabeceras y filas de datos
      const rows = table.findAll('tbody tr');
      expect(rows).toHaveLength(3);

      // Fila 1: Alto de los Godos
      expect(rows[0].find('th[scope="row"]').text()).toBe('Alto de los Godos');
      expect(rows[0].findAll('td')[0].text()).toBe('1.100');
      expect(rows[0].findAll('td')[1].text()).toBe('44.90%');

      // Fila 2: San Simón
      expect(rows[1].find('th[scope="row"]').text()).toBe('San Simón');
      expect(rows[1].findAll('td')[0].text()).toBe('850');
      expect(rows[1].findAll('td')[1].text()).toBe('34.69%');

      // Fila 3: Boquerón
      expect(rows[2].find('th[scope="row"]').text()).toBe('Boquerón');
      expect(rows[2].findAll('td')[0].text()).toBe('500');
      expect(rows[2].findAll('td')[1].text()).toBe('20.41%');

      // Pie de tabla tfoot: suma acumulada exacta (1100 + 850 + 500 = 2450)
      const tfoot = table.find('tfoot');
      expect(tfoot.exists()).toBe(true);
      expect(tfoot.text()).toContain('Total Acumulado');
      expect(tfoot.text()).toContain('2.450');
      expect(tfoot.text()).toContain('100.00%');
    });

    it('3.3 Fidelidad de Tabla 2 (Reparto Modal): etiquetas, conteos y porcentaje exacto', () => {
      const wrapper = mount(AccessibleDataFallback, {
        props: {
          kpis: kpisPrueba,
          parroquias: parroquiasPrueba,
          repartoModal: repartoModalPrueba,
          matrizOd: matrizOdPrueba
        }
      });

      const table = wrapper.findAll('.accessible-table')[1];
      expect(table.exists()).toBe(true);

      const rows = table.findAll('tbody tr');
      expect(rows).toHaveLength(3);

      expect(rows[0].find('th[scope="row"]').text()).toBe('Transporte público (bus/buseta)');
      expect(rows[0].findAll('td')[0].text()).toBe('3.672');
      expect(rows[0].findAll('td')[1].text()).toBe('60.00%');

      // Pie de tabla tfoot: suma de viajes (3672 + 1530 + 918 = 6120)
      const tfoot = table.find('tfoot');
      expect(tfoot.exists()).toBe(true);
      expect(tfoot.text()).toContain('Total de Viajes');
      expect(tfoot.text()).toContain('6.120');
      expect(tfoot.text()).toContain('100.00%');
    });

    it('3.4 Fidelidad de Tabla 3 (Matriz O-D): zonas de origen y destino, tiempos, costos y fallback N/D', () => {
      const wrapper = mount(AccessibleDataFallback, {
        props: {
          kpis: kpisPrueba,
          parroquias: parroquiasPrueba,
          repartoModal: repartoModalPrueba,
          matrizOd: matrizOdPrueba
        }
      });

      const table = wrapper.findAll('.accessible-table')[2];
      expect(table.exists()).toBe(true);

      const rows = table.findAll('tbody tr');
      expect(rows).toHaveLength(2);

      // Fila 1: Con costo y tiempo numéricos
      expect(rows[0].find('th[scope="row"]').text()).toBe('Alto de los Godos');
      expect(rows[0].findAll('td')[0].text()).toBe('San Simón');
      expect(rows[0].findAll('td')[1].text()).toBe('2.400');
      expect(rows[0].findAll('td')[2].text()).toBe('28.5 min');
      expect(rows[0].findAll('td')[3].text()).toBe('40.00 Bs');

      // Fila 2: Con costo null -> 'N/D'
      expect(rows[1].find('th[scope="row"]').text()).toBe('Boquerón');
      expect(rows[1].findAll('td')[0].text()).toBe('San Simón');
      expect(rows[1].findAll('td')[1].text()).toBe('1.800');
      expect(rows[1].findAll('td')[2].text()).toBe('35.0 min');
      expect(rows[1].findAll('td')[3].text()).toBe('N/D');

      // Footer totalizador: 2400 + 1800 = 4200
      const tfoot = table.find('tfoot');
      expect(tfoot.exists()).toBe(true);
      expect(tfoot.text()).toContain('Total General de Flujos');
      expect(tfoot.text()).toContain('4.200');
    });

    it('3.5 Resiliencia ante datos vacíos o nulos sin lanzar excepciones', () => {
      const wrapper = mount(AccessibleDataFallback, {
        props: {
          kpis: null,
          parroquias: [],
          repartoModal: [],
          matrizOd: []
        }
      });

      // No debe existir el resumen de KPIs si kpis es null
      expect(wrapper.find('.accessible-summary-box').exists()).toBe(false);

      // Las 3 tablas deben mostrar celdas vacías informativas
      const tables = wrapper.findAll('.accessible-table');
      expect(tables).toHaveLength(3);

      expect(tables[0].text()).toContain('No se registran datos para esta encuesta.');
      expect(tables[1].text()).toContain('No se registran viajes en esta encuesta.');
      expect(tables[2].text()).toContain('No se registran flujos de viajes O-D.');

      // Ningún tfoot debe renderizarse con listas vacías
      expect(wrapper.findAll('tfoot')).toHaveLength(0);
    });

    it('3.6 Paridad estricta entre métricas de AccessibleDataFallback y KpiCardsGrid', () => {
      const fallbackWrapper = mount(AccessibleDataFallback, {
        props: {
          kpis: kpisPrueba,
          parroquias: parroquiasPrueba,
          repartoModal: repartoModalPrueba,
          matrizOd: matrizOdPrueba
        }
      });

      const kpisWrapper = mount(KpiCardsGrid, {
        props: {
          kpis: kpisPrueba,
          parroquias: parroquiasPrueba,
          repartoModal: repartoModalPrueba,
          matrizOd: matrizOdPrueba,
          loading: false
        }
      });

      const fallbackText = fallbackWrapper.text();
      const kpisText = kpisWrapper.text();

      // Mismos totales clave reflejados
      expect(fallbackText).toContain('2.450');
      expect(kpisText).toContain('2.450');

      expect(fallbackText).toContain('6.120');
      expect(kpisText).toContain('6.120');

      expect(fallbackText).toContain('Alto de los Godos');
      expect(kpisText).toContain('Alto de los Godos');
    });
  });

  // =========================================================================
  // 4. NAVEGACIÓN DE TECLADO Y ALTERNANCIA ACCESIBLE DE VISTAS
  // =========================================================================
  describe('4. Navegación de Teclado y Alternancia Accesible', () => {
    it('4.1 Botón toggle en DashboardView gestiona correctamente aria-pressed y etiquetas accesibles', async () => {
      const wrapper = mount(DashboardView);
      await flushPromises();

      const toggleBtn = wrapper.find('.btn-toggle-view');
      expect(toggleBtn.exists()).toBe(true);

      // Estado inicial: visual activo
      expect(toggleBtn.attributes('aria-pressed')).toBe('false');
      expect(toggleBtn.attributes('aria-label')).toBe('Cambiar a modo de vista tabular accesible');
      expect(toggleBtn.text()).toContain('Ver Tablas Accesibles');
      expect(wrapper.find('.dashboard-visual-layout').exists()).toBe(true);
      expect(wrapper.find('.dashboard-accessible-layout').exists()).toBe(false);

      // Disparo de evento click (accesible con Enter o Espacio en HTML)
      await toggleBtn.trigger('click');
      await flushPromises();

      // Estado alternado: accesible activo
      expect(toggleBtn.attributes('aria-pressed')).toBe('true');
      expect(toggleBtn.attributes('aria-label')).toBe('Cambiar a modo de gráficos interactivos');
      expect(toggleBtn.text()).toContain('Ver Gráficos y Mapas');
      expect(wrapper.find('.dashboard-visual-layout').exists()).toBe(false);
      expect(wrapper.find('.dashboard-accessible-layout').exists()).toBe(true);

      // Segundo click: regresa al modo visual
      await toggleBtn.trigger('click');
      await flushPromises();

      expect(toggleBtn.attributes('aria-pressed')).toBe('false');
      expect(wrapper.find('.dashboard-visual-layout').exists()).toBe(true);
      expect(wrapper.find('.dashboard-accessible-layout').exists()).toBe(false);
    });

    it('4.2 Estructura semántica WCAG AA en AccessibleDataFallback: figure, figcaption, captions e ids', () => {
      const wrapper = mount(AccessibleDataFallback);

      const figure = wrapper.find('figure.accessible-data-fallback');
      expect(figure.exists()).toBe(true);
      expect(figure.attributes('role')).toBe('region');
      expect(figure.attributes('aria-label')).toBeTruthy();

      const figcaption = wrapper.find('figcaption.accessible-caption');
      expect(figcaption.exists()).toBe(true);

      // Verificación de los 3 captions en las tablas
      const captions = wrapper.findAll('caption');
      expect(captions).toHaveLength(3);
      expect(captions[0].attributes('id')).toBe('table-parroquias-caption');
      expect(captions[1].attributes('id')).toBe('table-modal-caption');
      expect(captions[2].attributes('id')).toBe('table-od-caption');
    });

    it('4.3 Barra de controles del dashboard expone role="toolbar" para navegación por pestañas de teclado', async () => {
      const wrapper = mount(DashboardView);
      await flushPromises();

      const toolbar = wrapper.find('[role="toolbar"]');
      expect(toolbar.exists()).toBe(true);
      expect(toolbar.attributes('aria-label')).toBe('Controles del dashboard');
    });

    it('4.4 Encabezados y celdas de AccessibleDataFallback usan atributos de alcance scope="col" y scope="row"', () => {
      const wrapper = mount(AccessibleDataFallback, {
        props: {
          parroquias: [{ parroquia: 'san_simon', total_respuestas: 10, porcentaje: 100 }]
        }
      });

      const thCol = wrapper.findAll('th[scope="col"]');
      expect(thCol.length).toBeGreaterThanOrEqual(3);

      const thRow = wrapper.find('tbody th[scope="row"]');
      expect(thRow.exists()).toBe(true);
      expect(thRow.text()).toBe('San Simón');
    });
  });
});
