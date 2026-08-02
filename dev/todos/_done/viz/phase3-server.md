# Phase 3: WebSocket Server

**File:** `py/pytanga/viz/server.py`

**Goal:** Implement an `aiohttp`-based server that serves the static HTML/JS frontend
and provides a WebSocket endpoint for real-time scene updates. On new client
connections, the server sends a `scene_config` message before any entity data,
carrying camera settings, space extent, grid/axes preferences, and background color.

**Prerequisites:** Phase 1 (`Scene`, `SceneConfig`, `CameraConfig`, `Visualizer` stubs), Phase 2 (`serializer`)

---

## 1. Design

### 1.1 Server Architecture

The server combines two responsibilities on a single port:
- **HTTP:** Serves the static `templates/` directory (viewer.html, viewer.js, renderers, controls.js, animator.js)
- **WebSocket:** Accepts client connections at `/ws` and pushes:
  1. `scene_config` message (once, on connect)
  2. `scene_update` messages (entity state, on connect and on `flush()`)

```python
# py/pytanga/viz/server.py

from __future__ import annotations
import json
import webbrowser
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

import aiohttp
from aiohttp import web

# Type for the flush callback: returns (entities_list, removed_list)
FlushCallback = Callable[[], tuple[List[Dict[str, Any]], List[str]]]


class VizServer:
    """Lightweight HTTP + WebSocket server for the Tanga 3D viewer."""

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
        self._ws_clients: Set[web.WebSocketResponse] = set()
        self._flush_callback: FlushCallback | None = None

    # --- Lifecycle ---

    async def start(self, flush_callback: FlushCallback) -> None:
        """Build and start the aiohttp application (non-blocking setup).

        Call this once before any connections.
        """
        self._flush_callback = flush_callback
        self._app = self._build_app()

        self._runner = web.AppRunner(self._app)
        await self._runner.setup()
        self._site = web.TCPSite(self._runner, self._host, self._port)
        await self._site.start()

    async def stop(self) -> None:
        """Gracefully shut down all connections and the server."""
        # Close all WebSocket connections
        for ws in list(self._ws_clients):
            await ws.close(code=aiohttp.WSCloseCode.GOING_AWAY)
        self._ws_clients.clear()

        if self._site is not None:
            await self._site.stop()
        if self._runner is not None:
            await self._runner.cleanup()

    async def push(self, entities: List[Dict[str, Any]], removed: List[str]) -> None:
        """Serialize and broadcast a scene update to all connected WebSocket clients."""
        from .serializer import serialize_scene_update

        if not self._ws_clients:
            return

        message = serialize_scene_update(entities, removed)
        data = json.dumps(message)

        dead: list[web.WebSocketResponse] = []
        for ws in self._ws_clients:
            try:
                await ws.send_str(data)
            except (ConnectionError, aiohttp.ClientError):
                dead.append(ws)

        for ws in dead:
            self._ws_clients.discard(ws)

    async def push_full_state(self, ws: web.WebSocketResponse, scene_config: dict | None = None) -> None:
        """Send scene config + complete scene state to a single client (on connect).

        Args:
            ws: The WebSocket connection.
            scene_config: The serialized SceneConfig dict. Sent first if provided.
        """
        # 1. Send scene configuration first
        if scene_config is not None:
            await ws.send_str(json.dumps(scene_config))

        # 2. Send full entity state
        if self._flush_callback is None:
            return

        entities, _ = self._flush_callback()
        if entities:
            from .serializer import serialize_scene_update
            message = serialize_scene_update(entities, [])
            await ws.send_str(json.dumps(message))

    # --- Internals ---

    def _build_app(self) -> web.Application:
        app = web.Application()
        app.router.add_get("/ws", self._ws_handler)
        # Serve static files with a fallback to viewer.html at "/"
        app.router.add_get("/", self._index_handler)
        app.router.add_static("/", self._static_dir, show_index=False)
        return app

    async def _index_handler(self, request: web.Request) -> web.FileResponse:
        """Serve viewer.html at the root."""
        return web.FileResponse(self._static_dir / "viewer.html")

    async def _ws_handler(self, request: web.Request) -> web.WebSocketResponse:
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self._ws_clients.add(ws)

        # Send scene config + current state to the new client
        scene_config = self._flush_callback_config() if self._flush_callback_config else None
        await self.push_full_state(ws, scene_config)

        try:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    # Handle incoming messages (click events, ready signal)
                    try:
                        data = json.loads(msg.data)
                        if data.get("type") == "ready":
                            await self.push_full_state(ws, scene_config)
                    except json.JSONDecodeError:
                        pass
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    break
        finally:
            self._ws_clients.discard(ws)

        return ws

    # --- Convenience ---

    @property
    def url(self) -> str:
        return f"http://{self._host}:{self._port}"

    def open_browser(self) -> None:
        """Open the viewer URL in the default browser."""
        webbrowser.open(self.url)
```

### 1.2 Flush Callbacks

The server uses two callbacks from the `Scene`:
- `flush_callback()` → `(entities_list, removed_list)` — for entity state
- `flush_callback_config()` → `dict` — for `SceneConfig.to_dict()`

```python
# Type for entity flush: returns (entities_list, removed_list)
FlushCallback = Callable[[], tuple[List[Dict[str, Any]], List[str]]]
# Type for config fetch: returns the scene_config dict
ConfigCallback = Callable[[], Dict[str, Any]]
```

The `VizServer.__init__` accepts both:

```python
class VizServer:
    def __init__(self, *, host, port, static_dir=None):
        ...
        self._flush_callback: FlushCallback | None = None
        self._flush_callback_config: ConfigCallback | None = None
```

