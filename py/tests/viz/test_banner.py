# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the Banner model + wire serialization (Phase 1)."""

import asyncio
import threading

import pytest

from pytanga.viz import SliderView, Visualizer
from pytanga.viz._banner import (
    Banner,
    serialize_banner,
    serialize_banner_clear,
    serialize_banner_remove,
)
from pytanga.viz._controls import Button, Dropdown, Slider


def test_serialize_banner_global_defaults():
    banner = Banner(id="b1", text="Hello $x$")
    msg = serialize_banner(banner)
    assert msg["type"] == "banner_define"
    assert msg["scene"] is None
    assert msg["id"] == "b1"
    assert msg["text"] == "Hello $x$"
    assert msg["title"] == ""
    assert msg["align_x"] == 0.5
    assert msg["align_y"] == 0.5
    assert msg["auto_hide"] is True
    assert msg["dismissable"] is True
    assert msg["controls"] == []


def test_serialize_banner_scoped():
    banner = Banner(id="b1", text="x")
    assert serialize_banner(banner, scene="detail")["scene"] == "detail"
    assert serialize_banner(banner, scene="")["scene"] == ""


def test_serialize_banner_controls_kind_specific():
    banner = Banner(
        id="b1",
        text="x",
        controls=[
            Slider(id="s", label="S", min=0, max=10, step=1, value=5),
            Dropdown(id="d", label="D", options=["a", "b"], value="a"),
            Button(id="b", label="B"),
        ],
    )
    controls = serialize_banner(banner)["controls"]
    assert [c["id"] for c in controls] == ["s", "d", "b"]

    assert controls[0]["kind"] == "slider"
    assert controls[0]["min"] == 0
    assert controls[0]["max"] == 10
    assert controls[0]["step"] == 1
    assert controls[0]["value"] == 5

    assert controls[1]["kind"] == "dropdown"
    assert controls[1]["options"] == ["a", "b"]
    assert controls[1]["value"] == "a"

    assert controls[2]["kind"] == "button"


def test_align_out_of_range_raises():
    with pytest.raises(ValueError):
        Banner(id="b", text="x", align_x=-0.1)
    with pytest.raises(ValueError):
        Banner(id="b", text="x", align_y=1.1)
    # Boundary values are valid.
    Banner(id="b", text="x", align_x=0.0, align_y=1.0)


def test_serialize_banner_remove_and_clear():
    assert serialize_banner_remove("b1") == {
        "type": "banner_remove",
        "scene": None,
        "id": "b1",
    }
    assert serialize_banner_remove("b1", scene="detail") == {
        "type": "banner_remove",
        "scene": "detail",
        "id": "b1",
    }
    assert serialize_banner_clear() == {"type": "banner_clear", "scene": None}
    assert serialize_banner_clear(scene="detail") == {
        "type": "banner_clear",
        "scene": "detail",
    }


# ── Phase 2 — Visualizer banner API ─────────────────────────


class _FakeServer:
    def __init__(self) -> None:
        self.pushed: list[str] = []

    async def push_raw(self, data: str) -> None:
        self.pushed.append(data)


def _viz() -> Visualizer:
    return Visualizer(add_default_axes=False, add_default_grid=False)


def test_show_banner_stores_registers_pushes(monkeypatch):
    viz = _viz()
    pushed: list[tuple] = []
    monkeypatch.setattr(viz._layout.overlay, "_push_banner", lambda b, s: pushed.append((b.id, s)))

    async def _on_ok(value, event):
        pass

    bid = viz.show_banner(
        "hi", title="T", controls=[Button(id="ok", label="OK", on_click=_on_ok)]
    )

    assert bid == "banner_1"
    assert viz._banners[None][bid].text == "hi"
    assert viz._handler_registry.get("ok", "click") is _on_ok
    assert pushed == [("banner_1", None)]


def test_show_banner_auto_id_unique():
    viz = _viz()
    a = viz.show_banner("a")
    b = viz.show_banner("b")
    assert a == "banner_1"
    assert b == "banner_2"
    assert a != b


def test_show_banner_explicit_id_reuse_raises(monkeypatch):
    viz = _viz()
    monkeypatch.setattr(viz._layout.overlay, "_push_banner", lambda b, s: None)
    viz.show_banner("a", id="dup")
    with pytest.raises(ValueError):
        viz.show_banner("b", id="dup")


def test_remove_banner_unregisters_and_pushes(monkeypatch):
    viz = _viz()
    removed: list = []
    monkeypatch.setattr(viz._layout.overlay, "_push_banner", lambda b, s: None)
    monkeypatch.setattr(viz._layout.overlay, "_push_banner_remove", lambda i, s: removed.append((i, s)))

    async def _on_ok(value, event):
        pass

    async def _on_close(value, event):
        pass

    bid = viz.show_banner(
        "hi", controls=[Button(id="ok", on_click=_on_ok)], on_close=_on_close
    )
    assert viz._handler_registry.get("ok", "click") is _on_ok
    assert viz._handler_registry.get(bid, "close") is _on_close

    viz.remove_banner(bid)
    assert bid not in viz._banners[None]
    assert viz._handler_registry.get("ok", "click") is None
    assert viz._handler_registry.get(bid, "close") is None
    assert removed == [(bid, None)]


def test_clear_banners_scoped(monkeypatch):
    viz = _viz()
    cleared: list = []
    monkeypatch.setattr(viz._layout.overlay, "_push_banner", lambda b, s: None)
    monkeypatch.setattr(viz._layout.overlay, "_push_banner_clear", lambda s: cleared.append(s))

    viz.show_banner("a")
    viz.show_banner("b", scene_name="detail")
    viz.clear_banners(scene_name=None)

    assert None not in viz._banners
    assert "detail" in viz._banners
    assert cleared == [None]


