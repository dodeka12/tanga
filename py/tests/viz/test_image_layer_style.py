# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for `ImageLayerStyle` / `LayerBlendMode` / `ImageChannelMode` (`image.py`)."""

from __future__ import annotations

import pytest

from pytanga.viz import (
    DEFAULT_IMAGE_LAYER_STYLE,
    ImageChannelMode,
    ImageLayerStyle,
    LayerBlendMode,
)


class TestLayerBlendMode:
    def test_values_and_codes(self) -> None:
        assert LayerBlendMode.NORMAL.value == "normal"
        assert LayerBlendMode.ADD.value == "add"
        assert LayerBlendMode.MULTIPLY.value == "multiply"
        assert LayerBlendMode.SCREEN.value == "screen"
        assert LayerBlendMode.ADD.code == 1
        assert LayerBlendMode.SCREEN.code == 3

    def test_from_code(self) -> None:
        assert LayerBlendMode.from_code(0) is LayerBlendMode.NORMAL
        assert LayerBlendMode.from_code(2) is LayerBlendMode.MULTIPLY
        with pytest.raises(ValueError):
            LayerBlendMode.from_code(9)


class TestImageChannelMode:
    def test_from_str(self) -> None:
        assert ImageChannelMode.from_str("gray") is ImageChannelMode.GRAY
        assert ImageChannelMode.from_str("rgb") is ImageChannelMode.RGB
        assert ImageChannelMode.from_str("magnitude") is ImageChannelMode.MAGNITUDE
        assert ImageChannelMode.from_str("alpha") is ImageChannelMode.ALPHA
        with pytest.raises(ValueError):
            ImageChannelMode.from_str("bogus")


class TestImageLayerStyle:
    def test_defaults_are_none(self) -> None:
        style = ImageLayerStyle()
        assert style.enabled is None
        assert style.opacity is None
        assert style.blend is None
        assert style.channel is None
        assert style.value_min is None
        assert style.value_max is None

    def test_default_instance(self) -> None:
        assert DEFAULT_IMAGE_LAYER_STYLE.enabled is None
        assert DEFAULT_IMAGE_LAYER_STYLE.opacity is None
        assert DEFAULT_IMAGE_LAYER_STYLE.blend is None

    def test_partial_init(self) -> None:
        style = ImageLayerStyle(opacity=0.5)
        assert style.opacity == 0.5
        assert style.enabled is None
        assert style.blend is None

    def test_string_coercion(self) -> None:
        style = ImageLayerStyle(blend="add", channel="gray")
        assert style.blend is LayerBlendMode.ADD
        assert style.channel is ImageChannelMode.GRAY

    def test_opacity_validation(self) -> None:
        with pytest.raises(ValueError, match="opacity"):
            ImageLayerStyle(opacity=1.5)

    def test_value_range_validation(self) -> None:
        with pytest.raises(ValueError, match="value_min"):
            ImageLayerStyle(value_min=2.0, value_max=1.0)
