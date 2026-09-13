# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the interactive image plane (`ActImagePlane`)."""

from __future__ import annotations

import asyncio

from pytanga.geometry import Direction, Point
from pytanga.viz import (
    ActImagePlane,
    ClickBinding,
    ClickEvent,
    DragBinding,
    DragEvent,
    ImageView,
)
from pytanga.viz._interaction import (
    DragMode,
    InteractionEventType,
    ModifierKey,
    MouseButton,
)


def _view() -> ImageView:
    return ImageView("img1")


class TestDragAnchor:
    def test_vertical_ray_hits_origin_plane(self) -> None:
        ap = ActImagePlane(_view())
        hit = ap.drag_anchor(Point(2.0, 3.0, 10.0), Direction(0.0, 0.0, -1.0))
        assert (hit.x, hit.y, hit.z) == (2.0, 3.0, 0.0)

    def test_oblique_ray(self) -> None:
        ap = ActImagePlane(_view())
        # ray from (0, 0, 5) with direction (1, 2, -1): t = 5, hit = (5, 10, 0)
        hit = ap.drag_anchor(Point(0.0, 0.0, 5.0), Direction(1.0, 2.0, -1.0))
        assert (hit.x, hit.y, hit.z) == (5.0, 10.0, 0.0)

    def test_parallel_ray_falls_back_to_origin_xy(self) -> None:
        ap = ActImagePlane(_view())
        hit = ap.drag_anchor(Point(7.0, 8.0, 0.0), Direction(1.0, 0.0, 0.0))
        assert (hit.x, hit.y, hit.z) == (7.0, 8.0, 0.0)


class TestInteractionConfig:
    def test_no_handlers_no_triggers(self) -> None:
        ap = ActImagePlane(_view())
        cfg = ap.interaction_config
        assert cfg.enabled is True
        assert cfg.triggers == []

    def test_general_drag_handler_adds_catch_all(self) -> None:
        async def on_drag(event, ap):  # noqa: ANN001, ANN202
            return True

        ap = ActImagePlane(_view(), handler=on_drag)
        cfg = ap.interaction_config
        assert len(cfg.triggers) == 1
        trigger = cfg.triggers[0]
        assert trigger.event_type is InteractionEventType.DRAG
        assert trigger.mouse_button is None
        assert trigger.drag_mode is DragMode.XY_PLANE

    def test_drag_bindings_produce_specific_triggers(self) -> None:
        async def on_drag(event, ap):  # noqa: ANN001, ANN202
            return True

        ap = ActImagePlane(
            _view(),
            drag_bindings=[
                DragBinding(MouseButton.LEFT, on_drag, ModifierKey.CTRL),
                DragBinding(MouseButton.RIGHT, on_drag),
            ],
        )
        triggers = ap.interaction_config.triggers
        assert len(triggers) == 2
        assert triggers[0].event_type is InteractionEventType.DRAG
        assert triggers[0].mouse_button is MouseButton.LEFT
        assert triggers[0].modifiers == frozenset({ModifierKey.CTRL})
        assert triggers[1].mouse_button is MouseButton.RIGHT
        assert triggers[1].modifiers == frozenset()

    def test_click_bindings_and_general_click(self) -> None:
        async def on_click(event, ap):  # noqa: ANN001, ANN202
            pass

        ap = ActImagePlane(
            _view(),
            on_click=on_click,
            click_bindings=[
                ClickBinding(MouseButton.LEFT, on_click, ModifierKey.SHIFT)
            ],
        )
        triggers = ap.interaction_config.triggers
        assert len(triggers) == 2
        assert triggers[0].event_type is InteractionEventType.CLICK
        assert triggers[0].mouse_button is MouseButton.LEFT
        assert triggers[0].modifiers == frozenset({ModifierKey.SHIFT})
        assert triggers[1].event_type is InteractionEventType.CLICK
        assert triggers[1].mouse_button is None


class TestBindings:
    def test_drag_binding_variadic_modifiers(self) -> None:
        async def on_drag(event, ap):  # noqa: ANN001, ANN202
            return True

        binding = DragBinding(
            MouseButton.LEFT, on_drag, ModifierKey.CTRL, ModifierKey.SHIFT
        )
        assert binding.button is MouseButton.LEFT
        assert binding.modifiers == frozenset({ModifierKey.CTRL, ModifierKey.SHIFT})

    def test_click_binding_no_modifiers(self) -> None:
        async def on_click(event, ap):  # noqa: ANN001, ANN202
            pass

        binding = ClickBinding(MouseButton.RIGHT, on_click)
        assert binding.button is MouseButton.RIGHT
        assert binding.modifiers == frozenset()


class TestDispatch:
    def test_most_specific_binding_wins(self) -> None:
        calls: list[str] = []

        async def general(event, ap):  # noqa: ANN001, ANN202
            calls.append("general")
            return True

        async def plain(event, ap):  # noqa: ANN001, ANN202
            calls.append("plain")
            return True

        async def ctrl(event, ap):  # noqa: ANN001, ANN202
            calls.append("ctrl")
            return True

        ap = ActImagePlane(
            _view(),
            handler=general,
            drag_bindings=[
                DragBinding(MouseButton.LEFT, plain),
                DragBinding(MouseButton.LEFT, ctrl, ModifierKey.CTRL),
            ],
        )

        asyncio.run(
            ap._on_drag(
                DragEvent(
                    mouse_button=MouseButton.LEFT,
                    modifiers=frozenset({ModifierKey.CTRL}),
                    world_position=Point(1.0, 2.0, 0.0),
                )
            )
        )
        assert calls == ["ctrl"]

        calls.clear()
        asyncio.run(
            ap._on_drag(
                DragEvent(
                    mouse_button=MouseButton.LEFT, world_position=Point(1.0, 2.0, 0.0)
                )
            )
        )
        assert calls == ["plain"]

        calls.clear()
        asyncio.run(
            ap._on_drag(
                DragEvent(
                    mouse_button=MouseButton.RIGHT, world_position=Point(1.0, 2.0, 0.0)
                )
            )
        )
        assert calls == ["general"]

    def test_click_dispatch(self) -> None:
        calls: list[str] = []

        async def on_click(event, ap):  # noqa: ANN001, ANN202
            calls.append("click")

        ap = ActImagePlane(
            _view(),
            click_bindings=[ClickBinding(MouseButton.LEFT, on_click, ModifierKey.ALT)],
        )
        asyncio.run(
            ap._on_click_event(
                ClickEvent(
                    mouse_button=MouseButton.LEFT,
                    modifiers=frozenset({ModifierKey.ALT}),
                )
            )
        )
        assert calls == ["click"]


class TestEntity:
    def test_entity_is_the_image_view(self) -> None:
        view = _view()
        ap = ActImagePlane(view)
        assert ap.entity is view
        assert ap.image_view is view
