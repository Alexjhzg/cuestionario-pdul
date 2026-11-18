import fs from 'node:fs/promises';
import { test, expect } from '../../../frontend/node_modules/@playwright/test/index.mjs';

const CANONICAL_SURVEY_ID = '00000000-0000-0000-0000-000000000001';

const FORBIDDEN_INITIAL_CHUNK_PATTERN =
  /echarts|zrender|leaflet|formio|DashboardView|FormBuilderView|AdminSurveyListView|AdminResponsesView/i;

const FORBIDDEN_INITIAL_BODY_SIGNATURES = [
  'zrender',
  'echarts',
  'echartsInstance',
  'zrenderVersion',
  'registerTheme',
  'leaflet-container',
  'tileLayer',
  'formio-builder',
  'Dashboard de Movilidad Urbana',
  'Constructor Visual de Encuestas',
  'Respuestas Ciudadanas Recibidas',
  'Total de Encuestas',
];

function stripViteDynamicManifest(jsBody) {
  return jsBody
    .replace(/["'](?:\.?\/)?assets\/[^"']+\.(?:js|css)["']/g, '""')
    .replace(/import\s*\(\s*["']\.\/[^"']+["']\s*\)/g, 'import("")');
}

function isLocalhostUrl(rawUrl) {
  try {
    const parsed = new URL(rawUrl);
    return (
      parsed.protocol === 'data:' ||
      parsed.protocol === 'blob:' ||
      parsed.hostname === '127.0.0.1' ||
      parsed.hostname === 'localhost'
    );
  } catch {
    return true;
  }
}

