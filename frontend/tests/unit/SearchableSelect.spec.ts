import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import SearchableSelect from '@/components/common/SearchableSelect.vue';

const sampleOptions = [
  { value: 'san_simon', label: 'San Simón' },
  { value: 'boqueron', label: 'Boquerón' },
  { value: 'las_cocuizas', label: 'Las Cocuizas' }
];

describe('SearchableSelect.vue — Buscador integrado dentro del propio selector', () => {
  it('inicia cerrado sin campo de búsqueda visible arriba y despliega el buscador adentro al hacer clic', async () => {
    const wrapper = mount(SearchableSelect, {
      attachTo: document.body,
      props: {
        id: 'parroquia',
        modelValue: '',
        options: sampleOptions,
        placeholderOption: 'Seleccione su parroquia',
        searchPlaceholder: 'Buscar parroquia...'
      }
    });

    // Cerrado: no hay buscador ni panel desplegable visible
    expect(wrapper.find('[data-testid="searchable-dropdown-panel"]').exists()).toBe(false);
    expect(wrapper.find('input#parroquia-search').exists()).toBe(false);

    // Al pulsar el selector, se abre el panel con el buscador integrado adentro
    await wrapper.get('[data-testid="parroquia-trigger"]').trigger('click');
    const panel = wrapper.get('[data-testid="searchable-dropdown-panel"]');
    const searchInput = panel.get('input#parroquia-search');

    await searchInput.setValue('simon');
    const optionButtons = panel.findAll('[role="option"]').map((b) => b.text());
    expect(optionButtons).toEqual(['San Simón']);

    // Al seleccionar la opción se emite update:modelValue y se cierra el desplegable
    await panel.get('[role="option"]').trigger('click');
    expect(wrapper.emitted('update:modelValue')).toEqual([['san_simon']]);
    expect(wrapper.find('[data-testid="searchable-dropdown-panel"]').exists()).toBe(false);

    wrapper.unmount();
  });

  it('selecciona automáticamente la única coincidencia al presionar Enter dentro del buscador', async () => {
    const wrapper = mount(SearchableSelect, {
      props: {
        id: 'parroquia',
        modelValue: '',
        options: sampleOptions,
        placeholderOption: 'Seleccione su parroquia'
      }
    });

    await wrapper.get('[data-testid="parroquia-trigger"]').trigger('click');
    const searchInput = wrapper.get('input#parroquia-search');
    await searchInput.setValue('boque');
    await searchInput.trigger('keydown', { key: 'Enter' });

    expect(wrapper.emitted('update:modelValue')).toEqual([['boqueron']]);
    expect(wrapper.find('[data-testid="searchable-dropdown-panel"]').exists()).toBe(false);
  });

  it('muestra mensaje claro cuando no hay coincidencias y restaura al limpiar', async () => {
    const wrapper = mount(SearchableSelect, {
      props: {
        id: 'parroquia',
        modelValue: '',
        options: sampleOptions
      }
    });

    await wrapper.get('[data-testid="parroquia-trigger"]').trigger('click');
    await wrapper.get('input#parroquia-search').setValue('inexistente');
    expect(wrapper.get('[data-testid="searchable-dropdown-panel"]').text()).toContain(
      'Sin coincidencias para «inexistente»'
    );

    await wrapper.get('.searchable-clear-btn').trigger('click');
    expect(wrapper.findAll('[role="option"]')).toHaveLength(3);
  });
});
