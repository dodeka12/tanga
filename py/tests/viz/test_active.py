# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for active scene objects (:class:`ActSceneObject` / :class:`ActPoint`)."""

import asyncio
import json

import pytest

from pytanga.geometry import Direction, Point
from pytanga.viz._act_style import ActPointStyle
from pytanga.viz._active import ActiveObject, ActPoint, ClickBinding, DragBinding
from pytanga.viz._interaction import (
    DragEvent,
    DragMode,
    InteractionEventType,
    ModifierKey,
    MouseButton,
)
from pytanga.viz import SliderView
from pytanga.viz.visualizer import Visualizer


class _FakeStyles:
    """Minimal stand-in for ``VizSceneHandle.styles``."""

    def __init__(self) -> None:
        self.act_point = ActPointStyle()


class _FakeSceneConfig:
    """Minimal stand-in for ``SceneConfig.space_dim``."""

    def __init__(self, space_dim: int | None) -> None:
        self.space_dim = space_dim


class _FakeScene:
    """Minimal stand-in for ``VizSceneHandle.scene``."""

    def __init__(self, space_dim: int | None) -> None:
        self.config = _FakeSceneConfig(space_dim)


class _FakeSceneHandle:
    """Records the interaction calls :class:`ActPoint` makes via its handle."""

    def __init__(self, space_dim: int | None = None) -> None:
        self.styles = _FakeStyles()
        self.scene = _FakeScene(space_dim)
        self.configs: list[tuple[str, object]] = []
        self.handlers: dict[InteractionEventType, object] = {}
        self.updates: list[tuple[str, Point]] = []
        self.style_updates: list[tuple[str, object]] = []
        self.visibility: list[tuple[str, bool]] = []
        self.flushes = 0

    def set_interaction(self, object_id: str, config: object) -> None:
        self.configs.append((object_id, config))

    def on_interaction(
        self, object_id: str, event_type: InteractionEventType, handler: object
    ) -> None:
        self.handlers[event_type] = handler

    def update_entity(self, object_id: str, entity: Point) -> None:
        self.updates.append((object_id, entity))

    def update_style(self, object_id: str, style: object) -> None:
        self.style_updates.append((object_id, style))

    def set_visible(self, object_id: str, visible: bool) -> None:
        self.visibility.append((object_id, visible))

    def flush(self) -> None:
        self.flushes += 1


def _init_point(**kwargs) -> tuple[ActPoint, _FakeSceneHandle]:  # noqa: ANN003
    """Create and initialise an :class:`ActPoint` with a fake handle."""
    handle = _FakeSceneHandle()
    ap = ActPoint(1, 2, 3, **kwargs)
    ap._init(handle, "pt1")
    return ap, handle


def _init_point_2d(**kwargs) -> tuple[ActPoint, _FakeSceneHandle]:  # noqa: ANN003
    """Create and initialise an :class:`ActPoint` in a 2D scene."""
    handle = _FakeSceneHandle(space_dim=2)
    ap = ActPoint(1, 2, 3, **kwargs)
    ap._init(handle, "pt1")
    return ap, handle


def _coords(p: Point) -> tuple[float, float, float]:
    return (p.x, p.y, p.z)


class TestInteractionRegistration:
    def test_registers_drag_move_by_default(self):  # noqa: ANN201
        ap, handle = _init_point()
        assert InteractionEventType.DRAG_MOVE in handle.handlers
        assert InteractionEventType.DRAG_START not in handle.handlers
        assert InteractionEventType.DRAG_END not in handle.handlers

    def test_registers_start_and_end_when_provided(self):  # noqa: ANN201
        async def on_start(event, ap):  # noqa: ANN001, ANN202
            pass

        async def on_end(event, ap):  # noqa: ANN001, ANN202
            pass

        ap, handle = _init_point(on_drag_start=on_start, on_drag_end=on_end)
        assert InteractionEventType.DRAG_MOVE in handle.handlers
        assert InteractionEventType.DRAG_START in handle.handlers
        assert InteractionEventType.DRAG_END in handle.handlers

    def test_registers_only_start_when_only_start_provided(self):  # noqa: ANN201
        async def on_start(event, ap):  # noqa: ANN001, ANN202
            pass

        ap, handle = _init_point(on_drag_start=on_start)
        assert InteractionEventType.DRAG_START in handle.handlers
        assert InteractionEventType.DRAG_END not in handle.handlers

    def test_sets_interaction_config(self):  # noqa: ANN201
        ap, handle = _init_point()
        assert len(handle.configs) == 1
        assert handle.configs[0][0] == "pt1"


