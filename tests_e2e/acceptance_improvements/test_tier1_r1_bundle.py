"""Tier 1 & Tier 2 Opaque-Box Acceptance Tests for R1:
- Feature F1: Lazy-loading admin views via defineAsyncComponent in frontend/src/App.vue
- Feature F2: Vite manualChunks bundle splitting in frontend/vite.config.ts & frontend/dist
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List


def _read_text(path: Path) -> str:
    assert path.is_file(), f"Expected file to exist: {path}"
    return path.read_text(encoding="utf-8")


def _list_dist_assets(dist_dir: Path) -> List[Path]:
    assets_dir = dist_dir / "assets"
    assert assets_dir.is_dir(), f"Missing built assets directory: {assets_dir}"
    return sorted(assets_dir.iterdir())


def _find_entry_assets(dist_dir: Path, ext: str) -> List[Path]:
    assets = _list_dist_assets(dist_dir)
    return [
        p for p in assets
        if p.name.startswith("index-") and p.name.endswith(ext)
    ]


def _find_vue_chunks(dist_dir: Path) -> List[Path]:
    return [
        p for p in _list_dist_assets(dist_dir)
        if p.name.endswith(".js")
        and "primevue" not in p.name.lower()
        and (
            p.name.lower().startswith("vue")
            or "vue-vendor" in p.name.lower()
            or "-vue" in p.name.lower()
        )
    ]


def _strip_vite_dynamic_import_manifest(js_code: str) -> str:
    """Strip Vite 5 __vite__mapDeps asset path strings and dynamic import('./...') specifiers
    so entry-bundle scans inspect actual bundled implementation code rather than lazy chunk names.
    """
    stripped = re.sub(r'["\'](?:\.?/)?assets/[^"\']+\.(?:js|css)["\']', '""', js_code)
    stripped = re.sub(r'import\s*\(\s*["\']\./[^"\']+["\']\s*\)', 'import("")', stripped)
    return stripped


# ---------------------------------------------------------------------------
# Feature F1 — App.vue defineAsyncComponent & citizen/admin view isolation
# ---------------------------------------------------------------------------


def test_f1_app_vue_imports_define_async_component(repo_root: Path) -> None:
    app_vue = _read_text(repo_root / "frontend" / "src" / "App.vue")
    assert "defineAsyncComponent" in app_vue, (
        "App.vue must import and use defineAsyncComponent for admin views."
    )


def test_f1_app_vue_lazy_loads_all_four_admin_views(repo_root: Path) -> None:
    app_vue = _read_text(repo_root / "frontend" / "src" / "App.vue")
    for symbol in ("DashboardView", "FormBuilderView", "AdminSurveyListView", "AdminResponsesView"):
        pattern = (
            rf"const\s+{symbol}\s*=\s*defineAsyncComponent\s*\(\s*\(\)\s*=>\s*"
            rf"import\s*\(\s*['\"](?:\./|@/)views/{symbol}\.vue['\"]\s*\)"
        )
        assert re.search(pattern, app_vue, re.DOTALL), (
            f"App.vue must define {symbol} with defineAsyncComponent(() => import('./views/{symbol}.vue'))"
        )


def test_f1_app_vue_keeps_survey_fill_view_static(repo_root: Path) -> None:
    app_vue = _read_text(repo_root / "frontend" / "src" / "App.vue")
    assert re.search(
        r"import\s+SurveyFillView\s+from\s+['\"]\./views/SurveyFillView\.vue['\"]",
        app_vue,
    ), "SurveyFillView must remain statically imported for immediate citizen rendering."
    assert not re.search(
        r"defineAsyncComponent[^;]*SurveyFillView",
        app_vue,
        re.DOTALL,
    ), "SurveyFillView must NOT be wrapped in defineAsyncComponent."


def test_f1_app_vue_preserves_type_exports_and_props(repo_root: Path) -> None:
    app_vue = _read_text(repo_root / "frontend" / "src" / "App.vue")
    assert "export type AppView" in app_vue
    assert "export interface NavTabItem" in app_vue
    assert "adminMode?: boolean" in app_vue
    assert "initialView?: AppView" in app_vue


def test_f1_app_vue_gates_admin_panels_with_v_if(repo_root: Path) -> None:
    app_vue = _read_text(repo_root / "frontend" / "src" / "App.vue")
    for view_id in ("gis-dashboard", "admin-surveys", "admin-responses", "form-builder"):
        assert f'v-if="currentView === \'{view_id}\'"' in app_vue, (
            f"Admin panel {view_id} must be gated by v-if so async chunk is not mounted/fetched prematurely."
        )
    assert 'v-show="!isAdminMode || currentView === \'survey-fill\'"' in app_vue


def test_f1_tier2_no_static_admin_imports_in_app_vue(repo_root: Path) -> None:
    app_vue = _read_text(repo_root / "frontend" / "src" / "App.vue")
    for symbol in ("DashboardView", "FormBuilderView", "AdminSurveyListView", "AdminResponsesView"):
        assert not re.search(
            rf"^\s*import\s+{symbol}\s+from\s+",
            app_vue,
            re.MULTILINE,
        ), f"{symbol} must not have a static top-level import in App.vue."


def test_f1_tier2_app_vue_does_not_directly_import_heavy_vendors(repo_root: Path) -> None:
    app_vue = _read_text(repo_root / "frontend" / "src" / "App.vue")
    for vendor in ("echarts", "leaflet", "@formio/"):
        assert vendor not in app_vue, f"App.vue shell must not directly import {vendor}."


def test_f1_tier2_citizen_survey_views_exclude_admin_and_heavy_vendors(repo_root: Path) -> None:
    citizen_files = [
        repo_root / "frontend" / "src" / "views" / "SurveyFillView.vue",
        repo_root / "frontend" / "src" / "components" / "survey" / "SurveyWizard.vue",
    ]
    forbidden = (
        "DashboardView",
        "FormBuilderView",
        "AdminSurveyListView",
        "AdminResponsesView",
        "echarts",
        "leaflet",
        "@formio/",
    )
    for fpath in citizen_files:
        content = _read_text(fpath)
        for token in forbidden:
            assert token not in content, f"Citizen component {fpath.name} must not reference {token}."


# ---------------------------------------------------------------------------
# Feature F2 — Vite manualChunks & production dist isolation
# ---------------------------------------------------------------------------


def test_f2_vite_config_defines_manual_chunks(repo_root: Path) -> None:
    vite_cfg = _read_text(repo_root / "frontend" / "vite.config.ts")
    assert "rollupOptions" in vite_cfg
    assert "manualChunks" in vite_cfg


def test_f2_vite_config_isolates_required_vendor_groups(repo_root: Path) -> None:
    vite_cfg = _read_text(repo_root / "frontend" / "vite.config.ts")
    for expected_marker in ("echarts", "zrender", "leaflet", "@formio/", "primevue", "vue"):
        assert expected_marker in vite_cfg, (
            f"vite.config.ts manualChunks must isolate '{expected_marker}'."
        )


def test_f2_dist_index_html_and_entry_chunks_exist(frontend_dist_dir: Path) -> None:
    index_html = _read_text(frontend_dist_dir / "index.html")
    assert "<script" in index_html
    js_entries = _find_entry_assets(frontend_dist_dir, ".js")
    css_entries = _find_entry_assets(frontend_dist_dir, ".css")
    assert len(js_entries) >= 1, "Expected initial entry JS bundle assets/index-*.js in frontend/dist."
    assert len(css_entries) >= 1, "Expected initial entry CSS bundle assets/index-*.css in frontend/dist."


def test_f2_dist_index_html_does_not_preload_heavy_or_admin_chunks(frontend_dist_dir: Path) -> None:
    index_html = _read_text(frontend_dist_dir / "index.html")
    forbidden_refs = (
        "echarts",
        "zrender",
        "leaflet",
        "formio",
        "DashboardView",
        "FormBuilderView",
        "AdminSurveyListView",
        "AdminResponsesView",
    )
    lowered = index_html.lower()
    for token in forbidden_refs:
        assert token.lower() not in lowered, (
            f"frontend/dist/index.html must not preload/link '{token}' on initial citizen load."
        )


def test_f2_dist_has_separate_vendor_and_admin_view_chunks(frontend_dist_dir: Path) -> None:
    asset_names = [p.name for p in _list_dist_assets(frontend_dist_dir)]
    js_names = [n for n in asset_names if n.endswith(".js")]

    # Heavy vendor JS chunks (note: leaflet is tree-shaken when DashboardView uses `import type`)
    assert any("echarts" in n.lower() or "zrender" in n.lower() for n in js_names), (
        f"Expected separate echarts/zrender JS chunk in dist/assets; found: {js_names}"
    )
    leaflet_assets = [n for n in asset_names if "leaflet" in n.lower()]
    for leaflet_asset in leaflet_assets:
        assert not leaflet_asset.startswith("index-") and not leaflet_asset.startswith("DashboardView-"), (
            f"If leaflet chunk is emitted, it must be isolated from index and DashboardView: {leaflet_asset}"
        )
    assert any("formio" in n.lower() for n in js_names), (
        f"Expected separate @formio/js JS chunk in dist/assets; found: {js_names}"
    )
    assert any("primevue" in n.lower() for n in js_names), (
        f"Expected separate primevue JS chunk in dist/assets; found: {js_names}"
    )
    assert _find_vue_chunks(frontend_dist_dir), (
        f"Expected separate vue vendor JS chunk in dist/assets; found: {js_names}"
    )

    # Admin view async JS chunks
    for view_name in ("DashboardView", "FormBuilderView", "AdminSurveyListView", "AdminResponsesView"):
        assert any(view_name in n for n in js_names), (
            f"Expected separate async JS chunk for {view_name} in dist/assets; found: {js_names}"
        )


def test_f2_tier2_initial_entry_js_excludes_heavy_libraries_and_admin_views(
    frontend_dist_dir: Path,
) -> None:
    js_entries = _find_entry_assets(frontend_dist_dir, ".js")
    assert js_entries, "Missing assets/index-*.js"
    combined_entry_js = "\n".join(_read_text(p) for p in js_entries)
    sanitized_entry_js = _strip_vite_dynamic_import_manifest(combined_entry_js)

    # Implementation-body signatures unique to heavy libraries or admin views
    # (excludes App.vue navTab labels such as 'Gestión de Encuestas' and Vite __vite__mapDeps paths)
    forbidden_markers = (
        "zrender",
        "echarts",
        "echartsInstance",
        "zrenderVersion",
        "registerTheme",
        "leaflet-container",
        "tileLayer",
        "formiojs",
        "formio-builder",
        "Dashboard de Movilidad Urbana",
        "Constructor Visual de Encuestas",
        "Supervisión de Respuestas Ciudadanas",
        "Respuestas Ciudadanas Recibidas",
        "Total de Encuestas",
    )
    for marker in forbidden_markers:
        assert marker not in sanitized_entry_js, (
            f"Initial citizen entry JS ({[p.name for p in js_entries]}) must NOT bundle '{marker}'."
        )


def test_f2_tier2_initial_entry_css_excludes_leaflet_and_formio_styles(
    frontend_dist_dir: Path,
) -> None:
    css_entries = _find_entry_assets(frontend_dist_dir, ".css")
    assert css_entries, "Missing assets/index-*.css"
    combined_entry_css = "\n".join(_read_text(p) for p in css_entries)

    for marker in (".leaflet-container", ".leaflet-tile", ".formio-builder", ".formio-component"):
        assert marker not in combined_entry_css, (
            f"Initial citizen entry CSS ({[p.name for p in css_entries]}) must NOT bundle '{marker}'."
        )


def test_f2_tier2_dist_contains_isolated_heavy_css_or_formio_css(frontend_dist_dir: Path) -> None:
    css_names = [p.name for p in _list_dist_assets(frontend_dist_dir) if p.name.endswith(".css")]
    non_entry_css = [n for n in css_names if not n.startswith("index-")]
    assert len(non_entry_css) >= 1, (
        f"Expected admin/vendor CSS to be code-split outside index-*.css; found CSS: {css_names}"
    )
    assert any("formio" in n.lower() or "formbuilder" in n.lower() for n in non_entry_css), (
        f"Expected Form.io/FormBuilder CSS in split CSS chunks; found: {non_entry_css}"
    )


def test_f2_tier2_all_index_html_asset_links_exist_on_disk(frontend_dist_dir: Path) -> None:
    index_html = _read_text(frontend_dist_dir / "index.html")
    refs = re.findall(r'(?:src|href)=["\'](/assets/[^"\']+)["\']', index_html)
    assert len(refs) >= 2, f"Expected entry JS and CSS asset links in index.html, got: {refs}"
    for rel in refs:
        target = frontend_dist_dir / rel.lstrip("/")
        assert target.is_file(), f"Asset referenced by dist/index.html does not exist: {target}"


def test_f2_tier2_dist_excludes_echarts_leaflet_from_vue_chunk(frontend_dist_dir: Path) -> None:
    vue_chunks = _find_vue_chunks(frontend_dist_dir)
    assert vue_chunks, "Expected a dedicated vue chunk in frontend/dist/assets/"
    vue_code = "\n".join(_read_text(p) for p in vue_chunks)
    for forbidden in ("zrender", "leaflet-container", "formiojs", "formio-builder"):
        assert forbidden not in vue_code, (
            f"Vue chunk must not absorb '{forbidden}'."
        )