test.describe('Citizen Mobile Journeys (360x740)', () => {
  test.use({
    viewport: { width: 360, height: 740 },
    isMobile: true,
    hasTouch: true,
  });

  test('T4-01: Citizen mobile load isolates heavy chunks and has zero overflow', async ({ page }) => {
    const assetResponses = [];
    const jsBodyChecks = [];
    const externalRequests = [];

    page.on('request', (req) => {
      if (!isLocalhostUrl(req.url())) {
        externalRequests.push(req.url());
      }
    });

    page.on('response', (resp) => {
      const url = resp.url();
      if (/\.(?:js|mjs|css)(?:\?|$)/i.test(url)) {
        assetResponses.push({ url, status: resp.status() });
      }
      if (/\.(?:js|mjs)(?:\?|$)/i.test(url) && resp.status() === 200) {
        jsBodyChecks.push(
          resp
            .text()
            .then((body) => ({ url, body }))
            .catch(() => ({ url, body: '' }))
        );
      }
    });

    await page.goto('/', { waitUntil: 'networkidle' });
    const downloadedJsBodies = await Promise.all(jsBodyChecks);

    await expect(page.locator('.wizard-title')).toBeVisible();
    await expect(page.locator('.app-nav')).toHaveCount(0);
    await expect(page.locator('.header-admin-badge')).toHaveCount(0);
    await expect(page.locator('#parroquia')).toBeVisible();

    const overflow = await page.evaluate(() => ({
      scrollWidth: document.documentElement.scrollWidth,
      innerWidth: window.innerWidth,
    }));
    expect(overflow.scrollWidth).toBeLessThanOrEqual(overflow.innerWidth);

    expect(externalRequests).toEqual([]);
    expect(assetResponses.length).toBeGreaterThan(0);

    const leakedAssets = assetResponses.filter((a) =>
      FORBIDDEN_INITIAL_CHUNK_PATTERN.test(a.url)
    );
    expect(leakedAssets).toEqual([]);

    expect(downloadedJsBodies.length).toBeGreaterThan(0);
    for (const { url, body } of downloadedJsBodies) {
      const sanitized = stripViteDynamicManifest(body);
      for (const sig of FORBIDDEN_INITIAL_BODY_SIGNATURES) {
        expect(sanitized, `Initial JS asset ${url} must not bundle "${sig}"`).not.toContain(sig);
      }
    }
  });

  test('T4-02: Citizen completes 8-step survey with ViajesMobileCards chaining, return trip, modal & submit', async ({
    page,
  }) => {
    await page.addInitScript(() => {
      window.localStorage.clear();
    });

    await page.goto('/', { waitUntil: 'networkidle' });
    await expect(page.locator('.wizard-title')).toBeVisible();

    // Step 1 validation error before filling
    await page.getByRole('button', { name: 'Siguiente' }).click();
    await expect(page.locator('.wizard-error-banner[role="alert"]')).toBeVisible();

    // Fill Step 1
    await page.locator('#parroquia').selectOption('san_simon');
    await page.locator('#comunidad_sector').fill('Las Brisas');
    await page.locator('#zona_residencia_od').fill('Z-01');
    await page.locator('#avenida_calle').fill('Av. Bolívar');
    await page.locator('#casa_apartamento').fill('Casa 12');
    await page.getByRole('button', { name: 'Siguiente' }).click();

    // Fill Step 2
    await page.locator('input[name="tipo_vivienda"][value="casa"]').check();
    await page.locator('#total_cuartos_vivienda').fill('4');
    await page.getByRole('button', { name: 'Siguiente' }).click();

    // Fill Step 3
    await page.locator('#grupos_gastos_separados').fill('1');
    await page.locator('#hogar_numero').fill('1');
    await page.locator('#cuartos_dormir_hogar').fill('2');
    await page.locator('#numero_personas_hogar').fill('1');
    await page.locator('input[name="tenencia_vivienda"][value="propia_pagada"]').check();
    await page.getByRole('button', { name: 'Siguiente' }).click();

    // Fill Step 4 (ResidentesCards)
    await expect(page.locator('#titulo-residentes')).toBeVisible();
    await page.locator('#residente-nombre').fill('María Pérez');
    await page.locator('#residente-parentesco').selectOption('1');
    await page.locator('#residente-sexo').selectOption('2');
    await page.locator('#residente-edad').fill('34');
    await page.locator('#residente-sabe-leer').selectOption('si');
    await page.locator('#residente-nivel-educativo').selectOption('universitario');
    await page.locator('#residente-actividad').selectOption('1');
    await page.locator('#residente-medio-transporte').selectOption('6');
    await page.locator('#residente-licencia').selectOption('si');
    await page.locator('#residente-vehiculo-disp').selectOption('no');
    await page.locator('.add-residente-btn').click();
    await expect(page.locator('.residente-card[role="listitem"]')).toHaveCount(1);
    await page.getByRole('button', { name: 'Siguiente' }).click();

    // Step 5 (ViajesMobileCards)
    await expect(page.locator('#titulo-viajes-od')).toBeVisible();

    // Empty trip validation error
    await page.locator('.add-viaje-btn').click();
    await expect(page.locator('.form-error-banner[role="alert"]')).toBeVisible();

    // Fill trip with invalid tiempo=0 first
    await page.locator('#viaje-persona').selectOption('1');
    await page.locator('#viaje-origen-dir').fill('Av. Bolívar, Casa 12');
    await page.locator('#viaje-origen').fill('san_simon');
    await page.locator('#viaje-destino-dir').fill('Centro Comercial');
    await page.locator('#viaje-destino').fill('boqueron');
    await page.locator('#viaje-hora-salida-h').selectOption('07');
    await page.locator('#viaje-hora-salida-m').selectOption('30');
    await page.locator('#viaje-hora-salida-periodo').selectOption('AM');
    await page.locator('#viaje-hora-llegada-h').selectOption('08');
    await page.locator('#viaje-hora-llegada-m').selectOption('05');
    await page.locator('#viaje-hora-llegada-periodo').selectOption('AM');
    await page.locator('#viaje-motivo').selectOption('1');
    await page.locator('#viaje-modo').selectOption('6');
    await page.locator('#viaje-tiempo').fill('0');
    await page.locator('#viaje-costo').fill('15');
    await page.locator('.add-viaje-btn').click();
    await expect(page.locator('.form-error-banner[role="alert"]')).toBeVisible();

    // Fix tiempo=35 and add trip
    await page.locator('#viaje-tiempo').fill('35');
    await page.locator('.add-viaje-btn').click();

    await expect(page.locator('.viaje-card[role="listitem"]')).toHaveCount(1);
    await expect(page.locator('#titulo-viajes-od')).toContainText('(1)');

    // Verify no mobile horizontal overflow on ViajesMobileCards
    const step5Overflow = await page.evaluate(() => ({
      scrollWidth: document.documentElement.scrollWidth,
      innerWidth: window.innerWidth,
    }));
    expect(step5Overflow.scrollWidth).toBeLessThanOrEqual(step5Overflow.innerWidth);

    // Verify origin chaining into next trip form
    await expect(page.locator('#viaje-origen-dir')).toHaveValue('Centro Comercial');
    await expect(page.locator('#viaje-origen')).toHaveValue('boqueron');
    await expect(page.locator('#viaje-destino')).toHaveValue('');

    // 1-tap return trip
    await page.locator('.viaje-card .return-btn').first().click();
    await expect(page.locator('.viaje-card[role="listitem"]')).toHaveCount(2);
    await expect(page.locator('#titulo-viajes-od')).toContainText('(2)');

    // Detail modal ("Ver más" -> "Cerrar")
    await page.locator('.viaje-card .details-btn').first().click();
    const viajeModal = page.locator('[role="dialog"][aria-labelledby="modal-viaje-title"]');
    await expect(viajeModal).toBeVisible();
    await viajeModal.getByRole('button', { name: 'Cerrar' }).first().click();
    await expect(viajeModal).toHaveCount(0);

    // Delete second trip
    await page.locator('.viaje-card .delete-btn').nth(1).click();
    await expect(page.locator('.viaje-card[role="listitem"]')).toHaveCount(1);

    await page.getByRole('button', { name: 'Siguiente' }).click();

    // Step 6
    await page.locator('#rutas_tp_dia').fill('1');
    await page.locator('#tiempo_espera_paradas_min').fill('10');
    await page.locator('#km_residencia_parada').fill('0.5');
    await page.locator('input[name="dificultades_acceso_tp"][value="no"]').check();
    await page.locator('input[name="calificacion_servicio_tp"][value="bueno"]').check();
    await page.locator('#gasto_semanal_transporte_bs').fill('120');
    await page.locator('input[name="acuerdo_rutas_directas"][value="de_acuerdo"]').check();
    await page.locator('#comentarios_transporte_maturin').fill('Mejorar frecuencia');
    await page.getByRole('button', { name: 'Siguiente' }).click();

    // Step 7
    await page.locator('input[name="cambio_movilidad_5_anos"][value="no"]').check();
    await page.locator('input[name="caminatas_mas_10min"][value="si"]').check();
    await page.locator('input[name="usa_bicicleta"][value="no"]').check();
    await page.locator('#dias_camina_bici_semana').fill('5');
    await page.locator('input[name="modo_actividades_centro"][value="transporte_publico"]').check();
    await page.locator('input[name="aceras_adecuadas"][value="no"]').check();
    await page.locator('input[name="seguridad_desplazamiento_centro"][value="neutral"]').check();
    await page.getByRole('button', { name: 'Siguiente' }).click();

    // Step 8
    await page.locator('input[name="frecuencia_visita_parques"][value="semanal"]').check();
    await page.locator('input[name="actividades_parques"][value="caminar"]').check();
    await page.locator('input[name="caminatas_ciudad"][value="a_veces"]').check();
    await page.locator('input[name="seguridad_parques_dia"][value="bastante_seguro"]').check();
    await page.locator('input[name="seguridad_parques_noche"][value="poco_seguro"]').check();
    await page.locator('input[name="limpieza_parques"][value="regular"]').check();
    await page.locator('input[name="impedimentos_espacios"][value="falta_tiempo"]').check();
    await page.locator('input[name="satisfaccion_centro"][value="neutral"]').check();
    await page.locator('input[name="mejoras_prioritarias"][value="iluminacion"]').check();
    await page.locator('#parque_mejorar_primero').fill('Parque La Guaricha');
    await page.locator('input[name="disposicion_participar_mejoras"][value="si"]').check();
    await page.locator('#sugerencias_esparcimiento').fill('Más iluminación');
    await page.locator('input[name="acera_comoda"][value="en_desacuerdo"]').check();
    await page.locator('#sectores_para_caminar').fill('Av. Bolívar');
    await page.locator('input[name="facilidad_llegada_parques"][value="facil"]').check();
    await page.locator('input[name="esparcimientos_faltantes"][value="iluminacion"]').check();
    await page.locator('input[name="cruce_peatonal_todas"][value="no"]').check();
    await page.locator('input[name="seguridad_cruzar_interseccion"][value="poco_seguro"]').check();
    await page.locator('input[name="hay_semaforo_peatonal"][value="si"]').check();
    await page.locator('input[name="mapas_senales_caminata"][value="no"]').check();
    await page.locator('input[name="movilidad_reducida_sin_ayuda"][value="no"]').check();
    await page.locator('input[name="nombres_calles_visibles"][value="si"]').check();
    await page.locator('input[name="senalizacion_clara_sin_obstaculos"][value="no"]').check();
    await page.locator('input[name="trayecto_pie_parada_seguro"][value="neutral"]').check();
    await page.locator('input[name="aire_ruido_aceptables"][value="si"]').check();
    await page.locator('input[name="conductores_ceden_paso"][value="no"]').check();
    await page.locator('input[name="ciudad_prioriza_peaton"][value="no"]').check();
    await page.locator('input[name="participacion_consultas_peatonales"][value="no"]').check();
    await page.locator('input[name="planes_movilidad_peatonal_normativa"][value="no_sabe"]').check();
    await page.locator('#observaciones_generales').fill('Encuesta móvil E2E completa');
    await expect(page.locator('.declaration-label input[type="checkbox"]')).toBeChecked();

    const submitResponsePromise = page.waitForResponse(
      (res) =>
        res.url().includes('/api/v1/encuestas/') &&
        res.url().endsWith('/respuestas') &&
        res.request().method() === 'POST'
    );
    await page.locator('.submit-final-btn').click();
    const submitResponse = await submitResponsePromise;
    expect(submitResponse.status()).toBe(201);

    await expect(page.locator('.success-card')).toBeVisible();
    await expect(page.locator('h2.success-title')).toContainText('¡Encuesta Registrada Exitosamente!');
  });
});

