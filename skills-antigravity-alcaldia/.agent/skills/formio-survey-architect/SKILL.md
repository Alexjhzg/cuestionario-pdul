---
name: formio-survey-architect
description: >-
  Diseña, genera, modifica y valida esquemas JSON compatibles con Form.io (@formio/js)
  para encuestas municipales, consultas públicas y estudios técnicos como la Encuesta
  Origen-Destino (PDUL). Úsala cuando el usuario pida crear o editar formularios,
  digitalizar cuestionarios en PDF/papel a JSON de Form.io, configurar lógica
  condicional, grillas repetibles (datagrid/editgrid) o validar esquemas de encuestas.
  No la uses para consultas SQL en PostgreSQL (usa postgres-jsonb-dba), endpoints
  FastAPI (usa fastapi-survey-backend) ni componentes visuales de mapas o gráficos
  (usa municipal-gis-dashboard).
---

# Arquitecto de Encuestas con Form.io (`@formio/js`)

## Descripción General
Esta skill guía la construcción y validación de esquemas JSON 100% compatibles con el motor open-source `@formio/js` (sin dependencias de la nube comercial de Form.io), listos para persistirse en columnas `JSONB` de PostgreSQL y renderizarse en aplicaciones Vue 3 / React.

## Dependencias y Coordinación con Otras Skills
- **`citizen-survey-ux`**: Aplica la matriz ergonómica de selección de controles (radios visibles para ≤ 5 opciones, `editgrid` en modo tarjetas para móviles en lugar de tablas anchas, y pistas `description` claras).
- **`postgres-jsonb-dba`**: Coordina la estructura de las claves (`key`) para optimizar índices GIN y consultas con `jsonb_array_elements`.
- **`fastapi-survey-backend`**: Asegura que el payload `submission.data` generado por el esquema coincida con los validadores Pydantic v2 del backend.
- **`municipal-gis-dashboard`**: Garantiza que los campos geográficos (`parroquia`, `zona_residencia_od`, `zona_od_origen`, `zona_od_destino`) utilicen códigos estandarizados compatibles con las capas `GeoJSON` de Leaflet.

## Mejores Prácticas de Ingeniería de Software para Esquemas
1. **Versionado Semántico de Esquemas (`schema_version`):**
   - Incluye siempre un campo oculto (`type: "hidden"`, `key: "schema_version"`, `defaultValue: "1.0.0"`) o metadato raíz para permitir la evolución del cuestionario sin romper consultas sobre respuestas históricas en PostgreSQL.
2. **Modularidad y Reutilización (DRY):**
   - Mantén los catálogos repetidos (como los códigos de Modo de Transporte `1..8` o las 11 Parroquias de Maturín) consistentes e idénticos entre secciones.
3. **Validación en Integración Continua (Quality Gate):**
   - Ningún esquema JSON se considera terminado sin pasar la validación estática automatizada con `scripts/validate_formio_schema.py`.

## Flujo de Trabajo Paso a Paso

### 1. Clasificación del Instrumento y Estructura Raíz
1. Identifica el tipo de instrumento:
   - **Consulta Pública Ciudadana (Simple):** Usa `"display": "form"` e incluye obligatoriamente `cedula` y `parroquia` para control de participación única.
   - **Encuesta Técnica Multisección (ej. Encuesta Origen-Destino PDUL):** Usa `"display": "wizard"` (navegación por páginas) o agrupa cada sección en componentes `type: "panel"` con `collapsible: true`. Consulta el mapeo completo en [pdul-origen-destino-mapeo.md](./references/pdul-origen-destino-mapeo.md).
2. Revisa la plantilla de referencia en [pdul-secciones-base.json](./examples/pdul-secciones-base.json) antes de redactar esquemas complejos.

### 2. Aplicación de Reglas de Construcción de Componentes
1. **Estándar de Nombres (`key`):**
   - Usa estrictamente `snake_case` en minúsculas, sin tildes, eñes (`ñ` -> `n`) ni caracteres especiales (ej. `servicio_agua`, `tiempo_viaje_min`, `tenencia_vivienda`).
   - Prohibido duplicar `key` en el mismo nivel de alcance; las claves dentro de un `datagrid` tienen alcance local a cada fila del arreglo.
