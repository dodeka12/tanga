# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Unit tests for the backend image-status control (pytanga.viz._controls)."""

from __future__ import annotations

import asyncio

from pytanga.viz._controls import (
    IMAGE_STATUS_ID,
    ControlEvent,
    ControlHandlerRegistry,
    ImageStatus,
    ImageStatusRecord,
    _default_image_status_sink,
)


def test_handle_event_parses_image_loaded_payload() -> None:
    ctrl = ImageStatus(IMAGE_STATUS_ID)
    d = ctrl.handle_event(
        "image_loaded",
        {
            "image_id": "img1",
            "source": "url",
            "width": 640,
            "height": 480,
            "browser_id": "b1",
        },
    )
    assert d.event == "image_loaded"
    assert d.push is None
    record = d.value
    assert isinstance(record, ImageStatusRecord)
    assert record.image_id == "img1"
    assert record.source == "url"
    assert record.width == 640
    assert record.height == 480
    assert record.level is None
    assert record.tile_version is None
    assert record.browser_id == "b1"


def test_handle_event_parses_tile_payload() -> None:
    ctrl = ImageStatus(IMAGE_STATUS_ID)
    for event in ("image_tile_load", "image_tile_loaded"):
        d = ctrl.handle_event(
            event,
            {
                "image_id": "img1",
                "source": "tiled",
                "width": 8192,
                "height": 4096,
                "level": 3,
                "tile_version": 2,
            },
        )
        assert d.event == event
        record = d.value
        assert record.level == 3
        assert record.tile_version == 2


def test_handle_event_defaults_when_omitted() -> None:
    ctrl = ImageStatus(IMAGE_STATUS_ID)
    d = ctrl.handle_event("image_loaded", {"image_id": "img1"})
    record = d.value
    assert record.image_id == "img1"
    assert record.source is None
    assert record.width is None
    assert record.height is None
    assert record.level is None
    assert record.tile_version is None
    assert record.browser_id is None


def test_register_handlers_registers_default_sinks() -> None:
    ctrl = ImageStatus(IMAGE_STATUS_ID)
    registry = ControlHandlerRegistry()
    assert ctrl.register_handlers(registry) is True
    assert registry.get(IMAGE_STATUS_ID, "image_loaded") is _default_image_status_sink
    assert registry.get(IMAGE_STATUS_ID, "image_tile_load") is _default_image_status_sink
    assert (
        registry.get(IMAGE_STATUS_ID, "image_tile_loaded")
        is _default_image_status_sink
    )


def test_register_handlers_uses_custom_sinks() -> None:
    async def loaded(value, event):  # noqa: ANN001, ANN202
        return None

    async def tile_load(value, event):  # noqa: ANN001, ANN202
        return None

    async def tile_loaded(value, event):  # noqa: ANN001, ANN202
        return None

    ctrl = ImageStatus(
        IMAGE_STATUS_ID,
        on_image_loaded=loaded,
        on_image_tile_load=tile_load,
        on_image_tile_loaded=tile_loaded,
    )
    registry = ControlHandlerRegistry()
    ctrl.register_handlers(registry)
    assert registry.get(IMAGE_STATUS_ID, "image_loaded") is loaded
    assert registry.get(IMAGE_STATUS_ID, "image_tile_load") is tile_load
    assert registry.get(IMAGE_STATUS_ID, "image_tile_loaded") is tile_loaded


class _FakeTransport:
    def __init__(self) -> None:
        self._handlers: dict[tuple[str, str], object] = {}

    def register(self, id: str, handler: object, *, event: str = "change") -> None:
        self._handlers[(id, event)] = handler

    def get(self, id: str, event: str = "change") -> object | None:
        return self._handlers.get((id, event))


def test_dispatch_routes_to_image_status() -> None:
    from pytanga.viz._layout import LayoutHostImpl

    transport = _FakeTransport()
    ctrl = ImageStatus(IMAGE_STATUS_ID)

    captured: list[ImageStatusRecord] = []

    async def loaded(record: ImageStatusRecord, event: ControlEvent) -> None:
        captured.append(record)

    transport._handlers[(IMAGE_STATUS_ID, "image_loaded")] = loaded

    layout = LayoutHostImpl(
        None,
        scene_factory=lambda name: None,
        transport=transport,
        image_status=ctrl,
    )

    asyncio.run(
        layout.dispatch_control_event(
            "control:image_loaded",
            {
                "control_id": IMAGE_STATUS_ID,
                "image_id": "img1",
                "source": "url",
                "width": 640,
                "height": 480,
            },
        )
    )

    assert len(captured) == 1
    assert captured[0].image_id == "img1"
    assert captured[0].source == "url"
    assert captured[0].width == 640


def test_visualizer_on_image_loaded_replaces_handler() -> None:
    from pytanga.viz.visualizer import Visualizer

    class _Fake:
        def __init__(self) -> None:
            self._image_status = ImageStatus(IMAGE_STATUS_ID)
            self._transport = _FakeTransport()
            self._image_status.register_handlers(self._transport)

    fake = _Fake()
    calls: list[ImageStatusRecord] = []

    async def loaded(record: ImageStatusRecord, event: ControlEvent) -> None:
        calls.append(record)

    Visualizer.on_image_loaded(fake, loaded)
    handler = fake._transport.get(IMAGE_STATUS_ID, "image_loaded")
    assert handler is loaded

    async def _dispatch() -> None:
        await handler(ImageStatusRecord(image_id="img1"), ControlEvent())  # type: ignore[misc]

    asyncio.run(_dispatch())
    assert len(calls) == 1
    assert calls[0].image_id == "img1"
