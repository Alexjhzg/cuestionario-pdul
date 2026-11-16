"""Fixtures y datos de prueba para la suite E2E Opaque-Box del Cuestionario PDUL.

Incluye:
- Catálogos oficiales de Maturín (11 parroquias, 8 modos de transporte, 8 motivos de viaje).
- Escenarios realistas de encuestas ciudadanas (hogar unipersonal, familia multimodal, lote rural).
- Casos de borde y combinaciones inválidas para validación de contratos.
"""

from typing import Any, Dict, List
from uuid import uuid4

PARROQUIAS_MATURIN: List[str] = [
    "alto_de_los_godos",
    "boqueron",
    "las_cocuizas",
    "la_cruz",
    "san_simon",
    "santa_cruz",
    "el_corozo",
    "el_furrial",
    "jusepin",
    "la_pica",
    "san_vicente",
]

PARROQUIAS_NOMBRES: Dict[str, str] = {
    "alto_de_los_godos": "Alto de Los Godos",
    "boqueron": "Boquerón",
    "las_cocuizas": "Las Cocuizas",
    "la_cruz": "La Cruz",
    "san_simon": "San Simón",
    "santa_cruz": "Santa Cruz",
    "el_corozo": "El Corozo",
    "el_furrial": "El Furrial",
    "jusepin": "Jusepín",
    "la_pica": "La Pica",
    "san_vicente": "San Vicente",
}

MODOS_TRANSPORTE: Dict[str, str] = {
    "1": "A pie",
    "2": "Bicicleta",
    "3": "Motocicleta",
    "4": "Automóvil Particular",
    "5": "Taxi",
    "6": "Transporte público",
    "7": "Transporte informal",
    "8": "Otro",
}

MOTIVOS_VIAJE: Dict[str, str] = {
    "1": "Trabajo",
    "2": "Estudio / Escuela / Universidad",
    "3": "Compras / Abastecimiento",
    "4": "Trámites / Gestiones personales",
    "5": "Salud / Consulta médica",
    "6": "Recreación / Deporte / Ocio",
    "7": "Visita familiar o amigos",
    "8": "Regreso al hogar",
}

