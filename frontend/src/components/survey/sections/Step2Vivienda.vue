<script setup lang="ts">
import QuestionHelpTip from '@/components/common/QuestionHelpTip.vue';
import { QUESTION_HELP_TIPS } from '@/utils/questionHelpCatalog';
import { TIPOS_VIVIENDA } from '@/utils/surveyOptions';

defineProps<{
  modelValue: Record<string, any>;
}>();

const emit = defineEmits<{
  (e: 'update-field', field: string, value: any): void;
}>();
</script>

<template>
  <fieldset class="survey-field survey-radio-fieldset">
    <legend class="survey-label">
      <span>1.- Tipo de vivienda:</span>
      <QuestionHelpTip
        :text="QUESTION_HELP_TIPS.tipo_vivienda"
        question-label="Tipo de vivienda"
      />
    </legend>
    <label v-for="op in TIPOS_VIVIENDA" :key="op.value" class="survey-radio-option">
      <input
        type="radio"
        name="tipo_vivienda"
        :value="op.value"
        :checked="modelValue.tipo_vivienda === op.value"
        @change="emit('update-field', 'tipo_vivienda', op.value)"
      />
      <span>{{ op.label }}</span>
    </label>
    <div v-if="modelValue.tipo_vivienda === 'otro'" class="survey-field">
      <label for="tipo_vivienda_otro" class="survey-label">g.- Otro tipo:</label>
      <input
        id="tipo_vivienda_otro"
        :value="modelValue.tipo_vivienda_otro || ''"
        type="text"
        class="survey-input"
        placeholder="Escriba qué otro tipo de vivienda es"
        @input="emit('update-field', 'tipo_vivienda_otro', ($event.target as HTMLInputElement).value)"
      />
    </div>
  </fieldset>

  <div class="survey-field">
    <div class="survey-label-row">
      <label for="total_cuartos_vivienda" class="survey-label">
        2.- Contando sala-comedor, cuartos para dormir y otros cuartos, ¿cuántos espacios tiene en total la vivienda?
      </label>
      <QuestionHelpTip
        :text="QUESTION_HELP_TIPS.total_cuartos_vivienda"
        question-label="Cantidad total de espacios de la vivienda"
      />
    </div>
    <span id="hint-total-cuartos" class="survey-hint">
      (No incluye baños, pasillos, balcones, cocina, ni lavaderos)
    </span>
    <input
      id="total_cuartos_vivienda"
      :value="modelValue.total_cuartos_vivienda ?? ''"
      type="number"
      inputmode="numeric"
      min="1"
      aria-describedby="hint-total-cuartos"
      class="survey-input"
      placeholder="Escriba la cantidad total de espacios"
      @input="emit('update-field', 'total_cuartos_vivienda', ($event.target as HTMLInputElement).value === '' ? '' : Number(($event.target as HTMLInputElement).value))"
    />
  </div>
</template>
