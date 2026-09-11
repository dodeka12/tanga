# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the Visualizer layout registry + URL plumbing (``set_layout``)."""

import asyncio
import json

import pytest

from pytanga.viz import (
    ButtonView,
    CameraConfig3d,
    GroupView,
    MenuView,
    SceneView,
    SliderView,
    SplitView,
    Visualizer,
)
from pytanga.viz.views import serialize_layout


def _layout():
    return SplitView("horizontal", [SceneView("a"), SceneView("b")])


class TestSetLayout:
    def test_register_and_serialize(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        layout = _layout()
        name = viz.set_layout(layout, name="demo")
        assert name == "demo"
        assert viz._layouts["demo"].base is layout
        assert viz._layouts_serialized["demo"] == serialize_layout(layout, name="demo")

    def test_default_name(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        assert viz.set_layout(_layout()) == ""

    def test_overwrite(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        a = SceneView("a")
        b = SceneView("b")
        viz.set_layout(a, name="x")
        viz.set_layout(b, name="x")
        assert viz._layouts["x"].base is b

    def test_rejects_non_view(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        with pytest.raises(TypeError, match="must be a View"):
            viz.set_layout("nope")

    def test_layout_serialized_for_missing(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        assert viz._layout_serialized_for("missing") is None


class TestControlHandlerRegistration:
    @staticmethod
    async def _noop(value, event):
        return None

    def test_slider_handler_registered(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        layout = SplitView(
            "horizontal",
            [SceneView("a"), GroupView("g", [SliderView("s1", on_change=self._noop)])],
        )
        viz.set_layout(layout)
        assert viz._handler_registry.get("s1") is self._noop

    def test_button_handler_registered(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        viz.set_layout(GroupView("g", [ButtonView("b1", on_click=self._noop)]))
        assert viz._handler_registry.get("b1", "click") is self._noop

    def test_no_handler_not_registered(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        viz.set_layout(GroupView("g", [ButtonView("b1")]))
        assert viz._handler_registry.get("b1") is None

    def test_overwrite_removes_stale_handler(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        viz.set_layout(GroupView("g", [ButtonView("b1", on_click=self._noop)]))
        assert viz._handler_registry.get("b1", "click") is self._noop
        viz.set_layout(SplitView("horizontal", [SceneView("a"), SceneView("b")]))
        assert viz._handler_registry.get("b1") is None


class TestSetValuePush:
    def test_view_set_value_pushes_control_update(self, monkeypatch):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        view = SliderView("radius", value=1.0)
        viz.set_layout(view)

        server = _FakeServer()
        monkeypatch.setattr(viz, "_server", server)
        monkeypatch.setattr(viz, "_loop", object())
        monkeypatch.setattr(
            asyncio,
            "run_coroutine_threadsafe",
            lambda coro, loop: asyncio.run(coro),
        )

        view.set_value(3.5)

        assert view.value == 3.5
        msg = json.loads(server.captured[0])
        assert msg == {
            "type": "control_update",
            "scene": "",
            "id": "radius",
            "value": 3.5,
        }

    def test_view_set_value_unmounted_only_mutates(self):
        view = SliderView("radius", value=1.0)
        assert view._push is None  # not yet mounted → no push callback
        view.set_value(3.5)
        assert view.value == 3.5


class TestShowLayout:
    def test_show_layout_registers_and_opens(self, monkeypatch):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        layout = _layout()
        opened = {}
        monkeypatch.setattr(viz, "_server", object())
        monkeypatch.setattr(
            viz,
            "_open_layout_browser",
            lambda name, wait_for_browser, timeout=None: opened.setdefault(
                "name", name
            ),
        )

        viz.show(layout=layout, layout_name="demo")

        assert viz._layouts["demo"].base is layout
        assert opened["name"] == "demo"

    def test_show_layout_default_name(self, monkeypatch):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        opened = {}
        monkeypatch.setattr(viz, "_server", object())
        monkeypatch.setattr(
            viz,
            "_open_layout_browser",
            lambda name, wait_for_browser, timeout=None: opened.setdefault(
                "name", name
            ),
        )

        viz.show(layout=_layout())

        assert opened["name"] == ""


class TestOpenLayoutBrowser:
    def test_builds_layout_url(self, monkeypatch):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        viz._server = object()
        captured = {}
        monkeypatch.setattr(
            viz,
            "_open_browser_url",
            lambda url, wait_for_browser, timeout=None: captured.setdefault("url", url),
        )

        viz._open_layout_browser("demo", wait_for_browser=False)

        assert captured["url"].startswith("/?view=demo&token=")


class _FakeServer:
    def __init__(self):
        self.captured = []

    async def push_raw(self, data):
        self.captured.append(data)


class TestSetViewCamera:
    def test_rejects_non_scene_view(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        with pytest.raises(TypeError, match="must be a SceneView"):
            viz.set_view_camera(ButtonView("b"), CameraConfig3d())

    def test_updates_view_and_pushes_message(self, monkeypatch):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        view = SceneView("main")
        viz.set_layout(SplitView("horizontal", [view, SceneView("side")]))

        server = _FakeServer()
        monkeypatch.setattr(viz, "_server", server)
        monkeypatch.setattr(viz, "_loop", object())
        monkeypatch.setattr(
            asyncio,
            "run_coroutine_threadsafe",
            lambda coro, loop: asyncio.run(coro),
        )

        viz.set_view_camera(view, CameraConfig3d(position=(1, 2, 3), target=(0, 0, 0)))

        assert view.camera is not None
        msg = json.loads(server.captured[0])
        assert msg["type"] == "view_camera"
        assert msg["view_id"] == view.id
        assert msg["camera"]["position"] == [1.0, 2.0, 3.0]


class TestMenuApi:
    def test_serialize_layout_overlay_omitted_when_empty(self):
        node = serialize_layout(SceneView("a"))
        assert "overlay" not in node

    def test_serialize_layout_overlay_included(self):
        node = serialize_layout(SceneView("a"), overlay=[MenuView("Menu")])
        assert node["overlay"][0]["type"] == "menu"


class TestSceneLayoutFor:
    def test_base_scene_returns_stack_wrapping_main_scene_view(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        payload = viz._scene_layout_for("")
        assert payload["type"] == "view_layout"
        assert payload["root"]["type"] == "stack"
        scene_node = payload["root"]["children"][0]
        assert scene_node["type"] == "scene_view"
        assert scene_node["scene"] == ""

    def test_named_scene_wraps_its_scene_view(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        viz.scene("detail")
        payload = viz._scene_layout_for("detail")
        assert payload["type"] == "view_layout"
        assert payload["root"]["type"] == "stack"
        scene_node = payload["root"]["children"][0]
        assert scene_node["type"] == "scene_view"
        assert scene_node["scene"] == "detail"


class _FakeLayoutServer:
    def __init__(self, sessions):
        self._sessions = sessions
        self.pushed = []

    def get_browser_sessions(self):
        return list(self._sessions)

    async def push_layout_to_session(self, browser_id, payload):
        self.pushed.append((browser_id, payload))


class TestPushLayoutUpdates:
    def test_single_scene_session_gets_scene_layout(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        viz.scene("detail")
        viz._server = _FakeLayoutServer(
            [{"id": "b1", "scene": "detail", "layout": None}]
        )
        asyncio.run(viz._push_layout_updates())
        browser_id, payload = viz._server.pushed[0]
        assert browser_id == "b1"
        assert payload["root"]["children"][0]["scene"] == "detail"

    def test_layout_session_gets_named_layout(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        viz.set_layout(SceneView("a"), name="demo")
        viz._server = _FakeLayoutServer([{"id": "b1", "scene": "a", "layout": "demo"}])
        asyncio.run(viz._push_layout_updates())
        browser_id, payload = viz._server.pushed[0]
        assert browser_id == "b1"
        assert payload["name"] == "demo"


def test_layout_host_getitem_base_overlay():
    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    root = SceneView("a")
    viz.set_layout(root, name="demo")
    assert viz._layout["demo"].base is root
    assert viz._layout.base is viz._layout[""].base
    assert viz._layout.overlay is viz._layout[""].overlay


def test_add_layout_conflict_raises():
    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    viz.add_scene("a")
    with pytest.raises(ValueError):
        viz.add_layout(SceneView("b"), name="a")
    viz.add_layout(SceneView("a"), name="ab")
    assert viz._layout["ab"].base.scene == "a"


def test_add_polymorphic_view_goes_to_overlay():
    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    group = GroupView("panel", [SliderView("s")])
    assert viz.add(group) is None
    assert group in viz._layout._global_overlay


def test_add_global_overlay_sends_granular_define(monkeypatch):
    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    sent = []
    monkeypatch.setattr(viz._transport, "send", lambda msg: sent.append(msg))

    viz.add(GroupView("panel", [SliderView("s")]))

    assert [m["type"] for m in sent] == ["overlay_define"]
    # The cached layout is refreshed but no full `view_layout` is re-pushed.
    assert viz._layout._layouts_serialized[""]["overlay"][0]["type"] == "group"


def test_add_polymorphic_entity_goes_to_scene():
    from pytanga.geometry.entities import Point

    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    eid = viz.add(Point(0, 0, 0))
    assert eid in viz._layout.scene("")._objects


def test_views_have_stable_unique_ids():
    a = GroupView("a")
    b = GroupView("b")
    assert a.id and b.id
    assert a.id != b.id


def test_remove_global_overlay_sends_granular_remove(monkeypatch):
    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    group = GroupView("panel", [SliderView("s")])
    viz.add(group)

    sent = []
    monkeypatch.setattr(viz._transport, "send", lambda msg: sent.append(msg))
    viz.remove_view(group.id)

    assert [m["type"] for m in sent] == ["overlay_remove"]
    assert sent[0]["id"] == group.id
    assert group not in viz._layout._global_overlay
    assert "overlay" not in viz._layout._layouts_serialized[""]


def test_remove_global_overlay_unknown_id_is_noop(monkeypatch):
    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    viz.add(GroupView("panel", [SliderView("s")]))

    sent = []
    monkeypatch.setattr(viz._transport, "send", lambda msg: sent.append(msg))
    viz.remove_view("nope")

    assert sent == []
    assert len(viz._layout._global_overlay) == 1