class TestDragPhases:
    @pytest.mark.anyio
    async def test_drag_start_handler_receives_event_and_point(self):  # noqa: ANN201
        calls = []

        async def on_start(event, ap):  # noqa: ANN001, ANN202
            calls.append((event, ap))

        ap, handle = _init_point(on_drag_start=on_start)
        event = DragEvent(object_id="pt1", event_type=InteractionEventType.DRAG_START)
        await handle.handlers[InteractionEventType.DRAG_START](event)
        assert len(calls) == 1
        assert calls[0][0] is event
        assert calls[0][1] is ap

    @pytest.mark.anyio
    async def test_drag_end_handler_receives_event_and_point(self):  # noqa: ANN201
        calls = []

        async def on_end(event, ap):  # noqa: ANN001, ANN202
            calls.append((event, ap))

        ap, handle = _init_point(on_drag_end=on_end)
        event = DragEvent(object_id="pt1", event_type=InteractionEventType.DRAG_END)
        await handle.handlers[InteractionEventType.DRAG_END](event)
        assert len(calls) == 1
        assert calls[0][0] is event
        assert calls[0][1] is ap

    @pytest.mark.anyio
    async def test_drag_start_does_not_move_point(self):  # noqa: ANN201
        async def on_start(event, ap):  # noqa: ANN001, ANN202
            pass

        ap, handle = _init_point(on_drag_start=on_start)
        before = _coords(ap.point)
        event = DragEvent(
            object_id="pt1",
            event_type=InteractionEventType.DRAG_START,
            world_position=Point(9, 9, 9),
        )
        await handle.handlers[InteractionEventType.DRAG_START](event)
        assert _coords(ap.point) == before
        assert handle.updates == []
        assert handle.flushes == 0

    @pytest.mark.anyio
    async def test_drag_move_moves_point_and_flushes(self):  # noqa: ANN201
        ap, handle = _init_point()
        event = DragEvent(
            object_id="pt1",
            event_type=InteractionEventType.DRAG_MOVE,
            world_position=Point(4, 5, 6),
        )
        await handle.handlers[InteractionEventType.DRAG_MOVE](event)
        assert _coords(ap.point) == (4, 5, 6)
        assert len(handle.updates) == 1
        assert handle.updates[0][0] == "pt1"
        assert _coords(handle.updates[0][1]) == (4, 5, 6)
        assert handle.flushes == 1

    @pytest.mark.anyio
    async def test_custom_move_handler_can_suppress_default(self):  # noqa: ANN201
        async def handler(event, ap):  # noqa: ANN001, ANN202
            return True

        ap, handle = _init_point(handler=handler)
        event = DragEvent(
            object_id="pt1",
            event_type=InteractionEventType.DRAG_MOVE,
            world_position=Point(7, 8, 9),
        )
        await handle.handlers[InteractionEventType.DRAG_MOVE](event)
        assert _coords(ap.point) == (1, 2, 3)
        assert handle.updates == []
        assert handle.flushes == 0


