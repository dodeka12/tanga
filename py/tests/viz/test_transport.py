# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the ``WebSocketTransport`` adapter (phase 2)."""

import asyncio

import pytest

from pytanga.viz._ports import ServerState
from pytanga.viz._transport import WebSocketTransport


class _FakeServer:
    def __init__(self) -> None:
        self.pushed: list[str] = []

    async def push_raw(self, data: str) -> None:
        self.pushed.append(data)


class _FakeRegistry:
    def __init__(self) -> None:
        self._h: dict[tuple[str, str], object] = {}

    def register(self, control_id, handler, *, event="change", origin=None) -> None:
        self._h[(control_id, event)] = handler

    def unregister(self, control_id, event=None) -> None:
        if event is None:
            for key in [k for k in self._h if k[0] == control_id]:
                del self._h[key]
        else:
            self._h.pop((control_id, event), None)

    def get(self, control_id, event="change"):
        return self._h.get((control_id, event))


def _transport(server: _FakeServer | None = None) -> WebSocketTransport:
    state = ServerState()
    if server is not None:
        state.server = server
        state.loop = asyncio.new_event_loop()
    return WebSocketTransport(state, _FakeRegistry())


def test_send_noop_pre_boot() -> None:
    t = _transport()  # server/loop are None
    t.send({"type": "x"})  # must not raise


def test_send_serializes_and_pushes(monkeypatch) -> None:
    server = _FakeServer()
    state = ServerState()
    state.server = server
    state.loop = object()
    monkeypatch.setattr(
        asyncio, "run_coroutine_threadsafe", lambda coro, loop: asyncio.run(coro)
    )
    t = WebSocketTransport(state, _FakeRegistry())
    t.send({"type": "banner_define", "id": "b"})
    assert server.pushed == ['{"type": "banner_define", "id": "b"}']


@pytest.mark.anyio
async def test_send_async_awaits_push() -> None:
    server = _FakeServer()
    t = _transport(server)
    await t.send_async({"type": "x"})
    assert server.pushed == ['{"type": "x"}']


def test_register_get_roundtrip() -> None:
    t = _transport()

    async def _h(value, event):
        pass

    t.register("s", _h, event="change")
    assert t.get("s", "change") is _h
    assert t.get("s", "click") is None
    assert t.get("s") is _h  # default event == "change"


def test_unregister() -> None:
    t = _transport()

    async def _h(value, event):
        pass

    t.register("s", _h, event="change")
    t.register("s", _h, event="click")
    t.unregister("s", "change")
    assert t.get("s", "change") is None
    assert t.get("s", "click") is _h
    t.unregister("s")  # all events
    assert t.get("s", "click") is None


@pytest.mark.anyio
async def test_dispatch_exact_wildcard_unknown() -> None:
    t = _transport()
    seen: list[tuple] = []

    async def _exact(msg_type, payload):
        seen.append(("exact", msg_type, payload))

    async def _control(msg_type, payload):
        seen.append(("control", msg_type, payload))

    async def _interaction(msg_type, payload):
        seen.append(("interaction", msg_type, payload))

    t.route("banner_closed", _exact)
    t.route("control:*", _control)
    t.route("interaction:*", _interaction)

    await t.dispatch("banner_closed", {"id": "b"})
    await t.dispatch("control:change", {"control_id": "s", "value": 1})
    await t.dispatch("interaction:click", {"object_id": "o"})
    await t.dispatch("unknown", {})  # no-op

    assert seen == [
        ("exact", "banner_closed", {"id": "b"}),
        ("control", "control:change", {"control_id": "s", "value": 1}),
        ("interaction", "interaction:click", {"object_id": "o"}),
    ]
