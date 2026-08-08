# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Lightweight HTTP + WebSocket server for the Tanga 3D viewer.

Serves the static HTML/JS frontend and provides a WebSocket endpoint
(``/ws``) for real-time scene updates.
Supports multiple named scenes reachable at ``/{name}`` paths.
"""

from __future__ import annotations

import asyncio
import json
import webbrowser
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

from aiohttp import web

# Callback types
FlushCallback = Callable[[str], tuple[list[dict[str, Any]], list[str]]]
ConfigCallback = Callable[[], dict[str, Any]]
SceneConfigCallback = Callable[[str], dict[str, Any] | None]
ControlCallback = Callable[[str, dict[str, Any]], Awaitable[None]]
SceneListCallback = Callable[[], list[str]]
PushControlsCallback = Callable[[str], Awaitable[None]]


@dataclass
class BrowserSession:
    """A connected WebSocket client browsing a specific scene."""

    id: str  # unique browser ID (UUID)
    scene: str  # currently viewed scene name ("" = main)
    remote_addr: str
    ws: web.WebSocketResponse
    viewer_name: str | None = None  # optional friendly label from ?viewer= URL param


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
    ) -> None:
        self._host = host
        self._port = port
        self._static_dir = static_dir or Path(__file__).parent / "templates"
        self._app: web.Application | None = None
        self._runner: web.AppRunner | None = None
        self._site: web.TCPSite | None = None
        self._ws_clients: set[web.WebSocketResponse] = set()
        self._browser_sessions: dict[str, BrowserSession] = {}
        self._flush_callback: FlushCallback | None = None
        self._config_callback: ConfigCallback | None = None
        self._scene_config_callback: SceneConfigCallback | None = None
        self._scene_list_callback: SceneListCallback | None = None
        self._control_callback: ControlCallback | None = None
        self._on_connect: Callable[[str], Awaitable[None]] | None = None
        self._on_disconnect: Callable[[str], Awaitable[None]] | None = None
        self._pending_screenshots: dict[str, asyncio.Future[Any]] = {}
        self._pending_page_tokens: dict[str, dict[str, Any]] = {}

    # ── Lifecycle ───────────────────────────────────────────

    async def start(
        self,
        flush_callback: FlushCallback,
        config_callback: ConfigCallback,
        *,
        control_callback: ControlCallback | None = None,
        on_connect: Callable[[str], Awaitable[None]] | None = None,
        on_disconnect: Callable[[str], Awaitable[None]] | None = None,
        push_controls: PushControlsCallback | None = None,
        scene_config_callback: SceneConfigCallback | None = None,
        scene_list_callback: SceneListCallback | None = None,
        on_ready: Callable[[], None] | None = None,
    ) -> None:
        """Build and start the aiohttp application (non-blocking setup)."""
        self._flush_callback = flush_callback
        self._config_callback = config_callback
        self._scene_config_callback = scene_config_callback
        self._scene_list_callback = scene_list_callback
        self._control_callback = control_callback
        self._on_connect = on_connect
        self._on_disconnect = on_disconnect
        self._push_controls_cb = push_controls
        self._on_ready = on_ready
        self._app = self._build_app()

        self._runner = web.AppRunner(self._app)
        await self._runner.setup()
        try:
            self._site = web.TCPSite(
                self._runner, self._host, self._port, reuse_address=True
            )
            await self._site.start()
        except OSError as e:
            if (
                getattr(e, "errno", 0) == 98
                or "address already in use" in str(e).lower()
            ):
                raise RuntimeError(
                    f"Port {self._port} is already in use. "
                    f"Close the other process or use Visualizer(port=...) "
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

        if self._site is not None:
            await self._site.stop()
        if self._runner is not None:
            await self._runner.cleanup()

    # ── Push ──────────────────────────────────────────────

    async def push(
        self, entities: list[dict[str, Any]], removed: list[str], *, scene: str = ""
    ) -> None:
        """Serialize and broadcast a scene update to all WebSocket clients."""
        from .serializer import serialize_scene_update

        if not self._ws_clients:
            return

        message = serialize_scene_update(entities, removed)
        message["scene"] = scene
        data = json.dumps(message)

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
        dead: list[web.WebSocketResponse] = []
        for ws in self._ws_clients:
            try:
                await ws.send_str(data)
            except (ConnectionError, Exception):
                dead.append(ws)
        for ws in dead:
            self._ws_clients.discard(ws)

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
        self, ws: web.WebSocketResponse, *, scene_name: str = ""
    ) -> None:
        """Send scene config + full entity state to a single client."""
        from .serializer import serialize_scene_update

        # 0. Clear the browser scene first (handles reconnect with new server)
        await ws.send_str(json.dumps({"type": "clear_all"}))

        # 1. Scene configuration (scoped to the specific scene if available)
        if self._scene_config_callback is not None:
            cfg = self._scene_config_callback(scene_name)
        elif self._config_callback is not None:
            cfg = self._config_callback()
        else:
            cfg = None

        if cfg is not None:
            cfg.setdefault("name", scene_name)
            await ws.send_str(json.dumps(cfg))

        # 2. Full state (entities + labels merged)
        if self._flush_callback is not None:
            entities, _ = self._flush_callback(scene_name)
            if entities:
                msg = serialize_scene_update(entities, [])
                msg["scene"] = scene_name
                await ws.send_str(json.dumps(msg))

        # 3. Scene list (so the frontend knows available scenes)
        if self._scene_list_callback is not None:
            scene_names = self._scene_list_callback()
            await ws.send_str(
                json.dumps({"type": "scene_list", "scenes": scene_names, "default": ""})
            )

    # ── Browser sessions (read-only access for Visualizer) ─

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
        if rel_path:
            file_path = self._static_dir / rel_path
            if file_path.is_file():
                return web.FileResponse(file_path)

        # Inject a page token for WS connectivity correlation
        viewer_path = self._static_dir / "viewer.html"
        page_token = uuid4().hex[:8]
        remote_addr = request.remote or "unknown"
        self._pending_page_tokens[page_token] = {
            "remote_addr": remote_addr,
            "timestamp": asyncio.get_running_loop().time(),
        }

        # Print initial page-load note
        self._print_page_load(remote_addr, page_token)

        html = viewer_path.read_text(encoding="utf-8")
        token_script = f'<script>window.__tanga_page_token = "{page_token}";</script>'
        # Inject after <head> or at start of file
        if "</head>" in html:
            html = html.replace("</head>", f"{token_script}\n</head>")
        else:
            html = token_script + "\n" + html

        resp = web.StreamResponse(
            status=200,
            reason="OK",
            headers={"Content-Type": "text/html; charset=utf-8"},
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

        # Assign a unique browser ID and send it immediately
        browser_id = uuid4().hex[:8]
        session = BrowserSession(
            id=browser_id, scene="", remote_addr=remote_addr, ws=ws
        )
        self._browser_sessions[browser_id] = session

        await ws.send_str(json.dumps({"type": "browser_id", "browser_id": browser_id}))

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

                        if msg_type == "ready":
                            scene_name = data.get("scene", "")
                            # Correlate page token if present (HTTP→WS round-trip diagnostic)
                            page_token = data.get("page_token")
                            if page_token:
                                self._pending_page_tokens.pop(page_token, None)
                            # Print comprehensive connection summary
                            self._print_ws_connected(
                                remote_addr,
                                page_token,
                                msg_browser_id,
                                data.get("viewer_name"),
                            )
                            # Validate scene exists
                            if self._scene_list_callback is not None:
                                available = self._scene_list_callback()
                                if scene_name and scene_name not in available:
                                    # Scene doesn't exist — navigate to main
                                    await ws.send_str(
                                        json.dumps({"type": "navigate", "scene": ""})
                                    )
                                    scene_name = ""

                            current_session.scene = scene_name
                            # Store viewer_name from the ready message
                            viewer_name = data.get("viewer_name")
                            if viewer_name:
                                current_session.viewer_name = viewer_name
                            await self._push_full_state(ws, scene_name=scene_name)
                            if self._push_controls_cb is not None:
                                await self._push_controls_cb(scene_name)
                            if self._on_ready is not None:
                                self._on_ready()

                        elif msg_type == "screenshot:data":
                            rid = data.get("request_id")
                            if rid and rid in self._pending_screenshots:
                                if not self._pending_screenshots[rid].done():
                                    self._pending_screenshots[rid].set_result(
                                        data["data"]
                                    )
                        elif msg_type in (
                            "control:change",
                            "control:click",
                            "control:group_toggle",
                        ):
                            # Inject browser_id into the payload for the callback
                            if msg_browser_id:
                                data["browser_id"] = msg_browser_id
                            if self._control_callback is not None:
                                asyncio.create_task(
                                    self._control_callback(msg_type, data)
                                )
                    except json.JSONDecodeError:
                        pass
                elif msg.type == web.WSMsgType.ERROR:
                    break
        finally:
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
        except ImportError:
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
        except ImportError:
            print(f"✓ Browser connected  ({detail})")

    def _print_ws_reachability_note(self) -> None:
        """Print a note about WebSocket reachability for port forwarding setups."""
        ws_url = f"ws://{self._host}:{self._port}/ws"
        note = (
            "Note: the WebSocket connection ("
            + ws_url
            + ") must also be reachable from the\n"
            "browser. If using port forwarding or a reverse proxy, ensure WebSocket\n"
            "upgrade requests are forwarded — otherwise the viewer will render an\n"
            "empty 3D scene.\n"
        )
        try:
            from rich.console import Console
            from rich.text import Text

            Console().print(Text(note, style="dim"))
        except ImportError:
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
        try:
            from rich.console import Console
            from rich.panel import Panel
            from rich.text import Text

            console = Console()
            for info in stale:
                panel = Panel(
                    Text.assemble(
                        "[bold red]WebSocket connection failed[/bold red]\n",
                        f"Browser at [cyan]{info['remote_addr']}[/cyan] loaded the "
                        "page via HTTP but the WebSocket never connected.\n"
                        "Check that the following URL is reachable:\n",
                        Text(ws_url, style="bold cyan underline"),
                    ),
                    border_style="red",
                    padding=(1, 2),
                )
                console.print(panel)
        except ImportError:
            for info in stale:
                print(
                    f"WARNING: Browser at {info['remote_addr']} loaded the page "
                    f"but WebSocket never connected. "
                    f"Check that {ws_url} is reachable "
                    f"(port forwarding/proxy must support WebSocket upgrades)."
                )

    def open_browser(self) -> None:
        """Open the viewer URL in the default browser with graceful fallback."""
        try:
            ok = webbrowser.open(self.url)
            if ok:
                return
        except Exception:
            pass

        try:
            from rich.console import Console
            from rich.panel import Panel
            from rich.text import Text

            console = Console()
            url_text = Text(self.url, style="bold cyan underline")
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
            self._print_ws_reachability_note()
        except ImportError:
            print("Could not open browser automatically.")
            print(f"Open {self.url} manually to view the scene.")
            self._print_ws_reachability_note()

    async def wait_for_client(self, timeout: float = 30.0) -> bool:
        """Wait until at least one WebSocket client connects.

        Returns ``True`` if a client connected, ``False`` on timeout.
        """
        import time as _time

        deadline = _time.monotonic() + timeout
        while _time.monotonic() < deadline:
            if self._ws_clients:
                return True
            await asyncio.sleep(0.5)
        return False
