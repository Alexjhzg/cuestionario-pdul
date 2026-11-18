<script setup lang="ts">
import QuestionHelpTip from '@/components/common/QuestionHelpTip.vue';
import { QUESTION_HELP_TIPS } from '@/utils/questionHelpCatalog';
import {
  ACUERDO_RUTAS_DIRECTAS,
  CALIFICACION_TP,
  DIFICULTADES_ACCESO_TP,
  OPCIONES_SI_NO_SIN_TILDE
} from '@/utils/surveyOptions';

defineProps<{
  modelValue: Record<string, any>;
}>();

const emit = defineEmits<{
  (e: 'update-field', field: string, value: any): void;
}>();
</script>

<template>
  <h2 class="step-section-heading">SECCIÓN VI: CARACTERÍSTICAS DE TRANSPORTE PÚBLICO (SI SE UTILIZÓ EN ALGÚN VIAJE)</h2>

  <div class="survey-field">
    <div class="survey-label-row">
      <label for="rutas_tp_dia" class="survey-label">
        1.- ¿Cuántas rutas de transporte público diferentes utilizó en el día?
      </label>
      <QuestionHelpTip
        :text="QUESTION_HELP_TIPS.rutas_tp_dia"
        question-label="cantidad de rutas de transporte público utilizadas"
      />
    </div>
    <input
      id="rutas_tp_dia"
      :value="modelValue.rutas_tp_dia ?? ''"
      type="number"
      inputmode="numeric"
      min="0"
      max="20"
      class="survey-input"
      placeholder="0 si no utilizó o cantidad de rutas"
      @input="emit('update-field', 'rutas_tp_dia', ($event.target as HTMLInputElement).value === '' ? '' : Number(($event.target as HTMLInputElement).value))"
    />
  </div>

  <div class="survey-field">
    <div class="survey-label-row">
      <label for="tiempo_espera_paradas_min" class="survey-label">
        2.- Tiempo total de espera en las paradas (suma de todos los viajes, colocar el tiempo en minutos):
      </label>
      <QuestionHelpTip
        :text="QUESTION_HELP_TIPS.tiempo_espera_paradas_min"
        question-label="tiempo total de espera en paradas"
      />
    </div>
    <input
      id="tiempo_espera_paradas_min"
      :value="modelValue.tiempo_espera_paradas_min ?? ''"
      type="number"
      inputmode="numeric"
      min="0"
      max="600"
      class="survey-input"
      placeholder="0 si no esperó o tiempo en minutos"
      @input="emit('update-field', 'tiempo_espera_paradas_min', ($event.target as HTMLInputElement).value === '' ? '' : Number(($event.target as HTMLInputElement).value))"
    />
  </div>

  <div class="survey-field">
    <div class="survey-label-row">
      <label for="km_residencia_parada" class="survey-label">
        3.- ¿Cuánto kilómetros aproximadamente recorrió desde su residencia hasta la parada para tomar el transporte público?
      </label>
      <QuestionHelpTip
        :text="QUESTION_HELP_TIPS.km_residencia_parada"
        question-label="distancia en kilómetros hasta la parada"
      />
    </div>
    <input
      id="km_residencia_parada"
      :value="modelValue.km_residencia_parada ?? ''"
      type="number"
      inputmode="decimal"
      step="0.1"
      min="0"
      max="100"
      class="survey-input"
      placeholder="0 si vive al lado o distancia en kilómetros (ej. 0.5)"
      @input="emit('update-field', 'km_residencia_parada', ($event.target as HTMLInputElement).value === '' ? '' : Number(($event.target as HTMLInputElement).value))"
    />
  </div>

  <fieldset class="survey-field survey-radio-fieldset">
    <legend class="survey-label">
      <span>4.- ¿Ha tenido dificultades para acceder al transporte público en su zona?</span>
      <QuestionHelpTip
        :text="QUESTION_HELP_TIPS.dificultades_acceso_tp"
        question-label="dificultades para acceder al transporte público"
      />
    </legend>
    <div class="survey-radio-group horizontal">
      <label v-for="op in OPCIONES_SI_NO_SIN_TILDE" :key="op.value" class="survey-radio-option">
        <input
          type="radio"
          name="dificultades_acceso_tp"
          :value="op.value"
          :checked="modelValue.dificultades_acceso_tp === op.value"
          @change="emit('update-field', 'dificultades_acceso_tp', op.value)"
        />
        <span>{{ op.label }}</span>
      </label>
    </div>
  </fieldset>

  <fieldset v-if="modelValue.dificultades_acceso_tp === 'si'" class="survey-field survey-radio-fieldset">
    <legend class="survey-label">
      <span>5.- Si marcó Si, indique la principal dificultad:</span>
      <QuestionHelpTip
        :text="QUESTION_HELP_TIPS.principal_dificultad_tp"
        question-label="principal dificultad de acceso al transporte público"
      />
    </legend>
    <label v-for="op in DIFICULTADES_ACCESO_TP" :key="op.value" class="survey-radio-option">
      <input
        type="radio"
        name="principal_dificultad_tp"
        :value="op.value"
        :checked="modelValue.principal_dificultad_tp === op.value"
        @change="emit('update-field', 'principal_dificultad_tp', op.value)"
      />
      <span>{{ op.label }}</span>
    </label>
    <div v-if="modelValue.principal_dificultad_tp === 'otro'" class="survey-field nested-field">
      <label for="principal_dificultad_tp_otro" class="survey-label">e.- Otro (especifique):</label>
      <input
        id="principal_dificultad_tp_otro"
        :value="modelValue.principal_dificultad_tp_otro || ''"
        type="text"
        class="survey-input"
        placeholder="Describa la principal dificultad"
        @input="emit('update-field', 'principal_dificultad_tp_otro', ($event.target as HTMLInputElement).value)"
      />
    </div>
  </fieldset>

  <fieldset class="survey-field survey-radio-fieldset">
    <legend class="survey-label">
      <span>6.- ¿Considera que el servicio de transporte público es:</span>
      <QuestionHelpTip
        :text="QUESTION_HELP_TIPS.calificacion_servicio_tp"
        question-label="calificación del servicio de transporte público"
      />
    </legend>
    <label v-for="op in CALIFICACION_TP" :key="op.value" class="survey-radio-option">
      <input
        type="radio"
        name="calificacion_servicio_tp"
        :value="op.value"
        :checked="modelValue.calificacion_servicio_tp === op.value"
        @change="emit('update-field', 'calificacion_servicio_tp', op.value)"
      />
      <span>{{ op.label }}</span>
    </label>
  </fieldset>

  <div class="survey-field">
    <div class="survey-label-row">
      <label for="gasto_semanal_transporte_bs" class="survey-label">
        7.- ¿Cuánto gasta semanalmente en transporte (todos los miembros del hogar)? (en bolívares):
      </label>
      <QuestionHelpTip
        :text="QUESTION_HELP_TIPS.gasto_semanal_transporte_bs"
        question-label="gasto semanal en transporte público"
      />
    </div>
    <input
      id="gasto_semanal_transporte_bs"
      :value="modelValue.gasto_semanal_transporte_bs ?? ''"
      type="number"
      inputmode="numeric"
      min="0"
      class="survey-input"
      placeholder="0 si no posee o monto en Bs."
      @input="emit('update-field', 'gasto_semanal_transporte_bs', ($event.target as HTMLInputElement).value === '' ? '' : Number(($event.target as HTMLInputElement).value))"
    />
  </div>

  <fieldset class="survey-field survey-radio-fieldset">
    <legend class="survey-label">
      <span>8.- ¿Estaría usted de acuerdo en que se crean rutas directas desde su origen a su destino final?</span>
      <QuestionHelpTip
        :text="QUESTION_HELP_TIPS.acuerdo_rutas_directas"
        question-label="acuerdo con rutas directas de transporte público"
      />
    </legend>
    <label v-for="op in ACUERDO_RUTAS_DIRECTAS" :key="op.value" class="survey-radio-option">
      <input
        type="radio"
        name="acuerdo_rutas_directas"
        :value="op.value"
        :checked="modelValue.acuerdo_rutas_directas === op.value"
        @change="emit('update-field', 'acuerdo_rutas_directas', op.value)"
      />
      <span>{{ op.label }}</span>
    </label>
  </fieldset>

  <div class="survey-field">
    <div class="survey-label-row">
      <label for="comentarios_transporte_maturin" class="survey-label">
        9.- ¿Tiene algún comentario o sugerencia sobre el transporte en Maturín?
      </label>
      <QuestionHelpTip
        :text="QUESTION_HELP_TIPS.comentarios_transporte_maturin"
        question-label="comentarios sobre el transporte en Maturín"
      />
    </div>
    <textarea
      id="comentarios_transporte_maturin"
      :value="modelValue.comentarios_transporte_maturin || ''"
      class="survey-input survey-textarea"
      rows="3"
      placeholder="Escriba aquí sus comentarios o sugerencias..."
      @input="emit('update-field', 'comentarios_transporte_maturin', ($event.target as HTMLTextAreaElement).value)"
    ></textarea>
  </div>
</template>

