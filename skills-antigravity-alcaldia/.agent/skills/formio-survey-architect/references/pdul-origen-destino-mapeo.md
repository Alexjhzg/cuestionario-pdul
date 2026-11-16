# Mapeo de la Encuesta Origen-Destino (PDUL Maturín) a Form.io

Este documento de referencia detalla cómo estructurar las **8 secciones** del *Cuestionario Origen-Destino (Plan de Movilidad Urbana - PDUL)* de la Alcaldía Bolivariana del Municipio Maturín dentro de un esquema JSON de `@formio/js`.

---

## Catálogo Oficial de Parroquias del Municipio Maturín (`parroquia`)

Usa siempre estos valores estandarizados (`snake_case`) en el componente `parroquia` para garantizar compatibilidad directa con las capas `GeoJSON` en Leaflet y las consultas agrupadas en PostgreSQL:

| Código (`value`) | Etiqueta (`label`) | Tipo |
| :--- | :--- | :--- |
| `alto_de_los_godos` | Alto de los Godos | Urbana |
| `boqueron` | Boquerón | Urbana |
| `las_cocuizas` | Las Cocuizas | Urbana |
| `la_cruz` | La Cruz | Urbana |
| `san_simon` | San Simón (Centro) | Urbana |
| `el_corozo` | El Corozo | Rural / Periurbana |
| `el_furrial` | El Furrial | Rural / Periurbana |
| `jusepin` | Jusepín | Rural / Periurbana |
| `la_pica` | La Pica | Rural / Periurbana |
| `san_vicente` | San Vicente | Rural / Periurbana |
| `santa_cruz` | Santa Cruz | Urbana |

---

## Estructura de Secciones y Componentes Form.io

### Sección I: Identificación de la Unidad Residencial (`panel_seccion_i`)
- `parroquia` (`select`, requerido): Parroquia según catálogo municipal.
- `comunidad_sector` (`textfield`, requerido): Nombre de la comunidad o sector.
- `zona_residencia_od` (`textfield` o `select`, requerido): Código de Zona O-D según zonificación del PDUL.
- `avenida_calle` (`textfield`, requerido): Avenida o calle.
- `casa_apartamento` (`textfield`, requerido): Identificador de casa, quinta o apartamento.
- `cedula` (`textfield`, opcional en PDUL / requerido en consulta ciudadana): Cédula del informante calificado (`^[0-9]{6,9}$`).

### Sección II: Datos de la Vivienda (`panel_seccion_ii`)
- `tipo_vivienda` (`radio`, requerido):
  - `quinta_casa_quinta`, `casa`, `apartamento_edificio`, `apartamento_quinta_casa`, `casa_vecindad`, `vivienda_rustica`, `otro`.
- `tipo_vivienda_otro` (`textfield`, condicional cuando `tipo_vivienda == "otro"`).
- `total_cuartos_vivienda` (`number`, requerido, `min: 1`, `max: 30`): Total de cuartos excluyendo baños, pasillos, balcones, cocina y lavaderos.

### Sección III: Datos del Hogar (`panel_seccion_iii`)
- `grupos_gastos_separados` (`number`, requerido, `min: 1`).
- `hogar_numero` (`number`, requerido, `min: 1`).
- `cuartos_dormir_hogar` (`number`, requerido, `min: 0`).
- `numero_personas_hogar` (`number`, requerido, `min: 1`).
- `tenencia_vivienda` (`radio`, requerido):
  - `propia_pagada`, `propia_pagandose`, `alquilada`, `alquilada_parte`, `cedida_trabajo`, `cedida_familiar`, `tomada_invadida`, `otra_forma`.

### Sección IV: Características de los Residentes (`residentes` -> `type: "datagrid"`)
Cada fila representa a un miembro del hogar:
- `persona_numero` (`number`, requerido, `min: 1`).
- `nombre_apellido` (`textfield`, requerido).
- `parentesco_jefe_hogar` (`select`, requerido).
- `sexo` (`select` o `radio`: `1` = Hombre, `2` = Mujer).
- `edad` (`number`, requerido, `min: 0`, `max: 120`).
- `sabe_leer_escribir` (`select`: `si`, `no`).
- `nivel_educativo` (`select`: `ninguno`, `primaria`, `secundaria`, `tecnico`, `universitario`, `postgrado`).
- `ocupacion_principal` (`textfield` o `select`).
- `medio_transporte_habitual` (`select`: usa catálogo de modos 1..8).
- `posee_licencia` (`select`: `si`, `no`).
- `tiene_vehiculo_disponible` (`select`: `si`, `no`).
- `tipo_vehiculo` (`select`, condicional o habilitado si `tiene_vehiculo_disponible == "si"`).
- `cantidad_vehiculo` (`number`, `min: 0`).

