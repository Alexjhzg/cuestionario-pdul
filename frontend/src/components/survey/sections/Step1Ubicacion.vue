<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import QuestionHelpTip from '@/components/common/QuestionHelpTip.vue';
import GpsLocationCapture, { type GpsPayload } from '@/components/common/GpsLocationCapture.vue';
import { QUESTION_HELP_TIPS } from '@/utils/questionHelpCatalog';
import comunidadesCatalogJson from '@shared/catalogs/comunidades_maturin.json';
import zonasOdCatalogJson from '@shared/catalogs/zonas_od_maturin.json';
import {
  fetchCatalogoComunidades,
  fetchCatalogoZonasOd,
  type ComunidadCatalogoItem,
  type ZonaOdCatalogoItem
} from '@/services/api';
import { PARROQUIAS_MATURIN, formatParroquia } from '@/utils/validation';

const props = defineProps<{
  modelValue: Record<string, any>;
}>();

const emit = defineEmits<{
  (e: 'update-field', field: string, value: any): void;
  (e: 'mark-touched', field: string): void;
}>();

const localCatalog = comunidadesCatalogJson as ComunidadCatalogoItem[];
const localZonasCatalog = zonasOdCatalogJson as ZonaOdCatalogoItem[];

const remoteCommunities = ref<ComunidadCatalogoItem[] | null>(null);
const remoteZonas = ref<ZonaOdCatalogoItem[] | null>(null);
const isOtherComunidad = ref<boolean>(false);

function filterLocalByParroquia(parroquia: string): ComunidadCatalogoItem[] {
  if (!parroquia) return [];
  const p = parroquia.trim().toLowerCase();
  const targetParroquias = p === 'la_cruz' || p === 'santa_cruz' ? ['la_cruz', 'santa_cruz'] : [p];
  return localCatalog
    .filter((item) => targetParroquias.includes(item.parroquia))
    .slice()
    .sort((a, b) => a.nombre.localeCompare(b.nombre, 'es'));
}

function filterLocalZonasByParroquia(parroquia: string): ZonaOdCatalogoItem[] {
  if (!parroquia) return [];
  const p = parroquia.trim().toLowerCase();
  return localZonasCatalog.filter((item) => item.parroquia === p);
}

const comunidadesFiltradas = computed<ComunidadCatalogoItem[]>(() => {
  const p = props.modelValue.parroquia || '';
  if (!p) return [];
  if (remoteCommunities.value && remoteCommunities.value.length > 0) {
    return remoteCommunities.value;
  }
  return filterLocalByParroquia(p);
});

const selectedComunidadObj = computed<ComunidadCatalogoItem | undefined>(() => {
  const code = String(props.modelValue.comunidad_codigo || '').trim();
  const name = String(props.modelValue.comunidad_sector || '').trim();
  if (code) {
    const byCode = comunidadesFiltradas.value.find((c) => c.codigo === code);
    if (byCode) return byCode;
  }
  if (name) {
    return comunidadesFiltradas.value.find(
      (c) => c.nombre.toLowerCase() === name.toLowerCase()
    );
  }
  return undefined;
});

const zonasFiltradas = computed<ZonaOdCatalogoItem[]>(() => {
  const p = props.modelValue.parroquia || '';
  if (!p) return [];
  const baseZonas =
    remoteZonas.value && remoteZonas.value.length > 0
      ? remoteZonas.value
      : filterLocalZonasByParroquia(p);

  const selectedXpar = selectedComunidadObj.value?.xpar;
  if (selectedXpar) {
    const byXpar = baseZonas.filter((z) => z.xpar === selectedXpar);
    if (byXpar.length > 0) {
      return byXpar;
    }
  }
  return baseZonas;
});

const legacyComunidadOption = computed<string>(() => {
  if (isOtherComunidad.value) return '';
  const current = String(props.modelValue.comunidad_sector || '').trim();
  if (!current) return '';
  const exists = comunidadesFiltradas.value.some(
    (c) => c.nombre.toLowerCase() === current.toLowerCase()
  );
  return exists ? '' : current;
});

const legacyZonaOption = computed<string>(() => {
  const current = String(props.modelValue.zona_residencia_od || '').trim();
  if (!current) return '';
  const exists = zonasFiltradas.value.some(
    (z) => z.codigo.toLowerCase() === current.toLowerCase()
  );
  return exists ? '' : current;
});

const selectedComunidadSelectValue = computed<string>(() => {
  if (isOtherComunidad.value) return '__otra__';
  const current = String(props.modelValue.comunidad_sector || '').trim();
  if (!current) return '';
  const exact = comunidadesFiltradas.value.find(
    (c) => c.nombre.toLowerCase() === current.toLowerCase()
  );
  return exact ? exact.nombre : current;
});

