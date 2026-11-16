<script setup lang="ts">
defineProps<{
  visible: boolean;
  lastSavedAt?: string | null;
  step?: number;
}>();

const emit = defineEmits<{
  (e: 'restore'): void;
  (e: 'discard'): void;
}>();
</script>

<template>
  <aside
    v-if="visible"
    class="draft-banner"
    role="region"
    aria-label="Aviso de borrador guardado"
    aria-live="polite"
  >
    <div class="draft-banner-content">
      <div class="draft-banner-icon" aria-hidden="true">
        <i class="pi pi-history"></i>
      </div>
      <div class="draft-banner-text">
        <h4 class="draft-banner-title">Tienes un borrador guardado en este dispositivo</h4>
        <p class="draft-banner-desc">
          <span v-if="step !== undefined">Sección {{ step + 1 }} en progreso. </span>
          <span v-if="lastSavedAt">Último guardado: {{ lastSavedAt }}. </span>
          ¿Deseas continuar donde lo dejaste o iniciar una nueva encuesta?
        </p>
      </div>
    </div>
    <div class="draft-banner-actions">
      <button
        type="button"
        class="survey-btn survey-btn-primary draft-btn"
        @click="emit('restore')"
      >
        <i class="pi pi-check" aria-hidden="true"></i>
        <span>Continuar borrador</span>
      </button>
      <button
        type="button"
        class="survey-btn survey-btn-secondary draft-btn"
        @click="emit('discard')"
      >
        <i class="pi pi-trash" aria-hidden="true"></i>
        <span>Descartar y empezar de cero</span>
      </button>
    </div>
  </aside>
</template>

<style scoped>
.draft-banner {
  background-color: var(--color-lavender-wash);
  border: 1px solid #c7d7fe;
  border-radius: var(--radius-containers);
  padding: var(--spacing-16) var(--spacing-20);
  margin-block-end: var(--spacing-24);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-16);
  box-shadow: var(--shadow-sm);
}

@media (min-width: 640px) {
  .draft-banner {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }
}

.draft-banner-content {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-12);
}

.draft-banner-icon {
  font-size: 1.5rem;
  color: var(--color-royal-signal);
  display: flex;
  align-items: center;
  justify-content: center;
  padding-top: var(--spacing-4);
}

.draft-banner-title {
  font-size: var(--text-body);
  font-weight: var(--font-weight-bold);
  color: var(--color-midnight-ink);
  margin-block-end: var(--spacing-4);
}

.draft-banner-desc {
  font-size: var(--text-body-sm);
  color: var(--color-slate-caption);
  line-height: 1.4;
}

.draft-banner-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-8);
}

.draft-btn {
  padding: 0.5rem 1.25rem;
  font-size: var(--text-body-sm);
  min-block-size: var(--min-touch-target);
  min-inline-size: var(--min-touch-target);
}
</style>
