# Declaración de Suite de Pruebas Lista (TEST_READY)

**Fecha:** 2026-11-09T18:45:00Z  
**Autor:** `test_writer_e2e`  
**Estado:** LISTA PARA AUDITORÍA Y EJECUCIÓN (Tiers 1 a 4)

---

## 1. Resumen de Cobertura de la Suite E2E

Se ha establecido exitosamente la infraestructura completa de pruebas E2E de caja negra (opaque-box) bajo el directorio `tests_e2e/`, cubriendo exhaustivamente el inventario de características (F01–F62) y los contratos de interfaz de `PROJECT.md`.

| Nivel (Tier) | Directorio | Cantidad de Pruebas | Estado |
|--------------|------------|---------------------|--------|
| **Tier 1: Cobertura por Característica** | `tests_e2e/tier1_feature/` | 75 pruebas | 75/75 PASANDO (100%) |
| **Tier 2: Límites y Casos de Borde** | `tests_e2e/tier2_boundary/` | 51 pruebas | 49/51 PASANDO (2 defectos de implementación detectados) |
| **Tier 3: Combinaciones Inter-módulo** | `tests_e2e/tier3_cross_feature/` | 8 pruebas | 8/8 PASANDO (100%) |
| **Tier 4: Escenarios de Aplicación Real** | `tests_e2e/tier4_real_world/` | 5 pruebas | 5/5 PASANDO (100%) |
| **TOTAL GENERAL** | `tests_e2e/` | **139 pruebas** | **137/139 PASANDO (98.6%)** |

---

## 2. Componentes e Infraestructura Entregada

1. **Test Runner Maestro (`tests_e2e/run_e2e_tests.sh` y `tests_e2e/harness/runner.py`):**
   - Ejecuta las pruebas de forma secuencial por Tier con formato visual estructurado en consola y tiempos de ejecución.
   - Retorna código de salida limpio (código 0 si todas las pruebas pasan).
   - Compatible nativamente con Python `unittest` y `pytest`.

2. **Harness y Verificadores de Contratos (`tests_e2e/harness/`):**
   - `contracts.py`: Resolvedor de activos canónicos, emulador de persistencia e idempotencia con `client_submission_id`, verificador estricto de PII, simulador de cola offline y generador de tablas accesibles WCAG AA.
   - `fixtures.py`: Datos realistas de prueba para hogares unipersonales, familias multimodales, lotes rurales y esquemas de consultas ciudadanas del Form Builder.

3. **Documentación de Infraestructura (`TEST_INFRA.md`):**
   - Documento maestro con metodología, mapeo de características F01–F62 y comandos de ejecución.

---

## 3. Defectos de Implementación Descubiertos (Para Escalamiento)

La suite de pruebas E2E identificó dos discrepancias genuinas en los activos canónicos entregados en Milestone 1 (`shared/`):

1. **Conflicto de Mapeo en Catálogo de Modos de Transporte (`shared/catalogs/modos_transporte.json`):**
   - **Observación:** El archivo asigna el código `"1"` a `"A pie"`, `"2"` a `"Bicicleta"`, `"3"` a `"Motocicleta"`, `"4"` a `"Automóvil Particular"`, etc.
   - **Contrato Oficial (`PROJECT.md` Línea 151):** Exige `"1"` (Transporte público), `"2"` (Auto particular), `"3"` (A pie), `"4"` (Bicicleta), `"5"` (Moto), `"6"` (Taxi), `"7"` (Transporte laboral/escolar), `"8"` (Otro).
   - **Acción requerida:** Escalar a `worker_m1` para alinear los códigos de `modos_transporte.json` con la línea 151 de `PROJECT.md`.

2. **Orientación de Anillos de Polígonos GeoJSON (RFC 7946 Regla de la Mano Derecha):**
   - **Observación:** Los 11 polígonos de `shared/geojson/maturin_parroquias.geojson` tienen un área con signo negativo (orientación horaria / CW).
   - **Estándar RFC 7946 (Sección 3.1.6):** Los anillos exteriores de los polígonos deben estar orientados en sentido antihorario (CCW, área con signo positiva).
   - **Acción requerida:** Escalar a `worker_m1` para invertir el orden de los vértices de las coordenadas en `maturin_parroquias.geojson`.

---

## 4. Comando de Verificación Rápida

```bash
./tests_e2e/run_e2e_tests.sh
```
