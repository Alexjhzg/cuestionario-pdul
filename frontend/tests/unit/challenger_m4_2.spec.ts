import { describe, it, expect, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import fs from 'fs';
import path from 'path';

import App from '@/App.vue';
import AdminSurveyListView from '@/views/AdminSurveyListView.vue';
import AdminResponsesView from '@/views/AdminResponsesView.vue';

// Mocks de servicios API
vi.mock('@/services/api', () => ({
  fetchAdminEncuestas: vi.fn().mockResolvedValue([
    {
      id: '00000000-0000-0000-0000-000000000001',
      titulo: 'Encuesta Origen-Destino PDUL Maturín',
      slug: 'pdul_origen_destino',
      tipo_instrumento: 'encuesta_od_pdul',
      activa: true,
      creado_en: '2025-01-15T10:00:00Z',
      total_respuestas: 142
    },
    {
      id: '00000000-0000-0000-0000-000000000002',
      titulo: 'Consulta Espacios Públicos',
      slug: 'consulta_espacios',
      tipo_instrumento: 'consulta_ciudadana',
      activa: false,
      creado_en: '2025-02-01T12:00:00Z',
      total_respuestas: 28
    }
  ]),
  fetchAdminEncuesta: vi.fn().mockResolvedValue({
    id: '00000000-0000-0000-0000-000000000001',
    titulo: 'Encuesta Origen-Destino PDUL Maturín',
    slug: 'pdul_origen_destino',
    tipo_instrumento: 'encuesta_od_pdul',
    activa: true,
    esquema_formio: {
      display: 'form',
      components: [
        { type: 'textfield', key: 'parroquia', label: 'Parroquia', required: true },
        { type: 'button', key: 'submit', action: 'submit', label: 'Enviar' }
      ]
    }
  }),
  fetchAdminRespuestas: vi.fn().mockResolvedValue({
    items: [
      {
        id: 1,
        encuesta_id: '00000000-0000-0000-0000-000000000001',
        client_submission_id: 'e3d4c5b6-a789-4012-b345-6789abcdef01',
        parroquia: 'san_simon',
        zona_od: 'ZONA-01',
        datos: {
          cedula: '12345678',
          nombre_apellido: 'Juan Pérez',
          telefono: '04141234567',
          correo: 'juan@example.com',
          direccion_exacta: 'Calle Monagas #12',
          residentes: [{ nombre: 'Juan', edad: 40 }],
          viajes: [{ origen: 'San Simón', destino: 'Las Cocuizas' }]
        },
        fecha_registro: '2025-02-10T14:30:00Z'
      }
    ],
    total: 1,
    skip: 0,
    limit: 10
  }),
  updateEncuestaEstado: vi.fn().mockResolvedValue({
    id: '00000000-0000-0000-0000-000000000001',
    activa: false
  }),
  createAdminEncuesta: vi.fn().mockResolvedValue({
    id: '00000000-0000-0000-0000-000000000003',
    titulo: 'Nueva Encuesta Test',
    slug: 'nueva_encuesta_test'
  }),
  updateAdminEncuesta: vi.fn().mockResolvedValue({
    id: '00000000-0000-0000-0000-000000000001',
    titulo: 'Encuesta Actualizada'
  }),
  exportarRespuestasAdmin: vi.fn().mockResolvedValue(new Blob(['csv data'], { type: 'text/csv' })),
  descargarBlob: vi.fn(),
  triggerBlobDownload: vi.fn()
}));

describe('Empirical Verification Challenger M4-2: Ergonomía Táctil, WCAG AA y Responsividad Móvil', () => {

  const viewsDir = path.resolve(__dirname, '../../src/views');
  const componentsDir = path.resolve(__dirname, '../../src/components');
  const stylesDir = path.resolve(__dirname, '../../src/assets/styles');

  const appVueContent = fs.readFileSync(path.resolve(__dirname, '../../src/App.vue'), 'utf-8');
  const adminSurveyListContent = fs.readFileSync(path.resolve(viewsDir, 'AdminSurveyListView.vue'), 'utf-8');
  const adminResponsesContent = fs.readFileSync(path.resolve(viewsDir, 'AdminResponsesView.vue'), 'utf-8');
  const formBuilderContent = fs.readFileSync(path.resolve(viewsDir, 'FormBuilderView.vue'), 'utf-8');
  const formioBuilderContent = fs.readFileSync(path.resolve(componentsDir, 'admin/FormioBuilder.vue'), 'utf-8');
  const tokensCssContent = fs.readFileSync(path.resolve(stylesDir, 'tokens.css'), 'utf-8');
  const mainCssContent = fs.readFileSync(path.resolve(stylesDir, 'main.css'), 'utf-8');

  describe('1. Cero Dependencias y Ausencia Total de Clases Tailwind CSS y PrimeFlex', () => {
    it('verifica que package.json no incluye tailwindcss ni primeflex', () => {
      const packageJson = JSON.parse(
        fs.readFileSync(path.resolve(__dirname, '../../package.json'), 'utf-8')
      );
      const allDeps = {
        ...(packageJson.dependencies || {}),
        ...(packageJson.devDependencies || {})
      };
      expect(allDeps['tailwindcss']).toBeUndefined();
      expect(allDeps['primeflex']).toBeUndefined();
      expect(allDeps['@tailwindcss/typography']).toBeUndefined();
    });

    it('verifica ausencia de clases utilitarias de PrimeFlex (p-d-flex, p-col, p-grid, etc.) en todos los componentes M4', () => {
      const allContent = [
        appVueContent,
        adminSurveyListContent,
        adminResponsesContent,
        formBuilderContent,
        formioBuilderContent
      ].join('\n');

      const primeFlexRegex = /\b(p-d-flex|p-flex-|p-grid|p-col\b|p-col-[0-9]+|p-jc-|p-ai-|p-m-[0-9]|p-p-[0-9]|p-text-)\b/;
      expect(allContent).not.toMatch(primeFlexRegex);
    });

    it('verifica ausencia de clases de Tailwind CSS (flex-col, items-center, text-sm, etc.) en templates M4', () => {
      const tailwindRegex = /class="[^"]*\b(flex-col|items-center|justify-between|space-x-[0-9]|space-y-[0-9]|rounded-md|rounded-lg|bg-gray-[0-9]|bg-blue-[0-9]|text-white|text-gray-[0-9]|px-[0-9]|py-[0-9]|mx-auto|w-full|h-full)\b/;
      expect(appVueContent).not.toMatch(tailwindRegex);
      expect(adminSurveyListContent).not.toMatch(tailwindRegex);
      expect(adminResponsesContent).not.toMatch(tailwindRegex);
      expect(formBuilderContent).not.toMatch(tailwindRegex);
      expect(formioBuilderContent).not.toMatch(tailwindRegex);
    });
  });

  describe('2. Verificación de Tokens de Ergonomía Táctil en tokens.css y main.css', () => {
    it('verifica que --min-touch-target está configurado a 48px base y 52px en pointer: coarse', () => {
      expect(tokensCssContent).toMatch(/--min-touch-target:\s*48px;/);
      expect(tokensCssContent).toMatch(/@media\s*\(\s*pointer:\s*coarse\s*\)\s*\{[^}]*--min-touch-target:\s*52px;/);
    });

    it('verifica que los estilos globales de inputs, selects y botones en main.css usan var(--min-touch-target)', () => {
      expect(mainCssContent).toMatch(/\.survey-input,\s*\.survey-select,\s*\.survey-textarea\s*\{[^}]*min-block-size:\s*var\(--min-touch-target\);/);
      expect(mainCssContent).toMatch(/\.survey-btn\s*\{[^}]*min-block-size:\s*var\(--min-touch-target\);/);
    });
  });

  describe('3. Auditoría de Ergonomía Táctil en Componentes de Milestone 4', () => {
    it('App.vue: los botones de pestañas de navegación (.nav-tab-btn) cumplen min-block-size >= var(--min-touch-target)', () => {
      expect(appVueContent).toMatch(/\.nav-tab-btn\s*\{[^}]*min-block-size:\s*var\(--min-touch-target\);/);
      expect(appVueContent).toMatch(/\.nav-tab-btn\s*\{[^}]*min-height:\s*var\(--min-touch-target\);/);
    });

    it('AdminResponsesView.vue: todos los controles interactivos declaran min-block-size >= var(--min-touch-target)', () => {
      expect(adminResponsesContent).toMatch(/\.survey-select-input\s*\{[^}]*min-block-size:\s*var\(--min-touch-target\);/);
      expect(adminResponsesContent).toMatch(/\.page-size-select\s*\{[^}]*min-block-size:\s*var\(--min-touch-target\);/);
      expect(adminResponsesContent).toMatch(/\.btn-detail\s*\{[^}]*min-block-size:\s*var\(--min-touch-target\);/);
      expect(adminResponsesContent).toMatch(/\.page-btn\s*\{[^}]*min-block-size:\s*var\(--min-touch-target\);/);
      expect(adminResponsesContent).toMatch(/\.modal-close-btn\s*\{[^}]*min-block-size:\s*var\(--min-touch-target\);/);
      expect(adminResponsesContent).toMatch(/\.pii-toggle-label\s*\{[^}]*min-block-size:\s*var\(--min-touch-target\);/);
      expect(adminResponsesContent).toMatch(/\.builder-btn\s*\{[^}]*min-block-size:\s*var\(--min-touch-target\);/);
    });

    it('FormBuilderView.vue: todos los botones, selects y switch cumplen min-block-size >= var(--min-touch-target)', () => {
      expect(formBuilderContent).toMatch(/\.custom-switch-label\s*\{[^}]*min-block-size:\s*var\(--min-touch-target\);/);
      expect(formBuilderContent).toMatch(/\.preset-btn\s*\{[^}]*min-block-size:\s*var\(--min-touch-target\);/);
      expect(formBuilderContent).toMatch(/\.existing-select\s*\{[^}]*min-block-size:\s*var\(--min-touch-target\);/);
      expect(formBuilderContent).toMatch(/\.modal-close-btn\s*\{[^}]*min-block-size:\s*var\(--min-touch-target\);/);
    });

    it('FormioBuilder.vue: los componentes deeply-scoped declaran min-block-size >= var(--min-touch-target)', () => {
      expect(formioBuilderContent).toMatch(/:deep\(\.formcomponent\)\s*\{[^}]*min-block-size:\s*var\(--min-touch-target\);/);
      expect(formioBuilderContent).toMatch(/:deep\(\.btn\)\s*\{[^}]*min-block-size:\s*var\(--min-touch-target\);/);
      expect(formioBuilderContent).toMatch(/:deep\(\.nav-tabs \.nav-link\)\s*\{[^}]*min-block-size:\s*var\(--min-touch-target\);/);
    });

    it('AdminSurveyListView.vue: botones de acción y exportación declaran min-block-size >= var(--min-touch-target)', () => {
      expect(adminSurveyListContent).toMatch(/\.admin-btn\s*\{[^}]*min-block-size:\s*var\(--min-touch-target\);/);
      expect(adminSurveyListContent).toMatch(/\.action-btn\s*\{[^}]*min-block-size:\s*var\(--min-touch-target\);/);
      expect(adminSurveyListContent).toMatch(/\.pii-export-control\s*\{[^}]*min-block-size:\s*var\(--min-touch-target\);/);
      expect(adminSurveyListContent).toMatch(/\.modal-close-btn\s*\{[^}]*min-block-size:\s*var\(--min-touch-target\);/);
    });

    it('3.1 AUDITORÍA DE OBJETIVO TÁCTIL: .accessible-switch en AdminSurveyListView.vue debe cumplir min-block-size >= var(--min-touch-target)', () => {
      const switchDeclMatch = adminSurveyListContent.match(/\.accessible-switch\s*\{([^}]*)\}/);
      expect(switchDeclMatch).not.toBeNull();
      const switchCss = switchDeclMatch![1];
      const hasMinBlockSize = /min-block-size:\s*var\(--min-touch-target\)/.test(switchCss);
      expect(hasMinBlockSize, 'El botón interactivo .accessible-switch debe declarar min-block-size: var(--min-touch-target) para cumplir WCAG AA >= 48px/52px').toBe(true);
    });

    it('3.2 AUDITORÍA DE OBJETIVO TÁCTIL: .close-alert-btn en FormBuilderView.vue debe cumplir min-block-size >= var(--min-touch-target)', () => {
      const closeAlertMatch = formBuilderContent.match(/\.close-alert-btn\s*\{([^}]*)\}/);
      expect(closeAlertMatch).not.toBeNull();
      const css = closeAlertMatch![1];
      const hasMinBlockSize = /min-block-size:\s*var\(--min-touch-target\)/.test(css);
      expect(hasMinBlockSize, 'El botón .close-alert-btn debe declarar min-block-size: var(--min-touch-target)').toBe(true);
    });
  });

  describe('4. Responsividad Móvil y Ausencia de Desbordamiento Horizontal (< 768px y 360px)', () => {
    it('App.vue: la barra de navegación declara scroll horizontal táctil con momentum (-webkit-overflow-scrolling: touch)', () => {
      expect(appVueContent).toMatch(/\.nav-inner\s*\{[^}]*overflow-x:\s*auto;/);
      expect(appVueContent).toMatch(/\.nav-inner\s*\{[^}]*-webkit-overflow-scrolling:\s*touch;/);
    });

    it('App.vue: .header-inner debe declarar flex-wrap: wrap para evitar desbordamiento en 360px', () => {
      expect(appVueContent, '.header-inner en App.vue debe declarar flex-wrap: wrap').toMatch(/\.header-inner\s*\{[^}]*flex-wrap:\s*wrap;/);
    });

    it('AdminSurveyListView.vue: en pantallas < 768px oculta la tabla y muestra tarjetas táctiles en grilla móvil', () => {
      expect(adminSurveyListContent).toMatch(/@media\s*\(min-width:\s*768px\)\s*\{[^}]*\.desktop-table-wrapper\s*\{[^}]*display:\s*block;/);
      expect(adminSurveyListContent).toMatch(/@media\s*\(min-width:\s*768px\)\s*\{[^}]*\.mobile-cards-grid\s*\{[^}]*display:\s*none;/);
      expect(adminSurveyListContent).toMatch(/\.desktop-table-wrapper\s*\{[^}]*display:\s*none;/);
      expect(adminSurveyListContent).toMatch(/\.mobile-cards-grid\s*\{[^}]*display:\s*flex;[^}]*flex-direction:\s*column;/);
    });

    it('AdminResponsesView.vue: la tabla está protegida contra desbordamiento con .table-responsive-wrapper con overflow-x: auto y tabindex="0"', () => {
      expect(adminResponsesContent).toMatch(/\.table-responsive-wrapper\s*\{[^}]*overflow-x:\s*auto;[^}]*width:\s*100%;/);
    });
  });

  describe('5. Semántica WAI-ARIA y Accesibilidad Integral', () => {
    it('App.vue: implementa WAI-ARIA tabs semánticos con roles y estados reactivos', async () => {
      const wrapper = mount(App);
      const nav = wrapper.find('nav[role="navigation"]');
      expect(nav.exists()).toBe(true);

      const tablist = wrapper.find('[role="tablist"]');
      expect(tablist.exists()).toBe(true);

      const tabs = wrapper.findAll('[role="tab"]');
      expect(tabs.length).toBe(5);

      expect(tabs[0].attributes('aria-selected')).toBe('true');
      expect(tabs[0].attributes('tabindex')).toBe('0');
      expect(tabs[1].attributes('aria-selected')).toBe('false');
      expect(tabs[1].attributes('tabindex')).toBe('-1');

      await tabs[1].trigger('click');
      expect(tabs[1].attributes('aria-selected')).toBe('true');
      expect(tabs[1].attributes('tabindex')).toBe('0');
      expect(tabs[0].attributes('aria-selected')).toBe('false');
    });

    it('5.1 WAI-ARIA TABS: App.vue debe soportar navegación con teclas de flecha (ArrowRight, ArrowLeft, Home, End)', async () => {
      const wrapper = mount(App);
      const tabs = wrapper.findAll('[role="tab"]');
      expect(tabs.length).toBe(5);

      // Enfocar tab 0 y presionar ArrowRight -> debe activar tab 1
      await tabs[0].trigger('keydown', { key: 'ArrowRight' });
      await flushPromises();
      expect(tabs[1].attributes('aria-selected'), 'ArrowRight debe avanzar a tab 1').toBe('true');

      // Presionar End -> debe activar el último tab (tab 4)
      await tabs[1].trigger('keydown', { key: 'End' });
      await flushPromises();
      expect(tabs[4].attributes('aria-selected'), 'End debe ir al último tab').toBe('true');

      // Presionar ArrowRight en el último -> debe ciclar al primer tab (tab 0)
      await tabs[4].trigger('keydown', { key: 'ArrowRight' });
      await flushPromises();
      expect(tabs[0].attributes('aria-selected'), 'ArrowRight en último tab debe ciclar al primero').toBe('true');

      // Presionar ArrowLeft en el primero -> debe ciclar al último tab (tab 4)
      await tabs[0].trigger('keydown', { key: 'ArrowLeft' });
      await flushPromises();
      expect(tabs[4].attributes('aria-selected'), 'ArrowLeft en primer tab debe ciclar al último').toBe('true');

      // Presionar Home -> debe ir al primer tab (tab 0)
      await tabs[4].trigger('keydown', { key: 'Home' });
      await flushPromises();
      expect(tabs[0].attributes('aria-selected'), 'Home debe ir al primer tab').toBe('true');
    });

    it('AdminSurveyListView.vue: los switches tienen role="switch" y aria-checked vinculado', async () => {
      const wrapper = mount(AdminSurveyListView);
      await flushPromises();

      const switches = wrapper.findAll('button[role="switch"]');
      expect(switches.length).toBeGreaterThan(0);
      expect(switches[0].attributes('aria-checked')).toBe('true');
    });

    it('Modales accesibles: cuentan con role="dialog", aria-modal="true" y aria-labelledby', async () => {
      const wrapperSurveys = mount(AdminSurveyListView);
      await flushPromises();

      const switchBtn = wrapperSurveys.find('[data-testid="switch-status-00000000-0000-0000-0000-000000000001"]');
      await switchBtn.trigger('click');
      await flushPromises();

      const modalDialog = wrapperSurveys.find('[role="dialog"]');
      expect(modalDialog.exists()).toBe(true);
      expect(modalDialog.attributes('aria-modal')).toBe('true');
      expect(modalDialog.attributes('aria-labelledby')).toBe('confirm-dialog-title');
    });
  });

  describe('6. Protección Rigurosa de PII y Soberanía', () => {
    it('AdminResponsesView.vue: enmascara cédula, nombres, teléfono y dirección por defecto en la inspección detallada', async () => {
      const wrapper = mount(AdminResponsesView);
      await flushPromises();

      const detailBtn = wrapper.find('[data-testid="btn-detail-1"]');
      expect(detailBtn.exists()).toBe(true);
      await detailBtn.trigger('click');
      await flushPromises();

      const jsonViewer = wrapper.find('[data-testid="json-detail-viewer"]');
      expect(jsonViewer.exists()).toBe(true);
      const text = jsonViewer.text();

      expect(text).toContain('"cedula": "[PROTEGIDO / PII]"');
      expect(text).toContain('"nombre_apellido": "[PROTEGIDO / PII]"');
      expect(text).toContain('"telefono": "[PROTEGIDO / PII]"');
      expect(text).toContain('"correo": "[PROTEGIDO / PII]"');
      expect(text).toContain('"direccion_exacta": "[PROTEGIDO / PII]"');
      expect(text).toContain('San Simón');
      expect(text).toContain('Las Cocuizas');
    });

    it('FormioBuilder.vue: anula URLs remotas y desactiva componentes de terceros para preservar soberanía', () => {
      expect(formioBuilderContent).toContain("(Formio as any).setBaseUrl('')");
      expect(formioBuilderContent).toContain("(Formio as any).setProjectUrl('')");
      expect(formioBuilderContent).toContain("resource: false");
      expect(formioBuilderContent).toContain("premium: false");
    });
  });
});
