# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the interactive image plane (`ActImagePlane`)."""

from __future__ import annotations

from pytanga.geometry import Direction, Point
from pytanga.viz import ActImagePlane, ImageView
from pytanga.viz._interaction import DragMode, InteractionEventType, MouseButton


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
    def test_default_drag_trigger(self) -> None:
        ap = ActImagePlane(_view())
        cfg = ap.interaction_config
        assert cfg.enabled is True
        assert len(cfg.triggers) == 1
        trigger = cfg.triggers[0]
        assert trigger.event_type is InteractionEventType.DRAG
        assert trigger.mouse_button is MouseButton.LEFT
        assert trigger.drag_mode is DragMode.XY_PLANE

    def test_click_trigger_only_when_handler(self) -> None:
        async def on_click(event, ap):  # noqa: ANN001, ANN202
            pass

        ap = ActImagePlane(_view(), on_click=on_click)
        cfg = ap.interaction_config
        assert len(cfg.triggers) == 2
        assert cfg.triggers[1].event_type is InteractionEventType.CLICK

    def test_custom_drag_button(self) -> None:
        from pytanga.viz._interaction import ModifierKey

        ap = ActImagePlane(
            _view(),
            drag_button=MouseButton.RIGHT,
            drag_modifiers=frozenset({ModifierKey.CTRL}),
        )
        trigger = ap.interaction_config.triggers[0]
        assert trigger.mouse_button is MouseButton.RIGHT
        assert trigger.modifiers == frozenset({ModifierKey.CTRL})


class TestEntity:
    def test_entity_is_the_image_view(self) -> None:
        view = _view()
        ap = ActImagePlane(view)
        assert ap.entity is view
        assert ap.image_view is view
