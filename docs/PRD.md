# PRD — Plataforma Web de Encuestas y Movilidad Urbana (PDUL Maturín)

| Atributo | Detalle |
| :--- | :--- |
| **Documento** | Product Requirements Document (PRD) |
| **Versión** | 1.0 (Producción) |
| **Producto** | Plataforma Web de Encuestas Origen-Destino y Supervisión GIS — PDUL Maturín |
| **Ámbito Geográfico** | Municipio Maturín, Estado Monagas, Venezuela (11 Parroquias) |
| **Stack Principal** | FastAPI · SQLAlchemy 2.0 Async · PostgreSQL 16 (JSONB) · Vue 3 · TypeScript · Leaflet · ECharts |

---

## 1. Resumen Ejecutivo y Definición del Problema

### 1.1 Contexto
El **Plan de Desarrollo Urbano Local (PDUL)** de Maturín requiere levantar información primaria confiable sobre los patrones de movilidad cotidiana, composición sociodemográfica de los hogares, tenencia vehicular y evaluación del sistema de transporte público mediante una **Encuesta Origen-Destino (O-D)** aplicada tanto en campo (por encuestadores) como de forma ciudadana en línea.

### 1.2 Puntos de Dolor del Proceso Tradicional
1. **Errores de transcripción y lentitud:** La digitalización manual desde planillas físicas introduce errores tipográficos, inconsistencias de edad/actividad y retrasos de semanas para consolidar matrices O-D.
2. **Pérdida de formularios en zonas con conectividad intermitente:** Los encuestadores en sectores periféricos pierden respuestas completas cuando falla la señal móvil durante el envío.
3. **Ausencia de auditoría territorial:** Sin georreferenciación ni registro del dispositivo de captura, es imposible verificar si una encuesta fue levantada realmente en el sector declarado o desde un escritorio remoto.
4. **Riesgo de exposición de PII (Información Personal Identificable):** Compartir hojas de cálculo sin sanitización expone cédulas de identidad y nombres completos de los ciudadanos.

### 1.3 Propuesta de Valor
Construir una **plataforma web desacoplada, resiliente a desconexiones (*offline-first*) y soberana**, capaz de:
- Guiar al encuestado o encuestador paso a paso con validaciones inteligentes y ergonomía móvil.
- Garantizar **cero duplicados** y **cero pérdida de datos** mediante autoguardado local, cola *offline* e idempotencia criptográfica (`client_submission_id`).
- Proveer supervisión cartográfica en tiempo real (**Mapa de Levantamiento**) con semáforo de calidad GPS y detección de anomalías por IP.
- Transformar los microdatos JSONB en analítica urbana instantánea (reparto modal, mapas coropléticos y matrices O-D) protegiendo estrictamente la identidad ciudadana.

---

## 2. Objetivos y Métricas de Éxito (KPIs)

| Objetivo de Producto | Indicador Clave (KPI) | Meta / Criterio de Aceptación |
| :--- | :--- | :--- |
| **Fidelidad metodológica del PDUL** | Cobertura de variables del cuestionario oficial | 100% de las 8 secciones, 11 parroquias oficiales y 103 rutas de transporte público mapeadas. |
| **Resiliencia en campo** | Tasa de pérdida o duplicación ante cortes de red | **0% de duplicados** (garantizado por `UNIQUE(client_submission_id)`) y 100% de recuperación de borradores locales. |
| **Trazabilidad geográfica** | Cobertura de puntos GPS auditables | Clasificación automática del 100% de envíos con coordenadas en 3 niveles de calidad (`alta`, `media`, `alerta`). |
| **Privacidad por diseño** | Exposición de PII en logs y analítica | **0 campos PII** (`cedula`, nombres) expuestos en logs JSON, endpoints públicos o exportaciones anonimizadas. |
| **Usabilidad móvil (Campo)** | Ergonomía táctil y accesibilidad | Objetivos táctiles $\ge 48\text{px}$, tipografía $\ge 16\text{px}$ y conformidad **WCAG 2.1 AA**. |
| **Confiabilidad técnica** | Cobertura de pruebas automatizadas | $\ge 365$ tests automatizados pasando (Backend Pytest + Frontend Vitest) y verificación estricta TypeScript. |

---

## 3. Usuarios y Personas

