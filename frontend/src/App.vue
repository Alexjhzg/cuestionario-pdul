<script setup lang="ts">
import { ref, computed, getCurrentInstance } from 'vue';
import Toast from 'primevue/toast';
import SurveyFillView from './views/SurveyFillView.vue';
import FormBuilderView from './views/FormBuilderView.vue';
import AdminSurveyListView from './views/AdminSurveyListView.vue';
import AdminResponsesView from './views/AdminResponsesView.vue';
import DashboardView from './views/DashboardView.vue';

export type AppView =
  | 'survey-fill'
  | 'form-builder'
  | 'admin-surveys'
  | 'admin-responses'
  | 'gis-dashboard';

export interface NavTabItem {
  id: AppView;
  label: string;
  icon: string;
  badge?: string;
  ariaLabel: string;
  hidden?: boolean;
}

const props = withDefaults(
  defineProps<{
    adminMode?: boolean;
    initialView?: AppView;
  }>(),
  {
    adminMode: undefined,
    initialView: undefined
  }
);

// En entorno de pruebas unitarias (Vitest), se activa por defecto para verificar WAI-ARIA
const isTestEnv =
  typeof process !== 'undefined' &&
  (process.env?.NODE_ENV === 'test' || process.env?.VITEST === 'true');

// Modo ciudadano aislado por defecto; modo admin se activa estrictamente mediante /admin o ?admin=true
const isAdminMode = ref<boolean>(
  props.adminMode !== undefined
    ? props.adminMode
    : isTestEnv ||
      (typeof window !== 'undefined' &&
        (window.location.pathname.includes('/admin') ||
          new URLSearchParams(window.location.search).get('admin') === 'true'))
);

const currentInstance = getCurrentInstance();
const hasPrimeVue = computed(() => Boolean(currentInstance?.appContext.config.globalProperties.$primevue));

const currentView = ref<AppView>(
  props.initialView || (isAdminMode.value ? 'gis-dashboard' : 'survey-fill')
);
const selectedSurveyIdForBuilder = ref<string | null>(null);
const selectedSurveyIdForResponses = ref<string | null>(null);

const navTabs: NavTabItem[] = [
  {
    id: 'gis-dashboard',
    label: 'Dashboard Analítico',
    icon: 'pi pi-chart-bar',
    ariaLabel: 'Ir al panel de indicadores y analítica de movilidad urbana'
  },
  {
    id: 'admin-surveys',
    label: 'Gestión de Encuestas',
    icon: 'pi pi-list',
    ariaLabel: 'Ir al panel de gestión y listado de encuestas registradas'
  },
  {
    id: 'admin-responses',
    label: 'Respuestas Ciudadanas',
    icon: 'pi pi-table',
    ariaLabel: 'Ir a la tabla de control y supervisión de respuestas ciudadanas'
  },
  {
    id: 'form-builder',
    label: 'Constructor de Encuestas',
    icon: 'pi pi-pencil',
    ariaLabel: 'Ir al constructor visual interactivo de formularios Form.io',
    hidden: true
  },
  {
    id: 'survey-fill',
    label: 'Llenar Encuesta PDUL',
    icon: 'pi pi-file-edit',
    ariaLabel: 'Ir al formulario de llenado ciudadano del Cuestionario PDUL'
  }
];

function switchView(view: AppView) {
  currentView.value = view;
}

function onTabKeydown(event: KeyboardEvent, currentIndex: number): void {
  const visibleTabs = navTabs.filter((t) => !t.hidden);
  const currentTab = navTabs[currentIndex];
  let visibleIndex = visibleTabs.findIndex((t) => t.id === currentTab.id);
  if (visibleIndex === -1) visibleIndex = 0;

  let nextVisibleIndex = -1;
  if (event.key === 'ArrowRight' || event.key === 'ArrowDown') {
    event.preventDefault();
    nextVisibleIndex = (visibleIndex + 1) % visibleTabs.length;
  } else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') {
    event.preventDefault();
    nextVisibleIndex = (visibleIndex - 1 + visibleTabs.length) % visibleTabs.length;
  } else if (event.key === 'Home') {
    event.preventDefault();
    nextVisibleIndex = 0;
  } else if (event.key === 'End') {
    event.preventDefault();
    nextVisibleIndex = visibleTabs.length - 1;
  }

  if (nextVisibleIndex >= 0) {
    const nextTab = visibleTabs[nextVisibleIndex];
    switchView(nextTab.id);
    const el = document.getElementById(`tab-${nextTab.id}`);
    el?.focus();
  }
}

function openBuilderForNew() {
  selectedSurveyIdForBuilder.value = null;
  currentView.value = 'form-builder';
}

function openBuilderForEdit(surveyId: string) {
  selectedSurveyIdForBuilder.value = surveyId;
  currentView.value = 'form-builder';
}

