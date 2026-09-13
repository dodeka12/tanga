# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the `ImageCanvas` helper (`_image_view.py`)."""

from __future__ import annotations

import numpy as np
import pytest

from pytanga.geometry import Point
from pytanga.viz import ImageCanvas, ImageData, SceneView, Visualizer
from pytanga.viz._image_view import ImageView


def _viz() -> Visualizer:
    return Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)


class TestScene:
    def test_creates_dedicated_2d_scene(self) -> None:
        canvas = ImageCanvas(_viz())
        assert canvas.scene_name.startswith("imgc")
        scene = canvas.handle.scene
        assert scene.config.space_dim == 2

    def test_scene_view_references_scene(self) -> None:
        canvas = ImageCanvas(_viz())
        sv = canvas.scene_view()
        assert isinstance(sv, SceneView)
        assert sv.scene == canvas.scene_name


class TestCamera:
    def test_fit_to_image(self) -> None:
        canvas = ImageCanvas(_viz())
        canvas.set_image(ImageData("img1", data=np.zeros((10, 20), dtype=np.uint8)))
        cam = canvas.handle.scene.config.camera
        assert (cam.xmin, cam.xmax, cam.ymin, cam.ymax) == (-0.5, 19.5, -0.5, 9.5)
        assert cam.stretch == "fit"

    def test_fit_to_image_before_image_is_noop(self) -> None:
        canvas = ImageCanvas(_viz())
        canvas.fit_to_image()
        assert canvas.handle.scene.config.camera is None


class TestApi:
    def test_image_view_and_uniform_forwarding(self) -> None:
        canvas = ImageCanvas(_viz())
        assert isinstance(canvas.image_view, ImageView)
        canvas.set_uniform("u_brightness", 0.5)
        canvas.register_uniform("u_foo", 1)
        assert canvas.image_view.uniforms["u_brightness"] == 0.5
        assert canvas.image_view.uniforms["u_foo"] == 1

    def test_register_shader(self) -> None:
        canvas = ImageCanvas(_viz())
        canvas.set_image(ImageData("img1", data=np.zeros((4, 4), dtype=np.uint8)))
        canvas.register_shader("void main() {}", "vertex")
        shader = canvas.image_view._serialize()["shader"]
        assert shader["fragment"] == "void main() {}"
        assert shader["vertex"] == "vertex"

    def test_act_plane(self) -> None:
        canvas = ImageCanvas(_viz())
        from pytanga.viz import ActImagePlane

        assert isinstance(canvas.act_plane, ActImagePlane)
        assert canvas.act_plane.image_view is canvas.image_view


class TestOverlay:
    def test_add_returns_ref_and_clear_removes(self) -> None:
        canvas = ImageCanvas(_viz())
        ref = canvas.add(Point(1.0, 2.0, 0.0))
        assert ref is not None
        assert len(canvas._overlay_refs) == 1
        canvas.clear()
        assert canvas._overlay_refs == []

    def test_remove_ref(self) -> None:
        canvas = ImageCanvas(_viz())
        ref = canvas.add(Point(1.0, 2.0, 0.0))
        canvas.remove(ref)
        assert canvas._overlay_refs == []
