import { Page, expect } from '@playwright/test';
import type { SurveyArchetype } from './survey-archetypes';
import { AuditTracker } from './audit-tracker';

/**
 * Operador automatizado de acciones paso a paso para el Cuestionario PDUL.
 * Verifica visibilidad de ramas condicionales v-if y valida ergonomía táctil.
 */
export class SurveyBotOperator {
  constructor(private page: Page, private tracker: AuditTracker) {}

  async navigateToSurvey() {
    await this.page.goto('/');
    await this.page.waitForLoadState('networkidle');
    await expect(this.page.locator('.header-pdul-title')).toBeVisible();
    await this.tracker.checkHorizontalOverflow('Carga Inicial Cuestionario');
  }

  async nextStep(expectedNextStepTitle?: string) {
    const btnSiguiente = this.page.locator('button:has-text("Siguiente")');
    await expect(btnSiguiente).toBeVisible();
    await btnSiguiente.click();
    await this.page.waitForTimeout(350);
    if (expectedNextStepTitle) {
      await expect(this.page.locator('.step-title')).toContainText(expectedNextStepTitle);
    }
  }

  // =========================================================================
  // PASO 1: Ubicación y Residencia
  // =========================================================================
  async fillPaso1(data: SurveyArchetype['paso1']) {
    await this.page.selectOption('#parroquia', data.parroquia);
    await this.page.fill('#comunidad_sector', data.comunidad_sector);
    await this.page.fill('#zona_residencia_od', data.zona_residencia_od);
    await this.page.fill('#avenida_calle', data.avenida_calle);
    await this.page.fill('#casa_apartamento', data.casa_apartamento);
    await this.tracker.checkHorizontalOverflow('Paso 1: Ubicación');
  }

  // =========================================================================
  // PASO 2: Vivienda y Bifurcación "Otro"
  // =========================================================================
  async fillPaso2(data: SurveyArchetype['paso2']) {
    const radio = this.page.locator(`input[name="tipo_vivienda"][value="${data.tipo_vivienda}"]`);
    await radio.check();

    const campoOtro = this.page.locator('#tipo_vivienda_otro');
    if (data.tipo_vivienda === 'otro') {
      await expect(campoOtro).toBeVisible();
      if (data.tipo_vivienda_otro) {
        await campoOtro.fill(data.tipo_vivienda_otro);
      }
    } else {
      await expect(campoOtro).toHaveCount(0);
    }

    await this.page.fill('#total_cuartos_vivienda', data.total_cuartos_vivienda);
    await this.tracker.checkHorizontalOverflow('Paso 2: Vivienda');
  }

  // =========================================================================
  // PASO 3: Hogar y Tenencia
  // =========================================================================
  async fillPaso3(data: SurveyArchetype['paso3']) {
    await this.page.fill('#grupos_gastos_separados', data.grupos_gastos_separados);
    await this.page.fill('#hogar_numero', data.hogar_numero);
    await this.page.fill('#cuartos_dormir_hogar', data.cuartos_dormir_hogar);
    await this.page.fill('#numero_personas_hogar', data.numero_personas_hogar);

    const radioTenencia = this.page.locator(`input[name="tenencia_vivienda"][value="${data.tenencia_vivienda}"]`);
    await radioTenencia.check();

    const campoOtraTenencia = this.page.locator('#tenencia_vivienda_otro');
    if (data.tenencia_vivienda === 'otra_forma') {
      await expect(campoOtraTenencia).toBeVisible();
      if (data.tenencia_vivienda_otra) {
        await campoOtraTenencia.fill(data.tenencia_vivienda_otra);
      }
    } else {
      await expect(campoOtraTenencia).toHaveCount(0);
    }

    await this.tracker.checkHorizontalOverflow('Paso 3: Hogar');
  }

