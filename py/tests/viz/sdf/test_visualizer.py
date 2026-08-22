# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the SDF viewer facade (Phase 6)."""

from __future__ import annotations

from pytanga.geometry.entities import Point, Sphere
from pytanga.viz.sdf.distance import DistanceFunction
from pytanga.viz.sdf.visualizer import SdfVisualizer


def test_add_serializes_sdf_object() -> None:
    viz = SdfVisualizer(open_browser=False)
    oid = viz.add(Sphere(Point(0, 0, 0), 1.0), color="#ff0000")
    assert isinstance(oid, str)
    full_state, _ = viz._full_state_for("")
    assert len(full_state) == 1
    obj = full_state[0]
    assert obj["kind"] == "sdf"
    assert obj["sdfKind"] == "Sphere"
    assert obj["tree"]["kind"] == "sphere"
    assert obj["color"] == "#ff0000"


def test_distance_setter_emits_config_value() -> None:
    viz = SdfVisualizer(open_browser=False)
    assert viz.distance == "scalar_pseudo"
    viz.distance = DistanceFunction.MAGNITUDE
    assert viz.distance == "magnitude"
    viz.opacity = "sigmoid"
    assert viz.opacity == "sigmoid"


def test_camera_config_parity() -> None:
    from pytanga.viz.camera import CameraConfig3d

    cam = CameraConfig3d(position=(10, 6, 12), target=(0, 0, 0), fov=50)

    from pytanga.viz.visualizer import Visualizer

    std_viz = Visualizer(camera=cam, add_default_axes=False, add_default_grid=False)
    sdf_viz = SdfVisualizer(camera=cam, open_browser=False)

    std_cfg = std_viz._scene_config_for("")
    sdf_cfg = sdf_viz._scene_config_for("")

    # The camera dicts must match exactly (camera parity).
    assert std_cfg["camera"] == sdf_cfg["camera"]


def test_default_camera_is_none() -> None:
    viz = SdfVisualizer(open_browser=False)
    cfg = viz._scene_config_for("")
    assert "camera" not in cfg  # none specified → auto-fit on the frontend
    assert cfg["space_dim"] == 3