class TestDragModeConstraint:
    def test_drag_mode_sets_primary_trigger(self):  # noqa: ANN201
        ap, handle = _init_point(drag_mode=DragMode.XY_PLANE)
        config = handle.configs[0][1]
        assert len(config.triggers) == 1
        trigger = config.triggers[0]
        assert trigger.event_type == InteractionEventType.DRAG
        assert trigger.mouse_button == MouseButton.LEFT
        assert trigger.drag_mode == DragMode.XY_PLANE
        assert trigger.modifiers == frozenset()

    def test_drag_mode_omits_modifier_triggers(self):  # noqa: ANN201
        ap, handle = _init_point(drag_mode=DragMode.XY_PLANE)
        config = handle.configs[0][1]
        modes = {t.drag_mode for t in config.triggers}
        assert modes == {DragMode.XY_PLANE}
        assert all(t.modifiers == frozenset() for t in config.triggers)

    def test_drag_mode_none_keeps_four_default_triggers(self):  # noqa: ANN201
        ap, handle = _init_point()
        config = handle.configs[0][1]
        assert len(config.triggers) == 4
        modes = {t.drag_mode for t in config.triggers}
        assert modes == {
            DragMode.VIEW_PLANE,
            DragMode.XY_PLANE,
            DragMode.XZ_PLANE,
            DragMode.YZ_PLANE,
        }
        # Unmodified trigger remains view-plane.
        unmodified = [t for t in config.triggers if t.modifiers == frozenset()]
        assert len(unmodified) == 1
        assert unmodified[0].drag_mode == DragMode.VIEW_PLANE

    def test_drag_mode_serializes_for_frontend(self):  # noqa: ANN201
        ap, handle = _init_point(drag_mode=DragMode.XY_PLANE)
        config = handle.configs[0][1]
        d = config.to_dict()
        assert len(d["triggers"]) == 1
        assert d["triggers"][0]["drag_mode"] == "xy_plane"
        assert d["triggers"][0]["modifiers"] == []

    def test_drag_mode_keeps_lifecycle_handlers(self):  # noqa: ANN201
        async def on_start(event, ap):  # noqa: ANN001, ANN202
            pass

        async def on_end(event, ap):  # noqa: ANN001, ANN202
            pass

        async def handler(event, ap):  # noqa: ANN001, ANN202
            return False

        ap, handle = _init_point(
            drag_mode=DragMode.XY_PLANE,
            handler=handler,
            on_drag_start=on_start,
            on_drag_end=on_end,
        )
        assert InteractionEventType.DRAG_MOVE in handle.handlers
        assert InteractionEventType.DRAG_START in handle.handlers
        assert InteractionEventType.DRAG_END in handle.handlers

    def test_2d_defaults_to_xy_plane(self):  # noqa: ANN201
        ap, handle = _init_point_2d()
        config = handle.configs[0][1]
        assert len(config.triggers) == 1
        trigger = config.triggers[0]
        assert trigger.event_type == InteractionEventType.DRAG
        assert trigger.mouse_button == MouseButton.LEFT
        assert trigger.drag_mode == DragMode.XY_PLANE
        assert trigger.modifiers == frozenset()

    def test_explicit_drag_mode_overrides_2d_default(self):  # noqa: ANN201
        ap, handle = _init_point_2d(drag_mode=DragMode.VIEW_PLANE)
        config = handle.configs[0][1]
        assert len(config.triggers) == 1
        assert config.triggers[0].drag_mode == DragMode.VIEW_PLANE

    def test_3d_keeps_four_default_triggers(self):  # noqa: ANN201
        handle = _FakeSceneHandle(space_dim=3)
        ap = ActPoint(1, 2, 3)
        ap._init(handle, "pt1")
        config = handle.configs[0][1]
        assert len(config.triggers) == 4
        modes = {t.drag_mode for t in config.triggers}
        assert modes == {
            DragMode.VIEW_PLANE,
            DragMode.XY_PLANE,
            DragMode.XZ_PLANE,
            DragMode.YZ_PLANE,
        }


