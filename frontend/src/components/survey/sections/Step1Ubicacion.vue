<script setup lang="ts">
import { PARROQUIAS_MATURIN, formatParroquia } from '@/utils/validation';

defineProps<{
  modelValue: Record<string, any>;
}>();

const emit = defineEmits<{
  (e: 'update-field', field: string, value: any): void;
  (e: 'mark-touched', field: string): void;
}>();
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
      @change="emit('update-field', 'parroquia', ($event.target as HTMLSelectElement).value)"
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
    <input
      id="comunidad_sector"
      :value="modelValue.comunidad_sector || ''"
      type="text"
      class="survey-input"
      placeholder="Escriba el nombre de su comunidad o sector"
      @input="emit('update-field', 'comunidad_sector', ($event.target as HTMLInputElement).value)"
    />
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