### 3.1 Encuestador de Campo (Usuario Primario)
- **Perfil:** Personal técnico desplegado en las 11 parroquias de Maturín usando teléfonos inteligentes o tablets bajo luz solar y conexión 3G/4G inestable.
- **Necesidades:** Interfaz rápida sin recargas, botones grandes para operar con una mano, evitar reescribir direcciones repetitivas en los viajes de regreso y no perder el trabajo si se queda sin señal.

### 3.2 Ciudadano / Encuestado Web
- **Perfil:** Habitante del municipio que accede desde su móvil o PC mediante enlace público.
- **Necesidades:** Preguntas comprensibles con ayudas contextuales (*tooltips* explicativos), sin mensajes de error agresivos antes de terminar de escribir, y navegación clara por progreso.

### 3.3 Supervisor / Coordinador de Levantamiento
- **Perfil:** Responsable del control de calidad del operativo de campo.
- **Necesidades:** Ver en un mapa dónde se está levantando cada encuesta, detectar alertas de baja precisión GPS o envíos remotos (por IP), inspeccionar respuestas puntuales y exportar datos limpios en CSV/JSON.

### 3.4 Planificador Urbano / Analista PDUL
- **Perfil:** Especialista en movilidad y urbanismo.
- **Necesidades:** Consultar indicadores agregados en tiempo real (participación por parroquia, reparto modal, tiempos y costos promedio de viaje, flujos O-D) sin procesar JSON crudos manualmente.

---

## 4. Flujos de Usuario Principales (User Journeys)

### 4.1 Flujo de Captura en Campo (Encuestador / Ciudadano)
1. El usuario abre el enlace de la encuesta activa (`GET /api/v1/encuestas/{slug}`).
2. Si existe un borrador previo sin finalizar en `localStorage`, el sistema muestra el banner de restauración para continuar donde lo dejó.
3. El asistente solicita de forma no intrusiva la ubicación GPS del dispositivo y detecta automáticamente el tipo de dispositivo (`movil`, `tablet`, `escritorio`).
4. El usuario completa los pasos (Identificación, Vivienda, Residentes, Viajes O-D, Transporte Público si aplica, Movilidad Activa y Esparcimiento). En viajes, puede usar **"Regreso a casa"** en 1 toque para invertir origen y destino automáticamente.
5. Al enviar:
   - **Con conexión:** El backend valida, normaliza y persiste la respuesta retornando un recibo con ID de confirmación.
   - **Sin conexión:** La respuesta se guarda en la cola local (`pdul_offline_queue`) con su `client_submission_id` y se sincroniza automáticamente al recuperar internet.

### 4.2 Flujo de Supervisión Geográfica (Supervisor)
1. El supervisor ingresa al Panel Administrativo y selecciona la pestaña independiente **Mapa de Levantamiento**.
2. Visualiza las tarjetas KPI de cobertura (`Total Respuestas`, `Con Punto GPS`, `Sin Captura GPS`, `Alertas Geográficas / IP`).
3. Filtra por **Parroquia**, **Dispositivo** o activa el switch **"Solo alertas de ubicación"** para auditar puntos con error $> 500\text{ m}$ o fuera de Maturín.
4. Hace clic en un marcador del mapa (o en la tabla accesible alternativa) y presiona **"Inspeccionar respuesta"** para abrir el detalle completo (con PII enmascarada por defecto y opción explícita para revelarla).

---

## 5. Requisitos Funcionales Detallados y Criterios de Aceptación

### RF-01: Cuestionario Asistido por Pasos (Wizard PDUL)
- **Historia de usuario:** *Como encuestador/ciudadano, quiero completar el cuestionario en pasos lógicos y dinámicos para reducir la fatiga cognitiva y evitar errores de llenado.*
- **Criterios de aceptación (Given / When / Then):**
  - **Dado** que el usuario navega al paso de *Composición del Hogar*, **cuando** registra un residente menor de 5 años, **entonces** el sistema oculta opciones ilógicas (licencia de conducir, vehículo propio) y ajusta automáticamente valores coherentes.
  - **Dado** que el usuario indica que *no* utiliza transporte público en sus viajes, **cuando** avanza desde el paso de viajes, **entonces** el wizard omite automáticamente el subformulario de Transporte Público (Sección VI) y limpia datos obsoletos de ese paso antes de enviar.
  - **Dado** que un campo obligatorio queda vacío o inválido, **cuando** el usuario sale del campo (`:user-invalid`), **entonces** se muestra un mensaje claro sin bloquear la escritura inicial.

