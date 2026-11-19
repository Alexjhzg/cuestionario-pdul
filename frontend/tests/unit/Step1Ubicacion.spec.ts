import { describe, it, expect, vi, afterEach } from 'vitest';
import { mount } from '@vue/test-utils';
import Step1Ubicacion from '@/components/survey/sections/Step1Ubicacion.vue';
import { getStepErrors } from '@/utils/surveyStepValidation';

describe('Step1Ubicacion.vue — Listas desplegables dependientes en cascada', () => {
  it('renderiza select dependientes deshabilitados para comunidad y zona O-D antes de elegir parroquia', () => {
    const wrapper = mount(Step1Ubicacion, {
      props: {
        modelValue: {
          parroquia: '',
          comunidad_sector: '',
          zona_residencia_od: ''
        }
      }
    });

    const comunidadSelect = wrapper.find('select#comunidad_sector');
    const zonaSelect = wrapper.find('select#zona_residencia_od');

    expect(comunidadSelect.exists()).toBe(true);
    expect(zonaSelect.exists()).toBe(true);
    expect(wrapper.find('input#comunidad_sector').exists()).toBe(false);
    expect(wrapper.find('input#zona_residencia_od').exists()).toBe(false);
    expect(comunidadSelect.attributes('disabled')).toBeDefined();
    expect(zonaSelect.attributes('disabled')).toBeDefined();
  });

  it('filtra comunidades y zonas O-D en cascada según la parroquia elegida', async () => {
    const modelValue: Record<string, any> = {
      parroquia: '',
      comunidad_sector: '',
      comunidad_codigo: '',
      zona_residencia_od: ''
    };

    const wrapper = mount(Step1Ubicacion, {
      props: { modelValue }
    });

    await wrapper.find('select#parroquia').setValue('el_furrial');
    await wrapper.setProps({
      modelValue: { ...modelValue, parroquia: 'el_furrial' }
    });

    const comunidadSelect = wrapper.find('select#comunidad_sector');
    const zonaSelect = wrapper.find('select#zona_residencia_od');

    expect(comunidadSelect.attributes('disabled')).toBeUndefined();
    expect(zonaSelect.attributes('disabled')).toBeUndefined();

    const comOptions = comunidadSelect.findAll('option').map((o) => o.text());
    const zonaOptions = zonaSelect.findAll('option').map((o) => o.text());

    expect(comOptions).toContain('EL FURRIAL');
    expect(comOptions).not.toContain('ALTO DE LOS GODOS');
    expect(zonaOptions).toContain('El Furrial Centro');
    expect(zonaOptions).not.toContain('Los Guaritos I - IV');
  });

  it('asocia comunidad_codigo y refina zonas O-D según xpar de la comunidad en San Simón', async () => {
    const wrapper = mount(Step1Ubicacion, {
      props: {
        modelValue: {
          parroquia: 'san_simon',
          comunidad_sector: '',
          comunidad_codigo: '',
          zona_residencia_od: ''
        }
      }
    });

    await wrapper.find('select#comunidad_sector').setValue('CENTRO');
    const emitted = wrapper.emitted('update-field') || [];

    expect(emitted).toContainEqual(['comunidad_sector', 'CENTRO']);
    const codigoEmit = emitted.find((e) => e[0] === 'comunidad_codigo');
    expect(codigoEmit).toBeDefined();
    expect(codigoEmit![1]).toBeTruthy();

    await wrapper.setProps({
      modelValue: {
        parroquia: 'san_simon',
        comunidad_sector: 'CENTRO',
        comunidad_codigo: codigoEmit![1],
        zona_residencia_od: ''
      }
    });

    const zonaOptions = wrapper
      .find('select#zona_residencia_od')
      .findAll('option')
      .map((o) => o.text());
    expect(zonaOptions).toContain('San Simón Centro (160805)');
    expect(zonaOptions).not.toContain('San Simón Sur (160801)');
  });
});

