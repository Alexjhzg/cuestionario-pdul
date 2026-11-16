import { test, expect } from '@playwright/test';
import { AuditTracker } from './helpers/audit-tracker';

test.describe('Fase 4 - Retrocompatibilidad E2E de Borradores localStorage (pdul_draft_*)', () => {
  test('Restaura borrador legacy plano y normaliza parroquia humana a snake_case sin errores en consola', async ({ page }) => {
    const tracker = new AuditTracker(page);

    // Pre-cargar borrador legacy v1 plano antes de iniciar el render inicial
    await page.addInitScript(() => {
      if (!window.sessionStorage.getItem('__legacy_draft_seeded')) {
        window.localStorage.setItem(
          'pdul_draft_cuestionario-od-maturin',
          JSON.stringify({
            cedula: '19555666',
            parroquia: 'Alto de Los Godos',
            comunidad_sector: 'Sector Los Godos',
            zona_residencia_od: 'ZONA_02',
            avenida_calle: 'Av. Libertador',
            casa_apartamento: 'Casa 12',
            tipo_vivienda: 'quinta',
            total_cuartos_vivienda: 4,
            step: '1',
            savedAt: '10:30:00'
          })
        );
        window.sessionStorage.setItem('__legacy_draft_seeded', '1');
      }
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Confirmar banner de restauración visible
    const restoreBtn = page.locator('.draft-banner button:has-text("Continuar borrador")');
    await expect(restoreBtn).toBeVisible();
    await restoreBtn.click();

    // Debe restaurarse directamente en Paso 2 (Vivienda) con los datos cargados
    await expect(page.locator('.step-title')).toContainText('Vivienda');
    await expect(page.locator('#total_cuartos_vivienda')).toHaveValue('4');

    // Volver al Paso 1 para verificar que la parroquia humana fue normalizada al código canónico
    await page.locator('button:has-text("Anterior")').click();
    await expect(page.locator('#parroquia')).toHaveValue('alto_de_los_godos');
    await expect(page.locator('#comunidad_sector')).toHaveValue('Sector Los Godos');

    // Limpiar el borrador y confirmar que desaparece sin errores
    await page.evaluate(() => window.localStorage.clear());

    const bugs = tracker.getFindings().filter((f) => f.type === 'BUG');
    expect(bugs).toEqual([]);
  });
});

