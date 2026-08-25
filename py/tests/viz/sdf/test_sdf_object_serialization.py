# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for SdfObject/Combine/Composed/SdfGroup serialization (Phase 4)."""

from __future__ import annotations

from pytanga.geometry import Point, Sphere
from pytanga.viz import SdfSphereStyle, Visualizer
from pytanga.viz.sdf import Combine, Composed, ECompose, SdfGroup, SdfObject, capped_cylinder, sphere
from pytanga.viz.sdf.serializer import serialize_entity, serialize_entity_local


def _obj(color: str | None = None) -> SdfObject:
    style = SdfSphereStyle(color=color) if color else SdfSphereStyle()
    return SdfObject(Sphere(Point(0.0, 0.0, 0.0), 1.0), style=style)


def test_sdf_object_via_viz_add() -> None:
    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    oid = viz.add(_obj("#ff0000"))
    obj = [o for o in viz._scene.full_state(styles_map=viz.styles.kind) if o["id"] == oid][0]
    assert obj["kind"] == "sdf"
    assert obj["sdfKind"] == "SdfObject"
    assert obj["color"] == "#ff0000"


def test_combine_via_viz_add() -> None:
    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    oid = viz.add(_obj("#00ff00") + _obj("#0000ff"))
    obj = [o for o in viz._scene.full_state(styles_map=viz.styles.kind) if o["id"] == oid][0]
    assert obj["kind"] == "sdf"
    assert obj["sdfKind"] == "Combine"
    assert obj["tree"]["kind"] == "union"  # binary combine lowers to a combinator


def test_composed_materials_array() -> None:
    composed = Composed(_obj("#ffaa00"), (_obj("#44ff44"), ECompose.SUBTRACT))
    result = serialize_entity_local(composed, "c", {})
    assert result["sdfKind"] == "Composed"
    assert result["materials"] == [
        {"color": "#ffaa00", "opacity": None},
        {"color": "#44ff44", "opacity": None},
    ]


def test_sdf_group_materials_array() -> None:
    group = SdfGroup(_obj("#ffaa00"), (_obj("#44ff44"), "subtract"))
    result = serialize_entity_local(group, "g", {})
    assert result["sdfKind"] == "SdfGroup"
    assert result["materials"][0]["color"] == "#ffaa00"
    assert result["materials"][1]["color"] == "#44ff44"


def test_operator_combine_serializes_nested_tree() -> None:
    node = (_obj() + _obj()).to_sdf_node()
    assert node.kind == "union"
    assert len(node.children) == 2


def test_fullscreen_composed_still_works() -> None:
    # Legacy fullscreen viewer path (SdfNode members + string modes) unchanged.
    composed = Composed(sphere(1.0), (capped_cylinder(0.5, 0.3), "subtract"))
    result = serialize_entity(composed, "c")
    assert result["tree"]["kind"] == "group"
    assert [c["kind"] for c in result["tree"]["children"]] == ["sphere", "cappedCylinder"]


def test_composed_invalid_mode_still_raises() -> None:
    import pytest

    with pytest.raises(ValueError):
        Composed(sphere(1.0), (sphere(0.5), "xor"))
