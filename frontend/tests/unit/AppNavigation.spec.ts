import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import App from '@/App.vue';
import fs from 'fs';
import path from 'path';

// Mock de APIs para evitar llamadas de red reales durante pruebas de navegación
vi.mock('@/services/api', () => ({
  fetchEncuesta: vi.fn().mockResolvedValue({
    id: '00000000-0000-0000-0000-000000000001',
    titulo: 'Encuesta Mock',
    slug: 'pdul_origen_destino',
    activa: true,
    esquema_formio: { display: 'form', components: [] }
  }),
  fetchAdminEncuestas: vi.fn().mockResolvedValue([
    {
      id: '00000000-0000-0000-0000-000000000001',
      titulo: 'Encuesta PDUL Maturín',
      slug: 'pdul_origen_destino',
      tipo_instrumento: 'encuesta_od_pdul',
      activa: true,
      creado_en: '2026-11-10T10:00:00Z',
      total_respuestas: 50
    }
  ]),
  fetchAdminRespuestas: vi.fn().mockResolvedValue({
    total: 50,
    skip: 0,
    limit: 10,
    items: []
  }),
  updateEncuestaEstado: vi.fn(),
  exportarRespuestasAdmin: vi.fn(),
  descargarBlob: vi.fn(),
  triggerBlobDownload: vi.fn()
}));

// Mock de Formio para evitar carga de DOM pesada en pruebas de navegación
vi.mock('@formio/js', () => ({
  Formio: {
    builder: vi.fn().mockResolvedValue({
      on: vi.fn(),
      off: vi.fn(),
      destroy: vi.fn(),
      setForm: vi.fn(),
      schema: { display: 'form', components: [] }
    }),
    setBaseUrl: vi.fn(),
    setProjectUrl: vi.fn(),
    cdn: { setBaseUrl: vi.fn() }
  }
}));

