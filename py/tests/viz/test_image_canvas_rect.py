# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for per-handler enable/disable and cursor on `ImageCanvas`."""

from __future__ import annotations

from typing import Any

import numpy as np

from pytanga.viz import (
    DragBinding,
    DragEvent,
    ImageCanvas,
    ImageData,
    InteractionEventType,
    MouseButton,
    Visualizer,
)


class _FakeTransport:
    def __init__(self) -> None:
        self.handlers: dict[tuple[str, str], Any] = {}

    def register(
        self,
        object_id: str,
        handler: Any,
        *,
        event: str = "change",
        origin: Any = None,
    ) -> None:
        self.handlers[(object_id, event)] = handler

    def send(self, message: dict) -> None:
        pass

    def send_bytes(self, payload: bytes) -> None:
        pass


def _canvas(**kwargs: Any) -> tuple[Visualizer, ImageCanvas, _FakeTransport]:
    viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)
    fake = _FakeTransport()
    viz._transport = fake  # type: ignore[attr-defined]
    viz._interaction_host._transport = fake  # type: ignore[attr-defined]
    canvas = ImageCanvas(viz, **kwargs)
    canvas.set_image(ImageData("img1", data=np.zeros((10, 20), dtype=np.uint8)))
    return viz, canvas, fake


def _drag_triggers(viz: Visualizer, canvas: ImageCanvas) -> list[Any]:
    cfg = viz._interaction_host._interaction_configs[canvas.scene_name][
        canvas.image_view.id
    ]
    return [t for t in cfg.triggers if t.event_type is InteractionEventType.DRAG]


class TestBindingEnabled:
    async def _on_drag(self, _event: DragEvent, _canvas: ImageCanvas) -> bool:
        return True

    def test_binding_registered_disabled_has_no_trigger(self) -> None:
        binding = DragBinding(MouseButton.LEFT, self._on_drag, enabled=False)
        viz, canvas, _ = _canvas(drag_handlers=[binding])
        assert _drag_triggers(viz, canvas) == []

    def test_binding_enable_adds_trigger(self) -> None:
        binding = DragBinding(MouseButton.LEFT, self._on_drag, enabled=False)
        viz, canvas, _ = _canvas(drag_handlers=[binding])

        binding.enabled = True
        canvas.refresh_interaction()

        triggers = _drag_triggers(viz, canvas)
        assert len(triggers) == 1
        assert triggers[0].mouse_button is MouseButton.LEFT

    def test_binding_disable_removes_trigger(self) -> None:
        binding = DragBinding(MouseButton.LEFT, self._on_drag)
        viz, canvas, _ = _canvas(drag_handlers=[binding])
        assert len(_drag_triggers(viz, canvas)) == 1

        binding.enabled = False
        canvas.refresh_interaction()
        assert _drag_triggers(viz, canvas) == []


class TestHandlerEnabled:
    async def _on_drag(self, _event: DragEvent, _canvas: ImageCanvas) -> bool:
        return True

    def test_general_handler_toggle(self) -> None:
        viz, canvas, _ = _canvas(on_drag=self._on_drag)
        assert len(_drag_triggers(viz, canvas)) == 1

        canvas.set_handler_enabled(False)
        assert _drag_triggers(viz, canvas) == []

        canvas.set_handler_enabled(True)
        assert len(_drag_triggers(viz, canvas)) == 1


class TestCursor:
    def test_set_cursor_updates_scene_config(self) -> None:
        _, canvas, _ = _canvas()
        canvas.set_cursor("crosshair")
        assert canvas.handle.scene.config.cursor == "crosshair"
        canvas.set_cursor(None)
        assert canvas.handle.scene.config.cursor is None

    def test_cursor_serializes_in_scene_config(self) -> None:
        _, canvas, _ = _canvas()
        canvas.set_cursor("crosshair")
        assert canvas.handle.scene.config.to_dict()["cursor"] == "crosshair"

    def test_canvas_cursor_forwarded_to_plane_hover(self) -> None:
        cursor = "crosshair"
        _, canvas, _ = _canvas(cursor=cursor)
        assert canvas.act_plane.interaction_config.hover_cursor == "crosshair"
