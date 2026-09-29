# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the per-scene keyboard-shortcut facility."""

from __future__ import annotations

import asyncio

from pytanga.viz import KeyEvent, SceneConfig, Visualizer
from pytanga.viz._interaction import ModifierKey


def test_scene_config_keyboard_only_when_set() -> None:
    cfg = SceneConfig()
    assert "keyboard" not in cfg.to_dict()
    cfg.keyboard = [{"key": "Delete", "modifiers": []}]
    assert cfg.to_dict()["keyboard"] == [{"key": "Delete", "modifiers": []}]


def test_on_key_registers_under_namespaced_id() -> None:
    async def handler(event):  # noqa: ANN001, ANN202
        pass

    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    viz.on_key("Delete", handler)
    assert viz._handler_registry.get_interaction("key::delete", "key") is not None
    assert viz._layout.scene("").config.keyboard == [
        {"key": "delete", "modifiers": []}
    ]


def test_interaction_key_dispatch_runs_handler() -> None:
    received: list[KeyEvent] = []

    async def handler(event):  # noqa: ANN001, ANN202
        received.append(event)

    async def run() -> None:
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        viz.on_key("Delete", handler)
        await viz._dispatch_interaction_event(
            "interaction:key",
            {
                "type": "interaction:key",
                "event_type": "key",
                "scene": "",
                "key": "Delete",
                "modifiers": [],
                "browser_id": "b1",
            },
        )
        assert len(received) == 1
        assert received[0].key == "delete"
        assert received[0].scene == ""

    asyncio.run(run())


def test_key_matches_most_specific_binding() -> None:
    received: list[KeyEvent] = []

    async def plain(event):  # noqa: ANN001, ANN202
        received.append(("plain", event))

    async def ctrl(event):  # noqa: ANN001, ANN202
        received.append(("ctrl", event))

    async def run() -> None:
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        viz.on_key("d", plain)
        viz.on_key("d", ctrl, modifiers=[ModifierKey.CTRL])
        await viz._dispatch_interaction_event(
            "interaction:key",
            {
                "type": "interaction:key",
                "event_type": "key",
                "scene": "",
                "key": "d",
                "modifiers": ["ctrl"],
                "browser_id": "b1",
            },
        )
        assert [name for name, _ in received] == ["ctrl"]

    asyncio.run(run())
