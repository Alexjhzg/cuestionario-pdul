import { ref, onMounted, watch } from 'vue';
import type FormioBuilder from '@/components/admin/FormioBuilder.vue';
import pdulCanonicalSchema from '@shared/schemas/pdul_origen_destino.json';
import {
  fetchAdminEncuestas,
  fetchAdminEncuesta,
  createAdminEncuesta,
  updateAdminEncuesta,
  triggerBlobDownload,
  type EncuestaAdminItem
} from '@/services/api';
import { validateFormioSchema, type SchemaValidationResult } from '@/utils/schemaValidator';

export const BLANK_SCHEMA: Record<string, any> = {
  display: 'form',
  title: 'Nueva Consulta Ciudadana',
  name: 'nueva_consulta',
  path: 'nueva-consulta',
  components: [
    {
      type: 'textfield',
      key: 'parroquia',
      label: 'Parroquia',
      placeholder: 'Indique la parroquia',
      required: true
    },
    {
      type: 'button',
      key: 'submit',
      label: 'Enviar Participación',
      action: 'submit',
      theme: 'primary',
      block: true
    }
  ]
};

export function generateSlug(text: string): string {
  return text
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9_]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .slice(0, 100);
}

export function useFormBuilder(
  getInitialSurveyId: () => string | null | undefined,
  onSurveySaved: (surveyId: string) => void
) {
  const surveyId = ref<string | null>(getInitialSurveyId() || null);
  const titulo = ref('Encuesta de Participación Ciudadana');
  const slug = ref('consulta_ciudadana');
  const tipoInstrumento = ref('consulta_ciudadana');
  const activa = ref(true);
  const displayMode = ref<'form' | 'wizard'>('form');

  const currentSchema = ref<Record<string, any>>(JSON.parse(JSON.stringify(BLANK_SCHEMA)));
  const builderRef = ref<InstanceType<typeof FormioBuilder> | null>(null);

  const isSaving = ref(false);
  const isLoadingSurvey = ref(false);
  const successMessage = ref<string | null>(null);
  const errorMessage = ref<string | null>(null);
  const validationModalVisible = ref(false);
  const validationResults = ref<SchemaValidationResult | null>(null);

  const existingSurveys = ref<EncuestaAdminItem[]>([]);
  const selectedExistingSurveyId = ref<string>('');
  const fileInputRef = ref<HTMLInputElement | null>(null);

  function onTituloInput() {
    if (!surveyId.value) {
      slug.value = generateSlug(titulo.value);
    }
  }

  function loadCanonicalPdul() {
    currentSchema.value = JSON.parse(JSON.stringify(pdulCanonicalSchema));
    titulo.value = 'Encuesta Origen-Destino PDUL Maturín';
    slug.value = 'pdul_origen_destino';
    tipoInstrumento.value = 'encuesta_od_pdul';
    displayMode.value = currentSchema.value.display === 'wizard' ? 'wizard' : 'form';
    if (builderRef.value?.setSchema) {
      builderRef.value.setSchema(currentSchema.value);
    }
    successMessage.value = 'Esquema canónico PDUL cargado exitosamente.';
    errorMessage.value = null;
  }

  function loadBlankSchema() {
    currentSchema.value = JSON.parse(JSON.stringify(BLANK_SCHEMA));
    titulo.value = 'Nueva Consulta Ciudadana';
    slug.value = 'nueva_consulta';
    tipoInstrumento.value = 'consulta_ciudadana';
    displayMode.value = 'form';
    if (builderRef.value?.setSchema) {
      builderRef.value.setSchema(currentSchema.value);
    }
    successMessage.value = 'Esquema en blanco cargado.';
    errorMessage.value = null;
  }

  function triggerFileUpload() {
    fileInputRef.value?.click();
  }

  function onFileSelected(event: Event) {
    const target = event.target as HTMLInputElement;
    const file = target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const content = e.target?.result as string;
        const parsed = JSON.parse(content);
        if (!parsed || typeof parsed !== 'object') {
          throw new Error('El archivo no contiene un objeto JSON válido');
        }
        currentSchema.value = parsed;
        if (parsed.title) titulo.value = parsed.title;
        if (parsed.name) slug.value = generateSlug(parsed.name);
        displayMode.value = parsed.display === 'wizard' ? 'wizard' : 'form';
        if (builderRef.value?.setSchema) {
          builderRef.value.setSchema(parsed);
        }
        successMessage.value = `Esquema cargado exitosamente desde "${file.name}".`;
        errorMessage.value = null;
      } catch (err: any) {
        errorMessage.value = `Error al leer archivo JSON: ${err.message || 'Formato inválido'}`;
        successMessage.value = null;
      }
    };
    reader.readAsText(file);
    target.value = '';
  }

  async function loadFromExistingSurvey() {
    if (!selectedExistingSurveyId.value) return;
    isLoadingSurvey.value = true;
    errorMessage.value = null;
    try {
      const survey = await fetchAdminEncuesta(selectedExistingSurveyId.value);
      surveyId.value = survey.id;
      titulo.value = survey.titulo;
      slug.value = survey.slug;
      tipoInstrumento.value = survey.tipo_instrumento;
      activa.value = survey.activa;
      if (survey.esquema_formio) {
        currentSchema.value = survey.esquema_formio;
        displayMode.value = survey.esquema_formio.display === 'wizard' ? 'wizard' : 'form';
        if (builderRef.value?.setSchema) {
          builderRef.value.setSchema(survey.esquema_formio);
        }
      }
      successMessage.value = `Encuesta "${survey.titulo}" cargada para edición.`;
    } catch (err: any) {
      errorMessage.value = `Error al cargar encuesta: ${err.message || 'Fallo de red'}`;
    } finally {
      isLoadingSurvey.value = false;
    }
  }

  function validateCurrentSchema() {
    const exported = builderRef.value?.getSchema?.() || currentSchema.value;
    validationResults.value = validateFormioSchema(exported, { requireSubmit: true });
    validationModalVisible.value = true;
  }

  function exportSchemaJson() {
    const exported = builderRef.value?.getSchema?.() || currentSchema.value;
    const fileName = `${slug.value || 'esquema_encuesta'}.json`;
    const blob = new Blob([JSON.stringify(exported, null, 2)], {
      type: 'application/json'
    });
    triggerBlobDownload(blob, fileName);
    successMessage.value = `Esquema exportado como "${fileName}".`;
  }

  async function saveSurvey(asNew = false) {
    errorMessage.value = null;
    successMessage.value = null;

    if (!titulo.value.trim()) {
      errorMessage.value = 'El título de la encuesta es obligatorio.';
      return;
    }
    if (!slug.value.trim()) {
      errorMessage.value = 'El slug identificador es obligatorio.';
      return;
    }

    const exportedSchema = builderRef.value?.getSchema?.() || currentSchema.value;
    exportedSchema.title = titulo.value;
    exportedSchema.display = displayMode.value;

    isSaving.value = true;
    try {
      if (surveyId.value && !asNew) {
        const updated = await updateAdminEncuesta(surveyId.value, {
          titulo: titulo.value,
          tipo_instrumento: tipoInstrumento.value,
          activa: activa.value,
          esquema_formio: exportedSchema
        });
        successMessage.value = `Encuesta "${updated.titulo}" actualizada exitosamente.`;
        onSurveySaved(updated.id);
      } else {
        const created = await createAdminEncuesta({
          titulo: titulo.value,
          slug: slug.value,
          tipo_instrumento: tipoInstrumento.value,
          activa: activa.value,
          esquema_formio: exportedSchema
        });
        surveyId.value = created.id;
        successMessage.value = `Nueva encuesta "${created.titulo}" guardada exitosamente en la base de datos.`;
        onSurveySaved(created.id);
      }
    } catch (err: any) {
      errorMessage.value = err.message || 'Error al persistir la encuesta en el servidor';
    } finally {
      isSaving.value = false;
    }
  }

  onMounted(async () => {
    try {
      existingSurveys.value = await fetchAdminEncuestas();
    } catch {
      // No bloqueante
    }

    const initialId = getInitialSurveyId();
    if (initialId) {
      selectedExistingSurveyId.value = initialId;
      loadFromExistingSurvey();
    }
  });

  watch(
    getInitialSurveyId,
    (newId) => {
      if (newId && newId !== surveyId.value) {
        selectedExistingSurveyId.value = newId;
        loadFromExistingSurvey();
      }
    }
  );

  return {
    surveyId,
    titulo,
    slug,
    tipoInstrumento,
    activa,
    displayMode,
    currentSchema,
    builderRef,
    isSaving,
    isLoadingSurvey,
    successMessage,
    errorMessage,
    validationModalVisible,
    validationResults,
    existingSurveys,
    selectedExistingSurveyId,
    fileInputRef,
    onTituloInput,
    loadCanonicalPdul,
    loadBlankSchema,
    triggerFileUpload,
    onFileSelected,
    loadFromExistingSurvey,
    validateCurrentSchema,
    exportSchemaJson,
    saveSurvey
  };
}

