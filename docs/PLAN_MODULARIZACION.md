# PLAN INTEGRAL DE MODULARIZACIÓN
## Sistema de Consulta Ciudadana y Encuesta Origen-Destino PDUL
### Plan de Arquitectura Modular, Catálogo de Agentes Especializados y Hoja de Ruta de Ejecución Incremental

**Proyecto:** Cuestionario de Movilidad Urbana y Plan de Desarrollo Urbano Local (PDUL)  
**Entidad Promotora:** Alcaldía Bolivariana del Municipio Maturín, Estado Monagas, Venezuela  
**Documento:** Plan Maestro de Modularización Técnica (`PLAN_MODULARIZACION.md`)  
**Versión:** 1.0.0 (Línea Base Canónica)  
**Fecha:** Noviembre 2026  
**Estado:** Aprobado para Planificación y Ejecución  

---

## 1. Resumen Ejecutivo y Marco Estratégico

El presente documento constituye el **Plan Integral de Modularización** para el sistema de recolección, administración y analítica espacial de la Encuesta Origen-Destino del Plan de Desarrollo Urbano Local (PDUL) del Municipio Maturín. El sistema actual es plenamente funcional y cuenta con una cobertura empírica verificada del 100% en sus baterías de pruebas (145/145 pruebas E2E en 5 tiers, 57/57 pruebas unitarias backend con `pytest` y 200/200 pruebas frontend con `vitest`).

Sin embargo, el crecimiento orgánico del sistema durante sus etapas iniciales ha generado concentraciones de complejidad, acoplamientos entre capas y componentes monolíticos que amenazan la mantenibilidad, escalabilidad y auditabilidad a largo plazo.

### 1.1 Objetivos Estratégicos de la Modularización
1. **Desacoplamiento Estricto y Alta Cohesión:** Aplicar principios de Arquitectura Limpia (*Clean Architecture*) y Diseño Guiado por el Dominio (*DDD*), separando tajantemente las reglas de negocio del framework web (FastAPI) y del motor de base de datos (PostgreSQL/SQLite).
2. **Ergonomía, Accesibilidad y Modularidad Frontend:** Descomponer los monolitos de vista y componentes (>2,400 líneas en `SurveyWizard.vue`, >1,600 líneas en `AdminResponsesView.vue`) en primitivas atómicas reutilizables, subsecciones especializadas por paso y stores de estado global reactivo, preservando la conformidad WCAG 2.2 AA y ergonomía táctil (≥48px/52px).
3. **Soberanía de Datos y Eliminación de Duplicidades:** Unificar los esquemas canónicos de `@formio/js`, la cartografía GeoJSON de las 11 parroquias y los catálogos en una capa compartida (`shared/`) vinculada mediante alias de empaquetado (`@shared`), eliminando duplicaciones en activos y garantizando cero dependencia de servicios en la nube comercial (cero CDN, cero tracking, cero Google Maps o Form.io Cloud).
4. **Cero Regresiones Garantizado:** Implementar un sistema de cuatro capas de aseguramiento de calidad con fachadas transicionales que mantenga el 100% de éxito en las suites de pruebas existentes durante todas las fases de la migración.

---

## 2. Diagnóstico del Estado Actual y Cuellos de Botella (As-Is)

Una auditoría forense y de arquitectura sobre el repositorio reveló cuellos de botella técnicos específicos distribuidos en el Backend, Frontend y Capa Compartida:

```
ESTADO ACTUAL (AS-IS):
┌────────────────────────────────────────────────────────────────────────┐
│ FRONTEND MONOLÍTICO                                                    │
│ • SurveyWizard.vue (2,443 líneas) concentra 8 pasos y validaciones    │
│ • AdminResponsesView.vue (1,667 líneas) y DashboardView (989 líneas)   │
│ • Duplicidad en assets/schemas/ y assets/geojson/ vs shared/           │
│ • Estado disperso en refs locales, sin stores centralizados            │
└───────────────────────────────────▲────────────────────────────────────┘
                                    │ HTTP / REST
┌───────────────────────────────────▼────────────────────────────────────┐
│ BACKEND CON ACOPLAMIENTOS CRUZADOS                                     │
│ • Dependencia circular: database.py ↔ main.py (seeding en get_db)      │
│ • Repositorio depende de servicio: survey_repo -> question_analytics   │
│ • Servicios lanzan fastapi.HTTPException directamente                   │
│ • Bifurcaciones inline: if self._is_postgres() repetido en queries     │
│ • Fuga transaccional: services invocan session.commit() / rollback()   │
└────────────────────────────────────────────────────────────────────────┘
```

### 2.1 Diagnóstico de Backend
1. **Dependencia Circular en Inicialización y Seeding (`database.py` ↔ `main.py`):**
   En `backend/app/core/database.py` (líneas 72-75), la función generadora de sesiones importa diferidamente `seed_default_pdul_survey` desde `backend.app.main`, mientras que `main.py` (línea 15) importa la base de datos y la sesión desde `database.py`. Si ocurre una reconexión concurrente, se genera una condición de carrera sobre la inicialización de SQLite y la siembra del esquema.
2. **Inversión de Capas (Repositorio depende de Servicio):**
   En `backend/app/repositories/survey_repo.py` (líneas 407-408), el repositorio importa directamente la función `aggregate_all_survey_questions` desde `backend.app.services.question_analytics`. La capa de persistencia está asumiendo lógica de presentación y agregación de negocio que pertenece a la capa de aplicación.
3. **Acoplamiento Directo con el Framework Web (`HTTPException` en Servicios):**
   `SurveyService` (`services/survey_service.py`) y `AdminService` (`services/admin_service.py`) importan y lanzan directamente `fastapi.HTTPException` con códigos 400, 404, 409 y 503. Esto imposibilita la reutilización de estos servicios en tareas en segundo plano (Celery, ARQ), comandos CLI o pruebas unitarias aisladas sin mockear dependencias de FastAPI.
4. **Fuga del Manejo Transaccional a la Capa de Servicios:**
   `SurveyService` invoca explícitamente `await self.survey_repo.session.commit()` (línea 102) y `rollback()` (línea 122). Los servicios conocen los detalles de implementación de la sesión de SQLAlchemy en lugar de interactuar a través de un patrón *Unit of Work* abstracto.
5. **Bifurcación de Motores en Métodos de Consulta:**
   En `survey_repo.py` (líneas 122, 161, 202, 291), cada método de agregación analítica evalúa `if self._is_postgres(): ... else: ...`. El repositorio mezcla código SQL nativo para PostgreSQL (funciones `jsonb_array_elements`, `->>`, agregaciones de ventana `OVER()`) con extracciones en memoria para SQLite mediante bucles y diccionarios de Python, violando el Principio de Abierto/Cerrado (OCP).
6. **Duplicación de Factorías de Dependencias:**
   Las factorías `get_survey_service` y `get_admin_service` están implementadas de forma idéntica en múltiples routers (`endpoints/encuestas.py`, `endpoints/analitica.py`, `endpoints/admin.py`) ante la ausencia de un módulo unificado `api/deps.py`.
7. **Valores Fijos en Código (Hardcoded Identifiers):**
   Existen UUIDs por defecto (`"00000000-0000-0000-0000-000000000001"`) y nombres de slug fijos (`cuestionario-od-maturin` vs `pdul_origen_destino`) dispersos en servicios y repositorios sin centralizarse en la configuración del sistema.

### 2.2 Diagnóstico de Frontend
1. **Monolito Crítico del Cuestionario (`SurveyWizard.vue` — 2,443 líneas):**
   Concentra en un solo archivo de plantilla y script: la lógica de navegación de 8 pasos, las opciones de tipología de vivienda, grupos de gasto, dificultades de transporte, evaluación de seguridad, validaciones de campo en tiempo real (`:user-invalid`), gestión de foco accesible, anuncios `aria-live` y más de 1,000 líneas de reglas CSS scoped.
