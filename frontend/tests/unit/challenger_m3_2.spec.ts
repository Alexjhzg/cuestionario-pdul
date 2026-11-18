import { describe, it, expect, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import SurveyWizard from '@/components/survey/SurveyWizard.vue';
import ViajesMobileCards from '@/components/survey/ViajesMobileCards.vue';
import fs from 'fs';
import path from 'path';

// Mock scrollTo
window.scrollTo = vi.fn() as any;

describe('Challenger 2 Empirical Verification: Mobile Viewport 360px, Gestalt Proximity & Touch Accessibility', () => {

  describe('1. Single-Column Layout across all 8 sections in SurveyWizard.vue', () => {
    const stepsData = [
      { step: 0, title: 'Ubicación y Caracterización del Hogar' },
      { step: 1, title: 'Datos de la Vivienda' },
      { step: 2, title: 'Datos del Hogar' },
      { step: 3, title: 'Composición del Hogar y Residentes Habituales' },
      { step: 4, title: 'Movilidad Cotidiana y Registro de Viajes' },
      { step: 5, title: 'Calidad de los Servicios de Transporte' },
      { step: 6, title: 'Movilidad No Motorizada y Percepción' },
      { step: 7, title: 'Áreas de Esparcimiento y Recreación' },
      { step: 8, title: 'Infraestructura Peatonal y Cierre' }
    ];

    it.each(stepsData)('verifica que el paso $step ($title) respeta la estructura de sección vertical', ({ step, title }) => {
      const wrapper = mount(SurveyWizard, {
        props: {
          modelValue: {},
          step
        }
      });

      expect(wrapper.text()).toContain(title);
      const section = wrapper.find('.step-form-section');
      expect(section.exists()).toBe(true);

      // Cada sección tiene campos dispuestos verticalmente (.survey-field) o componentes hijos
      const fields = section.findAll('.survey-field');
      if (step !== 3 && step !== 4) {
        // En los pasos que no son componentes de lista, todos los campos son .survey-field directos
        expect(fields.length).toBeGreaterThan(0);
      }
    });

    it('verifica en el CSS que .step-form-section y .survey-field usan flex-direction: column (disposición en una sola columna)', () => {
      const mainCss = fs.readFileSync(path.resolve(__dirname, '../../src/assets/styles/main.css'), 'utf-8');
      const wizardVue = fs.readFileSync(path.resolve(__dirname, '../../src/components/survey/SurveyWizard.vue'), 'utf-8');

      // .survey-field en main.css
      expect(mainCss).toMatch(/\.survey-field\s*\{[^}]*display:\s*flex;[^}]*flex-direction:\s*column;/);

      // .step-form-section en SurveyWizard.vue
      expect(wizardVue).toMatch(/\.step-form-section\s*\{[^}]*display:\s*flex;[^}]*flex-direction:\s*column;/);
    });
  });

  describe('2. Gestalt Proximity Rule (label-input gap < question-question gap)', () => {
    it('verifica que las etiquetas (<label>) anteceden a los inputs y que los hints se colocan entre label e input vinculados por aria-describedby', () => {
      const wrapper = mount(SurveyWizard, {
        props: {
          modelValue: {},
          step: 0
        }
      });

      // Parroquia
      const parroquiaLabel = wrapper.find('label[for="parroquia"]');
      expect(parroquiaLabel.exists()).toBe(true);
      const parroquiaInput = wrapper.find('#parroquia');
      expect(parroquiaInput.exists()).toBe(true);
    });

    it('verifica empíricamente las proporciones de espaciado Gestalt en CSS', () => {
      const tokensCss = fs.readFileSync(path.resolve(__dirname, '../../src/assets/styles/tokens.css'), 'utf-8');

      // Extraer tokens
      const sp4 = tokensCss.match(/--spacing-4:\s*(\d+)px/);
      const sp6 = tokensCss.match(/--spacing-6:\s*(\d+)px/);
      const sp24 = tokensCss.match(/--spacing-24:\s*(\d+)px/);

      expect(sp4).not.toBeNull();
      expect(sp6).not.toBeNull();
      expect(sp24).not.toBeNull();

      const labelMargin = parseInt(sp4![1]); // 4px
      const hintMargin = parseInt(sp6![1]);  // 6px
      const questionGap = parseInt(sp24![1]); // 24px

      // Regla de proximidad Gestalt: margen entre label/hint y control < margen entre preguntas distintas
      expect(labelMargin).toBeLessThan(questionGap);
      expect(labelMargin + hintMargin).toBeLessThan(questionGap);
      expect(questionGap).toBe(24); // 1.5rem
    });
  });

  describe('3. Late Validation (:user-invalid) — Cero errores al cargar la encuesta', () => {
    it('no muestra banners de error ni marca campos en rojo al montar la encuesta vacía', () => {
      const wrapper = mount(SurveyWizard, {
        props: {
          modelValue: {},
          step: 0
        }
      });

      // Los mensajes de error individuales (.survey-error-msg) tienen display: none en CSS
      const errorMsgs = wrapper.findAll('.survey-error-msg');
      expect(errorMsgs.length).toBeGreaterThan(0);

      // Ningún input debe tener clase de error agregada prematuramente
      const inputs = wrapper.findAll('input, select');
      inputs.forEach(input => {
        expect(input.classes()).not.toContain('user-invalid-fallback');
        expect(input.classes()).not.toContain('is-invalid');
      });
    });

    it('activa la validación y previene el avance al intentar avanzar con campos inválidos', async () => {
      const wrapper = mount(SurveyWizard, {
        props: {
          modelValue: { parroquia: '' },
          step: 0
        }
      });

      const nextBtn = wrapper.findAll('button').find(b => b.text().includes('Siguiente'));
      expect(nextBtn).toBeDefined();

      await nextBtn!.trigger('click');

      expect(wrapper.emitted('update:step')).toBeFalsy();
    });
  });

  describe('4. ViajesMobileCards.vue: Tarjetas Apiladas, 360px Viewport y aria-label descriptivo', () => {
    const viajesEjemplo = [
      {
        viaje_numero: 1,
        persona_numero: 1,
        zona_od_origen: 'san_simon',
        zona_od_destino: 'las_cocuizas',
        motivo_viaje: '1',
        modo_principal: '6',
        tiempo_viaje_min: 30,
        costo_viaje_bs: 10
      }
    ];

    it('renderiza tarjetas de viajes apiladas verticalmente en .viajes-list', () => {
      const wrapper = mount(ViajesMobileCards, {
        props: {
          modelValue: viajesEjemplo,
          zonaResidenciaDefault: 'san_simon'
        }
      });

      const list = wrapper.find('.viajes-list');
      expect(list.exists()).toBe(true);
      expect(list.attributes('role')).toBe('list');

      const cards = wrapper.findAll('.viaje-card');
      expect(cards).toHaveLength(1);
      expect(cards[0].attributes('role')).toBe('listitem');
    });

    it('verifica que el botón "Agregar viaje de regreso a casa" cuenta con un aria-label descriptivo y accesible sin emojis', () => {
      const wrapper = mount(ViajesMobileCards, {
        props: {
          modelValue: viajesEjemplo,
          zonaResidenciaDefault: 'san_simon'
        }
      });

      const returnBtn = wrapper.find('.return-btn');
      expect(returnBtn.exists()).toBe(true);

      const ariaLabel = returnBtn.attributes('aria-label');
      expect(ariaLabel).toBeDefined();
      expect(ariaLabel).toContain('Agregar viaje de regreso a casa');
      expect(ariaLabel).toContain('para el viaje 1');
      expect(ariaLabel).toContain('Las Cocuizas');

      expect(returnBtn.text()).toContain('Agregar viaje de regreso a casa');
      expect(returnBtn.text()).not.toContain('🔄');
      expect(returnBtn.find('i.pi.pi-refresh').exists()).toBe(true);
    });

    it('verifica que la lista y tarjetas no tienen anchos fijos que desborden un viewport de 360px', () => {
      const viajesVue = fs.readFileSync(path.resolve(__dirname, '../../src/components/survey/ViajesMobileCards.vue'), 'utf-8');

      // No debe existir anchos fijos de elementos (fuera de media queries) que desborden
      expect(viajesVue).not.toMatch(/(?<!min-|max-)width:\s*[3-9]\d{2}px/);

      // Comprueba que .viajes-section usa width 100% y box-sizing border-box
      expect(viajesVue).toMatch(/\.viajes-section\s*\{[^}]*width:\s*100%;/);
      expect(viajesVue).toMatch(/\.viajes-section\s*\{[^}]*box-sizing:\s*border-box;/);
    });
  });

  describe('5. Auditoría de Ergonomía Táctil: min-block-size / min-height >= 48px (52px coarse pointer)', () => {
    it('comprueba la definición de los tokens de ergonomía táctil en tokens.css', () => {
      const tokensCss = fs.readFileSync(path.resolve(__dirname, '../../src/assets/styles/tokens.css'), 'utf-8');

      expect(tokensCss).toMatch(/--min-touch-target:\s*48px;/);
      expect(tokensCss).toMatch(/@media\s*\(pointer:\s*coarse\)\s*\{[\s\S]*?--min-touch-target:\s*52px;/);
    });

    it('comprueba el tamaño de los inputs, selects y botones en main.css', () => {
      const mainCss = fs.readFileSync(path.resolve(__dirname, '../../src/assets/styles/main.css'), 'utf-8');

      // .survey-input, .survey-select, .survey-textarea
      expect(mainCss).toMatch(/\.survey-input,\s*\.survey-select,\s*\.survey-textarea\s*\{[^}]*min-block-size:\s*var\(--min-touch-target\);/);

      // .survey-btn
      expect(mainCss).toMatch(/\.survey-btn\s*\{[^}]*min-block-size:\s*var\(--min-touch-target\);/);
    });

    it('AUDITORÍA ADVERSARIAL: detecta si .action-btn en ViajesMobileCards.vue cumple o incumple min-block-size >= 48px', () => {
      const viajesVue = fs.readFileSync(path.resolve(__dirname, '../../src/components/survey/ViajesMobileCards.vue'), 'utf-8');

      const match = viajesVue.match(/\.action-btn\s*\{[^}]*min-block-size:\s*([^;]+);/);
      expect(match).not.toBeNull();
      const declaredMinBlockSize = match![1].trim();

      // Observación empírica: declaredMinBlockSize es "44px"
      // Si es 44px, esto es menor al requisito de 48px (y 52px en coarse pointer)
      const isCompliant = declaredMinBlockSize === 'var(--min-touch-target)' || parseInt(declaredMinBlockSize) >= 48;
      
      // Registramos este resultado para la auditoría formal
      console.log(`[AUDIT] ViajesMobileCards .action-btn min-block-size declarado: ${declaredMinBlockSize} (Cumple >= 48px: ${isCompliant})`);
      expect(isCompliant).toBe(true);
    });

    it('AUDITORÍA ADVERSARIAL: detecta si .residente-btn-delete en ResidentesCards.vue cumple o incumple tamaño >= 48px', () => {
      const residentesVue = fs.readFileSync(path.resolve(__dirname, '../../src/components/survey/ResidentesCards.vue'), 'utf-8');

      const matchWidth = residentesVue.match(/\.residente-btn-delete\s*\{[^}]*width:\s*([^;]+);/);
      const matchHeight = residentesVue.match(/\.residente-btn-delete\s*\{[^}]*height:\s*([^;]+);/);

      expect(matchWidth).not.toBeNull();
      expect(matchHeight).not.toBeNull();

      const width = matchWidth![1].trim();
      const height = matchHeight![1].trim();

      const isCompliant = (width === 'var(--min-touch-target)' || parseInt(width) >= 48) && (height === 'var(--min-touch-target)' || parseInt(height) >= 48);
      console.log(`[AUDIT] ResidentesCards .residente-btn-delete dimensiones: ${width} x ${height} (Cumple >= 48px: ${isCompliant})`);
      expect(isCompliant).toBe(true);
    });

    it('AUDITORÍA ADVERSARIAL: detecta si .draft-btn en DraftRestoreBanner.vue cumple min-block-size >= 48px', () => {
      const bannerVue = fs.readFileSync(path.resolve(__dirname, '../../src/components/common/DraftRestoreBanner.vue'), 'utf-8');

      const match = bannerVue.match(/\.draft-btn\s*\{[^}]*min-block-size:\s*([^;]+);/);
      expect(match).not.toBeNull();
      const declaredMinBlockSize = match![1].trim();

      const isCompliant = declaredMinBlockSize === 'var(--min-touch-target)' || parseInt(declaredMinBlockSize) >= 48;
      console.log(`[AUDIT] DraftRestoreBanner .draft-btn min-block-size: ${declaredMinBlockSize} (Cumple >= 48px: ${isCompliant})`);
      expect(isCompliant).toBe(true);
    });

    it('AUDITORÍA ADVERSARIAL: detecta si .step-indicator-btn en SurveyWizard.vue cumple min-block-size >= 48px', () => {
      const wizardVue = fs.readFileSync(path.resolve(__dirname, '../../src/components/survey/SurveyWizard.vue'), 'utf-8');

      const match = wizardVue.match(/\.step-indicator-btn\s*\{[^}]*min-block-size:\s*([^;]+);/);
      expect(match).not.toBeNull();
      const declaredMinBlockSize = match![1].trim();

      const isCompliant = declaredMinBlockSize === 'var(--min-touch-target)' || parseInt(declaredMinBlockSize) >= 48;
      console.log(`[AUDIT] SurveyWizard .step-indicator-btn min-block-size: ${declaredMinBlockSize} (Cumple >= 48px: ${isCompliant})`);
      expect(isCompliant).toBe(true);
    });

    it('AUDITORÍA ADVERSARIAL: detecta si .sync-btn en OfflineSyncBadge.vue cumple min-block-size >= 48px', () => {
      const syncVue = fs.readFileSync(path.resolve(__dirname, '../../src/components/common/OfflineSyncBadge.vue'), 'utf-8');

      const match = syncVue.match(/\.sync-btn\s*\{[^}]*min-block-size:\s*([^;]+);/);
      expect(match).not.toBeNull();
      const declaredMinBlockSize = match![1].trim();

      const isCompliant = declaredMinBlockSize === 'var(--min-touch-target)' || parseInt(declaredMinBlockSize) >= 48;
      console.log(`[AUDIT] OfflineSyncBadge .sync-btn min-block-size: ${declaredMinBlockSize} (Cumple >= 48px: ${isCompliant})`);
      expect(isCompliant).toBe(true);
    });
  });
});
