# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for `ActRectangle2D` (interactive rectangle)."""

from __future__ import annotations

import asyncio
from typing import Any

from pytanga.geometry import Direction, Point, Rectangle2D
from pytanga.viz import ActRectangle2D, DragEvent
from pytanga.viz._act_style import ActPointStyle


class _FakeStyles:
    def __init__(self) -> None:
        self.act_point = ActPointStyle()


class _FakeSceneConfig:
    def __init__(self, space_dim: int | None) -> None:
        self.space_dim = space_dim


class _FakeScene:
    def __init__(self, space_dim: int | None) -> None:
        self.config = _FakeSceneConfig(space_dim)


class _FakeHandle:
    """Minimal stand-in for ``VizSceneHandle`` (records handle spawning)."""

    def __init__(self, space_dim: int | None = None) -> None:
        self.styles = _FakeStyles()
        self.scene = _FakeScene(space_dim)
        self.added: list[tuple[str, object]] = []
        self.updates: list[tuple[str, object]] = []
        self.removed: list[str] = []
        self.flushes = 0
        self._counter = 0

    def add(self, obj: Any, *, style: Any = None, **kwargs: Any) -> str:
        eid = f"h{self._counter}"
        self._counter += 1
        obj._init(self, eid)
        self.added.append((eid, style))
        return eid

    def set_interaction(self, object_id: str, config: object) -> None:
        pass

    def on_interaction(
        self, object_id: str, event_type: object, handler: object
    ) -> None:
        pass

    def update_entity(self, object_id: str, entity: object) -> None:
        self.updates.append((object_id, entity))

    def flush(self) -> None:
        self.flushes += 1

    def remove(self, object_id: str) -> None:
        self.removed.append(object_id)


def _rect(**kwargs: Any) -> tuple[ActRectangle2D, _FakeHandle]:
    handle = _FakeHandle(space_dim=2)
    rect = ActRectangle2D(center=Point(5.0, 5.0, 0.0), size=(10.0, 4.0), **kwargs)
    rect._init(handle, "r1")
    return rect, handle


class TestModel:
    def test_entity_is_rectangle2d(self) -> None:
        rect, _ = _rect()
        assert isinstance(rect.entity, Rectangle2D)
        assert rect.entity.size == (10.0, 4.0)

    def test_interaction_config_disabled(self) -> None:
        rect, _ = _rect()
        assert rect.interaction_config.enabled is False
        assert rect.interaction_config.triggers == []


class TestHandles:
    def test_spawns_five_handles(self) -> None:
        _, handle = _rect()
        assert len(handle.added) == 5  # 4 corners + 1 translate

    def test_spawns_four_handles_without_translate(self) -> None:
        rect = ActRectangle2D(
            center=Point(5.0, 5.0, 0.0), size=(10.0, 4.0), show_translate_handle=False
        )
        handle = _FakeHandle(space_dim=2)
        rect._init(handle, "r1")
        assert len(handle.added) == 4


class TestBehaviour:
    def test_corner_resize_recomputes_center_and_size(self) -> None:
        rect, _ = _rect()
        asyncio.run(
            rect._dispatch_corner_drag(
                0, DragEvent(world_position=Point(2.0, 3.0, 0.0))
            )
        )
        assert rect.entity.center.x == 6.0
        assert rect.entity.center.y == 5.0
        assert rect.entity.size == (8.0, 4.0)

    def test_translate_moves_center(self) -> None:
        rect, _ = _rect()
        asyncio.run(
            rect._dispatch_translate(DragEvent(world_delta=Direction(1.0, 2.0, 0.0)))
        )
        assert rect.entity.center.x == 6.0
        assert rect.entity.center.y == 7.0
        assert rect.entity.size == (10.0, 4.0)

    def test_on_change_fired(self) -> None:
        seen: list[Rectangle2D] = []
        rect, _ = _rect(on_change=seen.append)
        asyncio.run(
            rect._dispatch_translate(DragEvent(world_delta=Direction(1.0, 0.0, 0.0)))
        )
        assert len(seen) == 1
        assert seen[0].center.x == 6.0

    def test_on_corner_drag_override(self) -> None:
        calls: list[int] = []

        async def on_corner_drag(
            i: int, event: DragEvent, rect: ActRectangle2D
        ) -> bool:
            calls.append(i)
            return True

        rect, _ = _rect(on_corner_drag=on_corner_drag)
        asyncio.run(
            rect._dispatch_corner_drag(
                2, DragEvent(world_position=Point(9.0, 9.0, 0.0))
            )
        )
        assert calls == [2]
        # Default resize was suppressed → rectangle unchanged.
        assert rect.entity.size == (10.0, 4.0)