# ---------------------------------------------------------------------------
# Escenario 1: Estudiante unipersonal en San Simón (Movilidad Activa / A pie)
# ---------------------------------------------------------------------------
SAMPLE_SURVEY_SINGLE_PERSON_STUDENT: Dict[str, Any] = {
    "client_submission_id": "a1b2c3d4-e5f6-4a1b-8c2d-3e4f5a6b7c8d",
    "data": {
        "schema_version": "1.0.0",
        "parroquia": "san_simon",
        "zona_residencia_od": "01",
        "sector": "Centro de Maturín",
        "avenida_calle": "Calle Monagas con Av. Bolívar",
        "casa_apartamento": "Edif. Don Manuel, Piso 2, Apto 2B",
        "tipo_vivienda": "apartamento",
        "cuartos_dormir": 1,
        "grupos_gastos_hogares": 1,
        "numero_hogar": 1,
        "personas_hogar": 1,
        "regimen_tenencia": "alquilada",
        "residentes": [
            {
                "persona_numero": 1,
                "nombre_primer_apellido": "Estudiante Anonimizado",
                "parentesco": "1",  # Jefe/a
                "sexo": "femenino",
                "edad": 21,
                "asiste_educacion": "si",
                "nivel_instruccion": "5",  # Universitario
                "ocupacion_principal": "estudiante",
                "sector_economico": "educacion",
                "trabajo_horas": 0,
                "trabajo_ingreso": 0.0,
                "condicion_actividad": "estudiante",
                "medio_transporte_habitual": "3",  # A pie
            }
        ],
        "disponibilidad_vehicular": {
            "tiene_licencia": "no",
            "tiene_vehiculo_propio": "no",
            "tipo_vehiculo": "ninguno",
            "cantidad_vehiculos": 0,
        },
        "viajes": [
            {
                "numero_viaje": 1,
                "persona_numero": 1,
                "origen": "Residencia San Simón Centro",
                "zona_origen_od": "01",
                "hora_salida": "07:30",
                "destino": "Universidad de Oriente (UDO Los Guaritos)",
                "zona_destino_od": "03",
                "hora_llegada": "08:00",
                "motivo_viaje": "2",  # Estudio
                "modo_principal": "3",  # A pie
                "modo_secundario": "ninguno",
                "tiempo_minutos": 30,
                "costo_bolivares": 0.0,
            },
            {
                "numero_viaje": 2,
                "persona_numero": 1,
                "origen": "Universidad de Oriente (UDO Los Guaritos)",
                "zona_origen_od": "03",
                "hora_salida": "12:30",
                "destino": "Residencia San Simón Centro",
                "zona_destino_od": "01",
                "hora_llegada": "13:00",
                "motivo_viaje": "8",  # Regreso al hogar
                "modo_principal": "3",  # A pie
                "modo_secundario": "ninguno",
                "tiempo_minutos": 30,
                "costo_bolivares": 0.0,
            },
        ],
        # Sección VII: Movilidad activa
        "habitos_peatonales": {
            "frecuencia_caminata_semanal": "diario",
            "motivo_principal_caminata": "cercania",
            "infraestructura_peatonal_evaluacion": "regular",
            "cuenta_con_bicicleta": "no",
            "dispuesto_usar_ciclovia": "si",
        },
        # Sección VIII: Esparcimiento y Peatonalidad
        "diagnostico_esparcimiento": {
            "p1_actividades_recreativas": ["parque_plaza", "caminar"],
            "p20_cruce_peatonal_semaforizado": "no",  # Salto condicional a P23
            "p23_iluminacion_nocturna": "deficiente",
            "p24_sensacion_seguridad": "media",
            "p29_prioridad_mejora_urbana": "aceras_iluminacion",
        },
        "cedula": "28123456",
        "telefono": "04141234567",
        "email": "estudiante@ejemplo.ve",
    },
}

