/**
 * Arquetipos de datos para la cobertura del 100% de ramas y bifurcaciones
 * en el Cuestionario PDUL Maturín.
 */

export interface SurveyArchetype {
  id: string;
  name: string;
  description: string;
  paso1: {
    parroquia: string;
    comunidad_sector: string;
    zona_residencia_od: string;
    avenida_calle: string;
    casa_apartamento: string;
  };
  paso2: {
    tipo_vivienda: string;
    tipo_vivienda_otro?: string;
    total_cuartos_vivienda: string;
  };
  paso3: {
    grupos_gastos_separados: string;
    hogar_numero: string;
    cuartos_dormir_hogar: string;
    numero_personas_hogar: string;
    tenencia_vivienda: string;
    tenencia_vivienda_otra?: string;
  };
  paso4: Array<{
    nombre: string;
    parentesco: string;
    sexo: string;
    edad: string;
    sabe_leer: string;
    nivel_educativo: string;
    actividad: string;
    medio_transporte: string;
    licencia: string;
    vehiculo_disp: string;
    tipo_vehiculo?: string;
    cantidad_vehiculo?: string;
  }>;
  paso5: Array<{
    persona_numero: number;
    origen_dir: string;
    origen_zona: string;
    destino_dir: string;
    destino_zona: string;
    hora_salida_h: string;
    hora_salida_m: string;
    hora_salida_periodo: string;
    hora_llegada_h: string;
    hora_llegada_m: string;
    hora_llegada_periodo: string;
    motivo: string;
    motivo_otro?: string;
    modo_principal: string;
    modo_principal_otro?: string;
    modo_secundario?: string;
    modo_secundario_otro?: string;
    tiempo_min: string;
    costo_bs: string;
    probar_regreso_rapido?: boolean;
    probar_modal_detalles?: boolean;
  }>;
  paso6: {
    rutas_tp_dia: string;
    tiempo_espera_paradas_min: string;
    km_residencia_parada: string;
    dificultades_acceso_tp: string;
    principal_dificultad_tp?: string;
    principal_dificultad_tp_otro?: string;
    calificacion_servicio_tp: string;
    gasto_semanal_transporte_bs: string;
    acuerdo_rutas_directas: string;
    comentarios_transporte_maturin: string;
  };
  paso7: {
    cambio_movilidad_5_anos: string;
    motivo_cambio_desplazamiento?: string;
    motivo_cambio_desplazamiento_otro?: string;
    caminatas_mas_10min: string;
    usa_bicicleta: string;
    dias_camina_bici_semana: string;
    modo_actividades_centro: string;
    aceras_adecuadas: string;
    seguridad_desplazamiento_centro: string;
  };
  paso8: {
    frecuencia_visita_parques: string;
    actividades_parques: string[];
    actividades_parques_otras?: string;
    caminatas_ciudad: string;
    seguridad_parques_dia: string;
    seguridad_parques_noche: string;
    limpieza_parques: string;
    impedimentos_espacios: string[];
    impedimentos_espacios_otras?: string;
    satisfaccion_centro: string;
    mejoras_prioritarias: string[];
    mejoras_prioritarias_otro?: string;
    parque_mejorar_primero: string;
    disposicion_participar_mejoras: string;
    sugerencias_esparcimiento: string;
    acera_comoda: string;
    sectores_para_caminar: string;
    facilidad_llegada_parques: string;
    esparcimientos_faltantes: string[];
    esparcimientos_faltantes_otros?: string;
    cruce_peatonal_todas: string;
    seguridad_cruzar_interseccion?: string;
    hay_semaforo_peatonal: string;
    mapas_senales_caminata: string;
    movilidad_reducida_sin_ayuda: string;
    nombres_calles_visibles: string;
    senalizacion_clara_sin_obstaculos: string;
    trayecto_pie_parada_seguro: string;
    aire_ruido_aceptables: string;
    conductores_ceden_paso: string;
    ciudad_prioriza_peaton: string;
    participacion_consultas_peatonales: string;
    planes_movilidad_peatonal_normativa: string;
    observaciones_generales: string;
  };
}

