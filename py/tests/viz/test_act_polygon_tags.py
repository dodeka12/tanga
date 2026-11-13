# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for `ActPolygon` vertex tags, selection state, and stable IDs."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from pytanga.geometry import Point
from pytanga.viz import (
    ActPolygon,
    ClickEvent,
    DragEvent,
    SquarePointStyle,
    resolve_tag_color,
)
from pytanga.viz._act_style import ActPointStyle
from pytanga.viz._interaction import ModifierKey


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
    """Minimal ``VizSceneHandle`` stand-in (records handle spawning)."""

    def __init__(self, space_dim: int | None = None) -> None:
        self.styles = _FakeStyles()
        self.scene = _FakeScene(space_dim)
        self.added: list[tuple[str, object]] = []
        self.style_updates: list[tuple[str, object]] = []
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
        pass

    def update(self, object_id: str, **properties: Any) -> None:
        self.style_updates.append((object_id, properties))

    def update_style(self, entity_id: str, style: object) -> None:
        self.style_updates.append((entity_id, style))

    def flush(self) -> None:
        self.flushes += 1

    def remove(self, object_id: str) -> None:
        pass

    def set_visible(self, object_id: str, visible: bool) -> None:
        pass


def _polygon(points: list[Point] | None = None, **kwargs: Any):  # noqa: ANN202
    points = points or [
        Point(0.0, 0.0, 0.0),
        Point(1.0, 0.0, 0.0),
        Point(1.0, 1.0, 0.0),
    ]
    handle = _FakeHandle(space_dim=2)
    poly = ActPolygon(points, **kwargs)
    poly._init(handle, "p1")
    return poly, handle


def _quad(points: list[Point] | None = None, **kwargs: Any):  # noqa: ANN202
    points = points or [
        Point(0.0, 0.0, 0.0),
        Point(1.0, 0.0, 0.0),
        Point(1.0, 1.0, 0.0),
        Point(0.0, 1.0, 0.0),
    ]
    handle = _FakeHandle(space_dim=2)
    poly = ActPolygon(points, **kwargs)
    poly._init(handle, "p1")
    return poly, handle


def _ctrl_event(x: float, y: float) -> DragEvent:
    return DragEvent(
        world_position=Point(x, y, 0.0),
        modifiers=frozenset({ModifierKey.CTRL}),
    )


def test_default_tags_are_none() -> None:
    poly, _ = _polygon()
    assert poly.vertex_tags == [None, None, None]


def test_default_vertex_tag_fills_every_vertex() -> None:
    poly, _ = _polygon(default_vertex_tag="1")
    assert poly.vertex_tags == ["1", "1", "1"]


def test_vertex_tags_round_trip() -> None:
    poly, _ = _polygon(vertex_tags=["a", None, "c"])
    assert poly.vertex_tags == ["a", None, "c"]


def test_vertex_tags_wrong_length_raises() -> None:
    with pytest.raises(ValueError):
        ActPolygon([Point(0, 0, 0), Point(1, 0, 0)], vertex_tags=["a"])


def test_set_vertex_tag_and_tags() -> None:
    poly, _ = _polygon()
    poly.set_vertex_tag(1, "x")
    assert poly.vertex_tags == [None, "x", None]
    poly.set_vertex_tags(["a", "b", "c"])
    assert poly.vertex_tags == ["a", "b", "c"]
    with pytest.raises(ValueError):
        poly.set_vertex_tags(["a"])
    with pytest.raises(IndexError):
        poly.set_vertex_tag(3, "z")


def test_insert_assigns_default_tag_and_keeps_existing_ids() -> None:
    poly, _ = _polygon(closed=False, vertex_tags=["a", "b", "c"], default_vertex_tag="d")
    asyncio.run(poly._dispatch_vertex_drag(1, _ctrl_event(0.5, 0.5)))
    assert poly.vertex_tags == ["a", "b", "d", "c"]


def test_insert_before_start_assigns_default_tag() -> None:
    poly, _ = _polygon(closed=False, vertex_tags=["a", "b", "c"], default_vertex_tag="d")
    asyncio.run(poly._dispatch_vertex_drag(0, _ctrl_event(-1.0, 0.0)))
    assert poly.vertex_tags == ["d", "a", "b", "c"]


def test_delete_removes_tag() -> None:
    poly, _ = _quad(vertex_tags=["a", "b", "c", "d"])
    poly._delete_vertex(1)
    assert poly.vertex_tags == ["a", "c", "d"]


