# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the SDF viewer's light sources."""

from __future__ import annotations

import pytest

from pytanga.viz.sdf.lights import DirectionalLight, Light, serialize_light


def test_directional_light_normalizes_direction() -> None:
    light = DirectionalLight(direction=(0.0, 2.0, 0.0))
    assert light.direction == (0.0, 1.0, 0.0)


def test_directional_light_zero_direction_falls_back_to_z() -> None:
    light = DirectionalLight(direction=(0.0, 0.0, 0.0))
    assert light.direction == (0.0, 0.0, 1.0)


def test_directional_light_defaults() -> None:
    light = DirectionalLight()
    assert isinstance(light, Light)
    assert light.color == "#ffffff"
    assert light.intensity == 0.8


def test_directional_light_direction_setter_normalizes() -> None:
    light = DirectionalLight(direction=(1.0, 0.0, 0.0))
    light.direction = (0.0, 3.0, 0.0)
    assert light.direction == (0.0, 1.0, 0.0)
    light.direction = (0.0, 0.0, 0.0)
    assert light.direction == (0.0, 0.0, 1.0)


def test_serialize_light() -> None:
    light = DirectionalLight(direction=(1.0, 0.0, 0.0), color="#ff0000", intensity=2.0)
    assert serialize_light(light) == {
        "kind": "directional",
        "direction": [1.0, 0.0, 0.0],
        "color": "#ff0000",
        "intensity": 2.0,
    }


def test_serialize_light_rejects_unknown() -> None:
    with pytest.raises(TypeError):
        serialize_light(object())  # type: ignore[arg-type]
