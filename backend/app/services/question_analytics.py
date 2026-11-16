"""Servicio de agregación y análisis pregunta por pregunta para el Dashboard Municipal.

Genera la distribución de frecuencias y porcentajes para cada pregunta individual
del cuestionario PDUL, mapeando códigos internos a etiquetas humanas comprensibles
y asociando la sección y el tipo de gráfico idóneo (donut o barras).
"""

from collections import Counter
from typing import Any, Dict, List
from backend.app.schemas.analytics import PreguntaMetricaOut

COMMON_LABELS: Dict[str, str] = {
    "si": "Sí",
    "no": "No",
    "tal_vez": "Tal vez / Indeciso",
    "casa": "Casa",
    "apartamento_edificio": "Apartamento en Edificio",
    "quinta_casa_quinta": "Quinta o Casa-quinta",
    "vivienda_rustica": "Vivienda rústica",
    "casa_vecindad": "Casa de vecindad",
    "propia_pagada": "Propia pagada totalmente",
    "alquilada": "Alquilada",
    "propia_pagandose": "Propia pagándose",
    "cedida_familiar": "Cedida por familiar o amigo",
    "muy_bueno": "Muy Bueno",
    "bueno": "Bueno",
    "regular": "Regular",
    "malo": "Malo",
    "pesimo": "Pésimo",
    "muy_malo": "Muy Malo",
    "muy_seguro": "Muy Seguro",
    "seguro": "Seguro",
    "neutral": "Neutral (Ni seguro ni inseguro)",
    "inseguro": "Inseguro",
    "muy_inseguro": "Muy Inseguro",
    "poco_seguro": "Poco Seguro",
    "bastante_seguro": "Bastante Seguro",
    "nada_seguro": "Nada Seguro",
    "en_desacuerdo": "En desacuerdo",
    "totalmente_en_desacuerdo": "Totalmente en desacuerdo",
    "de_acuerdo": "De acuerdo",
    "totalmente_de_acuerdo": "Totalmente de acuerdo",
    "frecuencia_baja": "Frecuencia baja de unidades",
    "sobrecupo": "Sobrecupo / Aglomeración",
    "falta_de_rutas": "Falta de rutas de transporte",
    "inseguridad": "Inseguridad en paradas o unidades",
    "costo": "Costo del pasaje",
    "mal_estado": "Mal estado de las unidades",
    "mantenimiento_existentes": "Mantenimiento de áreas existentes",
    "rutas_peatonales_ciclovias": "Rutas peatonales y ciclovías",
    "iluminacion": "Mejor iluminación pública",
    "seguridad_policial": "Mayor presencia policial",
    "arbolado_sombra": "Arbolado y zonas de sombra",
    "juegos_infantiles": "Parques y juegos infantiles",
    "aparatos_ejercicio": "Gimnasios al aire libre",
    "san_simon": "San Simón",
    "alto_de_los_godos": "Alto de los Godos",
    "boqueron": "Boquerón",
    "las_cocuizas": "Las Cocuizas",
    "santa_cruz": "Santa Cruz",
    "san_vicente": "San Vicente",
    "la_pica": "La Pica",
    "el_furrial": "El Furrial",
    "el_corozo": "El Corozo",
    "jusepin": "Jusepín",
    "la_cruz": "La Cruz",
}

