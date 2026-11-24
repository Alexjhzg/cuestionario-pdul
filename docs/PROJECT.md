# Project: Plataforma Web de Encuestas y PDUL — Alcaldía de Maturín

## Architecture

El sistema adopta una arquitectura modular desacoplada de código abierto sin dependencias de servicios externos ni nubes de terceros:

1. **Frontend (`frontend/`):**
   - **Framework:** Vue 3 (Composition API `<script setup>`) con TypeScript y Vite.
   - **Componentes UI:** PrimeVue v3 con tema accesible (`lara-light-blue`).
   - **Estilos:** CSS nativo `:root` (Design Tokens `DESIGN.md`), `<style scoped>`, y aislamiento `.formio-local-wrapper`. Prohibido Tailwind CSS y PrimeFlex.
   - **Formularios & Builder:** `@formio/js` local para renderizado del cuestionario y constructor visual interactivo (`Formio.builder`).
   - **Cartografía GIS:** Leaflet con teselas OpenStreetMap y capas GeoJSON de las 11 parroquias de Maturín (`[9.7457, -63.1832]`, zoom 11), gestionado con `shallowRef`.
   - **Gráficos Estadísticos:** Apache ECharts (reparto modal y flujos O-D) con `shallowRef`, `ResizeObserver` y fallback accesible (`dataView` / tabla).
   - **Autoguardado y Resiliencia:** Composable `useSurveyDraft` con almacenamiento en `localStorage`, cola offline `pdul_offline_queue`, `client_submission_id` (UUID v4) y autosincronización en reconexión.
   - **UX de Viajes Móvil:** `ViajesMobileCards.vue` con prellenado inteligente y acción rápida de retorno a casa en 1 toque.
   - **Pruebas Unitarias Frontend:** Vitest + `@vue/test-utils` para composables, validaciones y componentes.

2. **Backend (`backend/`):**
   - **Framework:** FastAPI con Python 3.11+.
   - **ORM & Conectividad:** SQLAlchemy 2.0 en modo asíncrono (`AsyncSession`) con `asyncpg`.
   - **Validación & Serialización:** Pydantic v2 con normalización de cédula (`^[0-9]{6,9}$`), validación de catálogo de parroquias y RFC 7807 problem details.
   - **Patrón de Arquitectura:** Clean Architecture (`routers/`, `schemas/`, `services/`, `repositories/`).
   - **Soberanía y Privacidad:** Enmascaramiento estricto de PII (`cedula`, `nombre_apellido`, dirección exacta) en endpoints analíticos y logs estructurados.
   - **Idempotencia:** Detección de `client_submission_id` duplicado para retornar HTTP 200/201 con `idempotent_replay: true` sin duplicar filas.
   - **Pruebas Unitarias Backend:** Pytest con `pytest-asyncio` cubriendo validadores Pydantic v2, SurveyService, normalizadores, PII masking y endpoints.

3. **Base de Datos (`PostgreSQL 15+`):**
   - **Esquema Híbrido:** Tablas relacionales `encuestas` (esquema Form.io JSONB) y `respuestas_ciudadanas` (datos en JSONB).
   - **Índices de Alto Desempeño:** Índice GIN `(datos jsonb_path_ops)` e índices compuestos B-Tree en `(encuesta_id, parroquia)`, `(encuesta_id, zona_od)`.
   - **Restricciones de Integridad:** `UNIQUE (client_submission_id)`, `UNIQUE (encuesta_id, cedula)`, y parcial `UNIQUE (...) WHERE cedula IS NULL`.
   - **Analítica SQL JSONB:** Desenrollado seguro de viajes con `CROSS JOIN LATERAL jsonb_array_elements(...)` y agregación de selectboxes con `jsonb_each_text`.

---

## Feature Inventory

| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| F01 | Esquema base y metadatos | Campo `schema_version` y configuración JSON del Cuestionario PDUL | M1 | spec_miner |
| F02 | Catálogo de Parroquias | Validación de los 11 códigos oficiales `snake_case` de Maturín | M1 | spec_miner |
| F03 | Códigos Zonas O-D | Registro de zonificación origen y destino según plan PDUL | M1 | spec_miner |
| F04 | Vivienda y Cuartos | Tipología habitacional, especificación 'otro' y recuento de cuartos | M1 | spec_miner |
| F05 | Datos del Hogar | Grupos de gasto, número de hogar, densidad y régimen de tenencia | M1 | spec_miner |
| F06 | Grilla Residentes | Componente `datagrid` de 13 columnas por residente del hogar | M1 | spec_miner |
| F07 | Perfil de Residentes | Sexo, edad, parentesco, alfabetismo, ocupación, transporte habitual | M1 | spec_miner |
| F08 | Disponibilidad Vehicular | Tenencia de licencia, tipo y cantidad condicional de vehículos | M1 | spec_miner |
| F09 | Grilla de Viajes O-D | Componente `datagrid` de 13 columnas para viajes del día típico anterior | M1 | spec_miner |
| F10 | Trayecto y Cronología O-D | Origen, destino, zonificación O-D, horas de salida y llegada | M1 | spec_miner |
| F11 | Motivo y Modos de Viaje | Clasificación con catálogos oficiales 1..8 de motivos y modos (principal/secundario) | M1 | spec_miner |
| F12 | Costo y Tiempo de Viaje | Minutos de trayecto y costo monetario en Bs | M1 | spec_miner |
| F13 | Subformulario Transporte Público | Sección VI condicional al uso de TP (rutas, esperas, costo semanal, evaluación) | M1 | spec_miner |
| F14 | Movilidad Activa y No Motorizada | Sección VII (hábitos peatonales, bicicleta, motivos de cambio modal a 5 años) | M1 | spec_miner |
| F15 | Diagnóstico de Esparcimientos | Sección VIII (29 variables, actividades, impedimentos, mejoras prioritarias) | M1 | spec_miner |
| F16 | Salto Condicional Cruce Peatonal | Salto P20 Sí -> P21, P22; No -> P23 reflejando el documento físico | M1 | spec_miner |
| F17 | Botón Submit y Cierre | Componente `button` con acción `submit` validado por validador oficial | M1 | spec_miner |
| F18 | Capa GeoJSON Parroquias | Archivo `maturin_parroquias.geojson` con los 11 polígonos oficiales de Maturín | M1 | explorer_3 |
| F19 | Validación de Esquemas Form.io | Script `validate_formio_schema.py` ejecutado y superado para el esquema PDUL | M1 | spec_miner |
| F20 | Clean Architecture FastAPI | Estructura modular `routers/`, `schemas/`, `services/`, `repositories/` | M2 | explorer_2 |
| F21 | Conexión Async PostgreSQL | Motor SQLAlchemy 2.0 `AsyncEngine` con pool y driver `asyncpg` | M2 | explorer_2 |
| F22 | DDL y Tablas SQL | Tablas `encuestas`, `respuestas_ciudadanas` y tipos | M2 | explorer_2 |
| F23 | Índices GIN y B-Tree | Índices `(datos jsonb_path_ops)`, `(encuesta_id, parroquia)`, etc. | M2 | explorer_2 |
| F24 | Desempaquetado Form.io | Pydantic v2 `FormioSubmissionIn` admitiendo `{data: ...}` y plano | M2 | explorer_2 |
| F25 | Normalización Cédula | Regex y limpieza numérica `^[0-9]{6,9}$` sin puntos ni guiones | M2 | explorer_2 |
| F26 | Idempotencia en Recepción | Control de `client_submission_id` para evitar duplicados en reintentos | M2 | explorer_2 |
| F27 | Restricción Duplicados Voto/Hogar | `UNIQUE (encuesta_id, cedula)` y parcial para hogares sin cédula | M2 | explorer_2 |
| F28 | Anonimización Estricta PII | Exclusión total de cédula y nombres en analítica y logs estructurados | M2 | explorer_2 |
| F29 | Endpoint Esquema Activo | `GET /api/v1/encuestas/{slug}` | M2 | explorer_2 |
| F30 | Endpoint Recepción Envíos | `POST /api/v1/encuestas/{id}/respuestas` | M2 | explorer_2 |
| F31 | Endpoint Analítica Parroquias | `GET /api/v1/encuestas/{id}/resultados-parroquia` | M2 | explorer_2 |
| F32 | Endpoint Métricas ECharts | `GET /api/v1/encuestas/{id}/metricas` | M2 | explorer_2 |
| F33 | Endpoint Matriz O-D | `GET /api/v1/encuestas/{id}/matriz-od` | M2 | explorer_2 |
| F34 | Endpoint Reparto Modal | `GET /api/v1/encuestas/{id}/reparto-modal` | M2 | explorer_2 |
| F35 | Endpoints Admin Encuestas | `GET`, `POST`, `PATCH`, `PUT /api/v1/admin/encuestas` | M2 | explorer_2 |
| F36 | Endpoints Admin Exportación | `GET /api/v1/admin/encuestas/{id}/respuestas` y `/exportar` (CSV/JSON) | M2 | explorer_2 |
| F37 | Formato Errores RFC 7807 | Manejadores globales de excepción con `ProblemDetailOut` | M2 | explorer_2 |
| F38 | Suite Pytest Backend | Pruebas unitarias de schemas, service, normalizers, validator y PII | M2 | explorer_2 |
| F39 | Setup Vue 3 + PrimeVue v3 | Configuración Vite, PrimeVue `lara-light-blue`, variables CSS `:root` | M3 | explorer_3 |
| F40 | Tokens de Diseño Alcaldía | Implementación de paleta y medidas de `DESIGN.md` | M3 | explorer_3 |
| F41 | Asistente de 8 Pasos | `SurveyWizard.vue` con navegación semántica y tiempos estimados | M3 | explorer_3 |
| F42 | Ergonomía y Proximidad Gestalt | Objetivos táctiles ≥ 48px, tipografía ≥ 16px, hints accesibles | M3 | explorer_3 |
| F43 | Validación Tardía :user-invalid | Cero errores al inicio, validación al desenfocar y anuncio accesible | M3 | explorer_3 |
| F44 | Autoguardado localStorage | Composable `useSurveyDraft` persistiendo en `pdul_draft_${slug}` | M3 | explorer_3 |
| F45 | Banner de Restauración | `DraftRestoreBanner.vue` para reanudar encuestas en curso | M3 | explorer_3 |
| F46 | Cola Offline y Reconexión | `pdul_offline_queue` con `client_submission_id` y `OfflineSyncBadge.vue` | M3 | explorer_3 |
| F47 | Tarjetas Móviles Viajes | `ViajesMobileCards.vue` eliminando scroll horizontal | M3 | explorer_3 |
| F48 | Pre-llenado Inteligente Viajes | Encadenamiento de origen a partir del destino previo | M3 | explorer_3 |
| F49 | Retorno a Casa en 1 Toque | Botón rápido que invierte origen ↔ destino preservando modo y persona | M3 | explorer_3 |
| F50 | Tarjetas Móviles Residentes | `ResidentesCards.vue` con interfaz táctil y accesible | M3 | explorer_3 |
| F51 | Suite Vitest Frontend (UX) | Pruebas unitarias para `useSurveyDraft`, `useTripChain`, validaciones | M3 | explorer_3 |
| F52 | Form Builder con @formio/js | Componente `FormioBuilder.vue` con `Formio.builder` local soberano | M4 | explorer_3 |
| F53 | Validación y Previa en Builder | Exportación JSON validada con `validate_formio_schema.py` y previsualización | M4 | explorer_3 |
| F54 | Interfaz Administrativa | Vista `AdminSurveyListView.vue` con alternancia activa/inactiva | M4 | explorer_3 |
| F55 | Tabla de Envíos y Exportación | Visualización de envíos y descarga CSV/JSON en panel admin | M4 | explorer_3 |
| F56 | Suite Vitest Frontend (Admin) | Pruebas unitarias de vistas y componentes administrativos | M4 | explorer_3 |
| F57 | Tarjetas de Métricas KPIs | `KpiCardsGrid.vue` con 4 indicadores ejecutivos del levantamiento | M5 | explorer_3 |
| F58 | Mapa Leaflet Parroquias | `MaturinChoroplethMap.vue` con escala coroplética y `shallowRef` | M5 | explorer_3 |
| F59 | Gráfico ECharts Reparto Modal | `ModalSplitChart.vue` (donut/barras) con toolbox y resize | M5 | explorer_3 |
| F60 | Gráfico/Matriz Flujos O-D | `OdFlowMatrixChart.vue` para visualización de interacciones parroquiales | M5 | explorer_3 |
| F61 | Fallback Accesible de Datos | Tabla semántica HTML (`AccessibleDataFallback.vue`) para WCAG AA | M5 | explorer_3 |
| F62 | Suite Vitest Frontend (GIS/KPIs)| Pruebas unitarias para Leaflet map, ECharts component y ciclo de vida | M5 | explorer_3 |
| F63 | Suite Opaque-Box E2E (Tiers 1-4)| Batería de pruebas E2E automatizadas según metodología de 4 niveles | M6 | orchestrator |
| F64 | Endurecimiento Adversarial (Tier 5)| Pruebas de estrés de cobertura adversarial y casos extremos | M6 | orchestrator |

