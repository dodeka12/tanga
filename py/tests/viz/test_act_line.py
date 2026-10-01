# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for `ActLine` (interactive 2-point line segment)."""

from __future__ import annotations

import asyncio
from typing import Any

from pytanga.geometry import Direction, Line, Point
from pytanga.viz import ActLine, DragEvent
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


def _line(**kwargs: Any) -> tuple[ActLine, _FakeHandle]:
    handle = _FakeHandle(space_dim=2)
    line = ActLine(start=Point(0.0, 0.0, 0.0), end=Point(2.0, 0.0, 0.0), **kwargs)
    line._init(handle, "l1")
    return line, handle


class TestModel:
    def test_entity_is_line(self) -> None:
        line, _ = _line()
        assert isinstance(line.entity, Line)
        assert line.entity.start == Point(0.0, 0.0, 0.0)
        assert line.entity.end == Point(2.0, 0.0, 0.0)

    def test_start_end_properties(self) -> None:
        line, _ = _line()
        assert line.start == Point(0.0, 0.0, 0.0)
        assert line.end == Point(2.0, 0.0, 0.0)

    def test_spawns_three_handles(self) -> None:
        _, handle = _line()
        assert len(handle.added) == 3  # 2 endpoints + 1 translate


class TestBehaviour:
    def test_endpoint_drag_moves_endpoint(self) -> None:
        line, _ = _line()
        asyncio.run(
            line._dispatch_endpoint_drag(
                1, DragEvent(world_position=Point(3.0, 1.0, 0.0))
            )
        )
        assert line.end == Point(3.0, 1.0, 0.0)
        assert line.start == Point(0.0, 0.0, 0.0)

    def test_translate_moves_both_endpoints(self) -> None:
        line, _ = _line()
        asyncio.run(
            line._dispatch_translate(DragEvent(world_delta=Direction(1.0, 1.0, 0.0)))
        )
        assert line.start == Point(1.0, 1.0, 0.0)
        assert line.end == Point(3.0, 1.0, 0.0)

    def test_create_from_points(self) -> None:
        line = ActLine.create_from_points(
            Point(0.0, 0.0, 0.0), Point(4.0, 3.0, 0.0)
        )
        assert line.start == Point(0.0, 0.0, 0.0)
        assert line.end == Point(4.0, 3.0, 0.0)
        assert line.entity.length == 5.0  # |(4, 3)| = 5


class TestPlaneZ:
    """Handles stay on the body's plane (z), not snapping to z=0."""

    def test_handles_preserve_plane_z(self) -> None:
        handle = _FakeHandle(space_dim=3)
        line = ActLine(start=Point(0.0, 0.0, -0.6), end=Point(2.0, 0.0, -0.6))
        line._init(handle, "l1")
        for h in line._endpoint_handles:
            assert h.point.z == -0.6
        assert line._translate_handle.point.z == -0.6

    def test_endpoint_drag_preserves_z(self) -> None:
        handle = _FakeHandle(space_dim=3)
        line = ActLine(start=Point(0.0, 0.0, -0.6), end=Point(2.0, 0.0, -0.6))
        line._init(handle, "l1")
        asyncio.run(
            line._dispatch_endpoint_drag(
                1, DragEvent(world_position=Point(3.0, 1.0, -0.6))
            )
        )
        assert line.end == Point(3.0, 1.0, -0.6)

    def test_translate_preserves_z(self) -> None:
        handle = _FakeHandle(space_dim=3)
        line = ActLine(start=Point(0.0, 0.0, -0.6), end=Point(2.0, 0.0, -0.6))
        line._init(handle, "l1")
        asyncio.run(
            line._dispatch_translate(DragEvent(world_delta=Direction(1.0, 1.0, 0.0)))
        )
        assert line.start == Point(1.0, 1.0, -0.6)
        assert line.end == Point(3.0, 1.0, -0.6)