# ---------------------------------------------------------------------------
# Escenario 2: Familia de 4 personas en Boquerón con viajes multimodales
# ---------------------------------------------------------------------------
SAMPLE_SURVEY_FAMILY_MULTIMODAL: Dict[str, Any] = {
    "client_submission_id": "b2c3d4e5-f6a1-4b2c-9d3e-4f5a6b7c8d9e",
    "data": {
        "schema_version": "1.0.0",
        "parroquia": "boqueron",
        "zona_residencia_od": "05",
        "sector": "Tipuro II",
        "avenida_calle": "Avenida Las Palmeras, Manzana 14",
        "casa_apartamento": "Casa Nro 28",
        "tipo_vivienda": "casa_quinta",
        "cuartos_dormir": 3,
        "grupos_gastos_hogares": 1,
        "numero_hogar": 1,
        "personas_hogar": 4,
        "regimen_tenencia": "propia_pagada",
        "residentes": [
            {
                "persona_numero": 1,
                "nombre_primer_apellido": "Jefe de Hogar",
                "parentesco": "1",
                "sexo": "masculino",
                "edad": 45,
                "asiste_educacion": "no",
                "nivel_instruccion": "4",  # TSU / Técnico
                "ocupacion_principal": "empleado_privado",
                "sector_economico": "comercio",
                "trabajo_horas": 40,
                "trabajo_ingreso": 450.0,
                "condicion_actividad": "ocupado",
                "medio_transporte_habitual": "1",  # Transporte público
            },
            {
                "persona_numero": 2,
                "nombre_primer_apellido": "Cónyuge",
                "parentesco": "2",
                "sexo": "femenino",
                "edad": 42,
                "asiste_educacion": "no",
                "nivel_instruccion": "5",
                "ocupacion_principal": "profesional_independiente",
                "sector_economico": "servicios",
                "trabajo_horas": 35,
                "trabajo_ingreso": 500.0,
                "condicion_actividad": "ocupado",
                "medio_transporte_habitual": "2",  # Auto particular
            },
            {
                "persona_numero": 3,
                "nombre_primer_apellido": "Hijo Mayor",
                "parentesco": "3",
                "sexo": "masculino",
                "edad": 16,
                "asiste_educacion": "si",
                "nivel_instruccion": "3",  # Secundaria
                "ocupacion_principal": "estudiante",
                "sector_economico": "educacion",
                "trabajo_horas": 0,
                "trabajo_ingreso": 0.0,
                "condicion_actividad": "estudiante",
                "medio_transporte_habitual": "1",  # Transporte público
            },
            {
                "persona_numero": 4,
                "nombre_primer_apellido": "Hija Menor",
                "parentesco": "3",
                "sexo": "femenino",
                "edad": 9,
                "asiste_educacion": "si",
                "nivel_instruccion": "2",  # Primaria
                "ocupacion_principal": "estudiante",
                "sector_economico": "educacion",
                "trabajo_horas": 0,
                "trabajo_ingreso": 0.0,
                "condicion_actividad": "estudiante",
                "medio_transporte_habitual": "3",  # A pie a escuela cercana
            },
        ],
        "disponibilidad_vehicular": {
            "tiene_licencia": "si",
            "tiene_vehiculo_propio": "si",
            "tipo_vehiculo": "automovil",
            "cantidad_vehiculos": 1,
        },
        "viajes": [
            {
                "numero_viaje": 1,
                "persona_numero": 1,
                "origen": "Hogar Tipuro II Boquerón",
                "zona_origen_od": "05",
                "hora_salida": "06:45",
                "destino": "Zona Industrial Maturín",
                "zona_destino_od": "10",
                "hora_llegada": "07:30",
                "motivo_viaje": "1",  # Trabajo
                "modo_principal": "1",  # Transporte público
                "modo_secundario": "3",  # A pie
                "tiempo_minutos": 45,
                "costo_bolivares": 25.0,
            },
            {
                "numero_viaje": 2,
                "persona_numero": 2,
                "origen": "Hogar Tipuro II Boquerón",
                "zona_origen_od": "05",
                "hora_salida": "07:15",
                "destino": "Centro Comercial Petroriente",
                "zona_destino_od": "04",
                "hora_llegada": "07:35",
                "motivo_viaje": "1",  # Trabajo
                "modo_principal": "2",  # Auto particular
                "modo_secundario": "ninguno",
                "tiempo_minutos": 20,
                "costo_bolivares": 40.0,
            },
            {
                "numero_viaje": 3,
                "persona_numero": 1,
                "origen": "Zona Industrial Maturín",
                "zona_origen_od": "10",
                "hora_salida": "17:00",
                "destino": "Hogar Tipuro II Boquerón",
                "zona_destino_od": "05",
                "hora_llegada": "17:50",
                "motivo_viaje": "8",  # Regreso
                "modo_principal": "1",  # Transporte público
                "modo_secundario": "3",
                "tiempo_minutos": 50,
                "costo_bolivares": 25.0,
            },
            {
                "numero_viaje": 4,
                "persona_numero": 2,
                "origen": "Centro Comercial Petroriente",
                "zona_origen_od": "04",
                "hora_salida": "16:30",
                "destino": "Hogar Tipuro II Boquerón",
                "zona_destino_od": "05",
                "hora_llegada": "16:55",
                "motivo_viaje": "8",  # Regreso (1-touch return trip)
                "modo_principal": "2",
                "modo_secundario": "ninguno",
                "tiempo_minutos": 25,
                "costo_bolivares": 40.0,
            },
        ],
        # Sección VI: Transporte público (activada porque persona 1 usó modo "1")
        "transporte_publico": {
            "linea_ruta_utilizada": "Ruta 20 Tipuro - Centro",
            "tiempo_espera_minutos": 20,
            "frecuencia_servicio": "regular",
            "gasto_semanal_tp_bs": 250.0,
            "calificacion_servicio_tp": "regular",
            "motivo_inconformidad": "frecuencia_y_comodidad",
        },
        "habitos_peatonales": {
            "frecuencia_caminata_semanal": "ocasional",
            "motivo_principal_caminata": "salud",
            "infraestructura_peatonal_evaluacion": "buena",
            "cuenta_con_bicicleta": "si",
            "dispuesto_usar_ciclovia": "si",
        },
        "diagnostico_esparcimiento": {
            "p1_actividades_recreativas": ["parque_plaza", "deportes"],
            "p20_cruce_peatonal_semaforizado": "si",  # Salto a P21 y P22
            "p21_tiempo_espera_peatonal": "adecuado",
            "p22_rampa_accesibilidad": "si",
            "p23_iluminacion_nocturna": "buena",
            "p24_sensacion_seguridad": "alta",
            "p29_prioridad_mejora_urbana": "ciclovias",
        },
        "cedula": "15678901",
        "telefono": "04249876543",
        "email": "familia.boqueron@ejemplo.ve",
    },
}

