---
name: fastapi-survey-backend
description: >-
  Construye y mantiene endpoints asíncronos en Python con FastAPI, SQLAlchemy 2.0
  (AsyncSession) y Pydantic v2 para servir esquemas de Form.io, validar y persistir
  respuestas ciudadanas o del PDUL, y exponer métricas agregadas (por parroquia,
  reparto modal y Matrices Origen-Destino). Úsala cuando trabajes en el backend
  Python, validadores Pydantic, modelos SQLAlchemy o rutas REST `/api/v1/encuestas`.
  No la uses para diseñar el JSON de Form.io (usa formio-survey-architect) ni para
  componentes Vue/React (usa municipal-gis-dashboard).
---

# Backend FastAPI para Sistema de Encuestas Municipal y PDUL

## Descripción General
Esta skill define la arquitectura y patrones de código del backend en **FastAPI + SQLAlchemy 2.0 (asíncrono) + Pydantic v2**, garantizando validación estricta de payloads de `@formio/js`, prevención de votos duplicados, anonimización de datos personales en analítica y respuestas listas para Leaflet y Apache ECharts.

## Dependencias y Coordinación con Otras Skills
- **`formio-survey-architect`**: Consume los esquemas JSON de Form.io y valida las claves enviadas en `submission.data`.
- **`citizen-survey-ux`**: Procesa envíos idempotentes (`client_submission_id`) de la cola offline y devuelve errores estructurados legibles por campo para mostrar junto a los controles del formulario.
- **`postgres-jsonb-dba`**: Ejecuta de forma asíncrona las consultas JSONB e índices definidos en la base de datos.
- **`municipal-gis-dashboard`**: Entrega contratos JSON tipados (`labels`/`values`, `GeoJSON` properties, flujos Origen-Destino) listos para renderizar sin transformaciones pesadas en el cliente.

## Mejores Prácticas de Ingeniería de Software (Clean Architecture & SOLID)
1. **Separación Estricta en Capas (`Router -> Service -> Repository`):**
   - **Router (`api/v1/endpoints/`):** Solo maneja códigos de estado HTTP, inyección de dependencias (`Depends`) y serialización de respuesta.
   - **Service (`services/`):** Aplica reglas de negocio, normalización de cédula, verificación de encuesta activa e idempotencia.
   - **Repository (`repositories/`):** Encapsula las sentencias SQL/JSONB parametrizadas sobre `AsyncSession`, facilitando pruebas unitarias mediante *mocks* o base de datos de prueba transaccional.
2. **Manejo Estandarizado de Errores (RFC 7807) y Observabilidad:**
   - Devuelve errores consistentes (`{"code": "DUPLICATE_PARTICIPATION", "detail": "...", "field": "cedula"}`) para que el frontend pueda enfocar el campo exacto con `aria-invalid="true"`.
   - Registra eventos con logs estructurados incluyendo `request_id` y `encuesta_id`, **omitiendo siempre `cedula` y nombres** en los archivos de log.
3. **Idempotencia Nativa (`client_submission_id`):**
   - Si el payload incluye `client_submission_id` y ya fue procesado previamente, devuelve el registro existente (`200 OK` o `201 Created`) sin lanzar error, permitiendo sincronización transparente de encuestas tomadas sin señal en campo.

## Flujo de Trabajo Paso a Paso

### 1. Modelado y Validación de Entrada con Pydantic v2
Revisa la implementación de referencia en [fastapi-schemas-and-routes.py](./references/fastapi-schemas-and-routes.py):
1. **Normalización del Payload (`@field_validator` / `@model_validator`):**
   - Acepta tanto el envoltorio estándar de Form.io (`{"data": {...}}`) como el diccionario de datos directo.
   - Extrae y promueve `cedula`, `parroquia` y `zona_residencia_od` desde `data` hacia las columnas indexadas de `respuestas_ciudadanas`.
   - Limpia prefijos (`V-`, `E-`), puntos y espacios de `cedula`, verificando que contenga entre 6 y 9 dígitos numéricos (`^[0-9]{6,9}$`).
   - Verifica que `parroquia` pertenezca al catálogo oficial de las 11 parroquias del Municipio Maturín.
2. **Validación de Grillas (`residentes`, `viajes`):**
   - Si el payload incluye `viajes` (Sección V del PDUL), valida que cada elemento tenga `zona_od_origen`, `zona_od_destino`, `motivo_viaje` y `modo_principal`, y que `tiempo_viaje_min > 0`.

### 2. Persistencia Asíncrona y Control de Duplicados
1. Usa `AsyncSession` (`sqlalchemy.ext.asyncio`) con bloques transaccionales explícitos.
2. Captura `sqlalchemy.exc.IntegrityError` al hacer `await session.commit()`:
   - Ejecuta `await session.rollback()`.
   - Si la violación corresponde a `uq_voto_ciudadano`, lanza `HTTPException(status_code=status.HTTP_409_CONFLICT, detail="La cédula indicada ya registró su participación en esta consulta pública.")`.

### 3. Endpoints Estándar de la API (`/api/v1/encuestas`)
1. `GET /api/v1/encuestas/{slug}`: Devuelve metadatos y `esquema_formio` (solo si `activa == True`).
2. `POST /api/v1/encuestas/{encuesta_id}/respuestas`: Valida, extrae campos indexados y guarda la respuesta (`201 Created`).
3. `GET /api/v1/encuestas/{encuesta_id}/resultados-parroquia`: Devuelve conteos y porcentajes por parroquia listos para colorear el mapa coroplético en Leaflet.
4. `GET /api/v1/encuestas/{encuesta_id}/metricas?campo={key}`: Devuelve `{ "campo": key, "labels": [...], "values": [...] }` soportando tanto campos escalares como `selectboxes` multirrespuesta para Apache ECharts.
5. `GET /api/v1/encuestas/{encuesta_id}/matriz-od`: Devuelve los pares `(zona_origen, zona_destino, total_viajes, tiempo_promedio_min, costo_promedio_bs)` desagregados desde `datos->'viajes'`.

## Validación y Verificación
- Prueba los endpoints con `pytest` + `httpx.AsyncClient` verificando:
  - `201 Created` en envío válido con limpieza automática de cédula (ej. `"V-12.345.678"` -> `"12345678"`).
  - `409 Conflict` al reenviar la misma dupla `(encuesta_id, cedula)`.
  - `422 Unprocessable Entity` cuando `parroquia` no es válida o falta en `data`.
- Confirma que ningún endpoint GET de analítica exponga los campos `cedula`, `nombre_apellido` ni `casa_apartamento`.

## Errores Comunes a Evitar
- **Usar el ORM síncrono (`Session`) dentro de rutas `async def`:** Bloquea el event loop de FastAPI; usa siempre `AsyncSession` con el driver `asyncpg`.
- **Confiar únicamente en la validación del frontend de Form.io:** Un cliente puede enviar JSON arbitrario al `POST`; revalida siempre `cedula`, `parroquia` y tipos numéricos en Pydantic v2.
- **Cargar todas las filas en memoria de Python para calcular métricas:** Realiza siempre las agregaciones (`COUNT`, `AVG`, `jsonb_array_elements`) directamente en PostgreSQL.

