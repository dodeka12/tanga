# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""SDF viewer facade.

Mirrors the standard :class:`pytanga.viz.Visualizer` API for the
signed-distance-function viewer: it serializes the six supported geometry
entities via :mod:`pytanga.viz.sdf.serializer` and serves the SDF frontend
(``sdf_viewer.html`` + the ``sdf/`` JS library) through the shared
:class:`~pytanga.viz.server.VizServer`, reusing its WebSocket protocol and
lifecycle unchanged.

The camera travels through the same ``scene_config.camera`` field as the
standard viewer, so default and custom views match 1:1 (camera parity).
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
import time
from typing import Any

from pytanga.geometry.entities import Entity as GeoEntity
from pytanga.algebra import MV

from .composed import Composed
from .distance import DistanceFunction
from .lights import DirectionalLight, Light, serialize_light
from .overlay import Axes, Grid, SdfOverlay, serialize_overlay
from .primitives import SdfNode
from .serializer import serialize_entity

logger = logging.getLogger("tanga.viz.sdf")

DEFAULT_PORT = 8765


class SdfVisualizer:
    """Ray-marched SDF viewer (signed-distance-function), 3D only.

    Usage::

        from pytanga.viz.sdf import SdfVisualizer
        from pytanga.geometry import Line, Point, Sphere

        viz = SdfVisualizer()
        viz.add(Sphere(Point(0, 0, 0), 1.0), color="#ffaa00")
        viz.show()      # opens the SDF viewer in a browser
        viz.wait()      # blocks until Ctrl+C
    """

    def __init__(
        self,
        *,
        port: int | None = None,
        host: str | None = None,
        open_browser: bool | None = None,
        reuse_existing: bool = True,
        title: str = "Tanga SDF Viewer",
        background_color: str = "#1a1a2e",
        camera: Any | None = None,  # CameraConfig | View3dConfig | None
        add_default_light: bool = True,
        add_default_grid: bool = True,
        add_default_axes: bool = True,
    ) -> None:
        from pytanga.viz.camera import _normalize_camera_config

        from pytanga.viz._utils import _is_jupyter

        self._host = host or "localhost"
        self._port = port if port is not None else DEFAULT_PORT
        self._jupyter = _is_jupyter()
        if open_browser is None:
            open_browser = not self._jupyter
        self._open_browser = open_browser
        self._reuse_existing = reuse_existing
        self._title = title
        self._background_color = background_color
        self._camera = _normalize_camera_config(camera)

        from pytanga.viz._viz_styles import make_styles

        self._styles = make_styles()

        # Ordered for stable serialization (equals material-id order).
        self._objects: dict[str, Any] = {}
        self._props: dict[str, dict[str, Any]] = {}

        # Viewer-level distance / opacity transfer setting (stub hooks; wired
        # into the shader at Phase 8 / populated at Phase 12).
        self._distance = DistanceFunction.default()
        self._opacity = "step"

        # Lighting: one default directional light + ambient term, unless the
        # caller disabled the default light (mirrors add_default_axes/grid).
        self._lights: dict[str, Light] = {}
        self._ambient_color = "#ffffff"
        self._ambient_intensity = 0.45
        if add_default_light:
            self._add_default_light_source()

        # Overlays: one default ground grid + default coordinate axes, unless
        # disabled (mirrors add_default_grid / add_default_axes).
        self._overlays: dict[str, SdfOverlay] = {}
        if add_default_grid:
            self._overlays["__default_grid__"] = Grid()
        if add_default_axes:
            self._overlays["__default_axes__"] = Axes()

        self._server = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._shutdown_requested = threading.Event()
        self._atexit_registered = False

    # ── Entity management ───────────────────────────────────

    def add(
        self,
        obj: Any,
        *,
        entity_id: str | None = None,
        color: str | None = None,
        opacity: float | None = None,
        size: float | None = None,
        thickness: float | None = None,
        style: Any | None = None,
        combine: str | None = None,
        polarity: str | None = None,
        bound: Any | None = None,
        normalize: bool | None = None,
        calibrate: bool | None = None,
    ) -> str:
        """Add an object to the SDF scene and return its ID.

        Accepts a geometry entity, an operator, a bare :class:`SdfNode`
        primitive/combinator tree, a :class:`Composed` object, a raw
        :class:`~pytanga.algebra.MV` (the algebra path), or a
        :class:`~pytanga.viz.sdf.lights.Light` (a ``DirectionalLight``).
        ``style`` selects an alternative draw style (e.g.
        ``CrossHairPointStyle``). For a raw MV, ``bound`` (half-extents or a
        ``{"halfExtents": [..]}`` dict) clips infinite entities, ``normalize``
        (default ``True``) normalizes the MV before embedding, and ``calibrate``
        (default ``False``) computes the per-object gradient scale (Phase 9).
        """
        from uuid import uuid4

        if isinstance(obj, Light):
            return self._add_light(obj)
        if isinstance(obj, SdfOverlay):
            return self._add_overlay(obj)

        entity = self._resolve(obj)
        props = self._build_props(
            color=color,
            opacity=opacity,
            size=size,
            thickness=thickness,
            style=style,
            combine=combine,
            polarity=polarity,
            bound=bound,
            normalize=normalize,
            calibrate=calibrate,
        )

        oid = entity_id or uuid4().hex[:8]
        self._objects[oid] = entity
        self._props[oid] = props
        self._flush()
        return oid

    def update_entity(
        self,
        entity_id: str,
        obj: Any,
        *,
        color: str | None = None,
        opacity: float | None = None,
        size: float | None = None,
        thickness: float | None = None,
        style: Any | None = None,
        combine: str | None = None,
        polarity: str | None = None,
        bound: Any | None = None,
        normalize: bool | None = None,
        calibrate: bool | None = None,
    ) -> None:
        """Replace the object at ``entity_id`` and re-push it.

        ``obj`` may be a geometry entity, an operator, a bare :class:`SdfNode`,
        a :class:`Composed`, or a raw :class:`~pytanga.algebra.MV`; a
        :class:`~pytanga.viz.sdf.lights.Light` is routed to :meth:`update_light`.
        """
        if isinstance(obj, Light):
            self.update_light(entity_id, obj)
            return
        self._objects[entity_id] = self._resolve(obj)
        self._props[entity_id] = self._build_props(
            color=color,
            opacity=opacity,
            size=size,
            thickness=thickness,
            style=style,
            combine=combine,
            polarity=polarity,
            bound=bound,
            normalize=normalize,
            calibrate=calibrate,
        )
        self._push_update([entity_id])

    def _build_props(
        self,
        *,
        color: str | None = None,
        opacity: float | None = None,
        size: float | None = None,
        thickness: float | None = None,
        style: Any | None = None,
        combine: str | None = None,
        polarity: str | None = None,
        bound: Any | None = None,
        normalize: bool | None = None,
        calibrate: bool | None = None,
    ) -> dict[str, Any]:
        """Assemble the per-object property dict (``None`` = inherit default)."""
        props: dict[str, Any] = {}
        if color is not None:
            props["color"] = color
        if opacity is not None:
            props["opacity"] = opacity
        if size is not None:
            props["size"] = size
        if thickness is not None:
            props["thickness"] = thickness
        if style is not None:
            props["style"] = style
        if combine is not None:
            props["combine"] = combine
        if polarity is not None:
            props["polarity"] = polarity
        if bound is not None:
            props["bound"] = bound
        if normalize is not None:
            props["normalize"] = normalize
        if calibrate is not None:
            props["calibrate"] = calibrate
        return props

    def remove(self, entity_id: str) -> None:
        """Remove an entity, light, or overlay from the SDF scene."""
        if entity_id in self._lights:
            del self._lights[entity_id]
            self._push_config()
            return
        if entity_id in self._overlays:
            del self._overlays[entity_id]
            self._push_config()
            return
        self._objects.pop(entity_id, None)
        self._props.pop(entity_id, None)
        self._push_removed([entity_id])

    def clear(self) -> None:
        """Remove all entities, lights, and overlays."""
        removed = list(self._objects)
        self._objects.clear()
        self._props.clear()
        self._push_removed(removed)
        self._lights.clear()
        self._overlays.clear()
        self._push_config()

    def _resolve(self, obj: Any) -> Any:
        from pytanga.geometry.operators import Operator as GeoOperator

        if isinstance(obj, (SdfNode, Composed, GeoEntity, GeoOperator, MV)):
            return obj
        try:
            from pytanga.geometry import analyze

            result = analyze(obj)
            if result is None:
                raise ValueError(f"Could not analyze object: {obj!r}")
            return result
        except ImportError:
            raise TypeError(
                f"Object of type {type(obj).__name__} is not a recognized "
                f"geometry entity."
            ) from None

    # ── Lighting ────────────────────────────────────────────

    def _add_light(self, light: Light) -> str:
        """Add a light and return its ID."""
        from uuid import uuid4

        lid = "light-" + uuid4().hex[:8]
        self._lights[lid] = light
        self._push_config()
        return lid

    def update_light(self, light_id: str, light: Light) -> None:
        """Replace the light at ``light_id`` and push the light config."""
        self._lights[light_id] = light
        self._push_config()

    def _add_default_light_source(self) -> None:
        """Add the built-in default directional light (stable ID)."""
        self._lights["__default_light__"] = DirectionalLight()

    def _lighting_dict(self) -> dict[str, Any]:
        """Wire form of the ambient term plus the current light set."""
        return {
            "ambient": {
                "color": self._ambient_color,
                "intensity": self._ambient_intensity,
            },
            "lights": [serialize_light(light) for light in self._lights.values()],
        }

    @property
    def ambient(self) -> dict[str, Any]:
        """The current ambient light as ``{"color", "intensity"}``."""
        return {"color": self._ambient_color, "intensity": self._ambient_intensity}

    def set_ambient_light(
        self, *, color: str = "#ffffff", intensity: float = 0.45
    ) -> None:
        """Set the ambient light color and intensity (pushed to the viewer)."""
        self._ambient_color = color
        self._ambient_intensity = float(intensity)
        self._push_config()

    # ── Overlays ────────────────────────────────────────────

    def _add_overlay(self, overlay: SdfOverlay) -> str:
        """Add a shader-drawn overlay and return its ID."""
        from uuid import uuid4

        oid = "overlay-" + uuid4().hex[:8]
        self._overlays[oid] = overlay
        self._push_config()
        return oid

    def _overlay_dict(self) -> list[dict[str, Any]]:
        """Wire form of the current overlay list."""
        return [serialize_overlay(overlay) for overlay in self._overlays.values()]

    # ── Viewer-level settings (stubs until later phases) ────

    @property
    def distance(self) -> str:
        """The active distance function key (default ``"scalar_pseudo"``)."""
        return self._distance.value

    @distance.setter
    def distance(self, value: str | DistanceFunction) -> None:
        if isinstance(value, DistanceFunction):
            self._distance = value
        else:
            self._distance = DistanceFunction(value)
        self._push_config()

    @property
    def opacity(self) -> str:
        """The active opacity transfer key (default ``"step"``)."""
        return self._opacity

    @opacity.setter
    def opacity(self, value: str) -> None:
        self._opacity = value
        self._push_config()

    def _push_config(self) -> None:
        if self._loop is None or self._server is None:
            return
        message = json.dumps(
            {
                "type": "sdf_viewer_config",
                "distance": self.distance,
                "opacity": self.opacity,
                **self._lighting_dict(),
                "overlays": self._overlay_dict(),
            }
        )
        asyncio.run_coroutine_threadsafe(self._server.push_raw(message), self._loop)

    # ── Server callbacks ────────────────────────────────────

    def _full_state_for(self, scene_name: str) -> tuple[list[dict[str, Any]], list[str]]:
        out: list[dict[str, Any]] = []
        for oid, entity in self._objects.items():
            try:
                out.append(
                    serialize_entity(
                        entity,
                        oid,
                        self._props.get(oid, {}),
                        styles_map=self._styles.kind,
                    )
                )
            except TypeError as e:
                logger.warning("SDF serializer skipped %s: %s", oid, e)
        return out, []

    def _scene_config_for(self, scene_name: str) -> dict[str, Any]:
        from pytanga.viz.scene import SceneConfig

        cfg = SceneConfig(
            background_color=self._background_color,
            camera=self._camera,
            title=self._title,
            name=scene_name,
            space_dim=3,
        ).to_dict()
        # Lighting and overlays ride along with the scene config so they reach
        # the frontend on the initial connect; runtime changes go via
        # `sdf_viewer_config`.
        cfg["sdf_lighting"] = self._lighting_dict()
        cfg["sdf_overlays"] = self._overlay_dict()
        return cfg

    def _scene_list(self) -> list[str]:
        return [""]

    # ── Server lifecycle ────────────────────────────────────

    def start_server(self, host: str | None = None, port: int | None = None) -> None:
        """Start serving the SDF viewer without opening a browser."""
        from pytanga.viz.server import VizServer

        if host is not None:
            self._host = host
        if port is not None:
            self._port = port

        if self._server is not None:
            return

        logger.info("Starting SDF VizServer on %s:%d", self._host, self._port)
        self._server = VizServer(
            host=self._host, port=self._port, entry_page="sdf_viewer.html"
        )

        _boot_done = threading.Event()

        async def _boot() -> None:
            await self._server.start(
                self._full_state_for,
                lambda: self._scene_config_for(""),
                scene_config_callback=self._scene_config_for,
                scene_list_callback=self._scene_list,
            )
            _boot_done.set()

        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.create_task(_boot())
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()

        if not _boot_done.wait(timeout=5.0):
            raise RuntimeError("SDF server failed to start within 5s")

        if not self._atexit_registered:
            import atexit

            def _atexit_stop() -> None:
                try:
                    self.stop_server(timeout=2.0)
                except Exception:
                    pass

            atexit.register(_atexit_stop)
            self._atexit_registered = True

        import signal

        signal.signal(signal.SIGINT, lambda *_: self._shutdown_requested.set())
        signal.signal(signal.SIGTERM, lambda *_: self._shutdown_requested.set())

    def open_browser(self, *, wait_for_browser: bool | None = None) -> bool:
        """Open or reconnect a browser tab for the SDF scene (single scene ``""``).

        Mirrors the standard viewer: with ``reuse_existing`` (the default) this
        either waits interactively for an existing tab to reconnect (or the user
        to press Enter), or — when ``wait_for_browser`` is ``False`` (e.g.
        Jupyter) — does a short non-interactive reconnect check. With
        ``reuse_existing=False`` a new tab is always opened.
        """
        import concurrent.futures
        import secrets

        if self._server is None:
            raise RuntimeError("Server not started. Call start_server() first.")

        if wait_for_browser is None:
            wait_for_browser = not self._jupyter

        page_token = secrets.token_hex(4)  # 8 hex chars
        token_url = f"/?token={page_token}"

        if self._reuse_existing:
            # Interactive wait: user either clicks Reconnect or presses Enter.
            if wait_for_browser:
                connected = self.wait_for_browser(timeout=120.0)
                if not connected:
                    return False
            else:
                # wait_for_browser is False (e.g. Jupyter): just check if one is
                # already there, otherwise open a tab and don't wait.
                fut = asyncio.run_coroutine_threadsafe(
                    self._server.wait_for_ws_ready(timeout=3.0), self._loop
                )
                try:
                    reconnected = fut.result(timeout=3.5)
                except (concurrent.futures.TimeoutError, asyncio.TimeoutError):
                    reconnected = False
                if not reconnected:
                    if self._loop is not None:
                        self._loop.call_soon_threadsafe(
                            self._server._clear_ws_ready_events
                        )
                    self._server.open_browser(token_url)
        else:
            # reuse_existing disabled — always open a new tab.
            if self._loop is not None:
                self._loop.call_soon_threadsafe(self._server._clear_ws_ready_events)
            self._server.open_browser(token_url)
            if wait_for_browser:
                return self.wait_for_browser(timeout=30.0)
        return True

    def wait_for_browser(self, timeout: float = 120.0) -> bool:
        """Block until a browser connects, or the user opens one interactively.

        Prints a prompt and waits for EITHER an existing browser to reconnect,
        OR the user to press Enter (opens a new tab with a fresh token).

        Returns ``True`` if a browser connected, ``False`` if cancelled by the
        user (Ctrl+C) or on timeout after opening a tab.
        """
        import secrets

        if self._server is None or self._loop is None:
            raise RuntimeError("Server not started. Call start_server() first.")

        # Already connected?
        if self._server._any_ws_ready_thread.is_set():
            logger.info("Browser already connected")
            return True

        self._print_connect_prompt()

        enter_pressed = threading.Event()
        shutdown = getattr(self, "_shutdown_requested", threading.Event())

        def _wait_for_enter() -> None:
            try:
                input()
                enter_pressed.set()
            except (EOFError, KeyboardInterrupt):
                pass

        enter_thread = threading.Thread(target=_wait_for_enter, daemon=True)
        enter_thread.start()

        start_ts = time.monotonic()
        poll_interval = 0.2

        while True:
            if self._server._any_ws_ready_thread.is_set():
                logger.info(
                    "Browser reconnected after %.1fs", time.monotonic() - start_ts
                )
                return True
            if enter_pressed.is_set():
                logger.info("User pressed Enter - opening new tab")
                break
            if shutdown.is_set():
                logger.info("Shutdown requested during wait")
                return False
            time.sleep(poll_interval)

        page_token = secrets.token_hex(4)
        logger.info("Opening new tab with token=%s", page_token)

        if self._loop is not None:
            self._loop.call_soon_threadsafe(self._server._clear_ws_ready_events)

        self._server.open_browser(f"/?token={page_token}")

        logger.info(
            "Waiting up to %.0fs for new tab to connect at %s ...", timeout, self.url
        )
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self._server._any_ws_ready_thread.is_set():
                logger.info(
                    "New tab connected after %.1fs", time.monotonic() - start_ts
                )
                return True
            if shutdown.is_set():
                logger.info("Shutdown requested during tab wait")
                return False
            time.sleep(poll_interval)

        logger.warning("No browser connected within %.0fs after opening tab", timeout)
        self._print_ws_timeout_note()
        return False

    def _print_connect_prompt(self) -> None:
        """Print the interactive connect prompt including the server URL.

        The URL is printed on its own line so terminals (e.g. VS Code) can
        detect it as a clickable link.
        """
        try:
            from rich.console import Console
            from rich.text import Text

            Console().print(
                Text.assemble(
                    "Server: ",
                    Text(self.url, style="bold cyan"),
                    "\n",
                    "Press ",
                    Text("Enter", style="bold"),
                    " to open a new browser tab, or click ",
                    Text("'Reconnect'", style="bold"),
                    " in an existing tab...",
                )
            )
        except Exception:
            print(
                f"Server: {self.url}\n"
                "Press Enter to open a new browser tab, "
                "or click 'Reconnect' in an existing tab..."
            )

    def _print_ws_timeout_note(self) -> None:
        """Print a note about WebSocket reachability when the browser didn't connect."""
        ws_url = f"ws://{self._host}:{self._port}/ws"
        try:
            from rich.console import Console
            from rich.text import Text

            Console().print(
                Text(
                    f"If the browser loaded the page but shows an empty scene, "
                    f"check that\n{ws_url} is reachable "
                    f"(port forwarding/proxy must support WebSocket upgrades).",
                    style="dim",
                )
            )
        except Exception:
            print(
                f"If the browser loaded the page but shows an empty scene, "
                f"check that {ws_url} is reachable "
                f"(port forwarding/proxy must support WebSocket upgrades)."
            )

    def show(
        self,
        *,
        host: str | None = None,
        port: int | None = None,
        wait_for_browser: bool | None = None,
    ) -> bool:
        """Serve the SDF viewer and open a browser tab (non-blocking).

        Equivalent to :meth:`start_server` followed by :meth:`open_browser`.
        ``host``/``port`` are only used when the server is not already
        running; see :meth:`start_server` for their semantics.
        """
        if self._server is None:
            self.start_server(host=host or "localhost", port=port)
        return self.open_browser(wait_for_browser=wait_for_browser)

    def wait(self) -> None:
        """Block until Ctrl+C, then stop the server."""
        while not self._shutdown_requested.is_set():
            time.sleep(0.25)
        self.stop_server()

    def sleep_ms(self, milliseconds: int) -> bool:
        """Sleep for ``milliseconds``; return ``False`` if interrupted.

        Returns ``True`` when the full interval elapsed, or ``False`` if a
        terminal interrupt (Ctrl+C / SIGTERM) arrived first — the caller should
        then stop animating. Sleeps in short windows so an interrupt is observed
        promptly without busy-spinning.
        """
        deadline = time.monotonic() + milliseconds / 1000.0
        while not self._shutdown_requested.is_set():
            remaining = deadline - time.monotonic()
            if remaining <= 0.0:
                return True
            time.sleep(min(remaining, 0.05))
        return False

    def stop_server(self, *, timeout: float = 5.0) -> None:
        """Stop the SDF server and clean up."""
        if self._server is None:
            return

        async def _stop() -> None:
            await self._server.stop()

        if self._loop is not None and self._loop.is_running():
            fut = asyncio.run_coroutine_threadsafe(_stop(), self._loop)
            try:
                fut.result(timeout=timeout)
            except Exception:
                pass
            self._loop.call_soon_threadsafe(self._loop.stop)
            if self._thread is not None:
                self._thread.join(timeout=3.0)
        self._server = None
        self._loop = None
        self._thread = None

    @property
    def url(self) -> str:
        """The HTTP URL of the SDF viewer."""
        return f"http://{self._host}:{self._port}"

    @property
    def browser_sessions(self) -> list[dict[str, str]]:
        if self._server is None:
            return []
        return self._server.get_browser_sessions()

    # ── Push helpers ────────────────────────────────────────

    def _flush(self) -> None:
        self._push_update(list(self._objects))

    def flush(self) -> None:
        """Push all objects and the lighting/config to the viewer."""
        self._flush()
        self._push_config()

    def _push_update(self, ids: list[str]) -> None:
        if self._loop is None or self._server is None or not ids:
            return
        objects = []
        for oid in ids:
            entity = self._objects.get(oid)
            if entity is None:
                continue
            try:
                objects.append(
                    serialize_entity(
                        entity, oid, self._props.get(oid, {}), styles_map=self._styles.kind
                    )
                )
            except TypeError as e:
                logger.warning("SDF serializer skipped %s: %s", oid, e)
        message = json.dumps(
            {"type": "scene_update", "scene": "", "objects": objects, "removed": []}
        )
        asyncio.run_coroutine_threadsafe(self._server.push_raw(message), self._loop)

    def _push_removed(self, removed: list[str]) -> None:
        if self._loop is None or self._server is None or not removed:
            return
        message = json.dumps(
            {"type": "scene_update", "scene": "", "objects": [], "removed": removed}
        )
        asyncio.run_coroutine_threadsafe(self._server.push_raw(message), self._loop)