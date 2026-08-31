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
