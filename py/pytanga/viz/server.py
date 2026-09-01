# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Lightweight HTTP + WebSocket server for the Tanga 3D viewer.

Serves the static HTML/JS frontend and provides a WebSocket endpoint
(``/ws``) for real-time scene updates.
Supports multiple named scenes reachable at ``/{name}`` paths.
"""

from __future__ import annotations

import asyncio
import errno
import hashlib
import json
import logging
import sys
import threading
import time
import webbrowser
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

from aiohttp import web

logger = logging.getLogger("tanga.viz.server")

# Unified client→server event envelope: short event name → legacy message type
# routed to the control callback.  Interaction events (``interaction:*``) are
# routed to the interaction callback instead (coalescing dispatcher).
_EVENT_MSG_MAP = {
    "change": "control:change",
    "click": "control:click",
    "press": "control:press",
    "release": "control:release",
    "cell_change": "control:cell_change",
    "row_add": "control:row_add",
    "column_add": "control:column_add",
    "row_delete": "control:row_delete",
    "group_toggle": "control:group_toggle",
    "close": "close",
    "file_browser_navigate": "file_browser_navigate",
    "file_browser_select": "file_browser_select",
}


class PortInUseError(RuntimeError):
    """Raised when the viewer server cannot bind its port because it is in use."""


# WinSock error code for "address already in use" (WSAEADDRINUSE).  Python's
# ``errno`` module exposes ``errno.EADDRINUSE`` on POSIX (98 on Linux, 48 on
# macOS/BSD), but on Windows socket errors carry the raw WinSock code (10048)
# instead of the CRT value that ``errno.EADDRINUSE`` holds there (100).
_WSAEADDRINUSE = 10048


def _is_port_in_use_error(exc: OSError) -> bool:
    """Return ``True`` if ``exc`` reports that the port is already in use.

    The errno differs per platform: ``EADDRINUSE`` on POSIX, ``WSAEADDRINUSE``
    (10048) on Windows.  The WinSock error also has its own message text, so
    match that wording as a fallback for cases where the error is re-wrapped.
    """
    if getattr(exc, "errno", None) in (errno.EADDRINUSE, _WSAEADDRINUSE):
        return True
    if getattr(exc, "winerror", None) == _WSAEADDRINUSE:
        return True
    message = str(exc).lower()
    return (
        "address already in use" in message
        or "only one usage of each socket address" in message
    )


def compute_frontend_version(static_dir: Path) -> str:
    """Return a stable content hash over the frontend assets.

    The hash covers every file under ``static_dir`` (the live viewer's
    template directory), keyed by its path relative to ``static_dir`` so that
    renames are detected as well as content edits.  The backend injects this
    hash into the served ``viewer.html`` and advertises it over the WebSocket
    handshake so the browser can detect a stale, cached frontend.
    """
    h = hashlib.sha256()
    for p in sorted(static_dir.rglob("*")):
        if p.is_file():
            h.update(str(p.relative_to(static_dir)).encode("utf-8"))
            h.update(b"\0")
            h.update(p.read_bytes())
    return h.hexdigest()[:16]


def _ws_msg_brief(payload: Any) -> str:
    """Return a concise description of a WebSocket message for diagnostics."""
    if isinstance(payload, str):
        raw = payload
        try:
            obj = json.loads(raw)
        except Exception:
            return f"<non-json {len(raw)}B>"
    else:
        obj = payload
        raw = json.dumps(obj) if isinstance(obj, dict) else ""
    size = len(raw)
    t = obj.get("type", "?") if isinstance(obj, dict) else "?"

    if t == "object_update":
        return (
            f"object_update patches={len(obj.get('patches', []))} "
            f"removed={len(obj.get('removed', []))} "
            f"scene={obj.get('scene', '')!r} ({size}B)"
        )
    if t == "scene_update":
        return (
            f"scene_update objects={len(obj.get('objects', []))} "
            f"removed={len(obj.get('removed', []))} "
            f"scene={obj.get('scene', '')!r} ({size}B)"
        )
    if t == "controls_define":
        return (
            f"controls_define controls={len(obj.get('controls', []))} "
            f"groups={len(obj.get('groups', []))} "
            f"scene={obj.get('scene', '')!r} ({size}B)"
        )
    if t == "scene_config":
        return (
            f"scene_config name={obj.get('name', '')!r} "
            f"space_dim={obj.get('space_dim', '?')} ({size}B)"
        )
    if t == "scene_list":
        return f"scene_list scenes={obj.get('scenes', [])} ({size}B)"
    if t == "browser_id":
        return (
            f"browser_id id={obj.get('browser_id', '')!r} "
            f"v={obj.get('frontend_version', '?')} ({size}B)"
        )
    if t == "ready":
        return (
            f"ready scene={obj.get('scene', '')!r} "
            f"token={obj.get('page_token') or 'none'} "
            f"browser_id={obj.get('browser_id') or 'none'} ({size}B)"
        )
    if t == "clear_all":
        return f"clear_all ({size}B)"
    if t == "navigate":
        return f"navigate scene={obj.get('scene', '')!r} ({size}B)"
    if t == "control_update":
        return (
            f"control_update id={obj.get('id', '')!r} "
            f"scene={obj.get('scene', '')!r} ({size}B)"
        )
    if t == "control:cell_change":
        return (
            f"control:cell_change id={obj.get('control_id', '')!r} "
            f"row={obj.get('row', '?')} col={obj.get('col', '?')} ({size}B)"
        )
    if t == "control:row_add":
        return (
            f"control:row_add id={obj.get('control_id', '')!r} "
            f"row={obj.get('row', '?')} ({size}B)"
        )
    if t == "control:column_add":
        return (
            f"control:column_add id={obj.get('control_id', '')!r} "
            f"col={obj.get('col', '?')} ({size}B)"
        )
    if t == "control:row_delete":
        return (
            f"control:row_delete id={obj.get('control_id', '')!r} "
            f"rows={obj.get('rows', '?')} ({size}B)"
        )
    return f"type={t} ({size}B)"


async def _heartbeat(ws: web.WebSocketResponse, interval: float = 15.0) -> None:
    """Send periodic pings so dead/half-open connections are detected.

    A failed ``ping()`` surfaces as a ``WSMsgType.ERROR`` in the connection's
    message loop, which breaks the loop and triggers cleanup.
    """
    try:
        while not ws.closed:
            await asyncio.sleep(interval)
            await ws.ping()
    except (ConnectionError, Exception):
        pass


# Callback types
FlushCallback = Callable[[str], tuple[list[dict[str, Any]], list[str]]]
ConfigCallback = Callable[[], dict[str, Any]]
SceneConfigCallback = Callable[[str], dict[str, Any] | None]
ControlCallback = Callable[[str, dict[str, Any]], Awaitable[None]]
InteractionCallback = Callable[[str, dict[str, Any]], Awaitable[None]]
SceneListCallback = Callable[[], list[str]]
LayoutCallback = Callable[[str], dict[str, Any] | None]
PushControlsCallback = Callable[[str], Awaitable[None]]


@dataclass
class BrowserSession:
    """A connected WebSocket client browsing one or more scenes."""

    id: str  # unique browser ID (UUID)
    scene: str  # currently viewed scene name ("" = main; first scene for layouts)
    remote_addr: str
    ws: web.WebSocketResponse
    viewer_name: str | None = None  # optional friendly label from ?viewer= URL param
    scenes: list[str] = field(default_factory=list)  # all subscribed scene names


class VizServer:
    """Lightweight HTTP + WebSocket server for the Tanga 3D viewer.

    Combines static file serving (HTML/JS) and a WebSocket endpoint on a
    single port.  Supports multiple named scenes via URL path routing.
    """

    def __init__(
        self,
        *,
        host: str = "localhost",
        port: int = 8765,
        static_dir: Path | None = None,
        entry_page: str = "viewer.html",
    ) -> None:
        self._host = host
        self._port = port
        self._static_dir = static_dir or Path(__file__).parent / "templates"
        self._entry_page = entry_page
        self._frontend_version = compute_frontend_version(self._static_dir)
        self._app: web.Application | None = None
        self._runner: web.AppRunner | None = None
        self._sites: list[web.TCPSite] = []
        self._ws_clients: set[web.WebSocketResponse] = set()
        self._browser_sessions: dict[str, BrowserSession] = {}
        self._flush_callback: FlushCallback | None = None
        self._config_callback: ConfigCallback | None = None
        self._scene_config_callback: SceneConfigCallback | None = None
        self._scene_list_callback: SceneListCallback | None = None
        self._layout_callback: LayoutCallback | None = None
        self._control_callback: ControlCallback | None = None
        self._animation_stop_callback: Callable[[str, str], Awaitable[None]] | None = (
            None
        )
        self._push_animation_stop: Callable[[str], Awaitable[None]] | None = None
        self._on_connect: Callable[[str], Awaitable[None]] | None = None
        self._on_disconnect: Callable[[str], Awaitable[None]] | None = None
        self._pending_screenshots: dict[str, asyncio.Future[Any]] = {}
        self._pending_page_tokens: dict[str, dict[str, Any]] = {}
        self._any_ws_ready: asyncio.Event = asyncio.Event()
        self._any_ws_ready_thread: threading.Event = threading.Event()
        self._ws_error_event: asyncio.Event = asyncio.Event()
        self._ws_error_msg: str = ""

    # ── Lifecycle ───────────────────────────────────────────

    async def start(
        self,
        flush_callback: FlushCallback,
        config_callback: ConfigCallback,
        *,
        control_callback: ControlCallback | None = None,
        interaction_callback: InteractionCallback | None = None,
        on_connect: Callable[[str], Awaitable[None]] | None = None,
        on_disconnect: Callable[[str], Awaitable[None]] | None = None,
        push_controls: PushControlsCallback | None = None,
        animation_stop_callback: Callable[[str, str], Awaitable[None]] | None = None,
        push_animation_stop: Callable[[str], Awaitable[None]] | None = None,
        scene_config_callback: SceneConfigCallback | None = None,
        scene_list_callback: SceneListCallback | None = None,
        layout_callback: LayoutCallback | None = None,
        on_ready: Callable[[], None] | None = None,
    ) -> None:
        """Build and start the aiohttp application (non-blocking setup)."""
        self._flush_callback = flush_callback
        self._config_callback = config_callback
        self._scene_config_callback = scene_config_callback
        self._scene_list_callback = scene_list_callback
        self._layout_callback = layout_callback
        self._control_callback = control_callback
        self._interaction_callback = interaction_callback
        self._on_connect = on_connect
        self._on_disconnect = on_disconnect
        self._push_controls_cb = push_controls
        self._animation_stop_callback = animation_stop_callback
        self._push_animation_stop = push_animation_stop
        self._on_ready = on_ready
        self._app = self._build_app()

        self._runner = web.AppRunner(self._app)
        await self._runner.setup()
        try:
            # When host is "localhost", bind both IPv4 and IPv6 loopback so
            # browsers that resolve `localhost` to `::1` can still reach the
            # WebSocket endpoint — otherwise Firefox's WS connection can hang
            # in CONNECTING on Windows (the server would only listen on IPv4).
            reuse_address = sys.platform != "win32"
            bind_hosts = (
                ["127.0.0.1", "::1"] if self._host == "localhost" else [self._host]
            )

            self._sites = []
            for bind_host in bind_hosts:
                site = web.TCPSite(
                    self._runner, bind_host, self._port, reuse_address=reuse_address
                )
                try:
                    await site.start()
                    self._sites.append(site)
                except OSError:
                    # The primary (IPv4) bind must succeed; the IPv6 loopback
                    # bind is best-effort (may be unavailable on some systems).
                    if not self._sites:
                        raise
                    logger.info("Could not bind to %s (skipping)", bind_host)

            logger.info(
                "Server listening: bind=%s port=%d (http://%s:%d, ws /ws)",
                ",".join(bind_hosts[: len(self._sites)]),
                self._port,
                self._host,
                self._port,
            )
        except OSError as e:
            if _is_port_in_use_error(e):
                raise PortInUseError(
                    f"Port {self._port} is already in use. "
                    f"Close the other process or use start_server(port=...) "
                    f"to choose a different port."
                ) from e
            raise

    async def stop(self) -> None:
        """Gracefully shut down all connections and the server."""
        for ws in list(self._ws_clients):
            await ws.close(
                code=1001,  # aiohttp.WSCloseCode.GOING_AWAY
                message=b"Server shutting down",
            )
        self._ws_clients.clear()
        self._browser_sessions.clear()

        if self._sites:
            for site in self._sites:
                await site.stop()
            self._sites.clear()
        if self._runner is not None:
            await self._runner.cleanup()

    # ── Push ──────────────────────────────────────────────

    async def push(
        self,
        entities: list[dict[str, Any]],
        removed: list[str],
        *,
        scene: str = "",
        fit_camera: bool = False,
    ) -> None:
        """Serialize and broadcast a scene update to all WebSocket clients."""
        from .serializer import serialize_scene_update

        if not self._ws_clients:
            return

        message = serialize_scene_update(entities, removed)
        message["scene"] = scene
        if fit_camera:
            message["fit_camera"] = True
        data = json.dumps(message)
        logger.info(
            "WS SEND t=%.3f %s clients=%d",
            time.monotonic(),
            _ws_msg_brief(data),
            len(self._ws_clients),
        )

        dead: list[web.WebSocketResponse] = []
        for ws in self._ws_clients:
            try:
                await ws.send_str(data)
            except (ConnectionError, Exception):
                dead.append(ws)

        for ws in dead:
            self._ws_clients.discard(ws)

    async def push_raw(self, data: str) -> None:
        """Send an arbitrary JSON string to all connected clients."""
        if not self._ws_clients:
            return
        logger.info(
            "WS SEND t=%.3f %s clients=%d",
            time.monotonic(),
            _ws_msg_brief(data),
            len(self._ws_clients),
        )
        dead: list[web.WebSocketResponse] = []
        for ws in self._ws_clients:
            try:
                await ws.send_str(data)
            except (ConnectionError, Exception):
                dead.append(ws)
        for ws in dead:
            self._ws_clients.discard(ws)

    async def push_raw_to_browser(self, browser_id: str, data: str) -> None:
        """Send an arbitrary JSON string to a single browser session."""
        session = self._browser_sessions.get(browser_id)
        if session is None:
            return
        logger.info(
            "WS SEND t=%.3f %s browser=%s",
            time.monotonic(),
            _ws_msg_brief(data),
            browser_id,
        )
        try:
            await session.ws.send_str(data)
        except (ConnectionError, Exception):
            pass

    async def push_navigate(self, scene_name: str, target: str = "all") -> None:
        """Send a navigate command to matching browser sessions.

        Args:
            scene_name: The target scene name (empty string = main).
            target: One of ``"all"``, ``"scene:<name>"``, or ``"browser:<id>"``.
        """
        message = json.dumps({"type": "navigate", "scene": scene_name})

        matching: list[BrowserSession] = []
        if target == "all":
            matching = list(self._browser_sessions.values())
        elif target.startswith("scene:"):
            scene_filter = target[len("scene:") :]
            matching = [
                s for s in self._browser_sessions.values() if s.scene == scene_filter
            ]
        elif target.startswith("viewer:"):
            viewer_filter = target[len("viewer:") :]
            matching = [
                s
                for s in self._browser_sessions.values()
                if s.viewer_name == viewer_filter
            ]
        elif target.startswith("browser:"):
            browser_id = target[len("browser:") :]
            session = self._browser_sessions.get(browser_id)
            if session:
                matching = [session]

        for session in matching:
            try:
                await session.ws.send_str(message)
            except (ConnectionError, Exception):
                pass

    async def _push_full_state(
        self,
        ws: web.WebSocketResponse,
        *,
        scene_names: list[str],
        layout_payload: dict[str, Any] | None = None,
        browser_id: str | None = None,
    ) -> None:
        """Send optional ``view_layout`` then per-scene config + full state."""
        from .serializer import serialize_scene_update

        logger.info(
            "WS FULL-STATE-BEGIN t=%.3f id=%s scenes=%r",
            time.monotonic(),
            browser_id,
            scene_names,
        )

        # 0. Clear the browser first (handles reconnect with new server)
        clear_payload = json.dumps({"type": "clear_all"})
        logger.info(
            "WS SEND t=%.3f id=%s %s",
            time.monotonic(),
            browser_id,
            _ws_msg_brief(clear_payload),
        )
        await ws.send_str(clear_payload)
        # Small delay to ensure clear_all is processed before subsequent messages
        await asyncio.sleep(0.05)

        # 1. Layout (if any) — sent before any scene data
        if layout_payload is not None:
            layout_json = json.dumps(layout_payload)
            logger.info(
                "WS SEND t=%.3f id=%s %s",
                time.monotonic(),
                browser_id,
                _ws_msg_brief(layout_json),
            )
            await ws.send_str(layout_json)

        # 2. Per scene: configuration + full state
        for scene_name in scene_names:
            cfg = None
            if self._scene_config_callback is not None:
                cfg = self._scene_config_callback(scene_name)
            elif self._config_callback is not None:
                cfg = self._config_callback()

            if cfg is not None:
                cfg.setdefault("name", scene_name)
                cfg_payload = json.dumps(cfg)
                logger.info(
                    "WS SEND t=%.3f id=%s %s",
                    time.monotonic(),
                    browser_id,
                    _ws_msg_brief(cfg_payload),
                )
                await ws.send_str(cfg_payload)

            if self._flush_callback is not None:
                entities, _ = self._flush_callback(scene_name)
                if entities:
                    msg = serialize_scene_update(entities, [])
                    msg["scene"] = scene_name
                    state_payload = json.dumps(msg)
                    logger.info(
                        "WS SEND t=%.3f id=%s %s",
                        time.monotonic(),
                        browser_id,
                        _ws_msg_brief(state_payload),
                    )
                    await ws.send_str(state_payload)

        # 3. Scene list (so the frontend knows available scenes)
        if self._scene_list_callback is not None:
            scene_names_all = self._scene_list_callback()
            list_payload = json.dumps(
                {"type": "scene_list", "scenes": scene_names_all, "default": ""}
            )
            logger.info(
                "WS SEND t=%.3f id=%s %s",
                time.monotonic(),
                browser_id,
                _ws_msg_brief(list_payload),
            )
            await ws.send_str(list_payload)

        logger.info(
            "WS FULL-STATE-END t=%.3f id=%s scenes=%r",
            time.monotonic(),
            browser_id,
            scene_names,
        )

    # ── Browser sessions (read-only access for Visualizer) ─

    def _clear_ws_ready_events(self) -> None:
        """Clear both the asyncio.Event and its threading mirror.

        Must be called from the event loop.
        """
        logger.debug(
            "Clearing WS ready events (was_ready=%s)",
            self._any_ws_ready.is_set(),
        )
        self._any_ws_ready.clear()
        self._any_ws_ready_thread.clear()
        self._ws_error_event.clear()

    def _signal_ws_ready(self) -> None:
        """Set the ready events and invoke ``_on_ready`` (idempotent)."""
        if self._any_ws_ready.is_set():
            return
        self._any_ws_ready.set()
        self._any_ws_ready_thread.set()
        if self._on_ready is not None:
            self._on_ready()

    def get_browser_sessions(self) -> list[dict[str, str | None]]:
        """Return a list of active browser sessions as plain dicts."""
        return [
            {
                "id": s.id,
                "scene": s.scene,
                "remote_addr": s.remote_addr,
                "viewer_name": s.viewer_name,
            }
            for s in self._browser_sessions.values()
        ]

    # ── Internals ─────────────────────────────────────────

    def _build_app(self) -> web.Application:
        app = web.Application()
        app.router.add_get("/ws", self._ws_handler)
        # Catch-all route: serve static files if they exist, otherwise serve
        # viewer.html (SPA-style scene URL routing).
        app.router.add_get("/{name:.*}", self._catch_all_handler)
        return app

    async def _catch_all_handler(self, request: web.Request) -> web.StreamResponse:
        """Serve a static file if it exists, otherwise serve viewer.html.

        This handles both static assets (JS modules, CSS, renderers) and
        scene-URL routing (/, /scene1, /group/sub).  When the requested
        path maps to a file in the templates directory, it is served
        directly (with the correct MIME type).  Otherwise, viewer.html
        is served with an injected page token for WebSocket connectivity
        diagnostics.
        """
        rel_path = request.match_info.get("name", "")
        remote_addr = request.remote or "unknown"
        if rel_path:
            file_path = self._static_dir / rel_path
            if file_path.is_file():
                logger.debug("HTTP GET /%s -> static file -> %s", rel_path, remote_addr)
                return web.FileResponse(
                    file_path, headers={"Cache-Control": "no-cache"}
                )
            # If the path looks like a static file request (has a file
            # extension, e.g. /favicon.ico), return 404 instead of
            # serving viewer.html — avoids bogus page-load prints.
            if "." in rel_path.rsplit("/", 1)[-1]:
                logger.debug(
                    "HTTP GET /%s -> 404 (unknown static) -> %s", rel_path, remote_addr
                )
                raise web.HTTPNotFound()

        # Inject a page token for WS connectivity correlation
        # Use token from URL query param if present, otherwise generate random
        viewer_path = self._static_dir / self._entry_page
        page_token = request.query.get("token") or uuid4().hex[:8]
        logger.info(
            "HTTP GET / -> serving viewer.html (token=%s) -> %s",
            page_token,
            remote_addr,
        )
        self._pending_page_tokens[page_token] = {
            "remote_addr": remote_addr,
            "token": page_token,
            "timestamp": asyncio.get_running_loop().time(),
        }

        # Print initial page-load note
        self._print_page_load(remote_addr, page_token)

        html = viewer_path.read_text(encoding="utf-8")
        inject = (
            f'<script>window.__tanga_page_token = "{page_token}";</script>\n'
            f"<script>window.__tanga_frontend_version = "
            f'"{self._frontend_version}";</script>'
        )
        # Inject after <head> or at start of file
        if "</head>" in html:
            html = html.replace("</head>", f"{inject}\n</head>")
        else:
            html = inject + "\n" + html

        resp = web.StreamResponse(
            status=200,
            reason="OK",
            headers={
                "Content-Type": "text/html; charset=utf-8",
                "Cache-Control": "no-cache",
            },
        )
        resp.content_length = len(html.encode("utf-8"))
        await resp.prepare(request)
        await resp.write(html.encode("utf-8"))
        await resp.write_eof()
        return resp

    async def _ws_handler(self, request: web.Request) -> web.WebSocketResponse:
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self._ws_clients.add(ws)

        remote_addr = request.remote or "unknown"
        logger.info(
            "WS connect from %s (total_clients=%d, sessions=%d)",
            remote_addr,
            len(self._ws_clients),
            len(self._browser_sessions),
        )

        # Assign a unique browser ID and send it immediately
        browser_id = uuid4().hex[:8]
        session = BrowserSession(
            id=browser_id, scene="", remote_addr=remote_addr, ws=ws
        )
        self._browser_sessions[browser_id] = session
        logger.debug("WS session assigned id=%s remote=%s", browser_id, remote_addr)

        heartbeat_task = asyncio.create_task(_heartbeat(ws))
        logger.debug("WS heartbeat started id=%s", browser_id)

        bid_payload = json.dumps(
            {
                "type": "browser_id",
                "browser_id": browser_id,
                "frontend_version": self._frontend_version,
            }
        )
        logger.info(
            "WS SEND t=%.3f id=%s %s",
            time.monotonic(),
            browser_id,
            _ws_msg_brief(bid_payload),
        )
        await ws.send_str(bid_payload)

        # The frontend will send a "ready" message with the scene name.
        # We handle initialization inside the message loop.

        if self._on_connect is not None:
            await self._on_connect(remote_addr)

        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        msg_type = data.get("type", "")

                        # Always update browser_id from incoming messages
                        msg_browser_id = data.get("browser_id")
                        if msg_browser_id and msg_browser_id in self._browser_sessions:
                            current_session = self._browser_sessions[msg_browser_id]
                        else:
                            # Fallback: use the session we created
                            current_session = session
                            msg_browser_id = browser_id

                        logger.info(
                            "WS RECV t=%.3f %s from %s (id=%s)",
                            time.monotonic(),
                            _ws_msg_brief(data),
                            remote_addr,
                            msg_browser_id,
                        )

                        if msg_type == "ready":
                            scene_name = data.get("scene", "")
                            layout_name = data.get("layout")
                            # Correlate page token if present (HTTP→WS round-trip diagnostic)
                            page_token = data.get("page_token")
                            if page_token:
                                self._pending_page_tokens.pop(page_token, None)
                            logger.info(
                                "WS ready: id=%s token=%s viewer=%s scene=%s remote=%s "
                                "sessions=%d pending_tokens=%d - signalling ready",
                                msg_browser_id,
                                page_token or "reconnect",
                                data.get("viewer_name") or "none",
                                scene_name,
                                remote_addr,
                                len(self._browser_sessions),
                                len(self._pending_page_tokens),
                            )

                            # Handle CDN / load errors reported by the frontend
                            if data.get("error"):
                                self._ws_error_msg = data.get(
                                    "error_msg", data.get("error", "unknown error")
                                )
                                logger.error(
                                    "WS ready with error from %s: %s - %s",
                                    remote_addr,
                                    data.get("error"),
                                    self._ws_error_msg,
                                )
                                self._ws_error_event.set()
                                continue

                            # Print comprehensive connection summary
                            self._print_ws_connected(
                                remote_addr,
                                page_token,
                                msg_browser_id,
                                data.get("viewer_name"),
                            )
                            # Resolve the set of scenes to subscribe to.
                            layout_payload: dict[str, Any] | None = None
                            if layout_name is not None:
                                # Layout mode: subscribe to every scene in the layout.
                                if self._layout_callback is not None:
                                    layout_payload = self._layout_callback(layout_name)
                                if layout_payload is None:
                                    # Unknown layout — navigate to main.
                                    await ws.send_str(
                                        json.dumps({"type": "navigate", "scene": ""})
                                    )
                                    scene_names = [""]
                                else:
                                    names = layout_payload.get("scenes") or []
                                    scene_names = list(names) if names else [""]
                            else:
                                # Single-scene mode (existing behaviour).
                                if self._scene_list_callback is not None:
                                    available = self._scene_list_callback()
                                    if scene_name and scene_name not in available:
                                        # Scene doesn't exist — navigate to main
                                        await ws.send_str(
                                            json.dumps(
                                                {"type": "navigate", "scene": ""}
                                            )
                                        )
                                        scene_name = ""
                                scene_names = [scene_name]

                            current_session.scenes = list(scene_names)
                            current_session.scene = scene_names[0]
                            # Store viewer_name from the ready message
                            viewer_name = data.get("viewer_name")
                            if viewer_name:
                                current_session.viewer_name = viewer_name

                            # Push the full state first, then signal ready on the
                            # frontend's "scene_synced" ack, so the user's
                            # incremental flushes (scheduled after viz.start()
                            # returns) can't race with the initial full-state
                            # push. A short fallback timer keeps old/cached
                            # frontends (that never ack) from hanging start().
                            try:
                                await self._push_full_state(
                                    ws,
                                    scene_names=scene_names,
                                    layout_payload=layout_payload,
                                    browser_id=browser_id,
                                )
                            except Exception:
                                pass
                            for scene_name in scene_names:
                                try:
                                    if self._push_controls_cb is not None:
                                        await self._push_controls_cb(scene_name)
                                except Exception:
                                    pass
                                try:
                                    if self._push_animation_stop is not None:
                                        await self._push_animation_stop(scene_name)
                                except Exception:
                                    pass
                            # Fallback for frontends that never send "scene_synced".
                            asyncio.get_running_loop().call_later(
                                1.0, self._signal_ws_ready
                            )

                        elif msg_type == "scene_synced":
                            logger.info(
                                "WS scene_synced from %s (id=%s) - signalling ready",
                                remote_addr,
                                msg_browser_id,
                            )
                            self._signal_ws_ready()

                        elif msg_type == "animation_stop":
                            if self._animation_stop_callback is not None:
                                asyncio.create_task(
                                    self._animation_stop_callback(
                                        data.get("scene", ""),
                                        data.get("scope", "scene"),
                                    )
                                )
                        elif msg_type == "screenshot:data":
                            rid = data.get("request_id")
                            if rid and rid in self._pending_screenshots:
                                if not self._pending_screenshots[rid].done():
                                    self._pending_screenshots[rid].set_result(
                                        data["data"]
                                    )
                        elif msg_type == "event":
                            # Unified envelope: { type, target, event, data }.
                            target = data.get("target")
                            event_name = data.get("event")
                            event_data = data.get("data") or {}
                            if event_name and event_name.startswith("interaction:"):
                                if self._interaction_callback is not None:
                                    event_data["object_id"] = target
                                    if msg_browser_id:
                                        event_data["browser_id"] = msg_browser_id
                                    asyncio.create_task(
                                        self._interaction_callback(
                                            event_name, event_data
                                        )
                                    )
                            elif self._control_callback is not None and target:
                                event_data["control_id"] = target
                                if msg_browser_id:
                                    event_data["browser_id"] = msg_browser_id
                                asyncio.create_task(
                                    self._control_callback(
                                        _EVENT_MSG_MAP.get(event_name, event_name),
                                        event_data,
                                    )
                                )
                        elif msg_type in (
                            "control:change",
                            "control:click",
                            "control:cell_change",
                            "control:row_add",
                            "control:column_add",
                            "control:row_delete",
                            "control:group_toggle",
                            "control:press",
                            "control:release",
                            "banner_closed",
                            "editor_closed",
                            "file_browser_navigate",
                            "file_browser_select",
                        ):
                            # Inject browser_id into the payload for the callback
                            if msg_browser_id:
                                data["browser_id"] = msg_browser_id
                            if self._control_callback is not None:
                                asyncio.create_task(
                                    self._control_callback(msg_type, data)
                                )
                        elif msg_type.startswith("interaction:"):
                            if self._interaction_callback is not None:
                                if msg_browser_id:
                                    data["browser_id"] = msg_browser_id
                                asyncio.create_task(
                                    self._interaction_callback(msg_type, data)
                                )
                    except json.JSONDecodeError:
                        pass
                elif msg.type == web.WSMsgType.ERROR:
                    break
        finally:
            heartbeat_task.cancel()
            logger.debug("WS heartbeat stopped id=%s", browser_id)
            close_code = getattr(ws, "close_code", None)
            logger.info(
                "WS disconnect from %s (id=%s, close_code=%s, "
                "clients_remaining=%d, sessions_remaining=%d)",
                remote_addr,
                browser_id,
                close_code,
                len(self._ws_clients) - 1,
                len(self._browser_sessions) - 1,
            )
            # Clean up pending futures for this client
            for rid, future in list(self._pending_screenshots.items()):
                if not future.done():
                    try:
                        future.set_exception(
                            RuntimeError("WebSocket client disconnected")
                        )
                    except asyncio.InvalidStateError:
                        pass
            self._ws_clients.discard(ws)
            self._browser_sessions.pop(browser_id, None)
            if self._on_disconnect is not None:
                await self._on_disconnect(remote_addr)

        return ws

    # ── Screenshot ───────────────────────────────────────

    async def request_screenshot(
        self,
        *,
        width: int | None = None,
        height: int | None = None,
        timeout: float = 5.0,
    ) -> bytes:
        """Send a screenshot request and return the PNG bytes.

        Sends ``{"type": "screenshot", "request_id": "..."}`` to all
        connected WebSocket clients and waits for the first
        ``{"type": "screenshot:data", "request_id": "...", "data": "..."}``
        response.

        Args:
            width: Optional canvas width override.
            height: Optional canvas height override.
            timeout: Seconds to wait for a browser response.

        Returns:
            Raw PNG image bytes.

        Raises:
            RuntimeError: If no WebSocket clients are connected.
            TimeoutError: If no response arrives within *timeout* seconds.
        """
        if not self._ws_clients:
            # Wait a bit for the client to connect (up to the requested timeout)
            connected = await self.wait_for_client(timeout=timeout)
            if not connected:
                raise RuntimeError(
                    "No browser connected. Open the viewer in a browser first."
                )

        import uuid

        request_id = uuid.uuid4().hex[:8]
        future: asyncio.Future[Any] = asyncio.get_running_loop().create_future()
        self._pending_screenshots[request_id] = future

        msg: dict[str, Any] = {"type": "screenshot", "request_id": request_id}
        if width is not None:
            msg["width"] = width
        if height is not None:
            msg["height"] = height

        try:
            await self.push_raw(json.dumps(msg))
            data_url = await asyncio.wait_for(future, timeout=timeout)
        except TimeoutError:
            raise TimeoutError(
                f"Screenshot request timed out after {timeout}s"
            ) from None
        finally:
            self._pending_screenshots.pop(request_id, None)

        # Strip "data:image/png;base64," prefix and decode
        import base64

        _, b64 = data_url.split(",", 1)
        return base64.b64decode(b64)

    # ── Convenience ───────────────────────────────────────

    @property
    def url(self) -> str:
        """The HTTP URL of the viewer."""
        return f"http://{self._host}:{self._port}"

    def _print_page_load(self, remote_addr: str, page_token: str) -> None:
        """Print an initial note when a browser loads the HTML page."""
        try:
            from rich.console import Console
            from rich.text import Text

            Console().print(
                Text.assemble(
                    "Browser at ",
                    Text(remote_addr, style="cyan"),
                    " loaded page (token: ",
                    Text(page_token, style="dim"),
                    ")",
                    style="dim",
                )
            )
        except Exception:
            print(f"Browser at {remote_addr} loaded page (token: {page_token}).")

    def _print_ws_connected(
        self,
        remote_addr: str,
        page_token: str | None,
        browser_id: str,
        viewer_name: str | None,
    ) -> None:
        """Print a final note when the WebSocket round-trip completes."""
        parts = [f"id={browser_id}"]
        if page_token:
            parts.append(f"token={page_token}")
        if viewer_name:
            parts.append(f"viewer={viewer_name}")
        parts.append(f"ip={remote_addr}")
        detail = ", ".join(parts)
        try:
            from rich.console import Console
            from rich.text import Text

            Console().print(
                Text(f"✓ Browser connected  ({detail})", style="bold green")
            )
        except Exception:
            # rich (or the console encoding) can fail on non-UTF-8 consoles
            # (e.g. cp1252 on Windows); fall back to an ASCII-safe print so a
            # display failure can never crash the WebSocket handler.
            print(f"[OK] Browser connected  ({detail})")

    def _print_ws_reachability_note(self) -> None:
        """Print a note about WebSocket reachability for port forwarding setups."""
        ws_url = f"ws://{self._host}:{self._port}/ws"
        note = (
            "Note: the WebSocket connection ("
            + ws_url
            + ") must also be reachable from the\n"
            "browser. If using port forwarding or a reverse proxy, ensure WebSocket\n"
            "upgrade requests are forwarded - otherwise the viewer will render an\n"
            "empty 3D scene.\n"
        )
        try:
            from rich.console import Console
            from rich.text import Text

            Console().print(Text(note, style="dim"))
        except Exception:
            print(note)

    async def check_page_tokens(
        self, delay: float = 5.0, token_timeout: float = 10.0
    ) -> None:
        """After *delay* seconds, warn about page loads that never opened a WebSocket.

        For each page token that was served in ``viewer.html`` but hasn't been
        matched by a ``ready`` WebSocket message within *token_timeout* seconds,
        print a diagnostic warning.

        Args:
            delay: Seconds to wait before the first check.
            token_timeout: Maximum age of a pending token before warning.
        """
        await asyncio.sleep(delay)

        now = asyncio.get_running_loop().time()
        stale: list[dict[str, Any]] = []
        for token, info in list(self._pending_page_tokens.items()):
            if now - info["timestamp"] > token_timeout:
                stale.append(info)
                del self._pending_page_tokens[token]

        if not stale:
            return

        ws_url = f"ws://{self._host}:{self._port}/ws"
        for info in stale:
            logger.warning(
                "Browser at %s loaded page (token=%s) but WebSocket never connected. "
                "Check that %s is reachable.",
                info["remote_addr"],
                info["token"],
                ws_url,
            )

    def open_browser(self, path: str = "") -> None:
        """Open the viewer URL in the default browser with graceful fallback.

        Args:
            path: Optional URL path/query to append (e.g. ``"/?token=abc123"``).
        """
        url = self.url + path
        logger.info("Opening browser: %s", url)
        try:
            ok = webbrowser.open(url)
            if ok:
                return
        except Exception:
            pass

        try:
            from rich.console import Console
            from rich.panel import Panel
            from rich.text import Text

            console = Console()
            url_text = Text(url, style="bold cyan underline")
            panel = Panel(
                Text.assemble(
                    "[yellow]Could not open browser automatically.[/yellow]\n",
                    "Open ",
                    url_text,
                    " manually to view the scene.",
                ),
                border_style="yellow",
                padding=(1, 2),
            )
            console.print(panel)
        except ImportError:
            print("Could not open browser automatically.")
            print(f"Open {url} manually to view the scene.")

    async def wait_for_client(self, timeout: float = 30.0) -> bool:
        """Wait until at least one WebSocket client connects.

        Returns ``True`` if a client connected, ``False`` on timeout.
        """
        import time as _time

        deadline = _time.monotonic() + timeout
        while _time.monotonic() < deadline:
            if self._ws_clients:
                logger.debug(
                    "WS client connected after %.1fs",
                    timeout - (deadline - _time.monotonic()),
                )
                return True
            await asyncio.sleep(0.5)
        logger.info("wait_for_client timed out after %.0fs", timeout)
        return False

    async def wait_for_ws_ready(self, *, timeout: float = 30.0) -> bool:
        """Wait until at least one browser completes the WebSocket ready round-trip.

        Returns ``True`` if a ready message was received, ``False`` on timeout.
        Raises ``ConnectionError`` if the browser reports a load error (e.g. CDN
        failure).
        """
        if self._any_ws_ready.is_set():
            logger.debug("WS ready already set")
            return True
        if self._ws_error_event.is_set():
            raise ConnectionError(self._ws_error_msg or "Browser reported a load error")
        import time as _time

        start = _time.monotonic()
        logger.debug("Waiting for WS ready (timeout=%.0fs)...", timeout)
        done, _ = await asyncio.wait(
            [
                asyncio.create_task(self._any_ws_ready.wait()),
                asyncio.create_task(self._ws_error_event.wait()),
            ],
            timeout=timeout,
            return_when=asyncio.FIRST_COMPLETED,
        )
        elapsed = _time.monotonic() - start
        if self._ws_error_event.is_set():
            raise ConnectionError(self._ws_error_msg or "Browser reported a load error")
        if self._any_ws_ready.is_set():
            logger.info("WS ready received after %.1fs", elapsed)
            return True
        logger.info("WS ready timed out after %.1fs", elapsed)
        return False