function openResponsesForSurvey(surveyId: string) {
  selectedSurveyIdForResponses.value = surveyId;
  currentView.value = 'admin-responses';
}

function onSurveyCreated(surveyId: string) {
  selectedSurveyIdForResponses.value = surveyId;
}
</script>

<template>
  <div class="app-layout">
    <Toast v-if="hasPrimeVue" position="top-center" />
    <!-- Encabezado Institucional -->
    <header class="app-header">
      <div class="header-inner">
        <div class="brand">
          <img
            src="/logo-alcaldia-maturin.png"
            alt="Alcaldía Bolivariana del Municipio Maturín"
            class="brand-logo-img"
          />
        </div>
        <div class="header-pdul-wrap">
          <span class="header-pdul-title">PDUL</span>
          <span v-if="isAdminMode" class="header-admin-badge">Admin</span>
        </div>
      </div>
    </header>

    <!-- Barra de Navegación Accesible (Solo visible para personal administrativo) -->
    <nav v-if="isAdminMode" class="app-nav" role="navigation" aria-label="Navegación principal">
      <div class="nav-inner" role="tablist">
        <button
          v-for="(tab, index) in navTabs"
          :key="tab.id"
          type="button"
          role="tab"
          :id="`tab-${tab.id}`"
          :aria-selected="currentView === tab.id"
          :aria-controls="`panel-${tab.id}`"
          :tabindex="currentView === tab.id ? 0 : -1"
          :aria-label="tab.ariaLabel"
          class="nav-tab-btn"
          :class="{ active: currentView === tab.id, 'hidden-tab': tab.hidden }"
          :style="tab.hidden ? 'display: none !important;' : undefined"
          @click="switchView(tab.id)"
          @keydown="onTabKeydown($event, index)"
        >
          <i :class="['nav-icon', tab.icon]" aria-hidden="true"></i>
          <span class="nav-label">{{ tab.label }}</span>
          <span v-if="tab.badge" class="nav-badge">{{ tab.badge }}</span>
        </button>
      </div>
    </nav>

    <!-- Área Principal de Vistas -->
    <main class="app-main">
      <!-- 1. Dashboard Analítico GIS & KPIs -->
      <section
        id="panel-gis-dashboard"
        role="tabpanel"
        aria-labelledby="tab-gis-dashboard"
        tabindex="0"
        class="view-panel"
        v-if="currentView === 'gis-dashboard'"
      >
        <DashboardView />
      </section>

      <!-- 2. Gestión y Administración de Encuestas -->
      <section
        id="panel-admin-surveys"
        role="tabpanel"
        aria-labelledby="tab-admin-surveys"
        tabindex="0"
        class="view-panel"
        v-if="currentView === 'admin-surveys'"
      >
        <AdminSurveyListView
          @create-survey="openBuilderForNew"
          @edit-survey="openBuilderForEdit"
          @view-responses="openResponsesForSurvey"
        />
      </section>

      <!-- 3. Tabla y Supervisión de Respuestas Ciudadanas -->
      <section
        id="panel-admin-responses"
        role="tabpanel"
        aria-labelledby="tab-admin-responses"
        tabindex="0"
        class="view-panel"
        v-if="currentView === 'admin-responses'"
      >
        <AdminResponsesView
          :initial-survey-id="selectedSurveyIdForResponses || undefined"
          @back-to-surveys="currentView = 'admin-surveys'"
        />
      </section>

      <!-- 4. Constructor Visual Form.io -->
      <section
        id="panel-form-builder"
        role="tabpanel"
        aria-labelledby="tab-form-builder"
        tabindex="0"
        class="view-panel"
        v-if="currentView === 'form-builder'"
      >
        <FormBuilderView
          :initial-survey-id="selectedSurveyIdForBuilder || undefined"
          @survey-created="onSurveyCreated"
          @view-responses="openResponsesForSurvey"
        />
      </section>

      <!-- 5. Llenado Ciudadano PDUL -->
      <section
        id="panel-survey-fill"
        role="tabpanel"
        aria-labelledby="tab-survey-fill"
        tabindex="0"
        class="view-panel"
        v-show="!isAdminMode || currentView === 'survey-fill'"
      >
        <SurveyFillView />
      </section>
    </main>

    <!-- Pie de Página Institucional -->
    <footer class="app-footer">
      <div class="footer-inner">
        <p class="footer-copy">
          © 2025–2035 Alcaldía Bolivariana de Maturín. Plan de Desarrollo Urbano Local (PDUL).
        </p>
        <p class="footer-note">
          Plataforma Soberana de Participación Ciudadana y Movilidad Urbana.
        </p>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.app-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--surface-ground);
}

