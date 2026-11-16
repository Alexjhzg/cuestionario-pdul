---
name: postgres-jsonb-dba
description: >-
  Diseña esquemas relacionales e híbridos en PostgreSQL con columnas JSONB,
  índices GIN/B-Tree de expresión y consultas analíticas avanzadas (incluyendo
  Matrices Origen-Destino, partición modal y desagregación con jsonb_array_elements).
  Úsala para migraciones SQL, optimización de consultas JSONB, vistas materializadas
  y analítica de encuestas municipales o del PDUL. No la uses para generar esquemas
  JSON de Form.io (usa formio-survey-architect) ni código de rutas FastAPI
  (usa fastapi-survey-backend).
---

# Especialista PostgreSQL + JSONB para Encuestas y Movilidad Urbana

## Descripción General
Esta skill estandariza el diseño de base de datos en PostgreSQL para almacenar esquemas dinámicos de `@formio/js` y respuestas ciudadanas o muestrales (`JSONB`), garantizando integridad referencial, prevención de duplicados y consultas analíticas de sub-segundo para mapas GIS y tableros estadísticos.

## Dependencias y Coordinación con Otras Skills
- **`formio-survey-architect`**: Recibe las claves (`key` en `snake_case`) y estructuras anidadas (`datagrid` como `residentes` y `viajes`, o `selectboxes`) que se almacenan en `respuestas_ciudadanas.datos`.
- **`citizen-survey-ux`**: Soporta la sincronización offline e idempotencia mediante la columna `client_submission_id` (`UUID UNIQUE`).
- **`fastapi-survey-backend`**: Provee las consultas SQL parametrizadas y vistas analíticas consumidas por la capa de repositorio en SQLAlchemy 2.0 asíncrono.

## Mejores Prácticas de Ingeniería de Datos y Base de Datos
1. **Migraciones Versionadas y Reversibles (Alembic):**
   - Todo cambio de esquema (`CREATE TABLE`, `CREATE INDEX`, `ALTER TABLE`) debe expresarse en migraciones versionadas con funciones `upgrade()` y `downgrade()` explícitas e idempotentes (`IF NOT EXISTS` / `CONCURRENTLY` para índices en producción).
2. **Idempotencia para Trabajo de Campo Offline (`client_submission_id`):**
   - Incluye en `respuestas_ciudadanas` la columna `client_submission_id UUID UNIQUE` para que los reintentos de la cola offline del navegador (`ON CONFLICT (client_submission_id) DO NOTHING`) jamás dupliquen encuestas.
3. **Defensa en Profundidad con `CHECK` Constraints:**
   - Valida invariantes críticas a nivel de motor (ej. `CHECK (jsonb_typeof(datos) = 'object')` y validación del catálogo de parroquias).

## Flujo de Trabajo Paso a Paso

### 1. Diseño de Tablas y Restricciones (DDL)
1. **Tabla `encuestas`:**
   - `id` (`UUID` con `gen_random_uuid()` o `BIGSERIAL` PK).
   - `titulo` (`VARCHAR(255) NOT NULL`), `slug` (`VARCHAR(120) UNIQUE NOT NULL`).
   - `tipo_instrumento` (`VARCHAR(30) NOT NULL DEFAULT 'consulta_ciudadana'` — ej. `'consulta_ciudadana'` o `'encuesta_od_pdul'`).
   - `esquema_formio` (`JSONB NOT NULL`), `activa` (`BOOLEAN NOT NULL DEFAULT TRUE`), `creado_en` (`TIMESTAMPTZ NOT NULL DEFAULT NOW()`).
2. **Tabla `respuestas_ciudadanas`:**
   - `id` (`BIGSERIAL PRIMARY KEY`), `encuesta_id` (`REFERENCES encuestas(id) ON DELETE RESTRICT`).
   - Columnas promovidas (extraídas del payload para indexación directa):
     - `cedula` (`VARCHAR(15)`), `parroquia` (`VARCHAR(60) NOT NULL`), `zona_od` (`VARCHAR(30)`).
   - `datos` (`JSONB NOT NULL`): Payload íntegro enviado por Form.io.
   - `fecha_registro` (`TIMESTAMPTZ NOT NULL DEFAULT NOW()`).
