"""Script de población de datos sintéticos realistas para el PDUL Maturín.
Genera 100 encuestas ciudadanas con perfiles socio-demográficos,
cadenas de viajes y valoraciones de movilidad urbana.
"""

import json
import random
import sqlite3
import uuid
from datetime import datetime, timedelta

DB_PATH = "pdul_dev.db"
SURVEY_ID = "00000000-0000-0000-0000-000000000001"

PARROQUIAS_PESOS = [
    ("san_simon", 30),
    ("alto_de_los_godos", 24),
    ("boqueron", 16),
    ("las_cocuizas", 14),
    ("santa_cruz", 8),
    ("san_vicente", 3),
    ("la_pica", 2),
    ("el_furrial", 1),
    ("jusepin", 1),
    ("la_cruz", 1),
]

SECTORES_POR_PARROQUIA = {
    "san_simon": ["Centro", "Juanico", "Las Avenidas", "La Muralla", "Brisas del Orinoco", "Viento Colao"],
    "alto_de_los_godos": ["Los Guaritos I", "Los Guaritos II", "Los Guaritos III", "La Gran Victoria", "Fundemos", "Morichal"],
    "boqueron": ["Tipuro", "Palma Real", "La Toscana", "Los Girasoles", "Villas del Parque", "Agana"],
    "las_cocuizas": ["El Silencio", "Sabana Grande", "La Floresta", "Brisas del Aeropuerto", "Nazareno"],
    "santa_cruz": ["Zona Industrial", "Paramaconi", "Santa Elena", "San Rafael"],
    "san_vicente": ["San Vicente Centro", "Pueblo Libre", "El Corozo Norte"],
    "la_pica": ["La Pica Casco", "El Costo", "Vuelta Larga"],
    "el_furrial": ["El Furrial Centro", "Mano de Dios"],
    "jusepin": ["Jusepín Casco", "Campo Rojo"],
    "la_cruz": ["La Cruz Centro", "El Guayabal"],
}

NOMBRES_MASC = ["Carlos", "José", "Luis", "Jesús", "Manuel", "Alejandro", "Pedro", "Miguel", "Rafael", "Héctor", "Eduardo", "Víctor"]
NOMBRES_FEM = ["María", "Carmen", "Ana", "Luisa", "Elena", "Patricia", "Yusmary", "Rosa", "Gabriela", "Daniela", "Andreína", "Coromoto"]
APELLIDOS = ["Rodríguez", "González", "Hernández", "Pérez", "García", "Martínez", "López", "Sánchez", "Rondón", "Guzmán", "Subero", "Velasquez", "Febres"]

ZONAS_DESTINO_COMUNES = ["san_simon", "alto_de_los_godos", "boqueron", "las_cocuizas", "santa_cruz"]

def choose_weighted(items_with_weights):
    population, weights = zip(*items_with_weights)
    return random.choices(population, weights=weights, k=1)[0]

def generate_residentes(num_residentes):
    residentes = []
    parentesco_roles = ["1", "2", "3", "3", "3", "4", "5"]
    for i in range(1, num_residentes + 1):
        es_masc = random.random() < 0.48
        nom = random.choice(NOMBRES_MASC) if es_masc else random.choice(NOMBRES_FEM)
        ape = random.choice(APELLIDOS)
        
        if i == 1:
            parentesco = "1"
            edad = random.randint(24, 68)
        else:
            parentesco = random.choice(parentesco_roles[1:])
            if parentesco == "2":
                edad = random.randint(22, 65)
            elif parentesco == "3":
                edad = random.randint(3, 26)
            elif parentesco == "4":
                edad = random.randint(55, 82)
            else:
                edad = random.randint(18, 45)
                
        if edad < 6:
            nivel_ed = "1"
            actividad = "3"
        elif edad < 17:
            nivel_ed = "2"
            actividad = "2"
        else:
            nivel_ed = choose_weighted([("2", 30), ("3", 25), ("4", 35), ("5", 10)])
            actividad = choose_weighted([("1", 60), ("2", 15), ("3", 15), ("4", 8), ("5", 2)])
            
        residentes.append({
            "persona_numero": i,
            "nombres": f"{nom} {ape}",
            "parentesco": parentesco,
            "sexo": "1" if es_masc else "2",
            "edad": edad,
            "nivel_educativo": nivel_ed,
            "actividad_principal": actividad
        })
    return residentes

