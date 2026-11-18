"""Tier 1 & Tier 2 Opaque-Box Acceptance Tests for R3 (Modularization & Repo Cleanup):
- Features F6–F12: Line count reduction below baselines for all 6 R3 files,
  dedicated submodule/composable/subcomponent extraction, and public contract preservation.
- Feature F8: Residual files preserved intact (exact sizes & SHA-256) in archive/ or
  ignored at root via .gitignore without deletion or git tracking.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Set

import pytest

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from conftest import R3_BASELINES, RESIDUAL_FILES, sha256_file  # noqa: E402

_PREEXISTING_FRONTEND_MODULES: Set[str] = {
    "services/api.ts",
    "services/analyticsApi.ts",
    "utils/validation.ts",
    "utils/schemaValidator.ts",
    "composables/useAnalytics.ts",
    "composables/usePiiMasking.ts",
    "composables/useLeafletMap.ts",
    "composables/useECharts.ts",
    "components/admin/FormioBuilder.vue",
    "components/dashboard/KpiCardsGrid.vue",
    "components/dashboard/MaturinChoroplethMap.vue",
    "components/dashboard/ModalSplitChart.vue",
    "components/dashboard/OdFlowMatrixChart.vue",
    "components/dashboard/ParroquiasBarChart.vue",
    "components/dashboard/CalificacionTpDonutChart.vue",
    "components/dashboard/DificultadesTpBarChart.vue",
    "components/dashboard/SeguridadCentroDonutChart.vue",
    "components/dashboard/QuestionChartCard.vue",
    "components/dashboard/AccessibleDataFallback.vue",
    "components/dashboard/BaseChart.vue",
}


def _line_count(path: Path) -> int:
    assert path.is_file(), f"Missing R3 target file: {path}"
    with path.open("rb") as fh:
        return sum(1 for _ in fh)


def _combined_text(paths: List[Path]) -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in paths if p.is_file())


def _resolve_frontend_local_imports(entry_file: Path, src_root: Path) -> List[Path]:
    """Recursively resolve local .ts/.vue imports rooted inside frontend/src/."""
    visited: Set[Path] = set()
    queue: List[Path] = [entry_file.resolve()]
    resolved_files: List[Path] = []
    import_re = re.compile(r"""from\s+['"]((?:\.|@/)[^'"]+)['"]""")

    while queue:
        current = queue.pop(0)
        if current in visited or not current.is_file():
            continue
        visited.add(current)
        resolved_files.append(current)

        text = current.read_text(encoding="utf-8")
        for spec in import_re.findall(text):
            if spec.startswith("@/"):
                base = (src_root / spec[2:]).resolve()
            else:
                base = (current.parent / spec).resolve()

            candidates = [
                base,
                base.with_suffix(".ts"),
                base.with_suffix(".vue"),
                base / "index.ts",
            ]
            for cand in candidates:
                if cand.is_file() and src_root.resolve() in cand.parents:
                    if cand not in visited:
                        queue.append(cand)
                    break

    return resolved_files


def _extracted_modules_for(entry_file: Path, repo_root: Path) -> List[Path]:
    src_root = repo_root / "frontend" / "src"
    all_local = _resolve_frontend_local_imports(entry_file, src_root)
    extracted: List[Path] = []
    for path in all_local:
        if path == entry_file.resolve():
            continue
        rel = path.relative_to(src_root.resolve()).as_posix()
        if rel.startswith("types/") or rel in _PREEXISTING_FRONTEND_MODULES:
            continue
        if rel.startswith(("utils/", "composables/", "components/")):
            extracted.append(path)
    return extracted


# ---------------------------------------------------------------------------
# R3 Line Count Reductions (F6, F7, F9, F10, F11, F12)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("rel_path,baseline_lines", list(R3_BASELINES.items()))
def test_r3_target_file_strictly_reduced_below_baseline(
    repo_root: Path,
    rel_path: str,
    baseline_lines: int,
) -> None:
    target = repo_root / rel_path
    actual = _line_count(target)
    assert actual < baseline_lines, (
        f"R3 modularization requires {rel_path} ({actual} lines) to be strictly < baseline ({baseline_lines} lines)."
    )


def test_r3_total_line_count_reduced_substantially(
    repo_root: Path,
    r3_baselines: Dict[str, int],
) -> None:
    total_baseline = sum(r3_baselines.values())
    total_actual = sum(_line_count(repo_root / rel) for rel in r3_baselines)
    assert total_actual < total_baseline, (
        f"Combined R3 line count ({total_actual}) must be strictly below baseline ({total_baseline})."
    )


# ---------------------------------------------------------------------------
# Extracted Submodules / Composables / Subcomponents & Public Contracts
# ---------------------------------------------------------------------------


def test_f6_question_analytics_modularized_submodules_exist(repo_root: Path) -> None:
    services_dir = repo_root / "backend" / "app" / "services"
    facade_src = (services_dir / "question_analytics.py").read_text(encoding="utf-8")

    # Accept dedicated package (e.g. question_analytics_parts/ or question_analytics/)
    # or dedicated sibling submodules imported by question_analytics.py
    pkg_candidates = [
        d for d in services_dir.iterdir()
        if d.is_dir() and "question_analytics" in d.name
    ]
    pkg_py_files = [
        p for d in pkg_candidates for p in d.glob("*.py") if not p.name.startswith("__")
    ]
    sibling_py_files = [
        p for p in services_dir.glob("question_analytics_*.py")
        if p.name != "question_analytics.py"
    ]
    extracted_py = pkg_py_files + sibling_py_files
    assert len(extracted_py) >= 2, (
        f"Expected >= 2 dedicated analytics submodules under {services_dir}, found: {[p.name for p in extracted_py]}"
    )
    assert "question_analytics" in facade_src


def test_f7_viajes_mobile_cards_extracted_modules_and_contracts(repo_root: Path) -> None:
    parent = repo_root / "frontend" / "src" / "components" / "survey" / "ViajesMobileCards.vue"
    extracted = _extracted_modules_for(parent, repo_root)
    assert len(extracted) >= 2, (
        f"Expected ViajesMobileCards.vue to extract dedicated subcomponents/utils, found: {[p.name for p in extracted]}"
    )

    parent_src = parent.read_text(encoding="utf-8")
    for prop_or_emit in ("modelValue", "zonaResidenciaDefault", "residentes", "update:modelValue", "agregar-regreso", "eliminar"):
        assert prop_or_emit in parent_src, f"ViajesMobileCards.vue must preserve contract symbol '{prop_or_emit}'"

    combined = _combined_text([parent, *extracted])
    for selector_id in ("viaje-persona", "viaje-origen", "viaje-destino", "viaje-motivo", "viaje-modo", "viaje-tiempo", "viaje-costo"):
        assert selector_id in combined, f"ViajesMobileCards subtree must preserve '#{selector_id}'"


def test_f7_tier2_viajes_mobile_cards_preserves_accessibility_and_actions(repo_root: Path) -> None:
    parent = repo_root / "frontend" / "src" / "components" / "survey" / "ViajesMobileCards.vue"
    extracted = _extracted_modules_for(parent, repo_root)
    combined = _combined_text([parent, *extracted])
    for attr_or_cls in (
        'aria-labelledby="titulo-viajes-od"',
        'aria-labelledby="modal-viaje-title"',
        "add-viaje-btn",
        "return-btn",
        "details-btn",
        "delete-btn",
    ):
        assert attr_or_cls in combined, f"ViajesMobileCards subtree must preserve '{attr_or_cls}'"


def test_f9_admin_responses_extracted_modules_and_contracts(repo_root: Path) -> None:
    view_path = repo_root / "frontend" / "src" / "views" / "AdminResponsesView.vue"
    extracted = _extracted_modules_for(view_path, repo_root)
    assert len(extracted) >= 2, (
        f"Expected AdminResponsesView.vue to extract dedicated submodules/composables, found: {[p.name for p in extracted]}"
    )

    view_src = view_path.read_text(encoding="utf-8")
    assert "initialSurveyId" in view_src

    combined = _combined_text([view_path, *extracted])
    for testid in (
        "select-survey-inspect",
        "pagination-info-text",
        "select-page-size",
        "btn-prev-page",
        "btn-next-page",
        "checkbox-mask-pii",
        "btn-view-mode-grid",
        "btn-view-mode-json",
        "grid-detail-viewer",
        "json-detail-viewer",
        "btn-copy-json",
        "btn-modal-close",
    ):
        assert testid in combined, f"AdminResponsesView subtree must preserve data-testid='{testid}'"


def test_f9_tier2_admin_responses_preserves_aria_and_pii_masking_integration(repo_root: Path) -> None:
    view_path = repo_root / "frontend" / "src" / "views" / "AdminResponsesView.vue"
    extracted = _extracted_modules_for(view_path, repo_root)
    combined = _combined_text([view_path, *extracted])
    for marker in (
        'aria-labelledby="responses-title"',
        'aria-labelledby="modal-detail-title"',
        "usePiiMasking",
        "pii-warning-banner",
    ):
        assert marker in combined, f"AdminResponsesView subtree must preserve '{marker}'"


def test_f10_admin_survey_list_extracted_modules_and_contracts(repo_root: Path) -> None:
    view_path = repo_root / "frontend" / "src" / "views" / "AdminSurveyListView.vue"
    extracted = _extracted_modules_for(view_path, repo_root)
    assert len(extracted) >= 2, (
        f"Expected AdminSurveyListView.vue to extract dedicated submodules/composables, found: {[p.name for p in extracted]}"
    )

    view_src = view_path.read_text(encoding="utf-8")
    for emit_name in ("create-survey", "edit-survey", "view-responses"):
        assert emit_name in view_src, f"AdminSurveyListView.vue must preserve emit '{emit_name}'"

    combined = _combined_text([view_path, *extracted])
    for testid in (
        "checkbox-redact-pii",
        "btn-create-new-survey",
        "btn-cancel-deactivation",
        "btn-confirm-deactivation",
    ):
        assert testid in combined, f"AdminSurveyListView subtree must preserve data-testid='{testid}'"


def test_f10_tier2_admin_survey_list_preserves_aria_switch_and_export_hooks(repo_root: Path) -> None:
    view_path = repo_root / "frontend" / "src" / "views" / "AdminSurveyListView.vue"
    extracted = _extracted_modules_for(view_path, repo_root)
    combined = _combined_text([view_path, *extracted])
    for marker in (
        'aria-labelledby="admin-title"',
        'aria-labelledby="confirm-dialog-title"',
        'role="switch"',
        "exportarRespuestasAdmin",
    ):
        assert marker in combined, f"AdminSurveyListView subtree must preserve '{marker}'"


def test_f11_form_builder_extracted_modules_and_contracts(repo_root: Path) -> None:
    view_path = repo_root / "frontend" / "src" / "views" / "FormBuilderView.vue"
    extracted = _extracted_modules_for(view_path, repo_root)
    assert len(extracted) >= 2, (
        f"Expected FormBuilderView.vue to extract dedicated submodules/composables, found: {[p.name for p in extracted]}"
    )

    view_src = view_path.read_text(encoding="utf-8")
    for symbol in ("initialSurveyId", "survey-created", "view-responses"):
        assert symbol in view_src, f"FormBuilderView.vue must preserve contract '{symbol}'"

    combined = _combined_text([view_path, *extracted])
    for testid in (
        "btn-validate-schema",
        "btn-export-json",
        "btn-save-survey",
        "btn-save-as-new",
        "btn-load-canonical",
        "btn-load-blank",
    ):
        assert testid in combined, f"FormBuilderView subtree must preserve data-testid='{testid}'"


def test_f11_tier2_form_builder_preserves_sovereign_validator_and_modal_aria(repo_root: Path) -> None:
    view_path = repo_root / "frontend" / "src" / "views" / "FormBuilderView.vue"
    extracted = _extracted_modules_for(view_path, repo_root)
    combined = _combined_text([view_path, *extracted])
    for marker in (
        "validateFormioSchema",
        'aria-labelledby="validation-dialog-title"',
        "FormioBuilder",
    ):
        assert marker in combined, f"FormBuilderView subtree must preserve '{marker}'"


def test_f12_dashboard_extracted_modules_and_type_only_map_import(repo_root: Path) -> None:
    view_path = repo_root / "frontend" / "src" / "views" / "DashboardView.vue"
    extracted = _extracted_modules_for(view_path, repo_root)
    assert len(extracted) >= 2, (
        f"Expected DashboardView.vue to extract dedicated submodules/composables, found: {[p.name for p in extracted]}"
    )

    dashboard_src = view_path.read_text(encoding="utf-8")
    assert not re.search(
        r"import\s+MaturinChoroplethMap\s+from\s+",
        dashboard_src,
    ), "DashboardView.vue must use `import type` (not runtime import) for MaturinChoroplethMap to isolate leaflet."


def test_f12_tier2_dashboard_preserves_accessible_fallback_and_filter_controls(repo_root: Path) -> None:
    view_path = repo_root / "frontend" / "src" / "views" / "DashboardView.vue"
    extracted = _extracted_modules_for(view_path, repo_root)
    combined = _combined_text([view_path, *extracted])
    for marker in (
        "AccessibleDataFallback",
        "btn-toggle-view",
        "questions-search-input",
        "section-pill-btn",
        "exportarRespuestasAdmin",
    ):
        assert marker in combined, f"DashboardView subtree must preserve '{marker}'"


# ---------------------------------------------------------------------------
# Feature F8 — Residual files preserved intact (archive/ or root + .gitignore)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("filename", list(RESIDUAL_FILES.keys()))
def test_f8_residual_file_preserved_intact_and_gitignored(
    repo_root: Path,
    filename: str,
) -> None:
    root_path = repo_root / filename
    archive_path = repo_root / "archive" / filename

    in_archive = archive_path.is_file()
    in_root = root_path.is_file()
    assert in_archive or in_root, (
        f"Residual file '{filename}' must be preserved intact (either in archive/ or ignored at root), never deleted."
    )
    assert not (in_archive and in_root), (
        f"Residual file '{filename}' should not remain duplicated in both root and archive/."
    )

    actual_path = archive_path if in_archive else root_path
    expected = RESIDUAL_FILES[filename]
    assert actual_path.stat().st_size == expected["size"], (
        f"Byte size mismatch for {actual_path}: expected {expected['size']}, got {actual_path.stat().st_size}"
    )
    assert sha256_file(actual_path) == expected["sha256"], (
        f"SHA-256 checksum mismatch for {actual_path}"
    )


def test_f8_gitignore_and_git_check_ignore_cover_residuals(repo_root: Path) -> None:
    gitignore = (repo_root / ".gitignore").read_text(encoding="utf-8")
    assert "archive/" in gitignore or "archive" in gitignore or "pdf_text.txt" in gitignore

    for filename in RESIDUAL_FILES:
        rel_path = (
            f"archive/{filename}"
            if (repo_root / "archive" / filename).is_file()
            else filename
        )
        res = subprocess.run(
            ["git", "check-ignore", "-q", rel_path],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
        assert res.returncode == 0, f"git check-ignore must ignore {rel_path}"


def test_f8_tier2_residual_files_are_not_git_tracked(repo_root: Path) -> None:
    for target in ("archive/", *RESIDUAL_FILES.keys()):
        res = subprocess.run(
            ["git", "ls-files", target],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
        assert res.returncode == 0
        assert res.stdout.strip() == "", f"{target} must not be tracked by git: {res.stdout}"


def test_f8_tier2_core_root_assets_remain_present(repo_root: Path) -> None:
    for required in ("render.yaml", "requirements.txt", "shared/schemas/pdul_origen_destino.json"):
        assert (repo_root / required).is_file(), f"Core root asset missing: {required}"
