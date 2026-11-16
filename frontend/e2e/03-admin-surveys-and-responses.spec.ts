import { test, expect } from '@playwright/test';
import { AuditTracker } from './helpers/audit-tracker';

test.describe('Auditoría Funcional - Gestión Administrativa y Protección de PII (Milestones 4 y 5)', () => {
  test('Supervisión de encuestas, protección estricta de PII, modales y navegación WAI-ARIA', async ({ page }) => {
    const tracker = new AuditTracker(page);

    await page.goto('/?admin=true');
    await page.waitForLoadState('networkidle');

    // =========================================================================
    // 1. Pestaña: Gestión de Encuestas (AdminSurveyListView)
    // =========================================================================
    const tabSurveys = page.locator('#tab-admin-surveys');
    await tabSurveys.click();
    await page.waitForTimeout(400);

    await expect(tabSurveys).toHaveAttribute('aria-selected', 'true');
    const panelSurveys = page.locator('#panel-admin-surveys');
    await expect(panelSurveys).toBeVisible();

    // Verificar que la opción de crear nueva encuesta esté oculta de la interfaz
    const btnCreate = page.locator('[data-testid="btn-create-new-survey"]');
    await expect(btnCreate).not.toBeVisible();

    // Verificar tabla de encuestas registradas (desktop tabla o mobile cards)
    const surveyItems = page.locator('.survey-row, .survey-card').filter({ visible: true });
    await expect(surveyItems.first()).toBeVisible();

    await tracker.checkHorizontalOverflow('Gestión de Encuestas');

    // =========================================================================
    // 2. Pestaña: Respuestas Ciudadanas (AdminResponsesView)
    // =========================================================================
    const tabResponses = page.locator('#tab-admin-responses');
    await tabResponses.click();
    await page.waitForTimeout(500);

    await expect(tabResponses).toHaveAttribute('aria-selected', 'true');
    const panelResponses = page.locator('#panel-admin-responses');
    await expect(panelResponses).toBeVisible();

    // Auditoría de PII: La cédula y nombres NO deben aparecer en texto plano en la tabla principal
    const responsesContainer = panelResponses.locator('.responses-table-card').first();
    const tableText = await responsesContainer.innerText();
    expect(tableText).not.toMatch(/V-\d{7,8}/i);

    // Verificar paginación: Selector de filas por página
    const limitSelect = panelResponses.locator('#page-size-select');
    if (await limitSelect.count() > 0) {
      await limitSelect.selectOption('25');
      await page.waitForTimeout(400);
    }

    // Probar apertura del Modal de Detalle en formato Grid amigable para personal no técnico
    const btnFirstDetail = panelResponses.locator('.btn-detail').first();
    if (await btnFirstDetail.isVisible()) {
      await btnFirstDetail.click();
      await page.waitForTimeout(400);

      const modalDetail = page.locator('div[role="dialog"]');
      await expect(modalDetail).toBeVisible();

      // Comprobar que la vista predeterminada sea la Ficha Grid
      const gridViewer = modalDetail.locator('[data-testid="grid-detail-viewer"]');
      await expect(gridViewer).toBeVisible();
      await expect(modalDetail.locator('.card-section-title').first()).toBeVisible();

      // Cerrar modal
      const btnCloseModal = modalDetail.locator('[data-testid="btn-modal-close"]');
      await btnCloseModal.click();
      await page.waitForTimeout(300);
      await expect(modalDetail).not.toBeVisible();
    }

    await tracker.checkHorizontalOverflow('Respuestas Ciudadanas');

    // =========================================================================
    // 3. Verificación de Ocultación de Pestaña Crear Encuesta (Constructor)
    // =========================================================================
    const tabBuilder = page.locator('#tab-form-builder');
    await expect(tabBuilder).not.toBeVisible();

    // =========================================================================
    // 4. Navegación Accesible por Teclado WAI-ARIA entre pestañas visibles
    // =========================================================================
    await tabResponses.focus();
    await page.keyboard.press('ArrowLeft');
    await page.waitForTimeout(200);

    // Debe haberse seleccionado la pestaña anterior (admin-surveys)
    await expect(tabSurveys).toHaveAttribute('aria-selected', 'true');

    // Presionar Home -> debe ir a la primera pestaña (gis-dashboard)
    await page.keyboard.press('Home');
    await page.waitForTimeout(200);
    const tabDashboard = page.locator('#tab-gis-dashboard');
    await expect(tabDashboard).toHaveAttribute('aria-selected', 'true');

    // Verificar que no se hayan registrado errores
    const bugs = tracker.getFindings().filter((f) => f.type === 'BUG');
    if (bugs.length > 0) {
      console.warn('Bugs en Gestión y Respuestas:', JSON.stringify(bugs, null, 2));
    }
    expect(bugs, 'No deben encontrarse bugs en los paneles de gestión administrativa').toHaveLength(0);
  });
});
