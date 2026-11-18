<script setup lang="ts">
import {
  type ResponseDisplayData,
  TIPOS_VIVIENDA_LABELS,
  TENENCIA_VIVIENDA_LABELS,
  PARENTESCO_LABELS,
  NIVEL_EDUCATIVO_LABELS,
  ACTIVIDAD_LABELS,
  MODOS_TRANSPORTE_LABELS,
  MOTIVOS_VIAJE_LABELS,
  CALIFICACION_LABELS,
  ACUERDO_LABELS,
  DIFICULTAD_TP_LABELS,
  FRECUENCIA_LABELS,
  formatParroquia,
  humanLabel
} from '@/utils/responseFormatters';

defineProps<{
  displayData: ResponseDisplayData;
  maskPii: boolean;
}>();
</script>

<template>
  <!-- VISTA 1: FICHA INFORMATIVA EN GRID (Predeterminada para personal no técnico) -->
  <div class="grid-detail-container" data-testid="grid-detail-viewer">
    <!-- 1. Identificación y Ubicación -->
    <section class="detail-grid-card">
      <header class="detail-card-header">
        <i class="pi pi-map-marker icon-header" aria-hidden="true"></i>
        <h4 class="card-section-title">I. Identificación y Ubicación de la Residencia</h4>
      </header>
      <div class="detail-fields-grid">
        <div class="detail-field">
          <span class="field-title">Parroquia</span>
          <span class="field-content highlight-badge">{{ formatParroquia(displayData.parroquia) }}</span>
        </div>
        <div class="detail-field">
          <span class="field-title">Comunidad / Sector</span>
          <span class="field-content">{{ displayData.comunidad_sector || 'No especificado' }}</span>
        </div>
        <div class="detail-field">
          <span class="field-title">Zona O-D Residencia</span>
          <span class="field-content">{{ displayData.zona_residencia_od || 'No especificada' }}</span>
        </div>
        <div class="detail-field">
          <span class="field-title">Avenida / Calle</span>
          <span class="field-content" :class="{ 'is-masked': maskPii && displayData.avenida_calle === '[PROTEGIDO / PII]' }">
            {{ displayData.avenida_calle || '—' }}
          </span>
        </div>
        <div class="detail-field">
          <span class="field-title">Casa / Apartamento</span>
          <span class="field-content" :class="{ 'is-masked': maskPii && displayData.casa_apartamento === '[PROTEGIDO / PII]' }">
            {{ displayData.casa_apartamento || '—' }}
          </span>
        </div>
        <div class="detail-field">
          <span class="field-title">Cédula de Identidad</span>
          <span class="field-content" :class="{ 'is-masked': maskPii && displayData.cedula === '[PROTEGIDO / PII]' }">
            {{ displayData.cedula || 'No requerida / Anónimo' }}
          </span>
        </div>
      </div>
    </section>

    <!-- 2. Vivienda y Condiciones del Hogar -->
    <section class="detail-grid-card">
      <header class="detail-card-header">
        <i class="pi pi-home icon-header" aria-hidden="true"></i>
        <h4 class="card-section-title">II. Vivienda y Condiciones del Hogar</h4>
      </header>
      <div class="detail-fields-grid">
        <div class="detail-field">
          <span class="field-title">Tipo de Vivienda</span>
          <span class="field-content font-bold">{{ humanLabel(TIPOS_VIVIENDA_LABELS, displayData.tipo_vivienda) }}</span>
        </div>
        <div class="detail-field">
          <span class="field-title">Régimen de Tenencia</span>
          <span class="field-content">{{ humanLabel(TENENCIA_VIVIENDA_LABELS, displayData.tenencia_vivienda) }}</span>
        </div>
        <div class="detail-field">
          <span class="field-title">Total Cuartos de la Vivienda</span>
          <span class="field-content">{{ displayData.total_cuartos_vivienda ?? '—' }}</span>
        </div>
        <div class="detail-field">
          <span class="field-title">Cuartos para Dormir</span>
          <span class="field-content">{{ displayData.cuartos_dormir_hogar ?? '—' }}</span>
        </div>
        <div class="detail-field">
          <span class="field-title">Integrantes del Hogar</span>
          <span class="field-content font-bold highlight-badge">{{ displayData.numero_personas_hogar ?? (displayData.residentes?.length || '—') }} personas</span>
        </div>
        <div class="detail-field">
          <span class="field-title">Grupos de Gastos Separados</span>
          <span class="field-content">{{ displayData.grupos_gastos_separados ?? '1' }}</span>
        </div>
      </div>
    </section>

    <!-- 3. Composición del Hogar (Residentes) -->
    <section class="detail-grid-card">
      <header class="detail-card-header">
        <i class="pi pi-users icon-header" aria-hidden="true"></i>
        <h4 class="card-section-title">III. Miembros del Hogar Registrados ({{ displayData.residentes?.length || 0 }})</h4>
      </header>

      <div v-if="displayData.residentes && displayData.residentes.length > 0" class="subgrid-cards">
        <article
          v-for="(res, rIdx) in displayData.residentes"
          :key="rIdx"
          class="subgrid-item-card"
        >
          <div class="subgrid-card-top">
            <span class="subgrid-badge">Persona #{{ res.persona_numero || rIdx + 1 }}</span>
            <strong class="subgrid-name" :class="{ 'is-masked': maskPii && (res.nombres === '[PROTEGIDO / PII]' || res.nombre_apellido === '[PROTEGIDO / PII]') }">
              {{ res.nombres || res.nombre_apellido || `Integrante #${rIdx + 1}` }}
            </strong>
          </div>
          <div class="subgrid-details">
            <div><strong>Parentesco:</strong> {{ humanLabel(PARENTESCO_LABELS, res.parentesco) }}</div>
            <div><strong>Sexo / Edad:</strong> {{ res.sexo === '1' ? 'Hombre' : res.sexo === '2' ? 'Mujer' : (res.sexo || '—') }} • {{ res.edad }} años</div>
            <div><strong>Educación:</strong> {{ humanLabel(NIVEL_EDUCATIVO_LABELS, res.nivel_educativo) }}</div>
            <div><strong>Actividad:</strong> {{ humanLabel(ACTIVIDAD_LABELS, res.actividad_principal || res.ocupacion_principal) }}</div>
            <div v-if="res.medio_transporte_habitual">
              <strong>Transporte habitual:</strong> {{ humanLabel(MODOS_TRANSPORTE_LABELS, res.medio_transporte_habitual) }}
            </div>
          </div>
        </article>
      </div>
      <p v-else class="empty-subtext">No se registraron integrantes adicionales.</p>
    </section>

    <!-- 4. Registro de Viajes Cotidianos -->
    <section class="detail-grid-card">
      <header class="detail-card-header">
        <i class="pi pi-send icon-header" aria-hidden="true"></i>
        <h4 class="card-section-title">IV. Registro de Viajes Realizados ({{ displayData.viajes?.length || 0 }})</h4>
      </header>

      <div v-if="displayData.viajes && displayData.viajes.length > 0" class="subgrid-cards">
        <article
          v-for="(v, vIdx) in displayData.viajes"
          :key="vIdx"
          class="subgrid-item-card trip-subgrid-card"
        >
          <div class="subgrid-card-top">
            <span class="subgrid-badge trip-badge">Viaje #{{ v.viaje_numero || vIdx + 1 }}</span>
            <span class="trip-mode-tag">{{ humanLabel(MODOS_TRANSPORTE_LABELS, v.modo_principal) }}</span>
          </div>

          <div class="trip-od-route">
            <div class="od-step">
              <i class="pi pi-circle-fill od-origin-dot" aria-hidden="true"></i>
              <span><strong>Origen:</strong> {{ formatParroquia(v.zona_od_origen) }}</span>
            </div>
            <div class="od-arrow" aria-hidden="true"><i class="pi pi-arrow-down"></i></div>
            <div class="od-step">
              <i class="pi pi-map-marker od-dest-dot" aria-hidden="true"></i>
              <span><strong>Destino:</strong> {{ formatParroquia(v.zona_od_destino) }}</span>
            </div>
          </div>

          <div class="subgrid-details trip-meta-grid">
            <div><strong>Motivo:</strong> {{ humanLabel(MOTIVOS_VIAJE_LABELS, v.motivo_viaje || v.proposito_viaje) }}</div>
            <div><strong>Horario:</strong> {{ v.hora_salida || '—' }} ➔ {{ v.hora_llegada || '—' }}</div>
            <div><strong>Duración:</strong> {{ v.tiempo_viaje_min ? `${v.tiempo_viaje_min} min` : '—' }}</div>
            <div><strong>Costo:</strong> {{ v.costo_viaje_bs !== undefined && v.costo_viaje_bs !== null ? `Bs. ${v.costo_viaje_bs}` : 'Gratis / N/A' }}</div>
          </div>
        </article>
      </div>
      <p v-else class="empty-subtext">No se registraron viajes para este hogar el día anterior.</p>
    </section>

    <!-- 5. Transporte Público -->
    <section class="detail-grid-card">
      <header class="detail-card-header">
        <i class="pi pi-car icon-header" aria-hidden="true"></i>
        <h4 class="card-section-title">V. Características de Transporte Público</h4>
      </header>
      <div class="detail-fields-grid">
        <div class="detail-field">
          <span class="field-title">Calificación del Servicio</span>
          <span class="field-content font-bold">{{ humanLabel(CALIFICACION_LABELS, displayData.calificacion_servicio_tp) }}</span>
        </div>
        <div class="detail-field">
          <span class="field-title">Dificultad Principal</span>
          <span class="field-content">{{ humanLabel(DIFICULTAD_TP_LABELS, displayData.principal_dificultad_tp || displayData.dificultades_acceso_tp) }}</span>
        </div>
        <div class="detail-field">
          <span class="field-title">Tiempo de Espera en Parada</span>
          <span class="field-content">{{ displayData.tiempo_espera_paradas_min !== undefined ? `${displayData.tiempo_espera_paradas_min} min` : '—' }}</span>
        </div>
        <div class="detail-field">
          <span class="field-title">Distancia a la Parada</span>
          <span class="field-content">{{ displayData.km_residencia_parada !== undefined ? `${displayData.km_residencia_parada} km` : '—' }}</span>
        </div>
        <div class="detail-field">
          <span class="field-title">Rutas Utilizadas al Día</span>
          <span class="field-content">{{ displayData.rutas_tp_dia ?? '0' }}</span>
        </div>
        <div class="detail-field">
          <span class="field-title">Gasto Semanal Familiar</span>
          <span class="field-content font-bold highlight-badge">{{ displayData.gasto_semanal_transporte_bs !== undefined ? `Bs. ${displayData.gasto_semanal_transporte_bs}` : '—' }}</span>
        </div>
        <div class="detail-field full-width">
          <span class="field-title">¿De acuerdo con Rutas Directas?</span>
          <span class="field-content">{{ humanLabel(ACUERDO_LABELS, displayData.acuerdo_rutas_directas) }}</span>
        </div>
      </div>
    </section>

    <!-- 6. Movilidad Activa y Percepción Urbana -->
    <section class="detail-grid-card">
      <header class="detail-card-header">
        <i class="pi pi-compass icon-header" aria-hidden="true"></i>
        <h4 class="card-section-title">VI. Movilidad Activa, Esparcimiento y Urbanismo</h4>
      </header>
      <div class="detail-fields-grid">
        <div class="detail-field">
          <span class="field-title">Seguridad al Desplazarse en el Centro</span>
          <span class="field-content">{{ humanLabel(CALIFICACION_LABELS, displayData.seguridad_centro || displayData.seguridad_desplazamiento_centro) }}</span>
        </div>
        <div class="detail-field">
          <span class="field-title">Aceras Cómodas / Adecuadas</span>
          <span class="field-content">{{ humanLabel(ACUERDO_LABELS, displayData.acuerdo_acera_comoda || displayData.aceras_adecuadas) }}</span>
        </div>
        <div class="detail-field">
          <span class="field-title">Días que Camina / Usa Bicicleta</span>
          <span class="field-content">{{ displayData.dias_camina_bici_semana !== undefined ? `${displayData.dias_camina_bici_semana} días/semana` : '—' }}</span>
        </div>
        <div class="detail-field">
          <span class="field-title">Frecuencia Visita Parques / Plazas</span>
          <span class="field-content">{{ humanLabel(FRECUENCIA_LABELS, displayData.frecuencia_visita_parques) }}</span>
        </div>
        <div class="detail-field">
          <span class="field-title">Limpieza y Conservación</span>
          <span class="field-content">{{ humanLabel(CALIFICACION_LABELS, displayData.limpieza_parques || displayData.calificacion_limpieza_parques) }}</span>
        </div>
        <div class="detail-field">
          <span class="field-title">Disposición a Participar</span>
          <span class="field-content font-bold">{{ displayData.disposicion_participar === 'si' || displayData.disposicion_participar_mejoras === 'si' ? 'Sí' : (displayData.disposicion_participar || displayData.disposicion_participar_mejoras || '—') }}</span>
        </div>
        <div v-if="displayData.observaciones_generales" class="detail-field full-width">
          <span class="field-title">Observaciones / Propuestas del Ciudadano</span>
          <p class="field-observations">{{ displayData.observaciones_generales }}</p>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
