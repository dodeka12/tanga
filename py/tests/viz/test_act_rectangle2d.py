# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for `ActRectangle2D` (interactive rectangle)."""

from __future__ import annotations

import asyncio
import math
from typing import Any

from pytanga.geometry import Direction, Point, Rectangle2D
from pytanga.viz import ActPoint, ActRectangle2D, DragEvent, InteractionEventType
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
        self.visibility: list[tuple[str, bool]] = []
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

    def set_visible(self, object_id: str, visible: bool) -> None:
        self.visibility.append((object_id, visible))


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

    def test_interaction_config_clickable_with_on_click(self) -> None:
        async def on_click(event, rect):  # noqa: ANN001, ANN202
            pass

        rect = ActRectangle2D(
            center=Point(5.0, 5.0, 0.0), size=(10.0, 4.0), on_click=on_click
        )
        cfg = rect.interaction_config
        assert cfg.enabled is True
        assert any(t.event_type == InteractionEventType.CLICK for t in cfg.triggers)

    def test_body_style_from_constructor(self) -> None:
        from pytanga.viz import Rectangle2DStyle

        style = Rectangle2DStyle(color="#ff4444")
        rect = ActRectangle2D(center=Point(0.0, 0.0, 0.0), style=style)
        assert rect.body_style is style


class TestHandles:
    def test_spawns_six_handles(self) -> None:
        _, handle = _rect()
        assert len(handle.added) == 6  # 4 corners + 1 translate + 1 rotate

    def test_spawns_four_corners_only(self) -> None:
        rect = ActRectangle2D(
            center=Point(5.0, 5.0, 0.0),
            size=(10.0, 4.0),
            show_translate_handle=False,
            show_rotate_handle=False,
        )
        handle = _FakeHandle(space_dim=2)
        rect._init(handle, "r1")
        assert len(handle.added) == 4

    def test_translate_rotate_handles_are_twice_handle_size(self) -> None:
        from pytanga.viz import CirclePointStyle, IconPointStyle

        rect = ActRectangle2D(
            center=Point(5.0, 5.0, 0.0),
            size=(10.0, 4.0),
            handle_style=CirclePointStyle(size=2.0),
        )
        handle = _FakeHandle(space_dim=2)
        rect._init(handle, "r1")
        styles = [st for _, st in handle.added]
        translate_style = styles[4]
        rotate_style = styles[5]
        assert isinstance(translate_style, IconPointStyle)
        assert translate_style.size == 4.0
        assert translate_style.icon == "material:open_with"
        assert isinstance(rotate_style, IconPointStyle)
        assert rotate_style.size == 4.0
        assert rotate_style.icon == "material:rotate_right"

    def test_default_handles_are_screen_space(self) -> None:
        from pytanga.viz import CirclePointStyle, IconPointStyle

        rect = ActRectangle2D(center=Point(5.0, 5.0, 0.0), size=(10.0, 4.0))
        handle_style = rect._resolve_handle_style()
        translate_style = rect._resolve_translate_handle_style()
        rotate_style = rect._resolve_rotate_handle_style()
        assert isinstance(handle_style, CirclePointStyle)
        assert handle_style.screen_space is True
        assert handle_style.size == 6.0
        assert isinstance(translate_style, IconPointStyle)
        assert translate_style.screen_space is True
        assert translate_style.size == 12.0
        assert isinstance(rotate_style, IconPointStyle)
        assert rotate_style.screen_space is True
        assert rotate_style.size == 12.0

    def test_toggle_translate_rotate_handle_visibility(self) -> None:
        rect, handle = _rect()
        rect.set_translate_handle_visible(False)
        rect.set_rotate_handle_visible(False)
        assert ("h4", False) in handle.visibility  # translate handle
        assert ("h5", False) in handle.visibility  # rotate handle
        rect.set_translate_handle_visible(True)
        assert ("h4", True) in handle.visibility

    def test_handle_click_routes_to_parent_on_click(self) -> None:
        seen: list[object] = []

        async def on_click(event: object, act: object) -> None:  # noqa: ANN001
            seen.append(act)

        rect = ActRectangle2D(
            center=Point(5.0, 5.0, 0.0), size=(10.0, 4.0), on_click=on_click
        )
        handler = rect._handle_click_handler()
        asyncio.run(handler(None, None))  # type: ignore[arg-type]
        assert seen == [rect]


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

    def test_rotate_sets_angle(self) -> None:
        rect, _ = _rect()
        asyncio.run(
            rect._dispatch_rotate(DragEvent(world_position=Point(15.0, 15.0, 0.0)))
        )
        assert abs(rect.angle - math.pi / 4) < 1e-9
        assert abs(rect.entity.angle - math.pi / 4) < 1e-9

    def test_resize_preserves_angle(self) -> None:
        rect, _ = _rect(angle=math.pi / 2)
        asyncio.run(
            rect._dispatch_corner_drag(0, DragEvent(world_position=Point(2.0, 3.0, 0.0)))
        )
        assert abs(rect.angle - math.pi / 2) < 1e-9

    def test_min_size_clamps(self) -> None:
        rect, _ = _rect(min_size=2.0)
        asyncio.run(
            rect._dispatch_corner_drag(
                0, DragEvent(world_position=Point(9.9, 6.9, 0.0))
            )
        )
        assert rect.entity.size == (2.0, 2.0)

    def test_create_from_points(self) -> None:
        rect = ActRectangle2D.create_from_points(
            Point(0.0, 0.0, 0.0), Point(4.0, 2.0, 0.0)
        )
        assert rect.entity.center == Point(2.0, 1.0, 0.0)
        assert rect.entity.size == (4.0, 2.0)


