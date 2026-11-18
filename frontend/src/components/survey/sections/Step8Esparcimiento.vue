<script setup lang="ts">
import QuestionHelpTip from '@/components/common/QuestionHelpTip.vue';
import { QUESTION_HELP_TIPS } from '@/utils/questionHelpCatalog';
import {
  ACTIVIDADES_PARQUES,
  ACUERDO_ACERA_COMODA,
  CALIFICACION_LIMPIEZA,
  CAMINATAS_CIUDAD,
  DISPOSICION_PARTICIPAR,
  ESCALA_SEGURIDAD_PARQUES,
  ESPARCIMIENTOS_FALTANTES,
  FACILIDAD_LLEGADA,
  FRECUENCIA_VISITA_PARQUES,
  IMPEDIMENTOS_ESPACIOS,
  MEJORAS_PRIORITARIAS,
  OPCIONES_SI_NO,
  PLANES_MOVILIDAD_PESTONAL,
  SATISFACCION_CENTRO
} from '@/utils/surveyOptions';

defineProps<{
  modelValue: Record<string, any>;
}>();

const emit = defineEmits<{
  (e: 'update-field', field: string, value: any): void;
  (e: 'toggle-multi', field: string, value: string): void;
}>();

function isCheckedMulti(arr: unknown, value: string): boolean {
  return Array.isArray(arr) && arr.includes(value);
}
</script>

