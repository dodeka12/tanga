# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Unit tests for the backend client-log control (pytanga.viz._controls)."""

from __future__ import annotations

import asyncio
import logging

import pytest

from pytanga.viz._controls import (
    CLIENT_LOG_ID,
    ClientLog,
    ClientLogRecord,
    ControlEvent,
    ControlHandlerRegistry,
    _default_client_log_sink,
)


def test_handle_event_parses_full_payload() -> None:
    ctrl = ClientLog(CLIENT_LOG_ID)
    d = ctrl.handle_event(
        "log",
        {
            "level": "error",
            "message": "boom",
            "source": "three-view.js",
            "data": {"parent_id": "sphere"},
            "browser_id": "b1",
        },
    )
    assert d.event == "log"
    assert d.push is None
    record = d.value
    assert isinstance(record, ClientLogRecord)
    assert record.level == "error"
    assert record.message == "boom"
    assert record.source == "three-view.js"
    assert record.data == {"parent_id": "sphere"}
    assert record.browser_id == "b1"


def test_handle_event_defaults_when_omitted() -> None:
    ctrl = ClientLog(CLIENT_LOG_ID)
    d = ctrl.handle_event("log", {"message": "hi"})
    record = d.value
    assert record.level == "info"
    assert record.message == "hi"
    assert record.source is None
    assert record.data is None
    assert record.browser_id is None


def test_register_handlers_registers_default_on_log() -> None:
    ctrl = ClientLog(CLIENT_LOG_ID)
    registry = ControlHandlerRegistry()
    assert ctrl.register_handlers(registry) is True
    assert registry.get(CLIENT_LOG_ID, "log") is _default_client_log_sink


def test_register_handlers_uses_custom_on_log() -> None:
    async def sink(value, event):
        return None

    ctrl = ClientLog(CLIENT_LOG_ID, on_log=sink)
    registry = ControlHandlerRegistry()
    ctrl.register_handlers(registry)
    assert registry.get(CLIENT_LOG_ID, "log") is sink


@pytest.mark.parametrize(
    ("level", "expected"),
    [
        ("debug", "DEBUG"),
        ("info", "INFO"),
        ("warn", "WARNING"),
        ("error", "ERROR"),
        ("bogus", "WARNING"),
    ],
)
def test_default_sink_maps_level(caplog, level: str, expected: str) -> None:
    record = ClientLogRecord(level=level, message="msg", source="s")
    with caplog.at_level(logging.DEBUG, logger="tanga.viz.client"):
        asyncio.run(_default_client_log_sink(record, ControlEvent()))
    assert any(
        r.name == "tanga.viz.client" and r.levelname == expected
        for r in caplog.records
    )


class _FakeTransport:
    def __init__(self) -> None:
        self._handlers: dict[tuple[str, str], object] = {}

    def register(self, id: str, handler: object, *, event: str = "change") -> None:
        self._handlers[(id, event)] = handler

    def get(self, id: str, event: str = "change") -> object | None:
        return self._handlers.get((id, event))


def test_dispatch_routes_to_client_log() -> None:
    from pytanga.viz._layout import LayoutHostImpl

    transport = _FakeTransport()
    ctrl = ClientLog(CLIENT_LOG_ID)

    captured: list[ClientLogRecord] = []

    async def sink(record: ClientLogRecord, event: ControlEvent) -> None:
        captured.append(record)

    transport._handlers[(CLIENT_LOG_ID, "log")] = sink

    layout = LayoutHostImpl(
        None,
        scene_factory=lambda name: None,
        transport=transport,
        client_log=ctrl,
    )

    asyncio.run(
        layout.dispatch_control_event(
            "control:log",
            {"control_id": CLIENT_LOG_ID, "level": "error", "message": "boom"},
        )
    )

    assert len(captured) == 1
    assert captured[0].level == "error"
    assert captured[0].message == "boom"
