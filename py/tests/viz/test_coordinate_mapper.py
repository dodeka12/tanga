# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the pixel↔world ``CoordinateMapper`` implementations."""

from __future__ import annotations

import numpy as np
import pytest

from pytanga.geometry import Matrix, OpenCVFrame, Point
from pytanga.viz import CalibratedPlaneMapper, CameraCalibration, PlanarMapper

_CX, _CY = 320.0, 240.0


def _calibration() -> CameraCalibration:
    """A camera at the world origin (identity pose), 500 px focal length."""
    return CameraCalibration(
        K=Matrix([[500.0, 0.0, _CX], [0.0, 500.0, _CY], [0.0, 0.0, 1.0]]),
        R=Matrix(np.eye(3)),
        t=[0.0, 0.0, 0.0],
        image_size=(640, 480),
        frame=OpenCVFrame(),
        units=1.0,
    )


def test_planar_mapper_is_identity() -> None:
    mapper = PlanarMapper()
    p = mapper.to_world(3.0, 4.0)
    assert (p.x, p.y, p.z) == (3.0, 4.0, 0.0)
    assert mapper.to_pixel(Point(7.0, 8.0, 9.0)) == (7.0, 8.0)


def test_calibrated_mapper_round_trip() -> None:
    mapper = CalibratedPlaneMapper(_calibration(), depth=1.0)
    for u in (0.0, _CX, 639.0):
        for v in (0.0, _CY, 479.0):
            u2, v2 = mapper.to_pixel(mapper.to_world(u, v))
            assert u2 == pytest.approx(u, abs=1e-6)
            assert v2 == pytest.approx(v, abs=1e-6)


def test_calibrated_mapper_principal_point_at_depth() -> None:
    calib = _calibration()
    mapper = CalibratedPlaneMapper(calib, depth=0.5)
    center = np.asarray(calib.camera_center())
    p = mapper.to_world(_CX, _CY)
    dist = float(np.linalg.norm(np.asarray([p.x, p.y, p.z]) - center))
    assert dist == pytest.approx(0.5)