  // =========================================================================
  // PASO 4: Residentes y Bifurcación Vehicular
  // =========================================================================
  async fillPaso4(residentes: SurveyArchetype['paso4']) {
    const btnAgregar = this.page.locator('.add-residente-btn');

    for (let i = 0; i < residentes.length; i++) {
      const r = residentes[i];
      await this.page.fill('#residente-nombre', r.nombre);
      await this.page.selectOption('#residente-parentesco', r.parentesco);
      await this.page.selectOption('#residente-sexo', r.sexo);
      await this.page.fill('#residente-edad', r.edad);
      await this.page.selectOption('#residente-sabe-leer', r.sabe_leer);
      await this.page.selectOption('#residente-nivel-educativo', r.nivel_educativo);
      await this.page.selectOption('#residente-actividad', r.actividad);
      await this.page.selectOption('#residente-medio-transporte', r.medio_transporte);
      await this.page.selectOption('#residente-licencia', r.licencia);
      await this.page.selectOption('#residente-vehiculo-disp', r.vehiculo_disp);

      const selectTipoVehiculo = this.page.locator('#residente-tipo-vehiculo');
      const inputCantVehiculo = this.page.locator('#residente-cantidad-vehiculo');

      if (r.vehiculo_disp === 'si') {
        await expect(selectTipoVehiculo).toBeVisible();
        await expect(inputCantVehiculo).toBeVisible();
        if (r.tipo_vehiculo) {
          await selectTipoVehiculo.selectOption(r.tipo_vehiculo);
        }
        if (r.cantidad_vehiculo) {
          await inputCantVehiculo.fill(r.cantidad_vehiculo);
        }
      } else {
        await expect(selectTipoVehiculo).toHaveCount(0);
        await expect(inputCantVehiculo).toHaveCount(0);
      }

      await btnAgregar.click();
      await this.page.waitForTimeout(300);
    }

    await expect(this.page.locator('.residente-card')).toHaveCount(residentes.length);
    await this.tracker.checkHorizontalOverflow('Paso 4: Residentes');
  }

  // =========================================================================
  // PASO 5: Viajes Cotidianos y Horarios en la Misma Fila (.horarios-grid-row)
  // =========================================================================
  async fillPaso5(viajes: SurveyArchetype['paso5']) {
    const btnAgregarViaje = this.page.locator('.add-viaje-btn');

    // 1. Auditoría estricta de disposición: ambos inputs de hora deben residir en .horarios-grid-row
    const horariosRow = this.page.locator('.horarios-grid-row');
    await expect(horariosRow).toBeVisible();
    await expect(horariosRow.locator('#viaje-hora-salida-h')).toBeVisible();
    await expect(horariosRow.locator('#viaje-hora-llegada-h')).toBeVisible();

    for (let i = 0; i < viajes.length; i++) {
      const v = viajes[i];
      await this.page.selectOption('#viaje-persona', String(v.persona_numero));
      await this.page.fill('#viaje-origen-dir', v.origen_dir);
      await this.page.fill('#viaje-origen', v.origen_zona);
      await this.page.fill('#viaje-destino-dir', v.destino_dir);
      await this.page.fill('#viaje-destino', v.destino_zona);

      // Llenado de horas en la misma fila
      await this.page.selectOption('#viaje-hora-salida-h', v.hora_salida_h);
      await this.page.selectOption('#viaje-hora-salida-m', v.hora_salida_m);
      await this.page.selectOption('#viaje-hora-salida-periodo', v.hora_salida_periodo);

      await this.page.selectOption('#viaje-hora-llegada-h', v.hora_llegada_h);
      await this.page.selectOption('#viaje-hora-llegada-m', v.hora_llegada_m);
      await this.page.selectOption('#viaje-hora-llegada-periodo', v.hora_llegada_periodo);

      // Motivo y bifurcación otro
      await this.page.selectOption('#viaje-motivo', v.motivo);
      const campoMotivoOtro = this.page.locator('#viaje-motivo-otro');
      if (v.motivo === '8') {
        await expect(campoMotivoOtro).toBeVisible();
        if (v.motivo_otro) await campoMotivoOtro.fill(v.motivo_otro);
      } else {
        await expect(campoMotivoOtro).toHaveCount(0);
      }

      // Modo principal y bifurcación otro
      await this.page.selectOption('#viaje-modo', v.modo_principal);
      const campoModoOtro = this.page.locator('#viaje-modo-otro');
      if (v.modo_principal === '8') {
        await expect(campoModoOtro).toBeVisible();
        if (v.modo_principal_otro) await campoModoOtro.fill(v.modo_principal_otro);
      } else {
        await expect(campoModoOtro).toHaveCount(0);
      }

      // Modo secundario y bifurcación otro
      if (v.modo_secundario !== undefined) {
        await this.page.selectOption('#viaje-modo-sec', v.modo_secundario);
        const campoModoSecOtro = this.page.locator('#viaje-modo-sec-otro');
        if (v.modo_secundario === '8') {
          await expect(campoModoSecOtro).toBeVisible();
          if (v.modo_secundario_otro) await campoModoSecOtro.fill(v.modo_secundario_otro);
        } else {
          await expect(campoModoSecOtro).toHaveCount(0);
        }
      }

      await this.page.fill('#viaje-tiempo', v.tiempo_min);
      await this.page.fill('#viaje-costo', v.costo_bs);

      await btnAgregarViaje.click();
      await this.page.waitForTimeout(300);

      // Prueba opcional de acción rápida de regreso
      if (v.probar_regreso_rapido) {
        const btnRegreso = this.page.locator('.action-btn.return-btn').first();
        if (await btnRegreso.isVisible()) {
          await btnRegreso.click();
          await this.page.waitForTimeout(300);
        }
      }

      // Prueba opcional de modal de detalles
      if (v.probar_modal_detalles) {
        const btnDetalles = this.page.locator('.action-btn.details-btn').first();
        await btnDetalles.click();
        await this.page.waitForTimeout(250);

        const modalHorarios = this.page.locator('.detail-horarios-row');
        await expect(modalHorarios).toBeVisible();
        await expect(modalHorarios).toContainText(v.hora_salida_h);

        const btnCerrarModal = this.page.locator('.modal-close-btn');
        await btnCerrarModal.click();
        await this.page.waitForTimeout(200);
      }
    }

    await this.tracker.checkHorizontalOverflow('Paso 5: Viajes');
  }

