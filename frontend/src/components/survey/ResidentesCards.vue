<script setup lang="ts">
import { ref, nextTick } from 'vue';
import { useToast } from 'primevue/usetoast';
import type { Residente } from '@/types/survey';

const props = withDefaults(
  defineProps<{
    modelValue: Residente[];
    numeroPersonasDeclarado?: number;
  }>(),
  {
    modelValue: () => [],
    numeroPersonasDeclarado: undefined
  }
);

const emit = defineEmits<{
  (e: 'update:modelValue', residentes: Residente[]): void;
  (e: 'agregar', residente: Residente): void;
  (e: 'eliminar', index: number): void;
}>();

// Inyección segura de ToastService para notificaciones superiores sutiles
let toast: ReturnType<typeof useToast> | null = null;
try {
  toast = useToast();
} catch {
  toast = null;
}

// Referencia de la sección para auto-scroll suave
const sectionRef = ref<HTMLElement | null>(null);

const nuevoResidente = ref<Partial<Residente>>({
  persona_numero: props.modelValue.length + 1,
  nombres: '',
  nombre_apellido: '',
  parentesco: '',
  parentesco_jefe_hogar: '',
  sexo: '',
  edad: undefined,
  sabe_leer_escribir: '',
  nivel_educativo: '',
  actividad_principal: '',
  ocupacion_principal: '',
  medio_transporte_habitual: '',
  posee_licencia: '',
  tiene_vehiculo_disponible: '',
  tipo_vehiculo: '',
  cantidad_vehiculo: undefined
});

const formError = ref<string>('');

const parentescoLabels: Record<string, string> = {
  '1': 'Jefe(a) de Hogar',
  '2': 'Cónyuge / Pareja',
  '3': 'Hijo(a) / Hijastro(a)',
  '4': 'Padre / Madre',
  '5': 'Hermano(a)',
  '6': 'Nieto(a)',
  '7': 'Otro familiar',
  '8': 'No familiar',
  jefe: 'Jefe(a) del hogar',
  esposo_pareja: 'Esposo(a) / Pareja',
  hijo_hijastro: 'Hijo(a) / Hijastro(a)',
  padre_madre: 'Padre / Madre',
  hermano_hermana: 'Hermano(a)',
  nieto_nieta: 'Nieto(a)',
  otro_familiar: 'Otro familiar',
  no_familiar: 'No familiar'
};

const medioTransporteLabels: Record<string, string> = {
  '1': 'A pie',
  '2': 'Bicicleta',
  '3': 'Motocicleta',
  '4': 'Automóvil Particular',
  '5': 'Taxi',
  '6': 'Transporte público (bus, buseta)',
  '7': 'Transporte informal (por puesto, mototaxi)',
  '8': 'Otro'
};

function isBlankValue(value: unknown): boolean {
  return value === undefined || value === null || (typeof value === 'string' && value.trim().length === 0);
}