def test_fuse_removes_last_tag() -> None:
    poly = ActPolygon(
        [Point(0.0, 0.0, 0.0), Point(10.0, 0.0, 0.0), Point(10.0, 10.0, 0.0)],
        closed=False,
        auto_close=True,
        vertex_tags=["a", "b", "c"],
        show_translate_handle=False,
    )
    handle = _FakeHandle(space_dim=2)
    poly._init(handle, "p1")
    asyncio.run(poly._dispatch_vertex_drag(2, DragEvent(world_position=Point(0.0, 0.0, 0.0))))
    assert poly.vertex_tags == ["a", "b"]


def test_delete_selected_vertex_clears_selection() -> None:
    poly, _ = _quad()
    poly.set_selected_vertex(1)
    assert poly.selected_vertex == 1
    poly._delete_vertex(1)
    assert poly.selected_vertex is None


def test_insert_before_selected_vertex_shifts_index() -> None:
    poly, _ = _polygon(closed=False)
    poly.set_selected_vertex(1)
    asyncio.run(poly._dispatch_vertex_drag(0, _ctrl_event(-1.0, 0.0)))
    assert poly.selected_vertex == 2


def test_set_on_change_replaces_callback() -> None:
    first: list[list[Point]] = []
    second: list[list[Point]] = []
    poly, _ = _polygon(on_change=first.append)
    poly.set_on_change(second.append)
    asyncio.run(
        poly._dispatch_vertex_drag(1, DragEvent(world_position=Point(5.0, 0.0, 0.0)))
    )
    assert first == []
    assert len(second) == 1


def _style_for(poly: Any, handle: _FakeHandle, index: int) -> Any:
    eid = poly._vertex_handles[index].entity_id  # noqa: SLF001
    for recorded_id, style in reversed(handle.style_updates):
        if recorded_id == eid:
            return style
    for recorded_id, style in handle.added:
        if recorded_id == eid:
            return style
    return None


def test_tagging_false_ignores_tags() -> None:
    poly, handle = _polygon(vertex_tags=["a", "b", "c"])
    assert _style_for(poly, handle, 1).color == "#ff4444"


def test_endpoint_styles_apply_when_not_tagging() -> None:
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
    assert _style_for(poly, handle, 0).color == "#00cc44"
    assert _style_for(poly, handle, 1).color == "#ff4444"
    assert _style_for(poly, handle, 2).color == "#00cc44"


def test_tagging_uses_palette_color() -> None:
    poly, handle = _polygon(vertex_tags=["a", "b", "c"], tagging=True)
    assert _style_for(poly, handle, 1).color == resolve_tag_color("b")


def test_set_tag_color_overrides_palette() -> None:
    poly, handle = _polygon(vertex_tags=["a", "a", "a"], tagging=True)
    poly.set_tag_color("a", "#123456")
    assert _style_for(poly, handle, 0).color == "#123456"


def test_untagged_vertex_uses_base_style_in_tagging() -> None:
    poly, handle = _polygon(vertex_tags=["a", None, "c"], tagging=True)
    assert _style_for(poly, handle, 1).color == "#ff4444"


def test_selected_vertex_uses_selected_style() -> None:
    poly, handle = _polygon()
    poly.set_selected_vertex(1)
    assert _style_for(poly, handle, 1).color == "#ffff44"
    poly.set_selected_vertex(None)
    assert _style_for(poly, handle, 1).color == "#ff4444"


def test_selected_style_wins_over_tag() -> None:
    poly, handle = _polygon(vertex_tags=["a", "a", "a"], tagging=True)
    poly.set_selected_vertex(1)
    assert _style_for(poly, handle, 1).color == "#ffff44"


def test_custom_selected_style() -> None:
    custom = SquarePointStyle(color="#123456")
    poly, handle = _polygon(selected_handle_style=custom)
    poly.set_selected_vertex(1)
    assert _style_for(poly, handle, 1).color == "#123456"


def test_endpoint_style_suppressed_in_tagging() -> None:
    inner = SquarePointStyle(color="#ff4444")
    end = SquarePointStyle(color="#00cc44")
    poly = ActPolygon(
        [Point(0.0, 0.0, 0.0), Point(1.0, 0.0, 0.0), Point(1.0, 1.0, 0.0)],
        closed=False,
        show_translate_handle=False,
        handle_style=inner,
        end_handle_style=end,
        tagging=True,
        vertex_tags=["a", "b", "c"],
    )
    handle = _FakeHandle(space_dim=2)
    poly._init(handle, "p1")
    assert _style_for(poly, handle, 0).color == resolve_tag_color("a")
    assert _style_for(poly, handle, 2).color == resolve_tag_color("c")


