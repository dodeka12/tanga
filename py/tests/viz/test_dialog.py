# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the Dialog model + wire serialization (Phase 7)."""

import pytest

from pytanga.viz import Visualizer
from pytanga.viz._dialog import (
    Dialog,
    serialize_dialog,
    serialize_dialog_clear,
    serialize_dialog_remove,
)
from pytanga.viz.views import ButtonView, SliderView, StackView


def _content() -> StackView:
    return StackView(
        "vertical",
        [
            SliderView("s", label="Speed", min=0, max=10, value=5),
            ButtonView("b", label="Close"),
        ],
    )


def test_serialize_dialog_global_defaults():
    dialog = Dialog(id="d1", content=_content())
    msg = serialize_dialog(dialog)
    assert msg["type"] == "dialog_define"
    assert msg["scene"] is None
    assert msg["id"] == "d1"
    assert msg["title"] == ""
    assert msg["align_x"] == 0.5
    assert msg["align_y"] == 0.5
    assert msg["dismissable"] is True
    # ``content`` is a serialized view node (a stack of control views).
    assert isinstance(msg["content"], dict)
    assert msg["content"]["type"] == "stack"


def test_serialize_dialog_scoped():
    dialog = Dialog(id="d1", content=_content())
    assert serialize_dialog(dialog, scene="detail")["scene"] == "detail"
    assert serialize_dialog(dialog, scene="")["scene"] == ""


def test_serialize_dialog_modal():
    msg = serialize_dialog(Dialog(id="d1", content=_content(), dismissable=False))
    assert msg["dismissable"] is False


def test_serialize_dialog_width_height():
    from pytanga.viz import Size

    msg = serialize_dialog(
        Dialog(id="d1", content=_content(), width=Size.px(600), height=Size.percent(80))
    )
    assert msg["width"] == {"value": 600, "unit": "px"}
    assert msg["height"] == {"value": 80, "unit": "%"}


def test_serialize_dialog_content_children():
    msg = serialize_dialog(Dialog(id="d1", content=_content()))
    children = msg["content"]["children"]
    assert [c["type"] for c in children] == ["slider_view", "button_view"]
    assert children[0]["id"] == "s"
    assert children[1]["id"] == "b"


def test_align_out_of_range_raises():
    with pytest.raises(ValueError):
        Dialog(id="d", content=_content(), align_x=-0.1)
    with pytest.raises(ValueError):
        Dialog(id="d", content=_content(), align_y=1.1)
    # Boundary values are valid.
    Dialog(id="d", content=_content(), align_x=0.0, align_y=1.0)


def test_serialize_dialog_remove_and_clear():
    assert serialize_dialog_remove("d1") == {
        "type": "dialog_remove",
        "scene": None,
        "id": "d1",
    }
    assert serialize_dialog_remove("d1", scene="detail") == {
        "type": "dialog_remove",
        "scene": "detail",
        "id": "d1",
    }
    assert serialize_dialog_clear() == {"type": "dialog_clear", "scene": None}
    assert serialize_dialog_clear(scene="detail") == {
        "type": "dialog_clear",
        "scene": "detail",
    }


# ── Phase 7.2 — Visualizer dialog API ──────────────────────


class _FakeServer:
    def __init__(self) -> None:
        self.pushed: list[str] = []

    async def push_raw(self, data: str) -> None:
        self.pushed.append(data)


def _viz() -> Visualizer:
    return Visualizer(add_default_axes=False, add_default_grid=False)


def test_show_dialog_stores_registers_pushes(monkeypatch):
    viz = _viz()
    pushed: list[tuple] = []
    monkeypatch.setattr(viz._layout.overlay, "_push_dialog", lambda d, s: pushed.append((d.id, s)))

    async def _on_click(value, event):
        pass

    did = viz.show_dialog(
        StackView("vertical", [ButtonView("b", label="Close", on_click=_on_click)])
    )
    assert did == "dialog_1"
    # Stored under the global scope (None).
    assert viz._dialogs[None][did].id == did
    # Content control handler registered.
    assert viz._handler_registry.get("b", "click") is _on_click
    assert pushed == [(did, None)]


def test_show_dialog_explicit_id_collision_raises(monkeypatch):
    viz = _viz()
    monkeypatch.setattr(viz._layout.overlay, "_push_dialog", lambda d, s: None)
    viz.show_dialog(_content(), id="dup")
    with pytest.raises(ValueError):
        viz.show_dialog(_content(), id="dup")


def test_remove_dialog_unregisters_and_pushes(monkeypatch):
    viz = _viz()
    removed: list = []
    monkeypatch.setattr(viz._layout.overlay, "_push_dialog", lambda d, s: None)
    monkeypatch.setattr(viz._layout.overlay, "_push_dialog_remove", lambda i, s: removed.append((i, s)))

    async def _on_click(value, event):
        pass

    did = viz.show_dialog(
        StackView("vertical", [ButtonView("b", label="Close", on_click=_on_click)])
    )
    viz.remove_dialog(did)
    assert did not in viz._dialogs[None]
    assert viz._handler_registry.get("b", "click") is None
    assert removed == [(did, None)]


def test_clear_dialogs_scoped(monkeypatch):
    viz = _viz()
    cleared: list = []
    monkeypatch.setattr(viz._layout.overlay, "_push_dialog", lambda d, s: None)
    monkeypatch.setattr(viz._layout.overlay, "_push_dialog_clear", lambda s: cleared.append(s))

    viz.show_dialog(_content(), id="g")
    viz.show_dialog(_content(), id="s", scene_name="detail")
    viz.clear_dialogs(scene_name="detail")
    # Global dialog survives; only the scoped scope was cleared.
    assert "g" in viz._dialogs[None]
    assert "s" not in viz._dialogs.get("detail", {})
    assert cleared == ["detail"]


@pytest.mark.anyio
async def test_dialog_closed_dispatches_on_close(monkeypatch):
    viz = _viz()
    monkeypatch.setattr(viz._layout.overlay, "_push_dialog", lambda d, s: None)
    closed: list = []

    async def _on_close(value, event):
        closed.append(value)

    did = viz.show_dialog(_content(), on_close=_on_close)
    await viz._dispatch_control_event("close", {"id": did})
    assert closed == [None]
    # Handler is one-shot: unregistered after it runs.
    assert viz._handler_registry.get(did, "close") is None


def test_scene_handle_show_dialog_scopes(monkeypatch):
    viz = _viz()
    handle = viz.scene("detail")
    calls: list = []
    monkeypatch.setattr(viz, "show_dialog", lambda *a, **kw: calls.append(kw) or "x")
    handle.show_dialog(_content())
    assert calls[0]["scene_name"] == "detail"


def test_overlay_dialog_direct_lifecycle():
    viz = _viz()
    overlay = viz._layout.overlay

    async def _on_click(value, event):
        pass

    did = overlay.show_dialog(
        StackView("vertical", [ButtonView("b", label="Close", on_click=_on_click)])
    )
    assert did == "dialog_1"
    assert overlay._dialogs[None][did].id == did
    assert viz._handler_registry.get("b", "click") is _on_click

    overlay.remove_dialog(did)
    assert did not in overlay._dialogs[None]
    assert viz._handler_registry.get("b", "click") is None
