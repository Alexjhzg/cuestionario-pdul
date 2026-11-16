import { describe, it, expect, beforeEach } from 'vitest';
import { nextTick } from 'vue';
import { useSurveyDraft } from '@/composables/useSurveyDraft';

describe('Composable useSurveyDraft (Autoguardado Local y Cola Offline)', () => {
  const slug = 'cuestionario-od-maturin';
  const storageKey = `pdul_draft_${slug}`;

  beforeEach(() => {
    localStorage.clear();
  });

  it('guarda automáticamente en localStorage al modificar reactivamente los datos del formulario', async () => {
    const { formData, currentStep, saveToLocalStorage } = useSurveyDraft(slug);

    formData.value.cedula = '12345678';
    formData.value.parroquia = 'san_simon';
    currentStep.value = 1;

    // Disparar guardado o esperar el watcher reactivo
    await nextTick();
    saveToLocalStorage();

    const storedRaw = localStorage.getItem(storageKey);
    expect(storedRaw).not.toBeNull();

    const parsed = JSON.parse(storedRaw!);
    expect(parsed.data.cedula).toBe('12345678');
    expect(parsed.data.parroquia).toBe('san_simon');
    expect(parsed.step).toBe(1);
    expect(parsed.savedAt).toBeDefined();
  });

  it('detecta y restaura correctamente un borrador guardado previamente junto con el paso', () => {
    // Simular un borrador existente en localStorage
    const savedPayload = {
      data: {
        cedula: '19876543',
        parroquia: 'boqueron',
        sector_barrio: 'Tipuro'
      },
      step: 3,
      savedAt: '10:30:00'
    };
    localStorage.setItem(storageKey, JSON.stringify(savedPayload));

    const { formData, currentStep, hasRestorableDraft, restoreDraft } = useSurveyDraft(slug);

    expect(hasRestorableDraft.value).toBe(true);

    restoreDraft();

    expect(hasRestorableDraft.value).toBe(false);
    expect(formData.value.cedula).toBe('19876543');
    expect(formData.value.parroquia).toBe('boqueron');
    expect(formData.value.sector_barrio).toBe('Tipuro');
    expect(currentStep.value).toBe(3);
  });

  it('limpia el borrador de localStorage al llamar a clearDraft', () => {
    localStorage.setItem(storageKey, JSON.stringify({ data: { test: true }, step: 2 }));

    const { hasRestorableDraft, clearDraft } = useSurveyDraft(slug);
    expect(hasRestorableDraft.value).toBe(true);

    clearDraft();

    expect(localStorage.getItem(storageKey)).toBeNull();
    expect(hasRestorableDraft.value).toBe(false);
  });

  it('encola envíos offline con client_submission_id en formato UUID v4 y limpia el borrador', () => {
    localStorage.setItem(storageKey, JSON.stringify({ data: { cedula: '11223344' }, step: 1 }));

    const { enqueueOfflineSubmission, getOfflineQueue } = useSurveyDraft(slug);

    const encuestaId = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890';
    const payload = {
      cedula: '11223344',
      parroquia: 'las_cocuizas',
      residentes: [{ persona_numero: 1, nombres: 'Juan' }]
    };

    const submissionId = enqueueOfflineSubmission(encuestaId, payload);

    // Valida que el client_submission_id sea un UUID válido (36 caracteres con guiones)
    expect(submissionId).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
    );

    // Valida que la cola en localStorage contenga el elemento
    const queue = getOfflineQueue();
    expect(queue).toHaveLength(1);
    expect(queue[0].clientSubmissionId).toBe(submissionId);
    expect(queue[0].encuestaId).toBe(encuestaId);
    expect(queue[0].data.cedula).toBe('11223344');
    expect(queue[0].data.client_submission_id).toBe(submissionId);
    expect(queue[0].createdAt).toBeDefined();

    // El borrador activo debió limpiarse
    expect(localStorage.getItem(storageKey)).toBeNull();
  });

  it('maneja defensivamente valores no válidos o primitivos en pdul_offline_queue sin lanzar errores', () => {
    const invalidValues = ['null', '12345', '{}', 'true', '"texto_plano"'];
    const encuestaId = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890';
    const payload = { cedula: '20123456', parroquia: 'san_simon' };

    for (const invalidValue of invalidValues) {
      localStorage.setItem('pdul_offline_queue', invalidValue);

      const { getOfflineQueue, enqueueOfflineSubmission } = useSurveyDraft(slug);

      // Debe retornar arreglo vacío en vez de null, number u object
      expect(getOfflineQueue()).toEqual([]);

      // enqueueOfflineSubmission debe funcionar sin lanzar TypeError
      let submissionId = '';
      expect(() => {
        submissionId = enqueueOfflineSubmission(encuestaId, payload);
      }).not.toThrow();

      expect(submissionId).toMatch(
        /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
      );

      const updatedQueue = getOfflineQueue();
      expect(Array.isArray(updatedQueue)).toBe(true);
      expect(updatedQueue).toHaveLength(1);
      expect(updatedQueue[0].clientSubmissionId).toBe(submissionId);
    }
  });
});