/* Estilos de la Ficha Modal estilo Grid */
.grid-detail-container {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-16);
}

.detail-grid-card {
  background-color: #ffffff;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-cards);
  padding: var(--spacing-16);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-12);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.detail-card-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-8);
  border-bottom: 1px solid var(--border-color);
  padding-bottom: var(--spacing-8);
}

.detail-card-header .card-section-title {
  margin: 0;
  font-size: var(--text-body-sm);
  font-weight: var(--font-weight-bold);
  color: var(--color-midnight-ink);
}

.detail-card-header .icon-header {
  color: var(--color-royal-signal);
  font-size: 1.1rem;
}

.detail-fields-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-12);
}

.detail-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  background-color: var(--surface-subtle);
  padding: var(--spacing-8) var(--spacing-12);
  border-radius: var(--radius-inputs);
  border: 1px solid rgba(0, 0, 0, 0.03);
}

.detail-field.full-width {
  grid-column: 1 / -1;
}

.field-title {
  font-size: var(--text-caption);
  font-weight: var(--font-weight-semibold);
  color: var(--text-muted);
}

.field-content {
  font-size: var(--text-body-sm);
  color: var(--color-midnight-ink);
  word-break: break-word;
}

.field-content.font-bold {
  font-weight: var(--font-weight-bold);
}