<template>
  <h2 class="step-section-heading">SECCIÓN VIII: ESPARCIMIENTOS</h2>

  <!-- BLOQUE A: Parques y Espacios de Recreación -->
  <div class="survey-subsection-card">
    <h3 class="survey-subsection-title">A. Uso y Percepción de Parques y Plazas</h3>

    <fieldset class="survey-field survey-radio-fieldset">
      <legend class="survey-label">
        <span>1.- ¿Con qué frecuencia visita parques, plazas u otras áreas de esparcimientos?</span>
        <QuestionHelpTip
          :text="QUESTION_HELP_TIPS.frecuencia_visita_parques"
          question-label="frecuencia de visita a parques y plazas"
        />
      </legend>
      <label v-for="op in FRECUENCIA_VISITA_PARQUES" :key="op.value" class="survey-radio-option">
        <input
          type="radio"
          name="frecuencia_visita_parques"
          :value="op.value"
          :checked="modelValue.frecuencia_visita_parques === op.value"
          @change="emit('update-field', 'frecuencia_visita_parques', op.value)"
        />
        <span>{{ op.label }}</span>
      </label>
    </fieldset>

    <fieldset class="survey-field survey-radio-fieldset">
      <legend class="survey-label">
        <span>2.- ¿Qué actividad realiza principalmente en estos espacios? (admite respuestas múltiples):</span>
        <QuestionHelpTip
          :text="QUESTION_HELP_TIPS.actividades_parques"
          question-label="actividades principales en parques y plazas"
        />
      </legend>
      <label v-for="op in ACTIVIDADES_PARQUES" :key="op.value" class="survey-checkbox-option">
        <input
          type="checkbox"
          name="actividades_parques"
          :value="op.value"
          :checked="isCheckedMulti(modelValue.actividades_parques, op.value)"
          @change="emit('toggle-multi', 'actividades_parques', op.value)"
        />
        <span>{{ op.label }}</span>
      </label>
      <div v-if="isCheckedMulti(modelValue.actividades_parques, 'otras')" class="survey-field nested-field">
        <label for="actividades_parques_otras" class="survey-label">g.- Otras actividades (especifique):</label>
        <input
          id="actividades_parques_otras"
          :value="modelValue.actividades_parques_otras || ''"
          type="text"
          class="survey-input"
          placeholder="Especifique qué otra actividad realiza"
          @input="emit('update-field', 'actividades_parques_otras', ($event.target as HTMLInputElement).value)"
        />
      </div>
    </fieldset>

    <fieldset class="survey-field survey-radio-fieldset">
      <legend class="survey-label">
        <span>3.- ¿Suele hacer caminatas por la ciudad?</span>
        <QuestionHelpTip
          :text="QUESTION_HELP_TIPS.caminatas_ciudad"
          question-label="caminatas por la ciudad"
        />
      </legend>
      <div class="survey-radio-group horizontal">
        <label v-for="op in CAMINATAS_CIUDAD" :key="op.value" class="survey-radio-option">
          <input
            type="radio"
            name="caminatas_ciudad"
            :value="op.value"
            :checked="modelValue.caminatas_ciudad === op.value"
            @change="emit('update-field', 'caminatas_ciudad', op.value)"
          />
          <span>{{ op.label }}</span>
        </label>
      </div>
    </fieldset>

    <fieldset class="survey-field survey-radio-fieldset">
      <legend class="survey-label">
        <span>7.- ¿Qué tan seguro(a) se siente en parques y rutas peatonales durante el día?</span>
        <QuestionHelpTip
          :text="QUESTION_HELP_TIPS.seguridad_parques_dia"
          question-label="seguridad diurna en parques y rutas peatonales"
        />
      </legend>
      <label v-for="op in ESCALA_SEGURIDAD_PARQUES" :key="op.value" class="survey-radio-option">
        <input
          type="radio"
          name="seguridad_parques_dia"
          :value="op.value"
          :checked="modelValue.seguridad_parques_dia === op.value"
          @change="emit('update-field', 'seguridad_parques_dia', op.value)"
        />
        <span>{{ op.label }}</span>
      </label>
    </fieldset>

    <fieldset class="survey-field survey-radio-fieldset">
      <legend class="survey-label">
        <span>8.- ¿Qué tan seguro(a) se siente en parques y rutas peatonales durante la noche?</span>
        <QuestionHelpTip
          :text="QUESTION_HELP_TIPS.seguridad_parques_noche"
          question-label="seguridad nocturna en parques y rutas peatonales"
        />
      </legend>
      <label v-for="op in ESCALA_SEGURIDAD_PARQUES" :key="op.value" class="survey-radio-option">
        <input
          type="radio"
          name="seguridad_parques_noche"
          :value="op.value"
          :checked="modelValue.seguridad_parques_noche === op.value"
          @change="emit('update-field', 'seguridad_parques_noche', op.value)"
        />
        <span>{{ op.label }}</span>
      </label>
    </fieldset>

    <fieldset class="survey-field survey-radio-fieldset">
      <legend class="survey-label">
        <span>9.- ¿Cómo califica la limpieza y conservación de las áreas de esparcimiento?</span>
        <QuestionHelpTip
          :text="QUESTION_HELP_TIPS.limpieza_parques"
          question-label="limpieza y conservación de áreas de esparcimiento"
        />
      </legend>
      <label v-for="op in CALIFICACION_LIMPIEZA" :key="op.value" class="survey-radio-option">
        <input
          type="radio"
          name="limpieza_parques"
          :value="op.value"
          :checked="modelValue.limpieza_parques === op.value"
          @change="emit('update-field', 'limpieza_parques', op.value)"
        />
        <span>{{ op.label }}</span>
      </label>
    </fieldset>

    <fieldset class="survey-field survey-radio-fieldset">
      <legend class="survey-label">
        <span>10.- ¿Qué le impide usar más estos espacios? (admite respuestas múltiples):</span>
        <QuestionHelpTip
          :text="QUESTION_HELP_TIPS.impedimentos_espacios"
          question-label="impedimentos para usar áreas de esparcimiento"
        />
      </legend>
      <label v-for="op in IMPEDIMENTOS_ESPACIOS" :key="op.value" class="survey-checkbox-option">
        <input
          type="checkbox"
          name="impedimentos_espacios"
          :value="op.value"
          :checked="isCheckedMulti(modelValue.impedimentos_espacios, op.value)"
          @change="emit('toggle-multi', 'impedimentos_espacios', op.value)"
        />
        <span>{{ op.label }}</span>
      </label>
      <div v-if="isCheckedMulti(modelValue.impedimentos_espacios, 'otras')" class="survey-field nested-field">
        <label for="impedimentos_espacios_otras" class="survey-label">f.- Otras (especifique):</label>
        <input
          id="impedimentos_espacios_otras"
          :value="modelValue.impedimentos_espacios_otras || ''"
          type="text"
          class="survey-input"
          placeholder="Especifique qué otra razón le impide usarlos"
          @input="emit('update-field', 'impedimentos_espacios_otras', ($event.target as HTMLInputElement).value)"
        />
      </div>
    </fieldset>

    <fieldset class="survey-field survey-radio-fieldset">
      <legend class="survey-label">
        <span>11.- ¿Qué tan satisfecho(a) está con la cantidad y calidad de áreas de esparcimiento y caminata que hay en el centro de la ciudad?</span>
        <QuestionHelpTip
          :text="QUESTION_HELP_TIPS.satisfaccion_centro"
          question-label="satisfacción con áreas de esparcimiento del centro"
        />
      </legend>
      <label v-for="op in SATISFACCION_CENTRO" :key="op.value" class="survey-radio-option">
        <input
          type="radio"
          name="satisfaccion_centro"
          :value="op.value"
          :checked="modelValue.satisfaccion_centro === op.value"
          @change="emit('update-field', 'satisfaccion_centro', op.value)"
        />
        <span>{{ op.label }}</span>
      </label>
    </fieldset>

    <fieldset class="survey-field survey-radio-fieldset">
      <legend class="survey-label">
        <span>12.- ¿Qué mejoras deberían priorizarse? (admite respuestas múltiples):</span>
        <QuestionHelpTip
          :text="QUESTION_HELP_TIPS.mejoras_prioritarias"
          question-label="mejoras prioritarias en esparcimiento"
        />
      </legend>
      <label v-for="op in MEJORAS_PRIORITARIAS" :key="op.value" class="survey-checkbox-option">
        <input
          type="checkbox"
          name="mejoras_prioritarias"
          :value="op.value"
          :checked="isCheckedMulti(modelValue.mejoras_prioritarias, op.value)"
          @change="emit('toggle-multi', 'mejoras_prioritarias', op.value)"
        />
        <span>{{ op.label }}</span>
      </label>
      <div v-if="isCheckedMulti(modelValue.mejoras_prioritarias, 'otro')" class="survey-field nested-field">
        <label for="mejoras_prioritarias_otro" class="survey-label">m.- Otro (especifique):</label>
        <input
          id="mejoras_prioritarias_otro"
          :value="modelValue.mejoras_prioritarias_otro || ''"
          type="text"
          class="survey-input"
          placeholder="Describa qué otra mejora priorizar"
          @input="emit('update-field', 'mejoras_prioritarias_otro', ($event.target as HTMLInputElement).value)"
        />
      </div>
    </fieldset>

    <div class="survey-field">
      <div class="survey-label-row">
        <label for="parque_mejorar_primero" class="survey-label">
          13.- ¿Qué parque, plaza o ruta de esparcimiento considera que debe mejorarse primero?
        </label>
        <QuestionHelpTip
          :text="QUESTION_HELP_TIPS.parque_mejorar_primero"
          question-label="parque o plaza a mejorar primero"
        />
      </div>
      <input
        id="parque_mejorar_primero"
        :value="modelValue.parque_mejorar_primero || ''"
        type="text"
        class="survey-input"
        placeholder="Indique el nombre del parque, plaza o sector prioritario"
        @input="emit('update-field', 'parque_mejorar_primero', ($event.target as HTMLInputElement).value)"
      />
    </div>

    <fieldset class="survey-field survey-radio-fieldset">
      <legend class="survey-label">
        <span>14.- ¿Estaría dispuesto(a) a participar en actividades de mejoras de estos espacios?</span>
        <QuestionHelpTip
          :text="QUESTION_HELP_TIPS.disposicion_participar_mejoras"
          question-label="disposición a participar en mejoras"
        />
      </legend>
      <div class="survey-radio-group horizontal">
        <label v-for="op in DISPOSICION_PARTICIPAR" :key="op.value" class="survey-radio-option">
          <input
            type="radio"
            name="disposicion_participar_mejoras"
            :value="op.value"
            :checked="modelValue.disposicion_participar_mejoras === op.value"
            @change="emit('update-field', 'disposicion_participar_mejoras', op.value)"
          />
          <span>{{ op.label }}</span>
        </label>
      </div>
    </fieldset>

    <div class="survey-field">
      <div class="survey-label-row">
        <label for="sugerencias_esparcimiento" class="survey-label">
          15.- ¿Qué sugerencia daría para mejorar las áreas de esparcimiento y caminatas de la ciudad?
        </label>
        <QuestionHelpTip
          :text="QUESTION_HELP_TIPS.sugerencias_esparcimiento"
          question-label="sugerencias para áreas de esparcimiento"
        />
      </div>
      <textarea
        id="sugerencias_esparcimiento"
        :value="modelValue.sugerencias_esparcimiento || ''"
        class="survey-input survey-textarea"
        rows="3"
        placeholder="Escriba aquí sus sugerencias..."
        @input="emit('update-field', 'sugerencias_esparcimiento', ($event.target as HTMLTextAreaElement).value)"
      ></textarea>
    </div>
  </div>

  <!-- BLOQUE B: Aceras y Rutas de Caminata -->
  <div class="survey-subsection-card">
    <h3 class="survey-subsection-title">B. Infraestructura y Rutas de Caminata</h3>

    <fieldset class="survey-field survey-radio-fieldset">
      <legend class="survey-label">
        <span>16.- ¿Considera que la acera es suficiente y cómoda para caminar?</span>
        <QuestionHelpTip
          :text="QUESTION_HELP_TIPS.acera_comoda"
          question-label="suficiencia y comodidad de aceras"
        />
      </legend>
      <label v-for="op in ACUERDO_ACERA_COMODA" :key="op.value" class="survey-radio-option">
        <input
          type="radio"
          name="acera_comoda"
          :value="op.value"
          :checked="modelValue.acera_comoda === op.value"
          @change="emit('update-field', 'acera_comoda', op.value)"
        />
        <span>{{ op.label }}</span>
      </label>
    </fieldset>

    <div class="survey-field">
      <div class="survey-label-row">
        <label for="sectores_para_caminar" class="survey-label">
          17.- ¿Qué sector o sectores utiliza para caminar? (Colocar los sectores):
        </label>
        <QuestionHelpTip
          :text="QUESTION_HELP_TIPS.sectores_para_caminar"
          question-label="sectores que utiliza para caminar"
        />
      </div>
      <input
        id="sectores_para_caminar"
        :value="modelValue.sectores_para_caminar || ''"
        type="text"
        class="survey-input"
        placeholder="Ej: Av. Bolívar, Casco Central, Plaza Rómulo Gallegos..."
        @input="emit('update-field', 'sectores_para_caminar', ($event.target as HTMLInputElement).value)"
      />
    </div>

    <fieldset class="survey-field survey-radio-fieldset">
      <legend class="survey-label">
        <span>18.- ¿Qué tan fácil es llegar desde su hogar a las áreas de esparcimiento o ruta de caminata?</span>
        <QuestionHelpTip
          :text="QUESTION_HELP_TIPS.facilidad_llegada_parques"
          question-label="facilidad para llegar a áreas de esparcimiento"
        />
      </legend>
      <label v-for="op in FACILIDAD_LLEGADA" :key="op.value" class="survey-radio-option">
        <input
          type="radio"
          name="facilidad_llegada_parques"
          :value="op.value"
          :checked="modelValue.facilidad_llegada_parques === op.value"
          @change="emit('update-field', 'facilidad_llegada_parques', op.value)"
        />
        <span>{{ op.label }}</span>
      </label>
    </fieldset>

    <fieldset class="survey-field survey-radio-fieldset">
      <legend class="survey-label">
        <span>19.- ¿Qué esparcimientos considera que faltan en estos espacios? (admite respuestas múltiples):</span>
        <QuestionHelpTip
          :text="QUESTION_HELP_TIPS.esparcimientos_faltantes"
          question-label="equipamientos faltantes en espacios públicos"
        />
      </legend>
      <label v-for="op in ESPARCIMIENTOS_FALTANTES" :key="op.value" class="survey-checkbox-option">
        <input
          type="checkbox"
          name="esparcimientos_faltantes"
          :value="op.value"
          :checked="isCheckedMulti(modelValue.esparcimientos_faltantes, op.value)"
          @change="emit('toggle-multi', 'esparcimientos_faltantes', op.value)"
        />
        <span>{{ op.label }}</span>
      </label>
      <div v-if="isCheckedMulti(modelValue.esparcimientos_faltantes, 'otros')" class="survey-field nested-field">
        <label for="esparcimientos_faltantes_otros" class="survey-label">i.- Otros (especifique):</label>
        <input
          id="esparcimientos_faltantes_otros"
          :value="modelValue.esparcimientos_faltantes_otros || ''"
          type="text"
          class="survey-input"
          placeholder="Especifique qué otro elemento o servicio falta"
          @input="emit('update-field', 'esparcimientos_faltantes_otros', ($event.target as HTMLInputElement).value)"
        />
      </div>
    </fieldset>
  </div>

  <!-- BLOQUE C: Cruces Peatonales e Intersecciones -->
  <div class="survey-subsection-card">
    <h3 class="survey-subsection-title">C. Cruces Peatonales e Intersecciones</h3>

    <fieldset class="survey-field survey-radio-fieldset">
      <legend class="survey-label">
        <span>20.- ¿Existe cruce peatonal en todas las intersecciones?</span>
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

    <fieldset v-if="modelValue.cruce_peatonal_todas === 'si'" class="survey-field survey-radio-fieldset">
      <legend class="survey-label">
        <span>21.- ¿Está demarcado y visible?</span>
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

    <fieldset class="survey-field survey-radio-fieldset">
      <legend class="survey-label">
        <span>22.- ¿Se siente seguro al cruzar esta intersección?</span>
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

    <fieldset class="survey-field survey-radio-fieldset">
      <legend class="survey-label">
        <span>23.- ¿Hay semáforo peatonal?</span>
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

  <!-- BLOQUE D: Señalización, Accesibilidad y Entorno -->
  <div class="survey-subsection-card">
    <h3 class="survey-subsection-title">D. Señalización, Accesibilidad y Entorno Urbano</h3>

    <fieldset class="survey-field survey-radio-fieldset">
      <legend class="survey-label">
        <span>24.- ¿Existen mapas peatonales, señales de destino o de caminata?</span>
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

    <fieldset class="survey-field survey-radio-fieldset">
      <legend class="survey-label">
        <span>25.- ¿Puede una persona con movilidad reducida desplazarse sin ayuda por el centro de la ciudad?</span>
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

    <fieldset class="survey-field survey-radio-fieldset">
      <legend class="survey-label">
        <span>26.- ¿Hay señalizaciones de nombres de calles visibles?</span>
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

    <fieldset class="survey-field survey-radio-fieldset">
      <legend class="survey-label">
        <span>27.- ¿La señalización es clara y sin obstáculos?</span>
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

    <fieldset class="survey-field survey-radio-fieldset">
      <legend class="survey-label">
        <span>28.- ¿El trayecto a pie hasta la parada es seguro?</span>
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

    <fieldset class="survey-field survey-radio-fieldset">
      <legend class="survey-label">
        <span>29.- ¿El aire y el ruido son aceptables para caminar?</span>
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

    <fieldset class="survey-field survey-radio-fieldset">
      <legend class="survey-label">
        <span>30.- ¿Los conductores ceden el paso a los peatones?</span>
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

    <fieldset class="survey-field survey-radio-fieldset">
      <legend class="survey-label">
        <span>31.- ¿Considera que la ciudad prioriza al peatón sobre el automóvil?</span>
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

    <fieldset class="survey-field survey-radio-fieldset">
      <legend class="survey-label">
        <span>32.- ¿Ha participado en consultas sobre espacios peatonales?</span>
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

    <fieldset class="survey-field survey-radio-fieldset">
      <legend class="survey-label">
        <span>33.- ¿Existen planes de movilidad peatonal, presupuesto o normativa de prioridad peatonal?</span>
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
    <h3 class="survey-subsection-title">E. Observaciones Finales y Declaración</h3>

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
      <label class="declaration-label">
        <input
          type="checkbox"
          :checked="modelValue.acepta_declaracion !== false"
          @change="emit('update-field', 'acepta_declaracion', ($event.target as HTMLInputElement).checked)"
        />
        <span>Declaro que la información suministrada es verídica y autorizo su tratamiento estadístico anónimo para el Plan de Desarrollo Urbano Local (PDUL) de Maturín.</span>
      </label>
    </div>
  </div>
</template>

