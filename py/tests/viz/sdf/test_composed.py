# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for Composed SDF objects and the primitive-level library (Phase 06b)."""

from __future__ import annotations

import pytest

from pytanga.viz.sdf import (
    Composed,
    SdfVisualizer,
    box,
    capped_cylinder,
    sphere,
    torus,
)
from pytanga.viz.sdf.serializer import serialize_entity


def test_composed_serializes_to_group() -> None:
    body = Composed(sphere(1.0), (capped_cylinder(0.5, 0.3), "subtract"))
    result = serialize_entity(body, "c")
    tree = result["tree"]
    assert tree["kind"] == "group"
    assert [c["kind"] for c in tree["children"]] == ["sphere", "cappedCylinder"]
    assert [c.get("combine", "union") for c in tree["children"]] == [
        "union",
        "subtract",
    ]


def test_composed_default_union() -> None:
    body = Composed(sphere(1.0), box((0.5, 0.5, 0.5)))
    result = serialize_entity(body, "c")
    modes = [c.get("combine", "union") for c in result["tree"]["children"]]
    assert modes == ["union", "union"]


def test_composed_nested() -> None:
    inner = Composed(sphere(1.0), (box((0.4, 0.4, 0.4)), "subtract"))
    outer = Composed(inner, (torus(1.0, 0.1), "subtract"))
    result = serialize_entity(outer, "c")
    tree = result["tree"]
    assert tree["kind"] == "group"
    assert tree["children"][0]["kind"] == "group"  # nested group
    assert tree["children"][1]["combine"] == "subtract"


def test_composed_smooth_union_roundtrip() -> None:
    body = Composed(sphere(1.0), (capped_cylinder(0.5, 0.3), "smooth_union", 0.15))
    result = serialize_entity(body, "c")
    tree = result["tree"]
    assert [c.get("combine", "union") for c in tree["children"]] == [
        "union",
        "smooth_union",
    ]
    assert [c.get("smoothness") for c in tree["children"]] == [None, 0.15]


def test_composed_invalid_combine_raises() -> None:
    with pytest.raises(ValueError):
        Composed(sphere(1.0), (box((0.5, 0.5, 0.5)), "xor"))


def test_composed_single_material() -> None:
    body = Composed(sphere(1.0), (box((0.5, 0.5, 0.5)), "subtract"))
    result = serialize_entity(body, "c", {"color": "#ff0000", "opacity": 0.5})
    assert result["sdfKind"] == "Composed"
    assert result["color"] == "#ff0000"
    assert result["opacity"] == 0.5


def test_sdf_node_serializes_directly() -> None:
    node = sphere(1.0, position=(1.0, 2.0, 3.0))
    result = serialize_entity(node, "n", {"color": "#00ff00"})
    assert result["sdfKind"] == "sphere"
    assert result["tree"]["kind"] == "sphere"
    assert result["tree"]["transform"]["position"] == [1.0, 2.0, 3.0]
    assert result["color"] == "#00ff00"


def test_visualizer_adds_composed_and_primitive() -> None:
    viz = SdfVisualizer(open_browser=False)
    viz.add(Composed(sphere(1.0)), color="#ffaa00")
    viz.add(box((0.5, 0.5, 0.5)))
    full_state, _ = viz._full_state_for("")
    assert len(full_state) == 2
    assert full_state[0]["sdfKind"] == "Composed"
    assert full_state[1]["sdfKind"] == "box"
