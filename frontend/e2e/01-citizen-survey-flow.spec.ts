import { test, expect } from '@playwright/test';
import { AuditTracker } from './helpers/audit-tracker';

test.describe('Auditoría Funcional - Flujo Ciudadano (Llenado del Cuestionario PDUL)', () => {
  test('Llenado interactivo completo del Cuestionario PDUL y auditoría de anomalías', async ({ page }) => {
    const tracker = new AuditTracker(page);

    // 1. Cargar aplicación en modo ciudadano
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // 2. Verificar Aislamiento de Seguridad: la barra de administración no debe existir para el ciudadano
    const adminNav = page.locator('nav.app-nav');
    await expect(adminNav).toHaveCount(0);

    // 3. Verificar encabezado institucional
    await expect(page.locator('.header-pdul-title')).toHaveText('PDUL');
    const adminBadge = page.locator('.header-admin-badge');
    await expect(adminBadge).toHaveCount(0);

    // Auditar desbordamiento en carga inicial
    await tracker.checkHorizontalOverflow('Inicio Ciudadano');

    // =========================================================================
    // PASO 1 (Index 0): Sección I - Identificación y Ubicación de la Residencia
    // =========================================================================
    const btnSiguiente = page.locator('button:has-text("Siguiente")');

    // Prueba de intento de avanzar en blanco (debe alertar mediante Toast sin romper la UI)
    await btnSiguiente.click();
    await page.waitForTimeout(300);

    // Llenar campos requeridos de Sección I
    await page.selectOption('#parroquia', 'san_simon');
    await page.fill('#comunidad_sector', 'Sector Centro - Avenida Bolívar');
    await page.fill('#zona_residencia_od', 'San Simón Centro');
    await page.fill('#avenida_calle', 'Calle Monagas c/c Calle Chimborazo');
    await page.fill('#casa_apartamento', 'Casa Nro. 45');

    await tracker.checkHorizontalOverflow('Paso 1: Ubicación');
    await btnSiguiente.click();
    await page.waitForTimeout(400);

    // =========================================================================
    // PASO 2 (Index 1): Sección II - Datos de la Vivienda
    // =========================================================================
    await expect(page.locator('.step-title')).toBeVisible();

    // Tipo de vivienda (radio button)
    const radioCasa = page.locator('input[name="tipo_vivienda"][value="casa"]');
    await radioCasa.check();

    // Total de cuartos de la vivienda
    await page.fill('#total_cuartos_vivienda', '4');

    await tracker.checkHorizontalOverflow('Paso 2: Vivienda');
    await btnSiguiente.click();
    await page.waitForTimeout(400);

    // =========================================================================
    // PASO 3 (Index 2): Sección III - Datos del Hogar
    // =========================================================================
    await expect(page.locator('.step-title')).toBeVisible();

    await page.fill('#grupos_gastos_separados', '1');
    await page.fill('#hogar_numero', '1');
    await page.fill('#cuartos_dormir_hogar', '2');
    await page.fill('#numero_personas_hogar', '2'); // Declaramos 2 integrantes

    // Régimen de tenencia (radio button)
    const radioPropia = page.locator('input[name="tenencia_vivienda"][value="propia_pagada"]');
    await radioPropia.check();

    await tracker.checkHorizontalOverflow('Paso 3: Hogar');
    await btnSiguiente.click();
    await page.waitForTimeout(400);

    // =========================================================================
    // PASO 4 (Index 3): Sección IV - Composición del Hogar y Residentes Habituales
    // =========================================================================
    await expect(page.locator('.step-title')).toBeVisible();

    // Intentar agregar sin datos (debe mostrar advertencia interna en el componente)
    const btnAgregarMiembro = page.locator('.add-residente-btn');
    await btnAgregarMiembro.click();
    await page.waitForTimeout(200);

    // Agregar Miembro 1 (Jefe de hogar)
    await page.fill('#residente-nombre', 'Alejandro Morales');
    await page.selectOption('#residente-parentesco', '1'); // Jefe(a)
    await page.selectOption('#residente-sexo', '1'); // Hombre
    await page.fill('#residente-edad', '42');
    await page.selectOption('#residente-sabe-leer', 'si');
    await page.selectOption('#residente-nivel-educativo', 'universitario');
    await page.selectOption('#residente-actividad', '1'); // Trabaja
    await page.selectOption('#residente-medio-transporte', '6'); // Transporte público
    await page.selectOption('#residente-licencia', 'no');
    await page.selectOption('#residente-vehiculo-disp', 'no');
    await btnAgregarMiembro.click();
    await page.waitForTimeout(300);

    // Agregar Miembro 2 (Cónyuge)
    await page.fill('#residente-nombre', 'Elena Rondón');
    await page.selectOption('#residente-parentesco', '2'); // Cónyuge
    await page.selectOption('#residente-sexo', '2'); // Mujer
    await page.fill('#residente-edad', '39');
    await page.selectOption('#residente-sabe-leer', 'si');
    await page.selectOption('#residente-nivel-educativo', 'universitario');
    await page.selectOption('#residente-actividad', '1'); // Trabaja
    await page.selectOption('#residente-medio-transporte', '5'); // Taxi
    await page.selectOption('#residente-licencia', 'si');
    await page.selectOption('#residente-vehiculo-disp', 'si');
    await page.selectOption('#residente-tipo-vehiculo', 'automovil');
    await page.fill('#residente-cantidad-vehiculo', '1');
    await btnAgregarMiembro.click();
    await page.waitForTimeout(300);

    // Verificar que se hayan renderizado 2 tarjetas de miembros
    const memberCards = page.locator('.residente-card');
    await expect(memberCards).toHaveCount(2);

    await tracker.checkHorizontalOverflow('Paso 4: Residentes');
    await btnSiguiente.click();
    await page.waitForTimeout(400);

    // =========================================================================
    // PASO 5 (Index 4): Sección V - Movilidad Cotidiana y Registro de Viajes
    // =========================================================================
    await expect(page.locator('.step-title')).toBeVisible();

    const btnAgregarViaje = page.locator('.add-viaje-btn');
    await page.selectOption('#viaje-persona', '1');
    await page.fill('#viaje-origen-dir', 'Casa de habitación');
    await page.fill('#viaje-origen', 'San Simón');
    await page.fill('#viaje-destino-dir', 'Sede Laboral Los Guaritos');
    await page.fill('#viaje-destino', 'Alto de Los Godos');
    await page.selectOption('#viaje-hora-salida-h', '07');
    await page.selectOption('#viaje-hora-salida-m', '30');
    await page.selectOption('#viaje-hora-salida-periodo', 'AM');
    await page.selectOption('#viaje-hora-llegada-h', '08');
    await page.selectOption('#viaje-hora-llegada-m', '10');
    await page.selectOption('#viaje-hora-llegada-periodo', 'AM');
    await page.selectOption('#viaje-motivo', '1'); // Trabajo
    await page.selectOption('#viaje-modo', '6'); // Transporte público
    await page.fill('#viaje-tiempo', '40');
    await page.fill('#viaje-costo', '15');

    await btnAgregarViaje.click();
    await page.waitForTimeout(300);

    // Verificar que se renderice la tarjeta del viaje
    const tripCards = page.locator('.viaje-card');
    await expect(tripCards).toHaveCount(1);

    // Probar acción rápida: "Agregar viaje de regreso a casa"
    const btnRegreso = page.locator('.action-btn.return-btn').first();
    if (await btnRegreso.isVisible()) {
      await btnRegreso.click();
      await page.waitForTimeout(300);
      await expect(page.locator('.viaje-card')).toHaveCount(2);
    }

    await tracker.checkHorizontalOverflow('Paso 5: Viajes');
    await btnSiguiente.click();
    await page.waitForTimeout(400);

    // =========================================================================
    // PASO 6 (Index 5): Sección VI - Características de Transporte Público
    // =========================================================================
    await expect(page.locator('.step-title')).toBeVisible();
    await page.fill('#rutas_tp_dia', '2');
    await page.fill('#tiempo_espera_paradas_min', '35');
    await page.fill('#km_residencia_parada', '0.4');

    // Dificultades de acceso (activa campo condicional)
    await page.check('input[name="dificultades_acceso_tp"][value="si"]');
    await page.check('input[name="principal_dificultad_tp"][value="frecuencia_baja"]');

    // Calificación de TP
    await page.check('input[name="calificacion_servicio_tp"][value="regular"]');
    await page.fill('#gasto_semanal_transporte_bs', '180');

    // Acuerdo rutas directas
    await page.check('input[name="acuerdo_rutas_directas"][value="totalmente_de_acuerdo"]');

    // Comentario sobre el transporte
    await page.fill('#comentarios_transporte_maturin', 'Se requiere mayor frecuencia y unidades en horas pico.');

    await tracker.checkHorizontalOverflow('Paso 6: Transporte Público');
    await btnSiguiente.click();
    await page.waitForTimeout(400);

    // =========================================================================
    // PASO 7 (Index 6): Sección VII - Movilidad No Motorizada y Percepción
    // =========================================================================
    await expect(page.locator('.step-title')).toBeVisible();

    await page.check('input[name="cambio_movilidad_5_anos"][value="si"]');
    await page.check('input[name="motivo_cambio_desplazamiento"][value="costo"]');
    await page.check('input[name="caminatas_mas_10min"][value="si"]');
    await page.check('input[name="usa_bicicleta"][value="no"]');
    await page.fill('#dias_camina_bici_semana', '4');
    await page.check('input[name="modo_actividades_centro"][value="camina"]');
    await page.check('input[name="aceras_adecuadas"][value="no"]');
    await page.check('input[name="seguridad_desplazamiento_centro"][value="neutral"]');

    await tracker.checkHorizontalOverflow('Paso 7: Movilidad Activa');
    await btnSiguiente.click();
    await page.waitForTimeout(400);

    // =========================================================================
    // PASO 8 (Index 7): Sección VIII - Esparcimiento, Declaración y Envío Final
    // =========================================================================
    await expect(page.locator('.step-title')).toBeVisible();

    // Bloque A: Parques
    await page.check('input[name="frecuencia_visita_parques"][value="ocasionalmente"]');
    await page.check('input[name="actividades_parques"][value="caminar"]');
    await page.check('input[name="caminatas_ciudad"][value="si"]');
    await page.check('input[name="seguridad_parques_dia"][value="bastante_seguro"]');
    await page.check('input[name="seguridad_parques_noche"][value="poco_seguro"]');
    await page.check('input[name="limpieza_parques"][value="regular"]');
    await page.check('input[name="impedimentos_espacios"][value="distancia"]');
    await page.check('input[name="satisfaccion_centro"][value="neutral"]');
    await page.check('input[name="mejoras_prioritarias"][value="iluminacion"]');
    await page.fill('#parque_mejorar_primero', 'Parque del Casco Central');
    await page.check('input[name="disposicion_participar_mejoras"][value="si"]');
    await page.fill('#sugerencias_esparcimiento', 'Incorporar más bancas y sombra en las plazas.');

    // Bloque B: Aceras
    await page.check('input[name="acera_comoda"][value="en_desacuerdo"]');
    await page.fill('#sectores_para_caminar', 'Casco Central, Av. Bolívar');
    await page.check('input[name="facilidad_llegada_parques"][value="regular"]');
    await page.check('input[name="esparcimientos_faltantes"][value="bancas"]');

    // Bloque C: Cruces peatonales
    await page.check('input[name="cruce_peatonal_todas"][value="no"]');
    await page.check('input[name="seguridad_cruzar_interseccion"][value="neutral"]');
    await page.check('input[name="hay_semaforo_peatonal"][value="si"]');

    // Bloque D: Señalización, accesibilidad y entorno
    await page.check('input[name="mapas_senales_caminata"][value="si"]');
    await page.check('input[name="movilidad_reducida_sin_ayuda"][value="no"]');
    await page.check('input[name="nombres_calles_visibles"][value="no"]');
    await page.check('input[name="senalizacion_clara_sin_obstaculos"][value="no"]');
    await page.check('input[name="trayecto_pie_parada_seguro"][value="bastante_seguro"]');
    await page.check('input[name="aire_ruido_aceptables"][value="no"]');
    await page.check('input[name="conductores_ceden_paso"][value="si"]');
    await page.check('input[name="ciudad_prioriza_peaton"][value="no"]');
    await page.check('input[name="participacion_consultas_peatonales"][value="no"]');
    await page.check('input[name="planes_movilidad_peatonal_normativa"][value="no"]');

    // Observaciones finales
    await page.fill('#observaciones_generales', 'Se requiere mayor frecuencia en rutas y señalización visible en paradas principales.');

    await tracker.checkHorizontalOverflow('Paso 8: Cierre y Esparcimiento');

    // Botón de Envío Definitivo
    const btnEnviar = page.locator('.submit-final-btn');
    await expect(btnEnviar).toBeVisible();

    // Enviar y verificar confirmación
    await btnEnviar.click();

    // Verificar pantalla de éxito
    const successCard = page.locator('.success-card');
    await expect(successCard).toBeVisible({ timeout: 10000 });
    await expect(page.locator('.success-title')).toContainText('Registrada Exitosamente');

    // Comprobar que no hubo fallos críticos en la consola ni excepciones
    const findings = tracker.getFindings();
    const bugs = findings.filter((f) => f.type === 'BUG');
    if (bugs.length > 0) {
      console.warn('Bugs encontrados en Flujo Ciudadano:', JSON.stringify(bugs, null, 2));
    }
    expect(bugs, 'No deben ocurrir bugs de JavaScript ni errores HTTP 500 durante el llenado').toHaveLength(0);
  });
});
