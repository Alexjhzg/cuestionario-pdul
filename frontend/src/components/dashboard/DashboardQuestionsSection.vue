<script setup lang="ts">
import type { PreguntaMetricaItem } from '@/services/analyticsApi';
import QuestionChartCard from '@/components/dashboard/QuestionChartCard.vue';

defineProps<{
  preguntasMetricas: PreguntaMetricaItem[];
  filteredPreguntas: PreguntaMetricaItem[];
  availableSections: string[];
  selectedSectionFilter: string;
  searchQuery: string;
  isLoadingPreguntas: boolean;
}>();

const emit = defineEmits<{
  (e: 'update:selectedSectionFilter', sec: string): void;
  (e: 'update:searchQuery', q: string): void;
  (e: 'reset-filters'): void;
}>();
</script>

<template>
  <section class="section-all-questions" aria-label="Análisis gráfico pregunta por pregunta">
    <div class="questions-section-header">
      <div class="questions-title-block">
        <div class="header-badge">
          <i class="pi pi-chart-pie" aria-hidden="true"></i>
          <span>Cuestionario Completo</span>
        </div>
        <h2 class="questions-section-title">Análisis Estadístico por Cada Pregunta</h2>
        <p class="questions-section-desc">
          Gráficos individuales que representan textualmente la pregunta exacta formulada en cada una de las 8 secciones técnicas del Cuestionario PDUL Maturín.
        </p>
      </div>

      <div class="questions-filter-toolbar">
        <div class="search-input-wrapper">
          <i class="pi pi-search search-icon" aria-hidden="true"></i>
          <input
            type="text"
            :value="searchQuery"
            placeholder="Filtrar por texto de pregunta o clave..."
            class="questions-search-input"
            aria-label="Filtrar preguntas por texto"
            @input="emit('update:searchQuery', ($event.target as HTMLInputElement).value)"
          />
          <button
            v-if="searchQuery"
            type="button"
            class="btn-clear-search"
            @click="emit('update:searchQuery', '')"
            aria-label="Limpiar filtro de búsqueda"
          >
            <i class="pi pi-times" aria-hidden="true"></i>
          </button>
        </div>

        <div class="section-pills-list" role="group" aria-label="Filtrar preguntas por sección">
          <button
            type="button"
            class="section-pill-btn"
            :class="{ active: selectedSectionFilter === 'todas' }"
            @click="emit('update:selectedSectionFilter', 'todas')"
            :aria-pressed="selectedSectionFilter === 'todas'"
          >
            Todas ({{ preguntasMetricas.length }})
          </button>
          <button
            v-for="sec in availableSections"
            :key="sec"
            type="button"
            class="section-pill-btn"
            :class="{ active: selectedSectionFilter === sec }"
            @click="emit('update:selectedSectionFilter', sec)"
            :aria-pressed="selectedSectionFilter === sec"
          >
            {{ sec.split(':')[0] }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="filteredPreguntas.length > 0" class="grid-questions-cards">
      <QuestionChartCard
        v-for="item in filteredPreguntas"
        :key="item.clave"
        :item="item"
        :loading="isLoadingPreguntas"
      />
    </div>

    <div v-else-if="!isLoadingPreguntas" class="empty-questions-state">
      <i class="pi pi-search-minus empty-icon" aria-hidden="true"></i>
      <p class="empty-text">No se encontraron preguntas que coincidan con "{{ searchQuery }}".</p>
      <button
        type="button"
        class="btn-reset-filters"
        @click="emit('reset-filters')"
      >
        Restablecer filtros
      </button>
    </div>
  </section>
</template>

<style scoped>
.section-all-questions {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-20);
  margin-top: var(--spacing-16);
  padding-top: var(--spacing-24);
  border-top: 2px dashed var(--border-color);
}

.questions-section-header {
  background-color: var(--surface-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-containers);
  padding: var(--spacing-20);
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-16);
}

.questions-title-block {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-8);
}

.header-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-6);
  background-color: var(--color-lavender-wash);
  color: var(--color-royal-signal);
  font-size: var(--text-caption);
  font-weight: var(--font-weight-bold);
  padding: 4px 12px;
  border-radius: var(--radius-pills);
  width: fit-content;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.questions-section-title {
  font-size: var(--text-heading-sm);
  font-weight: var(--font-weight-bold);
  color: var(--color-midnight-ink);
  margin: 0;
}

.questions-section-desc {
  font-size: var(--text-body-sm);
  color: var(--text-muted);
  margin: 0;
  line-height: 1.5;
  max-width: 900px;
}

.questions-filter-toolbar {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-12);
  padding-top: var(--spacing-12);
  border-top: 1px solid var(--border-color);
}

.search-input-wrapper {
  position: relative;
  width: 100%;
  max-width: 600px;
}

.search-icon {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-slate-caption);
  pointer-events: none;
}

.questions-search-input {
  width: 100%;
  min-height: var(--min-touch-target);
  min-block-size: var(--min-touch-target);
  padding: var(--spacing-10) var(--spacing-36) var(--spacing-10) 40px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-inputs);
  background-color: var(--surface-card);
  font-family: var(--font-inter);
  font-size: var(--text-body-sm);
  color: var(--color-midnight-ink);
  transition: border-color var(--transition-base), box-shadow var(--transition-base);
}

.questions-search-input:focus {
  outline: none;
  border-color: var(--color-royal-signal);
  box-shadow: 0 0 0 3px rgba(20, 90, 255, 0.15);
}

.btn-clear-search {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: var(--color-slate-caption);
  cursor: pointer;
  padding: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-clear-search:hover {
  color: var(--color-midnight-ink);
}

.section-pills-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-8);
}

.section-pill-btn {
  display: inline-flex;
  align-items: center;
  min-height: 40px;
  padding: 6px 14px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-pills);
  background-color: var(--surface-card);
  color: var(--text-primary);
  font-family: var(--font-inter);
  font-size: 0.8rem;
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all var(--transition-base);
}

.section-pill-btn:hover {
  border-color: var(--color-royal-signal);
  color: var(--color-royal-signal);
}

.section-pill-btn.active {
  background-color: var(--color-royal-signal);
  border-color: var(--color-royal-signal);
  color: #ffffff;
  font-weight: var(--font-weight-bold);
}

.grid-questions-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-20);
}

.empty-questions-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-12);
  padding: var(--spacing-40) var(--spacing-20);
  background-color: var(--surface-card);
  border: 1px dashed var(--border-color);
  border-radius: var(--radius-containers);
  text-align: center;
}

.empty-icon {
  font-size: 2.5rem;
  color: var(--color-slate-caption);
}

.empty-text {
  font-size: var(--text-body);
  color: var(--text-muted);
  max-width: 500px;
  margin: 0;
}

.btn-reset-filters {
  min-height: var(--min-touch-target);
  min-block-size: var(--min-touch-target);
  padding: 0 var(--spacing-20);
  background-color: var(--color-royal-signal);
  color: #ffffff;
  border: none;
  border-radius: var(--radius-buttons);
  font-family: var(--font-inter);
  font-size: var(--text-body-sm);
  font-weight: var(--font-weight-bold);
  cursor: pointer;
}

@media (max-width: 1024px) {
  .grid-questions-cards {
    grid-template-columns: 1fr;
  }
}
</style>

