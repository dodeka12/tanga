# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Feature hosts for the Tanga viewer.

The ``Visualizer`` delegates its control/theme/interaction concerns to these
host classes.  Each host owns the state, lifecycle, and wire messages of one
kind of feature; they depend on two ports — a
:class:`~pytanga.viz._ports.Transport` (communication) and a
:class:`~pytanga.viz._ports.LayoutHost` (what is drawn) — instead of the
concrete visualizer.
"""

from __future__ import annotations

from typing import Any


class OverlayHost:
    """Base for the feature hosts: holds the two ports (Transport + LayoutHost).

    The ``_handler_registry`` / ``_push_message`` / ``_on_server_loop`` names are
    kept as thin aliases over the ports so per-host bodies stay stable during the
    migration; new code should use ``self._transport`` / ``self._layout`` directly.
    """

    def __init__(self, transport: Any, layout: Any) -> None:
        self._transport = transport
        self._layout = layout

    @property
    def _handler_registry(self) -> Any:
        return self._transport

    def _on_server_loop(self, coro_factory: Any) -> Any:
        return self._transport.on_server_loop(coro_factory)

    def _push_message(self, message: dict[str, Any]) -> None:
        self._transport.send(message)

    async def _push_message_async(self, message: dict[str, Any]) -> None:
        await self._transport.send_async(message)


class ThemeHost(OverlayHost):
    """Theme selection: state, validation, push, and file-watching."""

    def __init__(self, transport: Any, layout: Any) -> None:
        super().__init__(transport, layout)
        self._theme = "dark"
        self._theme_version = 0
        self._theme_watch_thread: Any = None
        self._theme_watch_stop: Any = None

    @property
    def theme(self) -> str:
        """The active UI theme id (default ``"dark"``)."""
        return self._theme

    def set_theme(self, theme_id: str) -> None:
        """Select the active UI theme and push it to all connected clients."""
        from ._themes import theme_css_files

        theme_css_files(theme_id)  # raises KeyError on unknown theme
        self._theme = theme_id
        self._theme_version += 1
        self._push_theme()

    async def set_theme_async(self, theme_id: str) -> None:
        """Async variant of :meth:`set_theme` — call from the server's event loop."""
        from ._themes import theme_css_files

        theme_css_files(theme_id)  # raises KeyError on unknown theme
        self._theme = theme_id
        self._theme_version += 1
        await self._transport.send_async(self._theme_message())

    def refresh_theme(self) -> None:
        """Re-push the active theme so connected viewers reload its CSS."""
        self._theme_version += 1
        self._push_theme()

    async def refresh_theme_async(self) -> None:
        """Async variant of :meth:`refresh_theme` — call from the server's loop."""
        self._theme_version += 1
        await self._transport.send_async(self._theme_message())

    def enable_theme_auto_reload(self, poll_interval: float = 1.0) -> None:
        """Watch the active theme's files and auto-refresh the viewer on change."""
        import threading

        if self._theme_watch_thread is not None:
            return
        self._theme_watch_stop = threading.Event()
        self._theme_watch_thread = threading.Thread(
            target=self._watch_theme_files,
            args=(float(poll_interval),),
            name="tanga-theme-watch",
            daemon=True,
        )
        self._theme_watch_thread.start()

    def disable_theme_auto_reload(self) -> None:
        """Stop the theme auto-reload watcher started by :meth:`enable_theme_auto_reload`."""
        if self._theme_watch_thread is None:
            return
        if self._theme_watch_stop is not None:
            self._theme_watch_stop.set()
        self._theme_watch_thread = None
        self._theme_watch_stop = None

    def _watch_theme_files(self, poll_interval: float) -> None:
        import logging

        from ._themes import theme_source_files

        logger = logging.getLogger("tanga.viz")

        def _signature(files):
            sig = []
            for p in files:
                try:
                    st = p.stat()
                    sig.append((str(p), st.st_mtime_ns, st.st_size))
                except OSError:
                    sig.append((str(p), -1, -1))
            return tuple(sig)

        last = None
        while (
            self._theme_watch_stop is not None and not self._theme_watch_stop.is_set()
        ):
            try:
                sig = _signature(theme_source_files(self._theme))
                if last is not None and sig != last:
                    self.refresh_theme()
                last = sig
            except Exception:
                logger.exception("theme auto-reload check failed")
            self._theme_watch_stop.wait(poll_interval)

    def _theme_message(self) -> dict[str, Any]:
        """Return the full ``theme_define`` message for the active theme."""
        return {"type": "theme_define", **self._theme_define_payload()}

    def _push_theme(self) -> None:
        """Push the active theme to all connected clients (thread-safe)."""
        self._transport.send(self._theme_message())

    def _theme_define_payload(self) -> dict[str, Any]:
        """Return the active theme's ``theme_define``-shaped payload (no ``type``)."""
        from ._themes import theme_css_files, theme_label

        return {
            "theme": self._theme,
            "label": theme_label(self._theme),
            "css": theme_css_files(self._theme),
            "version": self._theme_version,
        }


