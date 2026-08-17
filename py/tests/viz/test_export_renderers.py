# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests ensuring HTML exports bundle every renderer used by the live view.

The live three.js viewer dispatches through ``templates/renderers/factory.js``
and imports every ``*.js`` module in ``templates/renderers/``.  The HTML export
pipeline concatenates those same modules via ``_RENDERER_FILES``.  These tests
guard the invariant that the export bundle does not drift from the on-disk
renderer set (the regression that caused ``createAxes3D``/``createAxes2D`` to
be missing).
"""

from __future__ import annotations

import re

from pytanga.viz.export._bootstrap._html import (
    _RENDERER_FILES,
    _RENDERERS_DIR,
    generate_bootstrap_js,
)

_EXPORT_FUNC_RE = re.compile(r"^export\s+(?:async\s+)?function\s+(\w+)")


def _renderer_js_files():
    """Return all ``*.js`` renderer modules on disk, relative to the renderers dir."""
    return {p.relative_to(_RENDERERS_DIR) for p in _RENDERERS_DIR.rglob("*.js")}


def _bundled_js_files():
    """Return the renderer modules listed in the export bundle, relative to the renderers dir."""
    return {p.relative_to(_RENDERERS_DIR) for p in _RENDERER_FILES}


def test_renderer_files_match_live_view_directory():
    """The export bundle must include exactly the renderer modules on disk."""
    on_disk = _renderer_js_files()
    bundled = _bundled_js_files()

    missing = on_disk - bundled
    stale = bundled - on_disk

    assert not missing, (
        "Renderer modules on disk are missing from the HTML export bundle: "
        f"{sorted(str(p) for p in missing)}"
    )
    assert not stale, (
        "Renderer modules listed in the HTML export bundle no longer exist "
        f"on disk: {sorted(str(p) for p in stale)}"
    )


def test_bootstrap_defines_every_renderer_function():
    """The generated bootstrap must define each exported renderer function."""
    on_disk = _renderer_js_files()

    exported: dict[str, str] = {}
    for rel in on_disk:
        src = (_RENDERERS_DIR / rel).read_text(encoding="utf-8")
        for line in src.splitlines():
            m = _EXPORT_FUNC_RE.match(line.strip())
            if m:
                exported[m.group(1)] = str(rel)

    assert exported, "No exported renderer functions found; test is misconfigured."

    bootstrap = generate_bootstrap_js("")

    # Note: async functions are emitted as ``async function foo(...)``, which
    # still contains ``function foo(...)`` as a substring, so a single check
    # covers both plain and async renderer functions.
    for func_name, rel in exported.items():
        assert f"function {func_name}(" in bootstrap, (
            f"Renderer function {func_name} (exported from {rel}) is missing "
            "from the generated HTML export bootstrap."
        )


def test_scene_builder_bundled():
    """The shared scene-builder module must be bundled in the export."""
    from pytanga.viz.export._bootstrap._html import _SHARED_JS_FILES

    assert _SHARED_JS_FILES, "No shared JS modules configured"
    for path in _SHARED_JS_FILES:
        assert path.exists(), f"Shared JS module missing on disk: {path}"

    bootstrap = generate_bootstrap_js("")
    assert "function buildSceneObject(" in bootstrap
    assert "function buildOverlay(" in bootstrap
    assert "function removeObject(" in bootstrap
