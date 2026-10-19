# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the `DepthImage` pinhole camera mode (`depth_image.py`)."""

from __future__ import annotations

import numpy as np
import pytest

from pytanga.geometry import Matrix, OpenCVFrame
from pytanga.viz import (
    CameraCalibration,
    DepthImage,
    DepthImageData,
    DepthImageStyle,
    PinholeCamera,
)
from pytanga.viz._styles import _style_to_output
from pytanga.viz.depth_image import camera_transform, compute_pinhole_positions


def _build(style: DepthImageStyle) -> dict:
    depth = DepthImage(DepthImageData(depth=np.full((4, 6), 1.0, dtype=np.float32)))
    content, _ = depth._build(_style_to_output(style, "DepthImage"), "d0")
    return content


def _calib() -> CameraCalibration:
    return CameraCalibration(
        K=Matrix([[100.0, 0.0, 50.0], [0.0, 100.0, 40.0], [0.0, 0.0, 1.0]]),
        R=Matrix.identity(3),
        t=(0.0, 0.0, 2.0),
        image_size=(100, 80),
        frame=OpenCVFrame(),
        units=1.0,
    )


def test_serialize_intrinsics_and_depth_kind() -> None:
    content = _build(
        DepthImageStyle(camera=_calib(), depth_kind="axial")
    )
    cam = content["mesh"]["camera"]
    assert cam["fx"] == pytest.approx(100.0)
    assert cam["fy"] == pytest.approx(100.0)
    assert cam["cx"] == pytest.approx(50.0)
    assert cam["cy"] == pytest.approx(40.0)
    assert cam["depth_kind"] == "axial"


def test_serialize_depth_kind_aliases() -> None:
    assert _build(DepthImageStyle(camera=_calib(), depth_kind="z"))["mesh"]["camera"]["depth_kind"] == "axial"
    assert _build(DepthImageStyle(camera=_calib(), depth_kind="range"))["mesh"]["camera"]["depth_kind"] == "radial"
    assert _build(DepthImageStyle(camera=_calib(), depth_kind="disparity"))["mesh"]["camera"]["depth_kind"] == "inverse"


def test_camera_transform_from_calibration() -> None:
    tr = camera_transform(_calib())
    assert tr is not None
    assert np.allclose(tr.matrix(), _calib().camera_to_world().data)

    assert camera_transform(_calib(), apply_pose=False) is None
    assert camera_transform(None) is None


def test_serialize_pinhole_camera_has_no_pose() -> None:
    cam = PinholeCamera(fx=100.0, fy=100.0, cx=50.0, cy=40.0, width=100, height=80)
    content = _build(DepthImageStyle(camera=cam, depth_kind="radial"))
    assert "camera_to_world" not in content["mesh"]
    assert content["mesh"]["camera"]["depth_kind"] == "radial"
    # A bare PinholeCamera carries no pose, so no entity transform is produced.
    assert camera_transform(cam) is None


def test_pinhole_plane_z2_positions() -> None:
    depth = np.full((3, 4), 2.0, dtype=np.float32)
    pos, u, v = compute_pinhole_positions(depth, fx=100.0, fy=100.0, cx=2.0, cy=1.0)
    assert pos.shape == (12, 3)
    assert np.allclose(pos[:, 2], 2.0)
    assert np.allclose(pos[:, 0], (u - 2.0) / 100.0 * 2.0)
    assert np.allclose(pos[:, 1], (v - 1.0) / 100.0 * 2.0)


def test_pinhole_range_conversion() -> None:
    depth = np.full((2, 2), 3.0, dtype=np.float32)
    pos, u, v = compute_pinhole_positions(depth, fx=1.0, fy=1.0, cx=0.0, cy=0.0, depth_kind="radial")
    for i in range(pos.shape[0]):
        x = u[i]
        y = v[i]
        z = 3.0 / np.sqrt(x * x + y * y + 1.0)
        assert pos[i, 0] == pytest.approx(x * z)
        assert pos[i, 1] == pytest.approx(y * z)
        assert pos[i, 2] == pytest.approx(z)


