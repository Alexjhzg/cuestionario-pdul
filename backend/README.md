# Backend: Plataforma Web de Encuestas y PDUL — Alcaldía de Maturín

API asíncrona de alto rendimiento construida con FastAPI, SQLAlchemy 2.0 (`AsyncSession`), Pydantic v2 y persistencia híbrida PostgreSQL JSONB con soporte offline e idempotencia nativa.

## Características Principales

1. **Clean Architecture:** Estricta separación por capas (`core`, `models`, `schemas`, `repositories`, `services`, `api/v1/endpoints`).
2. **Soberanía y Privacidad de Datos:** Enmascaramiento y anonimización estricta de PII (`cedula`, `nombre_apellido`, etc.) en analítica pública y registros estructurados de observabilidad.
3. **Idempotencia Nativa:** Control de reintentos mediante `client_submission_id` (UUID v4) para garantizar sincronización de la cola offline de campo sin duplicar registros.
4. **Validación Exhaustiva:** Validación de catálogo oficial de las 11 parroquias de Maturín, normalización de cédula (`^[0-9]{6,9}$`), validación de grilla de viajes y respuestas de error RFC 7807 (`ProblemDetailOut`).
5. **Constructor y Administración:** Endpoints CRUD para gestión de estados de encuestas (activa/inactiva), listado y exportación tabular (CSV/JSON).

## Estructura de Directorios

```
backend/
├── app/
│   ├── main.py                     # Instancia FastAPI, CORS, manejadores RFC 7807, lifespan
│   ├── core/
│   │   ├── config.py               # Configuración mediante Pydantic Settings
│   │   ├── database.py             # SQLAlchemy 2.0 AsyncEngine y sesión
│   │   └── logging.py              # Logger estructurado JSON con filtro PII
│   ├── models/
│   │   ├── encuesta.py             # Modelo relacional 'encuestas'
│   │   └── respuesta.py            # Modelo híbrido 'respuestas_ciudadanas'
│   ├── schemas/
│   │   ├── encuesta.py             # Esquemas Pydantic para encuestas
│   │   ├── submission.py           # FormioSubmissionIn y recibo SubmissionReceiptOut
│   │   ├── analytics.py            # Modelos de agregación para Leaflet y ECharts
│   │   └── problem.py              # Especificación RFC 7807 ProblemDetailOut
│   ├── repositories/
│   │   ├── encuesta_repo.py        # Acceso a datos de encuestas
│   │   └── survey_repo.py          # Consultas JSONB, unnesting y agregación
│   ├── services/
│   │   ├── normalizers.py          # Limpieza de cédula, parroquia y filtro PII
│   │   ├── survey_service.py       # Lógica de recepción e idempotencia
│   │   └── admin_service.py        # Administración y exportación de datos
│   └── api/v1/
│       ├── api.py                  # Enrutador principal v1
│       └── endpoints/
│           ├── encuestas.py        # Endpoints públicos de esquema y recepción
│           ├── analitica.py        # Endpoints analíticos (parroquias, O-D, modos)
│           └── admin.py            # Endpoints administrativos
├── tests/
│   ├── conftest.py                 # Fixtures de prueba y base de datos en memoria
│   ├── unit/                       # Pruebas unitarias aisladas
│   └── integration/                # Pruebas de integración de endpoints
├── pyproject.toml
└── requirements.txt
```

## Ejecución de Pruebas

Para ejecutar la suite completa de pruebas unitarias e integración con Pytest:

```bash
backend/.venv/bin/pytest backend/tests -v
```
