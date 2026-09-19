# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Regression tests: the coordinate-overlay modules are in the export bundle.

``generate_library_js()`` (used by `inline`/`offline` export and by
`tools/build-viewer-js.py` to build the committed `js/tanga-viewer.js` that
jsDelivr serves for `delivery="cdn"`) must contain the tick math and both
renderers.
"""

from __future__ import annotations

from pathlib import Path

from pytanga.viz.export._bootstrap._html import generate_bootstrap_js

_REPO_ROOT = Path(__file__).resolve().parents[3]
_BUNDLE = _REPO_ROOT / "js" / "tanga-viewer.js"


def test_bootstrap_bundles_overlay_modules():  # noqa: ANN201
    b = generate_bootstrap_js("")
    assert "function niceLinearTicks(" in b
    assert "function formatValue(" in b
    assert "class AxesOverlay" in b
    assert "class GridUnderlay" in b


def test_committed_bundle_contains_overlay_modules():  # noqa: ANN201
    if not _BUNDLE.exists():
        return  # bundle is not required in every environment
    text = _BUNDLE.read_text(encoding="utf-8")
    assert "function niceLinearTicks(" in text
    assert "function formatValue(" in text
    assert "class AxesOverlay" in text
    assert "class GridUnderlay" in text


def test_bundle_defines_lighting_before_use():  # noqa: ANN201
    # Guard against a load-time TDZ in the concatenated bundle: `ray.js` reads
    # `lightPreamble` (from `sdf/lighting.js`) at module-load time, so the
    # definition must precede its use in the bundle's single scope.
    b = generate_bootstrap_js("")
    assert b.index("const lightPreamble") < b.index("${lightPreamble}")