describe('Step1Ubicacion.vue — Captura opcional de punto GPS', () => {
  const originalGeolocation = navigator.geolocation;

  afterEach(() => {
    Object.defineProperty(navigator, 'geolocation', {
      value: originalGeolocation,
      configurable: true,
      writable: true
    });
    vi.restoreAllMocks();
  });

  it('captura el punto GPS al pulsar el botón y emite los 4 campos al modelo', async () => {
    const mockGetCurrentPosition = vi.fn((success: PositionCallback) => {
      success({
        coords: {
          latitude: 9.745812,
          longitude: -63.183204,
          accuracy: 8.2,
          altitude: null,
          altitudeAccuracy: null,
          heading: null,
          speed: null,
          toJSON: () => ({})
        },
        timestamp: 1732032000000,
        toJSON: () => ({})
      } as GeolocationPosition);
    });

    Object.defineProperty(navigator, 'geolocation', {
      value: { getCurrentPosition: mockGetCurrentPosition },
      configurable: true
    });

    const wrapper = mount(Step1Ubicacion, {
      props: {
        modelValue: {
          parroquia: 'san_simon',
          comunidad_sector: 'CENTRO',
          zona_residencia_od: '160805'
        }
      }
    });

    const btn = wrapper.get('[data-testid="btn-gps-capture"]');
    await btn.trigger('click');

    const emitted = wrapper.emitted('update-field') || [];
    expect(emitted).toContainEqual(['gps_latitud', 9.745812]);
    expect(emitted).toContainEqual(['gps_longitud', -63.183204]);
    expect(emitted).toContainEqual(['gps_precision', 8]);
    expect(emitted).toContainEqual(['gps_capturado_en', new Date(1732032000000).toISOString()]);
  });

  it('muestra coordenadas, badge de precisión, enlace a OpenStreetMap y permite quitar el punto', async () => {
    const wrapper = mount(Step1Ubicacion, {
      props: {
        modelValue: {
          parroquia: 'san_simon',
          gps_latitud: 9.745812,
          gps_longitud: -63.183204,
          gps_precision: 10,
          gps_capturado_en: '2026-11-19T18:00:00.000Z'
        }
      }
    });

    expect(wrapper.get('[data-testid="gps-coords-value"]').text()).toBe('9.745812, -63.183204');
    expect(wrapper.get('[data-testid="gps-precision-badge"]').text()).toContain('±10 m');
    const mapLink = wrapper.get('[data-testid="link-gps-map"]');
    expect(mapLink.attributes('href')).toContain('openstreetmap.org/?mlat=9.745812&mlon=-63.183204');

    await wrapper.get('[data-testid="btn-gps-clear"]').trigger('click');
    const emitted = wrapper.emitted('update-field') || [];
    expect(emitted).toContainEqual(['gps_latitud', null]);
    expect(emitted).toContainEqual(['gps_longitud', null]);
    expect(emitted).toContainEqual(['gps_precision', null]);
    expect(emitted).toContainEqual(['gps_capturado_en', null]);
  });

  it('valida Paso 1 permitiendo GPS vacío (opcional) y rechazando coordenadas fuera de rango', () => {
    const baseValid = {
      parroquia: 'san_simon',
      comunidad_sector: 'CENTRO',
      zona_residencia_od: '160805',
      avenida_calle: 'Av. Bolívar',
      casa_apartamento: 'Casa 12'
    };

    expect(getStepErrors(0, baseValid)).toHaveLength(0);
    expect(
      getStepErrors(0, { ...baseValid, gps_latitud: 9.745812, gps_longitud: -63.183204 })
    ).toHaveLength(0);

    const invalidErrors = getStepErrors(0, {
      ...baseValid,
      gps_latitud: 120.5,
      gps_longitud: -63.18
    });
    expect(invalidErrors.length).toBeGreaterThan(0);
    expect(invalidErrors[0]).toContain('coordenadas GPS');
  });
});

