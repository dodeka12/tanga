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
        assert viz._layouts["demo"] is layout
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
        assert viz._layouts["x"] is b

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


class TestAddControlGroup:
    @staticmethod
    async def _noop(value, event):
        return None

    def test_overlay_group(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        viz.add_slider("s", label="S", on_change=self._noop)
        viz.add_button("b", label="B", on_click=self._noop)
        gid = viz.add_control_group("g", title="G", controls=["s", "b"], position="top-right")
        assert gid == "g"
        group = viz._scene_groups[""]["g"]
        assert isinstance(group, GroupView)
        assert group in viz._global_overlay
        assert [c.id for c in group.children] == ["s", "b"]
        # No legacy ControlGroup remains in the scene.
        assert viz._scenes[""]._groups == {}
        assert viz._grouped_control_ids("") == {"s", "b"}
        overlay = viz._layouts_serialized[""]["overlay"]
        assert overlay[0]["type"] == "group"
        assert overlay[0]["title"] == "G"
        assert "parent_id" not in overlay[0]

    def test_parent_id_serializes_into_scene_overlay(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        viz.add_slider("s", label="S")
        assert viz.add_control_group("g", controls=["s"], parent_id="sphere") == "g"
        group = viz._scene_groups[""]["g"]
        # A parent_id group mounts per-pane (not in the global overlay).
        assert group not in viz._global_overlay
        assert group in viz._scene_overlays[""]
        scene_node = viz._layouts_serialized[""]["root"]["children"][0]
        assert scene_node["type"] == "scene_view"
        assert scene_node["children"][0]["type"] == "group"
        assert scene_node["children"][0]["parent_id"] == "sphere"

    def test_on_toggle_registered(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)

        async def _toggle(value, event):
            return None

        viz.add_control_group("g", controls=[], on_toggle=_toggle)
        assert viz._handler_registry.get("g", "toggle") is _toggle


class TestShowLayout:
    def test_show_layout_registers_and_opens(self, monkeypatch):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        layout = _layout()
        opened = {}
        monkeypatch.setattr(viz, "_server", object())
        monkeypatch.setattr(
            viz,
            "_open_layout_browser",
            lambda name, wait_for_browser, timeout=None: opened.setdefault("name", name),
        )

        viz.show(layout=layout, layout_name="demo")

        assert viz._layouts["demo"] is layout
        assert opened["name"] == "demo"

    def test_show_layout_default_name(self, monkeypatch):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        opened = {}
        monkeypatch.setattr(viz, "_server", object())
        monkeypatch.setattr(
            viz,
            "_open_layout_browser",
            lambda name, wait_for_browser, timeout=None: opened.setdefault("name", name),
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
    def test_add_menu_returns_id_and_reflected_in_layout(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        viz.set_layout(SceneView("a"), name="demo")
        mid = viz.add_menu(children=[ButtonView("b1", label="Go")])
        assert mid == "menu_0"
        payload = viz._layout_serialized_for("demo")
        assert payload["overlay"][0]["type"] == "menu"

    def test_add_menu_creates_default_layout_when_none(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        mid = viz.add_menu()
        assert mid == "menu_0"
        payload = viz._layout_serialized_for("")
        assert payload["root"]["type"] == "stack"
        assert payload["overlay"][0]["type"] == "menu"

    def test_add_menu_per_scene_name_raises(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        with pytest.raises(NotImplementedError):
            viz.add_menu(scene_name="other")

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

    def test_per_scene_overlay_appears_under_pane(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        viz.scene("detail")
        viz._add_scene_group("detail", "g", controls=[], parent_id="obj")
        payload = viz._scene_layout_for("detail")
        scene_node = payload["root"]["children"][0]
        assert scene_node["children"][0]["type"] == "group"

    def test_global_overlay_only_for_base_scene(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        viz.scene("detail")
        viz.add_menu()
        base = viz._scene_layout_for("")
        assert any(o["type"] == "menu" for o in base.get("overlay", []))
        detail = viz._scene_layout_for("detail")
        assert "overlay" not in detail

    def test_cached_named_layout_refreshes_on_overlay_change(self):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        viz.scene("detail")
        viz._scene_layout_for("detail")  # populate the cache
        viz._add_scene_group("detail", "g", controls=[], parent_id="obj")
        payload = viz._scene_layout_for("detail")
        scene_node = payload["root"]["children"][0]
        assert scene_node["children"][0]["type"] == "group"


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
        viz._server = _FakeLayoutServer(
            [{"id": "b1", "scene": "a", "layout": "demo"}]
        )
        asyncio.run(viz._push_layout_updates())
        browser_id, payload = viz._server.pushed[0]
        assert browser_id == "b1"
        assert payload["name"] == "demo"

    def test_overlay_change_schedules_repush(self, monkeypatch):
        viz = Visualizer(add_default_axes=False, add_default_grid=False)
        scheduled = []
        monkeypatch.setattr(
            viz, "_push_layout_updates_threadsafe", lambda: scheduled.append(True)
        )
        viz.add_menu()
        assert scheduled
