import { isValidParroquia } from '@/utils/validation';
import { isVehiculoParticular } from '@/utils/tripCatalogs';
import type { Residente, ViajeOD } from '@/types/survey';

export function isBlankValue(value: unknown): boolean {
  if (value === undefined || value === null) return true;
  if (typeof value === 'string') return value.trim().length === 0;
  if (Array.isArray(value)) return value.length === 0;
  return false;
}

export function isNumericValue(value: unknown): boolean {
  if (isBlankValue(value)) return false;
  return !isNaN(Number(value));
}

function isFilled(value: unknown): boolean {
  return value !== undefined && value !== null && value !== '';
}

export function calculateStepProgress(stepIdx: number, data: Record<string, any>): number {
  if (!data) return 0;
  switch (stepIdx) {
    case 0: {
      let score = 0;
      if (data.parroquia && String(data.parroquia).trim().length > 0) score += 1.0;
      if (data.comunidad_sector && String(data.comunidad_sector).trim().length > 0) {
        score = Math.min(1, score + 0.1);
      }
      return Math.min(1, score);
    }
    case 1: {
      let filled = 0;
      if (data.tipo_vivienda) filled++;
      if (isFilled(data.total_cuartos_vivienda)) filled++;
      return filled > 0 ? filled / 2 : 0.25;
    }
    case 2: {
      let filled = 0;
      if (isFilled(data.grupos_gastos_separados)) filled++;
      if (isFilled(data.hogar_numero)) filled++;
      if (isFilled(data.cuartos_dormir_hogar)) filled++;
      if (isFilled(data.numero_personas_hogar)) filled++;
      if (data.tenencia_vivienda) filled++;
      return filled > 0 ? filled / 5 : 0.25;
    }
    case 3:
      return Array.isArray(data.residentes) && data.residentes.length > 0 ? 1 : 0.3;
    case 4:
      return Array.isArray(data.viajes) && data.viajes.length > 0 ? 1 : 0.3;
    case 5: {
      let filled = 0;
      if (isFilled(data.rutas_tp_dia)) filled++;
      if (isFilled(data.tiempo_espera_paradas_min)) filled++;
      if (isFilled(data.km_residencia_parada)) filled++;
      if (data.dificultades_acceso_tp) filled++;
      if (data.calificacion_servicio_tp) filled++;
      if (isFilled(data.gasto_semanal_transporte_bs)) filled++;
      if (data.acuerdo_rutas_directas) filled++;
      return filled > 0 ? filled / 7 : 0.25;
    }
    case 6: {
      let filled = 0;
      if (data.cambio_movilidad_5_anos) filled++;
      if (data.caminatas_mas_10min) filled++;
      if (data.usa_bicicleta) filled++;
      if (isFilled(data.dias_camina_bici_semana)) filled++;
      if (data.modo_actividades_centro) filled++;
      if (data.aceras_adecuadas) filled++;
      if (data.seguridad_desplazamiento_centro) filled++;
      return filled > 0 ? filled / 7 : 0.25;
    }
    case 7: {
      let filled = 0;
      if (data.frecuencia_visita_parques) filled++;
      if (data.caminatas_ciudad) filled++;
      if (data.seguridad_parques_dia) filled++;
      if (data.seguridad_parques_noche) filled++;
      if (data.limpieza_parques) filled++;
      if (data.satisfaccion_centro) filled++;
      if (data.acera_comoda) filled++;
      if (data.facilidad_llegada_parques) filled++;
      if (data.cruce_peatonal_todas) filled++;
      if (data.observaciones_generales && String(data.observaciones_generales).trim().length > 0) filled++;
      if (data.acepta_declaracion !== false) filled++;
      return filled > 0 ? filled / 11 : 0.25;
    }
    default:
      return 0;
  }
}