CUSTOM_FIELD_LABELS: Dict[str, Dict[str, str]] = {
    "sexo": {"1": "Hombre", "2": "Mujer", "masculino": "Hombre", "femenino": "Mujer"},
    "parentesco": {
        "1": "Jefe(a) de Hogar",
        "2": "Cónyuge / Pareja",
        "3": "Hijo(a) / Hijastro(a)",
        "4": "Padre / Madre",
        "5": "Hermano(a)",
        "6": "Nieto(a)",
        "7": "Otro familiar",
        "8": "No familiar",
        "jefe": "Jefe(a) de Hogar",
        "esposo_pareja": "Cónyuge / Pareja",
        "hijo_hijastro": "Hijo(a) / Hijastro(a)",
    },
    "nivel_educativo": {
        "1": "Ninguno",
        "2": "Primaria",
        "3": "Secundaria / Bachillerato",
        "4": "Técnico / Universitario",
        "5": "Postgrado",
        "ninguno": "Ninguno",
        "primaria": "Primaria",
        "secundaria": "Secundaria / Bachillerato",
        "tecnico": "Técnico",
        "universitario": "Universitario",
        "postgrado": "Postgrado",
    },
    "actividad_principal": {
        "1": "Empleado público",
        "2": "Empleado privado",
        "3": "Trabajador independiente / Por cuenta propia",
        "4": "Comerciante informal",
        "5": "Estudiante",
        "6": "Labores del hogar",
        "7": "Jubilado / Pensionado",
        "8": "Desempleado",
        "9": "Otro",
    },
    "ocupacion_principal": {
        "1": "Empleado público",
        "2": "Empleado privado",
        "3": "Trabajador independiente / Por cuenta propia",
        "4": "Comerciante informal",
        "5": "Estudiante",
        "6": "Labores del hogar",
        "7": "Jubilado / Pensionado",
        "8": "Desempleado",
        "9": "Otro",
    },
    "motivo_viaje": {
        "1": "Trabajo",
        "2": "Estudio",
        "3": "Compras / Abastecimiento",
        "4": "Trámites personales",
        "5": "Retorno al hogar",
        "6": "Recreación / Ocio",
        "7": "Salud / Asistencia médica",
        "8": "Otro",
    },
    "proposito_viaje": {
        "1": "Trabajo",
        "2": "Estudio",
        "3": "Compras / Abastecimiento",
        "4": "Trámites personales",
        "5": "Retorno al hogar",
        "6": "Recreación / Ocio",
        "7": "Salud / Asistencia médica",
        "8": "Otro",
    },
    "modo_principal": {
        "1": "A pie / Caminata",
        "2": "Bicicleta",
        "3": "Motocicleta particular",
        "4": "Automóvil particular (Conductor)",
        "5": "Automóvil particular (Acompañante)",
        "6": "Transporte público (Autobús / Microbús)",
        "7": "Transporte por puesto (Carrito)",
        "8": "Taxi / Mototaxi",
        "9": "Transporte institucional / Escolar",
        "10": "Otro modo",
    },
    "frecuencia_visita_parques": {
        "diario": "A diario",
        "varias_veces_semana": "Varias veces por semana",
        "una_vez_semana": "Una vez por semana",
        "quincenal": "Cada 15 días",
        "mensual": "Una vez al mes",
        "casi_nunca": "Casi nunca",
        "nunca": "Nunca",
    },
    "calificacion_limpieza_conservacion": {
        "muy_buena": "Muy Buena",
        "buena": "Buena",
        "regular": "Regular",
        "mala": "Mala",
        "muy_mala": "Muy Mala",
    },
}

