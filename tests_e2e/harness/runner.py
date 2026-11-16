#!/usr/bin/env python3
"""Runner Maestro para la Suite E2E Opaque-Box de la Plataforma PDUL - Alcaldía de Maturín.

Ejecuta las pruebas organizadas en los 4 niveles de la pirámide:
- Tier 1: Cobertura por Característica (Feature Coverage)
- Tier 2: Límites y Casos de Borde (Boundary & Corner Cases)
- Tier 3: Combinaciones Inter-módulo (Cross-Feature Combinations)
- Tier 4: Escenarios de Aplicación Real (Real-World Application Scenarios)

Retorna código de salida 0 únicamente si el 100% de las pruebas pasa.
"""

import os
from pathlib import Path
import sys
import time
import unittest

# Colores ANSI para salida en consola
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


class E2ERunner:
    def __init__(self, root_dir: Path) -> None:
        self.root_dir = root_dir
        self.tier_dirs = [
            ("Tier 1: Cobertura de Características", self.root_dir / "tier1_feature"),
            ("Tier 2: Casos Límite y de Borde", self.root_dir / "tier2_boundary"),
            ("Tier 3: Combinaciones Inter-módulo", self.root_dir / "tier3_cross_feature"),
            ("Tier 4: Escenarios de Aplicación Real", self.root_dir / "tier4_real_world"),
            ("Tier 5: Endurecimiento Adversarial", self.root_dir / "tier5_adversarial"),
        ]

    def run_all(self, verbose: bool = False) -> int:
        print(f"\n{BOLD}{CYAN}{'='*80}{RESET}")
        print(f"{BOLD}{CYAN} INICIANDO BATERÍA E2E OPAQUE-BOX — ALCALDÍA DE MATURÍN (PDUL){RESET}")
        print(f"{BOLD}{CYAN}{'='*80}{RESET}\n")

        total_tests = 0
        total_errors = 0
        total_failures = 0
        tier_summaries = []

        start_time = time.perf_counter()

        for tier_name, tier_path in self.tier_dirs:
            if not tier_path.exists():
                print(f"{YELLOW}ADVERTENCIA: Directorio {tier_path} no existe. Saltando.{RESET}")
                continue

            suite = unittest.defaultTestLoader.discover(
                start_dir=str(tier_path),
                pattern="test_*.py",
                top_level_dir=str(self.root_dir.parent),
            )
            count = suite.countTestCases()
            total_tests += count

            print(f"{BOLD}▶ Ejecutando {tier_name} ({count} pruebas)...{RESET}")
            t_start = time.perf_counter()

            stream = sys.stdout if verbose else open(os.devnull, "w")
            runner = unittest.TextTestRunner(
                stream=stream,
                verbosity=2 if verbose else 0,
                failfast=False,
            )
            result = runner.run(suite)
            t_elapsed = time.perf_counter() - t_start

            failures = len(result.failures)
            errors = len(result.errors)
            total_failures += failures
            total_errors += errors

            status_color = GREEN if (failures == 0 and errors == 0) else RED
            status_text = "PASS" if (failures == 0 and errors == 0) else "FAIL"
            print(
                f"  {status_color}✔ {tier_name}: {count - failures - errors}/{count} pruebas pasaron "
                f"[{status_text}] ({t_elapsed:.3f}s){RESET}"
            )

            if failures > 0:
                for test, trace in result.failures:
                    print(f"    {RED}FALLO: {test.id()}{RESET}")
                    if not verbose:
                        for line in trace.strip().splitlines()[-3:]:
                            print(f"      {line}")
            if errors > 0:
                for test, trace in result.errors:
                    print(f"    {RED}ERROR: {test.id()}{RESET}")
                    if not verbose:
                        for line in trace.strip().splitlines()[-3:]:
                            print(f"      {line}")

            tier_summaries.append({
                "name": tier_name,
                "total": count,
                "passed": count - failures - errors,
                "failed": failures + errors,
                "duration": t_elapsed,
            })

        total_elapsed = time.perf_counter() - start_time
        print(f"\n{BOLD}{CYAN}{'='*80}{RESET}")
        print(f"{BOLD} RESUMEN DE EJECUCIÓN E2E{RESET}")
        print(f"{BOLD}{CYAN}{'='*80}{RESET}")

        for s in tier_summaries:
            col = GREEN if s["failed"] == 0 else RED
            print(
                f"  • {s['name']:<40} : {col}{s['passed']}/{s['total']} OK{RESET} "
                f"({s['duration']:.3f}s)"
            )

        print(f"{'-'*80}")
        if total_failures == 0 and total_errors == 0:
            print(
                f"{BOLD}{GREEN}✓ ÉXITO TOTAL: 100% de las pruebas pasaron ({total_tests}/{total_tests}) "
                f"en {total_elapsed:.3f}s{RESET}\n"
            )
            return 0
        else:
            print(
                f"{BOLD}{RED}✗ FALLARON {total_failures + total_errors} de {total_tests} pruebas "
                f"en {total_elapsed:.3f}s{RESET}\n"
            )
            return 1


def main() -> int:
    verbose = "-v" in sys.argv or "--verbose" in sys.argv
    root_dir = Path(__file__).resolve().parent.parent
    runner = E2ERunner(root_dir)
    return runner.run_all(verbose=verbose)


if __name__ == "__main__":
    sys.exit(main())
