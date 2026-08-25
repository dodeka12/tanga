# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the SDF primitive/combinator descriptor model (Phase 4)."""

from __future__ import annotations

import math

from pytanga.geometry import Direction, GeneralRotor, Point, Rotor
from pytanga.viz.sdf.primitives import (
    bound_box,
    box,
    capped_cylinder,
    combine,
    ellipsoid,
    group,
    primitive,
    sphere,
    torus,
)


def test_primitive_to_dict_minimal() -> None:
    node = primitive("sphere", {"radius": 1.0})
    assert node.to_dict() == {"kind": "sphere", "params": {"radius": 1.0}}


def test_primitive_with_transform() -> None:
    node = primitive("sphere", {"radius": 0.5}, position=(1.0, 2.0, 3.0))
    assert node.to_dict() == {
        "kind": "sphere",
        "params": {"radius": 0.5},
        "transform": {"position": [1.0, 2.0, 3.0]},
    }


def test_primitive_extra_params_merge() -> None:
    node = primitive("cappedCylinder", halfHeight=5.0, radius=1.0)
    assert node.params == {"halfHeight": 5.0, "radius": 1.0}


def test_combine_serializes_children() -> None:
    a = primitive("sphere", {"radius": 1.0})
    b = primitive("sphere", {"radius": 2.0})
    node = combine("union", a, b)
    assert node.to_dict() == {
        "kind": "union",
        "children": [
            {"kind": "sphere", "params": {"radius": 1.0}},
            {"kind": "sphere", "params": {"radius": 2.0}},
        ],
    }


def test_bound_box() -> None:
    node = bound_box((5.0, 5.0, 5.0), position=(0.0, 0.0, 2.0))
    assert node.kind == "bound"
    assert node.params == {"halfExtents": [5.0, 5.0, 5.0]}
    assert node.transform == {"position": [0.0, 0.0, 2.0]}


def test_identity_transform_is_none() -> None:
    node = primitive("sphere", {"radius": 1.0})
    assert node.transform is None


def test_primitive_id_serialized() -> None:
    node = sphere(1.0, id="outer")
    assert node.id == "outer"
    assert node.to_dict() == {
        "kind": "sphere",
        "params": {"radius": 1.0},
        "id": "outer",
    }


def test_group_serializes_children_with_combine() -> None:
    a = primitive("sphere", {"radius": 1.0})
    b = primitive("box", {"halfExtents": [0.5, 0.5, 0.5]})
    b.combine = "subtract"
    node = group([a, b])
    assert node.to_dict() == {
        "kind": "group",
        "children": [
            {"kind": "sphere", "params": {"radius": 1.0}},
            {
                "kind": "box",
                "params": {"halfExtents": [0.5, 0.5, 0.5]},
                "combine": "subtract",
            },
        ],
    }


def test_named_primitive_helpers() -> None:
    assert sphere(2.0).to_dict() == {"kind": "sphere", "params": {"radius": 2.0}}
    assert torus(1.0, 0.2).to_dict() == {
        "kind": "torus",
        "params": {"mainRadius": 1.0, "tubeRadius": 0.2},
    }


def test_position_accepts_point() -> None:
    node = sphere(1.0, position=Point(1.0, 2.0, 3.0))
    assert node.transform == {"position": [1.0, 2.0, 3.0]}


def test_position_accepts_direction() -> None:
    node = box((1.0, 1.0, 1.0), position=Direction(1.0, 0.0, 0.0))
    assert node.transform == {"position": [1.0, 0.0, 0.0]}


def test_rotation_accepts_rotor() -> None:
    node = capped_cylinder(
        1.5, 0.35, rotation=Rotor(math.pi / 2.0, Direction(0.0, 0.0, 1.0))
    )
    assert node.transform == {
        "rotation": {"axis": [0.0, 0.0, 1.0], "angle": math.pi / 2.0}
    }


def test_rotation_accepts_axis_angle_tuple() -> None:
    node = ellipsoid((1.0, 2.0, 3.0), rotation=((0.0, 0.0, 1.0), 0.5))
    assert node.transform == {"rotation": {"axis": [0.0, 0.0, 1.0], "angle": 0.5}}


def test_rotation_accepts_general_rotor_at_origin() -> None:
    node = capped_cylinder(
        1.0, 0.3, rotation=GeneralRotor(0.5, Direction(0.0, 0.0, 1.0), Point(0.0, 0.0, 0.0))
    )
    assert node.transform == {"rotation": {"axis": [0.0, 0.0, 1.0], "angle": 0.5}}


def test_rotation_displaced_general_rotor_raises() -> None:
    displaced = GeneralRotor(0.5, Direction(0.0, 0.0, 1.0), Point(1.0, 0.0, 0.0))
    try:
        capped_cylinder(1.0, 0.3, rotation=displaced)
    except TypeError as exc:
        assert "displaced origin" in str(exc)
    else:
        raise AssertionError("expected TypeError for a displaced GeneralRotor")