def test_pinhole_inverse_conversion() -> None:
    # Raw inverse depth d = 1/Z; a constant d = 0.5 means Z = 2.
    depth = np.full((2, 2), 0.5, dtype=np.float32)
    pos, u, v = compute_pinhole_positions(depth, fx=1.0, fy=1.0, cx=0.0, cy=0.0, depth_kind="inverse")
    for i in range(pos.shape[0]):
        z = 2.0
        assert pos[i, 0] == pytest.approx(u[i] * z)
        assert pos[i, 1] == pytest.approx(v[i] * z)
        assert pos[i, 2] == pytest.approx(z)


def test_pose_places_surface_relative_to_camera() -> None:
    # Camera at the origin (R=I, t=0, OpenCV frame): optical axis is world -z.
    calib = CameraCalibration(
        K=Matrix([[100.0, 0.0, 50.0], [0.0, 100.0, 40.0], [0.0, 0.0, 1.0]]),
        R=Matrix.identity(3),
        t=(0.0, 0.0, 0.0),
        image_size=(100, 80),
        frame=OpenCVFrame(),
        units=1.0,
    )
    # A camera-frame point at axial depth Z=2 lands at world (0, 0, -2).
    world = calib.camera_to_world().data @ np.array([0.0, 0.0, 2.0, 1.0])
    assert np.allclose(world[:3], [0.0, 0.0, -2.0])


def test_pose_places_surface_for_arbitrary_extrinsics() -> None:
    # A 90° rotation about z plus a translation: the surface follows the pose.
    calib = CameraCalibration(
        K=Matrix([[100.0, 0.0, 50.0], [0.0, 100.0, 40.0], [0.0, 0.0, 1.0]]),
        R=Matrix([[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]]),
        t=(1.0, 2.0, 3.0),
        image_size=(100, 80),
        frame=OpenCVFrame(),
        units=1.0,
    )
    c2w = calib.camera_to_world().data
    center = np.asarray(calib.camera_center())
    forward = c2w[:3, :3] @ np.array([0.0, 0.0, 1.0])
    # A camera-frame point at axial depth Z=2 sits 2 m along the optical axis.
    world = c2w @ np.array([0.0, 0.0, 2.0, 1.0])
    assert np.allclose(world[:3], center + 2.0 * forward)


def test_camera_transform_matches_calibration_for_arbitrary_extrinsics() -> None:
    calib = CameraCalibration(
        K=Matrix([[100.0, 0.0, 50.0], [0.0, 100.0, 40.0], [0.0, 0.0, 1.0]]),
        R=Matrix([[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]]),
        t=(1.0, 2.0, 3.0),
        image_size=(100, 80),
        frame=OpenCVFrame(),
        units=1.0,
    )
    tr = camera_transform(calib)
    assert tr is not None
    assert np.allclose(tr.matrix(), calib.camera_to_world().data)


def test_scene_node_gets_camera_transform() -> None:
    from pytanga.viz import Visualizer

    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    world = viz.scene("world")
    world.new(
        DepthImage(DepthImageData(depth=np.full((4, 6), 2.0, dtype=np.float32))),
        entity_id="d0",
        style=DepthImageStyle(camera=_calib(), depth_kind="axial"),
    )
    node = viz._layout.scenes["world"].get_node("d0")
    assert np.allclose(node.transform.matrix(), _calib().camera_to_world().data)


def test_scene_node_identity_transform_without_pose() -> None:
    from pytanga.viz import Visualizer

    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    world = viz.scene("world")
    cam = PinholeCamera(fx=100.0, fy=100.0, cx=50.0, cy=40.0, width=100, height=80)
    world.new(
        DepthImage(DepthImageData(depth=np.full((4, 6), 2.0, dtype=np.float32))),
        entity_id="d0",
        style=DepthImageStyle(camera=cam, depth_kind="axial"),
    )
    node = viz._layout.scenes["world"].get_node("d0")
    assert node.transform.to_dict() == {
        "position": [0.0, 0.0, 0.0],
        "rotation": [0.0, 0.0, 0.0, 1.0],
        "scale": [1.0, 1.0, 1.0],
    }


def test_depth_kind_validation() -> None:
    with pytest.raises(ValueError, match="depth_kind"):
        DepthImageStyle(depth_kind="bogus")
    with pytest.raises(ValueError, match="depth_kind"):
        compute_pinhole_positions(
            np.zeros((2, 2), np.float32), 1.0, 1.0, 0.0, 0.0, depth_kind="bogus"
        )
