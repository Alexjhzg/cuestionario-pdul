import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import AdminResponsesView from '@/views/AdminResponsesView.vue';
import * as api from '@/services/api';
import fs from 'fs';
import path from 'path';

vi.mock('@/services/api', () => ({
  fetchAdminEncuestas: vi.fn(),
  fetchAdminRespuestas: vi.fn()
}));

const mockSurveys: api.EncuestaAdminItem[] = [
  {
    id: '00000000-0000-0000-0000-000000000001',
    titulo: 'Cuestionario Origen-Destino (PDUL Maturín)',
    slug: 'cuestionario-od-maturin',
    tipo_instrumento: 'encuesta_od_pdul',
    activa: true,
    creado_en: '2026-11-09T10:00:00Z',
    total_respuestas: 15
  }
];

const mockRespuestasResponse: api.AdminRespuestasResponse = {
  total: 15,
  skip: 0,
  limit: 10,
  items: [
    {
      id: 1,
      encuesta_id: '00000000-0000-0000-0000-000000000001',
      client_submission_id: '9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d',
      parroquia: 'san_simon',
      zona_od: 'Z-01',
      fecha_registro: '2026-11-10T10:15:30.000Z',
      datos: {
        cedula: '12345678',
        nombre_apellido: 'Juan Perez',
        telefono: '04141234567',
        parroquia: 'san_simon',
        zona_residencia_od: 'Z-01',
        residentes: [
          { numero_persona: 1, sexo: 'M', edad: 35 },
          { numero_persona: 2, sexo: 'F', edad: 32 }
        ],
        viajes: [
          { numero_viaje: 1, modo_principal: '1', costo_bs: 25 },
          { numero_viaje: 2, modo_principal: '1', costo_bs: 25 }
        ]
      }
    },
    {
      id: 2,
      encuesta_id: '00000000-0000-0000-0000-000000000001',
      client_submission_id: '8a2ceb3c-2a6c-3aac-8acc-1a9c6a2cba5c',
      parroquia: 'boqueron',
      zona_od: 'Z-04',
      fecha_registro: '2026-11-10T11:20:00.000Z',
      datos: {
        cedula: '87654321',
        nombre_apellido: 'Maria Gomez',
        parroquia: 'boqueron',
        residentes: [{ numero_persona: 1, sexo: 'F', edad: 28 }],
        viajes: []
      }
    }
  ]
};