# ---------------------------------------------------------------------------
# Escenario 3: Lote de 3 encuestas de campo en parroquias rurales
# ---------------------------------------------------------------------------
def generate_rural_survey(parroquia: str, cedula: str, submission_uuid: str) -> Dict[str, Any]:
    return {
        "client_submission_id": submission_uuid,
        "data": {
            "schema_version": "1.0.0",
            "parroquia": parroquia,
            "zona_residencia_od": "08",
            "sector": f"Sector Rural {parroquia.replace('_', ' ').title()}",
            "avenida_calle": "Carretera Nacional",
            "casa_apartamento": "Finca La Esperanza",
            "tipo_vivienda": "casa_quinta",
            "cuartos_dormir": 2,
            "grupos_gastos_hogares": 1,
            "numero_hogar": 1,
            "personas_hogar": 2,
            "regimen_tenencia": "propia_pagada",
            "residentes": [
                {
                    "persona_numero": 1,
                    "nombre_primer_apellido": "Productor Agropecuario",
                    "parentesco": "1",
                    "sexo": "masculino",
                    "edad": 52,
                    "asiste_educacion": "no",
                    "nivel_instruccion": "3",
                    "ocupacion_principal": "productor_agricola",
                    "sector_economico": "agricultura",
                    "trabajo_horas": 48,
                    "trabajo_ingreso": 600.0,
                    "condicion_actividad": "ocupado",
                    "medio_transporte_habitual": "5",  # Moto
                },
                {
                    "persona_numero": 2,
                    "nombre_primer_apellido": "Cónyuge Rural",
                    "parentesco": "2",
                    "sexo": "femenino",
                    "edad": 49,
                    "asiste_educacion": "no",
                    "nivel_instruccion": "2",
                    "ocupacion_principal": "labores_hogar",
                    "sector_economico": "ninguno",
                    "trabajo_horas": 0,
                    "trabajo_ingreso": 0.0,
                    "condicion_actividad": "hogar",
                    "medio_transporte_habitual": "5",
                },
            ],
            "disponibilidad_vehicular": {
                "tiene_licencia": "si",
                "tiene_vehiculo_propio": "si",
                "tipo_vehiculo": "motocicleta",
                "cantidad_vehiculos": 1,
            },
            "viajes": [
                {
                    "numero_viaje": 1,
                    "persona_numero": 1,
                    "origen": f"Hogar en {parroquia}",
                    "zona_origen_od": "08",
                    "hora_salida": "06:00",
                    "destino": "Mercado Municipal de Maturín",
                    "zona_destino_od": "01",
                    "hora_llegada": "06:45",
                    "motivo_viaje": "1",  # Trabajo/Comercio
                    "modo_principal": "5",  # Moto
                    "modo_secundario": "ninguno",
                    "tiempo_minutos": 45,
                    "costo_bolivares": 30.0,
                },
                {
                    "numero_viaje": 2,
                    "persona_numero": 1,
                    "origen": "Mercado Municipal de Maturín",
                    "zona_origen_od": "01",
                    "hora_salida": "12:00",
                    "destino": f"Hogar en {parroquia}",
                    "zona_destino_od": "08",
                    "hora_llegada": "12:45",
                    "motivo_viaje": "8",  # Regreso
                    "modo_principal": "5",  # Moto
                    "modo_secundario": "ninguno",
                    "tiempo_minutos": 45,
                    "costo_bolivares": 30.0,
                },
            ],
            "habitos_peatonales": {
                "frecuencia_caminata_semanal": "ocasional",
                "motivo_principal_caminata": "trabajo",
                "infraestructura_peatonal_evaluacion": "deficiente",
                "cuenta_con_bicicleta": "no",
                "dispuesto_usar_ciclovia": "no",
            },
            "diagnostico_esparcimiento": {
                "p1_actividades_recreativas": ["caminar"],
                "p20_cruce_peatonal_semaforizado": "no",
                "p23_iluminacion_nocturna": "muy_deficiente",
                "p24_sensacion_seguridad": "media",
                "p29_prioridad_mejora_urbana": "transporte_rural",
            },
            "cedula": cedula,
            "telefono": "04125556677",
            "email": f"productor_{parroquia}@ejemplo.ve",
        },
    }

