# 🏙️ PDUL Maturín — Plataforma Web de Encuestas y Movilidad Urbana

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Vue 3](https://img.shields.io/badge/Vue-3.5+-4FC08D.svg?style=flat-square&logo=vuedotjs&logoColor=white)](https://vuejs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6+-3178C6.svg?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-4169E1.svg?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Leaflet](https://img.shields.io/badge/GIS-Leaflet%20%2B%20GeoJSON-199900.svg?style=flat-square&logo=leaflet&logoColor=white)](https://leafletjs.com)
[![Apache ECharts](https://img.shields.io/badge/Analytics-Apache%20ECharts-AA344D.svg?style=flat-square&logo=apacheecharts&logoColor=white)](https://echarts.apache.org)
[![Tests](https://img.shields.io/badge/Tests-365%2B%20Passing-success.svg?style=flat-square&logo=pytest&logoColor=white)](#-testing--calidad-de-código)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

Sistema integral de captura, supervisión geoespacial y analítica de datos para el **Plan de Desarrollo Urbano Local (PDUL)** del Municipio Maturín (Monagas, Venezuela). Diseñado para digitalizar el estudio de transporte y movilidad urbana con arquitectura resiliente a fallos de conectividad en campo, anonimización estricta de datos personales (PII) y procesamiento de matrices Origen-Destino (O-D).

---

## 🌟 Características Destacadas

### 1. 📋 Captura Asistida y Experiencia Ciudadana (Mobile-First)
- **Wizard por pasos accesible:** Formulario modularizado paso a paso sin recarga, navegación por teclado y ergonomía táctil en pantalla móvil ($\ge 48\text{px}$).
- **Composición del Hogar y Grilla de Viajes Dinámica:** Registro granular de cada residente y sus viajes diarios con prellenado contextual y acción en 1 toque *"Regreso a casa"*.
- **Catálogo Oficial Georreferenciado:** Integración de las 11 parroquias oficiales de Maturín y un catálogo validado de **103 rutas de transporte público**.
- **Resiliencia Offline e Idempotencia:** Autoguardado continuo en almacenamiento local (`localStorage`), cola de reintentos (`IndexedDB` / `offline_queue`) y clave de idempotencia nativa (`client_submission_id` UUIDv4) para evitar duplicados ante reconexiones intermitentes.
- **Detección Automática de Dispositivo:** Identificación del entorno de captura (Móvil, Tablet, Escritorio) para auditoría de campo.

### 2. 🗺️ Supervisión Geográfica en Tiempo Real (Field Map)
- **Monitoreo Cartográfico de Encuestadores:** Visualización interactiva con Leaflet y OpenStreetMap de las ubicaciones exactas donde se levanta cada encuesta.
- **Semáforo de Calidad GPS y Auditoría de IP:**
  - 🟢 **Alta precisión:** Margen de error $\le 100\text{ m}$ (GPS satelital en campo).
  - 🟠 **Media precisión:** Margen entre $101\text{ m}$ y $500\text{ m}$.
  - 🔴 **Alerta Geográfica / IP:** Coordenadas fuera del municipio Maturín o con error $> 500\text{ m}$ (posible captura en PC de escritorio o estimación inexacta por dirección IP).
- **Inspección Rápida de Campo:** Apertura directa del detalle completo de la encuesta desde el mapa.

### 3. 📊 Dashboard Analítico y Matrices Origen-Destino
- **Mapa Coroplético Municipal:** Distribución espacial de respuestas por parroquia con visualización coroplética reactiva.
- **Analítica de Movilidad Urbana:** Indicadores de reparto modal (transporte público, vehículo particular, a pie, bicicleta), tiempos medios de traslado y costos en Bs.
- **Matriz O-D Interactiva:** Flujos de viajes intercomunales y frecuencias entre macrozonas.

### 4. 🔒 Privacidad, Soberanía y Seguridad (Data Privacy First)
- **Enmascaramiento de PII:** Censura estricta de Cédula de Identidad y datos sensibles en la capa de observabilidad, logs estructurados JSON y vistas públicas de analítica.
- **Exportación con Anonimización Opcional:** Descarga de microdatos en CSV y JSON con toggle de anonimización para exportes estadísticos conformes a normativas de protección de datos.

---

## 🏗️ Arquitectura del Sistema

El proyecto está diseñado bajo principios de **Clean Architecture** y separación estricta de responsabilidades:

```
cuestionario-pedul/
├── backend/                       # API Asíncrona (FastAPI + SQLAlchemy 2.0)
│   ├── alembic/                   # Migraciones versionadas de esquema PostgreSQL
│   ├── app/
│   │   ├── api/v1/endpoints/      # Rutas REST (encuestas, analítica, administración)
│   │   ├── core/                  # Configuración (Pydantic Settings), DB async y logging
│   │   ├── domain/                # Entidades puras y lógica de dominio
│   │   ├── infrastructure/        # Repositorios SQLAlchemy y adaptadores
│   │   ├── models/                # Modelos ORM (encuestas, respuestas_ciudadanas)
│   │   ├── schemas/               # Contratos Pydantic v2 (I/O, RFC 7807 problem details)
│   │   └── services/              # Casos de uso, idempotencia, normalizadores y PII masking
│   └── tests/                     # Suite de pruebas Pytest (Unitarias e Integración)
├── frontend/                      # SPA Reactiva (Vue 3 + TypeScript + Vite)
│   ├── src/
│   │   ├── components/            # Componentes modulares (Admin, Dashboard, Encuesta)
│   │   ├── composables/           # Lógica reutilizable (Mapas, Drafts, Analítica, Offline)
│   │   ├── services/              # Clientes HTTP tipados (FastAPI backend)
│   │   ├── utils/                 # Formateadores, validadores y catálogos
│   │   └── views/                 # Vistas principales (Wizard, Dashboard, Admin, Mapa)
│   └── tests/                     # Pruebas frontend (Vitest + Vue Test Utils)
├── shared/                        # Contratos y catálogos compartidos
│   ├── catalogs/                  # Catálogos canónicos (parroquias, rutas, motivos)
│   ├── geojson/                   # Cartografía municipal de Maturín
│   └── schemas/                   # Esquemas JSON canónicos (Form.io)
└── docs/                          # Documentación técnica y especificaciones de arquitectura
```

### Modelo de Datos Híbrido (PostgreSQL + JSONB)
Combina el rigor relacional con la flexibilidad de documentos JSONB:
- **`encuestas`:** Control del ciclo de vida, metadatos, estado de publicación y esquema JSONB canónico.
- **`respuestas_ciudadanas`:** Almacenamiento optimizado de las respuestas con índices **GIN** `jsonb_path_ops` para consultas de alto rendimiento y proyecciones relacionales de campos clave (`parroquia`, `zona_od`, `client_submission_id`, `fecha_registro`).

---

## 🚀 Puesta en Marcha Local

### Prerrequisitos
- **Node.js** $\ge 20.0$ y `npm`
- **Python** $\ge 3.11$ (probado en 3.13)
- **PostgreSQL** $\ge 15$ (o SQLite local para pruebas rápidas)

### 1. Clonar el Repositorio
```bash
git clone https://github.com/Alexjhzg/cuestionario-pdul.git
cd cuestionario-pdul
```

### 2. Configurar el Backend (FastAPI)
```bash
# Crear y activar entorno virtual
python3 -m venv backend/.venv
source backend/.venv/bin/activate

# Instalar dependencias
pip install -r backend/requirements.txt

# Copiar variables de entorno
cp .env.example .env

# Ejecutar migraciones de base de datos
alembic upgrade head

# Iniciar servidor de desarrollo
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
La documentación interactiva OpenAPI/Swagger estará disponible en: `http://localhost:8000/docs`

### 3. Configurar el Frontend (Vue 3 + Vite)
```bash
cd frontend

# Instalar dependencias
npm install

# Iniciar servidor Vite en desarrollo
npm run dev
```
La aplicación web estará disponible en: `http://localhost:5173`

---

## 🧪 Testing y Calidad de Código

El repositorio cuenta con una cobertura integral automatizada que supera los **365 tests**:

```bash
# Ejecutar pruebas unitarias e integración del Backend (84 tests)
backend/.venv/bin/pytest backend/tests/ -v

# Ejecutar pruebas unitarias del Frontend (281 tests en 28 suites)
npm --prefix frontend run test:unit

# Verificación de tipos TypeScript y Build de Producción
npm --prefix frontend run type-check
npm --prefix frontend run build
```

---

## ☁️ Despliegue en Producción

El repositorio incluye la especificación lista para desplegar en [Render](https://render.com) mediante [render.yaml](render.yaml):

- **Backend:** Web Service en Python con auto-migración `alembic upgrade head` y ASGI con `uvicorn`.
- **Frontend:** Static Site compilado con Vite y redirecciones SPA (`/* -> /index.html`).
- **Base de Datos:** Instancia gestionada de PostgreSQL 16.

---

## 📄 Licencia

Este proyecto está bajo la Licencia [MIT](LICENSE).

---

Desarrollado para el **Plan de Desarrollo Urbano Local (PDUL)** — Maturín, Monagas.

