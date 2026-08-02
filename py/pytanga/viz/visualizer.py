# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Top-level Visualizer class — the user-facing API for the Tanga 3D viewer.

Supports multiple named scenes, each served at a unique URL path.
"""

from __future__ import annotations

import asyncio
import json
import signal
import threading
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ._styles import AnnotationStyle, LabelStyle, ObjVizStyle

from pytanga.geometry.entities import Entity as GeoEntity

from ._jupyter import _JupyterDisplayMixin
from ._props import _normalize_color
from ._scene_handle import VizSceneHandle
from ._style_dict import (
    _kind_to_key,
    _make_default_annotation_style,
    _make_default_label_style,
    _make_default_label_styles,
    _make_default_styles,
    _resolve_annotation_style,
    _resolve_label_style,
    _StyleDict,
)
from ._timeline import Timeline
from ._types import VizInputType
from ._utils import _is_jupyter
from .scene import CameraConfig, Scene, SceneConfig, SceneObject


class Visualizer(_JupyterDisplayMixin):
    """Interactive 3D visualization of geometric entities via Three.js in a browser.

    Supports multiple named scenes, each reachable at ``/{name}`` under the
    main URL.  Entities added directly to the visualizer go to the **main
    scene** (backward compatible).

    Usage::

        from pytanga.viz import Visualizer
        from pytanga.geometry import Point

        viz = Visualizer(opns=True)
        viz.add(Point(1, 2, 3), color="#ff4444")
        viz.run()  # opens browser, blocks until Ctrl+C

    Create additional scenes::

        details = viz.scene("details")
        details.add(Sphere(0, 0, 0, 2), opacity=0.3)
    """

    # ── _JupyterDisplayMixin contract ──────────────────────
    _viewer_name: str | None = None
    _name: str = ""

    @property
    def _space_extent(self) -> float:
        return self._config.space_extent

    # ── Visualizer ─────────────────────────────────────────

    def __init__(
        self,
        *,
        port: int = 8765,
        host: str = "localhost",
        open_browser: bool | None = None,
        reuse_existing: bool = True,
        opns: bool = True,
        title: str = "Tanga 3D Viewer",
        annotation: str | None = None,
        # Scene configuration
        space_extent: float = 10.0,
        show_grid: bool = True,
        show_axes: bool = True,
        background_color: str = "#1a1a2e",
        # Camera configuration (None = auto-fit from entities)
        camera: CameraConfig | None = None,
    ) -> None:
        self._config = SceneConfig(
            space_extent=space_extent,
            show_grid=show_grid,
            show_axes=show_axes,
            background_color=background_color,
            camera=camera,
            title=title,
            annotation=annotation,
            name="",
        )
        self._port = port
        self._host = host
        self._open_browser = open_browser
        self._reuse_existing = reuse_existing
        self._opns = opns
        self._title = title
        self._annotation = annotation
        self._server = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None

        # Auto-detect Jupyter: disable browser open, enable _repr_html_
        self._jupyter = _is_jupyter()
        if open_browser is None:
            open_browser = not self._jupyter
        self._open_browser = open_browser

        # Per-kind entity/operator style instances (shared across all scenes).
        self._default_styles = _make_default_styles()

        # Default style instances (factory functions in _style_dict.py)
        self._default_label_style = _make_default_label_style()
        self._default_annotation_style = _make_default_annotation_style()
        self._default_label_styles = _make_default_label_styles()

        # Control handler registry (shared across all scenes)
        from ._controls import ControlHandlerRegistry

        self._handler_registry = ControlHandlerRegistry()

        # ── Multi-scene storage ──
        # Key "" is the main scene (backward compatible).
        self._scenes: dict[str, Scene] = {}
        self._scenes[""] = Scene(self._config, name="")

    # ── Scene access ─────────────────────────────────────────

    def scene(self, name: str) -> VizSceneHandle:
        """Get or create a named scene, returning a :class:`VizSceneHandle`.

        The handle exposes the full entity/control/animation API scoped to
        that scene.  Scenes inherit the visualizer's default styles.

        Names may contain slashes for grouping, e.g. ``"slides/intro"``.
        """
        if name not in self._scenes:
            cfg = SceneConfig(
                space_extent=self._config.space_extent,
                show_grid=self._config.show_grid,
                show_axes=self._config.show_axes,
                background_color=self._config.background_color,
                camera=None,
                title=name or self._config.title,
                name=name,
            )
            self._scenes[name] = Scene(cfg, name=name)
        return VizSceneHandle(self, name)

    @property
    def scenes(self) -> dict[str, Scene]:
        """All scenes keyed by name (``""`` is the main scene)."""
        return self._scenes

    @property
    def _scene(self) -> Scene:
        """The main scene (backward-compat property)."""
        return self._scenes[""]

    @_scene.setter
    def _scene(self, value: Scene) -> None:
        self._scenes[""] = value

    def list_scenes(self) -> list[str]:
        """Return all scene names (main scene is ``""``)."""
        return list(self._scenes.keys())

    def list_browsers(self) -> list[dict[str, str]]:
        """Return connected browser sessions as ``[{id, scene, remote_addr}]``.

        Returns an empty list if the server is not running.
        """
        if self._server is None:
            return []
        return self._server.get_browser_sessions()

    def navigate_to(self, scene_name: str, *, target: str = "all") -> None:
        """Send a navigate command to matching browser sessions.

        Args:
            scene_name: The target scene name (``""`` for the main scene).
            target: One of ``"all"`` (all connected browsers),
                ``"scene:<name>"`` (only browsers currently viewing a
                specific scene), or ``"browser:<id>"`` (a single browser).
        """
        if self._server is None or self._loop is None:
            return
        asyncio.run_coroutine_threadsafe(
            self._server.push_navigate(scene_name, target), self._loop
        )

    # ── Entity management (main scene) ───────────────────────

    def add(
        self,
        obj: VizInputType | None = None,
        *,
        entity_id: str | None = None,
        opns: bool | None = None,
        color: str
        | tuple[float, float, float]
        | tuple[float, float, float, float]
        | None = None,
        opacity: float | None = None,
        style: ObjVizStyle | None = None,
        label: str | None = None,
        label_style: LabelStyle | None = None,
    ) -> str | list[str] | tuple[str, str]:
        """Add a geometric entity, operator, multivector, or label to the main scene.

        See the class docstring for full parameter documentation.
        """
        return self._add_to_scene(
            "",
            obj=obj,
            entity_id=entity_id,
            opns=opns,
            color=color,
            opacity=opacity,
            style=style,
            label=label,
            label_style=label_style,
        )

    def _add_to_scene(
        self,
        scene_name: str,
        *,
        obj: VizInputType | None = None,
        entity_id: str | None = None,
        opns: bool | None = None,
        color: Any = None,
        opacity: float | None = None,
        style: ObjVizStyle | None = None,
        label: str | None = None,
        label_style: LabelStyle | None = None,
    ) -> str | list[str] | tuple[str, str]:
        """Add an entity to a specific scene."""
        from ._label import Label
        from ._styles import LabelStyle as _LS

        scene = self._scenes[scene_name]

        if isinstance(obj, Label):
            return scene.add_label(obj)

        if opns is None:
            opns = self._opns

        properties: dict[str, Any] = {}

        if color is not None:
            normalized = _normalize_color(color)
            if isinstance(normalized, tuple):
                properties["color"] = normalized[0]
                if opacity is None:
                    properties["opacity"] = normalized[1]
            else:
                properties["color"] = normalized

        if opacity is not None:
            properties["opacity"] = float(opacity)

        if style is not None:
            properties["style"] = style

        entity = self._resolve(obj, opns=opns)
        if isinstance(entity, list):
            ids: list[str] = []
            for ent in entity:
                eid = scene.add(
                    ent,
                    entity_id=entity_id if len(entity) == 1 else None,
                    **properties,
                )
                ids.append(eid)
            return ids

        eid = scene.add(entity, entity_id=entity_id, **properties)

        if label is not None:
            from ._label_frame import compute_label_position

            kind = type(entity).__name__
            resolved_ls = _resolve_label_style(
                self._default_label_style,
                self._default_label_styles.get(kind),
                label_style or _LS(),
            )

            position = compute_label_position(entity, resolved_ls.offset_local)
            lbl = Label(
                text=label,
                position=position,
                parent_id=eid,
                style=resolved_ls,
            )
            lid = scene.add_label(lbl)
            return (eid, lid)

        return eid

    def update(self, entity_id: str, **properties: Any) -> None:
        """Update rendering properties of an existing entity in the main scene."""
        self._scenes[""].update(entity_id, **properties)

    def update_entity(
        self, entity_id: str, obj: GeoEntity | Any, *, opns: bool | None = None
    ) -> None:
        """Replace the geometry for an existing entity in the main scene."""
        if opns is None:
            opns = self._opns
        entity = self._resolve(obj, opns=opns)
        if isinstance(entity, list):
            raise ValueError(
                f"update_entity expects a single entity, but the MV resolved to "
                f"{len(entity)} entities. Use the first one explicitly."
            )
        self._scenes[""].update_entity(entity_id, entity)

    def update_label(
        self,
        object_id: str,
        *,
        text: str | None = None,
        style: LabelStyle | None = None,
    ) -> None:
        """Update a label's text and/or style in the main scene."""
        self._scenes[""].update_label(object_id, text=text, style=style)

    def remove(self, entity_id: str) -> None:
        """Remove an entity from the main scene."""
        self._scenes[""].remove(entity_id)

    def clear(self) -> None:
        """Remove all entities from the main scene."""
        self._scenes[""].clear()

    # ── Title & annotation ──────────────────────────────────

    def set_title(self, title: str) -> None:
        """Update the viewport title overlay for the main scene."""
        self._set_scene_title("", title)

    def _set_scene_title(self, scene_name: str, title: str) -> None:
        scene = self._scenes[scene_name]
        scene.config.title = title
        self._push_scene_config(scene_name)

    def set_annotation(
        self, text: str | None, *, style: AnnotationStyle | None = None
    ) -> None:
        """Set or update the markdown annotation panel for the main scene."""
        self._set_scene_annotation("", text, style=style)

    def _set_scene_annotation(
        self, scene_name: str, text: str | None, *, style: AnnotationStyle | None = None
    ) -> None:
        scene = self._scenes[scene_name]
        scene.config.annotation = text

        if text is None or text == "":
            scene.remove("__annotation__")
        else:
            style_dict = _resolve_annotation_style(
                self._default_annotation_style, style
            )
            obj = SceneObject(
                id="__annotation__",
                layer="overlay",
                kind="annotation",
                data={"text": text, "style": style_dict},
            )
            scene.add_object(obj, object_id="__annotation__")

        self._flush_scene(scene_name)

    def _push_scene_config(self, scene_name: str = "") -> None:
        """Push the current SceneConfig to all connected WebSocket clients."""
        if self._server is None or self._loop is None:
            return
        data = json.dumps(self._scenes[scene_name].config.to_dict())
        asyncio.run_coroutine_threadsafe(self._server.push_raw(data), self._loop)

    @staticmethod
    def sleep_ms(milliseconds: int) -> None:
        """Pause execution for *milliseconds*."""
        time.sleep(milliseconds / 1000)

    # ── Default style configuration ─────────────────────────

    def set_default_color(
        self,
        kind: str,
        color: str | tuple[float, float, float] | tuple[float, float, float, float],
    ) -> None:
        """Set the default color (and optionally opacity) for an entity kind."""
        normalized = _normalize_color(color)
        key = _kind_to_key(kind)
        if key not in self._default_styles:
            raise ValueError(f"Unknown entity kind: {kind!r}")

        if isinstance(normalized, tuple):
            self._default_styles[key].color = normalized[0]
            self._default_styles[key].opacity = normalized[1]
        else:
            self._default_styles[key].color = normalized

    # ── MV resolution ──────────────────────────────────────

    def _resolve(self, obj: Any, *, opns: bool = True) -> GeoEntity | list[GeoEntity]:
        """Resolve an MV or Entity/Operator to one or more geo entities."""
        from pytanga.geometry.operators import Operator as GeoOperator

        if isinstance(obj, (GeoEntity, GeoOperator)):
            return obj  # type: ignore[return-value]

        try:
            from pytanga.geometry import analyze

            result = analyze(obj, opns=opns)
            if result is None:
                raise ValueError(f"Could not analyze object: {obj!r}")
            return result
        except ImportError:
            raise TypeError(
                f"Object of type {type(obj).__name__} is not a recognized "
                f"geometry entity, operator, or multivector."
            ) from None

    # ── Animation ──────────────────────────────────────────

    def animate_to(
        self,
        entity_id: str,
        *,
        position: tuple[float, float, float] | None = None,
        rotation: tuple[float, float, float] | None = None,
        opacity: float | None = None,
        scale: tuple[float, float, float] | None = None,
        duration: float = 1.0,
        easing: str = "ease-in-out",
    ) -> None:
        """Animate an entity in the main scene."""
        self._animate_scene_entity(
            "",
            entity_id,
            position=position,
            rotation=rotation,
            opacity=opacity,
            scale=scale,
            duration=duration,
            easing=easing,
        )

    def _animate_scene_entity(
        self,
        scene_name: str,
        entity_id: str,
        *,
        position: tuple[float, float, float] | None = None,
        rotation: tuple[float, float, float] | None = None,
        opacity: float | None = None,
        scale: tuple[float, float, float] | None = None,
        duration: float = 1.0,
        easing: str = "ease-in-out",
    ) -> None:
        if self._server is None:
            return

        target: dict[str, Any] = {}
        if position is not None:
            target["position"] = list(position)
        if rotation is not None:
            target["rotation"] = list(rotation)
        if opacity is not None:
            target["opacity"] = float(opacity)
        if scale is not None:
            target["scale"] = list(scale)

        if not target:
            return

        message = {
            "type": "animate",
            "scene": scene_name,
            "animations": [
                {
                    "id": entity_id,
                    "target": target,
                    "duration": duration,
                    "easing": easing,
                }
            ],
        }

        self._send_raw(json.dumps(message))

    def timeline(self) -> Timeline:
        """Create a :class:`Timeline` for the main scene."""
        return Timeline(self)

    def _scene_timeline(self, scene_name: str) -> Timeline:
        """Create a :class:`Timeline` targeting a specific scene."""
        return Timeline(self, scene_name=scene_name)

    def _send_raw(self, data: str) -> None:
        """Send an arbitrary JSON string to all connected WebSocket clients."""
        if self._server is None or self._loop is None:
            return
        asyncio.run_coroutine_threadsafe(self._server.push_raw(data), self._loop)

    # ── Server lifecycle ───────────────────────────────────

    def start(
        self, *, wait_for_browser: bool | None = None, timeout: float = 30.0
    ) -> bool:
        """Start the WebSocket server in a background thread (non-blocking).

        In Jupyter, ``wait_for_browser`` defaults to ``False`` because the
        iframes connect asynchronously when they render.  Outside Jupyter
        it defaults to ``True`` so entities are pushed reliably.
        """
        if wait_for_browser is None:
            wait_for_browser = not self._jupyter

        if self._server is not None:
            self.stop()

        from .server import VizServer

        self._server = VizServer(host=self._host, port=self._port)

        _boot_done = threading.Event()

        async def _boot() -> None:
            await self._server.start(
                lambda scene_name: (
                    self._scenes.get(scene_name, self._scenes[""]).full_state(
                        styles_map=self._default_styles
                    ),
                    [],
                ),
                self._config.to_dict,
                control_callback=self._dispatch_control_event,
                on_connect=self._on_client_connect,
                on_disconnect=self._on_client_disconnect,
                push_controls=self._push_controls_async,
                scene_config_callback=self._scene_config_for,
                scene_list_callback=self.list_scenes,
            )
            _boot_done.set()

        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        self._loop.create_task(_boot())

        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()

        if not _boot_done.wait(timeout=5.0):
            raise RuntimeError("Server failed to start within 5s")

        if self._open_browser:
            if self._reuse_existing:
                if not self._wait_for_client_quiet(timeout=3.0):
                    self._server.open_browser()
            else:
                self._server.open_browser()

        if wait_for_browser:
            return self.wait_for_browser(timeout=timeout)
        return True

    def _scene_config_for(self, scene_name: str) -> dict[str, Any] | None:
        """Callback: return config dict for a named scene, or None if not found."""
        scene = self._scenes.get(scene_name)
        if scene is None:
            return None
        return scene.config.to_dict()

    def stop(self, *, timeout: float = 5.0) -> None:
        """Stop the server and clean up."""
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

    def wait_for_browser(self, timeout: float = 30.0) -> bool:
        """Block until a browser connects to the viewer."""
        if self._server is None or self._loop is None:
            raise RuntimeError("Server not started. Call start() first.")

        try:
            from rich.console import Console, Group
            from rich.live import Live
            from rich.spinner import Spinner
            from rich.text import Text

            console = Console()
            url_text = Text(self.url, style="bold cyan underline")
            spinner = Spinner("dots", style="yellow")

            with Live(
                Group(
                    spinner,
                    Text.assemble(
                        " Waiting for browser to connect at ",
                        url_text,
                        " ...",
                    ),
                ),
                console=console,
                transient=True,
                refresh_per_second=10,
            ) as live:
                deadline = time.monotonic() + timeout
                while time.monotonic() < deadline:
                    if self._server._ws_clients:
                        live.update(
                            Text.from_markup(
                                "[bold green]✓[/bold green] Browser connected."
                            ),
                        )
                        return True
                    live.update(
                        Group(
                            spinner,
                            Text.assemble(
                                " Waiting for browser to connect at ",
                                url_text,
                                f" ... ({time.monotonic() - (deadline - timeout):.0f}s / {timeout:.0f}s)",
                            ),
                        ),
                    )
                    time.sleep(0.1)

            console.print(
                Text.from_markup(
                    f"[bold red]✗[/bold red] No browser connected within {timeout:.0f}s"
                )
            )
            return False
        except ImportError:
            print(f"Waiting for browser to connect at {self.url} ...")
            future = asyncio.run_coroutine_threadsafe(
                self._server.wait_for_client(timeout), self._loop
            )
            try:
                connected = future.result(timeout=timeout + 2)
                if connected:
                    print("Browser connected.")
                return connected
            except TimeoutError:
                return False

    def _wait_for_client_quiet(self, timeout: float = 3.0) -> bool:
        """Poll for a WebSocket client with a compact spinner."""
        if self._server is None:
            return False

        import sys

        sys.stdout.write("Waiting for existing browser to reconnect ...\n")
        sys.stdout.flush()
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self._server._ws_clients:
                return True
            time.sleep(0.1)

        print("No existing browser connected — opening new tab.")
        return False

    def _print_connect(self, remote_addr: str) -> None:
        try:
            from rich.console import Console
            from rich.text import Text

            Console().print(
                Text(f"✓ Browser connected  ({remote_addr}).", style="bold green")
            )
        except ImportError:
            print(f"Browser connected ({remote_addr}).")

    def _print_disconnect(self, remote_addr: str) -> None:
        try:
            from rich.console import Console
            from rich.text import Text

            Console().print(
                Text(f"Browser disconnected  ({remote_addr}).", style="bold yellow")
            )
        except ImportError:
            print(f"Browser disconnected ({remote_addr}).")

    async def _flush_scene_async(self, scene_name: str) -> None:
        """Push dirty state for a specific scene (must be called from server's event loop)."""
        if self._server is None:
            return
        scene = self._scenes.get(scene_name)
        if scene is None:
            return
        entities, removed = scene.flush(styles_map=self._default_styles)
        if entities or removed:
            await self._server.push(entities, removed, scene=scene_name)

    def _flush_scene(self, scene_name: str) -> None:
        """Schedule a scene update on the server's event loop (thread-safe)."""
        if self._loop is not None and self._server is not None:
            asyncio.run_coroutine_threadsafe(
                self._flush_scene_async(scene_name), self._loop
            )

    def flush(self) -> None:
        """Schedule all dirty scenes to be pushed to the server (thread-safe)."""
        if self._loop is not None and self._server is not None:
            for name in self._scenes:
                self._flush_scene(name)

    def run(self, *, wait_for_browser: bool | None = None) -> None:
        """Start the server, open the browser, and block until interrupted.

        In Jupyter, ``wait_for_browser`` defaults to ``False``.
        """
        if wait_for_browser is None:
            wait_for_browser = not self._jupyter
        from .server import VizServer

        self._server = VizServer(host=self._host, port=self._port)

        async def _run() -> None:
            await self._server.start(
                lambda scene_name: (
                    self._scenes.get(scene_name, self._scenes[""]).full_state(
                        styles_map=self._default_styles
                    ),
                    [],
                ),
                self._config.to_dict,
                control_callback=self._dispatch_control_event,
                on_connect=self._on_client_connect,
                scene_config_callback=self._scene_config_for,
                scene_list_callback=self.list_scenes,
            )
            if self._open_browser:
                self._server.open_browser()
            if wait_for_browser:
                await self._server.wait_for_client()
            # Flush initial state for the main scene
            await self._flush_scene_async("")

            stop_event = asyncio.Event()
            loop = asyncio.get_running_loop()

            def _signal_handler() -> None:
                stop_event.set()

            for sig in (signal.SIGINT, signal.SIGTERM):
                try:
                    loop.add_signal_handler(sig, _signal_handler)
                except NotImplementedError:
                    pass

            await stop_event.wait()

        try:
            asyncio.run(_run())
        except KeyboardInterrupt:
            pass
        finally:
            if self._server is not None:
                try:
                    asyncio.run(self._server.stop())
                except Exception:
                    pass
            try:
                from rich.console import Console
                from rich.text import Text

                Console().print(Text("Visualizer shut down.", style="dim"))
            except ImportError:
                print("Visualizer shut down.")

    # ── Interactive Controls (main scene) ───────────────────

    def add_slider(
        self,
        cid: str,
        *,
        label: str = "",
        min: float = 0.0,
        max: float = 1.0,
        step: float = 0.01,
        default: float | None = None,
        on_change: Any = None,
        parent_id: str | None = None,
    ) -> str:
        return self._add_scene_slider(
            "",
            cid,
            label=label,
            min=min,
            max=max,
            step=step,
            default=default,
            on_change=on_change,
            parent_id=parent_id,
        )

    def _add_scene_slider(
        self,
        scene_name: str,
        cid: str,
        *,
        label: str = "",
        min: float = 0.0,
        max: float = 1.0,
        step: float = 0.01,
        default: float | None = None,
        on_change: Any = None,
        parent_id: str | None = None,
    ) -> str:
        from ._controls import Slider

        ctrl = Slider(
            id=cid,
            label=label,
            min=min,
            max=max,
            step=step,
            default=default if default is not None else min,
            on_change=on_change,
            parent_id=parent_id,
        )
        self._scenes[scene_name].add_control(ctrl)
        if on_change is not None:
            self._handler_registry.register(cid, on_change)
        self._push_controls(scene_name)
        return cid

    def add_dropdown(
        self,
        cid: str,
        *,
        label: str = "",
        options: list[str] | None = None,
        default: str = "",
        on_change: Any = None,
        parent_id: str | None = None,
    ) -> str:
        return self._add_scene_dropdown(
            "",
            cid,
            label=label,
            options=options,
            default=default,
            on_change=on_change,
            parent_id=parent_id,
        )

    def _add_scene_dropdown(
        self,
        scene_name: str,
        cid: str,
        *,
        label: str = "",
        options: list[str] | None = None,
        default: str = "",
        on_change: Any = None,
        parent_id: str | None = None,
    ) -> str:
        from ._controls import Dropdown

        ctrl = Dropdown(
            id=cid,
            label=label,
            options=options or [],
            default=default,
            on_change=on_change,
            parent_id=parent_id,
        )
        self._scenes[scene_name].add_control(ctrl)
        if on_change is not None:
            self._handler_registry.register(cid, on_change)
        self._push_controls(scene_name)
        return cid

    def add_button(
        self,
        cid: str,
        *,
        label: str = "",
        on_click: Any = None,
        parent_id: str | None = None,
    ) -> str:
        return self._add_scene_button(
            "",
            cid,
            label=label,
            on_click=on_click,
            parent_id=parent_id,
        )

    def _add_scene_button(
        self,
        scene_name: str,
        cid: str,
        *,
        label: str = "",
        on_click: Any = None,
        parent_id: str | None = None,
    ) -> str:
        from ._controls import Button

        ctrl = Button(id=cid, label=label, on_click=on_click, parent_id=parent_id)
        self._scenes[scene_name].add_control(ctrl)
        if on_click is not None:
            self._handler_registry.register(cid, on_click)
        self._push_controls(scene_name)
        return cid

    def add_group(
        self,
        gid: str,
        *,
        title: str = "",
        controls: list[str] | None = None,
        position: str = "bottom-right",
        collapsed: bool = False,
        parent_id: str | None = None,
        on_toggle: Any = None,
    ) -> str:
        return self._add_scene_group(
            "",
            gid,
            title=title,
            controls=controls,
            position=position,
            collapsed=collapsed,
            parent_id=parent_id,
            on_toggle=on_toggle,
        )

    def _add_scene_group(
        self,
        scene_name: str,
        gid: str,
        *,
        title: str = "",
        controls: list[str] | None = None,
        position: str = "bottom-right",
        collapsed: bool = False,
        parent_id: str | None = None,
        on_toggle: Any = None,
    ) -> str:
        from ._controls import ControlGroup

        group = ControlGroup(
            id=gid,
            title=title,
            controls=controls or [],
            position=position,
            collapsed=collapsed,
            parent_id=parent_id,
            on_toggle=on_toggle,
        )
        self._scenes[scene_name].add_group(group)
        if on_toggle is not None:
            self._handler_registry.register(f"__group__{gid}", on_toggle)
        self._push_controls(scene_name)
        return gid

    def remove_control(self, cid: str) -> None:
        self._remove_scene_control("", cid)

    def _remove_scene_control(self, scene_name: str, cid: str) -> None:
        self._handler_registry.unregister(cid)
        self._scenes[scene_name].remove_control(cid)
        self._push_controls(scene_name)

    def remove_group(self, gid: str) -> None:
        self._remove_scene_group("", gid)

    def _remove_scene_group(self, scene_name: str, gid: str) -> None:
        self._handler_registry.unregister(f"__group__{gid}")
        self._scenes[scene_name].remove_group(gid)
        self._push_controls(scene_name)

    def clear_controls(self) -> None:
        self._clear_scene_controls("")

    def _clear_scene_controls(self, scene_name: str) -> None:
        self._handler_registry.clear()
        self._scenes[scene_name].clear_controls()
        self._push_controls_clear(scene_name)

    def _push_controls(self, scene_name: str = "") -> None:
        """Serialise current controls/groups for a scene and push to the frontend."""
        if self._server is None or self._loop is None:
            return
        from ._controls import serialize_controls

        scene = self._scenes[scene_name]
        groups = list(scene._groups.values())
        message = serialize_controls(groups, scene._controls)
        message["scene"] = scene_name
        asyncio.run_coroutine_threadsafe(
            self._server.push_raw(json.dumps(message)), self._loop
        )

    async def _push_controls_async(self, scene_name: str = "") -> None:
        """Async variant — must be called from the server's event loop."""
        if self._server is None:
            return
        from ._controls import serialize_controls

        scene = self._scenes.get(scene_name, self._scenes[""])
        groups = list(scene._groups.values())
        message = serialize_controls(groups, scene._controls)
        message["scene"] = scene_name
        await self._server.push_raw(json.dumps(message))

    def _push_controls_clear(self, scene_name: str = "") -> None:
        """Push a controls_clear message for a scene."""
        if self._server is None or self._loop is None:
            return
        asyncio.run_coroutine_threadsafe(
            self._server.push_raw(
                json.dumps({"type": "controls_clear", "scene": scene_name})
            ),
            self._loop,
        )

    async def _dispatch_control_event(
        self, msg_type: str, payload: dict[str, Any]
    ) -> None:
        """Handle an incoming control event from the frontend."""
        cid = payload.get("control_id")
        browser_id = payload.get("browser_id")
        if cid and (handler := self._handler_registry.get(cid)):
            try:
                if msg_type == "control:change":
                    await handler(payload.get("value"), browser_id=browser_id)
                elif msg_type == "control:click":
                    await handler(None, browser_id=browser_id)
                elif msg_type == "control:group_toggle":
                    await handler(payload.get("value"), browser_id=browser_id)
            except Exception:
                import logging

                logging.getLogger(__name__).exception(
                    "Error in control handler for %r", cid
                )

    async def _on_client_connect(self, remote_addr: str) -> None:
        """Push controls state and scene list when a new client connects."""
        self._print_connect(remote_addr)
        # Push controls for the main scene initially (scene-specific push happens
        # after the ready message tells us which scene the client wants)
        await self._push_controls_async("")

    async def _on_client_disconnect(self, remote_addr: str) -> None:
        """Log when a client disconnects."""
        self._print_disconnect(remote_addr)

    # ── Properties ──────────────────────────────────────────

    # ── Jupyter support ─────────────────────────────────────

    def display_row(
        self,
        *scenes: tuple[VizSceneHandle, str | None],
        width: int | str = "100%",
        height: int | str = 500,
        gap: int = 8,
    ) -> Any:
        """Display multiple scenes side by side in a single flex row.

        Each element in *scenes* is a ``(handle, viewer_name)`` tuple where
        *viewer_name* may be ``None``.

        Usage::

            viz.display_row(
                (one, "browser-one"),
                (two, "browser-two"),
                (three, "browser-three"),
            )

        Args:
            *scenes: One or more ``(VizSceneHandle, viewer_name | None)`` pairs.
            width: CSS width of the container (default ``"100%"``).
            height: CSS height of each iframe in pixels (default 500).
            gap: Gap between columns in pixels (default 8).
        """
        from IPython.display import HTML
        from IPython.display import display as ipy_display

        columns_html: list[str] = []
        for handle, viewer_name in scenes:
            src = handle.url
            if viewer_name:
                src += f"?viewer={viewer_name}"
            columns_html.append(
                f'<div style="flex: 1; min-width: 0;">'
                f'<h3 style="margin: 0 0 4px 0; font-size: 14px; color: #ccc;">Scene: {handle.name}</h3>'
                f'<iframe src="{src}" width="100%" height="{height}px" '
                f'style="border: 1px solid #444; border-radius: 4px;" '
                f'title="Tanga 3D Viewer — {handle.name}"></iframe>'
                f"</div>"
            )

        html = '<div style="display: flex; gap: {}px; width: {};">'.format(gap, width)
        html += "".join(columns_html)
        html += "</div>"
        ipy_display(HTML(html))
        return None

    def display_static(
        self,
        width: int | str = "100%",
        height: int | str = "500px",
        *,
        scene_name: str = "",
    ) -> Any:
        """Display a scene as standalone HTML (no server required).

        Parameters
        ----------
        width : int | str
            CSS width of the viewer.
        height : int | str
            CSS height of the viewer.
        scene_name : str
            The scene to display (``""`` for the main scene).
        """
        from pytanga.viz.export._html import render_export_html

        scene = self._scenes[scene_name]
        all_objects = scene.full_state(styles_map=self._default_styles)
        entities = [obj for obj in all_objects if obj.get("kind") != "label"]
        labels = scene._serialize_labels()

        html = render_export_html(
            entities=entities,
            labels=labels,
            scene_config=scene.config.to_dict(),
        )

        if self._jupyter:
            from IPython.display import HTML

            return HTML(html)
        else:
            import tempfile
            import webbrowser
            from pathlib import Path

            tmp = Path(tempfile.mktemp(suffix=".html"))
            tmp.write_text(html, encoding="utf-8")
            webbrowser.open(str(tmp))
            return None

    @property
    def default_styles(self) -> _StyleDict:
        """Per-kind style instances used as defaults."""
        return self._default_styles

    @property
    def default_label_style(self) -> LabelStyle:
        """The global default ``LabelStyle`` instance."""
        return self._default_label_style

    @property
    def default_label_styles(self) -> dict[str, LabelStyle | None]:
        """Per-kind default label style overrides."""
        return self._default_label_styles

    @property
    def main_scene(self) -> Scene:
        """The underlying main :class:`Scene` instance (backward compat)."""
        return self._scenes[""]

    @property
    def default_annotation_style(self) -> AnnotationStyle:
        """The global default ``AnnotationStyle`` instance."""
        return self._default_annotation_style

    @property
    def url(self) -> str:
        """The HTTP URL of the viewer."""
        return f"http://{self._host}:{self._port}"
