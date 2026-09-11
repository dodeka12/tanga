# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Port interfaces for the Tanga viewer.

Two structural interfaces decouple feature hosts from the concrete
``Visualizer``: :class:`LayoutHost` (what is drawn) and :class:`Transport`
(what talks in both directions).  Hosts are composed with these ports rather
than inheriting from or reaching back into the visualizer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Protocol

if TYPE_CHECKING:
    from .scene import Scene
    from .views import View


class Transport(Protocol):
    """Bidirectional message channel.

    Outbound sends serialize to JSON and push to connected browsers; inbound
    registers ``(id, event)`` handlers and routes incoming message types.
    """

    # ── outbound ──

    def send(self, message: dict[str, Any]) -> None:
        """Broadcast a message dict to all clients (thread-safe; no-op pre-boot)."""
        ...

    async def send_async(self, message: dict[str, Any]) -> None:
        """Awaitable :meth:`send`."""
        ...

    def flush(self) -> None:
        """Flush pending state to connected clients."""
        ...

    # ── inbound ──

    def register(
        self, id: str, handler: Any, *, event: str = "change", origin: Any = None
    ) -> None:
        """Register *handler* under ``(id, event)`` (optionally a handler origin)."""
        ...

    def send_to_browser(
        self, browser_id: str, message: dict[str, Any]
    ) -> Awaitable[None]:
        """Push *message* to a single browser (async)."""
        ...

    def unregister(self, id: str, event: str | None = None) -> None:
        """Unregister handlers for *id* (all events when *event* is ``None``)."""
        ...

    def get(self, id: str, event: str = "change") -> Any | None:
        """Return the handler registered under ``(id, event)``, or ``None``."""
        ...

    def clear(self, origin: Any = None) -> None:
        """Remove registered handlers (optionally only one origin class)."""
        ...

    def on_server_loop(
        self, coro_factory: Callable[[], Awaitable[Any]]
    ) -> Awaitable[Any]:
        """Run ``coro_factory()`` on the server loop and await it, from any loop."""
        ...

    def schedule(self, coro_factory: Callable[[], Awaitable[Any]]) -> None:
        """Schedule ``coro_factory()`` on the server loop (fire-and-forget)."""
        ...

    def route(self, msg_type: str, handler: Any) -> None:
        """Register a ``msg_type`` → handler route for inbound dispatch."""
        ...

    async def dispatch(self, msg_type: str, payload: dict[str, Any]) -> None:
        """Route an incoming ``(msg_type, payload)`` to its handler."""
        ...


class LayoutHost(Protocol):
    """The thing that owns what is drawn: scenes + view tree + serialization."""

    def scene(self, name: str) -> Scene:
        """Return the named scene model (``""`` for the main scene)."""
        ...

    def scene_names(self) -> list[str]:
        """Return the names of all scenes."""
        ...

    def add_scene(self, name: str) -> Scene:
        """Create a scene + auto single-``SceneView`` layout (raise if taken)."""
        ...

    def set_layout(self, root: View, name: str = "") -> str:
        """Register (or replace) the base view tree for *name*."""
        ...

    def add_layout(self, root: View, name: str = "") -> str:
        """Register a layout (raise if *name* is already taken)."""
        ...

    def register(self, root: View) -> set[str]:
        """Register *root*'s control handlers + inject push callbacks."""
        ...

    def resolve_control(self, cid: str) -> Any | None:
        """Return the control with id *cid* (layouts + dialogs), or ``None``."""
        ...

    def remove_view(self, view_id: str, *, scene: str | None = None) -> None:
        """Remove a mounted overlay view by its stable id."""
        ...

    def update_view(self, view_id: str, **fields: Any) -> None:
        """Mutate a mounted view's fields and re-sync the layout."""
        ...

    def serialize(self, *, scene: str | None = None) -> dict[str, Any] | None:
        """Return the serialized ``view_layout`` payload for *scene*, or ``None``."""
        ...


@dataclass
class ServerState:
    """Late-bound websocket server/loop pair.

    ``Visualizer`` owns one of these and keeps it in sync with ``self._server`` /
    ``self._loop`` (which are ``None`` until the server boots).  The concrete
    ``Transport`` reads it, so hosts never touch a raw server/loop.
    """

    server: Any = None
    loop: Any = None
