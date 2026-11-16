import { describe, it, expect, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import ViajesMobileCards from '@/components/survey/ViajesMobileCards.vue';
import type { ViajeOD } from '@/types/survey';

describe('Componente ViajesMobileCards.vue', () => {
  const mockViajes: ViajeOD[] = [
    {
      viaje_numero: 1,
      persona_numero: 1,
      zona_od_origen: 'alto_de_los_godos',
      zona_od_destino: 'san_simon',
      motivo_viaje: '1',
      modo_principal: '6',
      tiempo_viaje_min: 35,
      costo_viaje_bs: 15
    },
    {
      viaje_numero: 2,
      persona_numero: 1,
      zona_od_origen: 'san_simon',
      zona_od_destino: 'las_cocuizas',
      motivo_viaje: '2',
      modo_principal: '4',
      tiempo_viaje_min: 20,
      costo_viaje_bs: 0
    }
  ];

  it('renderiza correctamente las tarjetas de los viajes registrados', () => {
    const wrapper = mount(ViajesMobileCards, {
      props: {
        modelValue: mockViajes,
        zonaResidenciaDefault: 'alto_de_los_godos'
      }
    });

    const cards = wrapper.findAll('.viaje-card');
    expect(cards).toHaveLength(2);

    expect(wrapper.text()).toContain('Registro de Viajes Cotidianos (2)');
    expect(wrapper.text()).toContain('Alto de Los Godos');
    expect(wrapper.text()).toContain('San Simón');
    expect(wrapper.text()).toContain('Las Cocuizas');
    expect(wrapper.text()).toContain('35 min');
  });

  it('emite evento al pulsar el botón de regreso a casa en 1 toque invirtiendo origen y destino', async () => {
    const wrapper = mount(ViajesMobileCards, {
      props: {
        modelValue: [mockViajes[0]],
        zonaResidenciaDefault: 'alto_de_los_godos'
      }
    });

    const returnBtn = wrapper.find('.return-btn');
    expect(returnBtn.exists()).toBe(true);

    await returnBtn.trigger('click');

    // Debe emitir 'agregar-regreso'
    const emittedRegreso = wrapper.emitted('agregar-regreso');
    expect(emittedRegreso).toBeTruthy();
    expect(emittedRegreso![0][0]).toEqual({
      viaje_numero: 2,
      persona_numero: 1,
      zona_od_origen: 'san_simon',
      zona_od_destino: 'alto_de_los_godos',
      motivo_viaje: '1',
      modo_principal: '6',
      tiempo_viaje_min: 35,
      costo_viaje_bs: 15
    });

    // Debe emitir 'update:modelValue' con los dos viajes
    const emittedUpdate = wrapper.emitted('update:modelValue');
    expect(emittedUpdate).toBeTruthy();
    expect(emittedUpdate![0][0]).toHaveLength(2);
  });

  it('emite evento al eliminar viaje con un botón que posee aria-label accesible y descriptivo', async () => {
    const wrapper = mount(ViajesMobileCards, {
      props: {
        modelValue: [mockViajes[0]],
        zonaResidenciaDefault: 'alto_de_los_godos'
      }
    });

    const deleteBtn = wrapper.find('.delete-btn');
    expect(deleteBtn.exists()).toBe(true);

    // Verificar accesibilidad: el aria-label describe exactamente qué viaje se va a eliminar con nombres limpios
    const ariaLabel = deleteBtn.attributes('aria-label');
    expect(ariaLabel).toBe('Eliminar viaje 1 de Alto de Los Godos a San Simón');

    await deleteBtn.trigger('click');

    // Debe emitir el evento 'eliminar' con el índice 0
    expect(wrapper.emitted('eliminar')).toBeTruthy();
    expect(wrapper.emitted('eliminar')![0]).toEqual([0]);

    // Debe emitir 'update:modelValue' con array vacío
    expect(wrapper.emitted('update:modelValue')![0][0]).toEqual([]);
  });

  it('verifica que el formulario de viaje inicializa con campos limpios y placeholders explicativos (R5)', () => {
    const wrapper = mount(ViajesMobileCards, {
      props: {
        modelValue: [],
        zonaResidenciaDefault: 'alto_de_los_godos'
      }
    });

    const personaInput = wrapper.find<HTMLInputElement>('#viaje-persona');
    expect(personaInput.element.value).toBe('');
    expect(personaInput.attributes('placeholder')).toContain('Ej: 1');

    const destinoInput = wrapper.find<HTMLInputElement>('#viaje-destino');
    expect(destinoInput.element.value).toBe('');
    expect(destinoInput.attributes('placeholder')).toContain('Ej: San Simón');

    const modoSelect = wrapper.find<HTMLSelectElement>('#viaje-modo');
    expect(modoSelect.element.value).toBe('');

    const tiempoInput = wrapper.find<HTMLInputElement>('#viaje-tiempo');
    expect(tiempoInput.element.value).toBe('');
    expect(tiempoInput.attributes('placeholder')).toContain('Ej: 30');

    const costoInput = wrapper.find<HTMLInputElement>('#viaje-costo');
    expect(costoInput.element.value).toBe('');
    expect(costoInput.attributes('placeholder')).toContain('0 si no posee');
  });

  it('agrega un nuevo viaje mediante el formulario, emitiendo update:modelValue y limpiando campos (R2, R3, R5)', async () => {
    const scrollIntoViewMock = vi.fn();
    window.HTMLElement.prototype.scrollIntoView = scrollIntoViewMock;

    const wrapper = mount(ViajesMobileCards, {
      props: {
        modelValue: [],
        zonaResidenciaDefault: 'alto_de_los_godos'
      }
    });

    await wrapper.find('#viaje-persona').setValue(1);
    await wrapper.find('#viaje-origen-dir').setValue('Casa de habitación');
    await wrapper.find('#viaje-origen').setValue('alto_de_los_godos');
    await wrapper.find('#viaje-destino-dir').setValue('Sede laboral');
    await wrapper.find('#viaje-destino').setValue('san_simon');
    await wrapper.find('#viaje-hora-salida-h').setValue('07');
    await wrapper.find('#viaje-hora-llegada-h').setValue('08');
    await wrapper.find('#viaje-motivo').setValue('1');
    await wrapper.find('#viaje-modo').setValue('6');
    await wrapper.find('#viaje-tiempo').setValue(25);
    await wrapper.find('#viaje-costo').setValue(12.5);

    await wrapper.find('.add-viaje-btn').trigger('click');

    const emitted = wrapper.emitted('update:modelValue') as any[][];
    expect(emitted).toBeTruthy();
    expect(emitted[0][0]).toHaveLength(1);
    expect(emitted[0][0][0]).toMatchObject({
      viaje_numero: 1,
      persona_numero: 1,
      origen_direccion: 'Casa de habitación',
      zona_od_origen: 'alto_de_los_godos',
      destino_direccion: 'Sede laboral',
      zona_od_destino: 'san_simon',
      hora_salida: '07:00 AM',
      hora_llegada: '08:00 AM',
      motivo_viaje: '1',
      modo_principal: '6',
      tiempo_viaje_min: 25,
      costo_viaje_bs: 12.5
    });

    // Campos secundarios reseteados
    expect((wrapper.find('#viaje-destino').element as HTMLInputElement).value).toBe('');
    expect((wrapper.find('#viaje-modo').element as HTMLSelectElement).value).toBe('');
  });

  it('posiciona la hora de salida y hora de llegada en la misma fila mediante .horarios-grid-row y las muestra agrupadas en el modal', async () => {
    const wrapper = mount(ViajesMobileCards, {
      props: {
        modelValue: [
          {
            viaje_numero: 1,
            persona_numero: 1,
            zona_od_origen: 'alto_de_los_godos',
            zona_od_destino: 'san_simon',
            hora_salida: '07:15 AM',
            hora_llegada: '07:45 AM',
            motivo_viaje: '1',
            modo_principal: '6',
            tiempo_viaje_min: 30,
            costo_viaje_bs: 10
          }
        ],
        zonaResidenciaDefault: 'alto_de_los_godos'
      }
    });

    // 1. Verificación del formulario: ambos inputs residen en el mismo contenedor de fila .horarios-grid-row
    const horariosRow = wrapper.find('.horarios-grid-row');
    expect(horariosRow.exists()).toBe(true);
    expect(horariosRow.find('#viaje-hora-salida-h').exists()).toBe(true);
    expect(horariosRow.find('#viaje-hora-llegada-h').exists()).toBe(true);

    // 2. Verificación del modal de detalles: muestra horario conjunto en .detail-horarios-row
    const detailsBtn = wrapper.find('.details-btn');
    expect(detailsBtn.exists()).toBe(true);
    await detailsBtn.trigger('click');

    const modalHorarios = wrapper.find('.detail-horarios-row');
    expect(modalHorarios.exists()).toBe(true);
    expect(modalHorarios.text()).toContain('07:15 AM');
    expect(modalHorarios.text()).toContain('07:45 AM');
  });
});
