import { test, expect } from '@playwright/test';

test.describe('Demostración Visual Interactiva - Recorrido por Todas las Pantallas (PDUL)', () => {
  test('Tour guiado interactivo con pausas visuales por cada pantalla y sección', async ({ page }) => {
    // Configurar viewport amplio y nítido
    await page.setViewportSize({ width: 1280, height: 800 });

    const pausa = async (ms = 1200) => await page.waitForTimeout(ms);

    // -------------------------------------------------------------
    // PANTALLA 1: DASHBOARD ANALÍTICO DE MOVILIDAD Y PARTICIPACIÓN
    // -------------------------------------------------------------
    await page.goto('/?admin=true');
    await expect(page.locator('#tab-gis-dashboard')).toBeVisible();
    await pausa(1500);

    // Scroll por los KPIs y Gráficos
    await page.evaluate(() => window.scrollBy({ top: 400, behavior: 'smooth' }));
    await pausa(1200);

    await page.evaluate(() => window.scrollBy({ top: 500, behavior: 'smooth' }));
    await pausa(1200);

    // Alternar a vista accesible de tablas
    const toggleViewBtn = page.locator('.btn-toggle-view');
    if (await toggleViewBtn.isVisible()) {
      await toggleViewBtn.click();
      await pausa(1500);
      await toggleViewBtn.click();
      await pausa(1000);
    }

    await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
    await pausa(1000);

    // -------------------------------------------------------------
    // PANTALLA 2: GESTIÓN Y ADMINISTRACIÓN DE ENCUESTAS
    // -------------------------------------------------------------
    await page.click('#tab-admin-surveys');
    await expect(page.locator('#panel-admin-surveys')).toBeVisible();
    await pausa(1500);

    // -------------------------------------------------------------
    // PANTALLA 3: SUPERVISIÓN DE RESPUESTAS CIUDADANAS Y PROTECCIÓN PII
    // -------------------------------------------------------------
    await page.click('#tab-admin-responses');
    await expect(page.locator('#panel-admin-responses')).toBeVisible();
    await pausa(1500);

    // Abrir modal de detalle de respuesta si existe botón
    const btnFirstDetail = page.locator('.btn-detail').first();
    if (await btnFirstDetail.isVisible()) {
      await btnFirstDetail.click();
      await pausa(1500);
      const closeDetailBtn = page.locator('.modal-close-btn');
      if (await closeDetailBtn.isVisible()) {
        await closeDetailBtn.click();
        await pausa(800);
      }
    }

    // -------------------------------------------------------------
    // PANTALLA 4: LLENADO DEL CUESTIONARIO CIUDADANO (8 SECCIONES TÉCNICAS)
    // -------------------------------------------------------------
    await page.click('#tab-survey-fill');
    await expect(page.locator('.survey-wizard')).toBeVisible();
    await pausa(1500);

    // PASO 1: Ubicación
    await page.selectOption('#parroquia_residencia', 'san_simon');
    await page.fill('#comunidad_sector', 'Centro Maturín - Demostración en vivo');
    await page.fill('#avenida_calle', 'Av. Bolívar');
    await page.fill('#casa_apto_edificio', 'Edificio Alcaldía, Piso 2');
    await pausa(1000);
    await page.click('.btn-step-nav.next');
    await pausa(1000);

    // PASO 2: Vivienda
    await page.check('input[name="tipo_vivienda"][value="casa"]');
    await page.check('input[name="tenencia_vivienda"][value="propia"]');
    await pausa(1000);
    await page.click('.btn-step-nav.next');
    await pausa(1000);

    // PASO 3: Hogar
    await page.check('input[name="posee_vehiculo_hogar"][value="si"]');
    await pausa(800);
    await page.fill('#cant_automoviles', '1');
    await page.fill('#cant_motocicletas', '1');
    await page.check('input[name="fuente_energia_cocina"][value="gas_bombona"]');
    await page.check('input[name="agua_procedencia"][value="red_publica_acueducto"]');
    await pausa(1000);
    await page.click('.btn-step-nav.next');
    await pausa(1000);

    // PASO 4: Residentes
    await page.fill('#residente-nombres', 'Carlos Silva');
    await page.selectOption('#residente-parentesco', 'jefe');
    await page.selectOption('#residente-sexo', 'masculino');
    await page.fill('#residente-edad', '39');
    await page.selectOption('#residente-nivel-educativo', 'universitario');
    await page.selectOption('#residente-ocupacion', 'profesional_tecnico');
    await page.click('.add-residente-btn');
    await pausa(1200);
    await page.click('.btn-step-nav.next');
    await pausa(1000);

    // PASO 5: Viajes y Horarios en la Misma Fila
    await page.selectOption('#viaje-persona', '1');
    await page.fill('#viaje-origen-dir', 'Casco Central');
    await page.fill('#viaje-zona-origen', 'Z-01');
    await page.fill('#viaje-destino-dir', 'Juanico');
    await page.fill('#viaje-zona-destino', 'Z-04');
    await page.selectOption('#viaje-hora-salida-h', '07');
    await page.selectOption('#viaje-hora-salida-m', '30');
    await page.selectOption('#viaje-hora-salida-periodo', 'AM');
    await page.selectOption('#viaje-hora-llegada-h', '08');
    await page.selectOption('#viaje-hora-llegada-m', '00');
    await page.selectOption('#viaje-hora-llegada-periodo', 'AM');
    await page.selectOption('#viaje-motivo', 'trabajo');
    await page.selectOption('#viaje-modo-p', 'automovil_conductor');
    await page.fill('#viaje-tiempo', '30');
    await page.fill('#viaje-costo', '0');
    await page.click('.add-viaje-btn');
    await pausa(1500);
    await page.click('.btn-step-nav.next');
    await pausa(1000);

    // PASO 6: Calidad de Servicios de Transporte
    await page.fill('#rutas_tp_dia', '0');
    await page.fill('#tiempo_espera_paradas_min', '0');
    await page.fill('#km_residencia_parada', '1');
    await page.check('input[name="dificultades_acceso_tp"][value="no"]');
    await page.check('input[name="calificacion_servicio_tp"][value="bueno"]');
    await page.fill('#gasto_semanal_transporte_bs', '150');
    await page.check('input[name="acuerdo_rutas_directas"][value="de_acuerdo"]');
    await page.fill('#comentarios_transporte_maturin', 'Requiere mejor sincronización de semáforos.');
    await pausa(1000);
    await page.click('.btn-step-nav.next');
    await pausa(1000);

    // PASO 7: Movilidad Activa y Espacio Público
    await page.check('input[name="cambio_movilidad_5_anos"][value="no"]');
    await page.check('input[name="caminatas_mas_10min"][value="si"]');
    await page.check('input[name="usa_bicicleta"][value="si"]');
    await page.fill('#dias_camina_bici_semana', '4');
    await page.check('input[name="modo_actividades_centro"][value="camina"]');
    await page.check('input[name="aceras_adecuadas"][value="regular"]');
    await page.check('input[name="seguridad_desplazamiento_centro"][value="muy_seguro"]');
    await page.check('input[name="iluminacion_nocturna_adecuada"][value="neutral"]');
    await page.check('input[name="obstaculos_aceras"][value="no"]');
    await page.check('input[name="ancho_aceras_suficiente"][value="si"]');
    await page.check('input[name="calzada_buen_estado"][value="si"]');
    await page.check('input[name="rampas_accesibilidad_adecuadas"][value="si"]');
    await page.check('input[name="cruce_peatonal_todas"][value="si"]');
    await page.check('input[name="cruce_demarcado_visible"][value="si"]');
    await page.check('input[name="seguridad_cruzar_interseccion"][value="muy_seguro"]');
    await page.check('input[name="tiempo_semaforos_suficiente"][value="si"]');
    await page.check('input[name="arbolado_sombra_suficiente"][value="si"]');
    await page.check('input[name="bancos_descanso_suficientes"][value="si"]');
    await page.check('input[name="papeleras_disponibles"][value="si"]');
    await page.check('input[name="trayecto_pie_parada_seguro"][value="muy_seguro"]');
    await page.check('input[name="aire_ruido_aceptables"][value="si"]');
    await page.check('input[name="conductores_ceden_paso"][value="si"]');
    await page.check('input[name="ciudad_prioriza_peaton"][value="si"]');
    await page.check('input[name="participacion_consultas_peatonales"][value="si"]');
    await page.check('input[name="planes_movilidad_peatonal_normativa"][value="si"]');
    await pausa(1000);
    await page.click('.btn-step-nav.next');
    await pausa(1000);

    // PASO 8: Observaciones y Cierre
    await page.selectOption('#frecuencia_visita_parques', 'semanal');
    await page.selectOption('#caminatas_ciudad', 'frecuentemente');
    await page.selectOption('#seguridad_parques_dia', 'bastante_seguro');
    await page.selectOption('#seguridad_parques_noche', 'poco_seguro');
    await page.selectOption('#limpieza_parques', 'buena');
    await page.selectOption('#calidad_mobiliario_parques', 'buena');
    await page.check('input[name="disposicion_participar_mejoras"][value="si"]');
    await page.fill('#observaciones_generales', 'Demostración interactiva guiada completada con éxito.');
    await page.check('#acepta_declaracion');
    await pausa(1500);

    // Finalizar y Enviar
    await page.click('.btn-submit-survey');
    await expect(page.locator('.survey-success-state')).toBeVisible({ timeout: 10000 });
    await pausa(2000);
  });
});
