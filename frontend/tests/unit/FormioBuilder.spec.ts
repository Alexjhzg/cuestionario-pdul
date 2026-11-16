import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import FormioBuilder from '@/components/admin/FormioBuilder.vue';
import FormBuilderView from '@/views/FormBuilderView.vue';
import { Formio } from '@formio/js';
import * as api from '@/services/api';
import { validateFormioSchema } from '@/utils/schemaValidator';
import fs from 'fs';
import path from 'path';

// Mock Formio
vi.mock('@formio/js', () => {
  const mockInstance = {
    schema: { display: 'form', components: [{ type: 'button', key: 'submit', action: 'submit' }] },
    form: { display: 'form', components: [{ type: 'button', key: 'submit', action: 'submit' }] },
    on: vi.fn(),
    off: vi.fn(),
    destroy: vi.fn(),
    setForm: vi.fn()
  };

  return {
    Formio: {
      builder: vi.fn().mockResolvedValue(mockInstance),
      setBaseUrl: vi.fn(),
      setProjectUrl: vi.fn(),
      cdn: {
        setBaseUrl: vi.fn()
      }
    }
  };
});

vi.mock('@/services/api', () => ({
  fetchAdminEncuestas: vi.fn().mockResolvedValue([
    {
      id: '00000000-0000-0000-0000-000000000001',
      titulo: 'Cuestionario Origen-Destino (PDUL Maturín)',
      slug: 'cuestionario-od-maturin',
      tipo_instrumento: 'encuesta_od_pdul',
      activa: true,
      creado_en: '2026-11-09T10:00:00Z',
      total_respuestas: 10
    }
  ]),
  fetchAdminEncuesta: vi.fn().mockResolvedValue({
    id: '00000000-0000-0000-0000-000000000001',
    titulo: 'Cuestionario Origen-Destino (PDUL Maturín)',
    slug: 'cuestionario-od-maturin',
    tipo_instrumento: 'encuesta_od_pdul',
    activa: true,
    esquema_formio: {
      display: 'wizard',
      title: 'PDUL Cloned',
      components: [
        { type: 'textfield', key: 'parroquia' },
        { type: 'button', key: 'submit', action: 'submit' }
      ]
    }
  }),
  createAdminEncuesta: vi.fn().mockImplementation(async (payload) => ({
    id: '00000000-0000-0000-0000-000000000099',
    ...payload,
    creado_en: new Date().toISOString()
  })),
  descargarBlob: vi.fn()
}));