2. **Campos Base de Identificación y Georreferenciación:**
   - `cedula`: `type: "textfield"`, validación con expresión regular `"pattern": "^[0-9]{6,9}$"`. Obligatoria en consultas abiertas; opcional o de jefe de hogar en encuestas muestrales domiciliarias (PDUL).
   - `parroquia`: `type: "select"`, `"dataSrc": "values"` (o `"url"` apuntando exclusivamente a la API local `/api/v1/catalogos/parroquias`), requerido.
3. **Selección de Tipos de Componentes según la Pregunta:**
   - **Selección única (2 a 5 opciones o escalas Likert):** Usa `type: "radio"` con `inline: false` (o `true` para Sí/No).
   - **Selección única (> 5 opciones, ej. Parroquias o Zonas O-D):** Usa `type: "select"` con `searchEnabled: true`.
   - **Selección múltiple ("admite respuestas múltiples"):** Usa `type: "selectboxes"` (almacena `{"opcion_a": true, "opcion_b": false}`) o `type: "select"` con `"multiple": true` (almacena `["opcion_a"]`). Prefiere `select"` con `"multiple": true` cuando se requiera indexación directa de arreglos en PostgreSQL, o `selectboxes` cuando el formulario impreso liste casillas de verificación.
   - **Tablas repetibles (Miembros del Hogar / Registro de Viajes O-D):** Usa `type: "datagrid"` o `type: "editgrid"` con `minLength` y `initEmpty: false`.
   - **Cantidades, tiempos y costos:** Usa `type: "number"` con `validate.min`, `validate.max` y `delimiter: false` para años/códigos.
4. **Lógica Condicional y Saltos de Pregunta:**
   - Para preguntas de seguimiento o campos `"Otro (especifique)"`, usa el bloque estándar apuntando a una `key` previamente definida:
     ```json
     "conditional": {
       "show": true,
       "when": "key_pregunta_anterior",
       "eq": "valor_disparador"
     }
     ```
   - Si una sección entera depende de una condición (ej. Sección VI solo si algún viaje usó transporte público), aplica el bloque `conditional` o `customConditional` directamente sobre el componente `panel`.
5. **Cierre del Formulario:**
   - Cierra siempre el arreglo raíz `components` con un botón de envío:
     `{"type": "button", "key": "submit", "label": "Enviar Participación", "action": "submit", "theme": "primary", "block": true}`.

### 3. Validación Automatizada del Esquema
1. Guarda el esquema JSON generado en el proyecto.
2. Ejecuta el script validador incluido en esta skill para verificar cumplimiento de reglas antes de entregar:
   ```bash
   python3 .agent/skills/formio-survey-architect/scripts/validate_formio_schema.py <ruta_al_archivo.json>
   ```
3. Corrige cualquier error reportado (claves con formato inválido, referencias condicionales huérfanas, falta de botón `submit`, o URLs externas prohibidas).

## Validación y Verificación
- El comando `validate_formio_schema.py` debe finalizar con código de salida `0` (`OK`).
- Todos los campos `when` dentro de bloques `conditional` deben referenciar una `key` existente en el esquema.
- Ningún componente puede apuntar a dominios externos (`*.form.io`, APIs comerciales) para cumplir con la regla de Soberanía de Datos.

## Errores Comunes a Evitar
- **Aplanar tablas maestro-detalle:** No crees `residente_1_edad`, `residente_2_edad` para las Secciones IV y V del PDUL; usa siempre un componente `datagrid` (`residentes`, `viajes`) para permitir `N` miembros o `N` viajes por hogar y facilitar su desagregación con `jsonb_array_elements`.
- **Omitir el campo de especificación en opciones "Otro":** Siempre que un `radio`, `select` o `selectboxes` incluya la opción `"otro"`, agrega inmediatamente después un `textfield` con `key: "<pregunta>_otro"` y condicional activado por `"eq": "otro"`.
- **Usar tildes o mayúsculas en `values.value` o `key`:** Los textos visibles van en `label` (con ortografía completa y tildes), pero `key` y `value` deben ser siempre `snake_case` ASCII puro.

