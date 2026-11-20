import { describe, it, expect, vi, afterEach } from 'vitest';
import { mount } from '@vue/test-utils';
import Step1Ubicacion from '@/components/survey/sections/Step1Ubicacion.vue';
import { getStepErrors } from '@/utils/surveyStepValidation';

describe('Step1Ubicacion.vue — Selección de ubicación y campo de texto zona O-D', () => {
  it('renderiza select dependiente deshabilitado para comunidad antes de elegir parroquia y campo de texto para zona O-D', () => {
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
    const zonaInput = wrapper.find('input#zona_residencia_od');

    expect(comunidadSelect.exists()).toBe(true);
    expect(zonaInput.exists()).toBe(true);
    expect(wrapper.find('input#comunidad_sector').exists()).toBe(false);
    expect(wrapper.find('select#zona_residencia_od').exists()).toBe(false);
    expect(comunidadSelect.attributes('disabled')).toBeDefined();
  });

  it('filtra comunidades según la parroquia elegida y permite ingresar texto libre en zona O-D', async () => {
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
    const zonaInput = wrapper.find('input#zona_residencia_od');

    expect(comunidadSelect.attributes('disabled')).toBeUndefined();
    expect(zonaInput.exists()).toBe(true);

    const comOptions = comunidadSelect.findAll('option').map((o) => o.text());
    expect(comOptions).toContain('EL FURRIAL');
    expect(comOptions).not.toContain('ALTO DE LOS GODOS');

    await zonaInput.setValue('Zona Rural El Furrial');
    expect(wrapper.emitted('update-field')).toContainEqual(['zona_residencia_od', 'Zona Rural El Furrial']);
  });

  it('asocia comunidad_codigo al seleccionar una comunidad de la lista', async () => {
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