watch(
  () => props.modelValue.parroquia,
  async (newParroquia, oldParroquia) => {
    remoteCommunities.value = null;
    remoteZonas.value = null;

    if (!newParroquia) {
      return;
    }

    if (oldParroquia && oldParroquia !== newParroquia) {
      const validComunidades = filterLocalByParroquia(newParroquia);
      const currentCom = String(props.modelValue.comunidad_sector || '').trim();
      if (
        currentCom &&
        !validComunidades.some((c) => c.nombre.toLowerCase() === currentCom.toLowerCase())
      ) {
        isOtherComunidad.value = false;
        emit('update-field', 'comunidad_codigo', '');
        emit('update-field', 'comunidad_sector', '');
      }

      const validZonas = filterLocalZonasByParroquia(newParroquia);
      const currentZona = String(props.modelValue.zona_residencia_od || '').trim();
      if (
        currentZona &&
        !validZonas.some((z) => z.codigo.toLowerCase() === currentZona.toLowerCase())
      ) {
        emit('update-field', 'zona_residencia_od', '');
      }
    }

    try {
      const [comRows, zonaRows] = await Promise.allSettled([
        fetchCatalogoComunidades(newParroquia),
        fetchCatalogoZonasOd(newParroquia)
      ]);
      if (comRows.status === 'fulfilled' && Array.isArray(comRows.value) && comRows.value.length > 0) {
        remoteCommunities.value = comRows.value;
      }
      if (zonaRows.status === 'fulfilled' && Array.isArray(zonaRows.value) && zonaRows.value.length > 0) {
        remoteZonas.value = zonaRows.value;
      }
    } catch {
      // Respaldo offline inmediato con catálogos locales sincronizados
    }
  },
  { immediate: true }
);

function onParroquiaChange(event: Event) {
  const value = (event.target as HTMLSelectElement).value;
  emit('update-field', 'parroquia', value);
}

function onComunidadSelectChange(event: Event) {
  const val = (event.target as HTMLSelectElement).value;
  if (val === '__otra__') {
    isOtherComunidad.value = true;
    emit('update-field', 'comunidad_codigo', '');
    emit('update-field', 'comunidad_sector', '');
    return;
  }

  isOtherComunidad.value = false;
  const found = comunidadesFiltradas.value.find((c) => c.nombre === val);
  emit('update-field', 'comunidad_sector', val);
  emit('update-field', 'comunidad_codigo', found ? found.codigo : '');

  if (found?.xpar) {
    const matchingZonas = zonasFiltradas.value.filter((z) => z.xpar === found.xpar);
    const currentZona = String(props.modelValue.zona_residencia_od || '').trim();
    if (
      matchingZonas.length > 0 &&
      currentZona &&
      !matchingZonas.some((z) => z.codigo === currentZona)
    ) {
      emit('update-field', 'zona_residencia_od', '');
    }
  }
}

function onOtherComunidadInput(event: Event) {
  emit('update-field', 'comunidad_codigo', '');
  emit('update-field', 'comunidad_sector', (event.target as HTMLInputElement).value);
}

function onZonaSelectChange(event: Event) {
  const value = (event.target as HTMLSelectElement).value;
  emit('update-field', 'zona_residencia_od', value);
}

function onUpdateGps(payload: GpsPayload) {
  emit('update-field', 'gps_latitud', payload.latitude);
  emit('update-field', 'gps_longitud', payload.longitude);
  emit('update-field', 'gps_precision', payload.accuracy);
  emit('update-field', 'gps_capturado_en', payload.capturedAt);
}
</script>