### Sección V: Registro General de Viajes (`viajes` -> `type: "datagrid"`)
Para miembros mayores de 5 años (desplazamientos del día laboral típico anterior):
- `viaje_numero` (`number`, `min: 1`).
- `persona_numero` (`number`, referencia al miembro en `residentes`).
- `origen_direccion` (`textfield`, requerido).
- `zona_od_origen` (`textfield` o `select`, requerido).
- `destino_direccion` (`textfield`, requerido).
- `zona_od_destino` (`textfield` o `select`, requerido).
- `hora_salida` (`textfield` con máscara `99:99` o `time`, requerido).
- `hora_llegada` (`textfield` con máscara `99:99` o `time`, requerido).
- `motivo_viaje` (`select`, requerido):
  - `1` (Trabajo), `2` (Estudio), `3` (Compras), `4` (Salud), `5` (Recreación), `6` (Trámites), `7` (Visita Familiar), `8` (Otro).
- `modo_principal` y `modo_secundario` (`select`):
  - `1` (A pie), `2` (Bicicleta), `3` (Motocicleta), `4` (Automóvil Particular), `5` (Taxi), `6` (Transporte público: bus, buseta), `7` (Transporte informal: por puesto, mototaxi), `8` (Otro).
- `tiempo_viaje_min` (`number`, requerido, `min: 1`, `max: 600`).
- `costo_viaje_bs` (`number`, requerido, `min: 0`).

### Sección VI: Características de Transporte Público (`panel_seccion_vi`)
- `uso_transporte_publico` (`radio`: `si`, `no`) -> Activa el resto de la sección:
- `rutas_tp_utilizadas_dia` (`number`, `min: 1`).
- `tiempo_espera_paradas_min` (`number`, `min: 0`).
- `distancia_residencia_parada_km` (`number`, `min: 0`, `decimalLimit: 2`).
- `dificultad_acceso_tp` (`radio`: `si`, `no`).
- `principal_dificultad_tp` (`radio`, condicional si `dificultad_acceso_tp == "si"`): `frecuencia_baja`, `sobrecupo`, `falta_rutas`, `inseguridad`, `otro`.
- `calificacion_servicio_tp` (`radio`): `muy_bueno`, `bueno`, `regular`, `malo`, `muy_malo`.
- `gasto_semanal_tp_bs` (`number`, `min: 0`).
- `acuerdo_rutas_directas` (`radio`, escala Likert 5 niveles).
- `comentario_transporte_maturin` (`textarea`).

### Sección VII: Movilidad No Motorizada y Percepción (`panel_seccion_vii`)
- `cambio_forma_desplazarse_5a` (`radio`: `si`, `no`).
- `motivo_cambio_desplazamiento` (`radio`, condicional si `cambio_forma_desplazarse_5a == "si"`): `cambio_trabajo`, `cambio_residencia`, `falta_transporte`, `costo`, `otro`.
- `caminatas_mas_10min` (`radio`: `si`, `no`).
- `usa_bicicleta_transporte` (`radio`: `si`, `no`).
- `dias_semana_camina_bicicleta` (`number`, `min: 0`, `max: 7`).
- `desplazamiento_centro_modo` (`radio`: `camina`, `transporte_publico`).
- `aceras_adecuadas` (`radio`: `si`, `no`).
- `seguridad_desplazamiento_centro` (`radio`: `muy_seguro`, `seguro`, `neutral`, `inseguro`, `muy_inseguro`).

### Sección VIII: Esparcimientos y Peatonalidad (`panel_seccion_viii`)
- Incluye preguntas de frecuencia (`frecuencia_visita_parques`), selección múltiple con `selectboxes` (`actividades_espacios`, `impedimentos_uso_espacios`, `mejoras_prioritarias_espacios`, `esparcimientos_faltantes`), escalas de percepción de seguridad diurna/nocturna y el salto condicional clave en intersecciones:
  - `existe_cruce_peatonal` (`radio`: `si`, `no`):
    - Si marca `"si"`, muestra `cruce_demarcado_visible` (P21) y `seguridad_cruzar_interseccion` (P22).
    - Si marca `"no"`, salta directamente a `hay_semaforo_peatonal` (P23).