def generate_viajes(parroquia_origen, num_viajes):
    viajes = []
    horas_pico = [("06:30", "07:15"), ("07:00", "07:40"), ("07:30", "08:15"), ("12:15", "13:00"), ("16:45", "17:30"), ("17:30", "18:20")]
    modos_ponderados = [
        ("6", 48), # Bus/Buseta
        ("7", 22), # Carrito por puesto
        ("4", 15), # Automóvil particular
        ("1", 7),  # A pie
        ("3", 5),  # Motocicleta
        ("5", 2),  # Taxi
        ("2", 1),  # Bicicleta
    ]
    
    for v in range(1, num_viajes + 1):
        if v == 1:
            z_orig = parroquia_origen
            # Destino principal suele ser San Simón (Centro / comercial) o Godos
            z_dest = choose_weighted([
                ("san_simon", 55),
                ("alto_de_los_godos", 20),
                ("santa_cruz", 15),
                ("las_cocuizas", 5),
                ("boqueron", 5),
            ])
            proposito = choose_weighted([("1", 60), ("2", 25), ("3", 10), ("4", 5)])
            t_orig, t_dest = horas_pico[random.randint(0, 2)]
        elif v == 2:
            # Retorno al hogar
            z_orig = "san_simon"
            z_dest = parroquia_origen
            proposito = "5" # Regreso al hogar / otros
            t_orig, t_dest = horas_pico[random.randint(4, 5)]
        else:
            z_orig = parroquia_origen
            z_dest = random.choice(ZONAS_DESTINO_COMUNES)
            proposito = choose_weighted([("3", 45), ("4", 30), ("6", 25)]) # Compras, salud, recreacion
            t_orig, t_dest = horas_pico[3]

        modo = choose_weighted(modos_ponderados)
        
        # Tiempos y costos realistas
        if modo == "1":
            tiempo_min = random.randint(10, 25)
            costo_bs = 0.0
        elif modo == "2":
            tiempo_min = random.randint(15, 30)
            costo_bs = 0.0
        elif modo == "4":
            tiempo_min = random.randint(15, 30)
            costo_bs = random.choice([0.0, 30.0, 50.0]) # Gasolina
        elif modo == "6":
            tiempo_min = random.randint(25, 50)
            costo_bs = 15.0 # Pasaje urbano Maturín
        elif modo == "7":
            tiempo_min = random.randint(20, 40)
            costo_bs = 25.0 # Por puesto
        elif modo == "3":
            tiempo_min = random.randint(12, 25)
            costo_bs = 10.0
        else:
            tiempo_min = random.randint(15, 35)
            costo_bs = random.choice([70.0, 100.0, 150.0]) # Taxi

        viajes.append({
            "persona_numero": 1,
            "viaje_numero": v,
            "zona_od_origen": z_orig,
            "lugar_origen_especifico": "Residencia habitual" if v == 1 else "Lugar de destino",
            "zona_od_destino": z_dest,
            "lugar_destino_especifico": "Lugar de trabajo / estudio / comercio",
            "hora_salida": t_orig,
            "hora_llegada": t_dest,
            "tiempo_viaje_min": tiempo_min,
            "costo_viaje_bs": costo_bs,
            "modo_principal": modo,
            "proposito_viaje": proposito
        })
    return viajes