class TestPlaneZ:
    """Handles stay on the body's plane (z), not snapping to z=0."""

    def test_handles_preserve_plane_z(self) -> None:
        handle = _FakeHandle(space_dim=3)
        rect = ActRectangle2D(center=Point(5.0, 5.0, -0.6), size=(10.0, 4.0))
        rect._init(handle, "r1")
        for h in rect._corner_handles:
            assert h.point.z == -0.6
        assert rect._translate_handle.point.z == -0.6
        assert rect._rotate_handle.point.z == -0.6

    def test_resize_corner_preserves_z(self) -> None:
        handle = _FakeHandle(space_dim=3)
        rect = ActRectangle2D(center=Point(5.0, 5.0, -0.6), size=(10.0, 4.0))
        rect._init(handle, "r1")
        asyncio.run(
            rect._dispatch_corner_drag(
                0, DragEvent(world_position=Point(0.0, 0.0, -0.6))
            )
        )
        assert rect.entity.center.z == -0.6

    def test_translate_preserves_z(self) -> None:
        handle = _FakeHandle(space_dim=3)
        rect = ActRectangle2D(center=Point(5.0, 5.0, -0.6), size=(10.0, 4.0))
        rect._init(handle, "r1")
        asyncio.run(
            rect._dispatch_translate(DragEvent(world_delta=Direction(1.0, 1.0, 0.0)))
        )
        assert rect.entity.center == Point(6.0, 6.0, -0.6)



class TestLimits:
    """Resize clamps: explicit min/max, and fp-precision when ``None``."""

    def test_max_size_caps(self) -> None:
        handle = _FakeHandle(space_dim=3)
        rect = ActRectangle2D(center=Point(0.0, 0.0, 0.0), size=(1.0, 1.0), max_size=2.0)
        rect._init(handle, "r1")
        asyncio.run(
            rect._dispatch_corner_drag(
                0, DragEvent(world_position=Point(5.0, 5.0, 0.0))
            )
        )
        assert rect.entity.size == (2.0, 2.0)




class TestCreateClamp:
    def test_create_from_points_clamps_to_min_size(self) -> None:
        rect = ActRectangle2D.create_from_points(
            Point(0.0, 0.0, 0.0), Point(0.001, 0.0001, 0.0), min_size=0.5
        )
        assert rect.entity.size == (0.5, 0.5)



class TestHandleVisibility:
    def test_hidden_rotate_handle_is_disabled(self) -> None:
        rect, _ = _rect()
        rect.set_rotate_handle_visible(False)
        assert rect._rotate_handle._enabled is False

    def test_hidden_translate_handle_is_disabled(self) -> None:
        rect, _ = _rect()
        rect.set_translate_handle_visible(False)
        assert rect._translate_handle._enabled is False


class TestPixelScale:
    def test_act_point_has_set_pixel_scale(self) -> None:
        ap = ActPoint(0, 0)
        assert ap._pixel_scale == 1.0
        ap.set_pixel_scale(0.5)
        assert ap._pixel_scale == 0.5

    def test_rectangle_uses_pixel_scale_for_rotate_offset(self) -> None:
        handle = _FakeHandle(space_dim=3)
        rect = ActRectangle2D(center=Point(0.0, 0.0, 0.0), size=(0.01, 0.01))
        rect._init(handle, "r1")
        rect.set_pixel_scale(1.0)
        offset = rect._rotate_handle_position()
        # offset >= 2 * handle_size * pixel_scale keeps the icon off the corner.
        assert offset.x >= 2.0 * 6.0 * 1.0