2. **Monolitos de Vistas Administrativas y Dashboard:**
   - `AdminResponsesView.vue` (1,667 líneas): combina selectores de encuesta, paginador manual, tabla de auditoría, alternancia de enmascaramiento PII, modal de detalle con renderizado de JSON crudo y estilos masivos.
   - `AdminSurveyListView.vue` (991 líneas): mezcla lista de tarjetas de encuestas, modal de confirmación accesible, alternancia activa/inactiva reactiva con rollback y descargas blob de CSV/JSON.
   - `DashboardView.vue` (989 líneas): centraliza filtros reactivos, búsqueda, grid de KPIs, mapa Leaflet y múltiples instancias de ECharts.
3. **Ausencia de Capa de Stores Reactivos Globales:**
   El estado se gestiona mediante referencias locales (`ref`) en las vistas o mediante instancias no compartidas de composables (`useAnalytics` recrea el estado en cada consumidor), provocando descoordinación y prop-drilling en `App.vue`.
4. **Duplicación de Primitivas de Interfaz:**
   Modales de diálogo accesibles (`role="dialog"`), switches accesibles (`role="switch"`), paginadores y tablas de datos son implementados desde cero de manera repetitiva en distintas vistas.
5. **Duplicación Estructural de Componentes (Shims):**
   Existen archivos redundantes como `components/builder/FormioBuilder.vue` (7 líneas) que solo reenvía a `components/admin/FormioBuilder.vue`, y `AdminBuilderView.vue` que reenvía a `FormBuilderView.vue`.
6. **Duplicación de Paletas Cromáticas:**
   Cada componente de ECharts declara arrays de colores estáticos repetidos en lugar de consumir los tokens CSS de diseño (`tokens.css`) o un composable centralizado.

### 2.3 Diagnóstico de Capa Compartida y Activos Canónicos
1. **Duplicación Física de Archivos:**
   - `shared/schemas/pdul_origen_destino.json` está duplicado exactamente en `frontend/src/assets/schemas/pdul_origen_destino.json`.
   - `shared/geojson/maturin_parroquias.geojson` está duplicado exactamente en `frontend/src/assets/geojson/maturin_parroquias.geojson`.
   - `vite.config.ts` y `tsconfig.json` carecen del alias `@shared`.
2. **Re-declaración de Constantes y Catálogos:**
   La lista oficial de las 11 parroquias de Maturín (`PARROQUIAS_MATURIN`) está re-declarada en 5 ubicaciones distintas: `validation.ts`, `analyticsApi.ts`, `AccessibleDataFallback.vue`, `normalizers.py` y los arneses de pruebas E2E.
   Las claves de datos personales (`PII_KEYS`) están re-declaradas en 3 ubicaciones independientes.

---

## 3. R1. Arquitectura Modular Objetivo del Sistema

La arquitectura objetivo sigue un modelo de cuatro capas para Backend y un diseño orientado a componentes y estado reactivo para Frontend, con una capa canónica compartida inmutable.

```
ARQUITECTURA MODULAR OBJETIVO (TO-BE):
┌────────────────────────────────────────────────────────────────────────┐
│ CAPA COMPARTIDA CANÓNICA (shared/)                                     │
│ • shared/schemas/ (pdul_origen_destino.json canónico Form.io)          │
│ • shared/geojson/ (maturin_parroquias.geojson CCW RFC 7946)            │
│ • shared/catalogs/ (parroquias.json, modos.json, motivos.json)         │
│ • shared/types/ (DTOs de dominio, Enums, PII_FIELDS, Contratos TS)     │
└───────────────────┬────────────────────────────────▲───────────────────┘
                    │                                │
    Importación     │ Alias                          │ Importación
    Directa         │ @shared                        │ Canónica
    Python          │ Vite/TS                        │ Python
                    ▼                                │
┌───────────────────────────────────────┐ ┌──────────┴───────────────────┐
│ FRONTEND MODULAR (Vue 3 / TS)         │ │ BACKEND MODULAR (FastAPI / 2.0)│
│ ┌───────────────────────────────────┐ │ │ ┌──────────────────────────┐ │
│ │ VIEWS (Rutas, Layout, Deep-Links) │ │ │ │ PRESENTACIÓN (Routers,   │ │
│ ├───────────────────────────────────┤ │ │ │  deps.py, error_handlers)│ │
│ │ STORES (survey, draft, analytics) │ │ │ ├──────────────────────────┤ │
│ ├───────────────────────────────────┤ │ │ │ SERVICIOS DE APLICACIÓN  │ │
│ │ COMPOSABLES (Stateless Hooks)     │ │ │ │  (Survey, Admin, Analyt) │ │
│ ├───────────────────────────────────┤ │ │ ├──────────────────────────┤ │
│ │ COMPONENTES DE DOMINIO Y PASOS    │ │ │ │ DOMINIO PURO (Entidades, │ │
│ ├───────────────────────────────────┤ │ │ │  Value Objects, UoW ABC) │ │
│ │ UI BASE ATÓMICA (Botones, Modales)│ │ │ ├──────────────────────────┤ │
│ └───────────────────────────────────┘ │ │ │ INFRAESTRUCTURA (UoW,    │ │
│                                       │ │ │  Repos PostgreSQL/SQLite)│ │
└───────────────────────────────────────┘ │ └──────────────────────────┘ │
                                          └──────────────────────────────┘
```

---

### 3.1 Estructura Modular Objetivo del Backend

El backend se organiza estrictamente en cuatro capas concéntricas según los principios de Clean Architecture:

```
backend/app/
├── domain/                               # CAPA 1: DOMINIO PURO (Sin dependencias externas)
│   ├── __init__.py
│   ├── entities/                         # Entidades de negocio ricas e inmutables
│   │   ├── __init__.py
│   │   ├── survey.py                     # Entidad Survey (atributos, estado activo, métodos de validación)
│   │   └── submission.py                 # Entidad CitizenSubmission
│   ├── value_objects/                    # Objetos de valor inmutables
│   │   ├── __init__.py
│   │   ├── cedula.py                     # Value Object Cedula (normalización, validación 6-9 dígitos)
│   │   ├── parroquia.py                  # Value Object Parroquia (11 códigos Maturín, normalización)
│   │   └── trip.py                       # Value Object Trip (origen, destino, modo, tiempos, costos)
│   ├── exceptions.py                     # Excepciones tipadas de dominio (libres de HTTP)
│   └── interfaces/                       # Contratos abstractos (Protocol / ABC)
│       ├── __init__.py
│       ├── survey_repository.py          # AbstractSurveyRepository
│       ├── submission_repository.py      # AbstractSubmissionRepository
│       └── unit_of_work.py               # AbstractUnitOfWork
│
├── infrastructure/                       # CAPA 2: INFRAESTRUCTURA Y PERSISTENCIA
│   ├── __init__.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── session.py                    # Engine, sessionmaker, fallback resiliente
│   │   ├── unit_of_work.py               # Implementación SqlAlchemyUnitOfWork
│   │   └── models/                       # Modelos ORM SQLAlchemy 2.0 DeclarativeBase
│   │       ├── __init__.py
│   │       ├── base.py                   # Base declarativa y tipos personalizados (GUID, UniversalJSON)
│   │       ├── encuesta.py               # Tabla 'encuestas'
│   │       └── respuesta.py              # Tabla 'respuestas_ciudadanas'
│   └── repositories/                     # Implementación concreta de repositorios
│       ├── __init__.py
│       ├── encuesta_repo.py              # EncuestaRepository (SQLAlchemy)
│       ├── postgres_survey_repo.py       # Consultas analíticas nativas JSONB (PostgreSQL 15+)
│       ├── sqlite_survey_repo.py         # Estrategia de agregación para SQLite / pruebas locales
│       └── survey_repo.py                # Fachada SurveyRepository que selecciona la estrategia
│
├── services/                             # CAPA 3: SERVICIOS Y CASOS DE USO DE APLICACIÓN
│   ├── __init__.py
│   ├── survey_service.py                 # Registro de respuestas, verificación de duplicados, orquestación
│   ├── admin_service.py                  # Gestión de ciclo de vida de encuestas y exportaciones CSV/JSON
│   ├── analytics_service.py              # Orquestación de métricas parroquiales, reparto modal, matriz OD
│   ├── question_analytics.py             # Agregación pregunta a pregunta del esquema Form.io
│   └── normalizers.py                    # Utilidades de saneamiento y anonimización de PII
│
├── api/                                  # CAPA 4: PRESENTACIÓN Y ENTRADA HTTP (FastAPI)
│   ├── __init__.py
│   ├── deps.py                           # Proveedores centralizados de inyección de dependencias
│   ├── error_handlers.py                 # Traductores de excepciones de dominio a RFC 7807 Problem Details
│   └── v1/
│       ├── __init__.py
│       ├── api.py                        # Agregador de rutas
│       └── endpoints/
│           ├── __init__.py
│           ├── admin.py                  # Rutas administrativas (/api/v1/admin/...)
│           ├── analitica.py              # Rutas de analítica pública y municipal
│           └── encuestas.py              # Rutas de consulta ciudadana y envíos
│
├── schemas/                              # DTOs y validación de entrada/salida (Pydantic v2)
│   ├── __init__.py
│   ├── analytics.py                      # DTOs para ECharts, Leaflet, KPIs, O-D Matrix
│   ├── encuesta.py                       # DTOs de encuesta (Create, Update, Out, ListItem)
│   ├── problem.py                        # Schema estándar RFC 7807 (ProblemDetailOut)
│   └── submission.py                     # DTOs de envío (FormioSubmissionIn, Receipt)
│
├── bootstrap/                            # CICLO DE VIDA Y ARRANQUE DESACOPLADO
│   ├── __init__.py
│   └── seeder.py                         # Precarga del esquema oficial PDUL libre de referencias circulares
│
└── main.py                               # Configuración de FastAPI, middleware, lifespans e inclusión de rutas
```