def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Verificar existencia de encuesta activa
    cur.execute("SELECT id FROM encuestas WHERE id = ?", (SURVEY_ID,))
    if not cur.fetchone():
        print(f"Creando encuesta maestra {SURVEY_ID}...")
        cur.execute("""
            INSERT INTO encuestas (id, titulo, slug, tipo_instrumento, esquema_formio, activa)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            SURVEY_ID,
            "Encuesta Origen-Destino Maturín (PDUL)",
            "cuestionario-od-maturin",
            "encuesta_od_pdul",
            "{}",
            1
        ))

    # Limpiar únicamente las respuestas ciudadanas asociadas a la encuesta PDUL
    cur.execute("DELETE FROM respuestas_ciudadanas WHERE encuesta_id = ?", (SURVEY_ID,))
    print(f"Limpieza completada. Filas previas eliminadas: {cur.rowcount}")

    # Generar 100 ciudadanos con distribución verosímil
    total_viajes_count = 0
    total_residentes_count = 0
    
    for i in range(1, 101):
        submission_id = str(uuid.uuid4())
        parroquia = choose_weighted(PARROQUIAS_PESOS)
        sectores = SECTORES_POR_PARROQUIA.get(parroquia, ["Centro"])
        sector = random.choice(sectores)
        
        # Tamaño familiar: 1 a 6 residentes
        num_res = choose_weighted([(1, 10), (2, 20), (3, 30), (4, 25), (5, 10), (6, 5)])
        residentes = generate_residentes(num_res)
        total_residentes_count += len(residentes)
        
        # Viajes del hogar: 1 a 4 viajes
        num_viajes = choose_weighted([(1, 20), (2, 50), (3, 20), (4, 10)])
        viajes = generate_viajes(parroquia, num_viajes)
        total_viajes_count += len(viajes)
        
        # Indicadores de transporte y espacio público
        calif_tp = choose_weighted([
            ("regular", 42),
            ("malo", 32),
            ("bueno", 16),
            ("muy_malo", 8),
            ("muy_bueno", 2)
        ])
        
        dificultades_tp = choose_weighted([
            ("frecuencia_baja", 44),
            ("sobrecupo", 26),
            ("falta_de_rutas", 16),
            ("inseguridad", 10),
            ("costo", 4)
        ])
        
        seguridad_centro = choose_weighted([
            ("inseguro", 38),
            ("neutral", 32),
            ("seguro", 18),
            ("muy_inseguro", 9),
            ("muy_seguro", 3)
        ])
        
        mejoras_prioritarias = choose_weighted([
            ("mantenimiento_existentes", 34),
            ("rutas_peatonales_ciclovias", 24),
            ("iluminacion", 18),
            ("seguridad_policial", 14),
            ("mas_parques_plazas", 6),
            ("espacios_deportivos", 4)
        ])
        
        tipo_vivienda = choose_weighted([
            ("casa", 60),
            ("apartamento_edificio", 22),
            ("quinta_casa_quinta", 10),
            ("vivienda_rustica", 5),
            ("casa_vecindad", 3)
        ])
        
        tenencia_vivienda = choose_weighted([
            ("propia_pagada", 55),
            ("alquilada", 25),
            ("propia_pagandose", 10),
            ("cedida_familiar", 10)
        ])

        datos = {
            "parroquia": parroquia,
            "comunidad_sector": sector,
            "zona_residencia_od": parroquia,
            "tipo_vivienda": tipo_vivienda,
            "tenencia_vivienda": tenencia_vivienda,
            "total_cuartos_vivienda": random.randint(2, 6),
            "cuartos_dormir_hogar": random.randint(1, 4),
            "numero_personas_hogar": num_res,
            "residentes": residentes,
            "viajes": viajes,
            "rutas_tp_dia": random.randint(1, 4),
            "tiempo_espera_paradas_min": random.choice([15, 20, 25, 30, 40, 45, 60]),
            "km_residencia_parada": round(random.uniform(0.1, 1.5), 2),
            "dificultades_acceso_tp": dificultades_tp,
            "principal_dificultad_tp": dificultades_tp,
            "calificacion_servicio_tp": calif_tp,
            "gasto_semanal_transporte_bs": random.choice([120, 150, 200, 250, 300, 400, 500]),
            "acuerdo_rutas_directas": choose_weighted([("totalmente_de_acuerdo", 65), ("de_acuerdo", 25), ("neutral", 8), ("en_desacuerdo", 2)]),
            "seguridad_centro": seguridad_centro,
            "dias_camina_bici_semana": random.randint(1, 6),
            "acuerdo_acera_comoda": choose_weighted([("en_desacuerdo", 45), ("totalmente_en_desacuerdo", 25), ("neutral", 20), ("de_acuerdo", 10)]),
            "frecuencia_visita_parques": choose_weighted([("ocasionalmente", 40), ("mensual", 25), ("semanal", 20), ("nunca", 10), ("diario", 5)]),
            "escala_seguridad_parques": choose_weighted([("poco_seguro", 40), ("neutral", 30), ("bastante_seguro", 15), ("nada_seguro", 12), ("muy_seguro", 3)]),
            "calificacion_limpieza_parques": choose_weighted([("regular", 45), ("mala", 30), ("buena", 18), ("muy_mala", 5), ("muy_buena", 2)]),
            "mejoras_prioritarias": mejoras_prioritarias,
            "disposicion_participar": choose_weighted([("si", 70), ("tal_vez", 22), ("no", 8)]),
            "acepta_declaracion": True
        }
        
        cur.execute("""
            INSERT INTO respuestas_ciudadanas (
                encuesta_id, client_submission_id, cedula, parroquia, zona_od, datos, fecha_registro
            ) VALUES (?, ?, ?, ?, ?, ?, datetime('now', ?))
        """, (
            SURVEY_ID,
            submission_id,
            None, # Cédula no requerida por privacidad ciudadana
            parroquia,
            parroquia,
            json.dumps(datos, ensure_ascii=False),
            f"-{random.randint(0, 14)} days"
        ))

    conn.commit()
    conn.close()
    print("=" * 60)
    print(f"ÉXITO: Se insertaron 100 respuestas ciudadanas realistas.")
    print(f"Total residentes censados: {total_residentes_count}")
    print(f"Total viajes calculados: {total_viajes_count}")
    print("=" * 60)

if __name__ == "__main__":
    main()

