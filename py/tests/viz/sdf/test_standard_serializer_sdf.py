# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for SDF-styled objects in the standard viewer (Phase 1).

Covers the ``SdfStyle`` opt-in and the serializer routing that emits
``kind:"sdf"`` objects from the standard viewer instead of the normal mesh
pipeline, plus regressions for the unchanged non-SDF and fullscreen-SDF paths.
"""

from __future__ import annotations

import math
from copy import copy

import pytest
from pytanga.geometry.entities import (
    Direction,
    Line,
    Plane,
    Point,
    Sphere,
)
from pytanga.viz import SdfStyle, Visualizer
from pytanga.viz._styles import _DEFAULT_STYLE_FOR_KIND as _CANONICAL
from pytanga.viz.sdf import Composed, capped_cylinder, sphere
from pytanga.viz.serializer import serialize_entity


def _serialize(ent, props=None, *, styles_map=None):
    """Serialize with fresh canonical defaults (mirrors ``test_serializer.py``)."""
    sm = (
        {k: copy(v) for k, v in _CANONICAL.items()}
        if styles_map is None
        else styles_map
    )
    return serialize_entity(ent, "test_id", properties=props, styles_map=sm)


def test_sdf_style_serializes_kind_sdf() -> None:
    result = _serialize(Sphere(Point(1, 1, 1), 2.5), {"style": SdfStyle()})
    assert result["id"] == "test_id"
    assert result["layer"] == "scene"
    assert result["kind"] == "sdf"
    assert result["sdfKind"] == "Sphere"
    assert result["tree"]["kind"] == "sphere"


def test_sdf_style_resolves_color_and_opacity() -> None:
    result = _serialize(
        Sphere(Point(0, 0, 0), 1.0),
        {"style": SdfStyle(color="#123456", opacity=0.5)},
    )
    assert result["color"] == "#123456"
    assert result["opacity"] == 0.5


def test_sdf_style_emits_default_knobs() -> None:
    result = _serialize(Sphere(Point(0, 0, 0), 1.0), {"style": SdfStyle()})
    style = result["style"]
    assert style["style_type"] == "SdfStyle"
    assert style["soft_shadows"] is True
    assert style["max_steps"] == 256
    assert style["bound_padding"] == 0.05


def test_sdf_style_emits_phase1_stubs() -> None:
    result = _serialize(Sphere(Point(0, 0, 0), 1.0), {"style": SdfStyle()})
    assert "bound" in result
    assert "transform" in result
    assert result["transform"]["position"] == [0.0, 0.0, 0.0]
    assert result["transform"]["scale"] == [1.0, 1.0, 1.0]


def test_non_sdf_entity_serializes_unchanged() -> None:
    result = _serialize(Sphere(Point(1, 2, 3), 2.5))
    assert result["kind"] == "Sphere"
    assert "sdfKind" not in result
    assert "tree" not in result
    assert result["center"] == [1.0, 2.0, 3.0]


def test_sdf_visualizer_output_unchanged() -> None:
    # The fullscreen SDF viewer path must not gain the standard viewer's
    # bound/transform/style fields.
    from pytanga.viz.sdf.serializer import serialize_entity as sdf_serialize

    result = sdf_serialize(Sphere(Point(0, 0, 0), 1.0), "s")
    assert result["kind"] == "sdf"
    assert result["sdfKind"] == "Sphere"
    assert result["tree"]["kind"] == "sphere"
    assert "bound" not in result
    assert "transform" not in result
    assert "style" not in result


def test_per_kind_sdf_default_opts_in() -> None:
    # A per-kind SdfStyle default (styles_map["Sphere"]) also opts entities in.
    sm = {k: copy(v) for k, v in _CANONICAL.items()}
    sm["Sphere"] = SdfStyle()
    result = _serialize(Sphere(Point(0, 0, 0), 1.0), styles_map=sm)
    assert result["kind"] == "sdf"
    assert result["sdfKind"] == "Sphere"


def test_sdf_sphere_local_space() -> None:
    result = _serialize(Sphere(Point(1, 2, 3), 2.5), {"style": SdfStyle()})
    assert result["kind"] == "sdf"
    # The node transform carries all placement (the sphere centre).
    assert result["transform"]["position"] == pytest.approx([1.0, 2.0, 3.0])
    # The local tree is centred at the origin (no world position baked in).
    tree = result["tree"]
    assert tree["kind"] == "sphere"
    pos = tree.get("transform", {}).get("position", [0.0, 0.0, 0.0])
    assert pos == pytest.approx([0.0, 0.0, 0.0])
    # Radius-sized bound (inflated by the default bound_padding = 0.05).
    r = 2.5 + 0.05
    assert result["bound"]["min"] == pytest.approx([-r, -r, -r])
    assert result["bound"]["max"] == pytest.approx([r, r, r])


def test_sdf_infinite_line_finite_bound() -> None:
    line = Line(Point(0, 0, 0), Direction(1, 0, 0))
    result = _serialize(line, {"style": SdfStyle(), "thickness": 0.05})
    assert result["kind"] == "sdf"
    for v in result["bound"]["min"] + result["bound"]["max"]:
        assert math.isfinite(v)


def test_sdf_infinite_plane_finite_bound() -> None:
    plane = Plane(Point(0, 0, 0), Direction(0, 0, 1))
    result = _serialize(plane, {"style": SdfStyle()})
    assert result["kind"] == "sdf"
    for v in result["bound"]["min"] + result["bound"]["max"]:
        assert math.isfinite(v)


def test_sdf_composed_serializes_kind_sdf() -> None:
    bead = Composed(sphere(0.7), (capped_cylinder(1.0, 0.45), "subtract"))
    result = _serialize(bead, {"style": SdfStyle(color="#44ff44")})
    assert result["kind"] == "sdf"
    assert result["sdfKind"] == "Composed"
    assert result["tree"]["kind"] == "group"
    assert result["color"] == "#44ff44"
    # A Composed tree has a finite (centred) bound.
    for v in result["bound"]["min"] + result["bound"]["max"]:
        assert math.isfinite(v)


def test_visualizer_add_composed_sdf() -> None:
    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    oid = viz.add(
        Composed(sphere(0.7), (capped_cylinder(1.0, 0.45), "subtract")),
        style=SdfStyle(color="#44ff44"),
    )
    objs = viz._scene.full_state(styles_map=viz.styles.kind)
    sdf_objs = [o for o in objs if o["id"] == oid]
    assert len(sdf_objs) == 1
    obj = sdf_objs[0]
    assert obj["kind"] == "sdf"
    assert obj["sdfKind"] == "Composed"
    assert obj["tree"]["kind"] == "group"


def test_visualizer_add_sdf_sphere_with_label() -> None:
    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    oid = viz.add(
        Sphere(Point(1, 2, 3), 1.5),
        style=SdfStyle(color="#ffaa00"),
        label="SDF sphere",
    )
    objs = viz._scene.full_state(styles_map=viz.styles.kind)
    kinds = {o["id"]: o["kind"] for o in objs}
    assert kinds[oid] == "sdf"
    # The label is a separate overlay object attached to the SDF object.
    assert any(o["kind"] == "label" for o in objs)