describe('FormioBuilder.vue & FormBuilderView.vue (Milestone 4)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('FormioBuilder.vue', () => {
    it('1. Inicialización soberana: neutraliza URLs remotas y pasa opciones de aislamiento', async () => {
      const initialSchema = {
        display: 'form',
        components: [{ type: 'textfield', key: 'parroquia' }]
      };

      const wrapper = mount(FormioBuilder, {
        props: {
          modelValue: initialSchema
        }
      });
      await flushPromises();

      // Soberanía total verificada
      expect(Formio.setBaseUrl).toHaveBeenCalledWith('');
      expect(Formio.setProjectUrl).toHaveBeenCalledWith('');
      expect(Formio.cdn.setBaseUrl).toHaveBeenCalledWith('');

      // Invocación a Formio.builder
      expect(Formio.builder).toHaveBeenCalled();
      const callArgs = (Formio.builder as any).mock.calls[0];
      expect(callArgs[2].builder.resource).toBe(false);
      expect(callArgs[2].builder.premium).toBe(false);
      expect(callArgs[2].language).toBe('es');
      expect(wrapper.emitted('ready')).toBeTruthy();
    });

    it('2. Limpieza rigurosa en onBeforeUnmount: destruye instancia y elimina modales en document.body', async () => {
      // Simular modal huérfano en document.body
      const orphanModal = document.createElement('div');
      orphanModal.className = 'formio-dialog';
      document.body.appendChild(orphanModal);
      document.body.classList.add('modal-open');

      const wrapper = mount(FormioBuilder);
      await flushPromises();

      const instance = (wrapper.vm as any).builderInstance;
      wrapper.unmount();

      expect(instance.destroy).toHaveBeenCalledWith(true);
      expect(document.querySelectorAll('.formio-dialog').length).toBe(0);
      expect(document.body.classList.contains('modal-open')).toBe(false);
    });

    it('3. Métodos expuestos getSchema y setSchema', async () => {
      const wrapper = mount(FormioBuilder);
      await flushPromises();

      const schema = (wrapper.vm as any).getSchema();
      expect(schema).toBeDefined();

      const newSchema = { display: 'form', components: [] };
      (wrapper.vm as any).setSchema(newSchema);
      const instance = (wrapper.vm as any).builderInstance;
      expect(instance.setForm).toHaveBeenCalled();
    });
  });

  describe('FormBuilderView.vue', () => {
    it('4. Precarga de Esquema Canónico PDUL y Esquema en Blanco', async () => {
      const wrapper = mount(FormBuilderView);
      await flushPromises();

      // Cargar Canónico PDUL
      const btnCanonical = wrapper.find('[data-testid="btn-load-canonical"]');
      await btnCanonical.trigger('click');
      expect((wrapper.vm as any).currentSchema.components.length).toBeGreaterThan(0);
      expect((wrapper.vm as any).titulo).toContain('PDUL');

      // Cargar Esquema en Blanco
      const btnBlank = wrapper.find('[data-testid="btn-load-blank"]');
      await btnBlank.trigger('click');
      expect((wrapper.vm as any).currentSchema.components.length).toBe(2);
    });

    it('5. Cargar esquema desde encuesta existente', async () => {
      const wrapper = mount(FormBuilderView);
      await flushPromises();

      const selectExisting = wrapper.find('[data-testid="select-existing-survey"]');
      await selectExisting.setValue('00000000-0000-0000-0000-000000000001');
      await flushPromises();

      expect(api.fetchAdminEncuesta).toHaveBeenCalledWith('00000000-0000-0000-0000-000000000001');
      expect((wrapper.vm as any).titulo).toContain('Cuestionario Origen-Destino');
    });

    it('6. Guardar encuesta en base de datos vía createAdminEncuesta', async () => {
      const wrapper = mount(FormBuilderView);
      await flushPromises();

      const titleInput = wrapper.find('[data-testid="input-survey-title"]');
      await titleInput.setValue('Consulta Movilidad San Simón 2026');

      const slugInput = wrapper.find('[data-testid="input-survey-slug"]');
      await slugInput.setValue('consulta-movilidad-san-simon');

      const saveBtn = wrapper.find('[data-testid="btn-save-survey"]');
      await saveBtn.trigger('click');
      await flushPromises();

      expect(api.createAdminEncuesta).toHaveBeenCalled();
      expect(wrapper.emitted('survey-created')).toBeTruthy();
      expect(wrapper.text()).toContain('exitosamente');
    });

    it('7. Validador de Esquemas Form.io detecta botón submit y formato snake_case', () => {
      const validSchema = {
        display: 'form',
        components: [
          { type: 'textfield', key: 'nombre_ciudadano' },
          { type: 'button', key: 'submit', action: 'submit' }
        ]
      };
      const resultValid = validateFormioSchema(validSchema, { requireSubmit: true });
      expect(resultValid.valid).toBe(true);

      const invalidSchema = {
        display: 'form',
        components: [
          { type: 'textfield', key: 'nombreInvalidoCamelCase' }
        ]
      };
      const resultInvalid = validateFormioSchema(invalidSchema, { requireSubmit: true });
      expect(resultInvalid.valid).toBe(false);
      expect(resultInvalid.errors.some((e) => e.includes('submit'))).toBe(true);
      expect(resultInvalid.errors.some((e) => e.includes('snake_case'))).toBe(true);
    });

    it('8. Auditoría de Ergonomía Táctil: botones y controles declaran min-block-size >= 48px', () => {
      const viewContent = fs.readFileSync(
        path.resolve(__dirname, '../../src/views/FormBuilderView.vue'),
        'utf-8'
      );

      expect(viewContent).toMatch(/\.custom-switch-label\s*\{[^}]*min-block-size:\s*var\(--min-touch-target\);/);
      expect(viewContent).toMatch(/\.preset-btn\s*\{[^}]*min-block-size:\s*var\(--min-touch-target\);/);
      expect(viewContent).toMatch(/\.existing-select\s*\{[^}]*min-block-size:\s*var\(--min-touch-target\);/);
      expect(viewContent).toMatch(/\.modal-close-btn\s*\{[^}]*min-block-size:\s*var\(--min-touch-target\);/);
    });
  });
});