.field-content.highlight-badge {
  color: var(--color-royal-signal);
  font-weight: var(--font-weight-bold);
}

.field-content.is-masked {
  color: #b45309;
  font-style: italic;
  font-family: var(--font-roboto-mono);
}

.subgrid-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--spacing-12);
}

.subgrid-item-card {
  background-color: var(--surface-subtle);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-cards);
  padding: var(--spacing-12);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-8);
}

.subgrid-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-8);
}

.subgrid-badge {
  background-color: var(--color-royal-signal);
  color: #ffffff;
  padding: 2px 8px;
  border-radius: var(--radius-pills);
  font-size: var(--text-caption);
  font-weight: var(--font-weight-bold);
}

.subgrid-name {
  font-size: var(--text-body-sm);
  color: var(--color-midnight-ink);
}

.subgrid-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: var(--text-caption);
  color: var(--text-body-color);
}

.trip-subgrid-card {
  border-left: 3px solid var(--color-royal-signal);
}

.trip-badge {
  background-color: var(--color-lavender-wash);
  color: var(--color-royal-signal);
  border: 1px solid var(--color-royal-signal);
}

.trip-mode-tag {
  font-size: var(--text-caption);
  font-weight: var(--font-weight-bold);
  color: var(--color-royal-signal);
}

.trip-od-route {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: var(--text-caption);
  background-color: #ffffff;
  padding: var(--spacing-8);
  border-radius: var(--radius-inputs);
  border: 1px solid var(--border-color);
}

.od-step {
  display: flex;
  align-items: center;
  gap: 6px;
}

.od-origin-dot {
  color: #16a34a;
  font-size: 0.5rem;
}

.od-dest-dot {
  color: #dc2626;
  font-size: 0.75rem;
}

.od-arrow {
  margin-left: 2px;
  color: var(--text-muted);
  font-size: 0.65rem;
}

.trip-meta-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px;
}

.empty-subtext {
  font-size: var(--text-caption);
  color: var(--text-muted);
  font-style: italic;
  margin: 0;
}

.field-observations {
  margin: 0;
  font-size: var(--text-body-sm);
  line-height: 1.5;
  color: var(--color-midnight-ink);
}
</style>