class TestDragModifiers:
    def test_default_drag_trigger_is_unmodified(self):  # noqa: ANN201
        ap, handle = _init_point(drag_mode=DragMode.XY_PLANE)
        config = ap.interaction_config
        assert config.triggers[0].modifiers == frozenset()

    def test_set_drag_modifiers_gates_single_trigger(self):  # noqa: ANN201
        ap, handle = _init_point(drag_mode=DragMode.XY_PLANE)
        ap.set_drag_modifiers(ModifierKey.SHIFT)
        config = ap.interaction_config
        assert len(config.triggers) == 1
        assert config.triggers[0].modifiers == frozenset({ModifierKey.SHIFT})

    def test_set_drag_modifiers_no_args_resets(self):  # noqa: ANN201
        ap, handle = _init_point(drag_mode=DragMode.XY_PLANE)
        ap.set_drag_modifiers(ModifierKey.SHIFT)
        ap.set_drag_modifiers()
        config = ap.interaction_config
        assert config.triggers[0].modifiers == frozenset()

    def test_set_drag_modifiers_repushes_interaction(self):  # noqa: ANN201
        ap, handle = _init_point(drag_mode=DragMode.XY_PLANE)
        before = len(handle.configs)
        ap.set_drag_modifiers(ModifierKey.CTRL)
        assert len(handle.configs) == before + 1
        assert handle.configs[-1][1].triggers[0].modifiers == frozenset(
            {ModifierKey.CTRL}
        )



class TestActPointLabel:
    def test_add_with_label(self):  # noqa: ANN201
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        ap = ActPoint(1, 2, 3)
        eid = viz.add(ap, label="P")
        assert viz.get_label_ids(eid)  # a label is attached to the point

        # Removing the point also removes its attached label.
        viz.remove(eid)
        viz._scene.flush()
        assert viz._scene.entity_count == 0


class TestDragAnchor:
    def test_act_point_drag_anchor_returns_centre(self):  # noqa: ANN201
        handle = _FakeSceneHandle()
        ap = ActPoint(Point(0, 2, 0))
        ap._init(handle, "pt1")
        assert ap.drag_anchor(Point(9, 9, 9), Direction(1, 0, 0)) == Point(0, 2, 0)

    def test_dispatch_sends_anchor(self):  # noqa: ANN201
        class _RecordingServer:
            def __init__(self):  # noqa: ANN204
                self.sent = []

            async def push_raw_to_browser(self, browser_id, data):  # noqa: ANN001, ANN202
                self.sent.append((browser_id, data))

        async def _run():  # noqa: ANN202
            viz = Visualizer(add_default_axes=False, add_default_grid=False)
            server = _RecordingServer()
            viz._server = server

            handle = _FakeSceneHandle()
            ap = ActPoint(Point(0, 2, 0))
            ap._init(handle, "pt1")
            viz._act_objects["pt1"] = ap

            await viz._dispatch_interaction_event(
                "interaction:drag_start",
                {
                    "type": "interaction:drag_start",
                    "event_type": "drag_start",
                    "object_id": "pt1",
                    "browser_id": "b1",
                    "ray_origin": [9.0, 9.0, 9.0],
                    "ray_direction": [0.0, 0.0, 1.0],
                },
            )

            assert len(server.sent) == 1
            browser_id, data = server.sent[0]
            assert browser_id == "b1"
            assert json.loads(data) == {
                "type": "interaction:drag_anchor",
                "object_id": "pt1",
                "world_position": [0.0, 2.0, 0.0],
            }

        asyncio.run(_run())

    def test_drag_start_handler_receives_ideal_anchor(self):  # noqa: ANN201
        class _RecordingServer:
            def __init__(self):  # noqa: ANN204
                self.sent = []

            async def push_raw_to_browser(self, browser_id, data):  # noqa: ANN001, ANN202
                self.sent.append((browser_id, data))

        async def _run():  # noqa: ANN202
            viz = Visualizer(add_default_axes=False, add_default_grid=False)
            viz._server = _RecordingServer()

            received: list[Point] = []

            async def on_drag_start(event):  # noqa: ANN001, ANN202
                received.append(event.world_position)

            handle = _FakeSceneHandle()
            ap = ActPoint(Point(0, 2, 0))
            ap._init(handle, "pt1")
            viz._act_objects["pt1"] = ap
            viz.on_interaction("pt1", InteractionEventType.DRAG_START, on_drag_start)

            # The reported world_position is the mesh-surface hit (off-plane in
            # 2D); the handler must instead observe the ideal point's centre.
            await viz._dispatch_interaction_event(
                "interaction:drag_start",
                {
                    "type": "interaction:drag_start",
                    "event_type": "drag_start",
                    "object_id": "pt1",
                    "browser_id": "b1",
                    "world_position": [0.0, 2.0, 0.15],
                    "world_delta": [0.0, 0.0, 0.0],
                    "ray_origin": [9.0, 9.0, 9.0],
                    "ray_direction": [0.0, 0.0, 1.0],
                },
            )

            # The handler is dispatched via asyncio.create_task; yield so it runs.
            await asyncio.sleep(0)

            assert received == [Point(0, 2, 0)]

        asyncio.run(_run())