---

## Milestones

| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Esquemas Canónicos, Activos Geográficos y Validadores | F01–F19. Generación de `pdul_origen_destino.json`, `maturin_parroquias.geojson` y verificación con `validate_formio_schema.py` | none | DONE |
| M2 | Backend API Asíncrono, Persistencia PostgreSQL JSONB y Pruebas Pytest | F20–F38. FastAPI, SQLAlchemy 2.0 Async, PostgreSQL DDL, GIN indexes, Pydantic v2, SurveyService, idempotencia, PII masking, analítica y suite completa de pruebas unitarias pytest | M1 | DONE |
| M3 | Frontend Asistente Ciudadano, Autoguardado Offline y Pruebas Vitest | F39–F51. Vue 3 + PrimeVue v3, variables CSS nativas, wizard 8 pasos, autoguardado, cola offline, tarjetas móviles de viajes con regreso en 1 toque y suite Vitest de composables/componentes | M1 | DONE |
| M4 | Panel Administrativo y Constructor Visual de Encuestas | F52–F56. `@formio/js` local Form Builder, edición y exportación de esquemas, alternancia activa/inactiva, tabla de respuestas y exportación CSV/JSON | M2, M3 | DONE |
| M5 | Dashboard Analítico Municipal, Leaflet GIS y Apache ECharts | F57–F62. Tarjetas KPI, mapa coroplético de Maturín con Leaflet sobre 11 parroquias GeoJSON, Apache ECharts (reparto modal y flujos O-D), fallback accesible y pruebas Vitest | M2, M3 | DONE |
| M6 | Integración E2E, Pase 100% de Pruebas y Endurecimiento Adversarial | F63–F64. Pase del 100% de la suite E2E (Tiers 1-5) de la pista de pruebas y auditoría adversarial de cobertura (Tier 5) | M1, M2, M3, M4, M5, TEST_READY | DONE |