#### Especificación de Contratos Clave del Backend:

1. **Excepciones de Dominio Tipadas (`domain/exceptions.py`):**
   ```python
   class DomainError(Exception):
       def __init__(self, message: str, code: str = "DOMAIN_ERROR", field: str | None = None) -> None:
           super().__init__(message)
           self.message = message
           self.code = code
           self.field = field

   class SurveyNotFoundError(DomainError):
       def __init__(self, survey_id: str) -> None:
           super().__init__(f"No se encontró la encuesta '{survey_id}'.", "ENCUESTA_NO_ENCONTRADA")

   class SurveyInactiveError(DomainError):
       def __init__(self) -> None:
           super().__init__("La encuesta está inactiva y no acepta envíos.", "ENCUESTA_INACTIVA")

   class DuplicateCedulaError(DomainError):
       def __init__(self) -> None:
           super().__init__("La cédula indicada ya participó en esta consulta.", "CEDULA_DUPLICADA", "cedula")

   class RestrictedPiiFieldError(DomainError):
       def __init__(self, field_name: str) -> None:
           super().__init__(f"El campo '{field_name}' contiene PII y está protegido.", "CAMPO_PII_RESTRINGIDO", "campo")
   ```

2. **Contrato Abstracto de Unit of Work (`domain/interfaces/unit_of_work.py`):**
   ```python
   class AbstractUnitOfWork(ABC):
       surveys: AbstractSurveyRepository
       submissions: AbstractSubmissionRepository

       async def __aenter__(self) -> "AbstractUnitOfWork":
           return self

       async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
           if exc_type is not None:
               await self.rollback()
           else:
               await self.commit()

       @abstractmethod
       async def commit(self) -> None: ...

       @abstractmethod
       async def rollback(self) -> None: ...
   ```

3. **Inyección de Dependencias Centralizada (`api/deps.py`):**
   ```python
   async def get_uow() -> AsyncGenerator[AbstractUnitOfWork, None]:
       async with async_session_factory() as session:
           yield SqlAlchemyUnitOfWork(session)

   async def get_survey_service(uow: AbstractUnitOfWork = Depends(get_uow)) -> SurveyService:
       return SurveyService(uow)

   async def get_admin_service(uow: AbstractUnitOfWork = Depends(get_uow)) -> AdminService:
       return AdminService(uow)

   async def get_analytics_service(uow: AbstractUnitOfWork = Depends(get_uow)) -> AnalyticsService:
       return AnalyticsService(uow)
   ```

4. **Traductor Centralizado de Excepciones RFC 7807 (`api/error_handlers.py`):**
   Captura automáticamente las excepciones de dominio y las formatea como `ProblemDetailOut` con los códigos HTTP exactos esperados (404, 400, 409).

---

### 3.2 Estructura Modular Objetivo del Frontend

El frontend se reestructura en cinco capas especializadas: Componentes Base Atómicos, Componentes de Dominio y Compuestos, Vistas y Enrutamiento, Stores de Estado Global y Composables sin estado.

```
frontend/src/
├── main.ts
├── App.vue                                     # Shell de layout y navegación WAI-ARIA
├── assets/
│   ├── images/
│   │   └── logo-alcaldia-maturin.png
│   └── styles/
│       ├── tokens.css                          # Tokens de diseño (DESIGN.md)
│       └── main.css                            # Estilos globales y reset
├── components/
│   ├── ui/                                     # Capa 1: Primitivas Base UI Atómicas
│   │   ├── BaseButton.vue                      # min-block-size: 48px / 52px coarse
│   │   ├── BaseInput.vue                       # :user-invalid diferido tras blur
│   │   ├── BaseSelect.vue                      # Selector accesible nativo
│   │   ├── BaseSwitch.vue                      # role="switch", aria-checked
│   │   ├── BaseModal.vue                       # role="dialog", aria-modal, focus trap
│   │   ├── BaseCard.vue                        # Contenedor semántico accesible
│   │   ├── BaseBadge.vue                       # Pastillas de estado
│   │   └── BaseDataTable.vue                   # Tabla accesible con paginación
│   ├── common/                                 # Componentes de soporte transversales
│   │   ├── DraftRestoreBanner.vue
│   │   └── OfflineSyncBadge.vue
│   ├── survey/                                 # Capa 2: Módulo Cuestionario Ciudadano
│   │   ├── SurveyWizard.vue                    # Fachada orquestadora (<350 líneas)
│   │   ├── ResidentesCards.vue                 # Tarjetas de residentes (Paso 4)
│   │   ├── ViajesMobileCards.vue               # Tarjetas de viajes (Paso 5)
│   │   └── sections/                           # Secciones extraídas del wizard
│   │       ├── Step1Ubicacion.vue              # Parroquia, sector, zona O-D
│   │       ├── Step2Vivienda.vue               # Tipología habitacional
│   │       ├── Step3Hogar.vue                  # Gastos, dormitorios, tenencia
│   │       ├── Step6TransportePublico.vue      # Líneas, tiempos, costos, calificación
│   │       ├── Step7MovilidadActiva.vue        # Peatón, bicicleta, seguridad
│   │       └── Step8Esparcimiento.vue          # Parques, áreas verdes, veracidad
│   ├── admin/                                  # Módulo Administrativo
│   │   ├── AdminSurveyTable.vue
│   │   ├── AdminStatusToggle.vue
│   │   ├── AdminResponsesTable.vue
│   │   ├── AdminResponseDetailModal.vue
│   │   └── FormioBuilder.vue                   # Constructor soberano Form.io
│   └── dashboard/                              # Módulo Analítica y GIS
│       ├── BaseChart.vue                       # Wrapper base ECharts (shallowRef)
│       ├── KpiCardsGrid.vue
│       ├── MaturinChoroplethMap.vue            # Mapa Leaflet GeoJSON optimizado
│       ├── ModalSplitChart.vue
│       ├── OdFlowMatrixChart.vue
│       ├── ParroquiasBarChart.vue
│       ├── CalificacionTpDonutChart.vue
│       ├── DificultadesTpBarChart.vue
│       ├── SeguridadCentroDonutChart.vue
│       ├── QuestionChartCard.vue
│       └── AccessibleDataFallback.vue          # Tablas accesibles para lectores de pantalla
├── stores/                                     # Capa 3: Estado Reactivo Global
│   ├── surveyStore.ts                          # Encuesta activa, paso del wizard, validación
│   ├── draftStore.ts                           # Persistencia en localStorage y cola offline
│   ├── adminStore.ts                           # Encuestas administrativas y respuestas paginadas
│   └── analyticsStore.ts                       # Métricas en caché y control de race conditions
├── composables/                                # Capa 4: Hooks de Lógica Reutilizable
│   ├── useSurveyDraft.ts                       # Borrador y sincronización
│   ├── useTripChain.ts                         # Encadenamiento y retorno en 1 toque
│   ├── useAnalytics.ts                         # Cliente analítico
│   ├── useECharts.ts                           # Instancia, ResizeObserver y dispose
│   ├── useLeafletMap.ts                        # Map lifecycle y capas GeoJSON
│   └── usePiiMasking.ts                        # Reglas de enmascaramiento en cliente
├── services/                                   # Clientes de API Tipados
│   ├── api.ts
│   └── analyticsApi.ts
├── utils/
│   ├── validation.ts
│   └── schemaValidator.ts
└── views/                                      # Capa 5: Vistas a Nivel de Página
    ├── SurveyFillView.vue
    ├── DashboardView.vue
    ├── AdminSurveyListView.vue
    ├── AdminResponsesView.vue
    ├── FormBuilderView.vue
    └── AdminBuilderView.vue                    # Shim conservado por compatibilidad
```