  // =========================================================================
  // PASO 6: Transporte Público y Dificultades Condicionales
  // =========================================================================
  async fillPaso6(data: SurveyArchetype['paso6']) {
    await this.page.fill('#rutas_tp_dia', data.rutas_tp_dia);
    await this.page.fill('#tiempo_espera_paradas_min', data.tiempo_espera_paradas_min);
    await this.page.fill('#km_residencia_parada', data.km_residencia_parada);

    const radioDificultad = this.page.locator(`input[name="dificultades_acceso_tp"][value="${data.dificultades_acceso_tp}"]`);
    await radioDificultad.check();

    const fieldsetDificultad = this.page.locator('fieldset:has(legend:has-text("principal dificultad"))');
    const campoDificultadOtro = this.page.locator('#principal_dificultad_tp_otro');

    if (data.dificultades_acceso_tp === 'si') {
      await expect(fieldsetDificultad).toBeVisible();
      if (data.principal_dificultad_tp) {
        await this.page.check(`input[name="principal_dificultad_tp"][value="${data.principal_dificultad_tp}"]`);
        if (data.principal_dificultad_tp === 'otro') {
          await expect(campoDificultadOtro).toBeVisible();
          if (data.principal_dificultad_tp_otro) {
            await campoDificultadOtro.fill(data.principal_dificultad_tp_otro);
          }
        } else {
          await expect(campoDificultadOtro).toHaveCount(0);
        }
      }
    } else {
      await expect(fieldsetDificultad).toHaveCount(0);
      await expect(campoDificultadOtro).toHaveCount(0);
    }

    await this.page.check(`input[name="calificacion_servicio_tp"][value="${data.calificacion_servicio_tp}"]`);
    await this.page.fill('#gasto_semanal_transporte_bs', data.gasto_semanal_transporte_bs);
    await this.page.check(`input[name="acuerdo_rutas_directas"][value="${data.acuerdo_rutas_directas}"]`);
    await this.page.fill('#comentarios_transporte_maturin', data.comentarios_transporte_maturin);

    await this.tracker.checkHorizontalOverflow('Paso 6: Transporte Público');
  }

