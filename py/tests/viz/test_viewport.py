# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the viewport/navigation model (`camera.py`, `views.py`)."""

import pytest

from pytanga.viz._interaction import MouseButton
from pytanga.viz.camera import CameraAction, Navigation, ViewportConfig
from pytanga.viz.scene import SceneConfig
from pytanga.viz.views import CameraView, SceneView


def test_viewport_defaults() -> None:
    v = ViewportConfig()
    assert v.zoom == 1.0
    assert v.pan == (0.0, 0.0)
    assert v.to_dict() == {"zoom": 1.0, "pan": [0.0, 0.0]}


def test_viewport_to_dict_with_limits() -> None:
    v = ViewportConfig(
        zoom=2.0,
        pan=(0.1, -0.2),
        min_zoom=1.0,
        max_zoom=8.0,
        pan_xlim=(-0.5, 0.5),
        pan_ylim=(-0.25, 0.25),
    )
    assert v.to_dict() == {
        "zoom": 2.0,
        "pan": [0.1, -0.2],
        "min_zoom": 1.0,
        "max_zoom": 8.0,
        "pan_xlim": [-0.5, 0.5],
        "pan_ylim": [-0.25, 0.25],
    }


def test_viewport_rejects_non_positive_zoom() -> None:
    with pytest.raises(ValueError, match="zoom"):
        ViewportConfig(zoom=0.0)


def test_viewport_rejects_bad_pan() -> None:
    with pytest.raises(ValueError, match="pan"):
        ViewportConfig(pan=(1.0,))


def test_viewport_rejects_inverted_limits() -> None:
    with pytest.raises(ValueError, match="pan_xlim"):
        ViewportConfig(pan_xlim=(0.5, -0.5))


def test_viewport_rejects_min_gt_max_zoom() -> None:
    with pytest.raises(ValueError, match="min_zoom"):
        ViewportConfig(min_zoom=8.0, max_zoom=1.0)


def test_camera_view_default_omits_fields() -> None:
    assert CameraView().to_dict() == {}


def test_camera_view_serializes_new_fields() -> None:
    cv = CameraView(
        navigation="2d",
        controls={MouseButton.LEFT: CameraAction.PAN, MouseButton.MIDDLE: None},
        viewport=ViewportConfig(zoom=2.0, pan=(0.1, 0.0)),
    )
    assert cv.to_dict() == {
        "navigation": "2d",
        "controls": {"left": "pan", "middle": None},
        "viewport": {"zoom": 2.0, "pan": [0.1, 0.0]},
    }


def test_camera_view_accepts_navigation_enum() -> None:
    assert CameraView(navigation=Navigation.VIEW2D).to_dict() == {"navigation": "2d"}


def test_camera_view_rejects_bad_navigation() -> None:
    with pytest.raises(ValueError, match="navigation"):
        CameraView(navigation="bogus")


def test_scene_view_forwards_viewport() -> None:
    sv = SceneView("world", navigation="2d", viewport=ViewportConfig(zoom=2.0))
    assert sv.camera_view is not None
    assert sv.camera_view.to_dict() == {
        "navigation": "2d",
        "viewport": {"zoom": 2.0, "pan": [0.0, 0.0]},
    }


def test_scene_view_default_has_no_camera_view() -> None:
    assert SceneView("world").camera_view is None


def test_scene_config_emits_viewport() -> None:
    d = SceneConfig(viewport=ViewportConfig(zoom=2.0, pan=(0.1, 0.0))).to_dict()
    assert d["viewport"] == {"zoom": 2.0, "pan": [0.1, 0.0]}


def test_scene_config_omits_viewport_when_none() -> None:
    assert "viewport" not in SceneConfig().to_dict()