---

### 3.3 Capa Compartida (`shared/`) y Contratos Canónicos

La carpeta `shared/` actúa como la única fuente de verdad (*Single Source of Truth*) para backend, frontend y arneses de pruebas.

```
shared/
├── schemas/
│   └── pdul_origen_destino.json            # Esquema canónico Form.io (>3,000 líneas)
├── geojson/
│   └── maturin_parroquias.geojson          # Polígonos de las 11 parroquias (CCW RFC 7946)
├── catalogs/
│   ├── parroquias.json                     # Metadatos oficiales de las 11 parroquias
│   ├── modos_transporte.json               # Catálogo canónico de 8 modos
│   └── motivos_viaje.json                  # Catálogo canónico de 8 motivos
└── types/                                  # Contratos y tipos TypeScript compartidos
    ├── index.ts
    ├── catalogs.ts                         # Tipos de parroquias, modos y motivos
    ├── contracts.ts                        # DTOs de API y ProblemDetailOut
    └── pii.ts                              # Lista canónica de campos PII (PII_FIELDS)
```

#### Configuración de Alias `@shared` en Frontend:
En `frontend/vite.config.ts`:
```typescript
resolve: {
  alias: {
    '@': fileURLToPath(new URL('./src', import.meta.url)),
    '@shared': fileURLToPath(new URL('../shared', import.meta.url))
  }
}
```
En `frontend/tsconfig.json`:
```json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"],
      "@shared/*": ["../shared/*"]
    }
  }
}
```
Esto permite importar los activos canónicos directamente (ej. `import canonicalSchema from '@shared/schemas/pdul_origen_destino.json';`), procediendo a la eliminación física segura de las copias duplicadas en `frontend/src/assets/schemas/` y `frontend/src/assets/geojson/`.

---

## 4. R2. Especificación de Agentes, Justificación y Responsabilidades

### 4.1 Justificación Técnica del Enfoque Multi-Agente
El sistema involucra tecnologías heterogéneas que demandan competencias altamente especializadas:
- Ingesta de alta concurrencia y consultas espaciales en JSONB (PostgreSQL 15+).
- Arquitectura asíncrona de alto rendimiento en Python con validación estricta (FastAPI / Pydantic v2).
- Esquemas declarativos complejos y soberanía tecnológica (`@formio/js` offline).
- Accesibilidad estricta (WCAG 2.2 AA), ergonomía táctil y diseño mobile-first (Vue 3 / PrimeVue).
- Cartografía espacial y visualización analítica con gestión de ciclos de vida DOM (Leaflet + Apache ECharts).

La asignación de todas estas tareas a un agente monolítico provoca sobrecarga de contexto, pérdida de atención a invariantes críticas y riesgo de regresiones sutiles (como fugas de PII o fugas de memoria en el DOM de Leaflet/ECharts). Se define un catálogo de **8 agentes especializados** con límites de alcance rigurosos.

---

### 4.2 Catálogo Detallado de los 8 Agentes Especializados

```
                     ┌────────────────────────┐
                     │    system_architect    │
                     │ (Macro-diseño y ADRs)  │
                     └───────────┬────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        ▼                        ▼                        ▼
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│ schema_architect │   │database_engineer │   │ backend_engineer │
│  (Form.io/DRY)   │   │ (Postgres/JSONB) │   │(Clean FastAPI/v2)│
└────────┬─────────┘   └────────┬─────────┘   └────────┬─────────┘
         │                      │                      │
         └──────────────────────┼──────────────────────┘
                                │
        ┌───────────────────────┴───────────────────────┐
        ▼                                               ▼
┌──────────────────┐                          ┌──────────────────┐
│   ux_engineer    │                          │gis_dashboard_eng │
│(Mobile/WCAG/Sync)│                          │(Leaflet/ECharts) │
└────────┬─────────┘                          └────────┬─────────┘
         │                                              │
         └──────────────────────┬───────────────────────┘
                                │
        ┌───────────────────────┴───────────────────────┐
        ▼                                               ▼
┌────────────────────────┐                  ┌────────────────────────┐
│ adversarial_challenger │                  │   compliance_auditor   │
│(Fuzzing/Races/Stress)  │                  │ (100% Tests/PII/Gates) │
└────────────────────────┘                  └────────────────────────┘
```

#### Agente 1: `system_architect`
- **Arquetipo:** `architect`
- **Rol:** Arquitecto Líder de Sistemas y Software
- **Justificación Técnica:** Indispensable para salvaguardar la coherencia estructural del sistema completo, garantizar el cumplimiento de los contratos de interfaz entre Frontend, Backend y Persistencia, y arbitrar decisiones técnicas críticas sin sesgos de componente.
- **Habilidades Mapeadas:** Arquitectura Limpia, DDD, especificación OpenAPI 3.1, arquetipo Teamwork `architect`.
- **Tareas Concretas y Entregables:**
  - Autoría y actualización de `PLAN_MODULARIZACION.md`.
  - Definición formal de contratos de capa y diseño de interfaces abstractas (`AbstractUnitOfWork`, `AbstractSurveyRepository`).
  - Resolución de conflictos de límites de módulos y aprobación de ADRs.
- **Límites de Alcance:**
  - *In Scope:* Macro-arquitectura, contratos compartidos, reglas de dependencia, gobierno de interfaces.
  - *Out of Scope:* Implementación de componentes Vue o consultas SQL concretas.
- **Protocolos de Interacción:**
  - *Entradas:* Requerimientos de `ORIGINAL_REQUEST.md` e informes de diagnóstico.
  - *Salidas:* Contratos formalizados, especificaciones en `shared/types/`.
  - *Handoff hacia:* Todos los agentes ejecutores (`schema_architect`, `database_engineer`, `backend_engineer`, `ux_engineer`, `gis_dashboard_engineer`).

---

#### Agente 2: `schema_architect`
- **Arquetipo:** `implementer` (Especialista)
- **Rol:** Arquitecto de Esquemas y Formularios Form.io
- **Justificación Técnica:** El esquema declarativo de `@formio/js` es el núcleo funcional del cuestionario de 8 pasos. Una definición defectuosa, una clave no estandarizada o una referencia a URLs de servidores externos rompe la validación en el backend y viola la soberanía tecnológica municipal.
- **Habilidades Mapeadas:** `.agent/skills/formio-survey-architect/`
- **Tareas Concretas y Entregables:**
  - Gobernanza del esquema canónico `shared/schemas/pdul_origen_destino.json`.
  - Enforzar nomenclatura estricta en `snake_case`, saltos condicionales y validaciones nativas.
  - Ejecutar el validador semántico `scripts/validate_formio_schema.py`.
  - Configurar las restricciones del constructor soberano Form.io (desactivando dependencias de Form.io Cloud).
- **Límites de Alcance:**
  - *In Scope:* Esquemas JSON Form.io, catálogos canónicos, validación estructural de formularios.
  - *Out of Scope:* Endpoints de FastAPI, modelos SQLAlchemy, estilos CSS.