async function onAgregar() {
  formError.value = '';
  const nombreLimpio = (nuevoResidente.value.nombres || nuevoResidente.value.nombre_apellido || '').trim();

  if (!nombreLimpio) {
    formError.value = 'Por favor indique el nombre y apellido del residente.';
    return;
  }
  if (!nuevoResidente.value.parentesco) {
    formError.value = 'Por favor seleccione el parentesco con el jefe(a) de hogar.';
    return;
  }
  if (!nuevoResidente.value.sexo) {
    formError.value = 'Por favor seleccione el sexo.';
    return;
  }
  if (
    nuevoResidente.value.edad === undefined ||
    nuevoResidente.value.edad === null ||
    String(nuevoResidente.value.edad).trim() === ''
  ) {
    formError.value = 'Por favor indique la edad en años cumplidos.';
    return;
  }
  const edad = Number(nuevoResidente.value.edad);
  if (isNaN(edad) || edad < 0 || edad > 120) {
    formError.value = 'Por favor indique una edad válida (0 a 120 años).';
    return;
  }
  if (!nuevoResidente.value.sabe_leer_escribir) {
    formError.value = 'Por favor indique si sabe leer y escribir.';
    return;
  }
  if (!nuevoResidente.value.nivel_educativo) {
    formError.value = 'Por favor seleccione el nivel educativo alcanzado.';
    return;
  }
  if (!nuevoResidente.value.actividad_principal && !nuevoResidente.value.ocupacion_principal) {
    formError.value = 'Por favor seleccione la ocupación o actividad principal.';
    return;
  }
  if (!nuevoResidente.value.medio_transporte_habitual) {
    formError.value = 'Por favor seleccione el medio de transporte habitual.';
    return;
  }
  if (!nuevoResidente.value.posee_licencia) {
    formError.value = 'Por favor indique si posee licencia de conducir.';
    return;
  }
  if (!nuevoResidente.value.tiene_vehiculo_disponible) {
    formError.value = 'Por favor indique si tiene algún vehículo disponible.';
    return;
  }
  if (nuevoResidente.value.tiene_vehiculo_disponible === 'si') {
    if (!nuevoResidente.value.tipo_vehiculo) {
      formError.value = 'Por favor seleccione el tipo de vehículo.';
      return;
    }
    if (isBlankValue(nuevoResidente.value.cantidad_vehiculo) || Number(nuevoResidente.value.cantidad_vehiculo) < 1) {
      formError.value = 'Por favor indique la cantidad de vehículos.';
      return;
    }
  }

  const ocupacionLimpia = String(nuevoResidente.value.actividad_principal || nuevoResidente.value.ocupacion_principal || '');

  const residente: Residente = {
    persona_numero: props.modelValue.length + 1,
    nombres: nombreLimpio,
    nombre_apellido: nombreLimpio,
    parentesco: String(nuevoResidente.value.parentesco),
    parentesco_jefe_hogar: String(nuevoResidente.value.parentesco),
    sexo: String(nuevoResidente.value.sexo),
    edad,
    sabe_leer_escribir: String(nuevoResidente.value.sabe_leer_escribir),
    nivel_educativo: String(nuevoResidente.value.nivel_educativo),
    actividad_principal: ocupacionLimpia,
    ocupacion_principal: ocupacionLimpia,
    medio_transporte_habitual: String(nuevoResidente.value.medio_transporte_habitual),
    posee_licencia: String(nuevoResidente.value.posee_licencia),
    tiene_vehiculo_disponible: String(nuevoResidente.value.tiene_vehiculo_disponible),
    tipo_vehiculo: nuevoResidente.value.tiene_vehiculo_disponible === 'si' ? String(nuevoResidente.value.tipo_vehiculo) : undefined,
    cantidad_vehiculo: nuevoResidente.value.tiene_vehiculo_disponible === 'si' ? Number(nuevoResidente.value.cantidad_vehiculo) : undefined
  };

  const actualizados = [...props.modelValue, residente];
  emit('agregar', residente);
  emit('update:modelValue', actualizados);

  // R2: Notificación Toast sutil superior
  try {
    if (toast && typeof toast.add === 'function') {
      toast.add({
        severity: 'success',
        summary: 'Miembro del Hogar Registrado',
        detail: `${residente.nombres} ha sido agregado correctamente.`,
        life: 3000
      });
    }
  } catch {
    // Silencioso en entornos headless
  }

  // R3: Desplazamiento automático al inicio de la sección de residentes
  await nextTick();
  if (sectionRef.value && typeof sectionRef.value.scrollIntoView === 'function') {
    sectionRef.value.scrollIntoView({ behavior: 'smooth', block: 'start' });
  } else if (typeof window !== 'undefined' && typeof window.scrollTo === 'function') {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // R5: Reset en blanco sin valores preestablecidos para el siguiente residente
  nuevoResidente.value = {
    persona_numero: actualizados.length + 1,
    nombres: '',
    nombre_apellido: '',
    parentesco: '',
    parentesco_jefe_hogar: '',
    sexo: '',
    edad: undefined,
    sabe_leer_escribir: '',
    nivel_educativo: '',
    actividad_principal: '',
    ocupacion_principal: '',
    medio_transporte_habitual: '',
    posee_licencia: '',
    tiene_vehiculo_disponible: '',
    tipo_vehiculo: '',
    cantidad_vehiculo: undefined
  };
}

function onEliminar(index: number) {
  emit('eliminar', index);
  const actualizados = props.modelValue.filter((_, idx) => idx !== index).map((r, i) => ({
    ...r,
    persona_numero: i + 1
  }));
  emit('update:modelValue', actualizados);
}
</script>

<template>
  <div ref="sectionRef" class="residentes-section" aria-labelledby="titulo-residentes">
    <div class="residentes-header">
      <h3 id="titulo-residentes" class="residentes-title">
        Composición del Hogar y Residentes Habituales ({{ modelValue.length }}{{ numeroPersonasDeclarado ? ` de ${numeroPersonasDeclarado}` : '' }})
      </h3>
      <p class="residentes-desc">
        Registre a las personas que duermen habitualmente en la vivienda y comparten el gasto de alimentación.
      </p>
      <div
        v-if="numeroPersonasDeclarado && modelValue.length < numeroPersonasDeclarado"
        class="residentes-quota-alert"
        role="status"
      >
        <i class="pi pi-info-circle" aria-hidden="true"></i>
        <span>Faltan {{ numeroPersonasDeclarado - modelValue.length }} integrante(s) por registrar para completar los {{ numeroPersonasDeclarado }} declarados en la Sección III.</span>
      </div>
      <div
        v-else-if="numeroPersonasDeclarado && modelValue.length >= numeroPersonasDeclarado"
        class="residentes-quota-success"
        role="status"
      >
        <i class="pi pi-check-circle" aria-hidden="true"></i>
        <span>Se han registrado los {{ numeroPersonasDeclarado }} integrantes del hogar.</span>
      </div>
    </div>

    <!-- Lista de tarjetas resumidas de residentes -->
    <div v-if="modelValue.length > 0" class="residentes-list" role="list">
      <article
        v-for="(r, idx) in modelValue"
        :key="r.persona_numero"
        class="residente-card"
        role="listitem"
      >
        <div class="residente-avatar" aria-hidden="true">
          <i class="pi pi-user"></i>
        </div>

        <div class="residente-info">
          <div class="residente-headline">
            <strong class="residente-name">{{ r.nombres || r.nombre_apellido || `Persona #${idx + 1}` }}</strong>
            <span class="persona-number">#{{ idx + 1 }}</span>
          </div>
          <p class="residente-meta">
            {{ parentescoLabels[r.parentesco] || 'Miembro' }} • {{ r.edad }} años • {{ r.sexo === '1' ? 'Hombre' : 'Mujer' }}
          </p>
          <p v-if="r.ocupacion_principal || r.actividad_principal" class="residente-meta">
            Ocupación: {{ r.ocupacion_principal || r.actividad_principal }}
            <span v-if="r.medio_transporte_habitual && medioTransporteLabels[r.medio_transporte_habitual]"> • Transporte: {{ medioTransporteLabels[r.medio_transporte_habitual] }}</span>
          </p>
        </div>

        <div class="residente-actions">
          <button
            type="button"
            class="residente-btn-delete"
            :aria-label="`Eliminar residente ${idx + 1}: ${r.nombres || 'Persona ' + (idx + 1)}`"
            @click="onEliminar(idx)"
          >
            <i class="pi pi-trash" aria-hidden="true"></i>
            <span class="visually-hidden">Eliminar</span>
          </button>
        </div>
      </article>
    </div>

    <div v-else class="empty-state">
      <i class="pi pi-users empty-icon" aria-hidden="true"></i>
      <p>No se han registrado residentes aún. Agregue al menos al Jefe(a) de hogar.</p>
    </div>

    <!-- Formulario para agregar residente -->
    <fieldset class="nuevo-residente-form">
      <legend class="nuevo-residente-legend">
        <i class="pi pi-user-plus" aria-hidden="true"></i>
        <span>Agregar Miembro del Hogar</span>
      </legend>

      <div v-if="formError" class="form-error-banner" role="alert">
        <i class="pi pi-exclamation-triangle" aria-hidden="true"></i>
        <span>{{ formError }}</span>
      </div>

      <div class="grid-inputs">
        <div class="survey-field">
          <label class="survey-label" for="residente-nombre">
            Nombre Apellido:
          </label>
          <input
            id="residente-nombre"
            v-model="nuevoResidente.nombres"
            type="text"
            class="survey-input"
            placeholder="Ej: María P. (o Jefe de Hogar)"
          />
        </div>

        <div class="survey-field">
          <label class="survey-label" for="residente-parentesco">
            Parentesco con el jefe del hogar:
          </label>
          <select id="residente-parentesco" v-model="nuevoResidente.parentesco" class="survey-select">
            <option value="" disabled selected>-- Seleccione el parentesco con el jefe(a) --</option>
            <option value="1">Jefe(a) de Hogar</option>
            <option value="2">Cónyuge / Pareja</option>
            <option value="3">Hijo(a) / Hijastro(a)</option>
            <option value="4">Padre / Madre</option>
            <option value="5">Hermano(a)</option>
            <option value="6">Nieto(a)</option>
            <option value="7">Otro familiar</option>
            <option value="8">No familiar</option>
          </select>
        </div>

        <div class="survey-field">
          <label class="survey-label" for="residente-sexo">
            Sexo (1=Hombre, 2=Mujer):
          </label>
          <select id="residente-sexo" v-model="nuevoResidente.sexo" class="survey-select">
            <option value="" disabled selected>-- Seleccione el sexo --</option>
            <option value="1">Hombre</option>
            <option value="2">Mujer</option>
          </select>
        </div>

        <div class="survey-field">
          <label class="survey-label" for="residente-edad">
            Edad:
          </label>
          <input
            id="residente-edad"
            v-model.number="nuevoResidente.edad"
            type="number"
            min="0"
            max="120"
            class="survey-input"
            placeholder="Ej: 35 (edad en años cumplidos)"
          />
        </div>

        <div class="survey-field">
          <label class="survey-label" for="residente-sabe-leer">
            ¿Sabe leer y escribir?:
          </label>
          <select id="residente-sabe-leer" v-model="nuevoResidente.sabe_leer_escribir" class="survey-select">
            <option value="" disabled selected>-- Seleccione si sabe leer y escribir --</option>
            <option value="si">Sí</option>
            <option value="no">No</option>
          </select>
        </div>

        <div class="survey-field">
          <label class="survey-label" for="residente-nivel-educativo">
            Nivel Educativo alcanzado:
          </label>
          <select id="residente-nivel-educativo" v-model="nuevoResidente.nivel_educativo" class="survey-select">
            <option value="" disabled selected>-- Seleccione el nivel educativo --</option>
            <option value="ninguno">Ninguno</option>
            <option value="primaria">Primaria</option>
            <option value="secundaria">Secundaria</option>
            <option value="tecnico">Técnico</option>
            <option value="universitario">Universitario</option>
            <option value="postgrado">Postgrado / Maestría</option>
            <option value="doctorado">Doctorado</option>
          </select>
        </div>

        <div class="survey-field">
          <label class="survey-label" for="residente-actividad">
            Ocupación principal:
          </label>
          <select id="residente-actividad" v-model="nuevoResidente.actividad_principal" class="survey-select">
            <option value="" disabled selected>-- Seleccione la ocupación o actividad --</option>
            <option value="1">Trabaja</option>
            <option value="2">Estudia</option>
            <option value="3">Oficios del hogar</option>
            <option value="4">Jubilado / Pensionado</option>
            <option value="5">Busca trabajo</option>
            <option value="6">Otro</option>
          </select>
        </div>

        <div class="survey-field">
          <label class="survey-label" for="residente-medio-transporte">
            ¿Cuál es el medio de transporte que utiliza normalmente para trasladarse?:
          </label>
          <select id="residente-medio-transporte" v-model="nuevoResidente.medio_transporte_habitual" class="survey-select">
            <option value="" disabled selected>-- Seleccione el medio de transporte --</option>
            <option value="1">A pie</option>
            <option value="2">Bicicleta</option>
            <option value="3">Motocicleta</option>
            <option value="4">Automóvil Particular</option>
            <option value="5">Taxi</option>
            <option value="6">Transporte público (bus, buseta)</option>
            <option value="7">Transporte informal (por puesto, mototaxi)</option>
            <option value="8">Otro</option>
          </select>
        </div>

        <div class="survey-field">
          <label class="survey-label" for="residente-licencia">
            ¿Posee licencia de conducir?:
          </label>
          <select id="residente-licencia" v-model="nuevoResidente.posee_licencia" class="survey-select">
            <option value="" disabled selected>-- Seleccione si posee licencia --</option>
            <option value="si">Sí</option>
            <option value="no">No</option>
          </select>
        </div>

        <div class="survey-field">
          <label class="survey-label" for="residente-vehiculo-disp">
            ¿Tiene algún vehículo disponible?:
          </label>
          <select id="residente-vehiculo-disp" v-model="nuevoResidente.tiene_vehiculo_disponible" class="survey-select">
            <option value="" disabled selected>-- Seleccione si tiene vehículo disponible --</option>
            <option value="si">Sí</option>
            <option value="no">No</option>
          </select>
        </div>

        <div v-if="nuevoResidente.tiene_vehiculo_disponible === 'si'" class="survey-field">
          <label class="survey-label" for="residente-tipo-vehiculo">
            Tipo de vehículo:
          </label>
          <select id="residente-tipo-vehiculo" v-model="nuevoResidente.tipo_vehiculo" class="survey-select">
            <option value="" disabled selected>-- Seleccione el tipo de vehículo --</option>
            <option value="automovil">Automóvil</option>
            <option value="motocicleta">Motocicleta</option>
            <option value="bicicleta">Bicicleta</option>
            <option value="camioneta_rustico">Camioneta / Rústico</option>
            <option value="camion">Camión / Carga</option>
            <option value="otro">Otro</option>
          </select>
        </div>

        <div v-if="nuevoResidente.tiene_vehiculo_disponible === 'si'" class="survey-field">
          <label class="survey-label" for="residente-cantidad-vehiculo">
            Cantidad de Vehículo:
          </label>
          <input
            id="residente-cantidad-vehiculo"
            v-model.number="nuevoResidente.cantidad_vehiculo"
            type="number"
            min="1"
            max="20"
            class="survey-input"
            placeholder="Ej: 1"
          />
        </div>
      </div>

      <button
        type="button"
        class="survey-btn survey-btn-primary add-residente-btn"
        @click="onAgregar"
      >
        <i class="pi pi-plus" aria-hidden="true"></i>
        <span>Agregar este residente</span>
      </button>
    </fieldset>
  </div>
</template>

<style scoped>
.residentes-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-16);
  width: 100%;
}