  // =========================================================================
  // PASO 7: Movilidad Activa y Motivo de Cambio Condicional
  // =========================================================================
  async fillPaso7(data: SurveyArchetype['paso7']) {
    const radioCambio = this.page.locator(`input[name="cambio_movilidad_5_anos"][value="${data.cambio_movilidad_5_anos}"]`);
    await radioCambio.check();

    const fieldsetMotivo = this.page.locator('fieldset:has(legend:has-text("por qué motivo"))');
    const campoMotivoOtro = this.page.locator('#motivo_cambio_desplazamiento_otro');

    if (data.cambio_movilidad_5_anos === 'si') {
      await expect(fieldsetMotivo).toBeVisible();
      if (data.motivo_cambio_desplazamiento) {
        await this.page.check(`input[name="motivo_cambio_desplazamiento"][value="${data.motivo_cambio_desplazamiento}"]`);
        if (data.motivo_cambio_desplazamiento === 'otro') {
          await expect(campoMotivoOtro).toBeVisible();
          if (data.motivo_cambio_desplazamiento_otro) {
            await campoMotivoOtro.fill(data.motivo_cambio_desplazamiento_otro);
          }
        } else {
          await expect(campoMotivoOtro).toHaveCount(0);
        }
      }
    } else {
      await expect(fieldsetMotivo).toHaveCount(0);
      await expect(campoMotivoOtro).toHaveCount(0);
    }

    await this.page.check(`input[name="caminatas_mas_10min"][value="${data.caminatas_mas_10min}"]`);
    await this.page.check(`input[name="usa_bicicleta"][value="${data.usa_bicicleta}"]`);
    await this.page.fill('#dias_camina_bici_semana', data.dias_camina_bici_semana);
    await this.page.check(`input[name="modo_actividades_centro"][value="${data.modo_actividades_centro}"]`);
    await this.page.check(`input[name="aceras_adecuadas"][value="${data.aceras_adecuadas}"]`);
    await this.page.check(`input[name="seguridad_desplazamiento_centro"][value="${data.seguridad_desplazamiento_centro}"]`);

    await this.tracker.checkHorizontalOverflow('Paso 7: Movilidad Activa');
  }