### RF-02: Resiliencia Offline e Idempotencia de Envíos
- **Historia de usuario:** *Como encuestador en zona rural/periférica, quiero que mis encuestas se guarden localmente si falla internet y se envíen sin duplicarse al reconectar.*
- **Criterios de aceptación:**
  - **Dado** un corte de red al presionar "Enviar", **cuando** falla la petición HTTP, **entonces** el envío se encola en `pdul_offline_queue` con un `client_submission_id` (UUID v4) y se muestra el indicador `OfflineSyncBadge`.
  - **Dado** un reintento de envío con el mismo `client_submission_id`, **cuando** el backend lo recibe, **entonces** retorna HTTP `200`/`201` con `idempotent_replay: true` sin insertar una segunda fila.

### RF-03: Detección de Dispositivo y Telemetría GPS
- **Historia de usuario:** *Como supervisor, quiero saber con qué tipo de dispositivo y desde qué coordenadas se levantó cada encuesta.*
- **Criterios de aceptación:**
  - **Dado** cualquier envío desde el navegador, **cuando** se construye el payload, **entonces** se adjunta `dispositivo_tipo` (`movil`, `tablet`, `escritorio`, `desconocido`) y, si hubo permiso de geolocalización, `gps_latitud`, `gps_longitud` y `gps_precision`.
  - **Dado** el backend procesando un punto GPS, **cuando** evalúa calidad, **entonces** clasifica como:
    - `alta`: dentro de Monagas y precisión $\le 100\text{ m}$.
    - `media`: dentro de Monagas y precisión entre $101\text{ m}$ y $500\text{ m}$ (o precisión no reportada).
    - `alerta`: fuera del bounding box de Monagas (`lat` $8.3\text{–}10.6$, `lng` $-64.2\text{–}-62.0$) o precisión $> 500\text{ m}$ (posible ubicación estimada por red/IP).

### RF-04: Panel Administrativo y Mapa de Levantamiento
- **Historia de usuario:** *Como administrador, quiero gestionar encuestas, visualizar los puntos de recolección en un mapa limpio y exportar microdatos seguros.*
- **Criterios de aceptación:**
  - La pestaña **Mapa de Levantamiento** renderiza los marcadores sobre mapa base OpenStreetMap (sin grillas o cuadros superpuestos que dificulten la lectura vial), con círculo punteado de radio de precisión al hacer clic.
  - Incluye vista tabular alternativa accesible para lectores de pantalla y teclado.
  - La exportación en **CSV** y **JSON** permite activar/desactivar la anonimización de PII antes de la descarga.
  - El constructor visual (`@formio/js`) permite crear y editar esquemas y alternar el estado `activa`/`inactiva` con confirmación modal al desactivar.

### RF-05: Dashboard Analítico Municipal
- **Historia de usuario:** *Como planificador urbano, quiero consultar métricas agregadas de movilidad por parroquia, modo de transporte y pares Origen-Destino.*
- **Criterios de aceptación:**
  - Mapa coroplético interactivo por parroquia de Maturín usando `maturin_parroquias.geojson`.
  - Gráficos interactivos con Apache ECharts para reparto modal, motivos de viaje, distribución de dispositivos y flujos O-D, cada uno acompañado de un *fallback* tabular accesible.

---

## 6. Reglas de Negocio y Validación Defensiva (Frontend + Backend)

Para proteger la integridad de los datos incluso ante envíos directos al API o borradores antiguos, el backend (`FormioSubmissionIn` en Pydantic v2) aplica las siguientes reglas:

| Campo / Entidad | Regla de Validación | Comportamiento ante Incumplimiento |
| :--- | :--- | :--- |
| **Parroquia** | Obligatoria; debe pertenecer a uno de los 11 códigos oficiales `snake_case` de Maturín. | Error `422` (RFC 7807 `ProblemDetailOut`). |
| **Cédula** | Opcional para hogares sin cédula; si se provee, se limpia a dígitos y debe cumplir `^[0-9]{6,9}$`. Unicidad por encuesta (`UNIQUE(encuesta_id, cedula)`). | Error `422` si formato inválido; `409 CEDULA_DUPLICADA` si ya existe en esa encuesta. |
| **Zona O-D** | Normalizada y truncada a un máximo de 120 caracteres (`VARCHAR(120)`). | Sanitización automática sin error de desbordamiento SQL. |
| **Coordenadas GPS** | Si se envía una, la otra es obligatoria; finitas dentro de `lat [-90, 90]` y `lng [-180, 180]`. | Error `422` con detalle específico. |
| **Residentes** | Lista de objetos; si incluye `edad`, debe estar entre `0` y `120`. | Error `422` indicando el índice del residente inválido. |
| **Viajes** | Si incluye `tiempo_viaje_min`, debe ser numérico y $> 0$. | Error `422` indicando el viaje inválido. |
| **Dispositivo** | Enumerado normalizado a `{movil, tablet, escritorio, desconocido}`. | Mapeo seguro a `desconocido` si llega un valor no reconocido. |