And `start()` stores them:

```python
async def start(self, flush_callback: FlushCallback, config_callback: ConfigCallback) -> None:
    self._flush_callback = flush_callback
    self._flush_callback_config = config_callback
    ...
```

### 1.3 Integration with Visualizer

```python
# In visualizer.py — the run/start/stop/flush methods:

class Visualizer:
    # ... (existing code from Phase 1) ...

    def start(self) -> None:
        """Start the server in the current event loop (async, non-blocking)."""
        import asyncio
        from .server import VizServer

        self._server = VizServer(
            host=self._host,
            port=self._port,
        )

        # Schedule server start and flush initial scene
        async def _start():
            await self._server.start(
                self._scene.full_state,
                self._config.to_dict,  # SceneConfig → dict callback
            )
            if self._open_browser:
                self._server.open_browser()

        # Run in a new event loop on a daemon thread
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._loop.run_until_complete,
            args=(_start(),),
            daemon=True,
        )
        self._thread.start()

    async def _flush_async(self) -> None:
        """Push dirty state to clients (must be called from the server's event loop)."""
        if self._server is None:
            return
        entities, removed = self._scene.flush()
        if entities or removed:
            await self._server.push(entities, removed)

    def flush(self) -> None:
        """Schedule a scene update on the server's event loop (thread-safe)."""
        if self._loop is not None and self._server is not None:
            asyncio.run_coroutine_threadsafe(self._flush_async(), self._loop)

    def run(self) -> None:
        """Start the server and block until interrupted.

        This is the main entry point for simple scripts.
        """
        import asyncio

        self._server = VizServer(host=self._host, port=self._port)

        async def _run():
            await self._server.start(
                lambda: self._scene.full_state(),
                self._config.to_dict,
            )
            if self._open_browser:
                self._server.open_browser()
            # Push initial scene state
            await self._flush_async()
            # Keep running until cancelled
            try:
                while True:
                    await asyncio.sleep(3600)
            except asyncio.CancelledError:
                pass

        try:
            asyncio.run(_run())
        except KeyboardInterrupt:
            pass
        finally:
            if self._server is not None:
                asyncio.run(self._server.stop())

    def stop(self) -> None:
        """Stop the server. For non-blocking mode."""
        if self._loop is not None:
            async def _stop():
                if self._server is not None:
                    await self._server.stop()
            asyncio.run_coroutine_threadsafe(_stop(), self._loop)
            self._loop.call_soon_threadsafe(self._loop.stop)
            if self._thread is not None:
                self._thread.join(timeout=2.0)
```

---

## 2. Design Decisions

1. **Single port for HTTP + WS:** aiohttp handles both on the same port. The HTTP
   routes serve static files; the `/ws` route handles WebSocket upgrades. This
   simplifies the URL — users just open `http://localhost:8765`.

2. **Event loop threading:** The server runs on its own asyncio event loop in a
   daemon thread. The `Visualizer.flush()` method is thread-safe — it schedules
   the push on the server's loop via `asyncio.run_coroutine_threadsafe()`.

3. **`run()` blocks, `start()` doesn't:** Two modes:
   - `run()` — takes over the main thread, runs the event loop directly, blocks
     until Ctrl+C. Simplest for one-shot scripts.
   - `start()` / `flush()` / `stop()` — server runs in a background thread.
     Enables interactive use and animation loops.

4. **Client tracking:** The server maintains a `Set` of active WebSocket connections
   and broadcasts scene updates to all of them. On push failure (client disconnected),
   dead connections are cleaned up.

5. **Full state on connect:** When a new client connects, it receives the complete
   scene state via `push_full_state()`. Subsequent updates are deltas only.

6. **Static file serving:** `aiohttp`'s built-in `add_static()` routes serve the
   `templates/` directory. The JS files are served as ES modules (`type="module"`),
   which aiohttp handles with the correct MIME type for `.js` files.

---

## 3. Dependencies

Add to `pyproject.toml`:
```toml
[project]
dependencies = [
    # ... existing deps ...
    "aiohttp>=3.9",
]
```

---

## 4. Implementation Steps

1. Add `aiohttp` to `pyproject.toml` dependencies.
2. Create `py/pytanga/viz/server.py` with `VizServer` class.
3. Update `py/pytanga/viz/visualizer.py` with `start()`, `stop()`, `run()`, `flush()` implementations.
4. Add `threading` import to `visualizer.py`.
5. Create placeholder `py/pytanga/viz/templates/viewer.html` with a minimal page (just
   a "connecting..." message — the actual Three.js content comes in Phase 4).
6. Manual test: `Visualizer().run()` starts server, serves the placeholder page,
   accepts WebSocket connections without errors.
7. Write unit test: Start server on a random port, connect a WebSocket client,
   verify it receives the initial scene state message.

## 5. Verification Checklist

### Server Lifecycle
- [x] `VizServer.start()` creates HTTP routes and WebSocket endpoint.
- [x] `VizServer.stop()` closes all connections and shuts down cleanly.

### Static Files
- [x] Static files from `templates/` are served correctly (MIME types).

### WebSocket
- [x] WebSocket clients receive initial full-state message on connect.
- [x] WebSocket clients receive scene updates when `push()` is called.
- [x] Dead WebSocket clients are cleaned up on send failure.
- [x] Scene config (`scene_config` message) is sent before entity data on connect.

### Visualizer Integration
- [x] `Visualizer.run()` starts server, opens browser, blocks until Ctrl+C.
- [x] `Visualizer.start()` / `flush()` / `stop()` work in non-blocking mode.

### Dependencies
- [x] `aiohttp` is listed in `pyproject.toml`.