- **Protocolos de Interacción:**
  - *Entradas:* Requerimientos de preguntas del PDUL y catálogos de transporte.
  - *Salidas:* Esquema JSON validado, informe de conformidad de esquema.
  - *Handoff hacia:* `backend_engineer` (esquemas de validación) y `ux_engineer` (renderizado de UI).

---

#### Agente 3: `database_engineer`
- **Arquetipo:** `implementer` (Especialista)
- **Rol:** Ingeniero de Plataforma de Datos y PostgreSQL JSONB
- **Justificación Técnica:** La eficiencia del cálculo analítico (matrices O-D, desagregación modal) reside en consultas avanzadas JSONB (`jsonb_array_elements`, `jsonb_path_ops`) sobre PostgreSQL 15+. La separación de dialectos (PostgreSQL vs SQLite) y la encapsulación transaccional exigen diseño de base de datos especializado.
- **Habilidades Mapeadas:** `.agent/skills/postgres-jsonb-dba/`
- **Tareas Concretas y Entregables:**
  - Implementación de la jerarquía polimórfica de repositorios (`PostgresSurveyRepository` y `SqliteSurveyRepository`).
  - Eliminación de las bifurcaciones inline `_is_postgres()` en `survey_repo.py`.
  - Implementación de `SqlAlchemyUnitOfWork` gestionando transacciones atómicas seguras.
  - Mantenimiento de migraciones Alembic y verificación de índices GIN y B-Tree.
- **Límites de Alcance:**
  - *In Scope:* Modelos ORM, DDL, repositorios, Unit of Work, optimización de queries SQL/JSONB.
  - *Out of Scope:* Rutas HTTP, vistas frontend, diseño de esquemas Form.io.
- **Protocolos de Interacción:**
  - *Entradas:* Contratos abstractos de `system_architect` y requerimientos de DTOs de `backend_engineer`.
  - *Salidas:* Repositorios probados, adaptadores de dialecto, suite de integración de datos.
  - *Handoff hacia:* `backend_engineer` (servicios de aplicación).

---

#### Agente 4: `backend_engineer`
- **Arquetipo:** `implementer` (Especialista)
- **Rol:** Ingeniero Núcleo Backend y API FastAPI
- **Justificación Técnica:** Garantiza la separación entre la lógica de negocio y el framework HTTP, la tipificación estricta con Pydantic v2, la respuesta estandarizada bajo RFC 7807 y la protección absoluta contra fugas de PII en logs estructurados y endpoints analíticos.
- **Habilidades Mapeadas:** `.agent/skills/fastapi-survey-backend/`
- **Tareas Concretas y Entregables:**
  - Creación de la capa de Dominio puro (`backend/app/domain/`) con Value Objects (`Cedula`, `Parroquia`, `Trip`) y entidades.
  - Refactorización de servicios (`SurveyService`, `AdminService`, `AnalyticsService`) haciéndolos independientes de `HTTPException` y acoplados únicamente a `AbstractUnitOfWork`.
  - Centralización de la inyección de dependencias en `api/deps.py`.
  - Implementación de manejadores de error RFC 7807 en `api/error_handlers.py`.
  - Extracción del semillero a `bootstrap/seeder.py` eliminando el ciclo circular con `database.py`.
- **Límites de Alcance:**
  - *In Scope:* FastAPI routers, servicios de aplicación, dominio, Pydantic DTOs, seguridad de PII.
  - *Out of Scope:* SQL directo (delegado a `database_engineer`), código de cliente Vue.
- **Protocolos de Interacción:**
  - *Entradas:* Repositorios de `database_engineer`, esquemas de `schema_architect`.
  - *Salidas:* Routers REST desacoplados, especificación OpenAPI actualizada, tests pytest en verde.
  - *Handoff hacia:* `ux_engineer`, `gis_dashboard_engineer`, `compliance_auditor`.

---

#### Agente 5: `ux_engineer`
- **Arquetipo:** `implementer` (Especialista)
- **Rol:** Ingeniero de Experiencia de Usuario y Ergonomía Móvil
- **Justificación Técnica:** El cuestionario es completado por ciudadanos en dispositivos móviles bajo condiciones de conectividad variable. Se requiere dominio de interfaces táctiles (≥48px/52px), accesibilidad WCAG 2.2 AA, validaciones amigables (`:user-invalid`) y sincronización resiliente de borradores offline.
- **Habilidades Mapeadas:** `.agent/skills/citizen-survey-ux/`
- **Tareas Concretas y Entregables:**
  - Descomposición del monolito `SurveyWizard.vue` (2,443 líneas) en 8 subsecciones especializadas (`components/survey/sections/`).
  - Creación de la capa de componentes base atómicos (`components/ui/`: `BaseButton`, `BaseInput`, `BaseModal`, `BaseSwitch`).
  - Modularización de `useSurveyDraft` y `useTripChain`, y creación de `draftStore` y `surveyStore`.
  - Preservación de selectores DOM, clases CSS de prueba y atributos WAI-ARIA requeridos por `challenger_m4_2.spec.ts` y `SurveyWizard.spec.ts`.
- **Límites de Alcance:**
  - *In Scope:* Asistente de encuesta, componentes atómicos de UI, almacenamiento offline, ergonomía táctil.
  - *Out of Scope:* Mapas Leaflet y ECharts (delegado a `gis_dashboard_engineer`), backend Python.
- **Protocolos de Interacción:**
  - *Entradas:* Tokens de `tokens.css`, esquema canónico de `schema_architect`.
  - *Salidas:* Componentes Vue 3 accesibles, tests Vitest 100% verdes.
  - *Handoff hacia:* `compliance_auditor` (auditoría de accesibilidad y tests).

---

#### Agente 6: `gis_dashboard_engineer`
- **Arquetipo:** `implementer` (Especialista)
- **Rol:** Especialista en Visualización de Datos y Dashboard GIS
- **Justificación Técnica:** Leaflet y Apache ECharts requieren manipulación directa del DOM y no toleran los proxies reactivos profundos de Vue 3 (`ref`). Es indispensable aplicar `shallowRef`, controlar el ciclo de vida con `ResizeObserver` y garantizar tablas de datos alternativas para accesibilidad (`AccessibleDataFallback.vue`).
- **Habilidades Mapeadas:** `.agent/skills/municipal-gis-dashboard/`
- **Tareas Concretas y Entregables:**
  - Creación de `BaseChart.vue` para encapsular el ciclo de vida de ECharts y el composable `useECharts`.
  - Modularización de `DashboardView.vue` y componentes analíticos (`ModalSplitChart.vue`, `OdFlowMatrixChart.vue`, `MaturinChoroplethMap.vue`).
  - Integración del mapa Leaflet consumiendo el GeoJSON canónico desde `@shared/geojson/maturin_parroquias.geojson`.
  - Implementación de `analyticsStore` con caché por `surveyId` y protección contra carreras.
- **Límites de Alcance:**
  - *In Scope:* Gráficos ECharts, mapas Leaflet, componentes de dashboard, tablas accesibles de datos.
  - *Out of Scope:* Asistente de llenado ciudadano, backend Python, base de datos.
- **Protocolos de Interacción:**
  - *Entradas:* Contratos analíticos de `backend_engineer`, GeoJSON canónico de `shared/`.
  - *Salidas:* Componentes de visualización desacoplados, tests unitarios de dashboard en verde.
  - *Handoff hacia:* `compliance_auditor`.

---

#### Agente 7: `adversarial_challenger`
- **Arquetipo:** `challenger`
- **Rol:** Especialista en Pruebas Adversarias y Robustez
- **Justificación Técnica:** Los desarrolladores tienden a verificar las rutas felices y los casos de borde previstos. El sistema municipal requiere un agente adversario que simule intencionalmente concurrencia extrema, corrupción de almacenamiento, envíos repetidos con carreras de red y ataques de inyección.
- **Habilidades Mapeadas:** Pruebas de estrés de concurrencia, fuzzing, inyección de fallos, arquetipo Teamwork `challenger`.
- **Tareas Concretas y Entregables:**
  - Ejecución de pruebas de idempotencia bajo concurrencia masiva (mismo `client_submission_id`).
  - Pruebas de fuzzing sobre los endpoints de ingesta con payloads truncados o malformados.
  - Simulación de corrupción de `localStorage` y desconexión intempestiva en campo.
  - Mantenimiento y ejecución del arnés Tier 5 E2E (`tests_e2e/tier5_adversarial/`).
