# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the low-level `ImageView` (`_image_view.py`)."""

from __future__ import annotations

import numpy as np
import pytest

from pytanga.viz import (
    ImageChannelMode,
    ImageData,
    ImageDType,
    ImageLayerStyle,
    ImageView,
    LayerBlendMode,
)
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
        view.add_layer(_img("img2", channels=3))
        view.set_image(_img("img3", channels=4))
        assert [i.id for i in view.images] == ["img3", "img2"]

    def test_layer_cap(self) -> None:
        view = ImageView("img1")
        for i in range(MAX_IMAGE_LAYERS):
            view.add_layer(_img(f"img{i}"))
        with pytest.raises(ValueError, match="at most 4"):
            view.add_layer(_img("overflow"))

    def test_per_layer_defaults_seeded(self) -> None:
        view = ImageView("img1")
        view.set_image(_img("img1", channels=1))
        view.add_layer(_img("img2", dtype="uint16"))

        assert view.uniforms["u_layer0_enabled"] == 1
        assert view.uniforms["u_layer0_opacity"] == 1.0
        assert view.uniforms["u_layer0_blend"] == 0
        assert view.uniforms["u_layer0_mode"] == 0  # 1 channel → gray
        assert view.uniforms["u_layer0_value_max"] == 1.0
        assert view.uniforms["u_layer1_value_max"] == 65535.0  # uint16


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

    def test_set_layer_uniforms(self) -> None:
        view = ImageView("img1")
        view.set_image(_img("img1"))
        view.set_layer_enabled(0, False)
        view.set_layer_opacity(0, 0.5)
        view.set_layer_blend(0, LayerBlendMode.ADD)
        view.set_layer_value_range(0, 2.0, 8.0)
        view.set_layer_channel(0, ImageChannelMode.RGB)

        assert view.uniforms["u_layer0_enabled"] == 0
        assert view.uniforms["u_layer0_opacity"] == 0.5
        assert view.uniforms["u_layer0_blend"] == 1
        assert view.uniforms["u_layer0_value_min"] == 2.0
        assert view.uniforms["u_layer0_value_max"] == 8.0
        assert view.uniforms["u_layer0_mode"] == 1

    def test_set_layer_rejects_out_of_range(self) -> None:
        view = ImageView("img1")
        view.set_image(_img("img1"))
        with pytest.raises(IndexError):
            view.set_layer_opacity(1, 0.5)


class TestLayerStyle:
    def test_add_layer_returns_index(self) -> None:
        view = ImageView("img1")
        view.set_image(_img("img1"))
        assert view.add_layer(_img("img2")) == 1
        assert view.add_layer(_img("img3")) == 2

    def test_set_image_partial_style_full_apply(self) -> None:
        view = ImageView("img1")
        view.set_image(_img("img1", channels=3), ImageLayerStyle(opacity=0.5))
        assert view.uniforms["u_layer0_opacity"] == 0.5
        assert view.uniforms["u_layer0_enabled"] == 1  # default
        assert view.uniforms["u_layer0_blend"] == 0  # default normal
        assert view.uniforms["u_layer0_mode"] == 1  # auto from 3 channels

    def test_add_layer_partial_style(self) -> None:
        view = ImageView("img1")
        view.set_image(_img("img1"))
        view.add_layer(_img("img2", dtype="uint16"), ImageLayerStyle(enabled=False, blend="add"))
        assert view.uniforms["u_layer1_enabled"] == 0
        assert view.uniforms["u_layer1_blend"] == 1  # add
        assert view.uniforms["u_layer1_opacity"] == 1.0  # default
        assert view.uniforms["u_layer1_value_max"] == 65535.0  # auto from uint16

    def test_set_layer_overwrites(self) -> None:
        view = ImageView("img1")
        view.set_image(_img("img1"))
        view.add_layer(_img("img2"))
        view.set_layer(1, _img("img3", channels=3), ImageLayerStyle(opacity=0.5))
        assert [i.id for i in view.images] == ["img1", "img3"]
        assert view.uniforms["u_layer1_opacity"] == 0.5
        assert view.uniforms["u_layer1_mode"] == 1  # auto from 3 channels

    def test_set_layer_style_merges(self) -> None:
        view = ImageView("img1")
        view.set_image(_img("img1", channels=3))
        view.set_layer_style(0, ImageLayerStyle(opacity=0.5))
        assert view.uniforms["u_layer0_opacity"] == 0.5
        assert view.uniforms["u_layer0_enabled"] == 1  # unchanged
        assert view.uniforms["u_layer0_blend"] == 0  # unchanged
        assert view.uniforms["u_layer0_mode"] == 1  # unchanged

    def test_set_layer_style_full(self) -> None:
        view = ImageView("img1")
        view.set_image(_img("img1", channels=3))
        view.set_layer_style(
            0,
            ImageLayerStyle(
                enabled=False,
                opacity=0.5,
                blend="multiply",
                channel="gray",
                value_min=0.0,
                value_max=3.0,
            ),
        )
        assert view.uniforms["u_layer0_enabled"] == 0
        assert view.uniforms["u_layer0_opacity"] == 0.5
        assert view.uniforms["u_layer0_blend"] == 2  # multiply
        assert view.uniforms["u_layer0_mode"] == 0  # gray
        assert view.uniforms["u_layer0_value_min"] == 0.0
        assert view.uniforms["u_layer0_value_max"] == 3.0

    def test_set_layer_and_style_reject_out_of_range(self) -> None:
        view = ImageView("img1")
        view.set_image(_img("img1"))
        with pytest.raises(IndexError):
            view.set_layer_style(1, ImageLayerStyle(opacity=0.5))
        with pytest.raises(IndexError):
            view.set_layer(1, _img("img2"))


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
        img = result["images"][0]
        assert img["id"] == "img1"
        assert img["width"] == 4
        assert img["height"] == 3
        assert img["channels"] == 3
        assert img["dtype"] == 0
        assert img["source"] == "data"
        assert "version" in img
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

    def test_serialize_state_shape(self) -> None:
        view = ImageView("img1")
        view.set_image(_img("img1", channels=3))
        state = view._serialize_state()
        assert set(state) == {"images", "shader", "uniforms"}
        assert state["shader"] == {"fragment": None, "vertex": None}
        assert state["uniforms"]["u_mode"] == 1
        assert state["images"][0]["channels"] == 3

    def test_serialize_multilayer_per_layer_fields(self) -> None:
        view = ImageView("img1")
        view.set_image(_img("img1", channels=3))
        view.add_layer(_img("img2", dtype="uint16"))
        view.set_layer_opacity(1, 0.25)

        images = view._serialize()["images"]
        layer0 = images[0]
        layer1 = images[1]
        assert layer0["enabled"] == 1
        assert layer0["opacity"] == 1.0
        assert layer0["blend"] == 0
        assert layer0["mode"] == 1  # 3 channels → RGB
        assert layer0["value_max"] == 1.0
        assert layer1["mode"] == 0  # 1 channel → gray
        assert layer1["value_max"] == 65535.0
        assert layer1["opacity"] == 0.25
