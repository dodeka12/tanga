# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the server's multi-scene full-state push (`_push_full_state`)."""

import asyncio
import json

from pytanga.viz.server import VizServer


class _FakeWS:
    def __init__(self):
        self.sent: list[dict] = []

    async def send_str(self, payload: str) -> None:
        self.sent.append(json.loads(payload))


def _server() -> VizServer:
    server = VizServer()
    server._flush_callback = lambda name: ([{"id": f"{name}-obj", "kind": "Point"}], [])
    server._scene_config_callback = lambda name: {"type": "scene_config", "name": name}
    server._scene_list_callback = lambda: ["", "a", "b"]
    server._layout_callback = lambda name: {
        "type": "view_layout",
        "name": name,
        "scenes": ["a", "b"],
        "root": {},
    }
    return server


class TestPushFullState:
    def test_layout_push_orders_messages(self):
        server = _server()
        ws = _FakeWS()
        asyncio.run(
            server._push_full_state(
                ws,
                scene_names=["a", "b"],
                layout_payload=server._layout_callback("demo"),
                browser_id="b1",
            )
        )
        types = [m["type"] for m in ws.sent]
        assert types[0] == "clear_all"
        assert types[1] == "view_layout"
        assert ws.sent[2]["type"] == "scene_config" and ws.sent[2]["name"] == "a"
        assert ws.sent[3]["type"] == "scene_update" and ws.sent[3]["scene"] == "a"
        assert ws.sent[4]["type"] == "scene_config" and ws.sent[4]["name"] == "b"
        assert ws.sent[5]["type"] == "scene_update" and ws.sent[5]["scene"] == "b"
        assert types[-1] == "scene_list"

    def test_single_scene_push(self):
        server = _server()
        ws = _FakeWS()
        asyncio.run(server._push_full_state(ws, scene_names=["main"], browser_id="b1"))
        types = [m["type"] for m in ws.sent]
        assert types == ["clear_all", "scene_config", "scene_update", "scene_list"]

    def test_layout_payload_omitted_when_none(self):
        server = _server()
        ws = _FakeWS()
        asyncio.run(server._push_full_state(ws, scene_names=["a"], browser_id="b1"))
        types = [m["type"] for m in ws.sent]
        assert "view_layout" not in types


class TestResolveLayout:
    def _server(self) -> VizServer:
        server = VizServer()
        server._layout_callback = lambda name: {
            "type": "view_layout",
            "name": name,
            "scenes": ["a", "b"],
            "root": {},
        }
        server._scene_layout_callback = lambda name: {
            "type": "view_layout",
            "name": name,
            "scenes": [name],
            "root": {"type": "stack"},
        }
        return server

    def test_single_scene_uses_scene_layout_callback(self):
        server = self._server()
        scene_names, payload = server._resolve_layout("detail", None)
        assert scene_names == ["detail"]
        assert payload == server._scene_layout_callback("detail")

    def test_layout_mode_uses_layout_callback(self):
        server = self._server()
        scene_names, payload = server._resolve_layout("", "demo")
        assert scene_names == ["a", "b"]
        assert payload["name"] == "demo"

    def test_unknown_layout_falls_back_to_main_scene(self):
        server = VizServer()
        server._layout_callback = lambda name: None
        server._scene_layout_callback = lambda name: None
        scene_names, payload = server._resolve_layout("", "missing")
        assert scene_names == [""]
        assert payload is None

    def test_single_scene_without_scene_layout_callback_returns_no_payload(self):
        server = VizServer()
        server._layout_callback = lambda name: None
        scene_names, payload = server._resolve_layout("main", None)
        assert scene_names == ["main"]
        assert payload is None


class TestThemeServing:
    def test_theme_links_injected_when_callback_set(self):
        server = VizServer()
        server._theme_callback = lambda: {
            "theme": "dark",
            "label": "Dark",
            "css": ["base.css", "tokens.css", "dark/tokens.css"],
        }
        html = server._theme_links_html()
        assert 'data-tanga-theme href="themes/base.css"' in html
        assert 'data-tanga-theme href="themes/tokens.css"' in html
        assert 'data-tanga-theme href="themes/dark/tokens.css"' in html

    def test_theme_links_omitted_when_callback_unset(self):
        server = VizServer()
        assert server._theme_links_html() == ""

