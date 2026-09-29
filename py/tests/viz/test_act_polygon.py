# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for `ActPolygon` (editable open/closed polygon)."""

from __future__ import annotations

import asyncio
from typing import Any

from pytanga.geometry import Direction, Point
from pytanga.viz import ActPolygon, DragEvent, SquarePointStyle
from pytanga.viz._act_style import ActPointStyle
from pytanga.viz._interaction import ModifierKey
from pytanga.viz._point_path import PointPath


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


def _polygon(points: list[Point] | None = None, **kwargs: Any):  # noqa: ANN202
    points = points or [Point(0.0, 0.0, 0.0), Point(1.0, 0.0, 0.0), Point(1.0, 1.0, 0.0)]
    handle = _FakeHandle(space_dim=2)
    poly = ActPolygon(points, **kwargs)
    poly._init(handle, "p1")
    return poly, handle


class TestModel:
    def test_entity_is_closed_path(self) -> None:
        poly, _ = _polygon()
        path = poly.entity
        assert isinstance(path, PointPath)
        assert len(path.points) == 4  # 3 vertices + closing repeat
        assert path.points[0] == path.points[-1]

    def test_open_path_not_closed(self) -> None:
        poly, _ = _polygon(closed=False)
        assert len(poly.entity.points) == 3

    def test_interaction_config_disabled(self) -> None:
        poly, _ = _polygon()
        assert poly.interaction_config.enabled is False


class TestHandles:
    def test_spawns_vertex_and_translate_handles(self) -> None:
        _, handle = _polygon()
        assert len(handle.added) == 4  # 3 vertices + 1 translate

    def test_all_vertices_have_delete_bindings(self) -> None:
        poly, _ = _polygon(closed=False)
        for i in range(len(poly.points)):
            bindings = poly._make_delete_bindings(i)
            assert bindings is not None
            assert len(bindings) == 2  # Ctrl + Ctrl+Shift

    def test_end_vertices_have_distinct_style(self) -> None:
        inner = SquarePointStyle(color="#ff4444")
        end = SquarePointStyle(color="#00cc44")
        poly = ActPolygon(
            [Point(0.0, 0.0, 0.0), Point(1.0, 0.0, 0.0), Point(1.0, 1.0, 0.0)],
            closed=False,
            show_translate_handle=False,
            handle_style=inner,
            end_handle_style=end,
        )
        handle = _FakeHandle(space_dim=2)
        poly._init(handle, "p1")
        styles = [s for _, s in handle.added]
        assert styles[0] is end  # start vertex
        assert styles[1] is inner  # inner vertex
        assert styles[2] is end  # end vertex