- **Límites de Alcance:**
  - *In Scope:* Generación de pruebas adversarias, arneses de estrés, reporte de vulnerabilidades.
  - *Out of Scope:* Modificación directa del código fuente productivo.
- **Protocolos de Interacción:**
  - *Entradas:* Módulos implementados por backend, frontend y datos.
  - *Salidas:* Informes empíricos de vulnerabilidad, casos de prueba adversarios.
  - *Escala a:* `system_architect` y agentes ejecutores para mitigación inmediata.

---

#### Agente 8: `compliance_auditor`
- **Arquetipo:** `auditor`
- **Rol:** Auditor de Calidad, Soberanía y No Regresión
- **Justificación Técnica:** Actúa como autoridad imparcial e independiente que certifica formalmente los criterios de salida de cada fase. Verifica que no se alteren pruebas existentes para forzar aprobaciones y certifica la ausencia de llamadas a servicios comerciales en la nube (Google Fonts, CDNs, Form.io Cloud).
- **Habilidades Mapeadas:** Aseguramiento de calidad, auditoría de privacidad (PII), verificación WCAG AA, arquetipo Teamwork `auditor`.
- **Tareas Concretas y Entregables:**
  - Ejecución independiente de los runners de pruebas en cada fase:
    - Backend: `pytest` (57+ tests).
    - Frontend: `npm run test:unit` (200+ tests) y `npm run build`.
    - E2E: `./tests_e2e/run_e2e_tests.sh` (145 tests).
  - Auditoría forense de fuga de datos personales mediante `penetration_pii_harness.py`.
  - Verificación estricta de soberanía tecnológica (cero URLs externas en el código).
  - Emisión de Certificados de Aprobación de Fase (*Phase Gate Sign-off*).
- **Límites de Alcance:**
  - *In Scope:* Ejecución de suites de prueba, verificación de métricas, veto de entregas que rompan contratos.
  - *Out of Scope:* Escribir código productivo o alterar aserciones en las pruebas.
- **Protocolos de Interacción:**
  - *Entradas:* Entregables completados e informes de handoff de los agentes ejecutores.
  - *Salidas:* Dictámenes de pase/rechazo, registros de auditoría de calidad.
  - *Reporta a:* `system_architect` y al orquestador general.

---

### 4.3 Matriz de Responsabilidades RACI Exhaustiva

| Entregable del Plan de Modularización | `system_architect` | `schema_architect` | `database_engineer` | `backend_engineer` | `ux_engineer` | `gis_dashboard_eng` | `adversarial_challenger` | `compliance_auditor` |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Plan Maestro (`PLAN_MODULARIZACION.md`)** | **A / R** | C | C | C | C | C | C | I |
| **Capa Compartida y Tipos Canónicos (`shared/`)** | A | **R** | C | C | C | C | C | I |
| **Capa de Dominio Backend (`app/domain/`)** | A | I | C | **R** | I | I | C | I |
| **Persistencia, Repositorios y Unit of Work** | A | I | **R** | C | I | I | C | I |
| **Servicios Desacoplados y Routers FastAPI** | A | I | C | **R** | I | I | C | I |
| **Desacoplamiento Seeder (`bootstrap/seeder.py`)** | A | C | C | **R** | I | I | I | I |
| **Componentes Atómicos UI (`components/ui/`)** | A | I | I | I | **R** | C | C | I |
| **Descomposición de Pasos del Wizard (1 al 8)** | A | C | I | I | **R** | I | C | I |
| **Módulos de Dashboard y Wrapper ECharts** | A | I | I | C | I | **R** | C | I |
| **Deduplicación Form Builder y Vistas Admin** | A | C | I | I | **R** | I | C | I |
| **Capa de Stores Reactivos (`stores/`)** | A | I | I | C | **R** | **R** | C | I |
| **Arneses Adversarios y Estrés de Concurrencia** | A | I | I | I | I | I | **R** | C |
| **Auditoría Forense de PII y Soberanía Tecnológica**| A | I | I | I | I | I | C | **R** |
| **Certificación de No Regresión por Fase (Gates)** | A | I | I | I | I | I | I | **R** |

*Definiciones:*  
- **R (Responsible):** El rol que ejecuta y construye activamente el entregable.  
- **A (Accountable):** El rol con la autoridad final de aprobación técnica del entregable.  
- **C (Consulted):** El rol especializado que aporta información, requisitos o revisiones.  
- **I (Informed):** El rol que es notificado del resultado y avances del entregable.  

---

## 5. R3. Estrategia de Fases y Compatibilidad con Pruebas

Para garantizar que el sistema mantenga una operatividad ininterrumpida y no sufra roturas de compatibilidad con las baterías de pruebas existentes, la modularización se divide en **6 fases secuenciales e incrementales** gobernadas por puertas de control (*gates*) automáticas.

```
HOJA DE RUTA SECUENCIAL (ROADMAP):
┌────────────────────────────────────────────────────────────────────────┐
│ FASE 0: Línea Base, Congelamiento de Contratos y Corrección Tipos       │
│ • Auditoría 145 E2E / 57 Pytest / 200 Vitest. Tag: baseline-pre-mod    │
│ • OpenAPI 3.1 congelado. Corrección de warning en QuestionChartCard    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ FASE 1: Modularización de Persistencia y Acceso a Datos                │
│ • Repositorios abstractos. SqlAlchemyUnitOfWork. Dialectos separados  │
│ • Eliminación de _is_postgres() en survey_repo.py. Fachadas activas    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ FASE 2: Modularización de Núcleo Backend y Dominio Limpio              │
│ • Capa app/domain/ (Value Objects Cedula/Parroquia, Excepciones puras) │
│ • Servicios desacoplados de HTTPException. api/deps.py centralizado    │
│ • Seeder desacoplado de database.py y main.py                          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ FASE 3: Modularización Frontend, Descomposición y Deduplicación        │
│ • Alias @shared en Vite/TS. Deduplicación de schemas/geojson en assets │
│ • Primitivas UI base (BaseButton, BaseModal, etc. >=48px/52px WCAG AA) │
│ • Descomposición de SurveyWizard en 8 secciones. BaseChart para ECharts│
│ • Stores reactivas (survey, draft, admin, analytics). Deduplicar build │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ FASE 4: Integración del Sistema y Validación E2E Multi-Nivel           │
│ • Validación cruzada de todos los contratos entre Backend y Frontend   │
│ • Ejecución del runner E2E completo: 145/145 pruebas en Tiers 1-5      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ FASE 5: Hardening Adversarial, Accesibilidad y Sello de No Regresión   │
│ • Estrés de concurrencia (8+ peticiones paralelas idénticas)           │
│ • Fuzzing y pruebas de penetración PII (penetration_pii_harness.py)    │
│ • Auditoría de soberanía (0 CDNs externos). Certificado Final v2.0     │
└────────────────────────────────────────────────────────────────────────┘
```

---

### 5.1 Especificación Detallada de las Fases

#### Fase 0: Línea Base, Congelamiento de Contratos y Corrección Preliminar de Tipos
- **Objetivo:** Auditar y congelar la línea base del sistema, formalizar contratos de interfaces antes de cualquier modificación y corregir la advertencia de TypeScript que bloquea `vue-tsc`.
- **Tareas Clave:**
  1. Ejecución y registro documental de las 3 suites actuales (145 E2E, 57 Pytest, 200 Vitest).
  2. Creación del punto de control Git: `git tag -a baseline-pre-modularization -m "Línea base previa a modularización"`.
  3. Validación canónica de `shared/schemas/pdul_origen_destino.json` con `validate_formio_schema.py`.
  4. Corrección de la importación no utilizada `beforeEach` en `frontend/tests/unit/QuestionChartCard.spec.ts` para que `npm run build` (`vue-tsc --noEmit && vite build`) compile con código de salida 0.
  5. Generación y congelamiento del contrato OpenAPI 3.1 en `shared/contracts/openapi.yaml`.