---

## 7. Requisitos No Funcionales (RNF)

### 7.1 Arquitectura y Persistencia
- **Backend:** Clean Architecture (`api` $\rightarrow$ `services` $\rightarrow$ `domain` $\rightarrow$ `infrastructure/repositories`), 100% asíncrono con FastAPI y SQLAlchemy 2.0 (`asyncpg`).
- **Base de Datos:** Esquema híbrido en PostgreSQL 16 (`encuestas` + `respuestas_ciudadanas`) con columna `datos JSONB` indexada con **GIN (`jsonb_path_ops`)** e índices B-Tree compuestos `(encuesta_id, parroquia)` y `(encuesta_id, zona_od)`.
- **Contratos de Error:** Todos los errores HTTP se serializan bajo el estándar **RFC 7807 (`ProblemDetailOut`)**.

### 7.2 Seguridad y Privacidad
- **Cero PII en Logs:** El logger estructurado JSON filtra y redacta `cedula` y nombres personales antes de escribir en salida estándar.
- **Privacidad en Analítica:** Los endpoints públicos (`/resultados-parroquia`, `/reparto-modal`, `/matriz-od`, `/metricas`) solo retornan agregaciones estadísticas.
- **CORS:** Configurable mediante variable de entorno `CORS_ORIGINS`.

### 7.3 Accesibilidad y Rendimiento Frontend
- **WCAG 2.1 AA:** Etiquetas semánticas (`<main>`, `<figure>`, `<caption>`), atributos ARIA dinámicos, navegación completa por teclado, y tablas accesibles como alternativa a gráficos y mapas.
- **Optimización de Mapas y Gráficos:** Uso de `shallowRef` en Vue 3 para instancias de Leaflet y ECharts evitando sobrecarga de reactividad profunda, junto a `ResizeObserver` para redimensionamiento fluido.

---

## 8. Alcance Fuera de Versión 1.0 y Roadmap Futuro

### Fuera de Alcance (v1.0)
- Sistema de cuentas, login y control de acceso basado en roles (RBAC/JWT) para encuestadores individuales (el despliegue actual asume enlace público ciudadano y panel interno protegido por entorno/red).
- Aplicaciones nativas en tiendas App Store / Google Play (cubierto por Web App *Mobile-First* con soporte *offline*).

### Evolución Sugerida (v1.1 / v2.0)
- **Autenticación Admin (JWT / OAuth2):** Proteger `/api/v1/admin/*` con sesiones de usuario y registro de auditoría de quién exportó o reveló PII.
- **Polígonos Cartográficos Oficiales (IGVSB):** Incorporar los límites parroquiales reales en GeoJSON cuando estén disponibles desde el catastro municipal oficial.
- **PWA Instalable:** Service Worker completo para instalación en pantalla de inicio en teléfonos de encuestadores.

---

## 9. Riesgos y Mitigaciones

| Riesgo | Impacto | Mitigación Implementada |
| :--- | :--- | :--- |
| **Pérdida de datos por señal nula en campo** | Alto | Autoguardado continuo en `localStorage` + cola *offline* + idempotencia por `client_submission_id`. |
| **Encuestadores respondiendo desde casa o con GPS apagado** | Medio | Semáforo automático de calidad GPS y detección de alertas $> 500\text{ m}$ / fuera de Monagas en el Mapa de Levantamiento. |
| **Incompatibilidad de borradores guardados tras actualizaciones** | Medio | Tolerancia a versiones previas de claves en `useSurveyDraft` y normalización defensiva en `FormioSubmissionIn`. |
| **Sobrecarga de consultas analíticas sobre JSONB** | Medio | Índices GIN `jsonb_path_ops`, extracción relacional de columnas clave y consultas agregadas optimizadas con `jsonb_array_elements`. |
