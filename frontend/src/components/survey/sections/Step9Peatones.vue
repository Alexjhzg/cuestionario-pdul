<script setup lang="ts">
import QuestionHelpTip from '@/components/common/QuestionHelpTip.vue';
import { QUESTION_HELP_TIPS } from '@/utils/questionHelpCatalog';
import {
  ESCALA_SEGURIDAD_PARQUES,
  OPCIONES_SI_NO,
  PLANES_MOVILIDAD_PESTONAL
} from '@/utils/surveyOptions';

defineProps<{
  modelValue: Record<string, any>;
}>();

const emit = defineEmits<{
  (e: 'update-field', field: string, value: any): void;
}>();
</script>

<template>
  <h2 class="step-section-heading">SECCIÓN IX: PEATONES</h2>

  <!-- BLOQUE A: Cruces Peatonales e Intersecciones -->
  <div class="survey-subsection-card">
    <h3 class="survey-subsection-title">A. Cruces Peatonales e Intersecciones</h3>

    <!-- 1.- Cruce peatonal en todas las intersecciones -->
    <fieldset class="survey-field survey-radio-fieldset">
      <legend class="survey-label">
        <span>1.- ¿Existe cruce peatonal en todas las intersecciones?</span>
        <QuestionHelpTip
          :text="QUESTION_HELP_TIPS.cruce_peatonal_todas"
          question-label="cruces peatonales en intersecciones"
        />
      </legend>
      <div class="survey-radio-group horizontal">
        <label v-for="op in OPCIONES_SI_NO" :key="op.value" class="survey-radio-option">
          <input
            type="radio"
            name="cruce_peatonal_todas"
            :value="op.value"
            :checked="modelValue.cruce_peatonal_todas === op.value"
            @change="emit('update-field', 'cruce_peatonal_todas', op.value)"
          />
          <span>{{ op.label }}</span>
        </label>
      </div>
    </fieldset>

    <!-- 2.- Demarcado y visible (condicional: sí en pregunta 1) -->
    <fieldset v-if="modelValue.cruce_peatonal_todas === 'si'" class="survey-field survey-radio-fieldset">
      <legend class="survey-label">
        <span>2.- ¿Está demarcado y visible?</span>
        <QuestionHelpTip
          :text="QUESTION_HELP_TIPS.cruce_demarcado_visible"
          question-label="demarcación y visibilidad de cruces peatonales"
        />
      </legend>
      <div class="survey-radio-group horizontal">
        <label v-for="op in OPCIONES_SI_NO" :key="op.value" class="survey-radio-option">
          <input
            type="radio"
            name="cruce_demarcado_visible"
            :value="op.value"
            :checked="modelValue.cruce_demarcado_visible === op.value"
            @change="emit('update-field', 'cruce_demarcado_visible', op.value)"
          />
          <span>{{ op.label }}</span>
        </label>
      </div>
    </fieldset>

    <!-- 3.- Seguridad al cruzar intersección (condicional: sí en pregunta 1) -->
    <fieldset v-if="modelValue.cruce_peatonal_todas === 'si'" class="survey-field survey-radio-fieldset">
      <legend class="survey-label">
        <span>3.- ¿Se siente seguro al cruzar esta intersección?</span>
        <QuestionHelpTip
          :text="QUESTION_HELP_TIPS.seguridad_cruzar_interseccion"
          question-label="seguridad al cruzar intersecciones"
        />
      </legend>
      <label v-for="op in ESCALA_SEGURIDAD_PARQUES" :key="op.value" class="survey-radio-option">
        <input
          type="radio"
          name="seguridad_cruzar_interseccion"
          :value="op.value"
          :checked="modelValue.seguridad_cruzar_interseccion === op.value"
          @change="emit('update-field', 'seguridad_cruzar_interseccion', op.value)"
        />
        <span>{{ op.label }}</span>
      </label>
    </fieldset>

    <!-- 4.- Semáforo peatonal -->
    <fieldset class="survey-field survey-radio-fieldset">
      <legend class="survey-label">
        <span>4.- ¿Hay semáforo peatonal?</span>
        <QuestionHelpTip
          :text="QUESTION_HELP_TIPS.hay_semaforo_peatonal"
          question-label="existencia de semáforo peatonal"
        />
      </legend>
      <div class="survey-radio-group horizontal">
        <label v-for="op in OPCIONES_SI_NO" :key="op.value" class="survey-radio-option">
          <input
            type="radio"
            name="hay_semaforo_peatonal"
            :value="op.value"
            :checked="modelValue.hay_semaforo_peatonal === op.value"
            @change="emit('update-field', 'hay_semaforo_peatonal', op.value)"
          />
          <span>{{ op.label }}</span>
        </label>
      </div>
    </fieldset>
  </div>

  <!-- BLOQUE B: Señalización, Accesibilidad y Entorno Urbano -->
  <div class="survey-subsection-card">
    <h3 class="survey-subsection-title">B. Señalización, Accesibilidad y Entorno Urbano</h3>

    <!-- 5.- Mapas peatonales -->
    <fieldset class="survey-field survey-radio-fieldset">
      <legend class="survey-label">
        <span>5.- ¿Existen mapas peatonales, señales de destino o de caminata?</span>
        <QuestionHelpTip
          :text="QUESTION_HELP_TIPS.mapas_senales_caminata"
          question-label="mapas peatonales y señales de caminata"
        />
      </legend>
      <div class="survey-radio-group horizontal">
        <label v-for="op in OPCIONES_SI_NO" :key="op.value" class="survey-radio-option">
          <input
            type="radio"
            name="mapas_senales_caminata"
            :value="op.value"
            :checked="modelValue.mapas_senales_caminata === op.value"
            @change="emit('update-field', 'mapas_senales_caminata', op.value)"
          />
          <span>{{ op.label }}</span>
        </label>
      </div>
    </fieldset>

    <!-- 6.- Movilidad reducida -->
    <fieldset class="survey-field survey-radio-fieldset">
      <legend class="survey-label">
        <span>6.- ¿Puede una persona con movilidad reducida desplazarse sin ayuda por el centro de la ciudad?</span>
        <QuestionHelpTip
          :text="QUESTION_HELP_TIPS.movilidad_reducida_sin_ayuda"
          question-label="accesibilidad para personas con movilidad reducida"
        />
      </legend>
      <div class="survey-radio-group horizontal">
        <label v-for="op in OPCIONES_SI_NO" :key="op.value" class="survey-radio-option">
          <input
            type="radio"
            name="movilidad_reducida_sin_ayuda"
            :value="op.value"
            :checked="modelValue.movilidad_reducida_sin_ayuda === op.value"
            @change="emit('update-field', 'movilidad_reducida_sin_ayuda', op.value)"
          />
          <span>{{ op.label }}</span>
        </label>
      </div>
    </fieldset>

    <!-- 7.- Señalizaciones nombres de calles -->
    <fieldset class="survey-field survey-radio-fieldset">
      <legend class="survey-label">
        <span>7.- ¿Hay señalizaciones de nombres de calles visibles?</span>
        <QuestionHelpTip
          :text="QUESTION_HELP_TIPS.nombres_calles_visibles"
          question-label="señalización de nombres de calles"
        />
      </legend>
      <div class="survey-radio-group horizontal">
        <label v-for="op in OPCIONES_SI_NO" :key="op.value" class="survey-radio-option">
          <input
            type="radio"
            name="nombres_calles_visibles"
            :value="op.value"
            :checked="modelValue.nombres_calles_visibles === op.value"
            @change="emit('update-field', 'nombres_calles_visibles', op.value)"
          />
          <span>{{ op.label }}</span>
        </label>
      </div>
    </fieldset>

    <!-- 8.- Señalización clara y sin obstáculos -->
    <fieldset class="survey-field survey-radio-fieldset">
      <legend class="survey-label">
        <span>8.- ¿La señalización es clara y sin obstáculos?</span>
        <QuestionHelpTip
          :text="QUESTION_HELP_TIPS.senalizacion_clara_sin_obstaculos"
          question-label="claridad de señalización sin obstáculos"
        />
      </legend>
      <div class="survey-radio-group horizontal">
        <label v-for="op in OPCIONES_SI_NO" :key="op.value" class="survey-radio-option">
          <input
            type="radio"
            name="senalizacion_clara_sin_obstaculos"
            :value="op.value"
            :checked="modelValue.senalizacion_clara_sin_obstaculos === op.value"
            @change="emit('update-field', 'senalizacion_clara_sin_obstaculos', op.value)"
          />
          <span>{{ op.label }}</span>
        </label>
      </div>
    </fieldset>

    <!-- 9.- Trayecto a pie seguro -->
    <fieldset class="survey-field survey-radio-fieldset">
      <legend class="survey-label">
        <span>9.- ¿El trayecto a pie hasta la parada es seguro?</span>
        <QuestionHelpTip
          :text="QUESTION_HELP_TIPS.trayecto_pie_parada_seguro"
          question-label="seguridad en trayecto a pie hacia la parada"
        />
      </legend>
      <label v-for="op in ESCALA_SEGURIDAD_PARQUES" :key="op.value" class="survey-radio-option">
        <input
          type="radio"
          name="trayecto_pie_parada_seguro"
          :value="op.value"
          :checked="modelValue.trayecto_pie_parada_seguro === op.value"
          @change="emit('update-field', 'trayecto_pie_parada_seguro', op.value)"
        />
        <span>{{ op.label }}</span>
      </label>
    </fieldset>

    <!-- 10.- Aire y ruido aceptables -->
    <fieldset class="survey-field survey-radio-fieldset">
      <legend class="survey-label">
        <span>10.- ¿El aire y el ruido son aceptables para caminar?</span>
        <QuestionHelpTip
          :text="QUESTION_HELP_TIPS.aire_ruido_aceptables"
          question-label="calidad del aire y nivel de ruido al caminar"
        />
      </legend>
      <div class="survey-radio-group horizontal">
        <label v-for="op in OPCIONES_SI_NO" :key="op.value" class="survey-radio-option">
          <input
            type="radio"
            name="aire_ruido_aceptables"
            :value="op.value"
            :checked="modelValue.aire_ruido_aceptables === op.value"
            @change="emit('update-field', 'aire_ruido_aceptables', op.value)"
          />
          <span>{{ op.label }}</span>
        </label>
      </div>
    </fieldset>

    <!-- 11.- Conductores ceden el paso -->
    <fieldset class="survey-field survey-radio-fieldset">
      <legend class="survey-label">
        <span>11.- ¿Los conductores ceden el paso a los peatones?</span>
        <QuestionHelpTip
          :text="QUESTION_HELP_TIPS.conductores_ceden_paso"
          question-label="respeto de conductores al paso peatonal"
        />
      </legend>
      <div class="survey-radio-group horizontal">
        <label v-for="op in OPCIONES_SI_NO" :key="op.value" class="survey-radio-option">
          <input
            type="radio"
            name="conductores_ceden_paso"
            :value="op.value"
            :checked="modelValue.conductores_ceden_paso === op.value"
            @change="emit('update-field', 'conductores_ceden_paso', op.value)"
          />
          <span>{{ op.label }}</span>
        </label>
      </div>
    </fieldset>

    <!-- 12.- Prioridad del peatón -->
    <fieldset class="survey-field survey-radio-fieldset">
      <legend class="survey-label">
        <span>12.- ¿Considera que la ciudad prioriza al peatón sobre el automóvil?</span>
        <QuestionHelpTip
          :text="QUESTION_HELP_TIPS.ciudad_prioriza_peaton"
          question-label="prioridad del peatón frente al automóvil"
        />
      </legend>
      <div class="survey-radio-group horizontal">
        <label v-for="op in OPCIONES_SI_NO" :key="op.value" class="survey-radio-option">
          <input
            type="radio"
            name="ciudad_prioriza_peaton"
            :value="op.value"
            :checked="modelValue.ciudad_prioriza_peaton === op.value"
            @change="emit('update-field', 'ciudad_prioriza_peaton', op.value)"
          />
          <span>{{ op.label }}</span>
        </label>
      </div>
    </fieldset>

    <!-- 13.- Participación en consultas -->
    <fieldset class="survey-field survey-radio-fieldset">
      <legend class="survey-label">
        <span>13.- ¿Ha participado en consultas sobre espacios peatonales?</span>
        <QuestionHelpTip
          :text="QUESTION_HELP_TIPS.participacion_consultas_peatonales"
          question-label="participación en consultas peatonales"
        />
      </legend>
      <div class="survey-radio-group horizontal">
        <label v-for="op in OPCIONES_SI_NO" :key="op.value" class="survey-radio-option">
          <input
            type="radio"
            name="participacion_consultas_peatonales"
            :value="op.value"
            :checked="modelValue.participacion_consultas_peatonales === op.value"
            @change="emit('update-field', 'participacion_consultas_peatonales', op.value)"
          />
          <span>{{ op.label }}</span>
        </label>
      </div>
    </fieldset>

    <!-- 14.- Planes de movilidad peatonal -->
    <fieldset class="survey-field survey-radio-fieldset">
      <legend class="survey-label">
        <span>14.- ¿Existen planes de movilidad peatonal, presupuesto o normativa de prioridad peatonal?</span>
        <QuestionHelpTip
          :text="QUESTION_HELP_TIPS.planes_movilidad_peatonal_normativa"
          question-label="planes y normativa de movilidad peatonal"
        />
      </legend>
      <label v-for="op in PLANES_MOVILIDAD_PESTONAL" :key="op.value" class="survey-radio-option">
        <input
          type="radio"
          name="planes_movilidad_peatonal_normativa"
          :value="op.value"
          :checked="modelValue.planes_movilidad_peatonal_normativa === op.value"
          @change="emit('update-field', 'planes_movilidad_peatonal_normativa', op.value)"
        />
        <span>{{ op.label }}</span>
      </label>
    </fieldset>
  </div>

  <!-- Observaciones Generales y Cierre -->
  <div class="survey-subsection-card">
    <h3 class="survey-subsection-title">C. Observaciones Finales y Declaración</h3>

    <div class="survey-field">
      <label for="observaciones_generales" class="survey-label">
        Observaciones o Propuestas Adicionales de Movilidad y Espacio Público:
      </label>
      <span id="hint-obs" class="survey-hint">Aporte sus comentarios para el Plan de Desarrollo Urbano Local (PDUL) de Maturín.</span>
      <textarea
        id="observaciones_generales"
        :value="modelValue.observaciones_generales || ''"
        rows="4"
        aria-describedby="hint-obs"
        class="survey-textarea"
        placeholder="Escriba aquí cualquier sugerencia de rutas, paradas, señalización o vialidad..."
        @input="emit('update-field', 'observaciones_generales', ($event.target as HTMLTextAreaElement).value)"
      ></textarea>
    </div>

    <div class="survey-field declaration-field">
      <label for="acepta_declaracion" class="declaration-label">
        <input
          id="acepta_declaracion"
          type="checkbox"
          :checked="modelValue.acepta_declaracion !== false"
          @change="emit('update-field', 'acepta_declaracion', ($event.target as HTMLInputElement).checked)"
        />
        <span>Declaro que la información suministrada es verídica y autorizo su tratamiento estadístico anónimo para el Plan de Desarrollo Urbano Local (PDUL) de Maturín.</span>
      </label>
    </div>
  </div>
</template>

