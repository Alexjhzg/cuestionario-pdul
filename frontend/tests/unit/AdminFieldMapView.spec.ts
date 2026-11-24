import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import fs from 'fs';
import path from 'path';
import AdminFieldMapView from '@/views/AdminFieldMapView.vue';
import * as api from '@/services/api';

vi.mock('@/services/api', async () => {
  const actual = await vi.importActual<typeof import('@/services/api')>('@/services/api');
  return {
    ...actual,
    fetchAdminEncuestas: vi.fn().mockResolvedValue([
      {
        id: '00000000-0000-0000-0000-000000000001',
        titulo: 'Encuesta PDUL Maturín',
        slug: 'cuestionario-od-maturin',
        tipo_instrumento: 'encuesta_od_pdul',
        activa: true,
        creado_en: '2026-11-10T10:00:00Z',
        total_respuestas: 3
      }
    ]),
    fetchAdminMapaLevantamiento: vi.fn().mockResolvedValue({
      encuesta_id: '00000000-0000-0000-0000-000000000001',
      total_respuestas: 3,
      total_con_gps: 2,
      total_sin_gps: 1,
      porcentaje_cobertura_gps: 66.7,
      total_alertas_ubicacion: 1,
      puntos: [
        {
          id: 101,
          latitud: 9.7458,
          longitud: -63.1832,
          precision_m: 12,
          parroquia: 'san_simon',
          comunidad_sector: 'CENTRO',
          zona_od: 'Casco Central',
          dispositivo_tipo: 'movil',
          fecha_registro: '2026-11-24T12:00:00Z',
          calidad_ubicacion: 'alta',
          motivo_alerta: null
        },
        {
          id: 102,
          latitud: 10.4806,
          longitud: -66.9036,
          precision_m: 1800,
          parroquia: 'boqueron',
          comunidad_sector: 'TIPURO',
          zona_od: 'Zona Norte',
          dispositivo_tipo: 'escritorio',
          fecha_registro: '2026-11-24T12:15:00Z',
          calidad_ubicacion: 'alerta',
          motivo_alerta: 'Coordenada fuera del ámbito geográfico de Maturín / Monagas'
        }
      ]
    }),
    fetchAdminRespuestaDetalle: vi.fn().mockResolvedValue({
      id: 101,
      encuesta_id: '00000000-0000-0000-0000-000000000001',
      client_submission_id: null,
      parroquia: 'san_simon',
      zona_od: 'Casco Central',
      fecha_registro: '2026-11-24T12:00:00Z',
      datos: {
        parroquia: 'san_simon',
        comunidad_sector: 'CENTRO',
        zona_residencia_od: 'Casco Central',
        cedula: '14852963',
        avenida_calle: 'Av. Bolívar',
        casa_apartamento: 'Casa 5',
        gps_latitud: 9.7458,
        gps_longitud: -63.1832,
        gps_precision: 12,
        dispositivo_tipo: 'movil',
        dispositivo_so: 'Android'
      }
    })
  };
});

describe('AdminFieldMapView.vue — Mapa de Levantamiento en Campo', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renderiza indicadores de cobertura GPS y aplica filtros por parroquia, dispositivo y alertas', async () => {
    const wrapper = mount(AdminFieldMapView);
    await flushPromises();

    const kpis = wrapper.get('[data-testid="field-map-kpis"]');
    expect(kpis.text()).toContain('3');
    expect(kpis.text()).toContain('66.7%');
    expect(kpis.text()).toContain('1');

    // Cambiar a vista tabla accesible para verificar filtrado exacto de filas
    await wrapper.get('[data-testid="btn-toggle-map-view-mode"]').trigger('click');
    await flushPromises();

    let rows = wrapper.findAll('[data-testid="field-map-table-view"] tbody tr');
    expect(rows).toHaveLength(2);

    // Filtrar por dispositivo escritorio
    await wrapper.get('[data-testid="filter-device-map"]').setValue('escritorio');
    rows = wrapper.findAll('[data-testid="field-map-table-view"] tbody tr');
    expect(rows).toHaveLength(1);
    expect(rows[0].text()).toContain('#102');

    // Quitar filtro de dispositivo y activar solo alertas
    await wrapper.get('[data-testid="filter-device-map"]').setValue('todos');
    await wrapper.get('[data-testid="checkbox-only-alerts"]').setValue(true);
    rows = wrapper.findAll('[data-testid="field-map-table-view"] tbody tr');
    expect(rows).toHaveLength(1);
    expect(rows[0].text()).toContain('Alerta');
  });

  it('permite inspeccionar un punto cargando el detalle con PII enmascarada por defecto', async () => {
    const wrapper = mount(AdminFieldMapView);
    await flushPromises();

    await wrapper.get('[data-testid="btn-toggle-map-view-mode"]').trigger('click');
    await flushPromises();

    await wrapper.get('[data-testid="btn-inspect-point-101"]').trigger('click');
    await flushPromises();

    expect(api.fetchAdminRespuestaDetalle).toHaveBeenCalledWith(
      '00000000-0000-0000-0000-000000000001',
      101
    );
    const modal = wrapper.find('[role="dialog"]');
    expect(modal.exists()).toBe(true);
    expect(modal.text()).toContain('Detalle de Respuesta #101');
    expect(modal.text()).toContain('[PROTEGIDO / PII]');
    expect(modal.text()).not.toContain('14852963');
  });

  it('cumple ergonomía táctil (>= 48px) en controles de vista y mapa', () => {
    const viewContent = fs.readFileSync(
      path.resolve(__dirname, '../../src/views/AdminFieldMapView.vue'),
      'utf-8'
    );
    const mapContent = fs.readFileSync(
      path.resolve(__dirname, '../../src/components/admin/AdminSurveyFieldMap.vue'),
      'utf-8'
    );

    expect(viewContent).toContain('min-block-size: var(--min-touch-target)');
    expect(mapContent).toContain('min-block-size: var(--min-touch-target)');
    expect(mapContent).not.toContain('maps.googleapis.com');
  });
});

