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

from .distance import DistanceFunction
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
        title: str = "Tanga SDF Viewer",
        background_color: str = "#1a1a2e",
        camera: Any | None = None,  # CameraConfig | View3dConfig | None
    ) -> None:
        from pytanga.viz.camera import _normalize_camera_config

        self._host = host or "localhost"
        self._port = port if port is not None else DEFAULT_PORT
        self._open_browser = open_browser
        self._title = title
        self._background_color = background_color
        self._camera = _normalize_camera_config(camera)

        from pytanga.viz._viz_styles import make_styles

        self._styles = make_styles()

        # Ordered for stable serialization (equals material-id order).
        self._objects: dict[str, GeoEntity] = {}
        self._props: dict[str, dict[str, Any]] = {}

        # Viewer-level distance / opacity transfer setting (stub hooks; wired
        # into the shader at Phase 8 / populated at Phase 12).
        self._distance = DistanceFunction.default()
        self._opacity = "step"

        self._server = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._shutdown_requested = threading.Event()
        self._atexit_registered = False

    # ── Entity management ───────────────────────────────────

    def add(
        self,
        obj: GeoEntity | Any,
        *,
        entity_id: str | None = None,
        color: str | None = None,
        opacity: float | None = None,
        size: float | None = None,
        thickness: float | None = None,
        combine: str | None = None,
        polarity: str | None = None,
    ) -> str:
        """Add a geometry entity to the SDF scene and return its ID."""
        from uuid import uuid4

        entity = self._resolve(obj)

        props: dict[str, Any] = {}
        if color is not None:
            props["color"] = color
        if opacity is not None:
            props["opacity"] = opacity
        if size is not None:
            props["size"] = size
        if thickness is not None:
            props["thickness"] = thickness
        if combine is not None:
            props["combine"] = combine
        if polarity is not None:
            props["polarity"] = polarity

        oid = entity_id or uuid4().hex[:8]
        self._objects[oid] = entity
        self._props[oid] = props
        self._flush()
        return oid

    def remove(self, entity_id: str) -> None:
        """Remove an entity from the SDF scene."""
        self._objects.pop(entity_id, None)
        self._props.pop(entity_id, None)
        self._push_removed([entity_id])

    def clear(self) -> None:
        """Remove all entities."""
        removed = list(self._objects)
        self._objects.clear()
        self._props.clear()
        self._push_removed(removed)

    def _resolve(self, obj: Any) -> GeoEntity:
        from pytanga.geometry.operators import Operator as GeoOperator

        if isinstance(obj, (GeoEntity, GeoOperator)):
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
        )
        return cfg.to_dict()

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

    def open_browser(self) -> bool:
        """Open the SDF viewer in a browser."""
        if self._server is None:
            raise RuntimeError("Server not started. Call start_server() first.")
        self._server.open_browser("/")
        return True

    def show(
        self,
        *,
        host: str | None = None,
        port: int | None = None,
    ) -> bool:
        """Serve the SDF viewer and open a browser tab (non-blocking)."""
        self.start_server(host=host, port=port)
        if self._open_browser is not False:
            return self.open_browser()
        return True

    def wait(self) -> None:
        """Block until Ctrl+C, then stop the server."""
        while not self._shutdown_requested.is_set():
            time.sleep(0.25)
        self.stop_server()

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