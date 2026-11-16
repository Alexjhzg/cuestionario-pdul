import { computed, ref } from 'vue';
import { SURVEY_STEPS } from '@/types/survey';

const activeSurveyId = ref<string>('00000000-0000-0000-0000-000000000001');
const activeSurveyTitle = ref<string>('Cuestionario Origen-Destino (PDUL Maturín)');
const activeSlug = ref<string>('cuestionario-od-maturin');
const currentStep = ref<number>(0);
const formData = ref<Record<string, any>>({
  cedula: '',
  parroquia: '',
  residentes: [],
  viajes: [],
  acepta_declaracion: true
});

export function useSurveyStore() {
  const totalSteps = computed(() => SURVEY_STEPS.length);
  const currentStepInfo = computed(() => SURVEY_STEPS[currentStep.value] || SURVEY_STEPS[0]);

  function setSurveyMeta(meta: { id?: string; titulo?: string; slug?: string }) {
    if (meta.id) activeSurveyId.value = meta.id;
    if (meta.titulo) activeSurveyTitle.value = meta.titulo;
    if (meta.slug) activeSlug.value = meta.slug;
  }

  function setStep(step: number) {
    if (step >= 0 && step < SURVEY_STEPS.length) {
      currentStep.value = step;
    }
  }

  function updateField(field: string, value: any) {
    formData.value = { ...formData.value, [field]: value };
  }

  function resetSurvey() {
    currentStep.value = 0;
    formData.value = {
      cedula: '',
      parroquia: '',
      residentes: [],
      viajes: [],
      acepta_declaracion: true
    };
  }

  return {
    activeSurveyId,
    activeSurveyTitle,
    activeSlug,
    currentStep,
    formData,
    totalSteps,
    currentStepInfo,
    setSurveyMeta,
    setStep,
    updateField,
    resetSurvey
  };
}

