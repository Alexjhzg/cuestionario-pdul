import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import QuestionChartCard from '@/components/dashboard/QuestionChartCard.vue';
import type { PreguntaMetricaItem } from '@/services/analyticsApi';

// Polyfill de ResizeObserver para happy-dom
class ResizeObserverMock {
  callback: ResizeObserverCallback;
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
  constructor(cb: ResizeObserverCallback) {
    this.callback = cb;
  }
}

// Polyfill de Canvas 2D
if (typeof HTMLCanvasElement !== 'undefined' && !HTMLCanvasElement.prototype.getContext) {
  HTMLCanvasElement.prototype.getContext = vi.fn(() => ({
    fillRect: vi.fn(),
    clearRect: vi.fn(),
    measureText: vi.fn(() => ({ width: 50 }))
  })) as any;
}

global.ResizeObserver = ResizeObserverMock as any;

describe('QuestionChartCard.vue - Gráficos de Preguntas Individuales', () => {
  const mockDonutItem: PreguntaMetricaItem = {
    seccion: 'Sección VI: Características de Transporte Público',
    clave: 'calificacion_servicio_tp',
    pregunta: '6.- ¿Considera que el servicio de transporte público es:',
    tipo_grafico: 'donut',
    total_respuestas: 124,
    labels: ['Regular', 'Malo', 'Bueno', 'Muy Bueno'],
    values: [57, 33, 28, 6]
  };

  const mockBarItem: PreguntaMetricaItem = {
    seccion: 'Sección I: Identificación de la Unidad Residencial',
    clave: 'parroquia',
    pregunta: '1.- Parroquia de residencia',
    tipo_grafico: 'bar',
    total_respuestas: 124,
    labels: ['San Simón', 'Alto de los Godos', 'Las Cocuizas'],
    values: [55, 28, 15]
  };

  const mockEmptyItem: PreguntaMetricaItem = {
    seccion: 'Sección VIII: Esparcimientos y Peatonalidad',
    clave: 'cruce_demarcado_visible',
    pregunta: '21.- ¿Está demarcado y visible?',
    tipo_grafico: 'donut',
    total_respuestas: 0,
    labels: [],
    values: []
  };

  it('1. Renderiza el texto exacto de la pregunta, sección y badge de respuestas', () => {
    const wrapper = mount(QuestionChartCard, {
      props: { item: mockDonutItem }
    });

    expect(wrapper.find('.question-title').text()).toBe(
      '6.- ¿Considera que el servicio de transporte público es:'
    );
    expect(wrapper.find('.section-tag').text()).toContain(
      'Sección VI: Características de Transporte Público'
    );
    expect(wrapper.find('.total-tag').text()).toContain('124 respuestas');
    expect(wrapper.attributes('aria-label')).toContain(
      '6.- ¿Considera que el servicio de transporte público es:'
    );
  });

  it('2. Monta correctamente un gráfico de tipo barra con sus datos', () => {
    const wrapper = mount(QuestionChartCard, {
      props: { item: mockBarItem }
    });

    expect(wrapper.find('.question-title').text()).toBe('1.- Parroquia de residencia');
    expect(wrapper.find('.chart-canvas').exists()).toBe(true);
  });

  it('3. Maneja estado vacío cuando no hay respuestas registradas', () => {
    const wrapper = mount(QuestionChartCard, {
      props: { item: mockEmptyItem }
    });

    expect(wrapper.find('.total-tag').text()).toContain('0 respuestas');
    expect(wrapper.find('.chart-canvas').exists()).toBe(true);
  });

  it('4. Desmonta limpiamente liberando ResizeObserver y ECharts', () => {
    const wrapper = mount(QuestionChartCard, {
      props: { item: mockDonutItem }
    });

    expect(() => wrapper.unmount()).not.toThrow();
  });
});