class TestClickHandler:
    _IDENTITY = [
        1.0,
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
    ]

    def test_click_trigger_added_when_on_click(self):  # noqa: ANN201
        async def on_click(event, act):  # noqa: ANN001, ANN202
            pass

        ap = ActPoint(Point(0, 2, 0), on_click=on_click)
        cfg = ap.interaction_config
        assert any(t.event_type == InteractionEventType.CLICK for t in cfg.triggers)

        ap_no_click = ActPoint(Point(0, 2, 0))
        cfg_no_click = ap_no_click.interaction_config
        assert not any(
            t.event_type == InteractionEventType.CLICK for t in cfg_no_click.triggers
        )

    def test_click_handler_receives_ideal_anchor(self):  # noqa: ANN201
        class _RecordingServer:
            def __init__(self):  # noqa: ANN204
                self.sent = []

            async def push_raw_to_browser(self, browser_id, data):  # noqa: ANN001, ANN202
                self.sent.append((browser_id, data))

        async def _run():  # noqa: ANN202
            viz = Visualizer(add_default_axes=False, add_default_grid=False)
            viz._server = _RecordingServer()

            received: list[Point] = []

            async def on_click(event, act):  # noqa: ANN001, ANN202
                received.append(event.world_position)

            handle = _FakeSceneHandle()
            ap = ActPoint(Point(0, 2, 0), on_click=on_click)
            ap._init(handle, "pt1")
            viz._act_objects["pt1"] = ap
            viz.on_interaction("pt1", InteractionEventType.CLICK, ap._on_click_event)

            # world_position is the mesh-surface hit (off-plane in 2D); the
            # handler must instead observe the ideal point's centre.
            await viz._dispatch_interaction_event(
                "interaction:click",
                {
                    "type": "interaction:click",
                    "event_type": "click",
                    "object_id": "pt1",
                    "browser_id": "b1",
                    "screen_position": [400.0, 300.0],
                    "world_position": [0.0, 2.0, 0.15],
                    "world_normal": [0.0, 0.0, 1.0],
                    "ray_origin": [9.0, 9.0, 9.0],
                    "ray_direction": [0.0, 0.0, 1.0],
                    "camera": {
                        "view": TestClickHandler._IDENTITY,
                        "view_inv": TestClickHandler._IDENTITY,
                        "proj": TestClickHandler._IDENTITY,
                        "proj_inv": TestClickHandler._IDENTITY,
                        "viewport_width": 800,
                        "viewport_height": 600,
                        "space_dim": 3,
                    },
                },
            )

            # The handler is dispatched via asyncio.create_task; yield so it runs.
            await asyncio.sleep(0)

            assert received == [Point(0, 2, 0)]

        asyncio.run(_run())


