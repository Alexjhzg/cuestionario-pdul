import { test, expect } from '@playwright/test';
import { AuditTracker } from './helpers/audit-tracker';
import { ARCHETYPES } from './helpers/survey-archetypes';
import { SurveyBotOperator } from './helpers/survey-actions';

test.describe('Bot Playwright - Auditoría Exhaustiva de Bifurcaciones y Ramas Condicionales (Cuestionario PDUL)', () => {

  // =========================================================================
  // BOT-01: Ruta Negativa / Base (Cero bifurcaciones activas)
  // =========================================================================
  test('BOT-01: Ruta Base sin bifurcaciones (Verifica que ramas dependientes permanezcan ocultas)', async ({ page }) => {
    const tracker = new AuditTracker(page);
    const bot = new SurveyBotOperator(page, tracker);
    const data = ARCHETYPES.bot01_negativo_base;

    await bot.navigateToSurvey();

    // Paso 1: Ubicación
    await bot.fillPaso1(data.paso1);
    await bot.nextStep();

    // Paso 2: Vivienda estándar (Sin campo otro)
    await bot.fillPaso2(data.paso2);
    await bot.nextStep();

    // Paso 3: Hogar con tenencia estándar (Sin campo otro)
    await bot.fillPaso3(data.paso3);
    await bot.nextStep();

    // Paso 4: Residente sin vehículo (Verifica cero campos vehiculares)
    await bot.fillPaso4(data.paso4);
    await bot.nextStep();

    // Paso 5: Viaje estándar con horarios en la misma fila
    await bot.fillPaso5(data.paso5);
    await bot.nextStep();

    // Paso 6: Sin dificultades en TP (Verifica que preguntas hijas no se muestren)
    await bot.fillPaso6(data.paso6);
    await bot.nextStep();

    // Paso 7: Sin cambio de movilidad en 5 años (Verifica que motivo no aparezca)
    await bot.fillPaso7(data.paso7);
    await bot.nextStep();

    // Paso 8: Cierre y Esparcimiento sin opciones 'otro' ni cruces en todas partes
    await bot.fillPaso8(data.paso8);
    await bot.submitAndVerifySuccess();

    const bugs = tracker.getFindings().filter((f) => f.type === 'BUG');
    expect(bugs, 'No deben ocurrir bugs de JavaScript en BOT-01').toHaveLength(0);
  });

  // =========================================================================
  // BOT-02: Ruta Extrema de Bifurcaciones ("Otro / Especifique")
  // =========================================================================
  test('BOT-02: Ruta Extrema de Bifurcaciones (Activa y valida 100% de campos dependientes v-if)', async ({ page }) => {
    const tracker = new AuditTracker(page);
    const bot = new SurveyBotOperator(page, tracker);
    const data = ARCHETYPES.bot02_extremo_bifurcaciones;

    await bot.navigateToSurvey();

    // Paso 1: Ubicación
    await bot.fillPaso1(data.paso1);
    await bot.nextStep();

    // Paso 2: Tipo de vivienda 'otro' -> Activa tipo_vivienda_otro
    await bot.fillPaso2(data.paso2);
    await bot.nextStep();

    // Paso 3: Tenencia 'otra_forma' -> Activa tenencia_vivienda_otra
    await bot.fillPaso3(data.paso3);
    await bot.nextStep();

    // Paso 4: Residente con vehículo 'si' -> Activa tipo_vehiculo y cantidad_vehiculo
    await bot.fillPaso4(data.paso4);
    await bot.nextStep();

    // Paso 5: Viaje con motivo '8', modo '8', modo_sec '8', botón regreso y modal de detalles
    await bot.fillPaso5(data.paso5);
    await bot.nextStep();

    // Paso 6: Dificultades 'si' y principal dificultad 'otro' -> Activa campo abierto
    await bot.fillPaso6(data.paso6);
    await bot.nextStep();

    // Paso 7: Cambio movilidad 'si' y motivo 'otro' -> Activa campo abierto
    await bot.fillPaso7(data.paso7);
    await bot.nextStep();

    // Paso 8: Esparcimiento con checkboxes 'otras' / 'otro' en 4 preguntas y cruces 'si'
    await bot.fillPaso8(data.paso8);
    await bot.submitAndVerifySuccess();

    const bugs = tracker.getFindings().filter((f) => f.type === 'BUG');
    expect(bugs, 'No deben ocurrir bugs de JavaScript en BOT-02').toHaveLength(0);
  });

  // =========================================================================
  // BOT-03: Ruta Hogar Multimodal y Tenencia Vehicular Privada
  // =========================================================================
  test('BOT-03: Ruta Vehicular Privada (Múltiples residentes, automóvil y trayectos motorizados)', async ({ page }) => {
    const tracker = new AuditTracker(page);
    const bot = new SurveyBotOperator(page, tracker);
    const data = ARCHETYPES.bot03_vehicular_privado;

    await bot.navigateToSurvey();

    await bot.fillPaso1(data.paso1);
    await bot.nextStep();

    await bot.fillPaso2(data.paso2);
    await bot.nextStep();

    await bot.fillPaso3(data.paso3);
    await bot.nextStep();

    await bot.fillPaso4(data.paso4);
    await bot.nextStep();

    await bot.fillPaso5(data.paso5);
    await bot.nextStep();

    await bot.fillPaso6(data.paso6);
    await bot.nextStep();

    await bot.fillPaso7(data.paso7);
    await bot.nextStep();

    await bot.fillPaso8(data.paso8);
    await bot.submitAndVerifySuccess();

    const bugs = tracker.getFindings().filter((f) => f.type === 'BUG');
    expect(bugs, 'No deben ocurrir bugs de JavaScript en BOT-03').toHaveLength(0);
  });

  // =========================================================================
  // BOT-04: Ruta Movilidad Activa (Caminante / Ciclista)
  // =========================================================================
  test('BOT-04: Ruta Peatón y Ciclista Urbano (Movilidad activa, ciclovías y cruces peatonales)', async ({ page }) => {
    const tracker = new AuditTracker(page);
    const bot = new SurveyBotOperator(page, tracker);
    const data = ARCHETYPES.bot04_movilidad_activa;

    await bot.navigateToSurvey();

    await bot.fillPaso1(data.paso1);
    await bot.nextStep();

    await bot.fillPaso2(data.paso2);
    await bot.nextStep();

    await bot.fillPaso3(data.paso3);
    await bot.nextStep();

    await bot.fillPaso4(data.paso4);
    await bot.nextStep();

    await bot.fillPaso5(data.paso5);
    await bot.nextStep();

    await bot.fillPaso6(data.paso6);
    await bot.nextStep();

    await bot.fillPaso7(data.paso7);
    await bot.nextStep();

    await bot.fillPaso8(data.paso8);
    await bot.submitAndVerifySuccess();

    const bugs = tracker.getFindings().filter((f) => f.type === 'BUG');
    expect(bugs, 'No deben ocurrir bugs de JavaScript en BOT-04').toHaveLength(0);
  });

  // =========================================================================
  // BOT-05: Prueba de Alternancia Dinámica y Validación de Horarios en Misma Fila
  // =========================================================================
  test('BOT-05: Alternancia Dinámica de Bifurcaciones (Toggle Sí/No) y Verificación Estricta de Horarios', async ({ page }) => {
    const tracker = new AuditTracker(page);
    const bot = new SurveyBotOperator(page, tracker);

    await bot.navigateToSurvey();

    // 1. Llenar Paso 1
    await bot.fillPaso1({
      parroquia: 'santa_cruz',
      comunidad_sector: 'Zona Industrial Santa Cruz',
      zona_residencia_od: 'Santa Cruz Sur',
      avenida_calle: 'Calle Principal',
      casa_apartamento: 'Galpón 5'
    });
    await bot.nextStep();

    // 2. Alternancia en Paso 2: Seleccionar 'otro', verificar que aparece, y luego cambiar a 'casa' y verificar que desaparece
    const radioOtro = page.locator('input[name="tipo_vivienda"][value="otro"]');
    const radioCasa = page.locator('input[name="tipo_vivienda"][value="casa"]');
    const inputOtro = page.locator('#tipo_vivienda_otro');

    await radioOtro.check();
    await expect(inputOtro).toBeVisible();
    await inputOtro.fill('Construcción temporal');

    await radioCasa.check();
    await expect(inputOtro).toHaveCount(0); // El campo dependiente desaparece limpiamente

    await page.fill('#total_cuartos_vivienda', '3');
    await bot.nextStep();

    // 3. Alternancia en Paso 3: Seleccionar 'otra_forma', verificar y luego cambiar a 'propia_pagada'
    const radioOtraTenencia = page.locator('input[name="tenencia_vivienda"][value="otra_forma"]');
    const radioPropia = page.locator('input[name="tenencia_vivienda"][value="propia_pagada"]');
    const inputOtraTenencia = page.locator('#tenencia_vivienda_otro');

    await radioOtraTenencia.check();
    await expect(inputOtraTenencia).toBeVisible();
    await inputOtraTenencia.fill('Prestada por empresa');

    await radioPropia.check();
    await expect(inputOtraTenencia).toHaveCount(0); // Desaparece limpiamente

    await page.fill('#grupos_gastos_separados', '1');
    await page.fill('#hogar_numero', '1');
    await page.fill('#cuartos_dormir_hogar', '2');
    await page.fill('#numero_personas_hogar', '1');
    await bot.nextStep();

    // 4. Alternancia en Paso 4: Residente con vehículo 'si' -> luego cambiar a 'no'
    await page.fill('#residente-nombre', 'Guillermo Parra');
    await page.selectOption('#residente-parentesco', '1');
    await page.selectOption('#residente-sexo', '1');
    await page.fill('#residente-edad', '50');
    await page.selectOption('#residente-sabe-leer', 'si');
    await page.selectOption('#residente-nivel-educativo', 'primaria');
    await page.selectOption('#residente-actividad', '4');
    await page.selectOption('#residente-medio-transporte', '6');
    await page.selectOption('#residente-licencia', 'no');

    // Alternar vehículo: 'si' muestra campos, 'no' los retira
    await page.selectOption('#residente-vehiculo-disp', 'si');
    await expect(page.locator('#residente-tipo-vehiculo')).toBeVisible();
    await expect(page.locator('#residente-cantidad-vehiculo')).toBeVisible();

    await page.selectOption('#residente-vehiculo-disp', 'no');
    await expect(page.locator('#residente-tipo-vehiculo')).toHaveCount(0);
    await expect(page.locator('#residente-cantidad-vehiculo')).toHaveCount(0);

    await page.locator('.add-residente-btn').click();
    await page.waitForTimeout(300);
    await bot.nextStep();

    // 5. Verificación estricta de Horarios en la Misma Fila (.horarios-grid-row)
    const horariosRow = page.locator('.horarios-grid-row');
    await expect(horariosRow).toBeVisible();
    const salidaSelect = horariosRow.locator('#viaje-hora-salida-h');
    const llegadaSelect = horariosRow.locator('#viaje-hora-llegada-h');
    await expect(salidaSelect).toBeVisible();
    await expect(llegadaSelect).toBeVisible();

    // Comprobar que comparten la misma coordenada vertical (misma fila top +/- 5px)
    const salidaBox = await salidaSelect.boundingBox();
    const llegadaBox = await llegadaSelect.boundingBox();
    expect(salidaBox).not.toBeNull();
    expect(llegadaBox).not.toBeNull();
    if (salidaBox && llegadaBox) {
      // En vista escritorio/tablet deben tener un desfase vertical menor a 5px
      const viewport = page.viewportSize();
      if (viewport && viewport.width >= 600) {
        expect(Math.abs(salidaBox.y - llegadaBox.y)).toBeLessThanOrEqual(5);
      }
    }

    // Agregar viaje y probar botón de regreso rápido
    await page.selectOption('#viaje-persona', '1');
    await page.fill('#viaje-origen-dir', 'Santa Cruz');
    await page.fill('#viaje-origen', 'Santa Cruz');
    await page.fill('#viaje-destino-dir', 'Mercado Municipal');
    await page.fill('#viaje-destino', 'San Simón');
    await page.selectOption('#viaje-hora-salida-h', '08');
    await page.selectOption('#viaje-hora-salida-m', '15');
    await page.selectOption('#viaje-hora-salida-periodo', 'AM');
    await page.selectOption('#viaje-hora-llegada-h', '08');
    await page.selectOption('#viaje-hora-llegada-m', '45');
    await page.selectOption('#viaje-hora-llegada-periodo', 'AM');
    await page.selectOption('#viaje-motivo', '3'); // Compras
    await page.selectOption('#viaje-modo', '6'); // TP
    await page.fill('#viaje-tiempo', '30');
    await page.fill('#viaje-costo', '15');
    await page.locator('.add-viaje-btn').click();
    await page.waitForTimeout(300);

    // Botón de regreso rápido a casa en 1 toque
    const btnRegreso = page.locator('.action-btn.return-btn').first();
    await expect(btnRegreso).toBeVisible();
    await btnRegreso.click();
    await page.waitForTimeout(300);
    await expect(page.locator('.viaje-card')).toHaveCount(2);

    await tracker.checkHorizontalOverflow('BOT-05: Fin de Alternancia');
  });

});
