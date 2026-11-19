import { describe, it, expect, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import ResidentesCards from '@/components/survey/ResidentesCards.vue';
import type { Residente } from '@/types/survey';

const mockResidentes: Residente[] = [
  {
    persona_numero: 1,
    nombres: 'María Pérez',
    parentesco: '1',
    sexo: '2',
    edad: 42,
    nivel_educativo: '4',
    actividad_principal: '1'
  }
];

describe('Componente ResidentesCards.vue (Composición del Hogar PDUL)', () => {
  it('inicializa el formulario con campos vacíos y sin valores predeterminados', () => {
    const wrapper = mount(ResidentesCards, {
      props: {
        modelValue: []
      }
    });

    // Inputs y selects deben iniciar sin prellenado forzado
    const nombreInput = wrapper.find<HTMLInputElement>('#residente-nombre');
    expect(nombreInput.element.value).toBe('');
    expect(nombreInput.attributes('placeholder')).toContain('Ej: María P.');

    const parentescoSelect = wrapper.find<HTMLSelectElement>('#residente-parentesco');
    expect(parentescoSelect.element.value).toBe('');

    const sexoSelect = wrapper.find<HTMLSelectElement>('#residente-sexo');
    expect(sexoSelect.element.value).toBe('');

    const edadInput = wrapper.find<HTMLInputElement>('#residente-edad');
    expect(edadInput.element.value).toBe('');
    expect(edadInput.attributes('placeholder')).toContain('Ej: 35');

    const actividadSelect = wrapper.find<HTMLSelectElement>('#residente-actividad');
    expect(actividadSelect.element.value).toBe('');
  });

  it('muestra estado vacío amigable cuando modelValue no tiene registros', () => {
    const wrapper = mount(ResidentesCards, {
      props: {
        modelValue: []
      }
    });

    expect(wrapper.find('.empty-state').exists()).toBe(true);
    expect(wrapper.text()).toContain('No se han registrado residentes aún');
  });

  it('renderiza tarjetas resumidas cuando existen miembros registrados', () => {
    const wrapper = mount(ResidentesCards, {
      props: {
        modelValue: mockResidentes
      }
    });

    const cards = wrapper.findAll('.residente-card');
    expect(cards).toHaveLength(1);
    expect(wrapper.text()).toContain('María Pérez');
    expect(wrapper.text()).toContain('Jefe(a) de Hogar');
    expect(wrapper.text()).toContain('42 años');
    expect(wrapper.text()).toContain('Mujer');
  });

  it('valida que los campos requeridos estén completos antes de agregar', async () => {
    const wrapper = mount(ResidentesCards, {
      props: {
        modelValue: []
      }
    });

    const addBtn = wrapper.find('.add-residente-btn');
    await addBtn.trigger('click');

    // Debe mostrar banner de error
    const banner = wrapper.find('.form-error-banner');
    expect(banner.exists()).toBe(true);
    expect(wrapper.emitted('agregar')).toBeFalsy();
  });

  it('agrega un nuevo residente, emite eventos y resetea los campos a vacío', async () => {
    const scrollIntoViewMock = vi.fn();
    window.HTMLElement.prototype.scrollIntoView = scrollIntoViewMock;

    const wrapper = mount(ResidentesCards, {
      props: {
        modelValue: []
      }
    });

    // Llenar todos los campos requeridos
    await wrapper.find('#residente-nombre').setValue('Pedro Gómez');
    await wrapper.find('#residente-parentesco').setValue('2');
    await wrapper.find('#residente-sexo').setValue('1');
    await wrapper.find('#residente-edad').setValue(45);
    await wrapper.find('#residente-sabe-leer').setValue('si');
    await wrapper.find('#residente-nivel-educativo').setValue('primaria');
    await wrapper.find('#residente-actividad').setValue('1');
    await wrapper.find('#residente-medio-transporte').setValue('1');
    await wrapper.find('#residente-licencia').setValue('no');
    await wrapper.find('#residente-vehiculo-disp').setValue('no');

    const addBtn = wrapper.find('.add-residente-btn');
    await addBtn.trigger('click');

    // Verificar evento 'agregar'
    const emittedAgregar = wrapper.emitted('agregar');
    expect(emittedAgregar).toBeTruthy();
    expect(emittedAgregar![0][0]).toMatchObject({
      persona_numero: 1,
      nombres: 'Pedro Gómez',
      parentesco: '2',
      sexo: '1',
      edad: 45,
      actividad_principal: '1'
    });

    // Verificar evento 'update:modelValue'
    const emittedUpdate = wrapper.emitted('update:modelValue');
    expect(emittedUpdate).toBeTruthy();
    expect(emittedUpdate![0][0]).toHaveLength(1);

    // Campos deben resetearse a vacío
    expect((wrapper.find('#residente-nombre').element as HTMLInputElement).value).toBe('');
    expect((wrapper.find('#residente-parentesco').element as HTMLSelectElement).value).toBe('');
    expect((wrapper.find('#residente-sexo').element as HTMLSelectElement).value).toBe('');
    expect((wrapper.find('#residente-edad').element as HTMLInputElement).value).toBe('');
    expect((wrapper.find('#residente-actividad').element as HTMLSelectElement).value).toBe('');
  });

  it('elimina un residente de la lista y emite update:modelValue reordenado', async () => {
    const wrapper = mount(ResidentesCards, {
      props: {
        modelValue: mockResidentes
      }
    });

    const deleteBtn = wrapper.find('.residente-btn-delete');
    expect(deleteBtn.exists()).toBe(true);
    expect(deleteBtn.attributes('aria-label')).toBe('Eliminar residente 1: María Pérez');

    await deleteBtn.trigger('click');

    expect(wrapper.emitted('eliminar')).toBeTruthy();
    expect(wrapper.emitted('eliminar')![0]).toEqual([0]);

    expect(wrapper.emitted('update:modelValue')).toBeTruthy();
    expect(wrapper.emitted('update:modelValue')![0][0]).toEqual([]);
  });

  it('bloquea números y caracteres no alfabéticos en el campo de nombre', async () => {
    const wrapper = mount(ResidentesCards, {
      props: {
        modelValue: []
      }
    });

    const nombreInput = wrapper.find<HTMLInputElement>('#residente-nombre');
    await nombreInput.setValue('María 123 P. #4!');
    expect(nombreInput.element.value).toBe('María  P. ');
  });

  it('aplica reglas de coherencia por edad para infante (< 5 años) ocultando licencia/vehículo y ajustando valores', async () => {
    const wrapper = mount(ResidentesCards, {
      props: { modelValue: [] }
    });

    await wrapper.find('#residente-nombre').setValue('Mateo Pérez');
    await wrapper.find('#residente-parentesco').setValue('3');
    await wrapper.find('#residente-sexo').setValue('1');
    await wrapper.find('#residente-edad').setValue(3);

    expect(wrapper.find('[data-testid="age-coherence-notice"]').text()).toContain('Menor de 5 años');
    expect(wrapper.find('#residente-licencia').exists()).toBe(false);
    expect(wrapper.find('#residente-vehiculo-disp').exists()).toBe(false);
    expect((wrapper.find('#residente-sabe-leer').element as HTMLSelectElement).disabled).toBe(true);
    expect((wrapper.find('#residente-medio-transporte').element as HTMLSelectElement).value).toBe('no_aplica');

    await wrapper.find('.add-residente-btn').trigger('click');
    const emitted = wrapper.emitted('update:modelValue') as any[][];
    expect(emitted).toBeTruthy();
    expect(emitted[0][0][0]).toMatchObject({
      nombres: 'Mateo Pérez',
      edad: 3,
      sabe_leer_escribir: 'no',
      nivel_educativo: 'ninguno',
      medio_transporte_habitual: 'no_aplica',
      posee_licencia: 'no',
      tiene_vehiculo_disponible: 'no'
    });
  });

  it('adapta etiqueta de transporte acompañado y filtra opciones ilógicas para niño de 8 años', async () => {
    const wrapper = mount(ResidentesCards, {
      props: { modelValue: [] }
    });

    await wrapper.find('#residente-edad').setValue(8);

    expect(wrapper.find('label[for="residente-medio-transporte"]').text()).toContain(
      'lo trasladan normalmente (acompañado)'
    );
    expect(wrapper.find('#residente-licencia').exists()).toBe(false);
    expect(wrapper.find('#residente-vehiculo-disp').exists()).toBe(false);

    const actividades = wrapper
      .findAll('#residente-actividad option')
      .map((o) => o.attributes('value'));
    expect(actividades).toContain('2'); // Estudia
    expect(actividades).not.toContain('1'); // Trabaja
    expect(actividades).not.toContain('4'); // Jubilado

    const niveles = wrapper
      .findAll('#residente-nivel-educativo option')
      .map((o) => o.attributes('value'));
    expect(niveles).toContain('primaria');
    expect(niveles).not.toContain('universitario');
  });
});