QUESTIONS_METRIC_CONFIG = [
    # Sección I
    {
        "seccion": "Sección I: Identificación de la Unidad Residencial",
        "clave": "parroquia",
        "pregunta": "1.- Parroquia de residencia",
        "tipo_grafico": "bar",
        "aliases": ["parroquia"],
    },
    {
        "seccion": "Sección I: Identificación de la Unidad Residencial",
        "clave": "zona_residencia_od",
        "pregunta": "3.- Zona de Residencia (Zonificación O-D)",
        "tipo_grafico": "bar",
        "aliases": ["zona_residencia_od", "zona_od"],
    },
    # Sección II
    {
        "seccion": "Sección II: Datos de la Vivienda",
        "clave": "tipo_vivienda",
        "pregunta": "1.- Tipo de vivienda",
        "tipo_grafico": "donut",
        "aliases": ["tipo_vivienda"],
    },
    {
        "seccion": "Sección II: Datos de la Vivienda",
        "clave": "total_cuartos_vivienda",
        "pregunta": "2.- Contando sala, comedor, cuartos para dormir y otros cuartos ¿Cuántos cuartos tiene en total esta vivienda?",
        "tipo_grafico": "bar",
        "aliases": ["total_cuartos_vivienda"],
    },
    # Sección III
    {
        "seccion": "Sección III: Datos del Hogar",
        "clave": "grupos_gastos_separados",
        "pregunta": "1.- ¿Cuántos grupos de personas de esta vivienda mantienen gastos separados para la comida?",
        "tipo_grafico": "bar",
        "aliases": ["grupos_gastos_separados"],
    },
    {
        "seccion": "Sección III: Datos del Hogar",
        "clave": "cuartos_dormir_hogar",
        "pregunta": "2.- ¿Cuántos cuartos para dormir utiliza este hogar?",
        "tipo_grafico": "bar",
        "aliases": ["cuartos_dormir_hogar"],
    },
    {
        "seccion": "Sección III: Datos del Hogar",
        "clave": "numero_personas_hogar",
        "pregunta": "3.- Número de personas que residen en este hogar",
        "tipo_grafico": "bar",
        "aliases": ["numero_personas_hogar"],
    },
    {
        "seccion": "Sección III: Datos del Hogar",
        "clave": "tenencia_vivienda",
        "pregunta": "4.- Para este hogar la vivienda es:",
        "tipo_grafico": "donut",
        "aliases": ["tenencia_vivienda"],
    },
    # Sección IV
    {
        "seccion": "Sección IV: Características de los Residentes",
        "clave": "sexo_residentes",
        "pregunta": "Distribución por Sexo de los Miembros del Hogar",
        "tipo_grafico": "donut",
        "aliases": ["residentes:sexo"],
    },
    {
        "seccion": "Sección IV: Características de los Residentes",
        "clave": "edad_residentes",
        "pregunta": "Grupos de Edad de los Miembros del Hogar",
        "tipo_grafico": "bar",
        "aliases": ["residentes:edad"],
    },
    {
        "seccion": "Sección IV: Características de los Residentes",
        "clave": "parentesco_jefe",
        "pregunta": "Parentesco con el Jefe del Hogar",
        "tipo_grafico": "bar",
        "aliases": ["residentes:parentesco", "residentes:parentesco_jefe_hogar"],
    },
    {
        "seccion": "Sección IV: Características de los Residentes",
        "clave": "nivel_educativo_res",
        "pregunta": "Nivel Educativo alcanzado por los Residentes",
        "tipo_grafico": "bar",
        "aliases": ["residentes:nivel_educativo"],
    },
    {
        "seccion": "Sección IV: Características de los Residentes",
        "clave": "ocupacion_res",
        "pregunta": "Ocupación o Actividad Principal de los Residentes",
        "tipo_grafico": "bar",
        "aliases": ["residentes:actividad_principal", "residentes:ocupacion_principal"],
    },
    {
        "seccion": "Sección IV: Características de los Residentes",
        "clave": "licencia_conducir",
        "pregunta": "¿Posee licencia de conducir?",
        "tipo_grafico": "donut",
        "aliases": ["residentes:posee_licencia"],
    },
    {
        "seccion": "Sección IV: Características de los Residentes",
        "clave": "vehiculo_disponible",
        "pregunta": "¿Tiene algún vehículo disponible?",
        "tipo_grafico": "donut",
        "aliases": ["residentes:tiene_vehiculo_disponible"],
    },
    # Sección V
    {
        "seccion": "Sección V: Registro General de Viajes",
        "clave": "modo_principal_viajes",
        "pregunta": "Modo Principal de Transporte Utilizado en los Viajes",
        "tipo_grafico": "donut",
        "aliases": ["viajes:modo_principal"],
    },
    {
        "seccion": "Sección V: Registro General de Viajes",
        "clave": "motivo_viaje_viajes",
        "pregunta": "Motivo o Propósito del Viaje",
        "tipo_grafico": "bar",
        "aliases": ["viajes:motivo_viaje", "viajes:proposito_viaje"],
    },
    {
        "seccion": "Sección V: Registro General de Viajes",
        "clave": "tiempo_viaje_rangos",
        "pregunta": "Tiempo de Duración del Viaje (minutos)",
        "tipo_grafico": "bar",
        "aliases": ["viajes:tiempo_viaje_min"],
    },
    {
        "seccion": "Sección V: Registro General de Viajes",
        "clave": "costo_viaje_rangos",
        "pregunta": "Costo Monetario del Viaje (Bolívares)",
        "tipo_grafico": "bar",
        "aliases": ["viajes:costo_viaje_bs"],
    },
    # Sección VI
    {
        "seccion": "Sección VI: Características de Transporte Público",
        "clave": "rutas_tp_utilizadas_dia",
        "pregunta": "1.- ¿Cuántas rutas de transporte público diferentes utilizó en el día?",
        "tipo_grafico": "bar",
        "aliases": ["rutas_tp_utilizadas_dia", "rutas_tp_dia"],
    },
    {
        "seccion": "Sección VI: Características de Transporte Público",
        "clave": "tiempo_espera_paradas_min",
        "pregunta": "2.- Tiempo total de espera en las paradas (en minutos)",
        "tipo_grafico": "bar",
        "aliases": ["tiempo_espera_paradas_min"],
    },
    {
        "seccion": "Sección VI: Características de Transporte Público",
        "clave": "distancia_residencia_parada_km",
        "pregunta": "3.- ¿Cuántos kilómetros aproximadamente recorrió desde su residencia hasta la parada?",
        "tipo_grafico": "bar",
        "aliases": ["distancia_residencia_parada_km", "km_residencia_parada"],
    },
    {
        "seccion": "Sección VI: Características de Transporte Público",
        "clave": "dificultad_acceso_tp",
        "pregunta": "4.- ¿Ha tenido dificultades para acceder al transporte público en su zona?",
        "tipo_grafico": "donut",
        "aliases": ["dificultad_acceso_tp", "dificultades_acceso_tp"],
    },
    {
        "seccion": "Sección VI: Características de Transporte Público",
        "clave": "principal_dificultad_tp",
        "pregunta": "5.- Si marcó Sí, indique la principal dificultad:",
        "tipo_grafico": "bar",
        "aliases": ["principal_dificultad_tp"],
    },
    {
        "seccion": "Sección VI: Características de Transporte Público",
        "clave": "calificacion_servicio_tp",
        "pregunta": "6.- ¿Considera que el servicio de transporte público es:",
        "tipo_grafico": "donut",
        "aliases": ["calificacion_servicio_tp"],
    },
    {
        "seccion": "Sección VI: Características de Transporte Público",
        "clave": "gasto_semanal_tp_bs",
        "pregunta": "7.- ¿Cuánto gasta semanalmente en transporte (en bolívares)?",
        "tipo_grafico": "bar",
        "aliases": ["gasto_semanal_tp_bs", "gasto_semanal_transporte_bs"],
    },
    {
        "seccion": "Sección VI: Características de Transporte Público",
        "clave": "acuerdo_rutas_directas",
        "pregunta": "8.- ¿Estaría usted de acuerdo en que se creen rutas directas desde su origen a su destino final?",
        "tipo_grafico": "donut",
        "aliases": ["acuerdo_rutas_directas"],
    },
    # Sección VII
    {
        "seccion": "Sección VII: Movilidad No Motorizada y Percepción",
        "clave": "cambio_forma_desplazarse_5a",
        "pregunta": "1.- ¿Ha cambiado su forma de desplazarse en los últimos 5 años?",
        "tipo_grafico": "donut",
        "aliases": ["cambio_forma_desplazarse_5a", "cambio_movilidad_5_anos"],
    },
    {
        "seccion": "Sección VII: Movilidad No Motorizada y Percepción",
        "clave": "motivo_cambio_desplazamiento",
        "pregunta": "2.- Si marcó Sí, ¿por qué motivo?",
        "tipo_grafico": "bar",
        "aliases": ["motivo_cambio_desplazamiento"],
    },
    {
        "seccion": "Sección VII: Movilidad No Motorizada y Percepción",
        "clave": "caminatas_mas_10min",
        "pregunta": "3.- ¿Realiza caminatas de más de 10 minutos como parte de sus desplazamientos?",
        "tipo_grafico": "donut",
        "aliases": ["caminatas_mas_10min"],
    },
    {
        "seccion": "Sección VII: Movilidad No Motorizada y Percepción",
        "clave": "usa_bicicleta_transporte",
        "pregunta": "4.- ¿Utiliza bicicleta como medio de transporte?",
        "tipo_grafico": "donut",
        "aliases": ["usa_bicicleta_transporte", "usa_bicicleta"],
    },
    {
        "seccion": "Sección VII: Movilidad No Motorizada y Percepción",
        "clave": "dias_semana_camina_bicicleta",
        "pregunta": "5.- ¿Cuántos días a la semana camina o usa bicicleta para desplazarse?",
        "tipo_grafico": "bar",
        "aliases": ["dias_semana_camina_bicicleta", "dias_camina_bici_semana"],
    },
    {
        "seccion": "Sección VII: Movilidad No Motorizada y Percepción",
        "clave": "desplazamiento_centro_modo",
        "pregunta": "6.- ¿Realiza desplazamiento en el centro de la ciudad para hacer sus actividades o utiliza el transporte público?",
        "tipo_grafico": "donut",
        "aliases": ["desplazamiento_centro_modo", "modo_actividades_centro"],
    },
    {
        "seccion": "Sección VII: Movilidad No Motorizada y Percepción",
        "clave": "aceras_adecuadas",
        "pregunta": "7.- ¿Considera que las aceras y espacios peatonales son adecuados?",
        "tipo_grafico": "donut",
        "aliases": ["aceras_adecuadas", "acuerdo_acera_comoda", "acera_comoda"],
    },
    {
        "seccion": "Sección VII: Movilidad No Motorizada y Percepción",
        "clave": "seguridad_desplazamiento_centro",
        "pregunta": "8.- ¿Se siente seguro al desplazarse por el centro de la ciudad?",
        "tipo_grafico": "donut",
        "aliases": ["seguridad_desplazamiento_centro", "seguridad_centro"],
    },
    # Sección VIII
    {
        "seccion": "Sección VIII: Esparcimientos y Peatonalidad",
        "clave": "frecuencia_visita_parques",
        "pregunta": "1.- ¿Con qué frecuencia visita parques, plazas u otras áreas de esparcimientos?",
        "tipo_grafico": "donut",
        "aliases": ["frecuencia_visita_parques"],
    },
    {
        "seccion": "Sección VIII: Esparcimientos y Peatonalidad",
        "clave": "actividades_espacios",
        "pregunta": "2.- ¿Qué actividad realiza principalmente en estos espacios?",
        "tipo_grafico": "bar",
        "aliases": ["actividades_espacios", "actividades_parques"],
    },
    {
        "seccion": "Sección VIII: Esparcimientos y Peatonalidad",
        "clave": "suele_hacer_caminatas_ciudad",
        "pregunta": "3.- ¿Suele hacer caminatas por la ciudad?",
        "tipo_grafico": "donut",
        "aliases": ["suele_hacer_caminatas_ciudad", "caminatas_ciudad"],
    },
    {
        "seccion": "Sección VIII: Esparcimientos y Peatonalidad",
        "clave": "seguridad_parques_rutas_dia",
        "pregunta": "7.- ¿Qué tan seguro(a) se siente en parques y rutas peatonales durante el día?",
        "tipo_grafico": "donut",
        "aliases": ["seguridad_parques_rutas_dia", "seguridad_parques_dia", "escala_seguridad_parques"],
    },
    {
        "seccion": "Sección VIII: Esparcimientos y Peatonalidad",
        "clave": "seguridad_parques_rutas_noche",
        "pregunta": "8.- ¿Qué tan seguro(a) se siente en parques y rutas peatonales durante la noche?",
        "tipo_grafico": "donut",
        "aliases": ["seguridad_parques_rutas_noche", "seguridad_parques_noche"],
    },
    {
        "seccion": "Sección VIII: Esparcimientos y Peatonalidad",
        "clave": "calificacion_limpieza_conservacion",
        "pregunta": "9.- ¿Cómo califica la limpieza y conservación de las áreas de esparcimiento?",
        "tipo_grafico": "donut",
        "aliases": ["calificacion_limpieza_conservacion", "calificacion_limpieza_parques", "limpieza_parques"],
    },
    {
        "seccion": "Sección VIII: Esparcimientos y Peatonalidad",
        "clave": "impedimentos_uso_espacios",
        "pregunta": "10.- ¿Qué le impide usar más estos espacios?",
        "tipo_grafico": "bar",
        "aliases": ["impedimentos_uso_espacios", "impedimentos_espacios"],
    },
    {
        "seccion": "Sección VIII: Esparcimientos y Peatonalidad",
        "clave": "satisfaccion_areas_centro",
        "pregunta": "11.- ¿Qué tan satisfecho(a) está con la cantidad y calidad de áreas de esparcimiento y caminata en el centro?",
        "tipo_grafico": "donut",
        "aliases": ["satisfaccion_areas_centro", "satisfaccion_centro"],
    },
    {
        "seccion": "Sección VIII: Esparcimientos y Peatonalidad",
        "clave": "mejoras_prioritarias_espacios",
        "pregunta": "12.- ¿Qué mejoras deberían priorizarse?",
        "tipo_grafico": "bar",
        "aliases": ["mejoras_prioritarias_espacios", "mejoras_prioritarias"],
    },
    {
        "seccion": "Sección VIII: Esparcimientos y Peatonalidad",
        "clave": "dispuesto_participar_actividades_mejoras",
        "pregunta": "14.- ¿Estaría dispuesto(a) a participar en actividades de mejoras de estos espacios?",
        "tipo_grafico": "donut",
        "aliases": ["dispuesto_participar_actividades_mejoras", "disposicion_participar_mejoras", "disposicion_participar"],
    },
    {
        "seccion": "Sección VIII: Esparcimientos y Peatonalidad",
        "clave": "acera_suficiente_comoda",
        "pregunta": "16.- ¿Considera que la acera es suficiente y cómoda para caminar?",
        "tipo_grafico": "donut",
        "aliases": ["acera_suficiente_comoda", "acera_comoda"],
    },
    {
        "seccion": "Sección VIII: Esparcimientos y Peatonalidad",
        "clave": "facilidad_llegar_espacios",
        "pregunta": "18.- ¿Qué tan fácil es llegar desde su hogar a las áreas de esparcimiento o ruta de caminata?",
        "tipo_grafico": "donut",
        "aliases": ["facilidad_llegar_espacios", "facilidad_llegada_parques"],
    },
    {
        "seccion": "Sección VIII: Esparcimientos y Peatonalidad",
        "clave": "esparcimientos_faltantes",
        "pregunta": "19.- ¿Qué esparcimientos considera que faltan en estos espacios?",
        "tipo_grafico": "bar",
        "aliases": ["esparcimientos_faltantes"],
    },
    {
        "seccion": "Sección VIII: Esparcimientos y Peatonalidad",
        "clave": "existe_cruce_peatonal",
        "pregunta": "20.- ¿Existe cruce peatonal en todas las intersecciones?",
        "tipo_grafico": "donut",
        "aliases": ["existe_cruce_peatonal", "cruce_peatonal_todas"],
    },
    {
        "seccion": "Sección VIII: Esparcimientos y Peatonalidad",
        "clave": "seguridad_cruzar_interseccion",
        "pregunta": "22.- ¿Se siente seguro al cruzar esta intersección?",
        "tipo_grafico": "donut",
        "aliases": ["seguridad_cruzar_interseccion"],
    },
    {
        "seccion": "Sección VIII: Esparcimientos y Peatonalidad",
        "clave": "hay_semaforo_peatonal",
        "pregunta": "23.- ¿Hay semáforo peatonal?",
        "tipo_grafico": "donut",
        "aliases": ["hay_semaforo_peatonal"],
    },
    {
        "seccion": "Sección VIII: Esparcimientos y Peatonalidad",
        "clave": "existen_mapas_senales_peatonales",
        "pregunta": "24.- ¿Existen mapas peatonales, señales de destino o de caminata?",
        "tipo_grafico": "donut",
        "aliases": ["existen_mapas_senales_peatonales", "mapas_senales_caminata"],
    },
    {
        "seccion": "Sección VIII: Esparcimientos y Peatonalidad",
        "clave": "movilidad_reducida_sin_ayuda",
        "pregunta": "25.- ¿Puede una persona con movilidad reducida desplazarse sin ayuda por el centro de la ciudad?",
        "tipo_grafico": "donut",
        "aliases": ["movilidad_reducida_sin_ayuda"],
    },
    {
        "seccion": "Sección VIII: Esparcimientos y Peatonalidad",
        "clave": "senalizacion_nombres_calles_visible",
        "pregunta": "26.- ¿Hay señalizaciones de nombres de calles visibles?",
        "tipo_grafico": "donut",
        "aliases": ["senalizacion_nombres_calles_visible", "nombres_calles_visibles"],
    },
    {
        "seccion": "Sección VIII: Esparcimientos y Peatonalidad",
        "clave": "senalizacion_clara_sin_obstaculos",
        "pregunta": "27.- ¿La señalización es clara y sin obstáculos?",
        "tipo_grafico": "donut",
        "aliases": ["senalizacion_clara_sin_obstaculos"],
    },
    {
        "seccion": "Sección VIII: Esparcimientos y Peatonalidad",
        "clave": "seguridad_trayecto_parada",
        "pregunta": "28.- ¿El trayecto a pie hasta la parada es seguro?",
        "tipo_grafico": "donut",
        "aliases": ["seguridad_trayecto_parada", "trayecto_pie_parada_seguro"],
    },
    {
        "seccion": "Sección VIII: Esparcimientos y Peatonalidad",
        "clave": "aire_ruido_aceptables",
        "pregunta": "29.- ¿El aire y el ruido son aceptables para caminar?",
        "tipo_grafico": "donut",
        "aliases": ["aire_ruido_aceptables"],
    },
    {
        "seccion": "Sección VIII: Esparcimientos y Peatonalidad",
        "clave": "conductores_ceden_paso",
        "pregunta": "30.- ¿Los conductores ceden el paso a los peatones?",
        "tipo_grafico": "donut",
        "aliases": ["conductores_ceden_paso"],
    },
    {
        "seccion": "Sección VIII: Esparcimientos y Peatonalidad",
        "clave": "ciudad_prioriza_peaton",
        "pregunta": "31.- ¿Considera que la ciudad prioriza al peatón sobre el automóvil?",
        "tipo_grafico": "donut",
        "aliases": ["ciudad_prioriza_peaton"],
    },
    {
        "seccion": "Sección VIII: Esparcimientos y Peatonalidad",
        "clave": "participado_consultas_espacios",
        "pregunta": "32.- ¿Ha participado en consultas sobre espacios peatonales?",
        "tipo_grafico": "donut",
        "aliases": ["participado_consultas_espacios", "participacion_consultas_peatonales"],
    },
    {
        "seccion": "Sección VIII: Esparcimientos y Peatonalidad",
        "clave": "existen_planes_movilidad_peatonal",
        "pregunta": "33.- ¿Existen planes de movilidad peatonal, presupuesto o normativa de prioridad peatonal?",
        "tipo_grafico": "donut",
        "aliases": ["existen_planes_movilidad_peatonal", "planes_movilidad_peatonal_normativa"],
    },
]