<template>
  <div class="survey-field">
    <div class="survey-label-row">
      <label for="parroquia" class="survey-label">
        1.- Parroquia:
        <span class="required-indicator" aria-hidden="true">*</span>
      </label>
      <QuestionHelpTip
        :text="QUESTION_HELP_TIPS.parroquia"
        question-label="Parroquia de residencia"
      />
    </div>
    <select
      id="parroquia"
      :value="modelValue.parroquia || ''"
      required
      class="survey-select"
      @blur="emit('mark-touched', 'parroquia')"
      @change="onParroquiaChange"
    >
      <option value="" disabled selected>Seleccione su parroquia</option>
      <option v-for="p in PARROQUIAS_MATURIN" :key="p" :value="p">
        {{ formatParroquia(p) }}
      </option>
    </select>
    <span class="survey-error-msg">
      <i class="pi pi-times-circle" aria-hidden="true"></i>
      Seleccione su parroquia.
    </span>
  </div>

  <div class="survey-field">
    <div class="survey-label-row">
      <label for="comunidad_sector" class="survey-label">
        2.- Comunidad/Sector:
        <span class="required-indicator" aria-hidden="true">*</span>
      </label>
      <QuestionHelpTip
        :text="QUESTION_HELP_TIPS.comunidad_sector"
        question-label="Comunidad o Sector"
      />
    </div>
    <select
      id="comunidad_sector"
      :value="selectedComunidadSelectValue"
      :disabled="!modelValue.parroquia"
      required
      class="survey-select"
      data-testid="select-comunidad-cascada"
      @blur="emit('mark-touched', 'comunidad_sector')"
      @change="onComunidadSelectChange"
    >
      <option value="" disabled>
        {{
          modelValue.parroquia
            ? 'Seleccione su comunidad o sector'
            : 'Seleccione primero una parroquia'
        }}
      </option>
      <option v-if="legacyComunidadOption" :value="legacyComunidadOption">
        {{ legacyComunidadOption }}
      </option>
      <option
        v-for="com in comunidadesFiltradas"
        :key="com.codigo"
        :value="com.nombre"
      >
        {{ com.nombre }}
      </option>
      <option v-if="modelValue.parroquia" value="__otra__">
        -- Otra comunidad / No aparece en la lista --
      </option>
    </select>
    <span class="survey-error-msg">
      <i class="pi pi-times-circle" aria-hidden="true"></i>
      Seleccione su comunidad o sector.
    </span>
  </div>

  <div v-if="isOtherComunidad" class="survey-field">
    <label for="comunidad_sector_otro" class="survey-label">
      Especifique su comunidad o sector:
      <span class="required-indicator" aria-hidden="true">*</span>
    </label>
    <input
      id="comunidad_sector_otro"
      :value="modelValue.comunidad_sector || ''"
      type="text"
      required
      class="survey-input"
      placeholder="Escriba el nombre de su comunidad o urbanización"
      @input="onOtherComunidadInput"
    />
  </div>

  <div class="survey-field">
    <div class="survey-label-row">
      <label for="zona_residencia_od" class="survey-label">
        3.- Zona de residencia (según zonificación O-D):
        <span class="required-indicator" aria-hidden="true">*</span>
      </label>
      <QuestionHelpTip
        :text="QUESTION_HELP_TIPS.zona_residencia_od"
        question-label="Zona de residencia según zonificación O-D"
      />
    </div>
    <select
      id="zona_residencia_od"
      :value="modelValue.zona_residencia_od || ''"
      :disabled="!modelValue.parroquia"
      required
      class="survey-select"
      data-testid="select-zona-od-cascada"
      @blur="emit('mark-touched', 'zona_residencia_od')"
      @change="onZonaSelectChange"
    >
      <option value="" disabled>
        {{
          modelValue.parroquia
            ? `Seleccione la zona o sector O-D (${zonasFiltradas.length} disponibles)`
            : 'Seleccione primero una parroquia'
        }}
      </option>
      <option v-if="legacyZonaOption" :value="legacyZonaOption">
        {{ legacyZonaOption }}
      </option>
      <option
        v-for="zona in zonasFiltradas"
        :key="zona.codigo"
        :value="zona.codigo"
      >
        {{ zona.nombre }}
      </option>
    </select>
    <span class="survey-error-msg">
      <i class="pi pi-times-circle" aria-hidden="true"></i>
      Seleccione la zona de residencia (zonificación O-D).
    </span>
  </div>

  <div class="survey-field">
    <div class="survey-label-row">
      <label for="avenida_calle" class="survey-label">4.- Avenida/Calle:</label>
      <QuestionHelpTip
        :text="QUESTION_HELP_TIPS.avenida_calle"
        question-label="Avenida o Calle"
      />
    </div>
    <input
      id="avenida_calle"
      :value="modelValue.avenida_calle || ''"
      type="text"
      class="survey-input"
      placeholder="Escriba el nombre de la avenida o calle"
      @input="emit('update-field', 'avenida_calle', ($event.target as HTMLInputElement).value)"
    />
  </div>

  <div class="survey-field">
    <div class="survey-label-row">
      <label for="casa_apartamento" class="survey-label">5.- Casa/Apartamento:</label>
      <QuestionHelpTip
        :text="QUESTION_HELP_TIPS.casa_apartamento"
        question-label="Casa o Apartamento"
      />
    </div>
    <input
      id="casa_apartamento"
      :value="modelValue.casa_apartamento || ''"
      type="text"
      class="survey-input"
      placeholder="Escriba el número o nombre de la casa o apartamento"
      @input="emit('update-field', 'casa_apartamento', ($event.target as HTMLInputElement).value)"
    />
  </div>

  <GpsLocationCapture
    :latitude="modelValue.gps_latitud ?? null"
    :longitude="modelValue.gps_longitud ?? null"
    :accuracy="modelValue.gps_precision ?? null"
    :captured-at="modelValue.gps_capturado_en ?? null"
    @update-gps="onUpdateGps"
  />
</template>
