export interface SurveyOption {
  readonly value: string;
  readonly label: string;
}

export const TIPOS_VIVIENDA: readonly SurveyOption[] = [
  { value: 'quinta_casa_quinta', label: 'a.- Quinta o Casa quinta' },
  { value: 'casa', label: 'b.- Casa' },
  { value: 'apartamento_edificio', label: 'c.- Apartamento en edificio' },
  { value: 'apartamento_quinta_casa', label: 'd.- Apartamento en quinta, casa-quinta o casa' },
  { value: 'casa_vecindad', label: 'e.- Casa de vecindad' },
  { value: 'vivienda_rustica', label: 'f.- Vivienda rústica (rancho)' },
  { value: 'otro', label: 'g.- Otro tipo' }
];

export const TENENCIA_VIVIENDA: readonly SurveyOption[] = [
  { value: 'propia_pagada', label: 'a.- Propia pagada totalmente' },
  { value: 'propia_pagandose', label: 'b.- Propia pagándose' },
  { value: 'alquilada', label: 'c.- Alquilada' },
  { value: 'alquilada_parte', label: 'd.- Alquilada parte de la Vivienda' },
  { value: 'cedida_trabajo', label: 'e.- Cedida por razones de trabajo' },
  { value: 'cedida_familiar', label: 'f.- Cedida por familiar o amigo' },
  { value: 'tomada_invadida', label: 'g.- Tomada/Invadida' },
  { value: 'otra_forma', label: 'h.- Otra forma' }
];

export const DIFICULTADES_ACCESO_TP: readonly SurveyOption[] = [
  { value: 'frecuencia_baja', label: 'a.- Frecuencia baja' },
  { value: 'sobrecupo', label: 'b.- Sobrecupo' },
  { value: 'falta_de_rutas', label: 'c.- Falta de rutas' },
  { value: 'inseguridad', label: 'd.- Inseguridad' },
  { value: 'otro', label: 'e.- Otro' }
];

export const CALIFICACION_TP: readonly SurveyOption[] = [
  { value: 'muy_bueno', label: 'a.- Muy bueno' },
  { value: 'bueno', label: 'b.- Bueno' },
  { value: 'regular', label: 'c.- Regular' },
  { value: 'malo', label: 'd.- Malo' },
  { value: 'muy_malo', label: 'e.- Muy malo' }
];

export const ACUERDO_RUTAS_DIRECTAS: readonly SurveyOption[] = [
  { value: 'totalmente_de_acuerdo', label: 'a.- Totalmente de acuerdo' },
  { value: 'de_acuerdo', label: 'b.- De acuerdo' },
  { value: 'neutral', label: 'c.- Ni de acuerdo ni en desacuerdo (Neutral)' },
  { value: 'en_desacuerdo', label: 'd.- En desacuerdo' },
  { value: 'totalmente_en_desacuerdo', label: 'e.- Totalmente en desacuerdo' }
];

export const MOTIVOS_CAMBIO_DESPLAZAMIENTO: readonly SurveyOption[] = [
  { value: 'cambio_trabajo', label: 'a.- Cambio de trabajo' },
  { value: 'cambio_residencia', label: 'b.- Cambio de residencia' },
  { value: 'falta_transporte', label: 'c.- Falta de transporte' },
  { value: 'costo', label: 'd.- Costo' },
  { value: 'otro', label: 'e.- Otro' }
];

export const MODO_CENTRO_ACTIVIDADES: readonly SurveyOption[] = [
  { value: 'camina', label: 'a.- Camina' },
  { value: 'transporte_publico', label: 'b.- Transporte público' }
];

export const SEGURIDAD_CENTRO: readonly SurveyOption[] = [
  { value: 'muy_seguro', label: 'a.- Muy seguro' },
  { value: 'seguro', label: 'b.- Seguro' },
  { value: 'neutral', label: 'c.- Neutral' },
  { value: 'inseguro', label: 'd.- Inseguro' },
  { value: 'muy_inseguro', label: 'e.- Muy Inseguro' }
];

export const FRECUENCIA_VISITA_PARQUES: readonly SurveyOption[] = [
  { value: 'nunca', label: 'a.- Nunca' },
  { value: 'ocasionalmente', label: 'b.- Ocasionalmente' },
  { value: 'mensual', label: 'c.- Mensual' },
  { value: 'semanal', label: 'd.- Semanal' },
  { value: 'diario', label: 'e.- Diario' }
];

export const ACTIVIDADES_PARQUES: readonly SurveyOption[] = [
  { value: 'caminar', label: 'a.- Caminar' },
  { value: 'trotar_correr', label: 'b.- Trotar/Correr' },
  { value: 'recreacion_infantil', label: 'c.- Recreación Infantil' },
  { value: 'deporte', label: 'd.- Deporte' },
  { value: 'descanso', label: 'e.- Descanso' },
  { value: 'lectura', label: 'f.- Lectura' },
  { value: 'otras', label: 'g.- Otras' }
];

export const CAMINATAS_CIUDAD: readonly SurveyOption[] = [
  { value: 'si', label: 'a.- Sí' },
  { value: 'no', label: 'b.- No' },
  { value: 'a_veces', label: 'c.- A veces' }
];

export const ESCALA_SEGURIDAD_PARQUES: readonly SurveyOption[] = [
  { value: 'nada_seguro', label: 'a.- Nada Seguro(a)' },
  { value: 'poco_seguro', label: 'b.- Poco seguro(a)' },
  { value: 'neutral', label: 'c.- Ni seguro(a), ni inseguro(a)/neutral' },
  { value: 'bastante_seguro', label: 'd.- Algo seguro(a) / Bastante seguro(a)' },
  { value: 'muy_seguro', label: 'e.- Totalmente seguro(a) / Muy seguro(a)' }
];

