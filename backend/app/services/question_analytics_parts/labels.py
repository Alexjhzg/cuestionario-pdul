"""Catálogos de etiquetas y normalización humana de opciones para analítica PDUL."""

from typing import Any, Dict

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
    for k_ref, overrides in CUSTOM_FIELD_LABELS.items():
        if k_ref in key and s in overrides:
            return overrides[s]

    if key in options_map and s in options_map[key]:
        return options_map[key][s]

    if s.lower() in COMMON_LABELS:
        return COMMON_LABELS[s.lower()]

    return s.replace("_", " ").title()
