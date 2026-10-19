# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the scene-lighting model (`_lighting.py` + `SceneConfig.lighting`)."""

from __future__ import annotations

import asyncio
import json

import pytest

from pytanga.viz import (
    DirectionalLightSpec,
    LightSpec,
    SceneConfig,
    SceneLighting,
    Visualizer,
)
from pytanga.viz._lighting import DEFAULT_SCENE_LIGHTING


class TestSceneLighting:
    def test_default_matches_wire_shape(self) -> None:
        assert DEFAULT_SCENE_LIGHTING.to_dict() == {
            "ambient": {"color": "#ffffff", "intensity": 0.5},
            "lights": [
                {
                    "direction": [
                        0.408248290463863,
                        0.816496580927726,
                        0.408248290463863,
                    ],
                    "color": "#ffffff",
                    "intensity": 0.8,
                },
                {
                    "direction": [
                        -0.5184758473652127,
                        -0.20739033894608505,
                        -0.8295613557843402,
                    ],
                    "color": "#ffffff",
                    "intensity": 0.3,
                },
            ],
        }

    def test_default_instance_equals_default_scene_lighting(self) -> None:
        assert SceneLighting() == DEFAULT_SCENE_LIGHTING

    def test_custom_to_dict(self) -> None:
        lighting = SceneLighting(
            ambient=LightSpec(color="#112233", intensity=0.25),
            lights=(
                DirectionalLightSpec(
                    direction=(1.0, 0.0, 0.0), color="#445566", intensity=0.75
                ),
            ),
        )
        assert lighting.to_dict() == {
            "ambient": {"color": "#112233", "intensity": 0.25},
            "lights": [
                {
                    "direction": [1.0, 0.0, 0.0],
                    "color": "#445566",
                    "intensity": 0.75,
                }
            ],
        }


class TestDirectionalLightSpec:
    def test_keeps_non_normalized_direction_as_is(self) -> None:
        spec = DirectionalLightSpec(direction=(2.0, 0.0, 0.0))
        assert spec.direction == (2.0, 0.0, 0.0)

    def test_default_direction_is_unit_z(self) -> None:
        assert DirectionalLightSpec().direction == (0.0, 0.0, 1.0)


class TestSceneConfigLighting:
    def test_default_omits_lighting_key(self) -> None:
        assert "lighting" not in SceneConfig().to_dict()

    def test_lighting_block_serialized_verbatim(self) -> None:
        lighting = SceneLighting(
            ambient=LightSpec(color="#000000", intensity=0.1),
            lights=(
                DirectionalLightSpec(
                    direction=(0.0, 1.0, 0.0), color="#ffffff", intensity=1.0
                ),
            ),
        )
        config = SceneConfig(lighting=lighting)
        assert config.to_dict()["lighting"] == lighting.to_dict()


class _FakeServer:
    def __init__(self) -> None:
        self.captured: list[str] = []

    async def push_raw(self, data: str) -> None:
        self.captured.append(data)


class TestSetSceneLighting:
    def test_sets_config_and_pushes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        server = _FakeServer()
        monkeypatch.setattr(viz, "_server", server)
        monkeypatch.setattr(viz, "_loop", object())
        monkeypatch.setattr(
            asyncio,
            "run_coroutine_threadsafe",
            lambda coro, loop: asyncio.run(coro),
        )

        lighting = SceneLighting(
            ambient=LightSpec(color="#111111", intensity=0.1),
            lights=(DirectionalLightSpec(direction=(1.0, 0.0, 0.0)),),
        )
        viz.set_scene_lighting(lighting)

        assert viz._layout.scenes[""].config.lighting is lighting
        assert viz._scene_config_for("")["lighting"] == lighting.to_dict()

        msg = json.loads(server.captured[-1])
        assert msg["type"] == "scene_config"
        assert msg["lighting"] == lighting.to_dict()

    def test_none_clears_and_omits(self, monkeypatch: pytest.MonkeyPatch) -> None:
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        viz._layout.scenes[""].config.lighting = SceneLighting()
        server = _FakeServer()
        monkeypatch.setattr(viz, "_server", server)
        monkeypatch.setattr(viz, "_loop", object())
        monkeypatch.setattr(
            asyncio,
            "run_coroutine_threadsafe",
            lambda coro, loop: asyncio.run(coro),
        )

        viz.set_scene_lighting(None)

        assert viz._layout.scenes[""].config.lighting is None
        assert "lighting" not in viz._scene_config_for("")
        assert "lighting" not in json.loads(server.captured[-1])