- **Criterios de Entrada (Entry Gate):**
  - Árbol de trabajo Git limpio.
  - 145 E2E, 57 Pytest y 200 Vitest en estado verde.
- **Criterios de Salida (Exit Gate):**
  - Registro de auditoría almacenado.
  - `npm run build` ejecutando con código de salida 0.
  - Contratos congelados aprobados por `system_architect` y `schema_architect`.

---

#### Fase 1: Modularización de Persistencia y Acceso a Datos
- **Objetivo:** Desacoplar el acceso a la base de datos de la lógica de aplicación, aislar las consultas JSONB nativas y resolver limpiamente el soporte de dialectos PostgreSQL vs SQLite.
- **Tareas Clave:**
  1. Definir contratos en `backend/app/domain/interfaces/`: `AbstractSurveyRepository`, `AbstractSubmissionRepository` y `AbstractUnitOfWork`.
  2. Implementar `infrastructure/database/unit_of_work.py` (`SqlAlchemyUnitOfWork`) gestionando `commit()` y `rollback()` de forma atómica.
  3. Separar las consultas de `survey_repo.py` en adaptadores especializados:
     - `PostgresSurveyRepository`: consultas analíticas nativas JSONB (`jsonb_array_elements`, `jsonb_path_ops`).
     - `SqliteSurveyRepository`: lógica de simulación en memoria para desarrollo local y pruebas de integración.
  4. Mantener `survey_repo.py` como fachada transicional que instancie la estrategia correspondiente según el motor activo.
  5. Mantener re-exportaciones completas en `backend/app/repositories/__init__.py` para garantizar 100% de compatibilidad con las pruebas existentes.
- **Criterios de Entrada (Entry Gate):**
  - Fase 0 aprobada y certificada.
- **Criterios de Salida (Exit Gate):**
  - `pytest backend/tests` pasando 100% (57/57).
  - `./tests_e2e/run_e2e_tests.sh` pasando 100% (145/145).
  - Cero sentencias SQL o unnesting JSONB fuera de `infrastructure/repositories/`.

---

#### Fase 2: Modularización de Núcleo Backend y Dominio Limpio
- **Objetivo:** Establecer la capa de dominio puro, desacoplar los servicios de aplicación de dependencias web (`HTTPException`) y eliminar la dependencia circular del ciclo de vida.
- **Tareas Clave:**
  1. Crear `backend/app/domain/entities/` y `domain/value_objects/` (`Cedula`, `Parroquia`, `Trip`).
  2. Crear excepciones de dominio tipadas en `domain/exceptions.py`.
  3. Refactorizar `SurveyService`, `AdminService` y `AnalyticsService`:
     - Reemplazar lanzamientos de `HTTPException` por excepciones de dominio.
     - Reemplazar llamadas directas a `session.commit()` por la interacción con `AbstractUnitOfWork`.
     - Eliminar identificadores fijos (UUIDs hardcodeados) delegándolos a `core/config.py`.
  4. Crear `backend/app/api/deps.py` centralizando las dependencias de FastAPI (`get_uow`, `get_survey_service`, etc.).
  5. Implementar manejadores de excepción RFC 7807 en `backend/app/api/error_handlers.py` registrándolos en `main.py`.
  6. Extraer la función de siembra inicial a `backend/app/bootstrap/seeder.py`, eliminando la importación circular de `seed_default_pdul_survey` en `database.py`.
  7. Mantener funciones fachada en `endpoints/encuestas.py` para asegurar que los fixtures de pruebas existentes no se rompan.
- **Criterios de Entrada (Entry Gate):**
  - Fase 1 aprobada y certificada.
- **Criterios de Salida (Exit Gate):**
  - `pytest backend/` pasando 100% (57/57).
  - `penetration_pii_harness.py` ejecutando sin detectar fugas de PII.
  - Batería E2E (145/145) pasando 100%.

---

#### Fase 3: Modularización Frontend, Descomposición y Deduplicación
- **Objetivo:** Eliminar la duplicación de esquemas y activos mediante `@shared`, crear la capa de componentes base atómicos, descomponer el monolito del wizard en 8 secciones e integrar stores reactivas.
- **Tareas Clave:**
  1. Configurar alias `@shared` en `vite.config.ts` y `tsconfig.json`.
  2. Reemplazar importaciones en el frontend hacia `@shared/schemas/` y `@shared/geojson/`, procediendo a la eliminación física de los archivos duplicados en `frontend/src/assets/schemas/` y `frontend/src/assets/geojson/`.
  3. Implementar componentes base en `components/ui/` (`BaseButton`, `BaseInput`, `BaseSelect`, `BaseSwitch`, `BaseModal`, `BaseCard`, `BaseBadge`, `BaseDataTable`) con ergonomía táctil (≥48px/52px) y WCAG AA.
  4. Descomponer `SurveyWizard.vue` extrayendo las secciones 1 a 8 en `components/survey/sections/`, preservando `SurveyWizard.vue` como fachada orquestadora liviana (<350 líneas) conservando los selectores DOM e IDs requeridos por las pruebas.
  5. Crear `BaseChart.vue` y el composable `useECharts` para aislar el ciclo de vida de ECharts con `shallowRef` y `ResizeObserver`.
  6. Deduplicar constructores: eliminar el stub `components/builder/FormioBuilder.vue` y consolidar en `components/admin/FormioBuilder.vue`; consolidar vistas de constructor.
  7. Introducir stores de estado global reactivo (`surveyStore`, `draftStore`, `adminStore`, `analyticsStore`).
- **Criterios de Entrada (Entry Gate):**
  - Fase 2 aprobada y certificada.
- **Criterios de Salida (Exit Gate):**
  - `npm run test:unit` pasando 100% (200/200).
  - `npm run build` (`vue-tsc --noEmit && vite build`) pasando sin errores.
  - `challenger_m4_2.spec.ts` y `challenger_m3_2.spec.ts` pasando 100% (auditoría estática de selectores y CSS).

---

#### Fase 4: Integración del Sistema y Validación E2E Multi-Nivel
- **Objetivo:** Verificar la interoperabilidad de extremo a extremo entre los nuevos módulos del Backend, Frontend y Capa Compartida en todos los niveles operativos.
- **Tareas Clave:**
  1. Ejecución de la suite completa de pruebas de extremo a extremo `./tests_e2e/run_e2e_tests.sh`.
  2. Validación detallada de los 5 Tiers:
     - Tier 1: 75 pruebas de cobertura de características.
     - Tier 2: 51 pruebas de casos límite y de borde.
     - Tier 3: 8 pruebas de interacción inter-módulo.
     - Tier 4: 5 escenarios reales (estudiante universitario, familia multimodal, encuestador offline, director municipal, administrador).
     - Tier 5: 6 pruebas de endurecimiento adversarial.
  3. Verificación de retrocompatibilidad en la deserialización de borradores existentes de `localStorage` (`pdul_draft_*`).
- **Criterios de Entrada (Entry Gate):**
  - Fases 2 y 3 concluidas con pruebas unitarias verdes.
- **Criterios de Salida (Exit Gate):**
  - 145/145 pruebas E2E pasando con código de salida 0 en < 0.15s.
  - Cero errores en consola de navegador o en los logs estructurados del backend.

---

#### Fase 5: Hardening Adversarial, Accesibilidad y Sello de No Regresión
- **Objetivo:** Someter el sistema modularizado a condiciones extremas de estrés, ataque y auditoría de privacidad, certificando la versión final 2.0.
- **Tareas Clave:**
  1. Ejecución del arnés de estrés de idempotencia y concurrencia (`stress_idempotency_harness.py`), validando que múltiples envíos simultáneos del mismo `client_submission_id` resulten exactamente en una sola inserción y respuestas `idempotent_replay: true`.
  2. Ejecución del arnés de penetración PII (`penetration_pii_harness.py`), certificando 0 cadenas de identificación personal en endpoints públicos y exportaciones CSV anonimizadas.
  3. Auditoría exhaustiva de soberanía tecnológica: confirmar que el código no contenga llamadas a CDNs externos, fuentes remotas o APIs en la nube.
  4. Auditoría de accesibilidad: navegación completa por teclado (`Tab`, `Space`, `Enter`, flechas de dirección), relaciones de contraste cromático ≥ 17.8:1 y atributos WAI-ARIA semánticos.
  5. Emisión del Dictamen Final de Certificación y creación del tag de versión: `git tag -a v2.0-modularization-certified -m "Sistema PDUL modularizado y certificado"`.
