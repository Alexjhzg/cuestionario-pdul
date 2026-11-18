<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import comunidadesCatalogJson from '@shared/catalogs/comunidades_maturin.json';
import {
  fetchCatalogoComunidades,
  type ComunidadCatalogoItem
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
const remoteCommunities = ref<ComunidadCatalogoItem[] | null>(null);

function filterLocalByParroquia(parroquia: string): ComunidadCatalogoItem[] {
  if (!parroquia) return [];
  const p = parroquia.trim().toLowerCase();
  const targetParroquias = p === 'la_cruz' || p === 'santa_cruz' ? ['la_cruz', 'santa_cruz'] : [p];
  return localCatalog
    .filter((item) => targetParroquias.includes(item.parroquia))
    .slice()
    .sort((a, b) => a.nombre.localeCompare(b.nombre, 'es'));
}

const comunidadesFiltradas = computed<ComunidadCatalogoItem[]>(() => {
  const p = props.modelValue.parroquia || '';
  if (!p) return [];
  if (remoteCommunities.value && remoteCommunities.value.length > 0) {
    return remoteCommunities.value;
  }
  return filterLocalByParroquia(p);
});

watch(
  () => props.modelValue.parroquia,
  async (newParroquia, oldParroquia) => {
    remoteCommunities.value = null;
    if (!newParroquia) {
      return;
    }
    if (oldParroquia && oldParroquia !== newParroquia && props.modelValue.comunidad_codigo) {
      const stillValid = filterLocalByParroquia(newParroquia).some(
        (c) => c.codigo === props.modelValue.comunidad_codigo
      );
      if (!stillValid) {
        emit('update-field', 'comunidad_codigo', '');
        emit('update-field', 'comunidad_sector', '');
      }
    }
    try {
      const rows = await fetchCatalogoComunidades(newParroquia);
      if (Array.isArray(rows) && rows.length > 0) {
        remoteCommunities.value = rows;
      }
    } catch {
      // Fallback offline inmediato con catálogo local sincronizado
    }
  },
  { immediate: true }
);

function onParroquiaChange(event: Event) {
  const value = (event.target as HTMLSelectElement).value;
  emit('update-field', 'parroquia', value);
}

function onCascadeComunidadSelect(event: Event) {
  const codigo = (event.target as HTMLSelectElement).value;
  if (!codigo) {
    emit('update-field', 'comunidad_codigo', '');
    return;
  }
  const found = comunidadesFiltradas.value.find((c) => c.codigo === codigo);
  emit('update-field', 'comunidad_codigo', codigo);
  if (found) {
    emit('update-field', 'comunidad_sector', found.nombre);
  }
}

function onComunidadTextInput(event: Event) {
  const text = (event.target as HTMLInputElement).value;
  emit('update-field', 'comunidad_sector', text);
  const match = comunidadesFiltradas.value.find(
    (c) => c.nombre.toLowerCase() === text.trim().toLowerCase()
  );
  emit('update-field', 'comunidad_codigo', match ? match.codigo : '');
}
</script>

<template>
  <div class="survey-field">
    <label for="parroquia" class="survey-label">
      1.- Parroquia:
      <span class="required-indicator" aria-hidden="true">*</span>
    </label>
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
    <label for="comunidad_sector" class="survey-label">2.- Comunidad/Sector:</label>
    <select
      v-if="modelValue.parroquia && comunidadesFiltradas.length > 0"
      id="comunidad_catalogo_select"
      :value="modelValue.comunidad_codigo || ''"
      class="survey-select"
      style="margin-block-end: 0.5rem;"
      aria-label="Seleccionar comunidad del diccionario oficial filtrado por parroquia"
      data-testid="select-comunidad-cascada"
      @change="onCascadeComunidadSelect"
    >
      <option value="">
        -- Seleccione del diccionario ({{ comunidadesFiltradas.length }} comunidades en {{ formatParroquia(modelValue.parroquia) }}) o escriba abajo --
      </option>
      <option
        v-for="com in comunidadesFiltradas"
        :key="com.codigo"
        :value="com.codigo"
      >
        {{ com.nombre }} ({{ com.codigo }})
      </option>
    </select>
    <input
      id="comunidad_sector"
      :value="modelValue.comunidad_sector || ''"
      type="text"
      list="comunidades-parroquia-datalist"
      class="survey-input"
      :placeholder="
        modelValue.parroquia
          ? 'Seleccione arriba o escriba el nombre de su comunidad o sector'
          : 'Seleccione primero una parroquia o escriba su comunidad/sector'
      "
      @input="onComunidadTextInput"
    />
    <datalist id="comunidades-parroquia-datalist">
      <option
        v-for="com in comunidadesFiltradas"
        :key="`dl-${com.codigo}`"
        :value="com.nombre"
      >
        {{ com.codigo }} - {{ formatParroquia(com.parroquia) }}
      </option>
    </datalist>
  </div>

  <div class="survey-field">
    <label for="zona_residencia_od" class="survey-label">
      3.- Zona de residencia (según zonificación O-D):
    </label>
    <input
      id="zona_residencia_od"
      :value="modelValue.zona_residencia_od || ''"
      type="text"
      class="survey-input"
      placeholder="Escriba la zona de residencia según la zonificación O-D"
      @input="emit('update-field', 'zona_residencia_od', ($event.target as HTMLInputElement).value)"
    />
  </div>

  <div class="survey-field">
    <label for="avenida_calle" class="survey-label">4.- Avenida/Calle:</label>
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
    <label for="casa_apartamento" class="survey-label">5.- Casa/Apartamento:</label>
    <input
      id="casa_apartamento"
      :value="modelValue.casa_apartamento || ''"
      type="text"
      class="survey-input"
      placeholder="Escriba el número o nombre de la casa o apartamento"
      @input="emit('update-field', 'casa_apartamento', ($event.target as HTMLInputElement).value)"
    />
  </div>
</template>