def test_alert_confirm_buttons(monkeypatch):
    viz = _viz()
    pushed: dict = {}
    monkeypatch.setattr(viz._layout.overlay, "_push_banner", lambda b, s: pushed.update({b.id: b}))

    async def _ok(value, event):
        pass

    async def _yes(value, event):
        pass

    bid = viz.alert("ack", on_ok=_ok)
    banner = pushed[bid]
    assert len(banner.controls) == 1
    assert banner.controls[0].label == "OK"
    assert viz._handler_registry.get(f"{bid}_ok", "click") is _ok

    bid2 = viz.confirm("?", on_yes=_yes)
    banner2 = pushed[bid2]
    assert [c.label for c in banner2.controls] == ["Yes", "No", "Cancel"]
    assert viz._handler_registry.get(f"{bid2}_yes", "click") is _yes


@pytest.mark.anyio
async def test_banner_closed_dispatches_on_close():
    viz = _viz()
    calls: list = []

    async def _on_close(value, event):
        calls.append(value)

    viz._handler_registry.register("b1", _on_close, event="close")
    await viz._dispatch_control_event("banner_closed", {"id": "b1"})
    assert calls == [None]


@pytest.mark.anyio
async def test_dispatch_close_unified_envelope():
    viz = _viz()
    calls: list = []

    async def _on_close(value, event):
        calls.append(value)

    viz._handler_registry.register("b1", _on_close, event="close")
    await viz._dispatch_control_event("close", {"control_id": "b1", "value": None})

    assert calls == [None]
    assert viz._handler_registry.get("b1", "close") is None  # one-shot


@pytest.mark.anyio
async def test_show_banner_async_awaits_push(monkeypatch):
    viz = _viz()
    viz._server = _FakeServer()
    viz._loop = asyncio.get_running_loop()

    pushed: list = []

    async def _push(banner, scene_name):
        pushed.append((banner.id, scene_name))

    monkeypatch.setattr(viz._layout.overlay, "_push_banner_async", _push)

    bid = await viz.show_banner_async("hi")
    assert pushed == [(bid, None)]


def test_show_banner_async_cross_loop_no_deadlock():
    viz = _viz()
    viz._server = _FakeServer()
    loop = asyncio.new_event_loop()
    thread = threading.Thread(target=loop.run_forever, daemon=True)
    thread.start()
    viz._loop = loop
    try:
        bid = asyncio.run(viz.show_banner_async("hi"))
        assert bid == "banner_1"
        assert any("banner_define" in d for d in viz._server.pushed)
    finally:
        loop.call_soon_threadsafe(loop.stop)
        thread.join(timeout=2.0)


def test_scene_handle_show_banner_scopes(monkeypatch):
    viz = _viz()
    handle = viz.scene("detail")
    calls: list = []
    monkeypatch.setattr(viz, "show_banner", lambda *a, **kw: calls.append(kw) or "x")
    handle.show_banner("hi")
    assert calls[0]["scene_name"] == "detail"


def test_scene_handle_alert_scopes(monkeypatch):
    viz = _viz()
    handle = viz.scene("detail")
    calls: list = []
    monkeypatch.setattr(viz, "alert", lambda *a, **kw: calls.append(kw) or "x")
    handle.alert("ack", title="T", ok_label="Got it")
    assert calls[0]["scene_name"] == "detail"
    assert calls[0]["title"] == "T"
    assert calls[0]["ok_label"] == "Got it"


def test_scene_handle_confirm_scopes(monkeypatch):
    viz = _viz()
    handle = viz.scene("detail")
    calls: list = []
    monkeypatch.setattr(viz, "confirm", lambda *a, **kw: calls.append(kw) or "x")
    handle.confirm("?", yes_label="Yep", no_label="Nope", cancel_label="Abort")
    assert calls[0]["scene_name"] == "detail"
    assert calls[0]["yes_label"] == "Yep"
    assert calls[0]["no_label"] == "Nope"
    assert calls[0]["cancel_label"] == "Abort"



# ── Phase 6.2 — slider press/release events ─────────────────


def test_add_slider_press_release_registration():
    viz = _viz()

    async def _on_change(v, e):
        pass

    async def _on_press(v, e):
        pass

    async def _on_release(v, e):
        pass

    viz.set_layout(SliderView(
        "s",
        on_change=_on_change,
        on_press=_on_press,
        on_release=_on_release,
    ))
    assert viz._handler_registry.get("s") is _on_change
    assert viz._handler_registry.get("s", "press") is _on_press
    assert viz._handler_registry.get("s", "release") is _on_release


@pytest.mark.anyio
async def test_dispatch_press_and_release():
    viz = _viz()
    press_calls = []
    release_calls = []

    async def _on_press(v, e):
        press_calls.append(v)

    async def _on_release(v, e):
        release_calls.append(v)

    viz._handler_registry.register("s", _on_press, event="press")
    viz._handler_registry.register("s", _on_release, event="release")

    await viz._dispatch_control_event(
        "control:press", {"control_id": "s", "value": 1.0}
    )
    await viz._dispatch_control_event(
        "control:release", {"control_id": "s", "value": 2.0}
    )
    assert press_calls == [1.0]
    assert release_calls == [2.0]


def test_overlay_banner_direct_lifecycle():
    viz = _viz()
    overlay = viz._layout.overlay

    async def _on_ok(value, event):
        pass

    bid = overlay.show_banner("hi", controls=[Button(id="ok", on_click=_on_ok)])
    assert bid == "banner_1"
    assert overlay._banners[None][bid].text == "hi"
    assert viz._handler_registry.get("ok", "click") is _on_ok

    overlay.remove_banner(bid)
    assert bid not in overlay._banners[None]
    assert viz._handler_registry.get("ok", "click") is None