class TestBindings:
    def test_drag_binding_adds_trigger_with_modifiers(self):  # noqa: ANN201
        async def on_drag(event, act):  # noqa: ANN001, ANN202
            return True

        ap = ActPoint(
            Point(0, 2, 0),
            drag_bindings=[DragBinding(MouseButton.LEFT, on_drag, ModifierKey.CTRL)],
        )
        cfg = ap.interaction_config
        drag_triggers = [
            t for t in cfg.triggers if t.event_type == InteractionEventType.DRAG
        ]
        assert any(
            t.mouse_button == MouseButton.LEFT
            and t.modifiers == frozenset({ModifierKey.CTRL})
            for t in drag_triggers
        )

    def test_click_binding_adds_trigger_with_button_and_modifiers(self):  # noqa: ANN201
        async def on_click(event, act):  # noqa: ANN001, ANN202
            pass

        ap = ActPoint(
            Point(0, 2, 0),
            click_bindings=[
                ClickBinding(MouseButton.RIGHT, on_click, ModifierKey.CTRL)
            ],
        )
        cfg = ap.interaction_config
        click_triggers = [
            t for t in cfg.triggers if t.event_type == InteractionEventType.CLICK
        ]
        assert any(
            t.mouse_button == MouseButton.RIGHT
            and t.modifiers == frozenset({ModifierKey.CTRL})
            for t in click_triggers
        )

    def test_no_bindings_has_no_binding_triggers(self):  # noqa: ANN201
        ap = ActPoint(Point(0, 2, 0))
        cfg = ap.interaction_config
        # A plain ActPoint registers only the standard drag triggers (no CLICK
        # trigger and no button-specific binding triggers).
        assert all(
            t.event_type != InteractionEventType.CLICK for t in cfg.triggers
        )


def test_on_interaction_registers_in_unified_registry():  # noqa: ANN201
    viz = Visualizer(add_default_axes=False, add_default_grid=False)

    async def handler(event):  # noqa: ANN001, ANN202
        pass

    viz.on_interaction("obj1", InteractionEventType.CLICK, handler)
    assert viz._handler_registry.get("obj1", "click") is handler


class TestEnabled:
    def test_defaults_enabled(self):  # noqa: ANN201
        ap, handle = _init_point()
        assert ap._enabled is True
        assert handle.configs[-1][1].enabled is True

    def test_disable_re_registers_with_enabled_false(self):  # noqa: ANN201
        ap, handle = _init_point()
        n_before = len(handle.configs)
        ap.disable()
        assert ap._enabled is False
        assert len(handle.configs) == n_before + 1
        assert handle.configs[-1][1].enabled is False
        # Triggers are retained (only the master switch is off).
        assert handle.configs[-1][1].triggers

    def test_enable_restores(self):  # noqa: ANN201
        ap, handle = _init_point()
        ap.disable()
        ap.enable()
        assert ap._enabled is True
        assert handle.configs[-1][1].enabled is True


class TestActiveObjectBase:
    def test_act_point_is_active_object(self) -> None:
        ap = ActPoint(1, 2, 3)
        assert isinstance(ap, ActiveObject)

    def test_act_point_reshape_handles_is_self(self) -> None:
        ap, _ = _init_point()
        assert ap._reshape_handles() == [ap]
        assert ap._all_handles() == [ap]

    def test_set_handles_enabled_disables_point(self) -> None:
        ap, handle = _init_point()
        ap.set_handles_enabled(False)
        assert ap._enabled is False
        assert handle.style_updates == []

    def test_set_handles_enabled_swaps_style(self) -> None:
        h = object()
        s = object()
        ap, handle = _init_point(handle_style=h, style=s)
        ap.set_handles_enabled(False)
        assert ap._enabled is False
        assert ("pt1", s) in handle.style_updates
        ap.set_handles_enabled(True)
        assert ap._enabled is True
        assert ("pt1", h) in handle.style_updates

    def test_set_handles_visible_hides_and_disables_point(self) -> None:
        ap, handle = _init_point()
        ap.set_handles_visible(False)
        assert ("pt1", False) in handle.visibility
        assert ap._enabled is False

