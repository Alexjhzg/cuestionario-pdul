# Infraestructura de Pruebas E2E Opaque-Box — Alcaldía de Maturín (PDUL)

Este documento detalla la arquitectura, metodología, inventario de pruebas y comandos de ejecución de la suite de pruebas de caja negra (opaque-box) establecida en `tests_e2e/` para la plataforma de encuestas y movilidad urbana del PDUL.

---

## 1. Metodología: Arquitectura de Pruebas en 4 Niveles (Tiers)

La suite de pruebas E2E adopta el principio de **Pruebas Guiadas por Requisitos (Requirement-Driven) y Caja Negra Estricta (Opaque-Box)**, derivando las verificaciones directamente de `ORIGINAL_REQUEST.md`, `PROJECT.md` y las especificaciones normativas de la Alcaldía de Maturín. No interactúa con métodos privados de módulos internos.

```
       ▲
      / \     Tier 4: Escenarios de Aplicación Real (5 pruebas)
     /   \    Flujos completos de extremo a extremo de ciudadanos, encuestadores y directores
    /-----\
   /       \   Tier 3: Combinaciones Inter-módulo (8 pruebas)
  /         \  Interacciones por pares entre Frontend, Backend, GIS y Builder
 /-----------\
/             \ Tier 2: Casos Límite y de Borde (51 pruebas)
/               \ Robustez ante entradas adversas, desconexiones, carreras y RFC 7946
/-----------------\
/                   \ Tier 1: Cobertura por Característica (75 pruebas)
/                     \ ≥5 pruebas independientes por característica de F01 a F62
/-----------------------\
```

---

## 2. Inventario de Pruebas por Nivel

### Tier 1: Cobertura por Característica (`tests_e2e/tier1_feature/`) — 75 Pruebas

| Archivo de Prueba | Características Cubiertas | Casos de Prueba |
|-------------------|---------------------------|-----------------|
| `test_f01_f03_schema_metadata_parishes_zones.py` | **F01, F02, F03**: Esquema raíz, versión, 11 códigos snake_case de parroquias de Maturín, zonas O-D. | 8 pruebas |
| `test_f04_f08_housing_household_residents.py` | **F04, F05, F06, F07, F08**: Tipo de vivienda, cuartos, datos del hogar, grilla `residentes` (13 columnas), perfil y tenencia vehicular. | 9 pruebas |
| `test_f09_f12_trips_modes_costs.py` | **F09, F10, F11, F12**: Grilla `viajes` (13 columnas), origen-destino, catálogos oficiales 1..8 de motivos y modos, tiempo y costo. | 9 pruebas |
| `test_f13_f17_transit_mobility_recreation_submit.py` | **F13, F14, F15, F16, F17**: Subformulario Transporte Público, movilidad activa, 29 variables de esparcimiento, salto P20->P21/P22 vs P23, botón submit. | 7 pruebas |
| `test_f18_f19_geojson_and_validator.py` | **F18, F19**: Capa GeoJSON 11 polígonos Maturín, atributos y ejecución de `validate_formio_schema.py`. | 7 pruebas |
| `test_f20_f28_backend_persistence_contracts.py` | **F20–F28**: Clean Architecture, desempaquetado Form.io, normalización cédula (6-9 dígitos), idempotencia `client_submission_id`, restricción 409 y anonimización PII. | 8 pruebas |
| `test_f29_f38_api_endpoints_contracts.py` | **F29–F38**: Endpoints `/slug`, `/respuestas`, `/resultados-parroquia`, `/metricas`, `/matriz-od`, `/reparto-modal`, admin y RFC 7807. | 9 pruebas |
| `test_f39_f51_citizen_ux_contracts.py` | **F39–F51**: Asistente 8 pasos, validación tardía `:user-invalid`, autoguardado `pdul_draft_*`, cola offline `pdul_offline_queue`, tarjetas móviles y retorno 1 toque. | 7 pruebas |
| `test_f52_f56_admin_builder_contracts.py` | **F52–F56**: Exportación Form Builder con validación oficial, conmutación activa/inactiva, tabla de respuestas y exportación CSV/JSON. | 6 pruebas |
| `test_f57_f62_gis_dashboard_contracts.py` | **F57–F62**: Cálculo de 4 KPIs, unión Leaflet GeoJSON por `codigo_parroquia`, series ECharts, flujos O-D y tabla accesible WCAG AA. | 5 pruebas |

---

### Tier 2: Límites y Casos de Borde (`tests_e2e/tier2_boundary/`) — 51 Pruebas

