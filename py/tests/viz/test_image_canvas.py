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

    def test_controls_config_set_on_scene(self) -> None:
        from pytanga.viz import CameraAction, MouseButton

        canvas = ImageCanvas(_viz(), controls={MouseButton.RIGHT: CameraAction.PAN})
        assert canvas.handle.scene.config.controls == {
            MouseButton.RIGHT: CameraAction.PAN
        }


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


class TestHandlers:
    def test_drag_handlers_forwarded_to_plane(self) -> None:
        from pytanga.viz import DragBinding, DragEvent, ModifierKey, MouseButton

        async def on_drag(event: DragEvent, canvas: ImageCanvas) -> bool:
            return True

        canvas = ImageCanvas(
            _viz(),
            drag_handlers=[DragBinding(MouseButton.RIGHT, on_drag, ModifierKey.CTRL)],
        )
        bindings = canvas.act_plane._drag_bindings
        assert len(bindings) == 1
        assert bindings[0].button is MouseButton.RIGHT
        assert bindings[0].modifiers == frozenset({ModifierKey.CTRL})

    def test_click_handlers_forwarded_to_plane(self) -> None:
        from pytanga.viz import ClickBinding, ClickEvent, MouseButton

        async def on_click(event: ClickEvent, canvas: ImageCanvas) -> None:
            pass

        canvas = ImageCanvas(
            _viz(),
            click_handlers=[ClickBinding(MouseButton.LEFT, on_click)],
        )
        bindings = canvas.act_plane._click_bindings
        assert len(bindings) == 1
        assert bindings[0].button is MouseButton.LEFT
        assert bindings[0].modifiers == frozenset()


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

    def test_set_image_resets_value_range(self) -> None:
        canvas = ImageCanvas(_viz())
        canvas.set_image(ImageData("img1", data=np.zeros((4, 4, 3), dtype=np.uint8)))
        assert canvas.image_view.uniforms["u_value_max"] == 1.0
        assert canvas.image_view.uniforms["u_mode"] == 1  # RGB

        # Replacing with a different dtype re-derives the normalization range.
        canvas.set_image(ImageData("img2", data=np.zeros((4, 4), dtype=np.uint16)))
        assert canvas.image_view.uniforms["u_value_max"] == 65535
        assert canvas.image_view.uniforms["u_mode"] == 0  # gray

    def test_set_image_auto_registers_tiled_pyramid(self) -> None:
        viz = _viz()
        canvas = ImageCanvas(viz)
        image = ImageData("img1", data=np.zeros((5000, 100, 3), dtype=np.uint8))
        assert image.source == "tiled"
        canvas.set_image(image)
        assert "img1" in viz._image_pyramids
        assert viz._image_pyramids["img1"] is image.tiled

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
