# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for `ActCircle` (interactive circle)."""

from __future__ import annotations

import asyncio
from typing import Any

from pytanga.geometry import Circle, Direction, Point
from pytanga.viz import ActCircle, DragEvent
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
        pass

    def flush(self) -> None:
        pass

    def remove(self, object_id: str) -> None:
        pass


def _circle(**kwargs: Any) -> tuple[ActCircle, _FakeHandle]:
    handle = _FakeHandle(space_dim=2)
    circle = ActCircle(center=Point(5.0, 5.0, 0.0), radius=3.0, **kwargs)
    circle._init(handle, "c1")
    return circle, handle


class TestModel:
    def test_entity_is_circle(self) -> None:
        circle, _ = _circle()
        assert isinstance(circle.entity, Circle)
        assert circle.entity.radius == 3.0
        assert circle.entity.center == Point(5.0, 5.0, 0.0)

    def test_radius_property(self) -> None:
        circle, _ = _circle()
        assert circle.radius == 3.0

    def test_spawns_two_handles(self) -> None:
        _, handle = _circle()
        assert len(handle.added) == 2  # 1 radius + 1 translate


class TestBehaviour:
    def test_radius_resize(self) -> None:
        circle, _ = _circle()
        asyncio.run(
            circle._dispatch_radius_drag(DragEvent(world_position=Point(9.0, 5.0, 0.0)))
        )
        assert circle.radius == 4.0

    def test_radius_min_clamp(self) -> None:
        circle, _ = _circle(min_radius=1.0)
        asyncio.run(
            circle._dispatch_radius_drag(DragEvent(world_position=Point(5.1, 5.0, 0.0)))
        )
        assert circle.radius == 1.0

    def test_translate_moves_center(self) -> None:
        circle, _ = _circle()
        asyncio.run(
            circle._dispatch_translate(DragEvent(world_delta=Direction(1.0, 2.0, 0.0)))
        )
        assert circle.entity.center == Point(6.0, 7.0, 0.0)
        assert circle.radius == 3.0

    def test_create_from_points(self) -> None:
        circle = ActCircle.create_from_points(
            Point(0.0, 0.0, 0.0), Point(3.0, 4.0, 0.0)
        )
        assert circle.entity.radius == 5.0
        assert circle.entity.center == Point(0.0, 0.0, 0.0)


class TestPlaneZ:
    """Handles stay on the body's plane (z), not snapping to z=0."""

    def test_handles_preserve_plane_z(self) -> None:
        handle = _FakeHandle(space_dim=3)
        circle = ActCircle(center=Point(5.0, 5.0, -0.6), radius=3.0)
        circle._init(handle, "c1")
        assert circle._radius_handle.point.z == -0.6
        assert circle._translate_handle.point.z == -0.6

    def test_translate_preserves_z(self) -> None:
        handle = _FakeHandle(space_dim=3)
        circle = ActCircle(center=Point(5.0, 5.0, -0.6), radius=3.0)
        circle._init(handle, "c1")
        asyncio.run(
            circle._dispatch_translate(DragEvent(world_delta=Direction(1.0, 1.0, 0.0)))
        )
        assert circle.entity.center == Point(6.0, 6.0, -0.6)



class TestLimits:
    """Resize clamps: explicit min/max, and fp-precision when ``None``."""

    def test_no_default_floor_when_min_none(self) -> None:
        handle = _FakeHandle(space_dim=3)
        circle = ActCircle(center=Point(0.0, 0.0, 0.0), radius=0.02)
        circle._init(handle, "c1")
        asyncio.run(
            circle._dispatch_radius_drag(DragEvent(world_position=Point(0.001, 0.0, 0.0)))
        )
        assert circle.radius == 0.001  # not clamped to the old 0.05 default

    def test_min_radius_clamps(self) -> None:
        handle = _FakeHandle(space_dim=3)
        circle = ActCircle(center=Point(0.0, 0.0, 0.0), radius=1.0, min_radius=0.5)
        circle._init(handle, "c1")
        asyncio.run(
            circle._dispatch_radius_drag(DragEvent(world_position=Point(0.1, 0.0, 0.0)))
        )
        assert circle.radius == 0.5

    def test_max_radius_caps(self) -> None:
        handle = _FakeHandle(space_dim=3)
        circle = ActCircle(center=Point(0.0, 0.0, 0.0), radius=1.0, max_radius=2.0)
        circle._init(handle, "c1")
        asyncio.run(
            circle._dispatch_radius_drag(DragEvent(world_position=Point(5.0, 0.0, 0.0)))
        )
        assert circle.radius == 2.0

