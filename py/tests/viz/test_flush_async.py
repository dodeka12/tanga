# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the awaitable ``flush_async()`` and ``flush(wait=True)`` APIs."""

import asyncio
import threading

import pytest

from pytanga.viz import Visualizer


class _FakeServer:
    """Minimal server stand-in that records ``push_raw`` calls."""

    def __init__(self) -> None:
        self.pushed: list[str] = []

    async def push_raw(self, data: str) -> None:
        self.pushed.append(data)


@pytest.mark.anyio
async def test_flush_async_noop_without_server():
    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    await viz.flush_async()  # no loop/server → silent no-op


@pytest.mark.anyio
async def test_flush_async_on_server_loop_flushes_all_scenes(monkeypatch):
    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    viz._server = _FakeServer()
    viz._loop = asyncio.get_running_loop()

    flushed: list[str] = []

    async def _record(name, *, fit_camera=False):
        flushed.append(name)

    monkeypatch.setattr(viz, "_flush_scene_async", _record)

    await viz.flush_async()

    assert sorted(flushed) == sorted(viz._scenes)


@pytest.mark.anyio
async def test_flush_async_named_scene(monkeypatch):
    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    viz.scene("detail")
    viz._server = _FakeServer()
    viz._loop = asyncio.get_running_loop()

    flushed: list[str] = []

    async def _record(name, *, fit_camera=False):
        flushed.append(name)

    monkeypatch.setattr(viz, "_flush_scene_async", _record)

    await viz.flush_async(scene="detail")

    assert flushed == ["detail"]


@pytest.mark.anyio
async def test_flush_async_forwards_fit_camera(monkeypatch):
    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    viz._server = _FakeServer()
    viz._loop = asyncio.get_running_loop()

    seen: list[bool] = []

    async def _record(name, *, fit_camera=False):
        seen.append(fit_camera)

    monkeypatch.setattr(viz, "_flush_scene_async", _record)

    await viz.flush_async(fit_camera=True)

    assert seen and all(seen)


def test_flush_wait_from_other_thread_does_not_deadlock():
    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    viz._server = _FakeServer()
    loop = asyncio.new_event_loop()
    thread = threading.Thread(target=loop.run_forever, daemon=True)
    thread.start()
    viz._loop = loop
    try:
        # The main thread is not the server loop's thread → safe blocking wait.
        viz.flush(wait=True)
    finally:
        loop.call_soon_threadsafe(loop.stop)
        thread.join(timeout=2.0)


@pytest.mark.anyio
async def test_flush_wait_on_server_loop_raises():
    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    viz._server = _FakeServer()
    viz._loop = asyncio.get_running_loop()

    with pytest.raises(RuntimeError, match="flush_async"):
        viz.flush(wait=True)


@pytest.mark.anyio
async def test_scene_handle_flush_async_delegates(monkeypatch):
    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    handle = viz.scene("detail")
    viz._server = _FakeServer()
    viz._loop = asyncio.get_running_loop()

    calls: list[dict] = []

    async def _fake_flush_async(*, fit_camera=False, scene=None):
        calls.append({"fit_camera": fit_camera, "scene": scene})

    monkeypatch.setattr(viz, "flush_async", _fake_flush_async)

    await handle.flush_async(fit_camera=True)

    assert calls == [{"fit_camera": True, "scene": "detail"}]