---

## Interface Contracts

### 1. Backend ↔ Base de Datos
- **Motor:** PostgreSQL 15+ accesible mediante URI `postgresql+asyncpg://...`
- **Tablas:**
  - `encuestas(id UUID, titulo VARCHAR, slug VARCHAR UNIQUE, tipo_instrumento VARCHAR, esquema_formio JSONB, activa BOOLEAN, creado_en TIMESTAMPTZ)`
  - `respuestas_ciudadanas(id BIGSERIAL, encuesta_id UUID, client_submission_id UUID UNIQUE, cedula VARCHAR, parroquia VARCHAR, zona_od VARCHAR, datos JSONB, fecha_registro TIMESTAMPTZ)`
- **Índices:** `idx_respuestas_datos_gin ON respuestas_ciudadanas USING GIN (datos jsonb_path_ops)`
- **Idempotencia:** Detección de duplicados sobre `client_submission_id`.

### 2. Frontend ↔ Backend REST API
- **Obtención de Cuestionario:** `GET /api/v1/encuestas/{slug}` -> Retorna `{ id, titulo, slug, esquema_formio, activa }`
- **Envío de Respuestas:** `POST /api/v1/encuestas/{id}/respuestas`
  - Payload: `{ client_submission_id: UUID, data: { cedula, parroquia, zona_residencia_od, residentes: [...], viajes: [...], ... } }`
  - Respuesta HTTP 201/200: `{ id, fecha_registro, idempotent_replay: bool, mensaje }`
  - Error HTTP 409 (Conflicto cédula): `{ code: "CEDULA_DUPLICADA", title: "Conflicto", status: 409, detail: "..." }`
  - Error HTTP 422 (Validación): RFC 7807 Problem Detail con lista de errores por campo.
- **Analítica Parroquial:** `GET /api/v1/encuestas/{id}/resultados-parroquia` -> Retorna `[{ parroquia, total_respuestas, porcentaje_total }]`
- **Analítica Reparto Modal:** `GET /api/v1/encuestas/{id}/reparto-modal` -> Retorna `[{ modo, etiqueta, total_viajes, porcentaje }]`
- **Analítica Matriz O-D:** `GET /api/v1/encuestas/{id}/matriz-od` -> Retorna `[{ zona_origen, zona_destino, total_viajes, tiempo_promedio_min, costo_promedio_bs }]`
- **Métricas Generales:** `GET /api/v1/encuestas/{id}/metricas?campo=...` -> Retorna `{ campo, series: [{ valor, etiqueta, conteo, porcentaje }] }`
- **Administración:**
  - `GET /api/v1/admin/encuestas` -> Lista de encuestas con métricas agregadas
  - `POST /api/v1/admin/encuestas` -> Creación de encuesta desde Form Builder
  - `PATCH /api/v1/admin/encuestas/{id}/estado` -> Alterna `activa: true/false`
  - `GET /api/v1/admin/encuestas/{id}/respuestas` -> Lista paginada para supervisores
  - `GET /api/v1/admin/encuestas/{id}/exportar?formato=csv|json` -> Descarga tabular

