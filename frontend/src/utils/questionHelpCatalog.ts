/**
 * Catálogo centralizado de descripciones de ayuda ciudadana (tooltips)
 * para las preguntas del Cuestionario Origen-Destino PDUL Maturín.
 */
export const QUESTION_HELP_TIPS: Record<string, string> = {
  // Sección I: Identificación y Ubicación
  parroquia:
    'División político-territorial oficial del Municipio Maturín donde se encuentra ubicada su vivienda.',
  comunidad_sector:
    'Barrio, urbanización, caserío o sector dentro de la parroquia elegida. Si no figura en la lista, seleccione «Otra comunidad».',
  zona_residencia_od:
    'Macrozona o sector de planificación de movilidad (Origen-Destino) correspondiente a su lugar de residencia.',
  avenida_calle:
    'Nombre o número de la avenida, calle, carrera o vereda principal de acceso a su vivienda.',
  casa_apartamento:
    'Número o identificador de la casa, quinta, bloque, edificio o apartamento.',

  // Sección II: Datos de la Vivienda
  tipo_vivienda:
    'Tipo constructivo predominante del inmueble donde habita (casa independiente, apartamento en edificio, quinta, rústica, etc.).',
  total_cuartos_vivienda:
    'Sume los espacios habitables cerrados: sala-comedor (1 si es un solo ambiente, 2 si están separados), dormitorios y otros cuartos (estudio, biblioteca). No cuente baños, cocina, pasillos, balcones ni lavaderos.',

  // Sección III: Datos del Hogar
  grupos_gastos_separados:
    'Si dentro de la vivienda conviven familias que preparan o costean sus alimentos por separado, cuente cada grupo como un hogar distinto. Si todos comparten gastos de comida, coloque 1.',
  hogar_numero:
    'Si respondió 1 grupo en la pregunta anterior, escriba 1. Si conviven varios hogares en la misma vivienda, indique el número correlativo del hogar entrevistado.',
  cuartos_dormir_hogar:
    'Cuente únicamente las habitaciones que los integrantes de este hogar utilizan habitualmente para dormir.',
  numero_personas_hogar:
    'Número total de personas (incluidos niños, bebés y adultos mayores) que duermen y residen habitualmente en este hogar.',
  tenencia_vivienda:
    'Situación legal o acuerdo bajo el cual este hogar ocupa la vivienda (propia pagada, pagándose, alquilada, cedida, etc.).',

  // Sección IV: Características de los Residentes
  residentes:
    'Agregue a cada persona que vive habitualmente en el hogar. Esta lista permite asociar cada viaje registrado en el paso siguiente con la persona que lo realizó.',

  // Sección V: Registro General de Viajes (O-D)
  viajes:
    'Un viaje es cada desplazamiento por vía pública realizado el día típico anterior (ej. ida al trabajo es 1 viaje, regreso a casa es otro viaje).',
  viaje_persona:
    'Indique cuál de los residentes registrados en el Paso 4 efectuó este desplazamiento.',
  viaje_origen_zona:
    'Parroquia o sector de partida al iniciar este viaje (para el primer trayecto del día suele ser su zona de residencia).',
  viaje_destino_zona:
    'Parroquia, zona o sector de la ciudad adonde llegó al terminar este desplazamiento.',
  viaje_motivo:
    'Actividad principal que originó este viaje (trabajo, estudio, compras, retorno al hogar, trámites o salud).',
  viaje_modo_principal:
    'Medio de transporte en el cual recorrió la mayor distancia del trayecto (bus, carrito por puesto, carro particular, moto, bicicleta o a pie).',
  viaje_tiempo_costo:
    'Tiempo total puerta a puerta en minutos (caminata + espera + recorrido) y gasto en Bolívares por este trayecto (0 si fue a pie o gratuito).',

  // Sección VI: Características de Transporte Público
  rutas_tp_dia:
    'Cantidad de líneas o rutas distintas (autobús, buseta o por puesto) que abordó ayer en todos sus viajes. Si hizo trasbordo entre 2 unidades distintas, cuente 2.',
  tiempo_espera_paradas_min:
    'Suma estimada en minutos de todo el tiempo que esperó en paradas durante los viajes del día.',
  km_residencia_parada:
    'Distancia aproximada caminando desde su casa hasta la parada más cercana donde toma el transporte (ej. 0.5 km equivale a unas 5 cuadras).',
  dificultades_acceso_tp:
    'Indique si presenta inconvenientes frecuentes para abordar transporte público en su zona.',
  principal_dificultad_tp:
    'Seleccione el obstáculo que más afecta su acceso al transporte (pocas unidades, sobrecupo, falta de rutas, inseguridad o tarifa).',
  calificacion_servicio_tp:
    'Valoración general sobre calidad, frecuencia, trato y estado de las unidades disponibles.',
  gasto_semanal_transporte_bs:
    'Monto total estimado en Bolívares que destinan en conjunto todos los miembros del hogar para pasajes durante una semana.',
  acuerdo_rutas_directas:
    'Su grado de acuerdo con implementar rutas directas desde su parroquia hasta los principales destinos sin necesidad de trasbordos.',
  comentarios_transporte_maturin:
    'Observaciones libres sobre paradas, frecuencias, tarifas o nuevas rutas necesarias en su comunidad.',

  // Sección VII: Movilidad No Motorizada y Percepción
  cambio_movilidad_5_anos:
    'Indique si en los últimos 5 años cambió de carro particular a transporte público, motocicleta, bicicleta o caminata (o viceversa).',
  motivo_cambio_desplazamiento:
    'Razón principal que motivó el cambio en su manera habitual de trasladarse.',
  caminatas_mas_10min:
    'Desplazamientos continuos a pie de más de 10 minutos como parte de su rutina diaria (trabajo, compras, estudio o ir a la parada).',
  usa_bicicleta:
    'Si utiliza bicicleta como medio de transporte para llegar a sus actividades (no solo uso deportivo ocasional).',
  dias_camina_bici_semana:
    'Cantidad de días en una semana típica (de 0 a 7) en los que realiza trayectos caminando o en bicicleta.',
  modo_actividades_centro:
    'Cómo se traslada y moviliza habitualmente dentro del casco central de Maturín para compras, trabajo o trámites.',
  aceras_adecuadas:
    'Evalúa si las aceras por donde camina tienen ancho libre, buen piso, drenaje y ausencia de obstáculos.',
  seguridad_desplazamiento_centro:
    'Percepción de seguridad vial y ciudadana al caminar por las calles y avenidas del centro.',

  // Sección VIII: Esparcimientos y Peatonalidad
  frecuencia_visita_parques:
    'Frecuencia con la que usted o su hogar visitan plazas, parques, paseos peatonales o áreas verdes.',
  actividades_parques:
    'Actividades habituales que realiza en esos espacios públicos (puede seleccionar varias opciones).',
  caminatas_ciudad:
    'Si acostumbra realizar caminatas recreativas, deportivas o urbanas por calles y parques de la ciudad.',
  seguridad_parques_dia:
    'Sensación de tranquilidad y resguardo en parques y rutas peatonales durante horas del día.',
  seguridad_parques_noche:
    'Sensación de seguridad, alumbrado y vigilancia en parques y rutas peatonales en horario nocturno.',
  limpieza_parques:
    'Calificación del estado de aseo, recolección de residuos, pintura y mantenimiento de áreas verdes.',
  impedimentos_espacios:
    'Principales razones por las cuales no usa más frecuentemente plazas y parques (distancia, deterioro, inseguridad, falta de iluminación, etc.).',
  satisfaccion_centro:
    'Nivel de conformidad con el número y condiciones actuales de parques, plazas y aceras del centro de Maturín.',
  mejoras_prioritarias:
    'Intervenciones que considera más urgentes para recuperar parques, plazas y rutas de caminata.',
  parque_mejorar_primero:
    'Nombre específico del parque, plaza o boulevard que debería priorizarse en su sector o en la ciudad.',
  disposicion_participar_mejoras:
    'Si estaría dispuesto a colaborar en jornadas comunitarias, contraloría o mantenimiento de estos espacios.',
  sugerencias_esparcimiento:
    'Propuestas ciudadanas para ampliar o rehabilitar áreas recreativas y paseos peatonales.',
  acera_comoda:
    'Si el ancho y estado del pavimento de las aceras permiten caminar cómodamente sin bajar a la calle.',
  sectores_para_caminar:
    'Avenidas, calles, parques o zonas específicas de la ciudad donde suele realizar sus caminatas.',
  facilidad_llegada_parques:
    'Qué tan accesible resulta trasladarse desde su residencia hasta las áreas recreativas o rutas peatonales.',
  esparcimientos_faltantes:
    'Equipamientos urbanos o recreativos ausentes en la ciudad que considera necesarios incorporar.',
  cruce_peatonal_todas:
    'Si las esquinas e intersecciones de su trayecto cuentan con paso peatonal (rayado cebrado).',
  cruce_demarcado_visible:
    'Si la pintura y señalización del paso peatonal se distinguen con claridad tanto de día como de noche.',
  seguridad_cruzar_interseccion:
    'Nivel de seguridad que siente al cruzar la vía considerando velocidad vehicular y visibilidad.',
  hay_semaforo_peatonal:
    'Presencia de semáforos con luz o señal específica para indicar cuándo debe cruzar el peatón.',
  mapas_senales_caminata:
    'Existencia de tótems, planos urbanos o letreros que indiquen distancias y direcciones a pie hacia sitios de interés.',
  movilidad_reducida_sin_ayuda:
    'Si personas en silla de ruedas, adultos mayores o con coches de bebé pueden cruzar las esquinas (rampas, sin desniveles) de forma autónoma.',
  nombres_calles_visibles:
    'Si las calles y avenidas cuentan con rótulos legibles con su nombre o numeración para orientarse.',
  senalizacion_clara_sin_obstaculos:
    'Si las señales peatonales y de tránsito están despejadas (sin ramas, avisos comerciales ni postes bloqueándolas).',
  trayecto_pie_parada_seguro:
    'Seguridad física y vial al caminar desde su casa o trabajo hasta la parada de transporte.',
  aire_ruido_aceptables:
    'Condiciones ambientales (nivel de humo vehicular y ruido) durante sus caminatas por el sector o centro.',
  conductores_ceden_paso:
    'Si los conductores de vehículos y motos respetan el derecho de paso del peatón en rayados y esquinas.',
  ciudad_prioriza_peaton:
    'Percepción general sobre si el diseño vial y las normas de Maturín dan prioridad al caminante frente al vehículo.',
  participacion_consultas_peatonales:
    'Si anteriormente ha sido convocado o participado en encuestas o asambleas sobre espacios públicos y caminerías.',
  planes_movilidad_peatonal_normativa:
    'Conocimiento sobre la existencia de planes municipales, presupuesto o normativa que proteja la movilidad peatonal.'
};

