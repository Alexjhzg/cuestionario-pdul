"""Tier 4 Real-World Browser E2E Acceptance Runner.

Boots an isolated ephemeral uvicorn backend + built frontend/dist reverse-proxy
server and executes the Playwright Chromium suite in browser/e2e_journeys.spec.mjs.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from conftest import REPO_ROOT  # noqa: E402


def test_t4_playwright_browser_e2e_journeys_on_dist_bundle(
    dist_proxy_server: Dict[str, Any],
) -> None:
    config_path = THIS_DIR / "playwright.config.mjs"
    assert config_path.is_file(), f"Missing Playwright config: {config_path}"

    env = os.environ.copy()
    env["E2E_BASE_URL"] = dist_proxy_server["base_url"]
    env["PLAYWRIGHT_BASE_URL"] = dist_proxy_server["base_url"]

    res = subprocess.run(
        [
            "npx",
            "--prefix",
            str(REPO_ROOT / "frontend"),
            "playwright",
            "test",
            "--config",
            str(config_path),
        ],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, (
        f"Playwright browser E2E journeys failed (exit {res.returncode}).\n"
        f"STDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
    )
