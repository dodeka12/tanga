# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for ``pytanga.viz.CameraCalibration``."""

from __future__ import annotations

import numpy as np
import pytest

from pytanga.geometry import CoordinateFrame, Direction, Matrix, OpenCVFrame
from pytanga.viz import CameraCalibration, PinholeCamera

_K = Matrix([[500.0, 0.0, 320.0], [0.0, 500.0, 240.0], [0.0, 0.0, 1.0]])
_STANDARD = CoordinateFrame(
    x=Direction(1.0, 0.0, 0.0),
    y=Direction(0.0, 1.0, 0.0),
    z=Direction(0.0, 0.0, 1.0),
)


def test_opencv_identity_camera_is_y_up():  # noqa: ANN201
    calib = CameraCalibration(_K, Matrix.identity(3), (0.0, 0.0, 0.0), image_size=(640, 480))
    cam = calib.to_pinhole_camera()
    assert isinstance(cam, PinholeCamera)
    assert np.allclose(cam.position, [0.0, 0.0, 0.0])
    assert np.allclose(cam.up, [0.0, 1.0, 0.0])  # y-up in the standard frame
    fwd = np.asarray(cam.target) - np.asarray(cam.position)
    assert np.allclose(fwd / np.linalg.norm(fwd), [0.0, 0.0, -1.0])


def test_standard_frame_identity_camera_is_opencv():  # noqa: ANN201
    calib = CameraCalibration(
        _K, Matrix.identity(3), (0.0, 0.0, 0.0), image_size=(640, 480), frame=_STANDARD
    )
    cam = calib.to_pinhole_camera()
    assert np.allclose(cam.up, [0.0, -1.0, 0.0])
    assert np.allclose(np.asarray(cam.target) - np.asarray(cam.position), [0.0, 0.0, 1.0])


def test_units_scale_translation():  # noqa: ANN201
    calib = CameraCalibration(
        _K, Matrix.identity(3), (0.0, 0.0, 1.0), image_size=(640, 480), units=0.001
    )
    cam = calib.to_pinhole_camera()
    assert np.allclose(cam.position, [0.0, 0.0, 0.001], atol=1e-12)


def test_world_to_camera():  # noqa: ANN201
    calib = CameraCalibration(_K, Matrix.identity(3), (0.0, 0.0, 0.0), image_size=(640, 480))
    e = calib.world_to_camera()
    assert e.shape == (4, 4)
    assert np.allclose(e.data[:3, :3], np.diag([1.0, -1.0, -1.0]))


def test_camera_to_world_is_inverse():  # noqa: ANN201
    calib = CameraCalibration(_K, Matrix.identity(3), (0.0, 0.0, 0.0), image_size=(640, 480))
    w2c = calib.world_to_camera()
    c2w = calib.camera_to_world()
    assert np.allclose((c2w @ w2c).data, np.eye(4), atol=1e-12)


def test_camera_center():  # noqa: ANN201
    calib = CameraCalibration(
        _K, Matrix.identity(3), (0.0, 0.0, 2.0), image_size=(640, 480), units=0.5
    )
    assert np.allclose(calib.camera_center(), [0.0, 0.0, 1.0], atol=1e-12)


def test_invalid_k_raises():  # noqa: ANN201
    with pytest.raises(ValueError):
        CameraCalibration(Matrix.identity(4), Matrix.identity(3), (0.0, 0.0, 0.0), image_size=(640, 480))


def test_invalid_image_size_raises():  # noqa: ANN201
    with pytest.raises(ValueError):
        CameraCalibration(_K, Matrix.identity(3), (0.0, 0.0, 0.0), image_size=(640,))  # type: ignore[arg-type]


def test_default_frame_is_opencv():  # noqa: ANN201
    assert isinstance(CameraCalibration(_K, Matrix.identity(3), (0, 0, 0), image_size=(640, 480)).frame, OpenCVFrame)
