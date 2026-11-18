import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import ResidentesCards from '@/components/survey/ResidentesCards.vue';
import ViajeForm from '@/components/survey/ViajeForm.vue';
import { MODOS_TRANSPORTE_LABELS } from '@/utils/responseFormatters';
import { isVehiculoParticular } from '@/utils/tripCatalogs';

describe('Mejoras Cuestionario PDUL — Transporte Institucional, Condicional Vehículo Particular y Limpieza de Variables', () => {
  describe('1. Inclusión de Transporte Institucional', () => {
    it('incluye la opción "Transporte Institucional" en el selector de medio de transporte habitual', () => {
      const wrapper = mount(ResidentesCards, {
        props: { modelValue: [] }
      });

      const select = wrapper.find<HTMLSelectElement>('#residente-medio-transporte');
      expect(select.exists()).toBe(true);

      const options = select.findAll('option');
      const optInstitucional = options.find((opt) => opt.attributes('value') === '9');
      expect(optInstitucional).toBeDefined();
      expect(optInstitucional?.text()).toContain('Transporte Institucional');
    });

    it('formatea y visualiza correctamente el transporte institucional en la tarjeta del residente y catálogo', () => {
      const wrapper = mount(ResidentesCards, {
        props: {
          modelValue: [
            {
              persona_numero: 1,
              nombres: 'Carlos Salazar',
              parentesco: '1',
              sexo: '1',
              edad: 38,
              actividad_principal: '1',
              medio_transporte_habitual: '9'
            }
          ]
        }
      });

      expect(wrapper.text()).toContain('Transporte: Transporte Institucional');
      expect(MODOS_TRANSPORTE_LABELS['9']).toBe('Transporte Institucional');
      expect(MODOS_TRANSPORTE_LABELS['institucional']).toBe('Transporte Institucional');
    });
  });

  describe('2. Lógica Condicional para Vehículo Particular en Viajes', () => {
    it('reconoce correctamente el modo particular con isVehiculoParticular', () => {
      expect(isVehiculoParticular('4')).toBe(true);
      expect(isVehiculoParticular('automovil')).toBe(true);
      expect(isVehiculoParticular('vehiculo particular')).toBe(true);
      expect(isVehiculoParticular('6')).toBe(false);
      expect(isVehiculoParticular('1')).toBe(false);
    });

    it('omite "modo secundario" y "costo del viaje" cuando modo principal es Vehículo Particular (4)', async () => {
      const wrapper = mount(ViajeForm, {
        props: {
          sugerenciaOrigen: 'San Simón',
          residentes: [
            { persona_numero: 1, nombres: 'Ana Gómez', parentesco: '1', sexo: '2', edad: 30 }
          ]
        }
      });

      // Inicialmente sin modo seleccionado, los campos existen en el DOM
      expect(wrapper.find('#viaje-modo-sec').exists()).toBe(true);
      expect(wrapper.find('#viaje-costo').exists()).toBe(true);

      // Seleccionar Vehículo Particular (4)
      await wrapper.find('#viaje-modo').setValue('4');

      // Deben omitirse del DOM
      expect(wrapper.find('#viaje-modo-sec').exists()).toBe(false);
      expect(wrapper.find('#viaje-costo').exists()).toBe(false);

      // Si cambia a Transporte Público (6), reaparecen
      await wrapper.find('#viaje-modo').setValue('6');
      expect(wrapper.find('#viaje-modo-sec').exists()).toBe(true);
      expect(wrapper.find('#viaje-costo').exists()).toBe(true);
    });

    it('permite registrar un viaje en vehículo particular sin exigir costo ni modo secundario', async () => {
      const wrapper = mount(ViajeForm, {
        props: {
          sugerenciaOrigen: 'San Simón',
          residentes: [
            { persona_numero: 1, nombres: 'Ana Gómez', parentesco: '1', sexo: '2', edad: 30 }
          ]
        }
      });

      await wrapper.find('#viaje-persona').setValue('1');
      await wrapper.find('#viaje-origen-dir').setValue('Av. Juncal');
      await wrapper.find('#viaje-origen').setValue('San Simón');
      await wrapper.find('#viaje-destino-dir').setValue('C.C. La Cascada');
      await wrapper.find('#viaje-destino').setValue('Las Cocuizas');
      await wrapper.find('#viaje-hora-salida-h').setValue('08');
      await wrapper.find('#viaje-hora-llegada-h').setValue('09');
      await wrapper.find('#viaje-motivo').setValue('1');
      await wrapper.find('#viaje-modo').setValue('4'); // Particular
      await wrapper.find('#viaje-tiempo').setValue(25);

      await wrapper.find('.add-viaje-btn').trigger('click');

      expect(wrapper.find('.form-error-banner').exists()).toBe(false);
      const emitted = wrapper.emitted('agregar-viaje') as any[][];
      expect(emitted).toBeTruthy();
      expect(emitted[0][0]).toMatchObject({
        persona_numero: 1,
        modo_principal: '4',
        modo_secundario: undefined,
        costo_viaje_bs: 0
      });
    });
  });

  describe('3. Limpieza de Variables al Avanzar de Registro', () => {
    it('reinicia todos los campos a blanco tras agregar un viaje, sin persistir datos del usuario anterior', async () => {
      const wrapper = mount(ViajeForm, {
        props: {
          sugerenciaOrigen: 'San Simón',
          residentes: [
            { persona_numero: 1, nombres: 'Ana Gómez', parentesco: '1', sexo: '2', edad: 30 },
            { persona_numero: 2, nombres: 'Luis Gómez', parentesco: '2', sexo: '1', edad: 32 }
          ]
        }
      });

      await wrapper.find('#viaje-persona').setValue('1');
      await wrapper.find('#viaje-origen-dir').setValue('Calle Monagas');
      await wrapper.find('#viaje-origen').setValue('San Simón');
      await wrapper.find('#viaje-destino-dir').setValue('Hospital Central');
      await wrapper.find('#viaje-destino').setValue('Las Cocuizas');
      await wrapper.find('#viaje-hora-salida-h').setValue('08');
      await wrapper.find('#viaje-hora-llegada-h').setValue('09');
      await wrapper.find('#viaje-motivo').setValue('7');
      await wrapper.find('#viaje-modo').setValue('6');
      await wrapper.find('#viaje-tiempo').setValue(20);
      await wrapper.find('#viaje-costo').setValue(15);

      await wrapper.find('.add-viaje-btn').trigger('click');

      // Tras agregar, los campos de destino, modo, tiempo y costo quedan limpios
      expect((wrapper.find('#viaje-destino-dir').element as HTMLInputElement).value).toBe('');
      expect((wrapper.find('#viaje-destino').element as HTMLInputElement).value).toBe('');
      expect((wrapper.find('#viaje-motivo').element as HTMLSelectElement).value).toBe('');
      expect((wrapper.find('#viaje-modo').element as HTMLSelectElement).value).toBe('');
      expect((wrapper.find('#viaje-tiempo').element as HTMLInputElement).value).toBe('');
      expect((wrapper.find('#viaje-costo').element as HTMLInputElement).value).toBe('');

      // Al cambiar de usuario/residente a Persona 2, se reinician las variables para no arrastrar datos
      await wrapper.find('#viaje-persona').setValue('2');
      expect((wrapper.find('#viaje-origen-dir').element as HTMLInputElement).value).toBe('');
      expect((wrapper.find('#viaje-destino-dir').element as HTMLInputElement).value).toBe('');
      expect((wrapper.find('#viaje-motivo').element as HTMLSelectElement).value).toBe('');
    });

    it('expone resetDraft para limpieza al avanzar de paso en el wizard', () => {
      const wrapper = mount(ViajeForm, {
        props: { sugerenciaOrigen: 'San Simón' }
      });
      expect(typeof (wrapper.vm as any).resetDraft).toBe('function');

      const wrapperRes = mount(ResidentesCards, {
        props: { modelValue: [] }
      });
      expect(typeof (wrapperRes.vm as any).resetDraft).toBe('function');
    });
  });
});