  // =========================================================================
  // PASO 8: Esparcimiento, Calidad del Entorno y Envío Final
  // =========================================================================
  async fillPaso8(data: SurveyArchetype['paso8']) {
    await this.page.check(`input[name="frecuencia_visita_parques"][value="${data.frecuencia_visita_parques}"]`);

    // Checkboxes actividades en parques
    for (const act of data.actividades_parques) {
      await this.page.check(`input[name="actividades_parques"][value="${act}"]`);
    }
    const campoActOtro = this.page.locator('#actividades_parques_otras');
    if (data.actividades_parques.includes('otras')) {
      await expect(campoActOtro).toBeVisible();
      if (data.actividades_parques_otras) await campoActOtro.fill(data.actividades_parques_otras);
    } else {
      await expect(campoActOtro).toHaveCount(0);
    }

    await this.page.check(`input[name="caminatas_ciudad"][value="${data.caminatas_ciudad}"]`);
    await this.page.check(`input[name="seguridad_parques_dia"][value="${data.seguridad_parques_dia}"]`);
    await this.page.check(`input[name="seguridad_parques_noche"][value="${data.seguridad_parques_noche}"]`);
    await this.page.check(`input[name="limpieza_parques"][value="${data.limpieza_parques}"]`);

    // Checkboxes impedimentos
    for (const imp of data.impedimentos_espacios) {
      await this.page.check(`input[name="impedimentos_espacios"][value="${imp}"]`);
    }
    const campoImpOtro = this.page.locator('#impedimentos_espacios_otras');
    if (data.impedimentos_espacios.includes('otras')) {
      await expect(campoImpOtro).toBeVisible();
      if (data.impedimentos_espacios_otras) await campoImpOtro.fill(data.impedimentos_espacios_otras);
    } else {
      await expect(campoImpOtro).toHaveCount(0);
    }

    await this.page.check(`input[name="satisfaccion_centro"][value="${data.satisfaccion_centro}"]`);

    // Checkboxes mejoras prioritarias
    for (const mej of data.mejoras_prioritarias) {
      await this.page.check(`input[name="mejoras_prioritarias"][value="${mej}"]`);
    }
    const campoMejOtro = this.page.locator('#mejoras_prioritarias_otro');
    if (data.mejoras_prioritarias.includes('otro')) {
      await expect(campoMejOtro).toBeVisible();
      if (data.mejoras_prioritarias_otro) await campoMejOtro.fill(data.mejoras_prioritarias_otro);
    } else {
      await expect(campoMejOtro).toHaveCount(0);
    }

    await this.page.fill('#parque_mejorar_primero', data.parque_mejorar_primero);
    await this.page.check(`input[name="disposicion_participar_mejoras"][value="${data.disposicion_participar_mejoras}"]`);
    await this.page.fill('#sugerencias_esparcimiento', data.sugerencias_esparcimiento);

    await this.page.check(`input[name="acera_comoda"][value="${data.acera_comoda}"]`);
    await this.page.fill('#sectores_para_caminar', data.sectores_para_caminar);
    await this.page.check(`input[name="facilidad_llegada_parques"][value="${data.facilidad_llegada_parques}"]`);

    // Checkboxes esparcimientos faltantes
    for (const esp of data.esparcimientos_faltantes) {
      await this.page.check(`input[name="esparcimientos_faltantes"][value="${esp}"]`);
    }
    const campoEspOtro = this.page.locator('#esparcimientos_faltantes_otros');
    if (data.esparcimientos_faltantes.includes('otros')) {
      await expect(campoEspOtro).toBeVisible();
      if (data.esparcimientos_faltantes_otros) await campoEspOtro.fill(data.esparcimientos_faltantes_otros);
    } else {
      await expect(campoEspOtro).toHaveCount(0);
    }

    // Cruces peatonales en todas partes
    await this.page.check(`input[name="cruce_peatonal_todas"][value="${data.cruce_peatonal_todas}"]`);
    const fieldsetCruceDemarcado = this.page.locator('fieldset:has(legend:has-text("¿Está demarcado y visible?"))');
    if (data.cruce_peatonal_todas === 'si') {
      await expect(fieldsetCruceDemarcado).toBeVisible();
      await this.page.check('input[name="cruce_demarcado_visible"][value="si"]');
    } else {
      await expect(fieldsetCruceDemarcado).toHaveCount(0);
    }

    if (data.seguridad_cruzar_interseccion) {
      await this.page.check(`input[name="seguridad_cruzar_interseccion"][value="${data.seguridad_cruzar_interseccion}"]`);
    }

    await this.page.check(`input[name="hay_semaforo_peatonal"][value="${data.hay_semaforo_peatonal}"]`);
    await this.page.check(`input[name="mapas_senales_caminata"][value="${data.mapas_senales_caminata}"]`);
    await this.page.check(`input[name="movilidad_reducida_sin_ayuda"][value="${data.movilidad_reducida_sin_ayuda}"]`);
    await this.page.check(`input[name="nombres_calles_visibles"][value="${data.nombres_calles_visibles}"]`);
    await this.page.check(`input[name="senalizacion_clara_sin_obstaculos"][value="${data.senalizacion_clara_sin_obstaculos}"]`);
    await this.page.check(`input[name="trayecto_pie_parada_seguro"][value="${data.trayecto_pie_parada_seguro}"]`);
    await this.page.check(`input[name="aire_ruido_aceptables"][value="${data.aire_ruido_aceptables}"]`);
    await this.page.check(`input[name="conductores_ceden_paso"][value="${data.conductores_ceden_paso}"]`);
    await this.page.check(`input[name="ciudad_prioriza_peaton"][value="${data.ciudad_prioriza_peaton}"]`);
    await this.page.check(`input[name="participacion_consultas_peatonales"][value="${data.participacion_consultas_peatonales}"]`);
    await this.page.check(`input[name="planes_movilidad_peatonal_normativa"][value="${data.planes_movilidad_peatonal_normativa}"]`);

    await this.page.fill('#observaciones_generales', data.observaciones_generales);
    await this.tracker.checkHorizontalOverflow('Paso 8: Esparcimiento y Cierre');
  }

  // =========================================================================
  // Envío Definitivo y Verificación de Éxito
  // =========================================================================
  async submitAndVerifySuccess() {
    const btnEnviar = this.page.locator('.submit-final-btn');
    await expect(btnEnviar).toBeVisible();
    await btnEnviar.click();

    const successCard = this.page.locator('.success-card');
    await expect(successCard).toBeVisible({ timeout: 12000 });
    await expect(this.page.locator('.success-title')).toContainText('Registrada Exitosamente');
  }
}
