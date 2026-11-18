import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import Step1Ubicacion from '@/components/survey/sections/Step1Ubicacion.vue';

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

