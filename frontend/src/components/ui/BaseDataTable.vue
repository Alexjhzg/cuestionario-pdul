<script setup lang="ts">
export interface TableColumn {
  key: string;
  label: string;
}

withDefaults(
  defineProps<{
    caption: string;
    captionId: string;
    columns: readonly TableColumn[];
    rows: readonly Record<string, any>[];
    emptyMessage?: string;
  }>(),
  {
    emptyMessage: 'No hay registros disponibles.'
  }
);
</script>

<template>
  <div
    tabindex="0"
    role="region"
    :aria-labelledby="captionId"
    class="base-table-wrapper"
  >
    <table class="base-table">
      <caption :id="captionId" class="base-table-caption">{{ caption }}</caption>
      <thead>
        <tr>
          <th v-for="col in columns" :key="col.key" scope="col">
            {{ col.label }}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="rows.length === 0">
          <td :colspan="columns.length" class="base-table-empty">
            {{ emptyMessage }}
          </td>
        </tr>
        <tr v-for="(row, idx) in rows" v-else :key="row.id ?? idx">
          <td v-for="col in columns" :key="col.key">
            <slot :name="`cell-${col.key}`" :row="row" :value="row[col.key]">
              {{ row[col.key] }}
            </slot>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.base-table-wrapper {
  overflow: auto;
  max-inline-size: 100%;
  container-type: inline-size;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-cards);
  background-color: var(--surface-card);
}

.base-table-wrapper:focus-visible {
  outline: 3px solid var(--focus-ring);
  outline-offset: 2px;
}

.base-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  font-size: var(--text-body-sm);
}

.base-table-caption {
  text-align: left;
  padding: var(--spacing-12) var(--spacing-16);
  font-weight: var(--font-weight-semibold);
  color: var(--color-midnight-ink);
}

.base-table th,
.base-table td {
  padding: var(--spacing-12) var(--spacing-16);
  border-bottom: 1px solid var(--border-color);
  text-align: left;
}

.base-table thead th {
  position: sticky;
  inset-block-start: 0;
  z-index: 1;
  background-color: var(--color-fog-surface);
  color: var(--color-midnight-ink);
  font-weight: var(--font-weight-semibold);
}

.base-table-empty {
  text-align: center;
  color: var(--text-helper);
  padding: var(--spacing-24);
}
</style>

