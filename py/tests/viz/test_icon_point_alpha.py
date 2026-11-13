# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Regression tests: icon-quad alpha survives style updates and hover.

An ``IconPointStyle`` (and any ``PointPath`` drawing icons) takes its alpha
from a glyph texture, not from ``material.opacity``.  The renderer therefore
sets ``transparent = True`` and ``depthWrite = False`` on the quad material.

A later style update, however, writes the *canonical* style opacity
(``1.0``) through ``applyOpacityUpdate``, which used to derive
``transparent``/``depthWrite`` from that number alone — turning the icon quad
opaque (a black/white square instead of a cut-out glyph).  The same happened on
hover via ``interaction.js``.  Both writers now honour the ``_alphaTexture``
userData tag that ``icon_point.js`` sets.

These tests pin the structural contract (the renderer modules import ``three``,
so ``node --test`` cannot load them).
"""

from __future__ import annotations

from pathlib import Path

from pytanga.viz.export._bootstrap._html import generate_library_js

_REPO_ROOT = Path(__file__).resolve().parents[3]
_TEMPLATES = _REPO_ROOT / "py" / "pytanga" / "viz" / "templates"
_BUNDLE = _REPO_ROOT / "js" / "tanga-viewer.js"


def _source(*parts: str) -> str:
    return (_TEMPLATES.joinpath(*parts)).read_text(encoding="utf-8")


# ── Renderer sources ────────────────────────────────────────────────


def test_icon_point_tags_texture_materials():  # noqa: ANN201
    src = _source("renderers", "icon_point.js")
    texture_block = src.split("if (texture) {", 1)[1].split(
        "const mesh = new THREE.Mesh", 1
    )[0]
    assert "material.userData" in texture_block
    assert "_alphaTexture: true" in texture_block


def test_opacity_update_honours_alpha_texture_in_both_branches():  # noqa: ANN201
    src = _source("renderers", "utils.js")
    assert src.count("target < 1.0 || alphaTex") == 2
    assert src.count("target >= 0.99 && !alphaTex") == 2


def test_hover_opacity_honours_alpha_texture():  # noqa: ANN201
    src = _source("interaction.js")
    assert "const alphaTex = !!(m.userData && m.userData._alphaTexture);" in src
    assert "m.transparent = translucent || alphaTex;" in src
    assert "m.depthWrite = !translucent && !alphaTex;" in src


# ── Export bundle ───────────────────────────────────────────────────


def test_generated_library_contains_alpha_texture_tag():  # noqa: ANN201
    lib = generate_library_js()
    # The icon marker plus both `applyOpacityUpdate` branches.
    assert lib.count("_alphaTexture") >= 2


def test_committed_bundle_contains_alpha_texture_tag():  # noqa: ANN201
    if not _BUNDLE.exists():
        return  # bundle is not required in every environment
    text = _BUNDLE.read_text(encoding="utf-8")
    assert "_alphaTexture" in text