.residentes-title {
  font-size: var(--text-subheading);
  color: var(--color-midnight-ink);
  margin-block-end: var(--spacing-4);
}

.residentes-desc {
  font-size: var(--text-body-sm);
  color: var(--text-helper);
  line-height: 1.4;
}

.residentes-quota-alert {
  display: flex;
  align-items: center;
  gap: var(--spacing-8);
  margin-top: var(--spacing-8);
  padding: var(--spacing-8) var(--spacing-12);
  background-color: #fffbeb;
  border: 1px solid #fde68a;
  color: #92400e;
  border-radius: var(--radius-cards);
  font-size: var(--text-body-sm);
}

.residentes-quota-success {
  display: flex;
  align-items: center;
  gap: var(--spacing-8);
  margin-top: var(--spacing-8);
  padding: var(--spacing-8) var(--spacing-12);
  background-color: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #166534;
  border-radius: var(--radius-cards);
  font-size: var(--text-body-sm);
}

.residentes-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-8);
}

.residente-card {
  background-color: var(--surface-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-cards);
  padding: var(--spacing-12) var(--spacing-16);
  display: flex;
  align-items: center;
  gap: var(--spacing-12);
  box-shadow: var(--shadow-sm);
}

.residente-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: var(--color-lavender-wash);
  color: var(--color-royal-signal);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  flex-shrink: 0;
}

