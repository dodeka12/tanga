# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for HTML export honoring the scene camera and per-frame camera playback."""

from pytanga.viz.camera import CameraConfig2d, CameraConfig3d
from pytanga.viz.export._animated_figure import (
    render_export_animated_figure,
    render_export_animated_html,
)
from pytanga.viz.export._animation_recording import AnimationRecording
from pytanga.viz.export._figure_html import render_figure
from pytanga.viz.export._html import render_snapshot
from pytanga.viz.scene import Scene, SceneConfig


def test_snapshot_honors_2d_camera_rectangle():
    scene = Scene(
        SceneConfig(camera=CameraConfig2d(xmin=-20, xmax=20, ymin=-5, ymax=5))
    )
    html = render_snapshot(scene.full_state(), scene.config.to_dict())
    assert "applyCameraConfig(" in html
    assert "xmin" in html
    assert "-20" in html
    assert "-5" in html


def test_figure_honors_3d_camera_up():
    scene = Scene(SceneConfig(camera=CameraConfig3d(position=(3, 4, 5), up=(0, 1, 0))))
    html = render_figure(
        scene.full_state(),
        scene.config.to_dict(),
        {"width": 400, "height": 300},
        {"title": "T"},
    )
    assert "applyCameraConfig(" in html
    assert '"up"' in html


def test_animated_figure_uses_scene_config():
    scene = Scene(
        SceneConfig(
            space_dim=2, camera=CameraConfig2d(xmin=-30, xmax=30, ymin=-10, ymax=10)
        )
    )
    rec = AnimationRecording(scene)
    rec.capture_frame()
    html = render_export_animated_figure(
        rec.to_dict(),
        figure_style={"width": 400, "height": 300},
        figure_config={"title": "T"},
        scene_config=scene.config.to_dict(),
    )
    assert "applyCameraConfig(" in html
    assert "space_dim" in html
    assert "-30" in html


def test_animated_html_plays_per_frame_camera():
    rec = {"frames": [], "frame_count": 0, "cameras": []}
    html = render_export_animated_html(rec, scene_config={"space_dim": 2})
    assert "const cameras = animData.cameras || [];" in html
    assert "applyCameraConfig(figCamera, figControls, cameras[n]" in html


def test_animation_recording_captures_cameras():
    scene = Scene()
    rec = AnimationRecording(scene)
    rec.capture_frame()
    scene.config.camera = CameraConfig3d(position=(2, 3, 5), target=(0, 0, 0))
    rec.capture_frame()

    data = rec.to_dict()
    assert data["frame_count"] == 2
    assert data["cameras"][0] is None
    cam = data["cameras"][1]
    assert cam["type"] == "3d"
    assert cam["position"] == [2, 3, 5]
    assert cam["target"] == [0, 0, 0]
