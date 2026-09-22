# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the visualization-only ``Frustum`` entity."""

import numpy as np
import pytest

from pytanga.entity import Direction, Point
from pytanga.geometry import Frustum


def _frustum(near=0.5, far=2.0, hw=1.0, hh=1.0):  # noqa: ANN001, ANN202
    return Frustum(
        Point(0.0, 0.0, 0.0),
        Direction(0.0, 0.0, 1.0),
        Direction(1.0, 0.0, 0.0),
        near,
        far,
        hw,
        hh,
    )


def test_frustum_apex_detection():  # noqa: ANN201
    f = _frustum(near=0.0)
    assert f.apex is True


def test_frustum_two_rectangles_not_apex():  # noqa: ANN201
    f = _frustum(near=0.5)
    assert f.apex is False


def test_frustum_rejects_bad_origin():  # noqa: ANN201
    with pytest.raises(TypeError):
        Frustum(1.0, Direction(0, 0, 1), Direction(1, 0, 0), 0.0, 2.0, 1.0, 1.0)


def test_frustum_from_camera_axis_aligned():  # noqa: ANN201
    K = np.diag([500.0, 500.0, 1.0])
    K[0, 2] = 320.0
    K[1, 2] = 240.0
    from pytanga.viz.camera import pinhole_camera

    cam = pinhole_camera(K, np.eye(3), np.array([0.0, 0.0, -5.0]), image_size=(640, 480))
    f = Frustum.from_camera(cam, near=0.5, far=2.0)
    assert f.apex is False
    # Camera at z=5 looks toward +z.
    assert f.origin == Point(0.0, 0.0, 5.0)
    assert (f.axis.x, f.axis.y, f.axis.z) == pytest.approx((0.0, 0.0, 1.0))
    assert f.near == pytest.approx(0.5)
    assert f.far == pytest.approx(2.0)
    # Half-height at far = far * (H/2) / fy = 2.0 * 240 / 500 = 0.96.
    assert f.far_half_height == pytest.approx(0.96)
    # Half-width at far = far * (W/2) / fx = 2.0 * 320 / 500 = 1.28.
    assert f.far_half_width == pytest.approx(1.28)


def test_frustum_from_camera_apex_when_near_nonpositive():  # noqa: ANN201
    from pytanga.viz.camera import pinhole_camera

    K = np.diag([500.0, 500.0, 1.0])
    K[0, 2] = 320.0
    K[1, 2] = 240.0
    cam = pinhole_camera(K, np.eye(3), np.array([0.0, 0.0, -5.0]), image_size=(640, 480))
    f = Frustum.from_camera(cam, near=0.0, far=2.0)
    assert f.apex is True
