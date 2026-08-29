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

    def test_ray_styled_quadric_not_yet_serialized(self):
        q = Quadric3D(tuple(float(i) for i in range(1, 11)))
        # Quadric3D is ray-capable, but its wire body lands in Phase 7.
        with pytest.raises(NotImplementedError):
            serialize_entity(
                q, "q1", properties={"style": RayStyle()}, kind="Quadric3D"
            )
