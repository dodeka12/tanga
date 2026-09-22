# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for ``Frustum`` serialization + scene resolution."""

from pytanga.entity import Direction, Point
from pytanga.geometry import Frustum
from pytanga.viz.scene import _resolve_scene_entity
from pytanga.viz.serializer import serialize_entity


def _frustum(near=0.5, far=2.0, hw=1.0, hh=1.0):  # noqa: ANN001, ANN202
    return Frustum(
        Point(1.0, 2.0, 3.0),
        Direction(0.0, 0.0, 1.0),
        Direction(1.0, 0.0, 0.0),
        near,
        far,
        hw,
        hh,
    )


def test_frustum_serialize_shape_only():  # noqa: ANN201
    f = _frustum(near=0.5, far=2.0, hw=1.0, hh=0.75)
    out = serialize_entity(f, "f0", kind="Frustum")
    assert out["kind"] == "Frustum"
    assert out["near"] == 0.5
    assert out["far"] == 2.0
    assert out["halfWidth"] == 1.0
    assert out["halfHeight"] == 0.75
    # Placement rides on the transform; content is shape-only.
    assert "apex" not in out
    assert out["transform"]["position"] == [1.0, 2.0, 3.0]
    assert len(out["transform"]["rotation"]) == 4


def test_frustum_serialize_apex():  # noqa: ANN201
    f = _frustum(near=0.0)
    out = serialize_entity(f, "f0", kind="Frustum")
    assert out["near"] == 0.0


def test_frustum_resolves_as_scene_entity():  # noqa: ANN201
    f = _frustum()
    assert _resolve_scene_entity(f) is f