class TestBehaviour:
    def test_move_vertex(self) -> None:
        poly, _ = _polygon()
        asyncio.run(
            poly._dispatch_vertex_drag(
                1, DragEvent(world_position=Point(5.0, 0.0, 0.0))
            )
        )
        assert poly.points[1] == Point(5.0, 0.0, 0.0)

    def test_ctrl_drag_start_inserts_before(self) -> None:
        poly, _ = _polygon(closed=False)
        event = DragEvent(
            world_position=Point(-1.0, 0.0, 0.0),
            modifiers=frozenset({ModifierKey.CTRL}),
        )
        asyncio.run(poly._dispatch_vertex_drag(0, event))
        assert len(poly.points) == 4
        assert poly.points[0] == Point(-1.0, 0.0, 0.0)  # new start (inserted before)
        assert poly.points[1] == Point(0.0, 0.0, 0.0)   # original start shifted

    def test_ctrl_drag_middle_inserts_after(self) -> None:
        poly, _ = _polygon(closed=False)
        event = DragEvent(
            world_position=Point(0.5, 0.5, 0.0),
            modifiers=frozenset({ModifierKey.CTRL}),
        )
        asyncio.run(poly._dispatch_vertex_drag(1, event))
        assert len(poly.points) == 4
        assert poly.points[2] == Point(0.5, 0.5, 0.0)

    def test_ctrl_drag_end_inserts(self) -> None:
        poly, _ = _polygon(closed=False)
        event = DragEvent(
            world_position=Point(2.0, 2.0, 0.0),
            modifiers=frozenset({ModifierKey.CTRL}),
        )
        asyncio.run(poly._dispatch_vertex_drag(len(poly.points) - 1, event))
        assert len(poly.points) == 4
        assert poly.points[-1] == Point(2.0, 2.0, 0.0)

    def test_ctrl_drag_insert_then_drag_away(self) -> None:
        poly, _ = _polygon(closed=False)
        # Ctrl+drag the end vertex: the first move inserts a new endpoint.
        first = DragEvent(
            world_position=Point(2.0, 0.0, 0.0),
            modifiers=frozenset({ModifierKey.CTRL}),
        )
        asyncio.run(poly._dispatch_vertex_drag(len(poly.points) - 1, first))
        assert len(poly.points) == 4
        assert poly.points[-1] == Point(2.0, 0.0, 0.0)

        # Continuation of the same drag: the new endpoint follows the mouse,
        # while the original endpoint stays put.
        second = DragEvent(
            world_position=Point(3.0, 1.0, 0.0),
            modifiers=frozenset({ModifierKey.CTRL}),
        )
        asyncio.run(poly._dispatch_vertex_drag(len(poly.points) - 1, second))
        assert poly.points[-1] == Point(3.0, 1.0, 0.0)
        assert poly.points[-2] == Point(1.0, 1.0, 0.0)

        # Drag end clears the insert state and rebuilds the handles.
        poly._finish_vertex_drag()
        assert poly._insert_drag_index is None

    def test_auto_close_fuses_endpoints(self) -> None:
        poly = ActPolygon(
            [Point(0.0, 0.0, 0.0), Point(10.0, 0.0, 0.0), Point(10.0, 10.0, 0.0)],
            closed=False,
            auto_close=True,
            show_translate_handle=False,
        )
        handle = _FakeHandle(space_dim=2)
        poly._init(handle, "p1")
        assert poly._closed is False
        assert len(poly.points) == 3

        # Drag the end vertex onto the start vertex → the two endpoints fuse
        # into one and the polygon closes with one fewer vertex.
        asyncio.run(
            poly._dispatch_vertex_drag(
                2, DragEvent(world_position=Point(0.0, 0.0, 0.0))
            )
        )
        assert poly._closed is True
        assert len(poly.points) == 2  # the end vertex was removed
        assert poly.points[0] == Point(0.0, 0.0, 0.0)
        assert poly.points[1] == Point(10.0, 0.0, 0.0)
        assert poly.entity.points[0] == poly.entity.points[-1]

        # The closed polygon no longer exposes endpoint handles.
        assert poly._is_endpoint(0) is False
        assert poly._is_endpoint(len(poly.points) - 1) is False

    def test_auto_close_needs_at_least_three_vertices(self) -> None:
        poly = ActPolygon(
            [Point(0.0, 0.0, 0.0), Point(10.0, 0.0, 0.0)],
            closed=False,
            auto_close=True,
            show_translate_handle=False,
        )
        handle = _FakeHandle(space_dim=2)
        poly._init(handle, "p1")

        # Two vertices are not enough to close: dragging the end onto the start
        # just moves it (no fusion).
        asyncio.run(
            poly._dispatch_vertex_drag(
                1, DragEvent(world_position=Point(0.0, 0.0, 0.0))
            )
        )
        assert poly._closed is False
        assert len(poly.points) == 2

    def test_no_auto_close_without_flag(self) -> None:
        poly = ActPolygon(
            [Point(0.0, 0.0, 0.0), Point(10.0, 0.0, 0.0), Point(10.0, 10.0, 0.0)],
            closed=False,
            show_translate_handle=False,
        )
        handle = _FakeHandle(space_dim=2)
        poly._init(handle, "p1")
        asyncio.run(
            poly._dispatch_vertex_drag(
                2, DragEvent(world_position=Point(0.0, 0.0, 0.0))
            )
        )
        assert poly._closed is False

    def test_auto_close_tolerance_derived_from_handle_size(self) -> None:
        poly = ActPolygon(
            [Point(0.0, 0.0, 0.0), Point(10.0, 0.0, 0.0), Point(10.0, 10.0, 0.0)],
            closed=False,
            auto_close=True,
            show_translate_handle=False,
            handle_style=SquarePointStyle(size=3.0),
        )
        assert poly._effective_close_tolerance() == 6.0  # 2 * size

    def test_auto_close_explicit_tolerance_wins(self) -> None:
        poly = ActPolygon(
            [Point(0.0, 0.0, 0.0), Point(10.0, 0.0, 0.0), Point(10.0, 10.0, 0.0)],
            closed=False,
            auto_close=True,
            close_tolerance=12.0,
            show_translate_handle=False,
            handle_style=SquarePointStyle(size=3.0),
        )
        assert poly._effective_close_tolerance() == 12.0

    def test_delete_vertex(self) -> None:
        poly, _ = _polygon()
        poly._delete_vertex(0)
        assert len(poly.points) == 2
        assert poly.points[0] == Point(1.0, 0.0, 0.0)
        assert poly._closed is False  # 3-vertex closed → 2-vertex open

    def test_delete_keeps_closed_with_four_vertices(self) -> None:
        poly, _ = _polygon(
            [
                Point(0.0, 0.0, 0.0),
                Point(1.0, 0.0, 0.0),
                Point(1.0, 1.0, 0.0),
                Point(0.0, 1.0, 0.0),
            ]
        )
        poly._delete_vertex(1)
        assert len(poly.points) == 3
        assert poly._closed is True

    def test_delete_open_opens_closed_polygon(self) -> None:
        poly, _ = _polygon()
        poly._delete_vertex(0, open=True)
        assert len(poly.points) == 2
        assert poly._closed is False
        assert poly._auto_close is True

    def test_delete_down_to_one_removes_composite(self) -> None:
        removed: list[None] = []

        def _on_removed() -> None:
            removed.append(None)

        poly, handle = _polygon(
            [Point(0.0, 0.0, 0.0), Point(1.0, 0.0, 0.0)], on_removed=_on_removed
        )
        poly._delete_vertex(0)
        assert len(removed) == 1
        assert "p1" in handle.removed

    def test_translate_moves_all_vertices(self) -> None:
        poly, _ = _polygon()
        asyncio.run(
            poly._dispatch_translate(DragEvent(world_delta=Direction(1.0, 1.0, 0.0)))
        )
        assert poly.points == [Point(1.0, 1.0, 0.0), Point(2.0, 1.0, 0.0), Point(2.0, 2.0, 0.0)]

    def test_on_change_fired(self) -> None:
        seen: list[list[Point]] = []
        poly, _ = _polygon(on_change=seen.append)
        asyncio.run(
            poly._dispatch_vertex_drag(
                1, DragEvent(world_position=Point(5.0, 0.0, 0.0))
            )
        )
        assert len(seen) == 1
        assert len(seen[0]) == 3

    def test_create_from_points_is_open(self) -> None:
        poly = ActPolygon.create_from_points(
            Point(0.0, 0.0, 0.0), Point(4.0, 2.0, 0.0)
        )
        assert poly._closed is False
        assert poly._auto_close is True
        assert poly.points == [Point(0.0, 0.0, 0.0), Point(4.0, 2.0, 0.0)]