### 3. Frontend ↔ Esquemas Form.io & Cartografía
- **Parroquias:** Exactamente los 11 códigos oficiales `snake_case`:
  `alto_de_los_godos`, `boqueron`, `las_cocuizas`, `la_cruz`, `san_simon`, `santa_cruz`, `el_corozo`, `el_furrial`, `jusepin`, `la_pica`, `san_vicente`.
- **Enlace Cartográfico:** Propiedad `feature.properties.codigo_parroquia` en `maturin_parroquias.geojson` hace join exacto con `parroquia` en API.
- **Modos de Transporte:** Claves numéricas `"1"` (A pie), `"2"` (Bicicleta), `"3"` (Motocicleta), `"4"` (Automóvil particular), `"5"` (Taxi), `"6"` (Transporte público - bus/buseta), `"7"` (Transporte informal - por puesto/mototaxi), `"8"` (Otro).

---

## Code Layout

```
/home/seem/Documentos/_proyectos/cuestionario-pedul/
├── .agent/                             # Reglas y skills de referencia
├── .agents/teamwork/                   # Archivos de coordinación de agentes
│   ├── ORIGINAL_REQUEST.md
│   ├── PROJECT.md                      # Documento maestro único de verdad
│   └── orchestrator/
│       ├── BRIEFING.md
│       ├── progress.md
│       ├── DISPATCH.md
│       └── GATE_STATUS.md
├── shared/                             # Activos canónicos compartidos
│   ├── schemas/
│   │   └── pdul_origen_destino.json    # Esquema Form.io oficial validado
│   └── geojson/
│       └── maturin_parroquias.geojson  # Capa GeoJSON oficial de las 11 parroquias
├── backend/                            # Módulo Backend FastAPI
│   ├── app/
│   │   ├── main.py
│   │   ├── core/                       # config, database, logging
│   │   ├── models/                     # SQLAlchemy models (encuesta, respuesta)
│   │   ├── schemas/                    # Pydantic v2 schemas
│   │   ├── repositories/               # Async SQL/JSONB repositories
│   │   ├── services/                   # Business logic, normalizers, PII masking
│   │   └── api/v1/endpoints/           # Routers (encuestas, analitica, admin)
│   ├── alembic/                        # Migraciones de BD
│   ├── tests/                          # Suite Pytest
│   │   ├── conftest.py
│   │   ├── unit/                       # Pydantic, services, normalizers, PII, validator
│   │   └── integration/                # Endpoints con httpx.AsyncClient
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/                           # Módulo Frontend Vue 3
│   ├── src/
│   │   ├── assets/                     # CSS nativo :root (DESIGN.md), geojson, schemas
│   │   ├── components/                 # Componentes presentacionales puros
│   │   │   ├── survey/                 # SurveyWizard, ViajesCards, ResidentesCards
│   │   │   ├── builder/                # FormioBuilder
│   │   │   ├── dashboard/              # KpiCards, MaturinMap, ModalSplitChart, OdMatrixChart
│   │   │   └── common/                 # DraftRestoreBanner, OfflineSyncBadge
│   │   ├── composables/                # useSurveyDraft, useTripChain, useAnalytics
│   │   ├── services/                   # Typed API client
│   │   ├── views/                      # SurveyFillView, AdminListView, AdminBuilderView, DashboardView
│   │   ├── router/
│   │   ├── App.vue
│   │   └── main.ts
│   ├── tests/                          # Suite Vitest + @vue/test-utils
│   │   └── unit/                       # Composables, validations, components
│   ├── package.json
│   ├── vite.config.ts
│   └── vitest.config.ts
└── tests_e2e/                          # Pista de Pruebas E2E (Opaque-box)
    ├── harness/                        # E2E Test runner and assertions
    ├── tier1_feature/                  # ≥5 tests por feature
    ├── tier2_boundary/                 # Edge cases y validaciones de límite
    ├── tier3_cross_feature/            # Interacciones entre módulos
    ├── tier4_real_world/               # Flujos de vida real (PDUL encuestas)
    └── run_e2e_tests.sh                # Script de ejecución con código de salida
```
