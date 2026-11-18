<script setup lang="ts">
import QuestionHelpTip from '@/components/common/QuestionHelpTip.vue';
import { QUESTION_HELP_TIPS } from '@/utils/questionHelpCatalog';
import { TENENCIA_VIVIENDA } from '@/utils/surveyOptions';

defineProps<{
  modelValue: Record<string, any>;
}>();

const emit = defineEmits<{
  (e: 'update-field', field: string, value: any): void;
}>();
</script>

<template>
  <div class="survey-field">
    <div class="survey-label-row">
      <label for="grupos_gastos_separados" class="survey-label">
        1.- ¿Cuántos grupos de personas de esta vivienda mantienen gastos separados para la comida?
      </label>
      <QuestionHelpTip
        :text="QUESTION_HELP_TIPS.grupos_gastos_separados"
        question-label="Grupos con gastos separados para la comida"
      />
    </div>
    <input
      id="grupos_gastos_separados"
      :value="modelValue.grupos_gastos_separados ?? ''"
      type="number"
      inputmode="numeric"
      min="1"
      max="20"
      class="survey-input"
      placeholder="Escriba la cantidad de grupos"
      @input="emit('update-field', 'grupos_gastos_separados', ($event.target as HTMLInputElement).value === '' ? '' : Number(($event.target as HTMLInputElement).value))"
    />
  </div>

  <div class="survey-field">
    <div class="survey-label-row">
      <label for="hogar_numero" class="survey-label">
        Hogar N°:
      </label>
      <QuestionHelpTip
        :text="QUESTION_HELP_TIPS.hogar_numero"
        question-label="Número de hogar dentro de la vivienda"
      />
    </div>
    <input
      id="hogar_numero"
      :value="modelValue.hogar_numero ?? ''"
      type="number"
      inputmode="numeric"
      min="1"
      max="20"
      class="survey-input"
      placeholder="Escriba el número de hogar"
      @input="emit('update-field', 'hogar_numero', ($event.target as HTMLInputElement).value === '' ? '' : Number(($event.target as HTMLInputElement).value))"
    />
  </div>

  <div class="survey-field">
    <div class="survey-label-row">
      <label for="cuartos_dormir_hogar" class="survey-label">
        2.- ¿Cuántos cuartos para dormir utiliza este hogar?
      </label>
      <QuestionHelpTip
        :text="QUESTION_HELP_TIPS.cuartos_dormir_hogar"
        question-label="Cuartos para dormir"
      />
    </div>
    <input
      id="cuartos_dormir_hogar"
      :value="modelValue.cuartos_dormir_hogar ?? ''"
      type="number"
      inputmode="numeric"
      min="1"
      max="20"
      class="survey-input"
      placeholder="Escriba la cantidad de cuartos para dormir"
      @input="emit('update-field', 'cuartos_dormir_hogar', ($event.target as HTMLInputElement).value === '' ? '' : Number(($event.target as HTMLInputElement).value))"
    />
  </div>

  <div class="survey-field">
    <div class="survey-label-row">
      <label for="numero_personas_hogar" class="survey-label">
        3.- Número de personas que residen en este hogar:
      </label>
      <QuestionHelpTip
        :text="QUESTION_HELP_TIPS.numero_personas_hogar"
        question-label="Número de personas que residen en este hogar"
      />
    </div>
    <input
      id="numero_personas_hogar"
      :value="modelValue.numero_personas_hogar ?? ''"
      type="number"
      inputmode="numeric"
      min="1"
      max="30"
      class="survey-input"
      placeholder="Escriba el número de personas que residen en este hogar"
      @input="emit('update-field', 'numero_personas_hogar', ($event.target as HTMLInputElement).value === '' ? '' : Number(($event.target as HTMLInputElement).value))"
    />
  </div>

  <fieldset class="survey-field survey-radio-fieldset">
    <legend class="survey-label">
      <span>4.- Para este hogar la vivienda es:</span>
      <QuestionHelpTip
        :text="QUESTION_HELP_TIPS.tenencia_vivienda"
        question-label="Tenencia de la vivienda"
      />
    </legend>
    <label v-for="op in TENENCIA_VIVIENDA" :key="op.value" class="survey-radio-option">
      <input
        type="radio"
        name="tenencia_vivienda"
        :value="op.value"
        :checked="modelValue.tenencia_vivienda === op.value"
        @change="emit('update-field', 'tenencia_vivienda', op.value)"
      />
      <span>{{ op.label }}</span>
    </label>
    <div v-if="modelValue.tenencia_vivienda === 'otra_forma'" class="survey-field">
      <label for="tenencia_vivienda_otro" class="survey-label">h.- Otra forma (especifique):</label>
      <input
        id="tenencia_vivienda_otro"
        :value="modelValue.tenencia_vivienda_otro || ''"
        type="text"
        class="survey-input"
        placeholder="Escriba otra forma de tenencia"
        @input="emit('update-field', 'tenencia_vivienda_otro', ($event.target as HTMLInputElement).value)"
      />
    </div>
  </fieldset>
</template>
