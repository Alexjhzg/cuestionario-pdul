import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import SearchableSelect from '@/components/common/SearchableSelect.vue';

const sampleOptions = [
  { value: 'san_simon', label: 'San Simón' },
  { value: 'boqueron', label: 'Boquerón' },
  { value: 'las_cocuizas', label: 'Las Cocuizas' }
];

describe('SearchableSelect.vue — Campo de búsqueda integrado en selects', () => {
  it('filtra opciones normalizando tildes y mayúsculas y restaura al limpiar', async () => {
    const wrapper = mount(SearchableSelect, {
      props: {
        id: 'parroquia',
        modelValue: '',
        options: sampleOptions,
        placeholderOption: 'Seleccione su parroquia',
        searchPlaceholder: 'Buscar parroquia...'
      }
    });

    const searchInput = wrapper.get('input#parroquia-search');
    await searchInput.setValue('simon');

    const filteredTexts = wrapper
      .findAll('select#parroquia option')
      .map((o) => o.text());
    expect(filteredTexts).toContain('San Simón');
    expect(filteredTexts).not.toContain('Boquerón');
    expect(filteredTexts).not.toContain('Las Cocuizas');

    // Botón limpiar búsqueda restaura todas las opciones
    await wrapper.get('.searchable-clear-btn').trigger('click');
    const restoredTexts = wrapper
      .findAll('select#parroquia option')
      .map((o) => o.text());
    expect(restoredTexts).toContain('Boquerón');
    expect(restoredTexts).toContain('Las Cocuizas');
  });

  it('selecciona automáticamente la única coincidencia al presionar Enter y emite update:modelValue', async () => {
    const wrapper = mount(SearchableSelect, {
      props: {
        id: 'parroquia',
        modelValue: '',
        options: sampleOptions,
        placeholderOption: 'Seleccione su parroquia'
      }
    });

    const searchInput = wrapper.get('input#parroquia-search');
    await searchInput.setValue('boque');
    await searchInput.trigger('keydown', { key: 'Enter' });

    expect(wrapper.emitted('update:modelValue')).toEqual([['boqueron']]);
  });

  it('muestra mensaje claro cuando no hay coincidencias para el texto buscado', async () => {
    const wrapper = mount(SearchableSelect, {
      props: {
        id: 'parroquia',
        modelValue: '',
        options: sampleOptions
      }
    });

    await wrapper.get('input#parroquia-search').setValue('inexistente');
    expect(wrapper.get('select#parroquia').text()).toContain('Sin coincidencias para «inexistente»');
  });
});
