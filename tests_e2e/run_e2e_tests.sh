#!/usr/bin/env bash
# ==============================================================================
# Script de Ejecución Maestro: Suite E2E Opaque-Box — Alcaldía de Maturín (PDUL)
# ==============================================================================
set -e

# Ubicar la raíz del proyecto
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH:-}"

echo "================================================================================"
echo " EJECUTANDO SUITE E2E OPAQUE-BOX — ALCALDÍA DE MATURÍN (PDUL)"
echo " Raíz del proyecto: ${PROJECT_ROOT}"
echo "================================================================================"

# Ejecutar el runner Python con soporte para argumentos opcionales (ej. -v / --verbose)
python3 "${PROJECT_ROOT}/tests_e2e/harness/runner.py" "$@"
EXIT_CODE=$?

exit ${EXIT_CODE}