test.describe('Admin Desktop Lazy Navigation & Export Journeys (1280x720)', () => {
  test.use({
    viewport: { width: 1280, height: 720 },
  });

  test('T4-03: Admin lazy loads DashboardView, AdminSurveyListView, AdminResponsesView & FormBuilderView', async ({
    page,
  }) => {
    // Seed a PII-rich submission so AdminResponsesView & CSV export always inspect real PII
    const seedRes = await page.request.post(
      `/api/v1/encuestas/${CANONICAL_SURVEY_ID}/respuestas`,
      {
        data: {
          client_submission_id: '55555555-5555-4555-8555-555555555555',
          data: {
            parroquia: 'alto_de_los_godos',
            zona_residencia_od: 'Z-02',
            cedula: '19888777',
            nombre_apellido: 'Pedro Secreto',
            telefono: '0414-9998877',
            correo: 'pedro.secreto@ejemplo.ve',
            direccion_exacta: 'Calle Secreta 42',
            residentes: [
              {
                persona_numero: 1,
                nombre_apellido: 'Pedro Secreto',
                parentesco: '1',
                sexo: '1',
                edad: 41,
              },
            ],
            viajes: [
              {
                viaje_numero: 1,
                persona_numero: 1,
                origen_direccion: 'Calle Secreta 42',
                zona_od_origen: 'alto_de_los_godos',
                destino_direccion: 'Centro',
                zona_od_destino: 'san_simon',
                motivo_viaje: '1',
                modo_principal: '6',
                tiempo_viaje_min: 30,
                costo_viaje_bs: 10,
              },
            ],
          },
        },
      }
    );
    expect([200, 201]).toContain(seedRes.status());

    // Create a disposable survey to exercise status switch confirm/reactivate safely
    const tempSlug = `e2e_toggle_${Date.now()}`;
    const createTemp = await page.request.post('/api/v1/admin/encuestas', {
      data: {
        titulo: 'Encuesta Temporal Toggle',
        slug: tempSlug,
        tipo_instrumento: 'consulta_ciudadana',
        esquema_formio: { display: 'form', components: [] },
        activa: true,
      },
    });
    expect(createTemp.status()).toBe(201);
    const tempSurvey = await createTemp.json();

    const loadedAssets = [];
    const externalRequests = [];

    page.on('request', (req) => {
      if (!isLocalhostUrl(req.url())) {
        externalRequests.push(req.url());
      }
    });
    page.on('response', (resp) => {
      const url = resp.url();
      if (/\.(?:js|mjs|css)(?:\?|$)/i.test(url)) {
        loadedAssets.push(url);
      }
    });

    // 1. DashboardView (/?admin=true)
    await page.goto('/?admin=true', { waitUntil: 'networkidle' });
    await expect(page.locator('.header-admin-badge')).toBeVisible();
    await expect(page.locator('nav.app-nav')).toBeVisible();
    await expect(page.locator('#panel-gis-dashboard h1.header-title')).toBeVisible();
    await expect(page.locator('section.section-kpis')).toBeVisible();

    expect(loadedAssets.some((u) => /echarts|zrender/i.test(u))).toBe(true);

    // Filter questions & toggle accessible table
    const searchInput = page.locator('input.questions-search-input');
    if ((await searchInput.count()) > 0) {
      await searchInput.fill('Parroquia');
      await expect(page.locator('button.btn-clear-search')).toBeVisible();
      await page.locator('button.btn-clear-search').click();
    }
    const sectionPills = page.locator('button.section-pill-btn');
    if ((await sectionPills.count()) > 1) {
      await sectionPills.nth(1).click();
      await sectionPills.first().click();
    }
    await page.locator('button.btn-toggle-view').click();
    await expect(page.locator('section.dashboard-accessible-layout')).toBeVisible();
    await page.locator('button.btn-toggle-view').click();

    // 2. AdminSurveyListView (#tab-admin-surveys)
    await page.locator('#tab-admin-surveys').click();
    await expect(page.locator('#panel-admin-surveys #admin-title')).toBeVisible();
    await expect(page.locator(`[data-testid="survey-row-${CANONICAL_SURVEY_ID}"]`)).toBeVisible();

    // Cancel deactivation modal on canonical survey
    const canonicalSwitch = page.locator(`[data-testid="switch-status-${CANONICAL_SURVEY_ID}"]`);
    await canonicalSwitch.click();
    await expect(page.locator('[role="dialog"][aria-labelledby="confirm-dialog-title"]')).toBeVisible();
    await page.locator('[data-testid="btn-cancel-deactivation"]').click();
    await expect(canonicalSwitch).toHaveAttribute('aria-checked', 'true');

    // Confirm deactivation & reactivate on disposable survey
    const tempSwitch = page.locator(`[data-testid="switch-status-${tempSurvey.id}"]`);
    await tempSwitch.click();
    await expect(page.locator('[data-testid="btn-confirm-deactivation"]')).toBeVisible();
    await page.locator('[data-testid="btn-confirm-deactivation"]').click();
    await expect(tempSwitch).toHaveAttribute('aria-checked', 'false');
    await tempSwitch.click();
    await expect(tempSwitch).toHaveAttribute('aria-checked', 'true');

    // Redacted streaming CSV download from AdminSurveyListView
    const redactCheckbox = page.locator('[data-testid="checkbox-redact-pii"]');
    await expect(redactCheckbox).toBeChecked();
    const [csvDownload, csvResponse] = await Promise.all([
      page.waitForEvent('download'),
      page.waitForResponse(
        (res) =>
          res.url().includes(`/api/v1/admin/encuestas/${CANONICAL_SURVEY_ID}/exportar`) &&
          res.url().includes('formato=csv') &&
          res.url().includes('redact_pii=true')
      ),
      page.locator(`[data-testid="btn-export-csv-${CANONICAL_SURVEY_ID}"]`).click(),
    ]);
    expect(csvResponse.status()).toBe(200);
    expect(csvResponse.headers()['content-disposition']).toBe(
      `attachment; filename="encuesta_${CANONICAL_SURVEY_ID}.csv"`
    );
    expect(csvDownload.suggestedFilename()).toMatch(
      /^cuestionario-od-maturin_respuestas_anonimizado_\d{4}-\d{2}-\d{2}\.csv$/
    );
    const csvPath = await csvDownload.path();
    const csvText = await fs.readFile(csvPath, 'utf-8');
    expect(csvText.split('\n')[0]).not.toContain('cedula');
    expect(csvText).not.toContain('Pedro Secreto');
    expect(csvText).not.toContain('19888777');
    expect(csvText).not.toContain('pedro.secreto@ejemplo.ve');

    // Unredacted streaming JSON download when redact_pii checkbox is toggled off
    await redactCheckbox.uncheck();
    await expect(redactCheckbox).not.toBeChecked();
    const [jsonDownload, jsonResponse] = await Promise.all([
      page.waitForEvent('download'),
      page.waitForResponse(
        (res) =>
          res.url().includes(`/api/v1/admin/encuestas/${CANONICAL_SURVEY_ID}/exportar`) &&
          res.url().includes('formato=json') &&
          res.url().includes('redact_pii=false')
      ),
      page.locator(`[data-testid="btn-export-json-${CANONICAL_SURVEY_ID}"]`).click(),
    ]);
    expect(jsonResponse.status()).toBe(200);
    expect(jsonResponse.headers()['content-disposition']).toBe(
      `attachment; filename="encuesta_${CANONICAL_SURVEY_ID}.json"`
    );
    expect(jsonDownload.suggestedFilename()).toMatch(
      /^cuestionario-od-maturin_respuestas_\d{4}-\d{2}-\d{2}\.json$/
    );
    const jsonPath = await jsonDownload.path();
    const jsonExportText = await fs.readFile(jsonPath, 'utf-8');
    const jsonExportRows = JSON.parse(jsonExportText);
    expect(Array.isArray(jsonExportRows)).toBe(true);
    expect(jsonExportRows.length).toBeGreaterThanOrEqual(1);
    expect(jsonExportText).toContain('Pedro Secreto');
    expect(jsonExportText).toContain('19888777');
    await redactCheckbox.check();

    // 3. AdminResponsesView
    await page.locator(`[data-testid="btn-view-responses-${CANONICAL_SURVEY_ID}"]`).click();
    await expect(page.locator('#panel-admin-responses #responses-title')).toBeVisible();
    await expect(page.locator('[data-testid="select-survey-inspect"]')).toHaveValue(CANONICAL_SURVEY_ID);
    await expect(page.locator('[data-testid="pagination-info-text"]')).toBeVisible();

    const firstDetailBtn = page.locator('[data-testid^="btn-detail-"]').first();
    await expect(firstDetailBtn).toBeVisible();
    await firstDetailBtn.click();

    await expect(page.locator('[data-testid="grid-detail-viewer"]')).toBeVisible();
    const maskCheckbox = page.locator('[data-testid="checkbox-mask-pii"]');
    await expect(maskCheckbox).toBeChecked();
    await maskCheckbox.uncheck();
    await expect(page.locator('.pii-warning-banner[role="alert"]')).toBeVisible();

    await page.locator('[data-testid="btn-view-mode-json"]').click();
    const jsonViewerText = await page.locator('[data-testid="json-detail-viewer"]').innerText();
    expect(() => JSON.parse(jsonViewerText)).not.toThrow();
    await page.locator('[data-testid="btn-modal-close"]').click();

    // 4. FormBuilderView (#panel-form-builder)
    await page.locator('#tab-admin-surveys').click();
    const loadSurveyPromise = page.waitForResponse(
      (res) =>
        res.url().includes(`/api/v1/admin/encuestas/${CANONICAL_SURVEY_ID}`) &&
        res.request().method() === 'GET'
    );
    await page.locator(`[data-testid="btn-edit-survey-${CANONICAL_SURVEY_ID}"]`).click();
    const loadSurveyRes = await loadSurveyPromise;
    expect(loadSurveyRes.status()).toBe(200);
    await expect(page.locator('#panel-form-builder h1.view-title')).toBeVisible();

    // Verify @formio/js chunk loaded on demand and zero external CDN calls
    expect(loadedAssets.some((u) => /formio/i.test(u))).toBe(true);
    expect(externalRequests).toEqual([]);

    // Load blank preset and verify schema validation modal opens & closes cleanly
    await page.locator('[data-testid="btn-load-blank"]').click();
    await page.locator('[data-testid="btn-validate-schema"]').click();
    const validationModal = page.locator('[role="dialog"][aria-labelledby="validation-dialog-title"]');
    await expect(validationModal).toBeVisible();
    await expect(page.locator('#validation-dialog-title')).toHaveText(
      /Esquema Válido|Observaciones de Validación/
    );
    await validationModal.getByRole('button', { name: 'Entendido' }).click();
    await expect(validationModal).toHaveCount(0);

    // Load canonical preset and verify local schema JSON export
    await page.locator('[data-testid="btn-load-canonical"]').click();
    await expect(page.locator('[data-testid="input-survey-slug"]')).toHaveValue('pdul_origen_destino');
    const [schemaDownload] = await Promise.all([
      page.waitForEvent('download'),
      page.locator('[data-testid="btn-export-json"]').click(),
    ]);
    expect(schemaDownload.suggestedFilename()).toBe('pdul_origen_destino.json');
    const schemaFilePath = await schemaDownload.path();
    const exportedSchema = JSON.parse(await fs.readFile(schemaFilePath, 'utf-8'));
    expect(Array.isArray(exportedSchema.components)).toBe(true);
    expect(exportedSchema.components.length).toBeGreaterThan(0);
  });
});
