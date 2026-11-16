import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import FormioBuilder from '@/components/admin/FormioBuilder.vue';
import FormBuilderView from '@/views/FormBuilderView.vue';
import { Formio } from '@formio/js';
import pdulCanonicalSchema from '@shared/schemas/pdul_origen_destino.json';
import fs from 'fs';
import path from 'path';

const { canonicalSample } = vi.hoisted(() => ({
  canonicalSample: {
    display: 'form',
    title: 'Encuesta Origen-Destino PDUL Maturín',
    name: 'pdul_origen_destino',
    path: 'pdul-origen-destino',
    components: [
      {
        type: 'panel',
        title: 'Sección I',
        key: 'seccion_i',
        components: [
          { type: 'textfield', key: 'parroquia', required: true },
          { type: 'textfield', key: 'zona_residencia_od', required: true }
        ]
      },
      {
        type: 'datagrid',
        key: 'residentes',
        components: [{ type: 'textfield', key: 'nombre' }]
      },
      {
        type: 'datagrid',
        key: 'viajes',
        components: [{ type: 'textfield', key: 'origen' }]
      },
      {
        type: 'button',
        key: 'submit',
        action: 'submit',
        theme: 'primary'
      }
    ]
  }
}));

// Mock API
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
  fetchAdminEncuesta: vi.fn().mockImplementation(async (id: string) => ({
    id,
    titulo: 'Cuestionario Origen-Destino (PDUL Maturín)',
    slug: 'cuestionario-od-maturin',
    tipo_instrumento: 'encuesta_od_pdul',
    activa: true,
    esquema_formio: canonicalSample
  })),
  createAdminEncuesta: vi.fn().mockImplementation(async (payload) => ({
    id: '00000000-0000-0000-0000-000000000099',
    ...payload,
    creado_en: new Date().toISOString()
  })),
  updateAdminEncuesta: vi.fn().mockImplementation(async (id, payload) => ({
    id,
    ...payload,
    actualizado_en: new Date().toISOString()
  })),
  triggerBlobDownload: vi.fn(),
  descargarBlob: vi.fn()
}));

// Mock Formio
vi.mock('@formio/js', () => {
  const createMockInstance = () => ({
    schema: canonicalSample,
    form: canonicalSample,
    on: vi.fn(),
    off: vi.fn(),
    destroy: vi.fn().mockResolvedValue(true),
    setForm: vi.fn()
  });

  return {
    Formio: {
      builder: vi.fn().mockImplementation(() => Promise.resolve(createMockInstance())),
      setBaseUrl: vi.fn(),
      setProjectUrl: vi.fn(),
      cdn: {
        setBaseUrl: vi.fn()
      }
    }
  };
});

