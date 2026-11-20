import { describe, it, expect, afterEach, vi } from 'vitest';
import { mount, type VueWrapper } from '@vue/test-utils';
import QuestionHelpTip from '@/components/common/QuestionHelpTip.vue';
import Step2Vivienda from '@/components/survey/sections/Step2Vivienda.vue';
import Step6TransportePublico from '@/components/survey/sections/Step6TransportePublico.vue';
import Step7MovilidadActiva from '@/components/survey/sections/Step7MovilidadActiva.vue';
import Step8Esparcimiento from '@/components/survey/sections/Step8Esparcimiento.vue';
import Step9Peatones from '@/components/survey/sections/Step9Peatones.vue';
import { QUESTION_HELP_TIPS } from '@/utils/questionHelpCatalog';

const mountedWrappers: VueWrapper[] = [];

function trackMount<T extends VueWrapper>(wrapper: T): T {
  mountedWrappers.push(wrapper);
  return wrapper;
}

afterEach(() => {
  vi.useRealTimers();
  while (mountedWrappers.length > 0) {
    mountedWrappers.pop()?.unmount();
  }
});

describe('QuestionHelpTip.vue — Toggletip accesible (?)', () => {
  it('inicia cerrado con aria-expanded="false" y despliega role="tooltip" al pulsar ?', async () => {
    const wrapper = trackMount(
      mount(QuestionHelpTip, {
        attachTo: document.body,
        props: {
          text: 'Explicación ciudadana de prueba.',
          questionLabel: 'espacios de la vivienda'
        }
      })
    );

    const btn = wrapper.get('[data-testid="btn-question-help"]');
    expect(btn.text()).toContain('?');
    expect(btn.attributes('aria-expanded')).toBe('false');
    expect(btn.attributes('aria-label')).toContain('espacios de la vivienda');
    expect(wrapper.find('[data-testid="question-help-popover"]').exists()).toBe(false);

    const tipId = btn.attributes('aria-controls');
    expect(tipId).toBeTruthy();

    await btn.trigger('click');

    expect(btn.attributes('aria-expanded')).toBe('true');
    const popover = wrapper.get('[data-testid="question-help-popover"]');
    expect(popover.attributes('role')).toBe('tooltip');
    expect(popover.attributes('id')).toBe(tipId);
    expect(popover.text()).toContain('Explicación ciudadana de prueba.');
  });

  it('cierra al presionar Escape y devuelve el foco al botón ?', async () => {
    const wrapper = trackMount(
      mount(QuestionHelpTip, {
        attachTo: document.body,
        props: {
          text: 'Descripción detallada.',
          questionLabel: 'pregunta de prueba'
        }
      })
    );

    const btn = wrapper.get('[data-testid="btn-question-help"]');
    await btn.trigger('click');
    expect(wrapper.find('[data-testid="question-help-popover"]').exists()).toBe(true);

    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
    await wrapper.vm.$nextTick();

    expect(wrapper.find('[data-testid="question-help-popover"]').exists()).toBe(false);
    expect(btn.attributes('aria-expanded')).toBe('false');
    expect(document.activeElement).toBe(btn.element);
  });

  it('cierra al hacer clic en el botón de cierre o fuera del componente', async () => {
    const wrapper = trackMount(
      mount(QuestionHelpTip, {
        attachTo: document.body,
        props: {
          text: 'Texto de ayuda.'
        }
      })
    );

    const btn = wrapper.get('[data-testid="btn-question-help"]');
    await btn.trigger('click');
    await wrapper.get('.question-help-close').trigger('click');
    expect(wrapper.find('[data-testid="question-help-popover"]').exists()).toBe(false);
    expect(document.activeElement).toBe(btn.element);

    await btn.trigger('click');
    expect(wrapper.find('[data-testid="question-help-popover"]').exists()).toBe(true);
    document.body.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    await wrapper.vm.$nextTick();
    expect(wrapper.find('[data-testid="question-help-popover"]').exists()).toBe(false);
  });

  it('permite un solo tooltip abierto a la vez (cerrando el anterior al abrir uno nuevo)', async () => {
    const wrapperA = trackMount(
      mount(QuestionHelpTip, {
        attachTo: document.body,
        props: {
          text: 'Ayuda A',
          questionLabel: 'Pregunta A'
        }
      })
    );
    const wrapperB = trackMount(
      mount(QuestionHelpTip, {
        attachTo: document.body,
        props: {
          text: 'Ayuda B',
          questionLabel: 'Pregunta B'
        }
      })
    );

    const btnA = wrapperA.get('[data-testid="btn-question-help"]');
    const btnB = wrapperB.get('[data-testid="btn-question-help"]');

    // Abrir A
    await btnA.trigger('click');
    expect(wrapperA.find('[data-testid="question-help-popover"]').exists()).toBe(true);
    expect(wrapperB.find('[data-testid="question-help-popover"]').exists()).toBe(false);

    // Abrir B -> Debe cerrar A inmediatamente
    await btnB.trigger('click');
    expect(wrapperA.find('[data-testid="question-help-popover"]').exists()).toBe(false);
    expect(wrapperB.find('[data-testid="question-help-popover"]').exists()).toBe(true);
  });

  it('cierra automáticamente el tooltip después de 5 segundos (5000ms)', async () => {
    vi.useFakeTimers();

    const wrapper = trackMount(
      mount(QuestionHelpTip, {
        attachTo: document.body,
        props: {
          text: 'Ayuda con temporizador',
          questionLabel: 'Pregunta Temporal',
          autoCloseMs: 5000
        }
      })
    );

    const btn = wrapper.get('[data-testid="btn-question-help"]');
    await btn.trigger('click');
    expect(wrapper.find('[data-testid="question-help-popover"]').exists()).toBe(true);

    // Avanzar 4.9 segundos: debe seguir abierto
    vi.advanceTimersByTime(4900);
    await wrapper.vm.$nextTick();
    expect(wrapper.find('[data-testid="question-help-popover"]').exists()).toBe(true);

    // Avanzar 200 ms más (total > 5000ms): debe cerrarse
    vi.advanceTimersByTime(200);
    await wrapper.vm.$nextTick();
    expect(wrapper.find('[data-testid="question-help-popover"]').exists()).toBe(false);
    expect(btn.attributes('aria-expanded')).toBe('false');
  });
});