3. **Prevención de Duplicados:**
   - Aplica siempre `CONSTRAINT uq_voto_ciudadano UNIQUE (encuesta_id, cedula)` para impedir doble participación por cédula en una misma encuesta.
   - En encuestas domiciliarias multihogar (PDUL), añade índice único parcial o compuesto sobre `(encuesta_id, zona_od, (datos->>'avenida_calle'), (datos->>'casa_apartamento'), (datos->>'hogar_numero'))` cuando `cedula IS NULL`.

### 2. Estrategia de Indexación de Alto Rendimiento
1. **Índice GIN General sobre `datos`:**
   - `CREATE INDEX idx_respuestas_datos_gin ON respuestas_ciudadanas USING GIN (datos jsonb_path_ops);` (óptimo para operadores de contención `@>`).
   - Si se requieren búsquedas de existencia de claves (`?`, `?|`), usa el operador GIN por defecto `USING GIN (datos)`.
2. **Índices B-Tree de Expresión para Agrupaciones Frecuentes:**
   - `CREATE INDEX idx_respuestas_encuesta_parroquia ON respuestas_ciudadanas (encuesta_id, parroquia);`
   - `CREATE INDEX idx_respuestas_zona_od ON respuestas_ciudadanas (encuesta_id, zona_od);`

### 3. Patrones de Consulta Analítica sobre JSONB
Consulta las plantillas completas en [sql-jsonb-patterns.sql](./references/sql-jsonb-patterns.sql):
1. **Campos escalares (`textfield`, `radio`, `select` simple):**
   - Extrae con `datos->>'clave'` y convierte tipos numéricos de forma segura (`(datos->>'tiempo_espera_paradas_min')::NUMERIC`).
2. **Preguntas de selección múltiple (`selectboxes` de Form.io):**
   - Form.io guarda `{"caminar": true, "deporte": false}`. Filtra opciones marcadas usando contención: `datos->'actividades_espacios' @> '{"caminar": true}'::jsonb` o expande con `jsonb_each_text(datos->'actividades_espacios') WHERE value = 'true'`.
3. **Grillas repetibles (`datagrid`: Residentes y Viajes O-D en Sección IV y V):**
   - Desagrega arreglos JSONB con `CROSS JOIN LATERAL jsonb_array_elements(r.datos->'viajes') AS v(viaje)`:
     - **Matriz Origen-Destino:** Agrupa por `v.viaje->>'zona_od_origen'` y `v.viaje->>'zona_od_destino'`.
     - **Reparto Modal y Tiempo/Costo Promedio:** Agrupa por `v.viaje->>'modo_principal'` calculando `AVG((v.viaje->>'tiempo_viaje_min')::NUMERIC)` y `AVG((v.viaje->>'costo_viaje_bs')::NUMERIC)`.

## Validación y Verificación
- Ejecuta `EXPLAIN (ANALYZE, BUFFERS)` sobre las consultas de dashboard para verificar que los filtros `@>` utilicen `Bitmap Index Scan on idx_respuestas_datos_gin` y las agrupaciones por parroquia usen `idx_respuestas_encuesta_parroquia`.
- Verifica que ninguna consulta de analítica pública proyecte la columna `cedula` ni `datos->>'nombre_apellido'` (cumplimiento de Soberanía y Privacidad de Datos).

## Errores Comunes a Evitar
- **Castear directamente texto vacío a numérico:** Usa siempre `NULLIF( trim(datos->>'campo'), '' )::NUMERIC` para evitar errores `invalid input syntax for type numeric` en campos condicionales no respondidos.
- **Usar `jsonb_array_elements` sin validar tipo array:** Protege siempre con `CASE WHEN jsonb_typeof(datos->'viajes') = 'array' THEN datos->'viajes' ELSE '[]'::jsonb END`.

