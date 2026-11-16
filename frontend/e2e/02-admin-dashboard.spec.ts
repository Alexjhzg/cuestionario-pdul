import { test, expect } from '@playwright/test';
import { AuditTracker } from './helpers/audit-tracker';

test.describe('Auditoría Funcional - Dashboard Analítico Municipal (Milestone 5)', () => {
  test('Apertura inmediata en Dashboard, renderizado de 6 gráficos, KPIs e interactividad', async ({ page }) => {
    const tracker = new AuditTracker(page);

    // 1. Ingresar en Modo Admin
    await page.goto('/?admin=true');
    await page.waitForLoadState('networkidle');

    // 2. Verificar que la barra de administración exista y esté en primera posición el Dashboard
    const adminNav = page.locator('nav.app-nav');
    await expect(adminNav).toBeVisible();

    const tabs = page.locator('nav.app-nav [role="tab"]');
    await expect(tabs).toHaveCount(5);

    // El primer tab debe ser el Dashboard Analítico y estar activo por defecto
    const firstTab = tabs.first();
    await expect(firstTab).toHaveAttribute('id', 'tab-gis-dashboard');
    await expect(firstTab).toHaveAttribute('aria-selected', 'true');
    await expect(firstTab).toHaveClass(/active/);

    // 3. Verificar que el panel del Dashboard esté visible en el DOM
    const dashboardPanel = page.locator('#panel-gis-dashboard');
    await expect(dashboardPanel).toBeVisible();

    // 4. Verificar Tarjetas de KPI (KpiCardsGrid)
    const kpiCards = page.locator('.kpi-card');
    await expect(kpiCards).toHaveCount(4);

    // Los valores deben ser números positivos reales derivados de la base de datos poblada
    const totalEncuestasEl = kpiCards.nth(0).locator('.kpi-value');
    await expect(totalEncuestasEl).toBeVisible();
    const encuestasVal = await totalEncuestasEl.textContent();
    expect(Number(encuestasVal)).toBeGreaterThan(0);

    // 5. Verificar presencia de los 6 gráficos analíticos en el DOM
    const chartCards = page.locator('.survey-card, .chart-card');
    // Deben existir al menos las tarjetas de gráficos configuradas
    await expect(chartCards.first()).toBeVisible();

    // Comprobar contenedores específicos de charts
    const parroquiasChart = page.locator('.parroquias-chart-card');
    await expect(parroquiasChart).toBeVisible();

    const calificacionChart = page.locator('.calificacion-chart-card');
    await expect(calificacionChart).toBeVisible();

    const dificultadesChart = page.locator('.dificultades-chart-card');
    await expect(dificultadesChart).toBeVisible();

    const seguridadChart = page.locator('.seguridad-chart-card');
    await expect(seguridadChart).toBeVisible();

    const modalSplitChart = page.locator('.chart-card');
    await expect(modalSplitChart).toBeVisible();

    const odMatrixChart = page.locator('.matrix-card');
    await expect(odMatrixChart).toBeVisible();

    // 6. Prueba de interactividad: Alternar modo visual / tablas accesibles (WCAG AA)
    const btnToggleAccessible = page.locator('.btn-toggle-view');
    await expect(btnToggleAccessible).toBeVisible();
    await btnToggleAccessible.click();
    await page.waitForTimeout(300);

    // Debe mostrarse la sección de tablas accesibles
    const accessibleFallback = page.locator('.accessible-data-fallback');
    await expect(accessibleFallback).toBeVisible();
    const tables = page.locator('.accessible-table');
    await expect(tables.first()).toBeVisible();

    // Regresar a modo visual
    await btnToggleAccessible.click();
    await page.waitForTimeout(300);
    await expect(accessibleFallback).toHaveCount(0);

    // 7. Prueba de interactividad: Botón de refrescar datos
    const btnRefresh = page.locator('.btn-refresh');
    await expect(btnRefresh).toBeVisible();
    await btnRefresh.click();
    await page.waitForTimeout(500);

    // 8. Auditar desbordamiento horizontal en el Dashboard
    await tracker.checkHorizontalOverflow('Dashboard Analítico Principal');

    // 9. Comprobar que no hubo bugs durante la auditoría
    const bugs = tracker.getFindings().filter((f) => f.type === 'BUG');
    if (bugs.length > 0) {
      console.warn('Bugs en Dashboard Analítico:', JSON.stringify(bugs, null, 2));
    }
    expect(bugs, 'No deben registrarse excepciones ni errores 500 en el Dashboard').toHaveLength(0);
  });
});