describe('Sección II Q2 reformulada y tooltips en secciones del cuestionario', () => {
  it('renderiza la pregunta 2 de Sección II con el término «espacios» y sin botones anidados en <label>', async () => {
    const wrapper = trackMount(
      mount(Step2Vivienda, {
        attachTo: document.body,
        props: {
          modelValue: {
            tipo_vivienda: '',
            total_cuartos_vivienda: ''
          }
        }
      })
    );

    const labelQ2 = wrapper.get('label[for="total_cuartos_vivienda"]');
    expect(labelQ2.text()).toContain(
      'Contando sala-comedor, cuartos para dormir y otros cuartos, ¿cuántos espacios tiene en total la vivienda?'
    );
    expect(wrapper.get('#total_cuartos_vivienda').attributes('placeholder')).toContain('espacios');
    expect(wrapper.findAll('label button')).toHaveLength(0);

    const helpButtons = wrapper.findAll('[data-testid="btn-question-help"]');
    expect(helpButtons).toHaveLength(2);

    await helpButtons[1].trigger('click');
    expect(wrapper.get('[data-testid="question-help-popover"]').text()).toBe(
      QUESTION_HELP_TIPS.total_cuartos_vivienda
    );
  });

  it('integra íconos de ayuda ? en Secciones VI, VII, VIII y IX sin anidar botones dentro de <label>', () => {
    const step6 = trackMount(mount(Step6TransportePublico, { props: { modelValue: { dificultades_acceso_tp: 'si' } } }));
    const step7 = trackMount(mount(Step7MovilidadActiva, { props: { modelValue: { cambio_movilidad_5_anos: 'si' } } }));
    const step8 = trackMount(mount(Step8Esparcimiento, { props: { modelValue: {} } }));
    const step9 = trackMount(mount(Step9Peatones, { props: { modelValue: { cruce_peatonal_todas: 'si' } } }));

    expect(step6.findAll('[data-testid="btn-question-help"]').length).toBe(10);
    expect(step7.findAll('[data-testid="btn-question-help"]').length).toBe(8);
    expect(step8.findAll('[data-testid="btn-question-help"]').length).toBe(16);
    expect(step9.findAll('[data-testid="btn-question-help"]').length).toBe(14);

    expect(step6.findAll('label button')).toHaveLength(0);
    expect(step7.findAll('label button')).toHaveLength(0);
    expect(step8.findAll('label button')).toHaveLength(0);
    expect(step9.findAll('label button')).toHaveLength(0);
  });
});

