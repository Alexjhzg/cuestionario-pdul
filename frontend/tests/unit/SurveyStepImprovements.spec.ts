import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import fs from 'node:fs';
import path from 'node:path';
import { Formio } from '@formio/js';
import ResidentesCards from '@/components/survey/ResidentesCards.vue';
import ViajeForm from '@/components/survey/ViajeForm.vue';
import { MODOS_TRANSPORTE_LABELS } from '@/utils/responseFormatters';
import {
  buildReturnTrip,
  buildTripFromDraft,
  isModoSinCosto,
  isVehiculoParticular,
  validateNewTripForm
} from '@/utils/tripCatalogs';
import { getStepValidationErrors } from '@/utils/surveyStepValidation';

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

  describe('4. Omisión de costo del viaje para modos 1 (A pie), 2 (Bicicleta), 3 (Motocicleta) y 4 (Vehículo Particular)', () => {
    it('isModoSinCosto identifica modos 1-4 y alias seguros sin confundir mototaxi ni modos pagos', () => {
      expect(isModoSinCosto('1')).toBe(true);
      expect(isModoSinCosto('2')).toBe(true);
      expect(isModoSinCosto('3')).toBe(true);
      expect(isModoSinCosto('4')).toBe(true);
      expect(isModoSinCosto(1)).toBe(true);
      expect(isModoSinCosto(2)).toBe(true);
      expect(isModoSinCosto(3)).toBe(true);
      expect(isModoSinCosto(4)).toBe(true);
      expect(isModoSinCosto('a pie')).toBe(true);
      expect(isModoSinCosto('a_pie')).toBe(true);
      expect(isModoSinCosto('bicicleta')).toBe(true);
      expect(isModoSinCosto('motocicleta')).toBe(true);
      expect(isModoSinCosto('moto')).toBe(true);
      expect(isModoSinCosto('automovil')).toBe(true);

      // Modos pagos o mototaxi NO están exentos
      expect(isModoSinCosto('5')).toBe(false);
      expect(isModoSinCosto('6')).toBe(false);
      expect(isModoSinCosto('7')).toBe(false);
      expect(isModoSinCosto('8')).toBe(false);
      expect(isModoSinCosto('9')).toBe(false);
      expect(isModoSinCosto('mototaxi')).toBe(false);
      expect(isModoSinCosto('Transporte informal (por puesto, mototaxi)')).toBe(false);
      expect(isModoSinCosto('')).toBe(false);
      expect(isModoSinCosto(undefined)).toBe(false);

      // isVehiculoParticular sigue limitado estrictamente al modo 4
      expect(isVehiculoParticular('1')).toBe(false);
      expect(isVehiculoParticular('2')).toBe(false);
      expect(isVehiculoParticular('3')).toBe(false);
      expect(isVehiculoParticular('4')).toBe(true);
    });

    it.each([
      { codigo: '1', nombre: 'A pie' },
      { codigo: '2', nombre: 'Bicicleta' },
      { codigo: '3', nombre: 'Motocicleta' }
    ])('oculta #viaje-costo manteniendo #viaje-modo-sec y guarda costo_viaje_bs=0 para modo $codigo ($nombre)', async ({ codigo }) => {
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
      await wrapper.find('#viaje-destino-dir').setValue('Plaza Bolívar');
      await wrapper.find('#viaje-destino').setValue('San Simón');
      await wrapper.find('#viaje-hora-salida-h').setValue('08');
      await wrapper.find('#viaje-hora-llegada-h').setValue('08');
      await wrapper.find('#viaje-motivo').setValue('1');

      // Primero ingresa costo bajo modo pago '6' y luego cambia al modo exento
      await wrapper.find('#viaje-modo').setValue('6');
      await wrapper.find('#viaje-costo').setValue(15);

      await wrapper.find('#viaje-modo').setValue(codigo);
      expect(wrapper.find('#viaje-costo').exists()).toBe(false);
      expect(wrapper.find('#viaje-modo-sec').exists()).toBe(true);
      await wrapper.find('#viaje-modo-sec').setValue('1');
      await wrapper.find('#viaje-tiempo').setValue(15);

      await wrapper.find('.add-viaje-btn').trigger('click');

      expect(wrapper.find('.form-error-banner').exists()).toBe(false);
      const emitted = wrapper.emitted('agregar-viaje') as any[][];
      expect(emitted).toBeTruthy();
      expect(emitted[0][0]).toMatchObject({
        modo_principal: codigo,
        modo_secundario: '1',
        costo_viaje_bs: 0
      });
    });

    it('restaura #viaje-costo vacío al cambiar desde un modo sin costo (1-4) hacia un modo pago (6)', async () => {
      const wrapper = mount(ViajeForm, {
        props: {
          sugerenciaOrigen: 'San Simón',
          residentes: [
            { persona_numero: 1, nombres: 'Ana Gómez', parentesco: '1', sexo: '2', edad: 30 }
          ]
        }
      });

      await wrapper.find('#viaje-modo').setValue('1');
      expect(wrapper.find('#viaje-costo').exists()).toBe(false);

      await wrapper.find('#viaje-modo').setValue('6');
      const costoInput = wrapper.find('#viaje-costo');
      expect(costoInput.exists()).toBe(true);
      expect((costoInput.element as HTMLInputElement).value).toBe('');
    });

    it('validateNewTripForm, buildTripFromDraft, buildReturnTrip y surveyStepValidation omiten costo para modos 1-4 y exigen costo en modo 6', () => {
      for (const modo of ['1', '2', '3', '4']) {
        const draft = {
          persona_numero: 1,
          origen_direccion: 'Casa',
          zona_od_origen: 'san_simon',
          destino_direccion: 'Trabajo',
          zona_od_destino: 'las_cocuizas',
          motivo_viaje: '1',
          modo_principal: modo,
          modo_secundario: modo === '4' ? '1' : '6',
          tiempo_viaje_min: 20,
          costo_viaje_bs: undefined
        };

        expect(
          validateNewTripForm({
            draft,
            sugerenciaOrigen: 'san_simon',
            horaSalidaH: '07',
            horaLlegadaH: '08'
          })
        ).toBeNull();

        const built = buildTripFromDraft({
          draft: { ...draft, costo_viaje_bs: 25 },
          sugerenciaOrigen: 'san_simon',
          horaSalida: { hora: '07', minuto: '00', periodo: 'AM' },
          horaLlegada: { hora: '07', minuto: '20', periodo: 'AM' },
          viajeNumero: 1
        });
        expect(built.costo_viaje_bs).toBe(0);
        if (modo === '4') {
          expect(built.modo_secundario).toBeUndefined();
        } else {
          expect(built.modo_secundario).toBe('6');
        }

        const returnTrip = buildReturnTrip({ ...built, costo_viaje_bs: 99 }, 2, 'san_simon');
        expect(returnTrip.costo_viaje_bs).toBe(0);

        const stepErrors = getStepValidationErrors(4, {
          viajes: [
            {
              persona_numero: 1,
              origen_direccion: 'Casa',
              zona_od_origen: 'san_simon',
              destino_direccion: 'Trabajo',
              zona_od_destino: 'las_cocuizas',
              hora_salida: '07:00 AM',
              hora_llegada: '07:20 AM',
              motivo_viaje: '1',
              modo_principal: modo,
              tiempo_viaje_min: 20,
              costo_viaje_bs: undefined
            }
          ]
        });
        expect(stepErrors).toEqual([]);
      }

      // Modo pago ('6') sin costo sí produce error
      expect(
        validateNewTripForm({
          draft: {
            persona_numero: 1,
            origen_direccion: 'Casa',
            zona_od_origen: 'san_simon',
            destino_direccion: 'Trabajo',
            zona_od_destino: 'las_cocuizas',
            motivo_viaje: '1',
            modo_principal: '6',
            tiempo_viaje_min: 20,
            costo_viaje_bs: undefined
          },
          sugerenciaOrigen: 'san_simon',
          horaSalidaH: '07',
          horaLlegadaH: '08'
        })
      ).toContain('costo del viaje');

      const paidErrors = getStepValidationErrors(4, {
        viajes: [
          {
            persona_numero: 1,
            origen_direccion: 'Casa',
            zona_od_origen: 'san_simon',
            destino_direccion: 'Trabajo',
            zona_od_destino: 'las_cocuizas',
            hora_salida: '07:00 AM',
            hora_llegada: '07:20 AM',
            motivo_viaje: '1',
            modo_principal: '6',
            tiempo_viaje_min: 20,
            costo_viaje_bs: undefined
          }
        ]
      });
      expect(paidErrors.some((e) => e.message.includes('costo del viaje'))).toBe(true);
    });

    it('evalúa correctamente customConditional de costo_viaje_bs dentro del datagrid viajes en @formio/js', async () => {
      const schemaPath = path.resolve(__dirname, '../../../shared/schemas/pdul_origen_destino.json');
      const schema = JSON.parse(fs.readFileSync(schemaPath, 'utf-8'));

      const hadOption = typeof (globalThis as any).Option === 'function';
      if (!hadOption) {
        (globalThis as any).Option = function DomOption(
          text = '',
          value = '',
          defaultSelected = false,
          selected = false
        ) {
          const opt = document.createElement('option');
          opt.text = String(text);
          opt.value = String(value);
          opt.defaultSelected = Boolean(defaultSelected);
          opt.selected = Boolean(selected);
          return opt;
        };
      }

      const container = document.createElement('div');
      document.body.appendChild(container);
      const form = await Formio.createForm(container, schema);

      try {
        await form.ready;
        const viajesGrid = form.getComponent('viajes') as any;
        expect(viajesGrid).toBeTruthy();

        const costoComp =
          viajesGrid?.components?.find((c: any) => c.component?.key === 'costo_viaje_bs') ||
          form.getComponent('costo_viaje_bs');
        expect(costoComp).toBeTruthy();

        for (const modo of ['1', '2', '3', '4']) {
          const rowData = { modo_principal: modo };
          const rootData = { viajes: [rowData] };
          expect(costoComp.checkCondition(rowData, rootData)).toBe(false);
        }

        for (const modo of ['5', '6', '7']) {
          const rowData = { modo_principal: modo };
          const rootData = { viajes: [rowData] };
          expect(costoComp.checkCondition(rowData, rootData)).toBe(true);
        }
      } finally {
        // Flush any pending choices.js requestAnimationFrame callbacks before teardown
        await new Promise((resolve) => setTimeout(resolve, 30));
        if (typeof form?.destroy === 'function') {
          form.destroy(true);
        }
        container.remove();
        if (!hadOption) {
          delete (globalThis as any).Option;
        }
      }
    });
  });
});