describe('AdminResponsesView.vue (Milestone 4)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.fetchAdminEncuestas).mockResolvedValue(JSON.parse(JSON.stringify(mockSurveys)));
    vi.mocked(api.fetchAdminRespuestas).mockResolvedValue(JSON.parse(JSON.stringify(mockRespuestasResponse)));

    // Polyfill portapapeles
    Object.defineProperty(navigator, 'clipboard', {
      value: {
        writeText: vi.fn().mockResolvedValue(undefined)
      },
      writable: true,
      configurable: true
    });
  });

  it('1. Carga inicial: renderiza selector de encuesta, tabla de respuestas y metadatos agregados', async () => {
    const wrapper = mount(AdminResponsesView);
    await flushPromises();

    expect(api.fetchAdminEncuestas).toHaveBeenCalledTimes(1);
    expect(api.fetchAdminRespuestas).toHaveBeenCalledWith('00000000-0000-0000-0000-000000000001', 0, 10);

    // Verificación de filas
    expect(wrapper.find('[data-testid="response-row-1"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="response-row-2"]').exists()).toBe(true);
    expect(wrapper.text()).toContain('San Simón');
    expect(wrapper.text()).toContain('Boquerón');
    expect(wrapper.text()).toContain('Z-01');
    expect(wrapper.text()).toContain('Z-04');
    expect(wrapper.text()).toContain('Página 1 de 2');
  });

  it('2. Protección Estricta de PII en Tabla: Cédula y Nombres NUNCA aparecen en el HTML de la grilla', async () => {
    const wrapper = mount(AdminResponsesView);
    await flushPromises();

    const tableHtml = wrapper.find('.responses-table').html();
    expect(tableHtml).not.toContain('12345678');
    expect(tableHtml).not.toContain('Juan Perez');
    expect(tableHtml).not.toContain('87654321');
    expect(tableHtml).not.toContain('Maria Gomez');
    expect(tableHtml).not.toContain('04141234567');
  });

  it('3. Navegación de Paginación: controla botones Anterior/Siguiente y recalcula skip', async () => {
    const wrapper = mount(AdminResponsesView);
    await flushPromises();

    const prevBtn = wrapper.find('[data-testid="btn-prev-page"]');
    const nextBtn = wrapper.find('[data-testid="btn-next-page"]');

    // En página 1, Anterior debe estar deshabilitado
    expect(prevBtn.attributes('disabled')).toBeDefined();
    expect(nextBtn.attributes('disabled')).toBeUndefined();

    // Avanzar a página 2
    await nextBtn.trigger('click');
    await flushPromises();

    expect(api.fetchAdminRespuestas).toHaveBeenCalledWith('00000000-0000-0000-0000-000000000001', 10, 10);
    expect(wrapper.text()).toContain('Página 2 de 2');
  });

  it('4. Cambio de tamaño de página: recalcula paginación y reinicia a página 1', async () => {
    const wrapper = mount(AdminResponsesView);
    await flushPromises();

    const sizeSelect = wrapper.find('[data-testid="select-page-size"]');
    await sizeSelect.setValue('25');
    await flushPromises();

    expect(api.fetchAdminRespuestas).toHaveBeenCalledWith('00000000-0000-0000-0000-000000000001', 0, 25);
    expect(wrapper.text()).toContain('Página 1 de 1');
  });

  it('5. Modal de Inspección Detallada con Enmascaramiento PII activo por defecto', async () => {
    const wrapper = mount(AdminResponsesView);
    await flushPromises();

    // Clic en "Ver Detalle" de la respuesta #1
    const detailBtn = wrapper.find('[data-testid="btn-detail-1"]');
    await detailBtn.trigger('click');

    const modal = wrapper.find('[role="dialog"]');
    expect(modal.exists()).toBe(true);
    expect(modal.text()).toContain('Detalle de Respuesta #1');

    // El visor de JSON debe mostrar [PROTEGIDO / PII] para cédula, nombre y teléfono
    const jsonViewer = wrapper.find('[data-testid="json-detail-viewer"]');
    expect(jsonViewer.text()).toContain('[PROTEGIDO / PII]');
    expect(jsonViewer.text()).not.toContain('12345678');
    expect(jsonViewer.text()).not.toContain('Juan Perez');
    expect(jsonViewer.text()).not.toContain('04141234567');

    // Desactivar el enmascaramiento para inspección supervisada
    const maskCheckbox = wrapper.find('[data-testid="checkbox-mask-pii"]');
    await maskCheckbox.setValue(false);

    // Ahora los datos sensibles deben ser visibles con advertencia
    expect(jsonViewer.text()).toContain('12345678');
    expect(jsonViewer.text()).toContain('Juan Perez');
    expect(wrapper.find('.pii-warning-banner').exists()).toBe(true);

    // Copiar JSON
    const copyBtn = wrapper.find('[data-testid="btn-copy-json"]');
    await copyBtn.trigger('click');
    expect(navigator.clipboard.writeText).toHaveBeenCalled();

    // Cerrar modal
    const closeBtn = wrapper.find('[data-testid="btn-modal-close"]');
    await closeBtn.trigger('click');
    expect(wrapper.find('[role="dialog"]').exists()).toBe(false);
  });

  it('6. Auditoría de Ergonomía Táctil: botones y controles interactivos declaran min-block-size >= 48px', () => {
    const viewContent = fs.readFileSync(
      path.resolve(__dirname, '../../src/views/AdminResponsesView.vue'),
      'utf-8'
    );

    expect(viewContent).toMatch(/\.survey-select-input\s*\{[^}]*min-block-size:\s*var\(--min-touch-target\);/);
    expect(viewContent).toMatch(/\.page-size-select\s*\{[^}]*min-block-size:\s*var\(--min-touch-target\);/);
    expect(viewContent).toMatch(/\.btn-detail\s*\{[^}]*min-block-size:\s*var\(--min-touch-target\);/);
    expect(viewContent).toMatch(/\.page-btn\s*\{[^}]*min-block-size:\s*var\(--min-touch-target\);/);
    expect(viewContent).toMatch(/\.pii-toggle-label\s*\{[^}]*min-block-size:\s*var\(--min-touch-target\);/);
    expect(viewContent).toMatch(/\.modal-close-btn\s*\{[^}]*min-block-size:\s*var\(--min-touch-target\);/);
  });
});
