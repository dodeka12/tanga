# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the pinhole camera model (`camera.py`)."""

import numpy as np
import pytest

from pytanga.viz.camera import (
    CameraLock,
    PinholeCamera,
    pinhole_camera,
)


def _identity_calibration():  # noqa: ANN202
    K = np.diag([500.0, 500.0, 1.0])
    K[0, 2] = 320.0
    K[1, 2] = 240.0
    return K, np.eye(3), np.array([0.0, 0.0, -5.0])


def test_pinhole_camera_fields():  # noqa: ANN201
    K, R, t = _identity_calibration()
    cam = pinhole_camera(K, R, t, image_size=(640, 480))
    assert cam.type == "pinhole"
    assert cam.fx == 500.0
    assert cam.fy == 500.0
    assert cam.cx == 320.0
    assert cam.cy == 240.0
    assert cam.width == 640
    assert cam.height == 480
    assert cam.fit == "fit"


def test_pinhole_camera_pose():  # noqa: ANN201
    K, R, t = _identity_calibration()
    cam = pinhole_camera(K, R, t, image_size=(640, 480))
    assert cam.position == pytest.approx((0.0, 0.0, 5.0))
    assert cam.target == pytest.approx((0.0, 0.0, 6.0))
    assert cam.up == pytest.approx((0.0, -1.0, 0.0))


def test_pinhole_camera_to_dict():  # noqa: ANN201
    K, R, t = _identity_calibration()
    cam = pinhole_camera(K, R, t, image_size=(640, 480))
    d = cam.to_dict()
    assert d["type"] == "pinhole"
    assert d["fx"] == 500.0
    assert d["fy"] == 500.0
    assert d["cx"] == 320.0
    assert d["cy"] == 240.0
    assert d["width"] == 640
    assert d["height"] == 480
    assert d["fit"] == "fit"


def test_pinhole_camera_rejects_bad_shapes():  # noqa: ANN201
    K, R, t = _identity_calibration()
    with pytest.raises(ValueError):
        pinhole_camera(K[:2, :], R, t, image_size=(640, 480))
    with pytest.raises(ValueError):
        pinhole_camera(K, R[:2, :], t, image_size=(640, 480))
    with pytest.raises(ValueError):
        pinhole_camera(K, R, t[:2], image_size=(640, 480))


def test_pinhole_camera_rejects_bad_fit():  # noqa: ANN201
    K, R, t = _identity_calibration()
    with pytest.raises(ValueError):
        pinhole_camera(K, R, t, image_size=(640, 480), fit="bogus")


def test_camera_lock_values():  # noqa: ANN201
    assert {v.value for v in CameraLock} == {"rotate", "pan", "zoom"}
    assert CameraLock("rotate") is CameraLock.ROTATE
    with pytest.raises(ValueError):
        CameraLock("nope")


def test_pinhole_camera_is_camera_config():  # noqa: ANN201
    from pytanga.viz.camera import CameraConfig

    K, R, t = _identity_calibration()
    assert isinstance(pinhole_camera(K, R, t, image_size=(640, 480)), CameraConfig)
    assert isinstance(PinholeCamera(fx=1, fy=1, cx=0, cy=0, width=10, height=10), CameraConfig)
