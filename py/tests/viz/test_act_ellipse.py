# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for `ActEllipse` (interactive ellipse)."""

from __future__ import annotations

import asyncio
import math
from typing import Any

from pytanga.geometry import Direction, Ellipse, Point
from pytanga.viz import ActEllipse, DragEvent, ModifierKey
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


class TestPlaneZ:
    """Handles stay on the body's plane (z), not snapping to z=0."""

    def test_handles_preserve_plane_z(self) -> None:
        handle = _FakeHandle(space_dim=3)
        ellipse = ActEllipse(
            center=Point(5.0, 5.0, -0.6), radius_u=10.0, radius_v=4.0
        )
        ellipse._init(handle, "e1")
        for h in ellipse._radius_handles:
            assert h.point.z == -0.6
        assert ellipse._translate_handle.point.z == -0.6
        assert ellipse._rotate_handle.point.z == -0.6

    def test_translate_preserves_z(self) -> None:
        handle = _FakeHandle(space_dim=3)
        ellipse = ActEllipse(
            center=Point(5.0, 5.0, -0.6), radius_u=10.0, radius_v=4.0
        )
        ellipse._init(handle, "e1")
        asyncio.run(
            ellipse._dispatch_translate(DragEvent(world_delta=Direction(1.0, 1.0, 0.0)))
        )
        assert ellipse.entity.center == Point(6.0, 6.0, -0.6)



class TestLimits:
    """Resize clamps: explicit min/max, and fp-precision when ``None``."""

    def test_no_default_floor_when_min_none(self) -> None:
        handle = _FakeHandle(space_dim=3)
        ellipse = ActEllipse(center=Point(0.0, 0.0, 0.0), radius_u=0.02, radius_v=0.02)
        ellipse._init(handle, "e1")
        asyncio.run(
            ellipse._dispatch_radius_drag(
                0, DragEvent(world_position=Point(0.001, 0.0, 0.0))
            )
        )
        assert ellipse.ellipse.radius_u == 0.001

    def test_min_radius_clamps(self) -> None:
        handle = _FakeHandle(space_dim=3)
        ellipse = ActEllipse(
            center=Point(0.0, 0.0, 0.0), radius_u=1.0, radius_v=1.0, min_radius=0.5
        )
        ellipse._init(handle, "e1")
        asyncio.run(
            ellipse._dispatch_radius_drag(
                0, DragEvent(world_position=Point(0.1, 0.0, 0.0))
            )
        )
        assert ellipse.ellipse.radius_u == 0.5

    def test_max_radius_caps(self) -> None:
        handle = _FakeHandle(space_dim=3)
        ellipse = ActEllipse(
            center=Point(0.0, 0.0, 0.0), radius_u=1.0, radius_v=1.0, max_radius=2.0
        )
        ellipse._init(handle, "e1")
        asyncio.run(
            ellipse._dispatch_radius_drag(
                0, DragEvent(world_position=Point(5.0, 0.0, 0.0))
            )
        )
        assert ellipse.ellipse.radius_u == 2.0



class TestCreateClamp:
    def test_create_from_points_clamps_to_min_radius(self) -> None:
        ellipse = ActEllipse.create_from_points(
            Point(0.0, 0.0, 0.0), Point(0.001, 0.0001, 0.0), min_radius=0.5
        )
        assert ellipse.ellipse.radius_u == 0.5
        assert ellipse.ellipse.radius_v == 0.5


class TestHandleControls:
    def test_set_handles_enabled_disables_all(self) -> None:
        ellipse, handle = _ellipse()
        ellipse.set_handles_enabled(False)
        assert all(h._enabled is False for h in ellipse._all_handles())

    def test_set_handles_visible_hides_and_disables_all(self) -> None:
        ellipse, handle = _ellipse()
        ellipse.set_handles_visible(False)
        for h in ellipse._all_handles():
            assert (h.entity_id, False) in handle.visibility
            assert h._enabled is False

    def test_set_drag_modifiers_gates_all(self) -> None:
        ellipse, handle = _ellipse()
        ellipse.set_drag_modifiers(ModifierKey.SHIFT)
        assert all(
            h._required_drag_modifiers == frozenset({ModifierKey.SHIFT})
            for h in ellipse._all_handles()
        )


class TestRotateHandleOffset:
    def test_rotate_handle_independent_of_perpendicular_axis(self) -> None:
        handle = _FakeHandle(space_dim=2)
        ellipse = ActEllipse(
            center=Point(0.0, 0.0, 0.0), radius_u=10.0, radius_v=100.0
        )
        ellipse._init(handle, "e1")
        before = ellipse._rotate_handle_position()

        ellipse._radius_v = 200.0
        after = ellipse._rotate_handle_position()

        assert (after.x, after.y, after.z) == (before.x, before.y, before.z)