def test_on_vertex_click_selects_and_fires_body_click() -> None:
    seen: list[int] = []
    body_clicks: list[Any] = []

    async def on_vertex_click(index, event, act):  # noqa: ANN001, ANN202
        seen.append(index)

    async def on_click(event, act):  # noqa: ANN001, ANN202
        body_clicks.append(act)

    poly = ActPolygon(
        [Point(0.0, 0.0, 0.0), Point(1.0, 0.0, 0.0), Point(1.0, 1.0, 0.0)],
        on_click=on_click,
        on_vertex_click=on_vertex_click,
    )
    handle = _FakeHandle(space_dim=2)
    poly._init(handle, "p1")
    asyncio.run(poly._make_vertex_click_handler(1)(ClickEvent(), None))
    assert seen == [1]
    assert body_clicks == [poly]
    assert poly.selected_vertex == 1


def test_select_on_click_false_still_fires_callback() -> None:
    seen: list[int] = []

    async def on_vertex_click(index, event, act):  # noqa: ANN001, ANN202
        seen.append(index)

    poly = ActPolygon(
        [Point(0.0, 0.0, 0.0), Point(1.0, 0.0, 0.0), Point(1.0, 1.0, 0.0)],
        select_on_click=False,
        on_vertex_click=on_vertex_click,
    )
    handle = _FakeHandle(space_dim=2)
    poly._init(handle, "p1")
    asyncio.run(poly._make_vertex_click_handler(1)(ClickEvent(), None))
    assert seen == [1]
    assert poly.selected_vertex is None


def test_tag_and_selection_changes_do_not_fire_on_change() -> None:
    seen: list[list[Point]] = []
    poly, _ = _polygon(on_change=seen.append)
    poly.set_vertex_tag(1, "x")
    poly.set_selected_vertex(1)
    poly.set_selected_vertex(None)
    poly.set_tagging(True)
    poly.set_tag_color("x", "#123456")
    assert seen == []


def test_tag_palette_is_deterministic() -> None:
    assert resolve_tag_color("z") == resolve_tag_color("z")
    assert resolve_tag_color("z") != resolve_tag_color("y")


def test_closed_segment_count_includes_closing_segment() -> None:
    poly, _ = _polygon()
    assert poly.segment_count == 3
    assert poly.entity.segment_colors == [None, None, None]


def test_open_segment_count_excludes_closing_segment() -> None:
    poly, _ = _polygon(closed=False)
    assert poly.segment_count == 2


def test_set_segment_colors_round_trips() -> None:
    poly, _ = _polygon()
    poly.set_segment_colors(["#ff0000", None, "#0000ff"])
    assert poly.segment_colors == ["#ff0000", None, "#0000ff"]
    assert poly.entity.segment_colors == ["#ff0000", None, "#0000ff"]
    with pytest.raises(ValueError):
        poly.set_segment_colors(["#ff0000"])


def test_set_segment_color_and_clear() -> None:
    poly, _ = _polygon()
    poly.set_segment_color(1, "#ff0000")
    assert poly.segment_colors == [None, "#ff0000", None]
    with pytest.raises(IndexError):
        poly.set_segment_color(3, "#0000ff")
    poly.clear_segment_color(1)
    assert poly.segment_colors == [None, None, None]


def test_delete_remaps_segment_colors() -> None:
    poly, _ = _quad()
    poly.set_segment_colors(["#a", "#b", "#c", "#d"])
    poly._delete_vertex(1)
    assert poly.segment_colors == ["#a", "#c", "#d"]


def test_insert_after_remaps_segment_colors() -> None:
    poly, _ = _polygon(closed=False)
    poly.set_segment_colors(["#a", "#b"])
    asyncio.run(poly._dispatch_vertex_drag(1, _ctrl_event(0.5, 0.5)))
    assert poly.segment_colors == ["#a", "#b", None]


def test_insert_before_start_remaps_segment_colors() -> None:
    poly, _ = _polygon(closed=False)
    poly.set_segment_colors(["#a", "#b"])
    asyncio.run(poly._dispatch_vertex_drag(0, _ctrl_event(-1.0, 0.0)))
    assert poly.segment_colors == [None, "#a", "#b"]


def test_fuse_preserves_closing_segment_color() -> None:
    poly = ActPolygon(
        [Point(0.0, 0.0, 0.0), Point(10.0, 0.0, 0.0), Point(10.0, 10.0, 0.0)],
        closed=False,
        auto_close=True,
        show_translate_handle=False,
    )
    handle = _FakeHandle(space_dim=2)
    poly._init(handle, "p1")
    poly.set_segment_colors(["#a", "#b"])
    asyncio.run(poly._dispatch_vertex_drag(2, DragEvent(world_position=Point(0.0, 0.0, 0.0))))
    assert poly.closed is True
    assert poly.segment_colors == ["#a", "#b"]


def test_segment_color_changes_do_not_fire_on_change() -> None:
    seen: list[list[Point]] = []
    poly, _ = _polygon(on_change=seen.append)
    poly.set_segment_colors([None, None, None])
    poly.set_segment_color(0, "#ff0000")
    poly.clear_segment_color(0)
    assert seen == []
