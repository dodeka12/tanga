# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the low-level `ImageView` (`_image_view.py`)."""

from __future__ import annotations

import numpy as np
import pytest

from pytanga.viz import ImageData, ImageDType, ImageView
from pytanga.viz._image_view import MAX_IMAGE_LAYERS


def _img(image_id: str, channels: int = 1, dtype: str = "uint8") -> ImageData:
    shape = (3, 4) if channels == 1 else (3, 4, channels)
    return ImageData(image_id, data=np.zeros(shape, dtype=dtype))


class TestLayers:
    def test_set_image_defines_frame(self) -> None:
        view = ImageView("img1")
        view.set_image(_img("img1"))
        assert view.frame == (4, 3)
        assert len(view.images) == 1

    def test_set_image_replaces_layer0(self) -> None:
        view = ImageView("img1")
        view.set_image(_img("img1"))
        view.add_image(_img("img2", channels=3))
        view.set_image(_img("img3", channels=4))
        assert [i.id for i in view.images] == ["img3", "img2"]

    def test_layer_cap(self) -> None:
        view = ImageView("img1")
        for i in range(MAX_IMAGE_LAYERS):
            view.add_image(_img(f"img{i}"))
        with pytest.raises(ValueError, match="at most 4"):
            view.add_image(_img("overflow"))


class TestUniforms:
    def test_standard_defaults_seeded(self) -> None:
        view = ImageView("img1")
        assert view.uniforms["u_brightness"] == 0.0
        assert view.uniforms["u_contrast"] == 1.0
        assert view.uniforms["u_midpoint"] == 0.5

    def test_set_and_register(self) -> None:
        view = ImageView("img1")
        view.set_uniform("u_foo", 1.5)
        view.register_uniform("u_foo", 0.0)  # keeps existing
        view.register_uniform("u_bar", 2)
        assert view.uniforms["u_foo"] == 1.5
        assert view.uniforms["u_bar"] == 2

    def test_channel_mode_defaults(self) -> None:
        gray = ImageView("g")
        gray.set_image(_img("g", channels=1))
        assert gray.uniforms["u_mode"] == 0

        rgb = ImageView("rgb")
        rgb.set_image(_img("rgb", channels=3))
        assert rgb.uniforms["u_mode"] == 1

    def test_value_range_defaults_by_dtype(self) -> None:
        u16 = ImageView("u16")
        u16.set_image(_img("u16", dtype="uint16"))
        assert u16.uniforms["u_value_max"] == 65535.0

        f32 = ImageView("f32")
        f32.set_image(_img("f32", dtype="float32"))
        assert f32.uniforms["u_value_min"] == 0.0
        assert f32.uniforms["u_value_max"] == 1.0


class TestSerialize:
    def test_serialize_shape(self) -> None:
        view = ImageView("img1")
        view.set_image(_img("img1", channels=3))
        result = view._serialize()

        assert result["id"] == "img1"
        assert result["layer"] == "scene"
        assert result["kind"] == "image"
        assert result["frame"] == {"width": 4, "height": 3}
        assert result["shader"] == {"fragment": None, "vertex": None}
        assert result["images"][0] == {
            "id": "img1",
            "width": 4,
            "height": 3,
            "channels": 3,
            "dtype": 0,
            "source": "data",
        }
        assert result["uniforms"]["u_mode"] == 1
        assert result["uniforms"]["u_brightness"] == 0.0

    def test_serialize_url_image(self) -> None:
        view = ImageView("u")
        view.set_image(
            ImageData("u", url="http://x", width=4, height=3, channels=3,
                      dtype=ImageDType.UINT8)
        )
        img = view._serialize()["images"][0]
        assert img["source"] == "url"
        assert img["url"] == "http://x"

    def test_serialize_custom_shader(self) -> None:
        view = ImageView("img1")
        view.set_image(_img("img1"))
        view.register_shader("void main() {}", "vertex")
        shader = view._serialize()["shader"]
        assert shader["fragment"] == "void main() {}"
        assert shader["vertex"] == "vertex"
