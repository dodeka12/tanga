# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for `ActEllipse` (interactive ellipse)."""

from __future__ import annotations

import asyncio
import math
from typing import Any

from pytanga.geometry import Direction, Ellipse, Point
from pytanga.viz import ActEllipse, DragEvent
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


def _ellipse(**kwargs: Any) -> tuple[ActEllipse, _FakeHandle]:
    handle = _FakeHandle(space_dim=2)
    ellipse = ActEllipse(
        center=Point(5.0, 5.0, 0.0), radius_u=10.0, radius_v=4.0, **kwargs
    )
    ellipse._init(handle, "e1")
    return ellipse, handle


class TestModel:
    def test_entity_is_ellipse(self) -> None:
        ellipse, _ = _ellipse()
        assert isinstance(ellipse.entity, Ellipse)
        assert ellipse.entity.radius_u == 10.0
        assert ellipse.entity.radius_v == 4.0

    def test_dirs_encode_angle(self) -> None:
        ellipse = ActEllipse(
            center=Point(0.0, 0.0, 0.0), radius_u=2.0, radius_v=1.0, angle=math.pi / 2
        )
        e = ellipse.entity
        assert abs(e.dir_u.x) < 1e-9
        assert abs(e.dir_u.y - 1.0) < 1e-9
        assert abs(e.dir_v.x + 1.0) < 1e-9
        assert abs(e.dir_v.y) < 1e-9

    def test_interaction_config_disabled(self) -> None:
        ellipse, _ = _ellipse()
        assert ellipse.interaction_config.enabled is False


class TestHandles:
    def test_spawns_handles(self) -> None:
        _, handle = _ellipse()
        # 2 radius + 1 translate + 1 rotate
        assert len(handle.added) == 4

    def test_no_rotate_handle(self) -> None:
        ellipse = ActEllipse(
            center=Point(5.0, 5.0, 0.0),
            radius_u=10.0,
            radius_v=4.0,
            show_rotate_handle=False,
        )
        handle = _FakeHandle(space_dim=2)
        ellipse._init(handle, "e1")
        assert len(handle.added) == 3


class TestBehaviour:
    def test_translate_moves_center(self) -> None:
        ellipse, _ = _ellipse()
        asyncio.run(
            ellipse._dispatch_translate(DragEvent(world_delta=Direction(1.0, 2.0, 0.0)))
        )
        assert ellipse.center.x == 6.0
        assert ellipse.center.y == 7.0

    def test_resize_radius(self) -> None:
        ellipse, _ = _ellipse()
        asyncio.run(
            ellipse._dispatch_radius_drag(
                0, DragEvent(world_position=Point(20.0, 5.0, 0.0))
            )
        )
        assert ellipse.entity.radius_u == 15.0

    def test_rotate_updates_angle(self) -> None:
        ellipse = ActEllipse(
            center=Point(0.0, 0.0, 0.0), radius_u=2.0, radius_v=1.0, angle=0.0
        )
        handle = _FakeHandle(space_dim=2)
        ellipse._init(handle, "e1")
        asyncio.run(
            ellipse._dispatch_rotate(DragEvent(world_position=Point(0.0, 1.0, 0.0)))
        )
        assert abs(ellipse.angle - math.pi / 2) < 1e-9

    def test_on_change_fired(self) -> None:
        seen: list[Ellipse] = []
        ellipse, _ = _ellipse(on_change=seen.append)
        asyncio.run(
            ellipse._dispatch_translate(DragEvent(world_delta=Direction(1.0, 0.0, 0.0)))
        )
        assert len(seen) == 1
        assert seen[0].center.x == 6.0
