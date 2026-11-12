# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests guarding the in-place updaters that remove per-frame entity rebuilds.

Renderer modules import ``three``, which is not installed in
``js/dev/node_modules``, so ``node --test`` cannot load them — the emitted
library text plus ``js/dev/tests/anim-export-smoke.mjs`` are the behavioural
gate.  These tests pin the *structural* contract instead: the affected kinds
must route to co-located updaters that rewrite geometry in place, and the
flat ``entityRequiresRebuild`` fallback must no longer short-circuit them.
"""

from __future__ import annotations

from pytanga.viz.export._bootstrap._html import (
    _RENDERERS_DIR,
    generate_library_js,
)

_RENDERER = _RENDERERS_DIR / "factory.js"


def _source(name: str) -> str:
    return (_RENDERERS_DIR / name).read_text(encoding="utf-8")


# ── PointPath (phase 4) ─────────────────────────────────────────────


def test_point_path_has_in_place_updater_and_helpers():  # noqa: ANN201
    src = _source("point_path.js")
    assert "export function updatePointPath" in src
    updater = src.split("export function updatePointPath", 1)[1]
    assert "rewriteFatLinePositions(mesh.geometry, positions)" in updater
    assert "hasVertexColors" in updater
    assert "export function flattenPath" in src
    assert "export function hasVertexColors" in src
    create = src.split("export function createPointPath", 1)[1].split(
        "export function updatePointPath", 1
    )[0]
    assert "flattenPath(" in create
    # The old updater was a bare `return false;` — the new one guards first.
    assert updater.index("if (") < updater.index("return false;")


def test_fat_line_rewrite_disposes_before_growing():  # noqa: ANN201
    helper = _source("fat-line-update.js")
    assert "export function rewriteFatLinePositions" in helper
    assert helper.index("geometry.dispose();") < helper.index("geometry.setPositions(")
    assert "geometry.instanceCount = count;" in helper


def test_apply_opacity_split_and_point_path_rebuild_short_circuit_removed():  # noqa: ANN201
    utils = _source("utils.js")
    assert "export function applyOpacityUpdate" in utils
    apply_style = utils.split("export function applyStyleUpdate", 1)[1]
    assert "applyOpacityUpdate(mesh, ent);" in apply_style
    rebuild = utils.split("export function entityRequiresRebuild", 1)[1]
    assert "ent.kind === 'PointPath'" not in rebuild


def test_point_path_helpers_survive_bundling_and_dispatch():  # noqa: ANN201
    lib = generate_library_js()
    assert "function applyOpacityUpdate(" in lib
    assert "function flattenPath(" in lib
    assert "function rewriteFatLinePositions(" in lib
    factory = _source("factory.js")
    assert "case 'PointPath':" in factory
    assert "return updatePointPath(mesh, ent, prev);" in factory


# ── Axis / Axes2D / Axes3D / Grid (phase 5) ───────────────────────


def test_axis_and_axes_updaters_exist_and_reuse_builder():  # noqa: ANN201
    axis = _source("axis.js")
    assert "export function updateAxis" in axis
    assert "clearGroupChildren(" in axis
    assert "addAxis(" in axis
    for name, updater_name in (("axes2d", "updateAxes2D"), ("axes3d", "updateAxes3D")):
        src = _source(f"{name}.js")
        assert f"export function {updater_name}" in src
        updater = src.split("export function update", 1)[1]
        assert "contentChanged(ent, prev, ['axes'])" in updater
        assert "addAxis(" in updater


def test_grid_updater_rewrites_positions_or_refills():  # noqa: ANN201
    grid = _source("grid.js")
    assert "export function updateGrid" in grid
    updater = grid.split("export function updateGrid", 1)[1]
    assert "setPositions(" in updater
    assert "clearGroupChildren(mesh, { disposeMaterials: false });" in updater
    assert "makeFatLineWithMaterial(" in updater


def test_entity_requires_rebuild_no_longer_short_circuits_kinds():  # noqa: ANN201
    utils = _source("utils.js")
    assert "export function clearGroupChildren" in utils
    rebuild = utils.split("export function entityRequiresRebuild", 1)[1]
    for kind in ("'Axis'", "'Axes2D'", "'Axes3D'", "'Grid'"):
        assert kind not in rebuild


def test_axis_grid_updaters_are_dispatched_and_bundled():  # noqa: ANN201
    factory = _source("factory.js")
    for kind in ("Axis", "Axes2D", "Axes3D", "Grid"):
        assert f"case '{kind}':" in factory
    lib = generate_library_js()
    for fn in (
        "function clearGroupChildren(",
        "function updateAxis(",
        "function updateAxes2D(",
        "function updateAxes3D(",
        "function updateGrid(",
    ):
        assert fn in lib