| Archivo de Prueba | Foco de Validación | Casos de Prueba |
|-------------------|--------------------|-----------------|
| `test_boundary_corner_cases.py` | Límites exactos de cédula (6 y 9 válidos, 5 y 10 rechazados), grilla vacía en día sin viajes, tiempos/costos negativos o >24h, carreras de `client_submission_id`, borradores corruptos y saltos nulos. | 12 pruebas |
| `test_schema_empirical_fuzz.py` | Fuzzing exhaustivo y validación estricta de componentes, tipos y Soberanía de Datos en el esquema Form.io. | 28 pruebas |
| `test_challenger_m1_2_geojson_catalogs.py` | Integridad espacial GeoJSON (orientación de anillos RFC 7946, límites Monagas, no auto-intersección) y concordancia estricta de catálogos con contratos. | 11 pruebas |

---

### Tier 3: Combinaciones Inter-módulo (`tests_e2e/tier3_cross_feature/`) — 8 Pruebas

| Archivo de Prueba | Interacción Validada | Casos de Prueba |
|-------------------|----------------------|-----------------|
| `test_cross_feature_combinations.py` | 1. Vehículo en perfil (F08) ↔ Viaje en auto (F09).<br>2. Viaje en bus (F09) ↔ Subformulario Sección VI TP (F13).<br>3. Borrador (F44) + Restauración (F45) + Cola offline (F46) ↔ Idempotencia backend (F26).<br>4. Desactivación admin (F35/F54) ↔ Bloqueo de envíos ciudadanos (F30).<br>5. Envíos parroquiales (F30) ↔ Resultados analíticos (F31) y mapa GeoJSON (F58).<br>6. Pre-llenado inteligente (F48) + Retorno 1 toque (F49) ↔ Matriz O-D (F33).<br>7. Form Builder (F52) + Validador (F19) ↔ Asistente Wizard (F41).<br>8. Hogar multimodal (F06/F09) ↔ Tarjetas KPI (F57) y Reparto Modal ECharts (F59). | 8 pruebas |

---

### Tier 4: Escenarios de Aplicación Real (`tests_e2e/tier4_real_world/`) — 5 Pruebas

| Escenario | Descripción del Flujo Completo |
|-----------|--------------------------------|
| **Escenario 1** | **Estudiante universitario en San Simón Centro:** Movilidad activa, cero vehículos, 2 viajes peatonales a la UDO, salto condicional de cruce peatonal P20->P23, persistencia segura y anonimización de PII. |
| **Escenario 2** | **Familia multimodal de 4 personas en Boquerón:** Trabajador en transporte público (Sección VI activa), estudiante en viaje escolar, retorno a casa generado con 1 solo toque y cálculo de costos. |
| **Escenario 3** | **Encuestador municipal en zonas rurales:** Trabajo sin conectividad en El Corozo, El Furrial y Jusepín; 3 encuestas encoladas offline, sincronización por lotes en sede de la Alcaldía y reintento idempotente sin duplicación. |
| **Escenario 4** | **Administrador municipal y nueva consulta:** Creación de encuesta 'Consulta Maturín 2030' con Form Builder, validación de esquema, publicación (activa: True), recepción ciudadana, cierre y exportación CSV/JSON. |
| **Escenario 5** | **Director de Movilidad Urbana y Dashboard:** Carga ejecutiva de 4 KPIs, unión de mapa coroplético con 11 polígonos GeoJSON de Maturín, reparto modal ECharts, flujos O-D y generación de tabla accesible WCAG AA. |

---

## 3. Instrucciones de Ejecución

### Ejecución de Toda la Suite E2E

```bash
# Mediante el runner oficial
./tests_e2e/run_e2e_tests.sh

# Modo detallado (verbose)
./tests_e2e/run_e2e_tests.sh -v

# Mediante el módulo estándar unittest de Python
python3 -m unittest discover -s tests_e2e -p "test_*.py"

# Mediante pytest (si está disponible en el entorno virtual)
pytest tests_e2e/
```

### Ejecución por Tier Específico

```bash
python3 -m unittest discover -s tests_e2e/tier1_feature -p "test_*.py"
python3 -m unittest discover -s tests_e2e/tier2_boundary -p "test_*.py"
python3 -m unittest discover -s tests_e2e/tier3_cross_feature -p "test_*.py"
python3 -m unittest discover -s tests_e2e/tier4_real_world -p "test_*.py"
```

---

## 4. Total de Pruebas

- **Total Casos de Prueba:** 139 pruebas
- **Tier 1:** 75 pruebas
- **Tier 2:** 51 pruebas
- **Tier 3:** 8 pruebas
- **Tier 4:** 5 pruebas
