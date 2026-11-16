<script setup lang="ts">
withDefaults(
  defineProps<{
    title?: string;
    as?: 'section' | 'article' | 'div';
  }>(),
  {
    title: undefined,
    as: 'section'
  }
);
</script>

<template>
  <component :is="as" class="survey-card base-card">
    <header v-if="title || $slots.header" class="base-card-header">
      <slot name="header">
        <h3 class="base-card-title">{{ title }}</h3>
      </slot>
    </header>
    <slot />
  </component>
</template>

<style scoped>
.base-card-header {
  margin-block-end: var(--spacing-12);
}

.base-card-title {
  margin: 0;
  font-size: var(--text-heading-sm);
  color: var(--color-midnight-ink);
}
</style>

