# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for ``pytanga.geometry.CoordinateFrame`` and ``OpenCVFrame``."""

from __future__ import annotations

import numpy as np

from pytanga.geometry import (
    CoordinateFrame,
    Direction,
    Matrix,
    MatrixProvider,
    OpenCVFrame,
    Point,
)


def test_opencv_frame_to_matrix():  # noqa: ANN201
    m = OpenCVFrame().to_matrix()
    assert m.shape == (4, 4)
    assert np.allclose(m, np.diag([1.0, -1.0, -1.0, 1.0]))


def test_opencv_frame_is_right_handed():  # noqa: ANN201
    assert OpenCVFrame().handedness() == 1


def test_opencv_frame_is_rotation():  # noqa: ANN201
    m = Matrix(OpenCVFrame().to_matrix())
    assert m.is_rotation()


def test_opencv_frame_maps_axes():  # noqa: ANN201
    m = Matrix(OpenCVFrame().to_matrix())
    # OpenCV +y (down) maps to standard -y (up).
    p = m @ Point(0.0, 1.0, 0.0)
    assert np.allclose([p.x, p.y, p.z], [0.0, -1.0, 0.0], atol=1e-9)


def test_opencv_frame_is_matrix_provider():  # noqa: ANN201
    assert isinstance(OpenCVFrame(), MatrixProvider)


def test_standard_frame_is_identity():  # noqa: ANN201
    f = CoordinateFrame(
        x=Direction(1.0, 0.0, 0.0),
        y=Direction(0.0, 1.0, 0.0),
        z=Direction(0.0, 0.0, 1.0),
    )
    assert np.allclose(f.to_matrix(), np.eye(4))
    assert f.handedness() == 1


def test_opencv_frame_set_transform():  # noqa: ANN201
    from pytanga.viz._nodes import VizSceneObject

    node = VizSceneObject("a", Point(0.0, 0.0, 0.0), None, kind="Point")
    node.set_transform(OpenCVFrame())
    assert np.allclose(
        node.transform.matrix(), np.diag([1.0, -1.0, -1.0, 1.0]), atol=1e-9
    )
