# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the calibrated background-image surface (`CalibratedSurface`)."""

from __future__ import annotations

import json
from pathlib import Path

from pytanga.geometry import Matrix, OpenCVFrame
from pytanga.viz import (
    CalibratedPlaneMapper,
    CalibratedSurface,
    CameraCalibration,
    CameraView,
    InteractionSurface,
    SceneView,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DATA_DIR = _REPO_ROOT / "py" / "examples" / "viz" / "camera" / "data" / "tless"


def _calibration() -> CameraCalibration:
    data = json.loads((_DATA_DIR / "calibration.json").read_text(encoding="utf-8"))
    return CameraCalibration(
        K=Matrix(data["K"]),
        R=Matrix(data["R_w2c"]),
        t=data["t_w2c"],
        image_size=(int(data["width"]), int(data["height"])),
        frame=OpenCVFrame(),
        units=0.001,
    )


class TestCalibratedSurface:
    def test_surface_uses_calibrated_mapper(self) -> None:
        surface = CalibratedSurface(_calibration(), depth=0.6)
        assert isinstance(surface, InteractionSurface)
        assert isinstance(surface.mapper, CalibratedPlaneMapper)

    def test_serialize_matches_mapper_plane(self) -> None:
        surface = CalibratedSurface(_calibration(), depth=0.6)
        point, normal = surface.mapper.plane()
        data = surface.serialize()
        assert data["point"] == [point.x, point.y, point.z]
        assert data["normal"] == [normal.x, normal.y, normal.z]


class TestBackgroundPane:
    def test_scene_view_serializes_surface_and_read_only(self) -> None:
        surface = CalibratedSurface(_calibration(), depth=0.6)
        view = SceneView("world", surface=surface, read_only=True)
        data = view._serialize()
        assert data["surface"]["id"] == surface.id
        assert data["read_only"] is True

    def test_scene_view_serializes_surface_with_camera_view(self) -> None:
        calib = _calibration()
        surface = CalibratedSurface(calib, depth=0.6)
        view = SceneView(
            "world",
            camera_view=CameraView(calib.to_pinhole_camera(), navigation="2d"),
            surface=surface,
        )
        data = view._serialize()
        assert data["surface"]["id"] == surface.id
        assert data["camera_view"]["navigation"] == "2d"

    def test_read_only_world_pane_omits_surface(self) -> None:
        data = SceneView("world", read_only=True)._serialize()
        assert data["read_only"] is True
        assert "surface" not in data