- **Criterios de Entrada (Entry Gate):**
  - Fase 4 aprobada con 145/145 pruebas E2E.
- **Criterios de Salida (Exit Gate):**
  - 100% de éxito en las 3 suites combinadas (145 E2E + 57 Pytest + 200 Vitest).
  - Cero fugas de PII y cero vulnerabilidades de concurrencia.
  - Firma del certificado de salida por `compliance_auditor` y `system_architect`.

---

### 5.2 Sistema de 4 Capas de Calidad Automatizadas

Para blindar el sistema contra cualquier regresión durante el proceso de modularización, se establece el siguiente pipeline de calidad:

```
[ Commit / Modificación de Código ]
                 │
                 ▼
┌────────────────────────────────────────────────────────────────────────┐
│ CAPA 1: Pruebas Unitarias Rápidas (< 3 segundos)                       │
│ • Backend: pytest backend/ (57+ pruebas unitarias de servicio/dominio) │
│ • Frontend: npm run test:unit (200 pruebas unitarias con Vitest)       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ PASS
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ CAPA 2: Compilación y Tipado Estricto (< 10 segundos)                  │
│ • Frontend: npm run build (vue-tsc --noEmit && vite build)             │
│ • Form.io: validate_formio_schema.py (validación de esquema JSON)      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ PASS
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ CAPA 3: Batería E2E Opaque-Box de 5 Niveles (< 1 segundo)              │
│ • ./tests_e2e/run_e2e_tests.sh (145 pruebas completas)                 │
│ • Cobertura: F01-F62, Límites, Cruces, Casos Reales, Adversariales     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ PASS
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ CAPA 4: Seguridad, Privacidad de PII y Soberanía Tecnológica           │
│ • penetration_pii_harness.py: 0 fugas de cédula/nombres en analítica   │
│ • Auditoría de Soberanía: 0 referencias a dominios cloud externos      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ PASS
                                    ▼
                  [ APROBACIÓN DE GATE DE CALIDAD ]
```

### 5.3 Estrategia de Fachadas Transicionales (*Transitional Facades*)
Para evitar la rotura de pruebas existentes durante la reorganización física de archivos:
1. **En Backend:** En `backend/app/repositories/__init__.py` y `backend/app/services/__init__.py`, se conservan re-exportaciones de las clases originales hacia los nuevos módulos de infraestructura y dominio. Las rutas de importación utilizadas en `backend/tests/` continuarán funcionando de forma transparente.
2. **En Routers:** Los endpoints conservan funciones alias de factoría (`get_survey_service`) que delegan internamente a `api/deps.py`.
3. **En Frontend:** `SurveyWizard.vue` conserva exactamente su interfaz de props y eventos (`submit`, `draft-saved`, `reset`), así como los selectores DOM e IDs (`#parroquia`, `.nav-tab-btn`, `.step-title`), delegando la renderización interna a los componentes de paso.
4. **En Vistas Administrativas:** `AdminBuilderView.vue` se conserva como fachada que reenvía a la vista consolidada de constructor para no invalidar `AppNavigation.spec.ts`.

### 5.4 Protocolo de Rollback y Puntos de Control Git
- Antes de iniciar cada fase, se genera un tag ligero anotado (`phase-N-start`).
- Cada fase se ejecuta en una rama dedicada (`refactor/phase-N-<nombre>`).
- Si una fase introduce una falla que no pueda resolverse en el tiempo asignado o genera regresiones en las baterías de pruebas, se ejecuta el protocolo de retorno inmediato:
  ```bash
  git checkout -f <tag-de-fase-anterior>
  ```
- Para la base de datos de desarrollo SQLite, se mantiene una copia de respaldo inmutable (`pdul_dev.db.backup_pre_seed`) que permite restaurar el estado inicial en un solo comando:
  ```bash
  cp pdul_dev.db.backup_pre_seed pdul_dev.db
  ```

---

## 6. Protocolo de Verificación y Validación Independiente

Para la auditoría y validación forense independiente del plan y de su posterior ejecución, se establecen los comandos exactos y sus resultados esperados:

### 6.1 Comandos de Ejecución y Criterios de Éxito

1. **Batería de Pruebas de Extremo a Extremo (E2E Opaque-Box):**
   ```bash
   ./tests_e2e/run_e2e_tests.sh
   ```
   *Criterio de Éxito:* Salida con código 0: `✓ ÉXITO TOTAL: 100% de las pruebas pasaron (145/145)`.
   - Tier 1: 75/75 OK
   - Tier 2: 51/51 OK
   - Tier 3: 8/8 OK
   - Tier 4: 5/5 OK
   - Tier 5: 6/6 OK

2. **Batería de Pruebas Unitarias e Integración Backend (Pytest):**
   ```bash
   backend/.venv/bin/pytest backend/
   ```
   *Criterio de Éxito:* Salida con código 0: `57 passed in < 1.0s (100% éxito)`.

3. **Batería de Pruebas Unitarias Frontend (Vitest):**
   ```bash
   cd frontend && npm run test:unit
   ```
   *Criterio de Éxito:* Salida con código 0: `Test Files 18 passed (18) | Tests 200 passed (200)`.

4. **Compilación y Tipado TypeScript Frontend:**
   ```bash
   cd frontend && npm run build
   ```
   *Criterio de Éxito:* Salida con código 0: `vue-tsc --noEmit` finaliza sin errores de tipo y Vite emite el paquete en `frontend/dist/`.

5. **Validación Semántica del Esquema Form.io Canónico:**
   ```bash
   python3 .agent/skills/formio-survey-architect/scripts/validate_formio_schema.py shared/schemas/pdul_origen_destino.json
   ```
   *Criterio de Éxito:* Salida con código 0: `VALIDATION OK`.

6. **Auditoría Forense de Penetración de PII:**
   ```bash
   PYTHONPATH=. backend/.venv/bin/python backend/tests/penetration_pii_harness.py
   ```
   *Criterio de Éxito:* Salida con código 0: `[PASS] No sensitive PII strings detected across all standard analytics endpoints`.

### 6.2 Condiciones de Invalidación Inmediata
Cualquiera de los siguientes eventos constituye causal de invalidación y rechazo inmediato de la entrega:
- Falla o desactivación de cualquiera de las 145 pruebas de `tests_e2e`, 57 pruebas de `pytest` o 200 pruebas de `vitest`.
- Modificación de contratos de datos personales que exponga cédulas, nombres o datos de contacto en endpoints públicos.
- Incorporación de dependencias externas a servidores en la nube comercial (CDNs, Google Maps, Form.io Cloud).
- Inclusión de librerías CSS utilitarias prohibidas (Tailwind CSS o PrimeFlex).
- Eliminación de atributos de accesibilidad WAI-ARIA o reducción de blancos táctiles por debajo de 48px.

---

## 7. Aprobación y Certificación del Plan

El presente **Plan Maestro de Modularización** queda debidamente registrado en la raíz del repositorio (`/home/seem/Documentos/_proyectos/cuestionario-pedul/PLAN_MODULARIZACION.md`) como documento rector y vinculante para la ejecución de las fases de modularización del sistema.

| Rol | Agente Responsable | Estado de Aprobación |
|---|---|:---:|
| **Arquitectura de Sistemas** | `system_architect` | **APROBADO** |
| **Gobernanza de Esquemas** | `schema_architect` | **APROBADO** |
| **Ingeniería de Persistencia** | `database_engineer` | **APROBADO** |
| **Núcleo Backend y APIs** | `backend_engineer` | **APROBADO** |
| **Experiencia de Usuario Móvil** | `ux_engineer` | **APROBADO** |
| **Dashboard y GIS Municipal** | `gis_dashboard_engineer` | **APROBADO** |
| **Verificación Adversarial** | `adversarial_challenger` | **CERTIFICADO** |
| **Auditoría y Puertas de Calidad** | `compliance_auditor` | **CERTIFICADO** |