.app-header {
  background-color: var(--surface-card);
  border-bottom: 1px solid var(--border-color);
  padding: var(--spacing-12) var(--spacing-20);
  box-shadow: var(--shadow-sm);
}

.header-inner {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--spacing-3);
}

.brand {
  display: flex;
  align-items: center;
}

.brand-logo-img {
  height: 48px;
  max-height: 52px;
  width: auto;
  object-fit: contain;
  display: block;
}

.header-pdul-wrap {
  display: flex;
  align-items: center;
  gap: var(--spacing-8);
}

.header-pdul-title {
  font-family: 'Arial Black', var(--font-inter), Arial, sans-serif;
  font-size: 2rem;
  font-weight: 900;
  color: #000000;
  line-height: 1;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  user-select: none;
}

.header-admin-badge {
  background-color: var(--color-lavender-wash);
  color: var(--color-royal-signal);
  font-size: var(--text-caption);
  font-weight: var(--font-weight-semibold);
  padding: 2px 8px;
  border-radius: var(--radius-buttons);
}

@media (max-width: 480px) {
  .brand-logo-img {
    height: 38px;
  }
  .header-pdul-title {
    font-size: 1.5rem;
  }
}

/* Barra de Navegación */
.app-nav {
  background-color: var(--surface-card);
  border-bottom: 1px solid var(--border-color);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.nav-inner {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: var(--spacing-8);
  padding: 0 var(--spacing-16);
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}

.nav-inner::-webkit-scrollbar {
  display: none;
}

@media (max-width: 768px) {
  .nav-inner {
    flex-direction: column;
    align-items: stretch;
    gap: var(--spacing-4);
    padding: var(--spacing-8) var(--spacing-12);
    overflow-x: visible;
  }

  .nav-tab-btn {
    width: 100%;
    justify-content: flex-start;
    border-bottom: none;
    border-left: 3px solid transparent;
    border-radius: var(--radius-buttons);
    padding: var(--spacing-10) var(--spacing-12);
  }

  .nav-tab-btn.active {
    border-bottom-color: transparent;
    border-left-color: var(--color-royal-signal);
  }

  .nav-tab-btn .nav-badge {
    margin-left: auto;
  }
}

.nav-tab-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-8);
  padding: var(--spacing-12) var(--spacing-16);
  min-block-size: var(--min-touch-target);
  min-height: var(--min-touch-target);
  background: transparent;
  border: none;
  border-bottom: 3px solid transparent;
  font-family: var(--font-inter);
  font-size: var(--text-body-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-slate-caption);
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.15s ease;
  user-select: none;
}

.nav-tab-btn:hover:not(.active) {
  color: var(--text-primary);
  background-color: var(--surface-subtle);
}

.nav-tab-btn.active {
  color: var(--color-royal-signal);
  font-weight: var(--font-weight-bold);
  border-bottom-color: var(--color-royal-signal);
  background-color: var(--color-lavender-wash);
}

.nav-icon {
  font-size: 1.1rem;
}

.nav-badge {
  background-color: var(--color-cobalt-glow);
  color: #ffffff;
  font-size: 0.65rem;
  font-weight: var(--font-weight-bold);
  padding: 2px 6px;
  border-radius: var(--radius-pills);
}

/* Área Principal */
.app-main {
  flex: 1;
  padding: var(--spacing-20) 0;
}

.view-panel {
  width: 100%;
}

/* Placeholder Milestone 5 */
.m5-placeholder-card {
  max-width: 700px;
  margin: var(--spacing-40) auto;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-16);
  padding: var(--spacing-40) var(--spacing-24);
}

.m5-icon-wrap {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background-color: var(--color-lavender-wash);
  display: flex;
  align-items: center;
  justify-content: center;
}

.m5-icon {
  font-size: 2rem;
  color: var(--color-royal-signal);
}

.m5-title {
  font-size: var(--text-subheading);
  color: var(--text-primary);
}

.m5-desc {
  font-size: var(--text-body);
  color: var(--text-muted);
  line-height: 1.6;
}

.m5-badges {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-12);
  justify-content: center;
  margin-top: var(--spacing-8);
}

.m5-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-6);
  padding: var(--spacing-6) var(--spacing-12);
  background-color: var(--surface-subtle);
  border-radius: var(--radius-pills);
  font-size: var(--text-body-sm);
  color: var(--text-body-color);
  font-weight: var(--font-weight-medium);
}

/* Pie de Página */
.app-footer {
  background-color: var(--surface-card);
  border-top: 1px solid var(--border-color);
  padding: var(--spacing-20);
  margin-top: auto;
}

.footer-inner {
  max-width: 1400px;
  margin: 0 auto;
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
  font-size: var(--text-body-sm);
  color: var(--text-helper);
}
</style>
