# Reglas Globales del Proyecto: Sistema de Consultas Públicas y Movilidad Urbana (PDUL - Alcaldía de Maturín)

## 1. Stack Tecnológico Oficial
- **Base de Datos:** PostgreSQL 15+ con soporte nativo `JSONB`, índices `GIN` (`jsonb_path_ops`) y funciones de desagregación `jsonb_array_elements`.
- **Backend API:** Python 3.11+ con **FastAPI**, **SQLAlchemy 2.0 (asíncrono con `asyncpg`)** y **Pydantic v2**.
- **Motor de Encuestas:** `@formio/js` renderizado localmente a partir de esquemas JSON almacenados en la base de datos.
- **Frontend y UI:** **Vue 3** (Composition API `<script setup>`) con **PrimeVue v3** (`https://v3.primevue.org/`), **CSS Moderno Nativo** (Variables CSS `:root` definidas en `DESIGN.md` + `<style scoped>` de Vue 3; **no utilizar Tailwind CSS ni PrimeFlex** para evitar colisiones de reset con Leaflet, Form.io y PrimeVue), **Leaflet** (teselas OpenStreetMap + capas `GeoJSON`) y **Apache ECharts**.

## 2. Licenciamiento y Soberanía de Datos (Obligatorio)
- **100% Open Source:** Utilizar exclusivamente paquetes con licencias abiertas permisivas (MIT, Apache 2.0, BSD, ISC) sin marcas de agua ni límites artificiales.
- **Soberanía y Privacidad Ciudadana:**
  - Ningún dato de encuestas o ciudadanos puede enviarse a nubes externas (prohibido usar la nube comercial `*.form.io`, Google Maps API o Mapbox).
  - Los endpoints públicos de analítica (`/resultados-parroquia`, `/metricas`, `/matriz-od`) **jamás** deben exponer datos de identificación personal (`cedula`, `nombre_apellido`, `casa_apartamento`).

## 3. Convenciones Transversales entre Capas
- **Claves de Preguntas (`key`) y Catálogos:** Estrictamente en `snake_case` minúscula y ASCII puro (sin tildes ni `ñ`).
- **Parroquias del Municipio Maturín:** Usar siempre los 11 códigos oficiales en `snake_case` (`alto_de_los_godos`, `boqueron`, `las_cocuizas`, `la_cruz`, `san_simon`, `santa_cruz`, `el_corozo`, `el_furrial`, `jusepin`, `la_pica`, `san_vicente`) para garantizar la unión exacta entre Form.io, PostgreSQL y los polígonos `GeoJSON` en Leaflet.
- **Orquestación por Skills:**
  - Creación/validación de esquemas Form.io -> activar skill `formio-survey-architect`.
  - Experiencia de usuario (UI/UX), accesibilidad WCAG AA, asistentes paso a paso y captura móvil/offline -> activar skill `citizen-survey-ux`.
  - Diseño de tablas, migraciones e índices GIN y SQL analítico -> activar skill `postgres-jsonb-dba`.
  - Endpoints REST asíncronos, arquitectura limpia y validación Pydantic v2 -> activar skill `fastapi-survey-backend`.
  - Componentes administrativos Vue 3 + PrimeVue v3 + Leaflet + ECharts -> activar skill `municipal-gis-dashboard`.

## 4. Mejores Prácticas de Ingeniería de Software (Obligatorias)
- **Arquitectura en Capas y Separación de Responsabilidades (Clean Architecture / SOLID):**
  - **Backend (`FastAPI`):** Separar estrictamente `routers/` (transporte HTTP), `schemas/` (contratos Pydantic v2), `services/` (reglas de negocio y normalización) y `repositories/` (consultas SQL/JSONB parametrizadas). Prohibido escribir lógica SQL directamente en los decoradores de ruta.
  - **Frontend (`Vue 3 + TypeScript`):** Separar `views/`, `components/` (presentacionales puros), `composables/` (`useSurveyDraft`, `useParroquiaMap`) y `services/` (cliente HTTP tipado).
- **Tipado Estricto y Desarrollo Guiado por Contratos (Contract-First):**
  - Python con anotaciones de tipos completas verificables con `mypy`/`ruff`; TypeScript con `"strict": true` sin uso de `any` en contratos de dominio.
- **Idempotencia y Resiliencia en Trabajo de Campo:**
  - Soportar siempre un identificador `client_submission_id` (UUID v4) generado en el cliente para que los reintentos automáticos en conexiones móviles inestables sean 100% idempotentes y nunca dupliquen registros.
- **Seguridad por Diseño (OWASP) y Observabilidad:**
  - Consultas SQL 100% parametrizadas (`bindparams`), validación de claves dinámicas mediante listas blancas/regex, errores estructurados (formato RFC 7807: `type`, `title`, `status`, `detail`, `errors`) y logs estructurados JSON sin datos personales (PII).
- **Pirámide de Pruebas Automatizadas (Pruebas Unitarias Obligatorias):**
  - **Validación de Esquemas:** Todo cambio en esquemas Form.io debe pasar `validate_formio_schema.py` y contar con pruebas unitarias del validador.
  - **Pruebas Unitarias Backend (`pytest` + `pytest-asyncio`):** Pruebas unitarias aisladas para validadores Pydantic v2 (normalización de cédula, catálogo de parroquias, grillas de viajes), lógica de negocio en `SurveyService` (idempotencia `client_submission_id`, manejo de duplicados `409`, anonimización de PII) y pruebas de endpoints con `httpx.AsyncClient`.
  - **Pruebas Unitarias Frontend (`Vitest` + `@vue/test-utils`):** Pruebas unitarias para los composables (`useSurveyDraft`, persistencia en `localStorage`, cola de sincronización offline), lógica de pre-llenado de viajes O-D (viaje de regreso en 1 toque) y renderizado de componentes.