def _build_options_lookup(schema: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    options_map: Dict[str, Dict[str, str]] = {}

    def scan(comp: Dict[str, Any]) -> None:
        key = comp.get("key")
        vals = comp.get("values") or comp.get("data", {}).get("values")
        if key and vals and isinstance(vals, list):
            options_map[key] = {
                str(item.get("value")): str(item.get("label", item.get("value")))
                for item in vals
                if isinstance(item, dict) and "value" in item
            }
        for child in comp.get("components", []):
            scan(child)
        for col in comp.get("columns", []):
            for child in col.get("components", []):
                scan(child)

    scan(schema)
    return options_map


def _humanize_value(
    key: str, val: Any, options_map: Dict[str, Dict[str, str]]
) -> str:
    s = str(val).strip()
    # Check field-specific custom overrides
    for k_ref, overrides in CUSTOM_FIELD_LABELS.items():
        if k_ref in key and s in overrides:
            return overrides[s]

    # Check schema options
    if key in options_map and s in options_map[key]:
        return options_map[key][s]

    # Check common dictionary
    if s.lower() in COMMON_LABELS:
        return COMMON_LABELS[s.lower()]

    # Fallback to human readable string
    return s.replace("_", " ").title()


def aggregate_all_survey_questions(
    schema: Dict[str, Any], rows: List[Dict[str, Any]]
) -> List[PreguntaMetricaOut]:
    """Agrega todas las preguntas predefinidas del cuestionario PDUL."""
    options_map = _build_options_lookup(schema)
    results: List[PreguntaMetricaOut] = []

    for cfg in QUESTIONS_METRIC_CONFIG:
        seccion = cfg["seccion"]
        clave = cfg["clave"]
        pregunta = cfg["pregunta"]
        tipo_grafico = cfg["tipo_grafico"]
        aliases = cfg["aliases"]

        counts: Counter[str] = Counter()
        total_respuestas = 0

        for r in rows:
            val_found = False
            for a in aliases:
                if ":" in a:
                    parent, child = a.split(":", 1)
                    sub_items = r.get(parent, [])
                    if isinstance(sub_items, list):
                        for item in sub_items:
                            if isinstance(item, dict):
                                cv = item.get(child)
                                if cv is not None and cv != "":
                                    total_respuestas += 1
                                    val_found = True
                                    if clave == "edad_residentes":
                                        try:
                                            age = int(cv)
                                            if age < 18:
                                                label = "Menor de 18 años"
                                            elif age <= 35:
                                                label = "18 a 35 años"
                                            elif age <= 50:
                                                label = "36 a 50 años"
                                            elif age <= 65:
                                                label = "51 a 65 años"
                                            else:
                                                label = "Mayor de 65 años"
                                        except Exception:
                                            label = str(cv)
                                        counts[label] += 1
                                    elif clave == "tiempo_viaje_rangos":
                                        try:
                                            t = float(cv)
                                            if t <= 15:
                                                label = "Hasta 15 min"
                                            elif t <= 30:
                                                label = "16 a 30 min"
                                            elif t <= 45:
                                                label = "31 a 45 min"
                                            elif t <= 60:
                                                label = "46 a 60 min"
                                            else:
                                                label = "Más de 60 min"
                                        except Exception:
                                            label = str(cv)
                                        counts[label] += 1
                                    elif clave == "costo_viaje_rangos":
                                        try:
                                            co = float(cv)
                                            if co == 0:
                                                label = "0 Bs (Gratuito / A pie)"
                                            elif co <= 15:
                                                label = "1 a 15 Bs"
                                            elif co <= 30:
                                                label = "16 a 30 Bs"
                                            elif co <= 50:
                                                label = "31 a 50 Bs"
                                            else:
                                                label = "Más de 50 Bs"
                                        except Exception:
                                            label = str(cv)
                                        counts[label] += 1
                                    else:
                                        label = _humanize_value(child, cv, options_map)
                                        counts[label] += 1
                else:
                    if a in r and r[a] is not None and r[a] != "" and r[a] != []:
                        val = r[a]
                        val_found = True
                        total_respuestas += 1
                        if isinstance(val, dict):  # Selectboxes
                            for subk, subv in val.items():
                                if subv:
                                    lbl = _humanize_value(subk, subk, options_map)
                                    counts[lbl] += 1
                        elif isinstance(val, list):
                            for list_item in val:
                                lbl = _humanize_value(a, list_item, options_map)
                                counts[lbl] += 1
                        else:
                            lbl = _humanize_value(a, val, options_map)
                            counts[lbl] += 1
                        break  # Found matching alias for this row

        # Ordenar ítems por frecuencia descendente
        sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        labels = [item[0] for item in sorted_items]
        values = [item[1] for item in sorted_items]

        results.append(
            PreguntaMetricaOut(
                seccion=seccion,
                clave=clave,
                pregunta=pregunta,
                tipo_grafico=tipo_grafico,
                total_respuestas=total_respuestas,
                labels=labels,
                values=values,
            )
        )

    return results
