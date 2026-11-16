import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import AdminSurveyListView from '@/views/AdminSurveyListView.vue';
import * as api from '@/services/api';

vi.mock('@/services/api', () => ({
  fetchAdminEncuestas: vi.fn(),
  updateEncuestaEstado: vi.fn(),
  toggleAdminEncuestaEstado: vi.fn(),
  exportarRespuestasAdmin: vi.fn(),
  descargarBlob: vi.fn(),
  triggerBlobDownload: vi.fn()
}));

const mockSurveys: api.EncuestaAdminItem[] = [
  {
    id: '00000000-0000-0000-0000-000000000001',
    titulo: 'Cuestionario Origen-Destino (PDUL Maturín)',
    slug: 'cuestionario-od-maturin',
    tipo_instrumento: 'encuesta_od_pdul',
    activa: true,
    creado_en: '2026-11-09T12:00:00Z',
    total_respuestas: 142
  },
  {
    id: '00000000-0000-0000-0000-000000000002',
    titulo: 'Consulta Ciudadana Parroquia Boquerón',
    slug: 'consulta-boqueron-2026',
    tipo_instrumento: 'consulta_ciudadana',
    activa: false,
    creado_en: '2026-11-10T08:30:00Z',
    total_respuestas: 28
  }
];

describe('AdminSurveyListView.vue (Milestone 4)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.fetchAdminEncuestas).mockResolvedValue(JSON.parse(JSON.stringify(mockSurveys)));
    vi.mocked(api.updateEncuestaEstado).mockImplementation(async (id, activa) => ({
      id,
      titulo: 'Encuesta Mock',
      slug: 'mock-slug',
      tipo_instrumento: 'consulta_ciudadana',
      creado_en: '2026-11-10T12:00:00Z',
      activa,
      esquema_formio: {}
    }));
    vi.mocked(api.exportarRespuestasAdmin).mockResolvedValue(new Blob(['mock-data']));
  });

  it('1. Carga inicial: renderiza títulos, slugs, badges de tipo y conteo de respuestas', async () => {
    const wrapper = mount(AdminSurveyListView);
    await flushPromises();

    expect(api.fetchAdminEncuestas).toHaveBeenCalledTimes(1);
    expect(wrapper.text()).toContain('Cuestionario Origen-Destino (PDUL Maturín)');
    expect(wrapper.text()).toContain('cuestionario-od-maturin');
    expect(wrapper.text()).toContain('Consulta Ciudadana Parroquia Boquerón');
    expect(wrapper.text()).toContain('142');
    expect(wrapper.text()).toContain('28');
  });

  it('2. Alternancia activa -> inactiva: solicita confirmación modal antes de desactivar', async () => {
    const wrapper = mount(AdminSurveyListView);
    await flushPromises();

    // La primera encuesta está activa
    const switchBtn = wrapper.find('[data-testid="switch-status-00000000-0000-0000-0000-000000000001"]');
    expect(switchBtn.exists()).toBe(true);
    expect(switchBtn.attributes('aria-checked')).toBe('true');

    // Clic en switch para desactivar
    await switchBtn.trigger('click');

    // Debe abrirse el diálogo modal de confirmación
    expect(wrapper.find('[role="dialog"]').exists()).toBe(true);
    expect(wrapper.text()).toContain('¿Desactivar Encuesta?');
    expect(wrapper.text()).toContain('Cuestionario Origen-Destino (PDUL Maturín)');

    // Cancelar
    const cancelBtn = wrapper.find('[data-testid="btn-cancel-deactivation"]');
    await cancelBtn.trigger('click');
    expect(wrapper.find('[role="dialog"]').exists()).toBe(false);
    expect(api.updateEncuestaEstado).not.toHaveBeenCalled();

    // Reintentar y confirmar
    await switchBtn.trigger('click');
    const confirmBtn = wrapper.find('[data-testid="btn-confirm-deactivation"]');
    await confirmBtn.trigger('click');
    await flushPromises();

    expect(api.updateEncuestaEstado).toHaveBeenCalledWith('00000000-0000-0000-0000-000000000001', false);
    expect(switchBtn.attributes('aria-checked')).toBe('false');
  });

  it('3. Alternancia inactiva -> activa: reactiva directamente sin modal de confirmación', async () => {
    const wrapper = mount(AdminSurveyListView);
    await flushPromises();

    // La segunda encuesta está inactiva
    const switchBtn = wrapper.find('[data-testid="switch-status-00000000-0000-0000-0000-000000000002"]');
    expect(switchBtn.exists()).toBe(true);
    expect(switchBtn.attributes('aria-checked')).toBe('false');

    await switchBtn.trigger('click');
    await flushPromises();

    // No abre modal
    expect(wrapper.find('[role="dialog"]').exists()).toBe(false);
    expect(api.updateEncuestaEstado).toHaveBeenCalledWith('00000000-0000-0000-0000-000000000002', true);
    expect(switchBtn.attributes('aria-checked')).toBe('true');
  });

  it('4. Disparadores de exportación CSV y JSON con respeto al toggle de anonimización PII', async () => {
    const wrapper = mount(AdminSurveyListView);
    await flushPromises();

    // Exportar CSV con redactPii = true (defecto)
    const exportCsvBtn = wrapper.find('[data-testid="btn-export-csv-00000000-0000-0000-0000-000000000001"]');
    await exportCsvBtn.trigger('click');
    await flushPromises();

    expect(api.exportarRespuestasAdmin).toHaveBeenCalledWith(
      '00000000-0000-0000-0000-000000000001',
      'csv',
      true
    );
    expect(api.descargarBlob).toHaveBeenCalledTimes(1);

    // Desmarcar el checkbox de PII
    const piiCheckbox = wrapper.find('[data-testid="checkbox-redact-pii"]');
    await piiCheckbox.setValue(false);

    // Exportar JSON con redactPii = false
    const exportJsonBtn = wrapper.find('[data-testid="btn-export-json-00000000-0000-0000-0000-000000000001"]');
    await exportJsonBtn.trigger('click');
    await flushPromises();

    expect(api.exportarRespuestasAdmin).toHaveBeenCalledWith(
      '00000000-0000-0000-0000-000000000001',
      'json',
      false
    );
    expect(api.descargarBlob).toHaveBeenCalledTimes(2);
  });

  it('5. Eventos de navegación: emite create-survey, view-responses y edit-survey', async () => {
    const wrapper = mount(AdminSurveyListView);
    await flushPromises();

    // Botón "+ Nueva Encuesta"
    const newSurveyBtn = wrapper.find('[data-testid="btn-create-new-survey"]');
    await newSurveyBtn.trigger('click');
    expect(wrapper.emitted('create-survey')).toHaveLength(1);

    // Botón "Respuestas"
    const viewBtn = wrapper.find('[data-testid="btn-view-responses-00000000-0000-0000-0000-000000000001"]');
    await viewBtn.trigger('click');
    expect(wrapper.emitted('view-responses')?.[0]).toEqual(['00000000-0000-0000-0000-000000000001']);

    // Botón "Constructor"
    const editBtn = wrapper.find('[data-testid="btn-edit-survey-00000000-0000-0000-0000-000000000001"]');
    await editBtn.trigger('click');
    expect(wrapper.emitted('edit-survey')?.[0]).toEqual(['00000000-0000-0000-0000-000000000001']);
  });

  it('6. Auditoría de Ergonomía Táctil: botones y controles declaran min-block-size >= 48px', () => {
    const fs = require('fs');
    const path = require('path');
    const viewContent = fs.readFileSync(
      path.resolve(__dirname, '../../src/views/AdminSurveyListView.vue'),
      'utf-8'
    );

    // Verificar que los botones de acción usan min-block-size var(--min-touch-target)
    expect(viewContent).toMatch(/\.admin-btn\s*\{[^}]*min-block-size:\s*var\(--min-touch-target\);/);
    expect(viewContent).toMatch(/\.action-btn\s*\{[^}]*min-block-size:\s*var\(--min-touch-target\);/);
    expect(viewContent).toMatch(/\.pii-export-control\s*\{[^}]*min-block-size:\s*var\(--min-touch-target\);/);
  });
});