describe('App.vue Navigation & WAI-ARIA Tabs (Milestone 4)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('1. Estructura semántica WAI-ARIA: existe <nav>, role="tablist" y 5 pestañas accesibles', () => {
    const wrapper = mount(App);

    const nav = wrapper.find('nav[role="navigation"]');
    expect(nav.exists()).toBe(true);
    expect(nav.attributes('aria-label')).toBe('Navegación principal');

    const tablist = nav.find('[role="tablist"]');
    expect(tablist.exists()).toBe(true);

    const tabs = tablist.findAll('[role="tab"]');
    expect(tabs).toHaveLength(5);

    // Comprobar IDs y controles
    const expectedTabs = [
      { id: 'tab-gis-dashboard', controls: 'panel-gis-dashboard', label: 'Dashboard Analítico' },
      { id: 'tab-admin-surveys', controls: 'panel-admin-surveys', label: 'Gestión de Encuestas' },
      { id: 'tab-admin-responses', controls: 'panel-admin-responses', label: 'Respuestas Ciudadanas' },
      { id: 'tab-form-builder', controls: 'panel-form-builder', label: 'Constructor de Encuestas' },
      { id: 'tab-survey-fill', controls: 'panel-survey-fill', label: 'Llenar Encuesta PDUL' }
    ];

    expectedTabs.forEach((exp, idx) => {
      const tab = tabs[idx];
      expect(tab.attributes('id')).toBe(exp.id);
      expect(tab.attributes('aria-controls')).toBe(exp.controls);
      expect(tab.text()).toContain(exp.label);
    });
  });

  it('2. Estado inicial: Dashboard Analítico está activo por defecto en modo admin', () => {
    const wrapper = mount(App);

    const activeTab = wrapper.find('#tab-gis-dashboard');
    expect(activeTab.attributes('aria-selected')).toBe('true');
    expect(activeTab.attributes('tabindex')).toBe('0');
    expect(activeTab.classes()).toContain('active');

    // Las demás inactivas
    const otherTabs = wrapper.findAll('[role="tab"]').filter((t) => t.attributes('id') !== 'tab-gis-dashboard');
    otherTabs.forEach((tab) => {
      expect(tab.attributes('aria-selected')).toBe('false');
      expect(tab.attributes('tabindex')).toBe('-1');
      expect(tab.classes()).not.toContain('active');
    });

    // Panel activo visible
    expect(wrapper.find('#panel-gis-dashboard').exists()).toBe(true);
  });

  it('3. Navegación entre vistas: el clic en pestañas actualiza aria-selected y monta la vista correspondiente', async () => {
    const wrapper = mount(App);

    // 1. Clic en "Constructor de Encuestas"
    const builderTab = wrapper.find('#tab-form-builder');
    await builderTab.trigger('click');
    await flushPromises();

    expect(builderTab.attributes('aria-selected')).toBe('true');
    expect(wrapper.find('#panel-form-builder').exists()).toBe(true);
    expect(wrapper.find('#tab-gis-dashboard').attributes('aria-selected')).toBe('false');

    // 2. Clic en "Gestión de Encuestas"
    const surveysTab = wrapper.find('#tab-admin-surveys');
    await surveysTab.trigger('click');
    await flushPromises();

    expect(surveysTab.attributes('aria-selected')).toBe('true');
    expect(wrapper.find('#panel-admin-surveys').exists()).toBe(true);

    // 3. Clic en "Respuestas Ciudadanas"
    const responsesTab = wrapper.find('#tab-admin-responses');
    await responsesTab.trigger('click');
    await flushPromises();

    expect(responsesTab.attributes('aria-selected')).toBe('true');
    expect(wrapper.find('#panel-admin-responses').exists()).toBe(true);

    // 4. Clic en "Llenar Encuesta PDUL"
    const surveyTab = wrapper.find('#tab-survey-fill');
    await surveyTab.trigger('click');
    await flushPromises();

    expect(surveyTab.attributes('aria-selected')).toBe('true');
    expect(wrapper.find('#panel-survey-fill').exists()).toBe(true);

    // 5. Clic de vuelta a "Dashboard Analítico"
    const dashboardTab = wrapper.find('#tab-gis-dashboard');
    await dashboardTab.trigger('click');
    await flushPromises();

    expect(dashboardTab.attributes('aria-selected')).toBe('true');
    expect(wrapper.find('#panel-gis-dashboard').exists()).toBe(true);
    expect(wrapper.text()).toContain('Dashboard Analítico');
    expect(wrapper.text()).toContain('PDUL');
  });

  it('4. Flujo inter-vistas: comunicación reactiva mediante eventos entre paneles', async () => {
    const wrapper = mount(App);

    // Ir a Gestión de Encuestas
    await wrapper.find('#tab-admin-surveys').trigger('click');
    await flushPromises();

    const adminSurveysComponent = wrapper.findComponent({ name: 'AdminSurveyListView' });
    expect(adminSurveysComponent.exists()).toBe(true);

    // Simular evento edit-survey emitido por la vista
    adminSurveysComponent.vm.$emit('edit-survey', '00000000-0000-0000-0000-000000000001');
    await flushPromises();

    // Debe cambiar a la pestaña form-builder
    expect(wrapper.find('#tab-form-builder').attributes('aria-selected')).toBe('true');
    expect(wrapper.find('#panel-form-builder').exists()).toBe(true);

    // Volver a Gestión y simular view-responses
    await wrapper.find('#tab-admin-surveys').trigger('click');
    await flushPromises();

    const adminSurveys2 = wrapper.findComponent({ name: 'AdminSurveyListView' });
    adminSurveys2.vm.$emit('view-responses', '00000000-0000-0000-0000-000000000001');
    await flushPromises();

    // Debe cambiar a la pestaña admin-responses
    expect(wrapper.find('#tab-admin-responses').attributes('aria-selected')).toBe('true');
    expect(wrapper.find('#panel-admin-responses').exists()).toBe(true);
  });

  it('5. Auditoría de Ergonomía Táctil y Ausencia de Tailwind/PrimeFlex', () => {
    const appPath = path.resolve(__dirname, '../../src/App.vue');
    const content = fs.readFileSync(appPath, 'utf-8');

    // Botones de navegación con min-block-size y min-height >= 48px
    expect(content).toMatch(/\.nav-tab-btn\s*\{[^}]*min-block-size:\s*var\(--min-touch-target\);/);
    expect(content).toMatch(/\.nav-tab-btn\s*\{[^}]*min-height:\s*var\(--min-touch-target\);/);

    // Scroll horizontal en contenedor móvil
    expect(content).toMatch(/\.nav-inner\s*\{[^}]*overflow-x:\s*auto;/);

    // Ausencia total de Tailwind CSS y PrimeFlex
    expect(content).not.toMatch(/@tailwind/);
    expect(content).not.toMatch(/primeflex/i);
    expect(content).not.toContain('flex-row');
    expect(content).not.toContain('p-button');
    expect(content).not.toContain('w-full');
  });
});