describe('Challenger M4 Empirical Verification Suite', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    document.body.innerHTML = '';
    document.body.className = '';
  });

  afterEach(() => {
    document.body.innerHTML = '';
    document.body.className = '';
  });

  describe('1. Ciclo de Vida, Aislamiento y Limpieza de Fugas de Memoria en FormioBuilder.vue', () => {
    it('1.1 Verifica que onBeforeUnmount invoca destroy(true) en la instancia activa', async () => {
      const wrapper = mount(FormioBuilder, {
        props: {
          modelValue: { display: 'form', components: [] }
        }
      });
      await flushPromises();

      const instance = (wrapper.vm as any).builderInstance;
      expect(instance).toBeDefined();
      expect(instance.destroy).not.toHaveBeenCalled();

      wrapper.unmount();

      expect(instance.destroy).toHaveBeenCalledTimes(1);
      expect(instance.destroy).toHaveBeenCalledWith(true);
      expect((wrapper.vm as any).builderInstance).toBeNull();
    });

    it('1.2 Remueve múltiples modales huérfanos .formio-dialog y clases de bloqueo en document.body', async () => {
      // Simular múltiples modales huérfanos colgados por Formio en document.body
      for (let i = 1; i <= 3; i++) {
        const dialog = document.createElement('div');
        dialog.className = `formio-dialog formio-dialog-theme-default dialog-idx-${i}`;
        dialog.innerHTML = `<div class="formio-dialog-content"><p>Modal ${i}</p></div>`;
        document.body.appendChild(dialog);
      }
      document.body.classList.add('modal-open', 'formio-dialog-open');

      expect(document.querySelectorAll('.formio-dialog').length).toBe(3);
      expect(document.body.classList.contains('modal-open')).toBe(true);
      expect(document.body.classList.contains('formio-dialog-open')).toBe(true);

      const wrapper = mount(FormioBuilder);
      await flushPromises();

      wrapper.unmount();

      // Comprobación empírica: 0 modales huérfanos y clases removidas
      expect(document.querySelectorAll('.formio-dialog').length).toBe(0);
      expect(document.body.classList.contains('modal-open')).toBe(false);
      expect(document.body.classList.contains('formio-dialog-open')).toBe(false);
    });

    it('1.3 Resiliencia ante fallos: si destroy(true) lanza una excepción, el unmount no colapsa y limpia el DOM', async () => {
      const wrapper = mount(FormioBuilder);
      await flushPromises();

      const instance = (wrapper.vm as any).builderInstance;
      instance.destroy.mockImplementation(() => {
        throw new Error('Fallo intencional durante destroy() en Form.io');
      });

      // Crear diálogo huérfano
      const dialog = document.createElement('div');
      dialog.className = 'formio-dialog';
      document.body.appendChild(dialog);
      document.body.classList.add('formio-dialog-open');

      // El unmount debe ser a prueba de bombas y no lanzar error no capturado
      expect(() => {
        wrapper.unmount();
      }).not.toThrow();

      // Debe haber limpiado el diálogo huérfano a pesar del fallo en destroy()
      expect(document.querySelectorAll('.formio-dialog').length).toBe(0);
      expect(document.body.classList.contains('formio-dialog-open')).toBe(false);
    });

    it('1.4 Prueba de estrés: 20 ciclos continuos de montaje/desmontaje rápido sin fugas en DOM', async () => {
      for (let cycle = 0; cycle < 20; cycle++) {
        const dialog = document.createElement('div');
        dialog.className = 'formio-dialog';
        document.body.appendChild(dialog);
        document.body.classList.add('modal-open');

        const wrapper = mount(FormioBuilder, {
          props: { modelValue: { display: 'form', components: [] } }
        });
        await flushPromises();
        wrapper.unmount();

        expect(document.querySelectorAll('.formio-dialog').length).toBe(0);
        expect(document.body.classList.contains('modal-open')).toBe(false);
      }
    });

    it('1.5 Desmontaje prematuro durante inicialización asíncrona', async () => {
      let resolvePromise: any;
      (Formio.builder as any).mockImplementationOnce(() => {
        return new Promise((resolve) => {
          resolvePromise = resolve;
        });
      });

      const wrapper = mount(FormioBuilder);
      wrapper.unmount();

      if (resolvePromise) {
        resolvePromise({
          destroy: vi.fn(),
          off: vi.fn()
        });
      }
      await flushPromises();

      expect(document.querySelectorAll('.formio-dialog').length).toBe(0);
    });

    it('1.6 AUDITORÍA ADVERSARIAL DE FUGA: Desmontaje mientras Formio.builder está en curso debe destruir la instancia al resolver', async () => {
      let resolveBuilderPromise: any;
      const mockDestroy = vi.fn();

      (Formio.builder as any).mockImplementationOnce(() => {
        return new Promise((resolve) => {
          resolveBuilderPromise = resolve;
        });
      });

      const wrapper = mount(FormioBuilder);
      expect((wrapper.vm as any).builderInstance).toBeNull();

      // Desmontar inmediatamente
      wrapper.unmount();

      // Formio.builder resuelve después del desmontaje
      resolveBuilderPromise({
        schema: { display: 'form', components: [] },
        destroy: mockDestroy,
        on: vi.fn(),
        off: vi.fn()
      });
      await flushPromises();

      expect(mockDestroy, 'Fuga de memoria: la instancia de Formio creada tras el desmontaje nunca fue destruida con destroy(true)').toHaveBeenCalledWith(true);
    });
  });

  describe('2. Precarga y Exportación del Esquema Canónico PDUL en FormBuilderView.vue', () => {
    it('2.1 Precarga correcta del esquema canónico PDUL y metadatos oficiales', async () => {
      const wrapper = mount(FormBuilderView);
      await flushPromises();

      const btnCanonical = wrapper.find('[data-testid="btn-load-canonical"]');
      expect(btnCanonical.exists()).toBe(true);
      await btnCanonical.trigger('click');
      await flushPromises();

      const schema = (wrapper.vm as any).currentSchema;
      expect(schema).toBeDefined();
      expect(schema.display).toBe('form');
      expect(schema.components.length).toBeGreaterThan(0);

      // Metadatos esperados
      expect((wrapper.vm as any).titulo).toBe('Encuesta Origen-Destino PDUL Maturín');
      expect((wrapper.vm as any).slug).toBe('pdul_origen_destino');
      expect((wrapper.vm as any).tipoInstrumento).toBe('encuesta_od_pdul');
      expect((wrapper.vm as any).displayMode).toBe('form');
    });

    it('2.2 Valida que el esquema exportado cumple las reglas del validador oficial Form.io', async () => {
      const wrapper = mount(FormBuilderView);
      await flushPromises();

      // Cargar canónico
      await wrapper.find('[data-testid="btn-load-canonical"]').trigger('click');
      await flushPromises();

      const exported = (wrapper.vm as any).currentSchema;

      // 1. Debe tener display y components
      expect(exported.display).toMatch(/^(form|wizard)$/);
      expect(Array.isArray(exported.components)).toBe(true);

      // 2. Verificar que contiene botón con action submit
      const hasSubmit = JSON.stringify(exported).includes('"action":"submit"');
      expect(hasSubmit).toBe(true);

      // 3. Verificar que todas las claves de componentes son snake_case o panel
      function checkKeys(components: any[]): string[] {
        const invalid: string[] = [];
        for (const comp of components) {
          if (comp.key && !/^[a-z0-9_]+$/.test(comp.key)) {
            invalid.push(comp.key);
          }
          if (comp.components) {
            invalid.push(...checkKeys(comp.components));
          }
          if (comp.columns) {
            for (const col of comp.columns) {
              if (col.components) invalid.push(...checkKeys(col.components));
            }
          }
        }
        return invalid;
      }

      const invalidKeys = checkKeys(exported.components);
      expect(invalidKeys).toEqual([]);

      // 4. Secciones clave del PDUL presentes en pdulCanonicalSchema
      const canonicalStr = JSON.stringify(pdulCanonicalSchema);
      expect(canonicalStr).toContain('parroquia');
      expect(canonicalStr).toContain('zona_residencia_od');
      expect(canonicalStr).toContain('residentes');
      expect(canonicalStr).toContain('viajes');
    });

    it('2.3 Manejo robusto de archivos JSON corruptos o no válidos vía FileReader', async () => {
      const wrapper = mount(FormBuilderView);
      await flushPromises();

      // Mock FileReader para simular carga síncrona de archivo corrupto
      const originalFileReader = globalThis.FileReader;
      class MockFileReader {
        onload: ((e: any) => void) | null = null;
        readAsText(_file: any) {
          if (this.onload) {
            this.onload({ target: { result: '{ "corrupt_json: invalid' } });
          }
        }
      }
      globalThis.FileReader = MockFileReader as any;

      try {
        const fakeFile = new File(['bad json'], 'corrupt.json', { type: 'application/json' });
        const fakeEvent = {
          target: {
            files: [fakeFile],
            value: ''
          }
        };

        (wrapper.vm as any).onFileSelected(fakeEvent);
        await flushPromises();

        expect(String((wrapper.vm as any).errorMessage)).toContain('Error al leer archivo JSON');
        expect((wrapper.vm as any).successMessage).toBeNull();
      } finally {
        globalThis.FileReader = originalFileReader;
      }
    });
  });

  describe('3. Soberanía Tecnológica y Ausencia de Solicitudes Externas', () => {
    it('3.1 Verifica neutralización de URLs remotas en Formio.setBaseUrl, setProjectUrl y cdn.setBaseUrl', async () => {
      mount(FormioBuilder);
      await flushPromises();

      expect(Formio.setBaseUrl).toHaveBeenCalledWith('');
      expect(Formio.setProjectUrl).toHaveBeenCalledWith('');
      expect(Formio.cdn.setBaseUrl).toHaveBeenCalledWith('');
    });

    it('3.2 Verifica que builder options desactivan resource y premium', async () => {
      mount(FormioBuilder);
      await flushPromises();

      const builderCalls = (Formio.builder as any).mock.calls;
      expect(builderCalls.length).toBeGreaterThan(0);
      const opts = builderCalls[0][2];
      expect(opts.builder).toBeDefined();
      expect(opts.builder.resource).toBe(false);
      expect(opts.builder.premium).toBe(false);
      expect(opts.noSource).toBe(true);
      expect(opts.noAlerts).toBe(true);
    });

    it('3.3 Auditoría de Red: Cero llamadas a APIs externas o CDN durante ciclo de vida del Builder', async () => {
      const fetchSpy = vi.spyOn(globalThis, 'fetch');

      const wrapper = mount(FormBuilderView);
      await flushPromises();

      await wrapper.find('[data-testid="btn-load-canonical"]').trigger('click');
      await flushPromises();

      await wrapper.find('[data-testid="btn-export-json"]').trigger('click');
      await flushPromises();

      wrapper.unmount();

      for (const call of fetchSpy.mock.calls) {
        const url = String(call[0]);
        expect(url).not.toMatch(/api\.form\.io|cdn\.form\.io|google|mapbox/);
      }
      fetchSpy.mockRestore();
    });
  });

  describe('4. Ergonomía Táctil y Accesibilidad (WCAG AA) en FormBuilderView', () => {
    it('4.1 Todos los botones de acción, switches y selects tienen min-block-size >= 48px', () => {
      const viewSource = fs.readFileSync(
        path.resolve(__dirname, '../../src/views/FormBuilderView.vue'),
        'utf-8'
      );
      const mainCss = fs.readFileSync(
        path.resolve(__dirname, '../../src/assets/styles/main.css'),
        'utf-8'
      );

      // Botones globales .survey-btn usados en FormBuilderView
      expect(mainCss).toMatch(/\.survey-btn\s*\{[^}]*min-block-size:\s*var\(--min-touch-target\);/);
      // Botones de preset
      expect(viewSource).toMatch(/\.preset-btn\s*\{[^}]*min-block-size:\s*var\(--min-touch-target\);/);
      // Select de encuestas existentes
      expect(viewSource).toMatch(/\.existing-select\s*\{[^}]*min-block-size:\s*var\(--min-touch-target\);/);
      // Switch de estado activa/inactiva
      expect(viewSource).toMatch(/\.custom-switch-label\s*\{[^}]*min-block-size:\s*var\(--min-touch-target\);/);
      // Botón cerrar modal
      expect(viewSource).toMatch(/\.modal-close-btn\s*\{[^}]*min-block-size:\s*var\(--min-touch-target\);/);
    });
  });
});
