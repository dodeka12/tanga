# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the reusable editor view API + dispatch."""

from __future__ import annotations

import pytest

from pytanga.viz import Visualizer


def _viz() -> Visualizer:
    return Visualizer(add_default_axes=False, add_default_grid=False)


def test_open_editor_registers_and_pushes(monkeypatch):
    viz = _viz()
    pushed: list[tuple] = []
    monkeypatch.setattr(
        viz._layout.overlay, "_push_editor_define", lambda c, **kw: pushed.append((c, kw))
    )

    async def _on_close(text, event):
        pass

    cid = viz.open_editor("e", label="Edit", value="x", on_close=_on_close)
    assert cid == "e"
    assert viz._handler_registry.get("e", "close") is _on_close
    assert pushed == [("e", {"label": "Edit", "value": "x"})]


def test_open_editor_without_handler():
    viz = _viz()
    viz.open_editor("e", value="x")
    assert viz._handler_registry.get("e", "close") is None


@pytest.mark.anyio
async def test_dispatch_editor_closed_keep():
    viz = _viz()
    calls: list = []

    async def _on_close(text, event):
        calls.append(text)

    viz._handler_registry.register("e", _on_close, event="close")
    await viz._dispatch_control_event("editor_closed", {"id": "e", "text": "x"})
    assert calls == ["x"]
    assert viz._handler_registry.get("e", "close") is None


@pytest.mark.anyio
async def test_dispatch_editor_closed_discard():
    viz = _viz()
    calls: list = []

    async def _on_close(text, event):
        calls.append(text)

    viz._handler_registry.register("e", _on_close, event="close")
    await viz._dispatch_control_event("editor_closed", {"id": "e", "text": None})
    assert calls == [None]
    assert viz._handler_registry.get("e", "close") is None


@pytest.mark.anyio
async def test_dispatch_editor_closed_unknown_id():
    viz = _viz()
    await viz._dispatch_control_event(
        "editor_closed", {"id": "missing", "text": "x"}
    )


def test_overlay_editor_direct_lifecycle(monkeypatch):
    viz = _viz()
    overlay = viz._layout.overlay
    pushed: list[tuple] = []
    monkeypatch.setattr(
        overlay, "_push_editor_define", lambda c, **kw: pushed.append((c, kw))
    )

    async def _on_close(text, event):
        pass

    cid = overlay.open_editor("e", label="Edit", value="x", on_close=_on_close)
    assert cid == "e"
    assert viz._handler_registry.get("e", "close") is _on_close
    assert pushed == [("e", {"label": "Edit", "value": "x"})]