export const CALIFICACION_LIMPIEZA: readonly SurveyOption[] = [
  { value: 'muy_buena', label: 'a.- Muy buena' },
  { value: 'buena', label: 'b.- Buena' },
  { value: 'regular', label: 'c.- Regular' },
  { value: 'mala', label: 'd.- Mala' },
  { value: 'muy_mala', label: 'e.- Muy mala' }
];

export const IMPEDIMENTOS_ESPACIOS: readonly SurveyOption[] = [
  { value: 'distancia', label: 'a.- Distancia' },
  { value: 'falta_tiempo', label: 'b.- Falta de tiempo' },
  { value: 'inseguridad', label: 'c.- Inseguridad' },
  { value: 'mala_accesibilidad', label: 'd.- Mala accesibilidad' },
  { value: 'falta_mantenimiento', label: 'e.- Falta de mantenimiento' },
  { value: 'otras', label: 'f.- Otras' }
];

export const SATISFACCION_CENTRO: readonly SurveyOption[] = [
  { value: 'muy_insatisfecho', label: 'a.- Muy insatisfecho(a)' },
  { value: 'insatisfecho', label: 'b.- Insatisfecho(a)' },
  { value: 'neutral', label: 'c.- Ni satisfecho(a) ni insatisfecho(a) / Neutral' },
  { value: 'satisfecho', label: 'd.- Satisfecho(a)' },
  { value: 'muy_satisfecho', label: 'e.- Muy satisfecho(a)' }
];

export const MEJORAS_PRIORITARIAS: readonly SurveyOption[] = [
  { value: 'mas_parques_plazas', label: 'a.- Crear más parques y plazas' },
  { value: 'mantenimiento_existentes', label: 'b.- Mejorar el mantenimiento de los parques y espacios existentes (limpieza, áreas verdes, bancas, iluminación)' },
  { value: 'rutas_peatonales_ciclovias', label: 'c.- Ampliar y mejorar las rutas peatonales y ciclovías' },
  { value: 'iluminacion', label: 'd.- Aumentar la iluminación en parques y rutas peatonales' },
  { value: 'seguridad_policial', label: 'e.- Mejorar la seguridad (vigilancia, cámaras, presencia policial)' },
  { value: 'mobiliario_urbano', label: 'f.- Instalar más mobiliario urbano (bancas, basureros, bebederos, sombras)' },
  { value: 'juegos_ninos', label: 'g.- Crear o mejorar áreas de juego para niños' },
  { value: 'espacios_deportivos', label: 'h.- Crear o mejorar espacios deportivos y recreativos (canchas, gimnasios al aire libre)' },
  { value: 'actividades_culturales', label: 'i.- Organizar más actividades culturales y recreativas (eventos, talleres, ferias)' },
  { value: 'accesibilidad_discapacidad', label: 'j.- Mejorar la accesibilidad para personas con discapacidad' },
  { value: 'recuperar_abandonados', label: 'k.- Recuperar espacios abandonados o subutilizados' },
  { value: 'participacion_ciudadana', label: 'l.- Promover la participación ciudadana en el diseño y cuidado de los espacios' },
  { value: 'otro', label: 'm.- Otro (especifique)' }
];

export const DISPOSICION_PARTICIPAR: readonly SurveyOption[] = [
  { value: 'si', label: 'a.- Sí' },
  { value: 'no', label: 'b.- No' },
  { value: 'tal_vez', label: 'c.- Tal vez' }
];

export const ACUERDO_ACERA_COMODA: readonly SurveyOption[] = [
  { value: 'totalmente_de_acuerdo', label: 'a.- Totalmente de acuerdo' },
  { value: 'de_acuerdo', label: 'b.- De acuerdo' },
  { value: 'neutral', label: 'c.- Ni de acuerdo ni en desacuerdo (Neutral)' },
  { value: 'en_desacuerdo', label: 'd.- En desacuerdo' },
  { value: 'totalmente_en_desacuerdo', label: 'e.- Totalmente en desacuerdo' }
];

export const FACILIDAD_LLEGADA: readonly SurveyOption[] = [
  { value: 'muy_facil', label: 'a.- Muy fácil' },
  { value: 'facil', label: 'b.- Fácil' },
  { value: 'regular', label: 'c.- Regular' },
  { value: 'dificil', label: 'd.- Difícil' },
  { value: 'muy_dificil', label: 'e.- Muy Difícil' }
];

export const ESPARCIMIENTOS_FALTANTES: readonly SurveyOption[] = [
  { value: 'bancas', label: 'a.- Bancas' },
  { value: 'sombra', label: 'b.- Sombra' },
  { value: 'iluminacion', label: 'c.- Iluminación' },
  { value: 'maquinas_ejercicios', label: 'd.- Maquinas de ejercicios' },
  { value: 'banos', label: 'e.- Baños' },
  { value: 'juegos', label: 'f.- Juegos' },
  { value: 'ciclovia', label: 'g.- Ciclovía' },
  { value: 'senalizacion', label: 'h.- Señalización' },
  { value: 'otros', label: 'i.- Otros' }
];

export const PLANES_MOVILIDAD_PESTONAL: readonly SurveyOption[] = [
  { value: 'si', label: 'a.- Sí' },
  { value: 'no', label: 'b.- No' },
  { value: 'no_sabe', label: 'c.- No Sabe/No responde' }
];

export const OPCIONES_SI_NO_SIN_TILDE: readonly SurveyOption[] = [
  { value: 'si', label: 'a.- Si' },
  { value: 'no', label: 'b.- No' }
];

export const OPCIONES_SI_NO: readonly SurveyOption[] = [
  { value: 'si', label: 'a.- Sí' },
  { value: 'no', label: 'b.- No' }
];

