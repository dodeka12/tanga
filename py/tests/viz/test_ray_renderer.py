# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the ray-renderer serializer branch and capability checks."""

import pytest

from pytanga.geometry import Point, Quadric3D, Sphere
from pytanga.viz import RayStyle
from pytanga.viz.serializer import serialize_entity


class TestRaySerializer:
    def test_ray_styled_unsupported_kind_raises(self):
        s = Sphere(Point(0.0, 0.0, 0.0), 1.0)
        with pytest.raises(ValueError, match="does not support analytic ray"):
            serialize_entity(s, "s1", properties={"style": RayStyle()}, kind="Sphere")

    def test_ray_styled_quadric_serializes(self):
        q = Quadric3D(tuple(float(i) for i in range(1, 11)))
        d = serialize_entity(
            q, "q1", properties={"style": RayStyle()}, kind="Quadric3D"
        )
        assert d["kind"] == "ray"
        assert d["rayKind"] == "Quadric3D"
