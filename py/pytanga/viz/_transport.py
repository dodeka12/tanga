# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Concrete :class:`Transport` over the websocket server + handler registry."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from ._ports import ServerState


class WebSocketTransport:
    """Bidirectional channel over a late-bound :class:`VizServer`.

    The server/loop are read from a mutable :class:`ServerState` (``None`` until
    the server boots), so ``send`` is a safe no-op before startup.  Inbound
    handlers live in the shared ``(id, event)`` registry.
    """

    def __init__(self, state: ServerState, registry: Any) -> None:
        self._state = state
        self._registry = registry
        self._routes: dict[str, Any] = {}

    # ── outbound ──

    def send(self, message: dict[str, Any]) -> None:
        """Broadcast *message* to all clients (thread-safe; no-op pre-boot)."""
        server = self._state.server
        loop = self._state.loop
        if server is None or loop is None:
            return
        asyncio.run_coroutine_threadsafe(server.push_raw(json.dumps(message)), loop)

    async def send_async(self, message: dict[str, Any]) -> None:
        """Awaitable :meth:`send`."""
        server = self._state.server
        if server is None:
            return
        await server.push_raw(json.dumps(message))

    def flush(self) -> None:
        """Flush pending state to connected clients (wired in phase 5)."""
        ...

    # ── inbound ──

    def register(
        self, id: str, handler: Any, *, event: str = "change", origin: Any = None
    ) -> None:
        """Register *handler* under ``(id, event)`` (optionally a handler origin)."""
        if origin is None:
            self._registry.register(id, handler, event=event)
        else:
            self._registry.register(id, handler, event=event, origin=origin)

    async def send_to_browser(self, browser_id: str, message: dict[str, Any]) -> None:
        """Push *message* to a single browser (async)."""
        server = self._state.server
        if server is None:
            return
        await server.push_raw_to_browser(browser_id, json.dumps(message))

    def unregister(self, id: str, event: str | None = None) -> None:
        """Unregister handlers for *id* (all events when *event* is ``None``)."""
        self._registry.unregister(id, event)

    def get(self, id: str, event: str = "change") -> Any | None:
        """Return the handler registered under ``(id, event)``, or ``None``."""
        return self._registry.get(id, event)

    def clear(self, origin: Any = None) -> None:
        """Remove registered handlers (optionally only one origin class)."""
        self._registry.clear(origin)

    async def on_server_loop(self, coro_factory: Any) -> Any:
        """Run ``coro_factory()`` on the server loop and await it, from any loop."""
        loop = self._state.loop
        server = self._state.server
        if loop is None or server is None:
            return None
        if asyncio.get_running_loop() is loop:
            return await coro_factory()
        fut = asyncio.run_coroutine_threadsafe(coro_factory(), loop)
        return await asyncio.wrap_future(fut)

    def schedule(self, coro_factory: Any) -> None:
        """Schedule ``coro_factory()`` on the server loop (fire-and-forget)."""
        loop = self._state.loop
        if loop is None:
            return
        asyncio.run_coroutine_threadsafe(coro_factory(), loop)

    def route(self, msg_type: str, handler: Any) -> None:
        """Register a ``msg_type`` → handler route for inbound dispatch."""
        self._routes[msg_type] = handler

    async def dispatch(self, msg_type: str, payload: dict[str, Any]) -> None:
        """Route an incoming ``(msg_type, payload)`` to its handler (no-op if unhandled)."""
        handler = self._routes.get(msg_type)
        if handler is None:
            for prefix in ("control:", "interaction:"):
                if msg_type.startswith(prefix):
                    handler = self._routes.get(f"{prefix}*")
                    if handler is not None:
                        break
        if handler is None:
            return
        await handler(msg_type, payload)