export const ARCHETYPES: Record<string, SurveyArchetype> = {
  // --------------------------------------------------------------------------
  // BOT-01: Ruta Negativa / Base (Cero bifurcaciones activas)
  // --------------------------------------------------------------------------
  bot01_negativo_base: {
    id: 'bot01_negativo_base',
    name: 'BOT-01: Ruta Base Sin Bifurcaciones',
    description: 'Valida que todas las preguntas dependientes (v-if) permanezcan ocultas',
    paso1: {
      parroquia: 'san_simon',
      comunidad_sector: 'Centro de Maturín',
      zona_residencia_od: 'San Simón Centro',
      avenida_calle: 'Av. Bicentenario',
      casa_apartamento: 'Edif. Monagas, Piso 2, Apto 4'
    },
    paso2: {
      tipo_vivienda: 'apartamento_edificio',
      total_cuartos_vivienda: '3'
    },
    paso3: {
      grupos_gastos_separados: '1',
      hogar_numero: '1',
      cuartos_dormir_hogar: '2',
      numero_personas_hogar: '1',
      tenencia_vivienda: 'alquilada'
    },
    paso4: [
      {
        nombre: 'Carlos Mendoza',
        parentesco: '1',
        sexo: '1',
        edad: '34',
        sabe_leer: 'si',
        nivel_educativo: 'universitario',
        actividad: '1',
        medio_transporte: '6',
        licencia: 'no',
        vehiculo_disp: 'no' // Cero campos de vehículos
      }
    ],
    paso5: [
      {
        persona_numero: 1,
        origen_dir: 'Edif. Monagas',
        origen_zona: 'San Simón Centro',
        destino_dir: 'Ministerio de Educación',
        destino_zona: 'San Simón',
        hora_salida_h: '07',
        hora_salida_m: '30',
        hora_salida_periodo: 'AM',
        hora_llegada_h: '08',
        hora_llegada_m: '00',
        hora_llegada_periodo: 'AM',
        motivo: '1', // Trabajo (No requiere otro)
        modo_principal: '6', // TP (No requiere otro)
        modo_secundario: '', // Ninguno
        tiempo_min: '30',
        costo_bs: '15'
      }
    ],
    paso6: {
      rutas_tp_dia: '1',
      tiempo_espera_paradas_min: '20',
      km_residencia_parada: '0.2',
      dificultades_acceso_tp: 'no', // Rama NO activa dificultad
      calificacion_servicio_tp: 'bueno',
      gasto_semanal_transporte_bs: '100',
      acuerdo_rutas_directas: 'de_acuerdo',
      comentarios_transporte_maturin: 'El servicio opera dentro de lo normal.'
    },
    paso7: {
      cambio_movilidad_5_anos: 'no', // Rama NO activa motivo
      caminatas_mas_10min: 'no',
      usa_bicicleta: 'no',
      dias_camina_bici_semana: '1',
      modo_actividades_centro: 'transporte_publico',
      aceras_adecuadas: 'si',
      seguridad_desplazamiento_centro: 'seguro'
    },
    paso8: {
      frecuencia_visita_parques: 'mensual',
      actividades_parques: ['caminar', 'descanso'],
      caminatas_ciudad: 'si',
      seguridad_parques_dia: 'muy_seguro',
      seguridad_parques_noche: 'neutral',
      limpieza_parques: 'buena',
      impedimentos_espacios: ['falta_tiempo'],
      satisfaccion_centro: 'satisfecho',
      mejoras_prioritarias: ['iluminacion', 'mantenimiento_existentes'],
      parque_mejorar_primero: 'Plaza Bolívar',
      disposicion_participar_mejoras: 'si',
      sugerencias_esparcimiento: 'Mantener las áreas verdes cuidadas.',
      acera_comoda: 'de_acuerdo',
      sectores_para_caminar: 'Casco Central',
      facilidad_llegada_parques: 'facil',
      esparcimientos_faltantes: ['bancas', 'iluminacion'],
      cruce_peatonal_todas: 'no', // Rama NO activa cruce_demarcado_visible
      seguridad_cruzar_interseccion: 'neutral',
      hay_semaforo_peatonal: 'no',
      mapas_senales_caminata: 'no',
      movilidad_reducida_sin_ayuda: 'si',
      nombres_calles_visibles: 'si',
      senalizacion_clara_sin_obstaculos: 'si',
      trayecto_pie_parada_seguro: 'muy_seguro',
      aire_ruido_aceptables: 'si',
      conductores_ceden_paso: 'si',
      ciudad_prioriza_peaton: 'no',
      participacion_consultas_peatonales: 'no',
      planes_movilidad_peatonal_normativa: 'no',
      observaciones_generales: 'Cuestionario base completado sin bifurcaciones activas.'
    }
  },

  // --------------------------------------------------------------------------
  // BOT-02: Ruta Extrema de Bifurcaciones ("Otro / Especifique")
  // --------------------------------------------------------------------------
  bot02_extremo_bifurcaciones: {
    id: 'bot02_extremo_bifurcaciones',
    name: 'BOT-02: Ruta Extrema con Todas las Ramas y "Otro"',
    description: 'Activa el 100% de los campos condicionales abiertos y sub-bifurcaciones',
    paso1: {
      parroquia: 'alto_de_los_godos',
      comunidad_sector: 'Los Guaritos III',
      zona_residencia_od: 'Los Godos Oeste',
      avenida_calle: 'Vereda 12 con Calle 4',
      casa_apartamento: 'Quinta 10-A'
    },
    paso2: {
      tipo_vivienda: 'otro', // Bifurcación activa campo abierto
      tipo_vivienda_otro: 'Trailer o módulo habitacional prefabricado',
      total_cuartos_vivienda: '2'
    },
    paso3: {
      grupos_gastos_separados: '1',
      hogar_numero: '1',
      cuartos_dormir_hogar: '1',
      numero_personas_hogar: '1',
      tenencia_vivienda: 'otra_forma', // Bifurcación activa campo abierto
      tenencia_vivienda_otra: 'Comodato institucional por trabajo'
    },
    paso4: [
      {
        nombre: 'Valeria Cedeño',
        parentesco: '1',
        sexo: '2',
        edad: '29',
        sabe_leer: 'si',
        nivel_educativo: 'postgrado',
        actividad: '3', // Trabajadora independiente
        medio_transporte: '8', // Otro
        licencia: 'si',
        vehiculo_disp: 'si', // Bifurcación activa tipo y cantidad
        tipo_vehiculo: 'motocicleta',
        cantidad_vehiculo: '1'
      }
    ],
    paso5: [
      {
        persona_numero: 1,
        origen_dir: 'Los Guaritos III',
        origen_zona: 'Alto de Los Godos',
        destino_dir: 'Sector El Silencio',
        destino_zona: 'Las Cocuizas',
        hora_salida_h: '09',
        hora_salida_m: '15',
        hora_salida_periodo: 'AM',
        hora_llegada_h: '09',
        hora_llegada_m: '50',
        hora_llegada_periodo: 'AM',
        motivo: '8', // Otro motivo
        motivo_otro: 'Entrega de pedidos y mercancía comercial',
        modo_principal: '8', // Otro modo principal
        modo_principal_otro: 'Monopatín eléctrico con batería auxiliar',
        modo_secundario: '8', // Otro modo secundario
        modo_secundario_otro: 'Mototaxi contratado por tramo difícil',
        tiempo_min: '35',
        costo_bs: '25',
        probar_regreso_rapido: true,
        probar_modal_detalles: true
      }
    ],
    paso6: {
      rutas_tp_dia: '3',
      tiempo_espera_paradas_min: '45',
      km_residencia_parada: '0.8',
      dificultades_acceso_tp: 'si', // Bifurcación activa principal_dificultad_tp
      principal_dificultad_tp: 'otro', // Sub-bifurcación activa texto otro
      principal_dificultad_tp_otro: 'Falta total de cambio o métodos de pago digital en las unidades',
      calificacion_servicio_tp: 'muy_malo',
      gasto_semanal_transporte_bs: '250',
      acuerdo_rutas_directas: 'totalmente_de_acuerdo',
      comentarios_transporte_maturin: 'Se precisa modernización del parque automotor y cobro electrónico.'
    },
    paso7: {
      cambio_movilidad_5_anos: 'si', // Bifurcación activa motivo_cambio
      motivo_cambio_desplazamiento: 'otro', // Sub-bifurcación activa texto otro
      motivo_cambio_desplazamiento_otro: 'Incremento excesivo en costo de repuestos y gasolina',
      caminatas_mas_10min: 'si',
      usa_bicicleta: 'si',
      dias_camina_bici_semana: '6',
      modo_actividades_centro: 'camina',
      aceras_adecuadas: 'no',
      seguridad_desplazamiento_centro: 'muy_inseguro'
    },
    paso8: {
      frecuencia_visita_parques: 'ocasionalmente',
      actividades_parques: ['caminar', 'otras'], // Activa actividades_parques_otras
      actividades_parques_otras: 'Fotografía urbana y avistamiento de aves',
      caminatas_ciudad: 'no',
      seguridad_parques_dia: 'poco_seguro',
      seguridad_parques_noche: 'nada_seguro',
      limpieza_parques: 'muy_mala',
      impedimentos_espacios: ['inseguridad', 'otras'], // Activa impedimentos_espacios_otras
      impedimentos_espacios_otras: 'Invasión de basura y aguas servidas en los accesos',
      satisfaccion_centro: 'muy_insatisfecho',
      mejoras_prioritarias: ['iluminacion', 'otro'], // Activa mejoras_prioritarias_otro
      mejoras_prioritarias_otro: 'Puntos de hidratación y vigilancia comunitaria permanente',
      parque_mejorar_primero: 'Parque La Guaricha',
      disposicion_participar_mejoras: 'si',
      sugerencias_esparcimiento: 'Rescatar las caminerías y reparar postes caídos.',
      acera_comoda: 'totalmente_en_desacuerdo',
      sectores_para_caminar: 'Av. Fuerzas Armadas y Casco Central',
      facilidad_llegada_parques: 'muy_dificil',
      esparcimientos_faltantes: ['bancas', 'otros'], // Activa esparcimientos_faltantes_otros
      esparcimientos_faltantes_otros: 'Módulos de primeros auxilios y baños públicos limpios',
      cruce_peatonal_todas: 'si', // Bifurcación activa seguridad_cruzar_interseccion
      seguridad_cruzar_interseccion: 'nada_seguro',
      hay_semaforo_peatonal: 'si',
      mapas_senales_caminata: 'no',
      movilidad_reducida_sin_ayuda: 'no',
      nombres_calles_visibles: 'no',
      senalizacion_clara_sin_obstaculos: 'no',
      trayecto_pie_parada_seguro: 'nada_seguro',
      aire_ruido_aceptables: 'no',
      conductores_ceden_paso: 'no',
      ciudad_prioriza_peaton: 'no',
      participacion_consultas_peatonales: 'si',
      planes_movilidad_peatonal_normativa: 'si',
      observaciones_generales: 'Auditoría integral de bifurcaciones extremas completada exitosamente.'
    }
  },

  // --------------------------------------------------------------------------
  // BOT-03: Ruta Hogar Multimodal y Tenencia Vehicular Privada
  // --------------------------------------------------------------------------
  bot03_vehicular_privado: {
    id: 'bot03_vehicular_privado',
    name: 'BOT-03: Ruta Hogar con Automóvil Privado y Multimodalidad',
    description: 'Evalúa familias con tenencia de automóvil, licencia y viajes particulares',
    paso1: {
      parroquia: 'las_cocuizas',
      comunidad_sector: 'Urbanización San Rafael',
      zona_residencia_od: 'Las Cocuizas Norte',
      avenida_calle: 'Av. Universidad',
      casa_apartamento: 'Casa Nro. 88'
    },
    paso2: {
      tipo_vivienda: 'quinta_casa_quinta',
      total_cuartos_vivienda: '6'
    },
    paso3: {
      grupos_gastos_separados: '1',
      hogar_numero: '1',
      cuartos_dormir_hogar: '3',
      numero_personas_hogar: '2',
      tenencia_vivienda: 'propia_pagada'
    },
    paso4: [
      {
        nombre: 'Roberto Gil',
        parentesco: '1',
        sexo: '1',
        edad: '48',
        sabe_leer: 'si',
        nivel_educativo: 'universitario',
        actividad: '2', // Empleado privado
        medio_transporte: '4', // Automóvil particular
        licencia: 'si',
        vehiculo_disp: 'si',
        tipo_vehiculo: 'automovil',
        cantidad_vehiculo: '2'
      },
      {
        nombre: 'Mariana Gil',
        parentesco: '3',
        sexo: '2',
        edad: '19',
        sabe_leer: 'si',
        nivel_educativo: 'universitario',
        actividad: '5', // Estudiante
        medio_transporte: '6', // TP
        licencia: 'no',
        vehiculo_disp: 'no'
      }
    ],
    paso5: [
      {
        persona_numero: 1,
        origen_dir: 'Urb. San Rafael',
        origen_zona: 'Las Cocuizas Norte',
        destino_dir: 'Zona Industrial de Maturín',
        destino_zona: 'Santa Cruz',
        hora_salida_h: '06',
        hora_salida_m: '45',
        hora_salida_periodo: 'AM',
        hora_llegada_h: '07',
        hora_llegada_m: '20',
        hora_llegada_periodo: 'AM',
        motivo: '1', // Trabajo
        modo_principal: '4', // Automóvil Particular
        modo_secundario: '1', // A pie tramo final
        tiempo_min: '35',
        costo_bs: '60',
        probar_regreso_rapido: true
      }
    ],
    paso6: {
      rutas_tp_dia: '0',
      tiempo_espera_paradas_min: '0',
      km_residencia_parada: '1.2',
      dificultades_acceso_tp: 'si',
      principal_dificultad_tp: 'inseguridad',
      calificacion_servicio_tp: 'regular',
      gasto_semanal_transporte_bs: '450',
      acuerdo_rutas_directas: 'de_acuerdo',
      comentarios_transporte_maturin: 'El transporte público actual desincentiva dejar el carro en casa.'
    },
    paso7: {
      cambio_movilidad_5_anos: 'si',
      motivo_cambio_desplazamiento: 'costo',
      caminatas_mas_10min: 'si',
      usa_bicicleta: 'no',
      dias_camina_bici_semana: '2',
      modo_actividades_centro: 'camina',
      aceras_adecuadas: 'si',
      seguridad_desplazamiento_centro: 'neutral'
    },
    paso8: {
      frecuencia_visita_parques: 'semanal',
      actividades_parques: ['deporte', 'caminar'],
      caminatas_ciudad: 'si',
      seguridad_parques_dia: 'bastante_seguro',
      seguridad_parques_noche: 'poco_seguro',
      limpieza_parques: 'regular',
      impedimentos_espacios: ['distancia'],
      satisfaccion_centro: 'neutral',
      mejoras_prioritarias: ['mobiliario_urbano', 'seguridad_policial'],
      parque_mejorar_primero: 'Parque Andrés Eloy Blanco',
      disposicion_participar_mejoras: 'tal_vez',
      sugerencias_esparcimiento: 'Habilitar áreas seguras de estacionamiento con vigilancia.',
      acera_comoda: 'neutral',
      sectores_para_caminar: 'Zona Este de Maturín',
      facilidad_llegada_parques: 'regular',
      esparcimientos_faltantes: ['maquinas_ejercicios', 'iluminacion'],
      cruce_peatonal_todas: 'no',
      seguridad_cruzar_interseccion: 'neutral',
      hay_semaforo_peatonal: 'si',
      mapas_senales_caminata: 'si',
      movilidad_reducida_sin_ayuda: 'si',
      nombres_calles_visibles: 'no',
      senalizacion_clara_sin_obstaculos: 'no',
      trayecto_pie_parada_seguro: 'poco_seguro',
      aire_ruido_aceptables: 'no',
      conductores_ceden_paso: 'no',
      ciudad_prioriza_peaton: 'no',
      participacion_consultas_peatonales: 'no',
      planes_movilidad_peatonal_normativa: 'no',
      observaciones_generales: 'Planificar pasos peatonales sincronizados en avenidas troncales.'
    }
  },

  // --------------------------------------------------------------------------
  // BOT-04: Ruta Movilidad Activa (Caminante / Ciclista)
  // --------------------------------------------------------------------------
  bot04_movilidad_activa: {
    id: 'bot04_movilidad_activa',
    name: 'BOT-04: Ruta Peatón y Ciclista Urbano',
    description: 'Enfocado en movilidad no motorizada, caminabilidad y cruces peatonales seguros',
    paso1: {
      parroquia: 'boqueron',
      comunidad_sector: 'Costanera Norte',
      zona_residencia_od: 'Boquerón Central',
      avenida_calle: 'Av. Alirio Ugarte Pelayo',
      casa_apartamento: 'Sector San Ramón Casa 12'
    },
    paso2: {
      tipo_vivienda: 'casa',
      total_cuartos_vivienda: '4'
    },
    paso3: {
      grupos_gastos_separados: '1',
      hogar_numero: '1',
      cuartos_dormir_hogar: '2',
      numero_personas_hogar: '1',
      tenencia_vivienda: 'propia_pagada'
    },
    paso4: [
      {
        nombre: 'Daniel Bastardo',
        parentesco: '1',
        sexo: '1',
        edad: '26',
        sabe_leer: 'si',
        nivel_educativo: 'tecnico',
        actividad: '3',
        medio_transporte: '2', // Bicicleta
        licencia: 'no',
        vehiculo_disp: 'si',
        tipo_vehiculo: 'bicicleta',
        cantidad_vehiculo: '1'
      }
    ],
    paso5: [
      {
        persona_numero: 1,
        origen_dir: 'Costanera Norte',
        origen_zona: 'Boquerón Central',
        destino_dir: 'Plaza Rómulo Gallegos',
        destino_zona: 'San Simón Centro',
        hora_salida_h: '07',
        hora_salida_m: '00',
        hora_salida_periodo: 'AM',
        hora_llegada_h: '07',
        hora_llegada_m: '25',
        hora_llegada_periodo: 'AM',
        motivo: '2', // Estudio
        modo_principal: '2', // Bicicleta
        modo_secundario: '1', // A pie
        tiempo_min: '25',
        costo_bs: '0',
        probar_regreso_rapido: true
      }
    ],
    paso6: {
      rutas_tp_dia: '0',
      tiempo_espera_paradas_min: '0',
      km_residencia_parada: '0.5',
      dificultades_acceso_tp: 'no',
      calificacion_servicio_tp: 'regular',
      gasto_semanal_transporte_bs: '0',
      acuerdo_rutas_directas: 'totalmente_de_acuerdo',
      comentarios_transporte_maturin: 'Se requieren ciclovías segregadas para conectar Boquerón con el centro.'
    },
    paso7: {
      cambio_movilidad_5_anos: 'si',
      motivo_cambio_desplazamiento: 'cambio_residencia',
      caminatas_mas_10min: 'si',
      usa_bicicleta: 'si',
      dias_camina_bici_semana: '7',
      modo_actividades_centro: 'camina',
      aceras_adecuadas: 'no',
      seguridad_desplazamiento_centro: 'seguro'
    },
    paso8: {
      frecuencia_visita_parques: 'diario',
      actividades_parques: ['deporte', 'caminar'],
      caminatas_ciudad: 'si',
      seguridad_parques_dia: 'muy_seguro',
      seguridad_parques_noche: 'bastante_seguro',
      limpieza_parques: 'muy_buena',
      impedimentos_espacios: ['distancia'],
      satisfaccion_centro: 'muy_satisfecho',
      mejoras_prioritarias: ['rutas_peatonales_ciclovias', 'mobiliario_urbano'],
      parque_mejorar_primero: 'Paseo Aeróbico',
      disposicion_participar_mejoras: 'si',
      sugerencias_esparcimiento: 'Desarrollar red continua de ciclovías con biciestacionamientos protegidos.',
      acera_comoda: 'totalmente_de_acuerdo',
      sectores_para_caminar: 'Eje Bicentenario y Av. Bolívar',
      facilidad_llegada_parques: 'muy_facil',
      esparcimientos_faltantes: ['ciclovia', 'sombra'],
      cruce_peatonal_todas: 'si', // Activa cruce_demarcado_visible
      seguridad_cruzar_interseccion: 'bastante_seguro',
      hay_semaforo_peatonal: 'si',
      mapas_senales_caminata: 'si',
      movilidad_reducida_sin_ayuda: 'si',
      nombres_calles_visibles: 'si',
      senalizacion_clara_sin_obstaculos: 'si',
      trayecto_pie_parada_seguro: 'bastante_seguro',
      aire_ruido_aceptables: 'si',
      conductores_ceden_paso: 'si',
      ciudad_prioriza_peaton: 'si',
      participacion_consultas_peatonales: 'si',
      planes_movilidad_peatonal_normativa: 'si',
      observaciones_generales: 'Excelente iniciativa para el diseño del Plan de Movilidad Urbana Sostenible.'
    }
  }
};