.residente-info {
  flex: 1;
}

.residente-headline {
  display: flex;
  align-items: center;
  gap: var(--spacing-8);
}

.residente-name {
  font-size: var(--text-body);
  color: var(--color-midnight-ink);
}

.persona-number {
  font-size: var(--text-caption);
  background-color: var(--color-fog-surface);
  color: var(--text-muted);
  padding: 1px 6px;
  border-radius: var(--radius-buttons);
}

.residente-meta {
  font-size: var(--text-body-sm);
  color: var(--text-helper);
}

.residente-actions {
  display: flex;
  align-items: center;
}

.residente-btn-delete {
  background: none;
  border: 1px solid transparent;
  color: var(--color-coral-lost);
  min-inline-size: var(--min-touch-target);
  min-block-size: var(--min-touch-target);
  width: var(--min-touch-target);
  height: var(--min-touch-target);
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  transition: background-color 0.15s ease;
}

.residente-btn-delete:hover {
  background-color: #fee2e2;
}

.empty-state {
  text-align: center;
  padding: var(--spacing-24);
  background-color: var(--color-fog-surface);
  border-radius: var(--radius-cards);
  color: var(--text-helper);
  font-size: var(--text-body-sm);
}

.empty-icon {
  font-size: 2rem;
  margin-block-end: var(--spacing-8);
  display: block;
}

.nuevo-residente-form {
  border: 1px solid var(--border-color);
  border-radius: var(--radius-containers);
  padding: var(--spacing-16);
  background-color: var(--surface-card);
  margin-top: var(--spacing-8);
}

.nuevo-residente-legend {
  font-weight: var(--font-weight-bold);
  font-size: var(--text-body);
  color: var(--color-midnight-ink);
  padding: 0 var(--spacing-8);
  display: flex;
  align-items: center;
  gap: var(--spacing-6);
}

.grid-inputs {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--spacing-12);
  margin-top: var(--spacing-12);
}

@media (min-width: 600px) {
  .grid-inputs {
    grid-template-columns: repeat(2, 1fr);
  }
}

.form-error-banner {
  background-color: #fef2f2;
  color: #b91c1c;
  padding: var(--spacing-8) var(--spacing-12);
  border-radius: var(--radius-cards);
  font-size: var(--text-body-sm);
  display: flex;
  align-items: center;
  gap: var(--spacing-8);
  margin-block-end: var(--spacing-12);
}

.add-residente-btn {
  width: 100%;
  margin-top: var(--spacing-12);
}
</style>