SAMPLE_RURAL_BATCH: List[Dict[str, Any]] = [
    generate_rural_survey("el_corozo", "12345678", "c3d4e5f6-a1b2-4c3d-8e4f-5a6b7c8d9e0f"),
    generate_rural_survey("el_furrial", "13456789", "d4e5f6a1-b2c3-4d4e-9f5a-6b7c8d9e0f1a"),
    generate_rural_survey("jusepin", "14567890", "e5f6a1b2-c3d4-4e5f-af6b-7c8d9e0f1a2b"),
]

# ---------------------------------------------------------------------------
# Esquema exportado desde Form Builder para una encuesta personalizada
# ---------------------------------------------------------------------------
SAMPLE_FORM_BUILDER_CUSTOM_SURVEY: Dict[str, Any] = {
    "display": "form",
    "title": "Consulta Ciudadana Maturín 2030",
    "name": "consulta_maturin_2030",
    "path": "consulta-maturin-2030",
    "components": [
        {
            "type": "hidden",
            "key": "schema_version",
            "defaultValue": "1.0.0",
        },
        {
            "type": "select",
            "key": "parroquia",
            "label": "Parroquia de Residencia",
            "required": True,
            "data": {
                "values": [
                    {"label": PARROQUIAS_NOMBRES[p], "value": p}
                    for p in PARROQUIAS_MATURIN
                ]
            },
        },
        {
            "type": "textfield",
            "key": "cedula",
            "label": "Cédula de Identidad",
            "required": True,
            "validate": {
                "pattern": "^[0-9]{6,9}$",
                "maxLength": 9,
                "minLength": 6,
            },
        },
        {
            "type": "radio",
            "key": "prioridad_inversion",
            "label": "¿Cuál considera la máxima prioridad de inversión municipal?",
            "required": True,
            "values": [
                {"label": "Vialidad y asfaltado", "value": "vialidad"},
                {"label": "Transporte público urbano", "value": "transporte"},
                {"label": "Ciclovías y aceras peatonales", "value": "movilidad_activa"},
                {"label": "Alumbrado público y seguridad", "value": "alumbrado"},
            ],
        },
        {
            "type": "textarea",
            "key": "propuesta_ciudadana",
            "label": "Describa brevemente su propuesta para la ciudad",
            "validate": {
                "maxLength": 500,
            },
        },
        {
            "type": "button",
            "key": "submit",
            "label": "Enviar Propuesta",
            "action": "submit",
            "theme": "primary",
        },
    ],
}
