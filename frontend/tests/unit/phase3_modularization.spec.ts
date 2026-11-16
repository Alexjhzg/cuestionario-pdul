import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import fs from 'node:fs';
import path from 'node:path';

vi.mock('@/services/analyticsApi', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/services/analyticsApi')>();
  return {
    ...actual,
    fetchAllAnalytics: vi.fn()
  };
});

import * as analyticsApi from '@/services/analyticsApi';
import {
  BaseBadge,
  BaseButton,
  BaseCard,
  BaseDataTable,
  BaseInput,
  BaseModal,
  BaseSelect,
  BaseSwitch
} from '@/components/ui';
import { usePiiMasking } from '@/composables/usePiiMasking';
import { PII_FIELDS } from '@shared/types/pii';
import { calculateStepProgress, getStepErrors } from '@/utils/surveyStepValidation';
import {
  useAdminStore,
  useAnalyticsStore,
  useDraftStore,
  useSurveyStore
} from '@/stores';

describe('Fase 3 - Modularización Frontend, Primitivas UI y Stores', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useSurveyStore().resetSurvey();
    useDraftStore().reset();
    useAdminStore().reset();
    useAnalyticsStore().reset();
  });

  describe('1. Deduplicación de activos @shared y eliminación de copias locales', () => {
    it('elimina copias redundantes en frontend/src y mantiene fuentes canónicas en shared/', () => {
      const repoRoot = path.resolve(__dirname, '../../../');
      const frontendRoot = path.resolve(__dirname, '../..');

      expect(
        fs.existsSync(path.join(frontendRoot, 'src/assets/schemas/pdul_origen_destino.json'))
      ).toBe(false);
      expect(
        fs.existsSync(path.join(frontendRoot, 'src/assets/geojson/maturin_parroquias.geojson'))
      ).toBe(false);
      expect(
        fs.existsSync(path.join(frontendRoot, 'src/components/builder/FormioBuilder.vue'))
      ).toBe(false);

      expect(fs.existsSync(path.join(repoRoot, 'shared/catalogs/parroquias.json'))).toBe(true);
      expect(fs.existsSync(path.join(repoRoot, 'shared/schemas/pdul_origen_destino.json'))).toBe(true);
      expect(fs.existsSync(path.join(repoRoot, 'shared/geojson/maturin_parroquias.geojson'))).toBe(true);
      expect(fs.existsSync(path.join(repoRoot, 'shared/types/pii.ts'))).toBe(true);
    });
  });

  describe('2. Primitivas accesibles en components/ui/', () => {
    it('BaseButton expone estado loading accesible y variante visual', () => {
      const wrapper = mount(BaseButton, {
        props: { variant: 'secondary', loading: true },
        slots: { default: 'Guardar' }
      });
      const btn = wrapper.find('button');
      expect(btn.classes()).toContain('base-btn--secondary');
      expect(btn.attributes('disabled')).toBeDefined();
      expect(btn.attributes('aria-busy')).toBe('true');
      expect(btn.text()).toContain('Guardar');
    });

    it('BaseInput mantiene aria-invalid="false" antes de interactuar y anuncia error tras blur inválido', async () => {
      const wrapper = mount(BaseInput, {
        props: {
          id: 'campo-cedula',
          label: 'Cédula',
          hint: 'Solo dígitos',
          required: true,
          modelValue: ''
        }
      });

      const input = wrapper.find('input');
      expect(input.attributes('aria-invalid')).toBe('false');
      expect(input.attributes('aria-describedby')).toBe('campo-cedula-hint');

      await input.trigger('blur');
      expect(input.attributes('aria-invalid')).toBe('true');
      expect(input.attributes('aria-describedby')).toContain('campo-cedula-error');

      await input.setValue('12345678');
      expect(wrapper.emitted('update:modelValue')?.[0]).toEqual(['12345678']);
    });

    it('BaseInput convierte valores numéricos cuando type="number"', async () => {
      const wrapper = mount(BaseInput, {
        props: {
          id: 'cuartos',
          label: 'Cuartos',
          type: 'number',
          modelValue: ''
        }
      });
      const input = wrapper.find('input');
      await input.setValue('4');
      expect(wrapper.emitted('update:modelValue')?.[0]).toEqual([4]);
    });

    it('BaseSelect emite cambios y valida en blur', async () => {
      const wrapper = mount(BaseSelect, {
        props: {
          id: 'parroquia-select',
          label: 'Parroquia',
          required: true,
          placeholderOption: 'Seleccione...',
          options: [
            { value: 'san_simon', label: 'San Simón' },
            { value: 'boqueron', label: 'Boquerón' }
          ],
          modelValue: ''
        }
      });

      const select = wrapper.find('select');
      expect(select.attributes('aria-invalid')).toBe('false');
      await select.trigger('blur');
      expect(select.attributes('aria-invalid')).toBe('true');

      await select.setValue('boqueron');
      expect(wrapper.emitted('update:modelValue')?.[0]).toEqual(['boqueron']);
    });

    it('BaseSwitch renderiza role="switch" con aria-checked y emite actualización al hacer clic', async () => {
      const wrapper = mount(BaseSwitch, {
        props: {
          modelValue: false,
          label: 'Proteger PII'
        }
      });

      const switchBtn = wrapper.find('button[role="switch"]');
      expect(switchBtn.exists()).toBe(true);
      expect(switchBtn.attributes('aria-checked')).toBe('false');

      await switchBtn.trigger('click');
      expect(wrapper.emitted('update:modelValue')?.[0]).toEqual([true]);
      expect(wrapper.emitted('toggle')).toHaveLength(1);
    });

    it('BaseModal renderiza diálogo modal WCAG AA y cierra con tecla Escape y botón de cierre', async () => {
      const wrapper = mount(BaseModal, {
        props: {
          open: true,
          titleId: 'modal-titulo',
          title: 'Detalle de respuesta'
        },
        slots: {
          default: '<p>Contenido interno</p>',
          footer: '<button type="button">Aceptar</button>'
        }
      });

      const dialog = wrapper.find('[role="dialog"]');
      expect(dialog.exists()).toBe(true);
      expect(dialog.attributes('aria-modal')).toBe('true');
      expect(dialog.attributes('aria-labelledby')).toBe('modal-titulo');
      expect(wrapper.find('#modal-titulo').text()).toBe('Detalle de respuesta');

      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
      expect(wrapper.emitted('close')).toHaveLength(1);

      await wrapper.find('.base-modal-close').trigger('click');
      expect(wrapper.emitted('close')).toHaveLength(2);
    });

    it('BaseDataTable cumple accesibilidad de tabla desplazable (region, caption, scope="col")', () => {
      const wrapper = mount(BaseDataTable, {
        props: {
          caption: 'Resumen por parroquia',
          captionId: 'cap-parroquias',
          columns: [
            { key: 'parroquia', label: 'Parroquia' },
            { key: 'total', label: 'Total' }
          ],
          rows: []
        }
      });

      const region = wrapper.find('[role="region"]');
      expect(region.attributes('tabindex')).toBe('0');
      expect(region.attributes('aria-labelledby')).toBe('cap-parroquias');
      expect(wrapper.find('caption#cap-parroquias').text()).toBe('Resumen por parroquia');
      expect(wrapper.findAll('th[scope="col"]')).toHaveLength(2);
      expect(wrapper.text()).toContain('No hay registros disponibles.');
    });

    it('BaseCard y BaseBadge renderizan semántica esperada', () => {
      const card = mount(BaseCard, {
        props: { title: 'Resumen' },
        slots: { default: '<span>Cuerpo</span>' }
      });
      expect(card.find('section.base-card').exists()).toBe(true);
      expect(card.find('h3').text()).toBe('Resumen');

      const badge = mount(BaseBadge, {
        props: { variant: 'success' },
        slots: { default: 'Activa' }
      });
      expect(badge.find('.base-badge--success').text()).toBe('Activa');
    });
  });

  describe('3. Composables y utilidades modularizadas', () => {
    it('usePiiMasking enmascara recursivamente campos definidos en @shared/types/pii', () => {
      const { maskPiiData, MASKED_PLACEHOLDER, PII_FIELD_SET } = usePiiMasking();
      expect(PII_FIELD_SET.has('cedula')).toBe(true);
      expect(PII_FIELDS.length).toBeGreaterThanOrEqual(8);

      const payload = {
        cedula: 'V-19123456',
        parroquia: 'san_simon',
        residentes: [
          {
            nombre_apellido: 'Ana Pérez',
            telefono: '0414-0000000',
            edad: 32
          }
        ]
      };

      const masked = maskPiiData(payload, true) as typeof payload;
      expect(masked.cedula).toBe(MASKED_PLACEHOLDER);
      expect(masked.parroquia).toBe('san_simon');
      expect(masked.residentes[0].nombre_apellido).toBe(MASKED_PLACEHOLDER);
      expect(masked.residentes[0].telefono).toBe(MASKED_PLACEHOLDER);
      expect(masked.residentes[0].edad).toBe(32);

      const unmasked = maskPiiData(payload, false) as typeof payload;
      expect(unmasked.cedula).toBe('V-19123456');
    });

    it('surveyStepValidation calcula progreso y errores por sección sin acoplamiento visual', () => {
      expect(calculateStepProgress(0, { parroquia: 'san_simon', comunidad_sector: 'Centro' })).toBe(1);

      const errsStep0 = getStepErrors(0, { parroquia: 'invalida' });
      expect(errsStep0).toContain('1.- Seleccione su parroquia.');

      const errsStep3 = getStepErrors(3, {
        numero_personas_hogar: 2,
        residentes: [{ nombre_apellido: 'Juan', parentesco: 'jefe', sexo: 'masculino', edad: 30 }]
      });
      expect(errsStep3.some((msg) => msg.includes('1 de 2 integrantes'))).toBe(true);
    });
  });

  describe('4. Stores reactivos desacoplados', () => {
    it('useSurveyStore y useDraftStore gestionan estado compartido y cola offline', () => {
      const survey = useSurveyStore();
      survey.setSurveyMeta({ id: 'survey-123', titulo: 'Encuesta PDUL', slug: 'pdul' });
      survey.updateField('parroquia', 'las_cocuizas');
      survey.setStep(2);

      expect(survey.activeSurveyId.value).toBe('survey-123');
      expect(survey.formData.value.parroquia).toBe('las_cocuizas');
      expect(survey.currentStep.value).toBe(2);

      const draft = useDraftStore();
      draft.enqueueItem({
        client_submission_id: 'sub-1',
        encuesta_id: 'survey-123',
        data: { parroquia: 'las_cocuizas' },
        queued_at: '2026-11-16T00:00:00Z'
      });
      expect(draft.pendingCount.value).toBe(1);
      draft.removeQueueItem('sub-1');
      expect(draft.pendingCount.value).toBe(0);
    });

    it('useAnalyticsStore implementa caché por encuesta y evita condiciones de carrera al cambiar de ID', async () => {
      const store = useAnalyticsStore();
      const datasetA = {
        kpis: {
          total_encuestas: 12,
          total_residentes: 30,
          total_viajes: 45,
          promedio_edad: 31,
          parroquia_lider: 'san_simon',
          fecha_ultima_respuesta: null
        },
        parroquias: [],
        repartoModal: [],
        matrizOd: []
      };
      const datasetB = {
        kpis: {
          total_encuestas: 99,
          total_residentes: 210,
          total_viajes: 310,
          promedio_edad: 35,
          parroquia_lider: 'las_cocuizas',
          fecha_ultima_respuesta: null
        },
        parroquias: [],
        repartoModal: [],
        matrizOd: []
      };

      const fetchMock = vi.mocked(analyticsApi.fetchAllAnalytics);
      fetchMock.mockResolvedValueOnce(datasetA);

      await store.loadAnalytics('enc-a');
      expect(store.kpis.value?.total_encuestas).toBe(12);

      // Segunda carga sin forceRefresh reutiliza caché
      await store.loadAnalytics('enc-a');
      expect(fetchMock).toHaveBeenCalledTimes(1);

      // Cambio rápido de encuesta: la respuesta tardía de 'enc-c' no debe sobrescribir 'enc-b'
      let resolveSlow!: (value: analyticsApi.AnalyticsDataset) => void;
      fetchMock
        .mockImplementationOnce(() => new Promise((r) => { resolveSlow = r; }))
        .mockResolvedValueOnce(datasetB);

      const slowPromise = store.loadAnalytics('enc-c');
      await store.loadAnalytics('enc-b');
      resolveSlow(datasetA);
      await slowPromise;

      expect(store.currentSurveyId.value).toBe('enc-b');
      expect(store.kpis.value?.total_encuestas).toBe(99);
    });
  });
});