class InteractionHost(OverlayHost):
    """Object interaction: config, handler registration, event dispatch."""

    def __init__(self, transport: Any, layout: Any, registry: Any) -> None:
        super().__init__(transport, layout)
        from ._interaction import InteractionHandlerRegistry

        self._registry = registry
        self._interaction_registry = InteractionHandlerRegistry(registry)
        self._interaction_configs: dict[str, dict[str, Any]] = {}
        self._act_objects: dict[str, Any] = {}

    def set_interaction(
        self, object_id: str, config: Any, *, scene_name: str = ""
    ) -> None:
        """Set the interaction configuration for an entity."""
        self._interaction_configs.setdefault(scene_name, {})[object_id] = config
        scene = self._layout.scene(scene_name)
        scene.set_interaction(object_id, config)

    def on_interaction(
        self,
        object_id: str,
        event_type: Any,
        handler: Any,
        *,
        scene_name: str = "",
    ) -> None:
        """Register an async handler for interaction events on an entity."""
        from ._controls import HandlerOrigin

        self._transport.register(
            object_id,
            handler,
            event=event_type.value,
            origin=HandlerOrigin.INTERACTION,
        )

    async def _send_drag_anchor(self, event: Any) -> None:
        """Resolve the ideal drag anchor and rebase the event on it."""
        from ._interaction import DragEvent, InteractionEventType

        if not isinstance(event, DragEvent):
            return
        if event.event_type is not InteractionEventType.DRAG_START:
            return
        if not event.browser_id:
            return
        act = self._act_objects.get(event.object_id)
        if act is None:
            return
        try:
            anchor = act.drag_anchor(event.ray_origin, event.ray_direction)
        except NotImplementedError:
            return
        event.world_position = anchor
        await self._transport.send_to_browser(
            event.browser_id,
            {
                "type": "interaction:drag_anchor",
                "object_id": event.object_id,
                "world_position": [anchor.x, anchor.y, anchor.z],
            },
        )

    async def _resolve_click_anchor(self, event: Any) -> None:
        """Overwrite a CLICK event's world_position with the ideal anchor."""
        from ._interaction import ClickEvent, InteractionEventType

        if not isinstance(event, ClickEvent):
            return
        if event.event_type is not InteractionEventType.CLICK:
            return
        act = self._act_objects.get(event.object_id)
        if act is None:
            return
        if event.camera is None:
            return
        try:
            ray_origin, ray_direction = event.camera.pixel_ray(
                event.screen_position[0], event.screen_position[1]
            )
            anchor = act.drag_anchor(ray_origin, ray_direction)
        except NotImplementedError:
            return
        event.world_position = anchor

    async def _dispatch_interaction_event(
        self, msg_type: str, data: dict[str, Any]
    ) -> None:
        """Parse + dispatch an incoming interaction event."""
        from ._interaction import _parse_event

        try:
            event = _parse_event(data)
        except (ValueError, KeyError):
            return
        await self._send_drag_anchor(event)
        await self._resolve_click_anchor(event)
        await self._interaction_registry.dispatch(event)
