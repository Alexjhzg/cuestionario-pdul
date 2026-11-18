<script setup lang="ts">
import QuestionHelpTip from '@/components/common/QuestionHelpTip.vue';
import { QUESTION_HELP_TIPS } from '@/utils/questionHelpCatalog';
import {
  MODO_CENTRO_ACTIVIDADES,
  MOTIVOS_CAMBIO_DESPLAZAMIENTO,
  OPCIONES_SI_NO_SIN_TILDE,
  SEGURIDAD_CENTRO
} from '@/utils/surveyOptions';

defineProps<{
  modelValue: Record<string, any>;
}>();

const emit = defineEmits<{
  (e: 'update-field', field: string, value: any): void;
}>();
</script>

<template>
  <h2 class="step-section-heading">SECCIÓN VII: MOVILIDAD NO MOTORIZADA Y PERCEPCIÓN</h2>

  <fieldset class="survey-field survey-radio-fieldset">
    <legend class="survey-label">
      <span>1.- ¿Ha cambiado su forma de desplazarse en los últimos 5 años?</span>
      <QuestionHelpTip
        :text="QUESTION_HELP_TIPS.cambio_movilidad_5_anos"
        question-label="cambio en su forma de desplazarse en 5 años"
      />
    </legend>
    <div class="survey-radio-group horizontal">
      <label v-for="op in OPCIONES_SI_NO_SIN_TILDE" :key="op.value" class="survey-radio-option">
        <input
          type="radio"
          name="cambio_movilidad_5_anos"
          :value="op.value"
          :checked="modelValue.cambio_movilidad_5_anos === op.value"
          @change="emit('update-field', 'cambio_movilidad_5_anos', op.value)"
        />
        <span>{{ op.label }}</span>
      </label>
    </div>
  </fieldset>

  <fieldset v-if="modelValue.cambio_movilidad_5_anos === 'si'" class="survey-field survey-radio-fieldset">
    <legend class="survey-label">
      <span>2.- Si marcó Sí, ¿por qué motivo?</span>
      <QuestionHelpTip
        :text="QUESTION_HELP_TIPS.motivo_cambio_desplazamiento"
        question-label="motivo de cambio de desplazamiento"
      />
    </legend>
    <label v-for="op in MOTIVOS_CAMBIO_DESPLAZAMIENTO" :key="op.value" class="survey-radio-option">
      <input
        type="radio"
        name="motivo_cambio_desplazamiento"
        :value="op.value"
        :checked="modelValue.motivo_cambio_desplazamiento === op.value"
        @change="emit('update-field', 'motivo_cambio_desplazamiento', op.value)"
      />
      <span>{{ op.label }}</span>
    </label>
    <div v-if="modelValue.motivo_cambio_desplazamiento === 'otro'" class="survey-field nested-field">
      <label for="motivo_cambio_desplazamiento_otro" class="survey-label">e.- Otro (especifique):</label>
      <input
        id="motivo_cambio_desplazamiento_otro"
        :value="modelValue.motivo_cambio_desplazamiento_otro || ''"
        type="text"
        class="survey-input"
        placeholder="Describa el motivo"
        @input="emit('update-field', 'motivo_cambio_desplazamiento_otro', ($event.target as HTMLInputElement).value)"
      />
    </div>
  </fieldset>

  <fieldset class="survey-field survey-radio-fieldset">
    <legend class="survey-label">
      <span>3.- ¿Realiza caminatas de más de 10 minutos como parte de sus desplazamientos?</span>
      <QuestionHelpTip
        :text="QUESTION_HELP_TIPS.caminatas_mas_10min"
        question-label="caminatas de más de 10 minutos"
      />
    </legend>
    <div class="survey-radio-group horizontal">
      <label v-for="op in OPCIONES_SI_NO_SIN_TILDE" :key="op.value" class="survey-radio-option">
        <input
          type="radio"
          name="caminatas_mas_10min"
          :value="op.value"
          :checked="modelValue.caminatas_mas_10min === op.value"
          @change="emit('update-field', 'caminatas_mas_10min', op.value)"
        />
        <span>{{ op.label }}</span>
      </label>
    </div>
  </fieldset>

  <fieldset class="survey-field survey-radio-fieldset">
    <legend class="survey-label">
      <span>4.- ¿Utiliza bicicleta como medio de transporte?</span>
      <QuestionHelpTip
        :text="QUESTION_HELP_TIPS.usa_bicicleta"
        question-label="uso de bicicleta como medio de transporte"
      />
    </legend>
    <div class="survey-radio-group horizontal">
      <label v-for="op in OPCIONES_SI_NO_SIN_TILDE" :key="op.value" class="survey-radio-option">
        <input
          type="radio"
          name="usa_bicicleta"
          :value="op.value"
          :checked="modelValue.usa_bicicleta === op.value"
          @change="emit('update-field', 'usa_bicicleta', op.value)"
        />
        <span>{{ op.label }}</span>
      </label>
    </div>
  </fieldset>

  <div class="survey-field">
    <div class="survey-label-row">
      <label for="dias_camina_bici_semana" class="survey-label">
        5.- ¿Cuántos días a la semana camina o usa bicicleta para desplazarse?
      </label>
      <QuestionHelpTip
        :text="QUESTION_HELP_TIPS.dias_camina_bici_semana"
        question-label="días a la semana que camina o usa bicicleta"
      />
    </div>
    <input
      id="dias_camina_bici_semana"
      :value="modelValue.dias_camina_bici_semana ?? ''"
      type="number"
      inputmode="numeric"
      min="0"
      max="7"
      class="survey-input"
      placeholder="0 si nunca o cantidad de días (0 a 7)"
      @input="emit('update-field', 'dias_camina_bici_semana', ($event.target as HTMLInputElement).value === '' ? '' : Number(($event.target as HTMLInputElement).value))"
    />
  </div>

  <fieldset class="survey-field survey-radio-fieldset">
    <legend class="survey-label">
      <span>6.- ¿Realiza desplazamiento en el centro de la ciudad para hacer sus actividades o utiliza el transporte público?</span>
      <QuestionHelpTip
        :text="QUESTION_HELP_TIPS.modo_actividades_centro"
        question-label="desplazamientos en el centro de la ciudad"
      />
    </legend>
    <label v-for="op in MODO_CENTRO_ACTIVIDADES" :key="op.value" class="survey-radio-option">
      <input
        type="radio"
        name="modo_actividades_centro"
        :value="op.value"
        :checked="modelValue.modo_actividades_centro === op.value"
        @change="emit('update-field', 'modo_actividades_centro', op.value)"
      />
      <span>{{ op.label }}</span>
    </label>
  </fieldset>

  <fieldset class="survey-field survey-radio-fieldset">
    <legend class="survey-label">
      <span>7.- ¿Considera que las aceras y espacios peatonales son adecuados?</span>
      <QuestionHelpTip
        :text="QUESTION_HELP_TIPS.aceras_adecuadas"
        question-label="estado de las aceras y espacios peatonales"
      />
    </legend>
    <div class="survey-radio-group horizontal">
      <label v-for="op in OPCIONES_SI_NO_SIN_TILDE" :key="op.value" class="survey-radio-option">
        <input
          type="radio"
          name="aceras_adecuadas"
          :value="op.value"
          :checked="modelValue.aceras_adecuadas === op.value"
          @change="emit('update-field', 'aceras_adecuadas', op.value)"
        />
        <span>{{ op.label }}</span>
      </label>
    </div>
  </fieldset>

  <fieldset class="survey-field survey-radio-fieldset">
    <legend class="survey-label">
      <span>8.- ¿Se siente seguro al desplazarse por el centro de la ciudad?</span>
      <QuestionHelpTip
        :text="QUESTION_HELP_TIPS.seguridad_desplazamiento_centro"
        question-label="seguridad al desplazarse por el centro"
      />
    </legend>
    <label v-for="op in SEGURIDAD_CENTRO" :key="op.value" class="survey-radio-option">
      <input
        type="radio"
        name="seguridad_desplazamiento_centro"
        :value="op.value"
        :checked="modelValue.seguridad_desplazamiento_centro === op.value"
        @change="emit('update-field', 'seguridad_desplazamiento_centro', op.value)"
      />
      <span>{{ op.label }}</span>
    </label>
  </fieldset>
</template>