export function getStepErrors(stepIdx: number, data: Record<string, any>): string[] {
  const errors: string[] = [];
  const source = data || {};

  const requireField = (field: string, label: string) => {
    if (isBlankValue(source[field])) errors.push(label);
  };

  const requireNumber = (field: string, label: string, min: number) => {
    if (!isNumericValue(source[field]) || Number(source[field]) < min) errors.push(label);
  };

  const requireMulti = (field: string, label: string) => {
    if (!Array.isArray(source[field]) || source[field].length === 0) errors.push(label);
  };

  switch (stepIdx) {
    case 0: {
      if (!source.parroquia || !isValidParroquia(source.parroquia)) {
        errors.push('1.- Seleccione su parroquia.');
      }
      requireField('comunidad_sector', '2.- Indique su comunidad o sector.');
      requireField('zona_residencia_od', '3.- Indique su zona de residencia (zonificación O-D).');
      requireField('avenida_calle', '4.- Indique la avenida o calle.');
      requireField('casa_apartamento', '5.- Indique la casa o apartamento.');
      break;
    }
    case 1: {
      requireField('tipo_vivienda', '1.- Seleccione el tipo de vivienda.');
      if (source.tipo_vivienda === 'otro') {
        requireField('tipo_vivienda_otro', '1.g.- Especifique el otro tipo de vivienda.');
      }
      requireNumber('total_cuartos_vivienda', '2.- Indique el total de espacios de la vivienda.', 1);
      break;
    }
    case 2: {
      requireNumber('grupos_gastos_separados', '1.- Indique cuántos grupos mantienen gastos separados.', 1);
      requireNumber('hogar_numero', 'Hogar N°: indique el número de hogar.', 1);
      requireNumber('cuartos_dormir_hogar', '2.- Indique cuántos cuartos para dormir utiliza el hogar.', 1);
      requireNumber('numero_personas_hogar', '3.- Indique el número de personas que residen en el hogar.', 1);
      requireField('tenencia_vivienda', '4.- Seleccione la forma de tenencia de la vivienda.');
      if (source.tenencia_vivienda === 'otra_forma') {
        requireField('tenencia_vivienda_otro', '4.h.- Especifique la otra forma de tenencia.');
      }
      break;
    }
    case 3: {
      const residentes: Residente[] = Array.isArray(source.residentes) ? source.residentes : [];
      const esperado = Number(source.numero_personas_hogar);

      if (residentes.length === 0) {
        errors.push('Registre al menos un residente en el hogar.');
      } else if (!isNaN(esperado) && esperado > 0 && residentes.length < esperado) {
        errors.push(
          `Ha registrado ${residentes.length} de ${esperado} integrantes declarados en la Sección III (Pregunta 3). Debe completar los datos de todos los miembros de la familia.`
        );
      }

      residentes.forEach((r, idx) => {
        const prefix = `Residente #${idx + 1}:`;
        if (isBlankValue(r.nombres) && isBlankValue(r.nombre_apellido)) {
          errors.push(`${prefix} indique el nombre y apellido.`);
        }
        if (isBlankValue(r.parentesco) && isBlankValue(r.parentesco_jefe_hogar)) {
          errors.push(`${prefix} seleccione el parentesco con el jefe de hogar.`);
        }
        if (isBlankValue(r.sexo)) errors.push(`${prefix} seleccione el sexo.`);
        if (!isNumericValue(r.edad) || Number(r.edad) < 0 || Number(r.edad) > 120) {
          errors.push(`${prefix} indique una edad válida (0 a 120 años).`);
        }
        if (isBlankValue(r.sabe_leer_escribir)) errors.push(`${prefix} indique si sabe leer y escribir.`);
        if (isBlankValue(r.nivel_educativo)) errors.push(`${prefix} seleccione el nivel educativo.`);
        if (isBlankValue(r.actividad_principal) && isBlankValue(r.ocupacion_principal)) {
          errors.push(`${prefix} seleccione la ocupación o actividad principal.`);
        }
        if (isBlankValue(r.medio_transporte_habitual)) {
          errors.push(`${prefix} seleccione el medio de transporte habitual.`);
        }
        if (isBlankValue(r.posee_licencia)) errors.push(`${prefix} indique si posee licencia de conducir.`);
        if (isBlankValue(r.tiene_vehiculo_disponible)) {
          errors.push(`${prefix} indique si tiene algún vehículo disponible.`);
        } else if (r.tiene_vehiculo_disponible === 'si') {
          if (isBlankValue(r.tipo_vehiculo)) errors.push(`${prefix} seleccione el tipo de vehículo.`);
          if (!isNumericValue(r.cantidad_vehiculo) || Number(r.cantidad_vehiculo) < 1) {
            errors.push(`${prefix} indique la cantidad de vehículos.`);
          }
        }
      });
      break;
    }
    case 4: {
      const viajes: ViajeOD[] = Array.isArray(source.viajes) ? source.viajes : [];
      if (viajes.length === 0) errors.push('Registre al menos un viaje realizado.');

      viajes.forEach((v, idx) => {
        const prefix = `Viaje #${idx + 1}:`;
        if (!isNumericValue(v.persona_numero) || Number(v.persona_numero) < 1) {
          errors.push(`${prefix} seleccione la persona que realizó el viaje.`);
        }
        if (isBlankValue(v.origen_direccion)) errors.push(`${prefix} indique la dirección o referencia de origen.`);
        if (isBlankValue(v.zona_od_origen)) errors.push(`${prefix} indique la zona O-D de origen.`);
        if (isBlankValue(v.destino_direccion)) errors.push(`${prefix} indique la dirección o referencia de destino.`);
        if (isBlankValue(v.zona_od_destino)) errors.push(`${prefix} indique la zona O-D de destino.`);
        if (isBlankValue(v.hora_salida)) errors.push(`${prefix} indique la hora de salida.`);
        if (isBlankValue(v.hora_llegada)) errors.push(`${prefix} indique la hora de llegada.`);
        if (isBlankValue(v.motivo_viaje)) {
          errors.push(`${prefix} seleccione el motivo del viaje.`);
        } else if (v.motivo_viaje === '8' && isBlankValue(v.motivo_viaje_otro)) {
          errors.push(`${prefix} especifique el otro motivo del viaje.`);
        }
        if (isBlankValue(v.modo_principal)) {
          errors.push(`${prefix} seleccione el modo de transporte principal.`);
        } else if (v.modo_principal === '8' && isBlankValue(v.modo_principal_otro)) {
          errors.push(`${prefix} especifique el otro modo de transporte principal.`);
        }
        if (!isVehiculoParticular(v.modo_principal)) {
          if (v.modo_secundario === '8' && isBlankValue(v.modo_secundario_otro)) {
            errors.push(`${prefix} especifique el otro modo de transporte secundario.`);
          }
        }
        if (!isNumericValue(v.tiempo_viaje_min) || Number(v.tiempo_viaje_min) < 1) {
          errors.push(`${prefix} indique el tiempo de viaje en minutos.`);
        }
        if (!isVehiculoParticular(v.modo_principal)) {
          if (!isNumericValue(v.costo_viaje_bs) || Number(v.costo_viaje_bs) < 0) {
            errors.push(`${prefix} indique el costo del viaje (puede ser 0).`);
          }
        }
      });
      break;
    }
    case 5: {
      requireNumber('rutas_tp_dia', '1.- Indique cuántas rutas de transporte público utilizó.', 0);
      requireNumber('tiempo_espera_paradas_min', '2.- Indique el tiempo total de espera en paradas.', 0);
      requireNumber('km_residencia_parada', '3.- Indique los kilómetros desde su residencia hasta la parada.', 0);
      requireField('dificultades_acceso_tp', '4.- Indique si ha tenido dificultades para acceder al transporte público.');
      if (source.dificultades_acceso_tp === 'si') {
        requireField('principal_dificultad_tp', '5.- Seleccione la principal dificultad de acceso.');
        if (source.principal_dificultad_tp === 'otro') {
          requireField('principal_dificultad_tp_otro', '5.e.- Especifique la otra dificultad.');
        }
      }
      requireField('calificacion_servicio_tp', '6.- Califique el servicio de transporte público.');
      requireNumber('gasto_semanal_transporte_bs', '7.- Indique el gasto semanal en transporte.', 0);
      requireField('acuerdo_rutas_directas', '8.- Indique su acuerdo con la creación de rutas directas.');
      requireField('comentarios_transporte_maturin', '9.- Escriba un comentario o sugerencia sobre el transporte en Maturín.');
      break;
    }
    case 6: {
      requireField('cambio_movilidad_5_anos', '1.- Indique si ha cambiado su forma de desplazarse en los últimos 5 años.');
      if (source.cambio_movilidad_5_anos === 'si') {
        requireField('motivo_cambio_desplazamiento', '2.- Seleccione el motivo del cambio de desplazamiento.');
        if (source.motivo_cambio_desplazamiento === 'otro') {
          requireField('motivo_cambio_desplazamiento_otro', '2.e.- Especifique el otro motivo.');
        }
      }
      requireField('caminatas_mas_10min', '3.- Indique si realiza caminatas de más de 10 minutos.');
      requireField('usa_bicicleta', '4.- Indique si utiliza bicicleta como medio de transporte.');
      requireNumber('dias_camina_bici_semana', '5.- Indique cuántos días a la semana camina o usa bicicleta.', 0);
      requireField('modo_actividades_centro', '6.- Indique cómo se desplaza en el centro de la ciudad.');
      requireField('aceras_adecuadas', '7.- Indique si las aceras y espacios peatonales son adecuados.');
      requireField('seguridad_desplazamiento_centro', '8.- Indique qué tan seguro se siente al desplazarse por el centro.');
      break;
    }
    case 7: {
      requireField('frecuencia_visita_parques', '1.- Indique con qué frecuencia visita parques y plazas.');
      requireMulti('actividades_parques', '2.- Seleccione al menos una actividad que realiza en estos espacios.');
      if (Array.isArray(source.actividades_parques) && source.actividades_parques.includes('otras')) {
        requireField('actividades_parques_otras', '2.g.- Especifique las otras actividades.');
      }
      requireField('caminatas_ciudad', '3.- Indique si suele hacer caminatas por la ciudad.');
      requireField('seguridad_parques_dia', '7.- Indique qué tan seguro se siente en parques y rutas peatonales durante el día.');
      requireField('seguridad_parques_noche', '8.- Indique qué tan seguro se siente en parques y rutas peatonales durante la noche.');
      requireField('limpieza_parques', '9.- Califique la limpieza y conservación de las áreas de esparcimiento.');
      requireMulti('impedimentos_espacios', '10.- Seleccione al menos un impedimento para usar estos espacios.');
      if (Array.isArray(source.impedimentos_espacios) && source.impedimentos_espacios.includes('otras')) {
        requireField('impedimentos_espacios_otras', '10.f.- Especifique los otros impedimentos.');
      }
      requireField('satisfaccion_centro', '11.- Indique su satisfacción con las áreas de esparcimiento del centro.');
      requireMulti('mejoras_prioritarias', '12.- Seleccione al menos una mejora prioritaria.');
      if (Array.isArray(source.mejoras_prioritarias) && source.mejoras_prioritarias.includes('otro')) {
        requireField('mejoras_prioritarias_otro', '12.m.- Especifique la otra mejora prioritaria.');
      }
      requireField('parque_mejorar_primero', '13.- Indique qué parque, plaza o ruta debe mejorarse primero.');
      requireField('disposicion_participar_mejoras', '14.- Indique si estaría dispuesto a participar en las mejoras.');
      requireField('sugerencias_esparcimiento', '15.- Escriba una sugerencia para mejorar las áreas de esparcimiento y caminatas.');
      requireField('acera_comoda', '16.- Indique si la acera es suficiente y cómoda para caminar.');
      requireField('sectores_para_caminar', '17.- Indique qué sectores utiliza para caminar.');
      requireField('facilidad_llegada_parques', '18.- Indique qué tan fácil es llegar a las áreas de esparcimiento.');
      requireMulti('esparcimientos_faltantes', '19.- Seleccione al menos un esparcimiento faltante.');
      if (Array.isArray(source.esparcimientos_faltantes) && source.esparcimientos_faltantes.includes('otros')) {
        requireField('esparcimientos_faltantes_otros', '19.i.- Especifique los otros esparcimientos faltantes.');
      }
      requireField('cruce_peatonal_todas', '20.- Indique si existe cruce peatonal en todas las intersecciones.');
      if (source.cruce_peatonal_todas === 'si') {
        requireField('cruce_demarcado_visible', '21.- Indique si el cruce peatonal está demarcado y visible.');
      }
      requireField('seguridad_cruzar_interseccion', '22.- Indique si se siente seguro al cruzar la intersección.');
      requireField('hay_semaforo_peatonal', '23.- Indique si hay semáforo peatonal.');
      requireField('mapas_senales_caminata', '24.- Indique si existen mapas o señales de caminata.');
      requireField('movilidad_reducida_sin_ayuda', '25.- Indique si una persona con movilidad reducida puede desplazarse sin ayuda.');
      requireField('nombres_calles_visibles', '26.- Indique si las señalizaciones de nombres de calles son visibles.');
      requireField('senalizacion_clara_sin_obstaculos', '27.- Indique si la señalización es clara y sin obstáculos.');
      requireField('trayecto_pie_parada_seguro', '28.- Indique si el trayecto a pie hasta la parada es seguro.');
      requireField('aire_ruido_aceptables', '29.- Indique si el aire y el ruido son aceptables para caminar.');
      requireField('conductores_ceden_paso', '30.- Indique si los conductores ceden el paso a los peatones.');
      requireField('ciudad_prioriza_peaton', '31.- Indique si la ciudad prioriza al peatón sobre el automóvil.');
      requireField('participacion_consultas_peatonales', '32.- Indique si ha participado en consultas sobre espacios peatonales.');
      requireField('planes_movilidad_peatonal_normativa', '33.- Indique si existen planes, presupuesto o normativa de movilidad peatonal.');
      requireField('observaciones_generales', 'Observaciones: escriba sus observaciones o propuestas adicionales.');
      if (source.acepta_declaracion === false) {
        errors.push('Debe confirmar la veracidad de la información para enviar.');
      }
      break;
    }
    default:
      break;
  }

  return errors;
}

