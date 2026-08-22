# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the SDF primitive/combinator descriptor model (Phase 4)."""

from __future__ import annotations

from pytanga.viz.sdf.primitives import bound_box, combine, primitive


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