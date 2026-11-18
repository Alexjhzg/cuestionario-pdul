import { describe, it, expect, beforeEach, vi } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';
import { nextTick } from 'vue';
import PrimeVue from 'primevue/config';
import ToastService from 'primevue/toastservice';

vi.mock('@/services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/services/api')>();
  return {
    ...actual,
    fetchEncuesta: vi.fn().mockResolvedValue({
      id: '00000000-0000-0000-0000-000000000001',
      titulo: 'Cuestionario Origen-Destino (PDUL Maturín)',
      slug: 'cuestionario-od-maturin',
      activa: true
    }),
    submitRespuesta: vi.fn().mockResolvedValue({
      id: 101,
      fecha_registro: '2026-11-16T15:00:00Z',
      idempotent_replay: false,
      mensaje: 'OK'
    })
  };
});

import {
  normalizeDraftStep,
  parseStoredDraft,
  useSurveyDraft
} from '@/composables/useSurveyDraft';
import SurveyFillView from '@/views/SurveyFillView.vue';

describe('Fase 4 - Retrocompatibilidad de borradores pdul_draft_* e integración UI', () => {
  const slug = 'cuestionario-od-maturin';
  const storageKey = `pdul_draft_${slug}`;

  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('normaliza pasos legacy numéricos, en string o fuera de rango dentro de [0, 8]', () => {
    expect(normalizeDraftStep(0)).toBe(0);
    expect(normalizeDraftStep('4')).toBe(4);
    expect(normalizeDraftStep(-5)).toBe(0);
    expect(normalizeDraftStep(999)).toBe(8);
    expect(normalizeDraftStep('no-numerico')).toBe(0);
    expect(normalizeDraftStep(undefined)).toBe(0);
  });

  it('restaura borrador v1 plano (sin envoltorio data) y normaliza etiqueta humana de parroquia', () => {
    const legacyFlatDraft = {
      cedula: '18555444',
      parroquia: 'Alto de Los Godos',
      comunidad_sector: 'Los Godos III',
      step: '2',
      savedAt: '09:15:00'
    };
    localStorage.setItem(storageKey, JSON.stringify(legacyFlatDraft));

    const { formData, currentStep, hasRestorableDraft, restoreDraft } = useSurveyDraft(slug, {
      cedula: '',
      parroquia: '',
      residentes: [],
      viajes: [],
      acepta_declaracion: true
    });

    expect(hasRestorableDraft.value).toBe(true);
    restoreDraft();

    expect(currentStep.value).toBe(2);
    expect(formData.value.cedula).toBe('18555444');
    expect(formData.value.parroquia).toBe('alto_de_los_godos');
    expect(formData.value.comunidad_sector).toBe('Los Godos III');
    expect(Array.isArray(formData.value.residentes)).toBe(true);
    expect(Array.isArray(formData.value.viajes)).toBe(true);
    expect(formData.value.acepta_declaracion).toBe(true);
  });

  it('restaura borrador legacy con llave formData y corrige residentes/viajes nulos según initialData', () => {
    localStorage.setItem(
      storageKey,
      JSON.stringify({
        formData: {
          parroquia: 'San Simón',
          residentes: null,
          viajes: undefined
        },
        step: 15,
        savedAt: '11:20:00'
      })
    );

    const { formData, currentStep, restoreDraft } = useSurveyDraft(slug, {
      cedula: '',
      parroquia: '',
      residentes: [],
      viajes: [],
      acepta_declaracion: true
    });

    restoreDraft();
    expect(currentStep.value).toBe(8);
    expect(formData.value.parroquia).toBe('san_simon');
    expect(formData.value.residentes).toEqual([]);
    expect(formData.value.viajes).toEqual([]);
  });

  it('ignora borradores corruptos o con tipo primitivo/array sin activar banner ni lanzar excepciones', () => {
    for (const badValue of ['"[invalid json', '[1,2,3]', '12345', '"texto"', 'null', '{}']) {
      localStorage.setItem(storageKey, badValue);
      expect(parseStoredDraft(localStorage.getItem(storageKey))).toBeNull();

      const draft = useSurveyDraft(slug);
      expect(draft.hasRestorableDraft.value).toBe(false);
    }
  });

  it('deserializa elementos legacy snake_case en pdul_offline_queue de forma transparente', () => {
    localStorage.setItem(
      'pdul_offline_queue',
      JSON.stringify([
        {
          client_submission_id: '11111111-1111-4111-8111-111111111111',
          encuesta_id: '00000000-0000-0000-0000-000000000001',
          data: { parroquia: 'boqueron', viajes: [] },
          created_at: '2026-10-01T12:00:00Z'
        }
      ])
    );

    const { getOfflineQueue } = useSurveyDraft(slug);
    const queue = getOfflineQueue();
    expect(queue).toHaveLength(1);
    expect(queue[0].clientSubmissionId).toBe('11111111-1111-4111-8111-111111111111');
    expect(queue[0].encuestaId).toBe('00000000-0000-0000-0000-000000000001');
    expect(queue[0].createdAt).toBe('2026-10-01T12:00:00Z');
  });

  it('SurveyFillView restaura borrador legacy en UI y navega entre secciones sin errores ni warnings de consola', async () => {
    localStorage.setItem(
      storageKey,
      JSON.stringify({
        data: {
          parroquia: 'Las Cocuizas',
          comunidad_sector: 'Las Cocuizas Sector Norte',
          zona_residencia_od: 'ZONA_02',
          avenida_calle: 'Av. Bolívar',
          casa_apartamento: 'Casa 4',
          tipo_vivienda: 'quinta',
          total_cuartos_vivienda: 4
        },
        step: 1,
        savedAt: '14:45:00'
      })
    );

    const errSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

    const wrapper = mount(SurveyFillView, {
      props: { encuestaSlug: slug },
      global: {
        plugins: [PrimeVue, ToastService]
      }
    });
    await flushPromises();
    await nextTick();

    // Debe mostrarse el banner de recuperación
    expect(wrapper.find('.draft-banner').exists()).toBe(true);

    // Clic en "Continuar borrador"
    const restoreBtn = wrapper.find('.draft-banner .survey-btn-primary');
    await restoreBtn.trigger('click');
    await nextTick();

    expect(wrapper.find('.draft-banner').exists()).toBe(false);
    expect(wrapper.find('.step-title').text()).toContain('Vivienda');
    const cuartosInput = wrapper.find<HTMLInputElement>('#total_cuartos_vivienda');
    expect(cuartosInput.exists()).toBe(true);
    expect(cuartosInput.element.value).toBe('4');

    expect(errSpy).not.toHaveBeenCalled();
    expect(warnSpy).not.toHaveBeenCalled();

    errSpy.mockRestore();
    warnSpy.mockRestore();
  });
});
