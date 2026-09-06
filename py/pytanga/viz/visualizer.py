# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Top-level Visualizer class — the user-facing API for the Tanga 3D viewer.

Supports multiple named scenes, each served at a unique URL path.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import json
import logging
import signal
import threading
import time
import warnings
from typing import TYPE_CHECKING, Any, Iterator, Sequence

if TYPE_CHECKING:
    from ._object_ref import VizObjectRef
    from ._styles import AnnotationStyle, LabelStyle, ObjVizStyle, TextureLabelStyle
    from ._viz_styles import VizStyles

from ._jupyter import _JupyterDisplayMixin
from ._keys import KeyModifier
from ._notebook_cell import current_cell_id, execution_token
from ._props import _normalize_color
from ._scene_handle import VizSceneHandle
from ._style_dict import (
    _kind_to_key,
    _resolve_annotation_style,
)
from ._timeline import Timeline
from ._types import SceneEntity, TransformRotation, Triple, Vec3, VizInputType
from ._utils import _is_jupyter
from .camera import (
    CameraConfig,
    View2DConfig,
    View3dConfig,
    _deduce_space_dim,
    _normalize_camera_config,
)
from .scene import Scene, SceneConfig, SceneObject
from .views import (
    SceneView,
    View,
)

logger = logging.getLogger("tanga.viz")


# Standard HTTP + WebSocket port.  Kept stable (rather than auto-picking a
# free port each time) so an already-open browser tab can reconnect to a
# restarted server.  Override via ``start_server(port=...)``; pass ``port=0``
# to explicitly auto-pick a free port.
DEFAULT_PORT = 8765


def _find_free_port(host: str) -> int:
    """Find an available TCP port on *host*."""
    import socket

    bind_host = "127.0.0.1" if host in ("localhost", "127.0.0.1") else host
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((bind_host, 0))
        return int(sock.getsockname()[1])


def _validate_space_dim(space_dim: int) -> int:
    """Validate a ``space_dim`` value (2 or 3) and return it unchanged."""
    if isinstance(space_dim, bool) or not isinstance(space_dim, int):
        raise ValueError(f"space_dim must be 2 or 3, got {space_dim!r}")
    if space_dim not in (2, 3):
        raise ValueError(f"space_dim must be 2 or 3, got {space_dim!r}")
    return space_dim


class Visualizer(_JupyterDisplayMixin):
    """Interactive 3D visualization of geometric entities via Three.js in a browser.

    Supports multiple named scenes, each reachable at ``/{name}`` under the
    main URL.  Entities added directly to the visualizer go to the **main
    scene** (backward compatible).

    Usage::

        from pytanga.viz import Visualizer
        from pytanga.geometry import Point

        viz = Visualizer()
        viz.add(Point(1, 2, 3), color="#ff4444")
        viz.run()  # opens browser, blocks until Ctrl+C

    Create additional scenes::

        details = viz.scene("details")
        details.add(Sphere(0, 0, 0, 2), opacity=0.3)
    """

    # ── _JupyterDisplayMixin contract ──────────────────────
    _viewer_name: str | None = None
    _name: str = ""

    # ── Visualizer ─────────────────────────────────────────

    def __init__(
        self,
        *,
        reuse_existing: bool = True,
        title: str = "Tanga 3D Viewer",
        annotation: str | None = None,
        background_color: str | None = None,
        # Camera configuration (None = auto-fit from entities). Accepts a
        # CameraConfig, or a View2DConfig/View3dConfig input spec.
        camera: CameraConfig | View2DConfig | View3dConfig | None = None,
        # 2 or 3. When None (default), deduced from the camera config whenever
        # possible; otherwise 3.
        space_dim: int | None = None,
        # Whether to automatically add default coordinate axes / a grid to
        # each scene.  Independent of the server and fully authoritative.
        add_default_axes: bool = True,
        add_default_grid: bool = True,
        # When True, enable the browser-triggered full-server stop key
        # (Ctrl+Q by default) for the main scene only.  Named scenes opt in via
        # ``VizSceneHandle.enable_server_stop_key()``.
        enable_server_stop_key: bool = False,
    ) -> None:
        if space_dim is None:
            space_dim = _deduce_space_dim(camera) or 3
        if space_dim == 2 and title == "Tanga 3D Viewer":
            title = "Tanga 2D Viewer"
        self._config = SceneConfig(
            background_color=background_color,
            camera=_normalize_camera_config(camera),
            title=title,
            annotation=annotation,
            name="",
            space_dim=space_dim,
        )
        self._port = DEFAULT_PORT
        self._host = "localhost"
        self._reuse_existing = reuse_existing
        self._title = title
        self._annotation = annotation
        self._add_default_axes = add_default_axes
        self._add_default_grid = add_default_grid
        # Late-bound server/loop holder shared with the Transport and hosts.
        # ``_server`` / ``_loop`` are properties backed by this state.
        from ._ports import ServerState

        self._server_state = ServerState()
        self._thread: threading.Thread | None = None
        self._saved_signal_handlers: dict[int, Any] | None = None
        self._atexit_registered = False
        self._display_pending: set[str] = set()
        self._display_execution: int | None = None

        # Interrupt handling: a global shutdown event (terminal Ctrl+C/SIGTERM)
        # plus lazily-created per-scene events (browser-side stop key).
        self._interrupt_events: dict[str, threading.Event] = {}
        self._scene_interrupt_configs: dict[str, dict[str, Any]] = {}
        # Per-scene browser-triggered full-server stop bindings (opt-in).
        self._server_stop_configs: dict[str, dict[str, Any]] = {}

        # Auto-detect Jupyter: disable browser open, enable _repr_html_
        self._jupyter = _is_jupyter()
        self._open_browser = not self._jupyter

        # Bundled default style configuration (master instance; scenes copy it).
        from ._viz_styles import make_styles

        self._global_styles = make_styles()

        # Control handler registry (shared across all scenes)
        from ._controls import CLIENT_LOG_ID, ClientLog, ControlHandlerRegistry

        self._handler_registry = ControlHandlerRegistry()

        # The Transport wraps the server + (id, event) registry; hosts talk and
        # register through it instead of reaching into the Visualizer.
        from ._transport import WebSocketTransport

        self._transport = WebSocketTransport(self._server_state, self._handler_registry)

        # Backend-only sink for browser log events (see `on_client_log`).
        self._client_log = ClientLog(CLIENT_LOG_ID)
        self._client_log.register_handlers(self._transport)

        # ── Multi-scene storage ──
        # Key "" is the main scene (backward compatible).
        # Layout host (view tree, overlays, serialization); the Visualizer
        # delegates control/theme/interaction concerns to the hosts below.
        from ._hosts import (
            InteractionHost,
            ThemeHost,
        )
        from ._layout import LayoutHostImpl

        self._layout = LayoutHostImpl(
            self._server_state,
            scene_factory=self._create_scene,
            transport=self._transport,
            client_log=self._client_log,
        )
        self._layout.add_scene("")
        self._theme_host = ThemeHost(self._transport, self._layout)
        self._interaction_host = InteractionHost(
            self._transport, self._layout, self._handler_registry
        )

        # Inbound routing: a data table on the transport.
        self._register_routes()

        self._default_objects_added: set[str] = set()

        # Seed default axes/grid immediately — independent of server start.
        self._add_default_scene_objects("")

        # Opt-in browser-triggered server stop for the main scene.
        if enable_server_stop_key:
            self.enable_server_stop_key()

    # ── Facade: layout ─────────────────────────────────────

    @property
    def layout(self) -> Any:
        """The :class:`LayoutHost` (scenes + layouts)."""
        return self._layout

    def set_layout(self, root: Any, name: str = "") -> str:
        """Register (or replace) a layout; register its control handlers."""
        return self._layout.set_layout(root, name)

    def add_layout(self, root: Any, name: str = "") -> str:
        """Register a layout (raise if *name* is taken)."""
        return self._layout.add_layout(root, name)

    def remove_view(self, view_id: str, *, scene: str | None = None) -> None:
        """Remove a mounted overlay view by its stable id (see ``viz.add``)."""
        self._layout.remove_view(view_id, scene=scene)

    def on_client_log(self, handler: Any) -> None:
        """Replace the backend sink for browser ``sendLog`` events.

        *handler* is an ``async def(value, event)`` receiving a
        :class:`~pytanga.viz._controls.ClientLogRecord`; the default logs via
        ``logging.getLogger("tanga.viz.client")``.
        """
        self._client_log.on_log = handler
        self._client_log.register_handlers(self._transport)

    # ── Facade: file chooser ───────────────────────────────

    def open_file_chooser(
        self, cid: str, *, scene_name: str = "", path: str | None = None
    ) -> None:
        """Open the file browser dialog for control *cid* (from the backend)."""
        self._layout.open_file_chooser(cid, path=path)

    def close_file_chooser(self, cid: str, *, scene_name: str = "") -> None:
        """Close the file browser dialog for control *cid*."""
        self._layout.close_file_chooser(cid)

    # ── Facade: theme ──────────────────────────────────────

    @property
    def theme(self) -> str:
        """The active theme id."""
        return self._theme_host.theme

    def set_theme(self, theme_id: str) -> None:
        """Switch to the theme with id *theme_id*."""
        self._theme_host.set_theme(theme_id)

    async def set_theme_async(self, theme_id: str) -> None:
        """Awaitable :meth:`set_theme`."""
        await self._theme_host.set_theme_async(theme_id)

    def refresh_theme(self) -> None:
        """Re-resolve and push the active theme."""
        self._theme_host.refresh_theme()

    async def refresh_theme_async(self) -> None:
        """Awaitable :meth:`refresh_theme`."""
        await self._theme_host.refresh_theme_async()

    def enable_theme_auto_reload(self, poll_interval: float = 1.0) -> None:
        """Watch the theme files and push updates when they change."""
        self._theme_host.enable_theme_auto_reload(poll_interval)

    def disable_theme_auto_reload(self) -> None:
        """Stop watching the theme files."""
        self._theme_host.disable_theme_auto_reload()

    # ── Facade: interaction ────────────────────────────────

    def on_interaction(
        self,
        object_id: str,
        event_type: Any,
        handler: Any,
        *,
        scene_name: str = "",
    ) -> None:
        """Register an async handler for interaction events on an entity."""
        self._interaction_host.on_interaction(
            object_id, event_type, handler, scene_name=scene_name
        )

    def set_interaction(
        self, object_id: str, config: Any, *, scene_name: str = ""
    ) -> None:
        """Set the interaction configuration for an entity."""
        self._interaction_host.set_interaction(object_id, config, scene_name=scene_name)

    # ── Internal forwarders (tests / VizSceneHandle) ───────

    @property
    def _theme(self) -> str:
        return self._theme_host._theme

    @property
    def _scenes(self) -> dict[str, Any]:
        return self._layout.scenes

    @property
    def _layouts(self) -> dict[str, Any]:
        return self._layout._layouts

    @property
    def _layouts_serialized(self) -> dict[str, dict[str, Any]]:
        return self._layout._layouts_serialized

    def _resolve_control(self, cid: str) -> Any:
        return self._layout.resolve_control(cid)

    def _scene_layout_for(self, scene_name: str) -> dict[str, Any] | None:
        return self._layout._scene_layout_for(scene_name)

    def _layout_serialized_for(self, layout_name: str) -> dict[str, Any] | None:
        return self._layout._layout_serialized_for(layout_name)

    async def _push_layout_updates(self) -> None:
        await self._layout._push_layout_updates()

    @property
    def _act_objects(self) -> dict[str, Any]:
        return self._interaction_host._act_objects

    async def _dispatch_interaction_event(
        self, msg_type: str, data: dict[str, Any]
    ) -> None:
        await self._interaction_host._dispatch_interaction_event(msg_type, data)

    @property
    def _server(self) -> Any:
        """The current :class:`VizServer` (or ``None`` pre-boot), backed by ServerState."""
        return self._server_state.server

    @_server.setter
    def _server(self, value: Any) -> None:
        self._server_state.server = value

    @property
    def _loop(self) -> Any:
        """The server event loop (or ``None`` pre-boot), backed by ServerState."""
        return self._server_state.loop

    @_loop.setter
    def _loop(self, value: Any) -> None:
        self._server_state.loop = value

    def _create_scene(self, name: str, space_dim: int | None = None) -> Scene:
        """Create a bare :class:`Scene` for *name* (no default objects).

        *space_dim* (2 or 3) overrides the visualizer default for a named
        scene; ``None`` inherits it.  The main scene (``""``) always uses the
        visualizer's own config.
        """
        if name == "":
            return Scene(
                self._config, name="", styles=self._global_styles.copy(), host=self
            )
        dim = self._config.space_dim if space_dim is None else _validate_space_dim(space_dim)
        cfg = SceneConfig(
            background_color=self._config.background_color,
            camera=None,
            title=name or self._config.title,
            name=name,
            space_dim=dim,
        )
        return Scene(cfg, name=name, styles=self._global_styles.copy(), host=self)

    def add_scene(
        self,
        name: str,
        *,
        space_dim: int | None = None,
        add_axes: bool = True,
        add_grid: bool = True,
    ) -> VizSceneHandle:
        """Create a scene + an auto single-``SceneView`` layout (raise if name taken)."""
        if space_dim is not None:
            _validate_space_dim(space_dim)
        self._layout.add_scene(name, space_dim)
        self._add_default_scene_objects(name, add_axes=add_axes, add_grid=add_grid)
        return VizSceneHandle(self, name)

    def scene(
        self,
        name: str,
        *,
        space_dim: int | None = None,
        enable_server_stop_key: bool = False,
        add_axes: bool = True,
        add_grid: bool = True,
    ) -> VizSceneHandle:
        """Get or create a named scene, returning a :class:`VizSceneHandle`.

        The handle exposes the full entity/control/animation API scoped to
        that scene.  Scenes inherit the visualizer's default styles.

        Names may contain slashes for grouping, e.g. ``"slides/intro"``.

        Args:
            name: Scene name (URL-path-friendly).
            space_dim: Space dimension for a newly created scene (``2`` or
                ``3``); ``None`` (default) inherits the visualizer's dimension.
                Applies only at creation.
            enable_server_stop_key: When ``True``, enable the
                browser-triggered full-server stop key (Ctrl+Q) for this
                scene, equivalent to calling
                ``viz.scene(name).enable_server_stop_key()`` afterward.
            add_axes: When ``False``, skip the default axes object for a
                newly created scene.  Applies only at creation; the main scene
                (``""``) is created in ``__init__`` and uses the
                ``add_default_axes`` constructor flag instead.
            add_grid: When ``False``, skip the default grid object for a
                newly created scene.  Applies only at creation; the main scene
                (``""``) is created in ``__init__`` and uses the
                ``add_default_grid`` constructor flag instead.
        """
        if name not in self._layout.scenes:
            if space_dim is not None:
                _validate_space_dim(space_dim)
            self._layout.add_scene(name, space_dim)
            self._add_default_scene_objects(name, add_axes=add_axes, add_grid=add_grid)
        if enable_server_stop_key:
            self._set_server_stop_key(
                name, enabled=True, key="q", modifiers=[KeyModifier.CTRL]
            )
        return VizSceneHandle(self, name)

    @property
    def scenes(self) -> dict[str, Scene]:
        """All scenes keyed by name (``""`` is the main scene)."""
        return self._layout.scenes

    @property
    def _scene(self) -> Scene:
        """The main scene (backward-compat property)."""
        return self._layout.scenes[""]

    @_scene.setter
    def _scene(self, value: Scene) -> None:
        self._layout.scenes[""] = value

    def list_scenes(self) -> list[str]:
        """Return all scene names (main scene is ``""``)."""
        return list(self._layout.scenes.keys())

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
        obj: Any = None,
        *,
        entity_id: str | None = None,
        color: str
        | tuple[float, float, float]
        | tuple[float, float, float, float]
        | None = None,
        opacity: float | None = None,
        style: ObjVizStyle | None = None,
        label: str | None = None,
        label_style: LabelStyle | None = None,
        tex_label: str | None = None,
        tex_label_style: "TextureLabelStyle | None" = None,
        parent_id: str | None = None,
        attach_to: str | None = None,
    ) -> str | None:
        """Add an entity to the main scene, or a :class:`View` to the overlay.

        A :class:`~pytanga.viz.views.View` argument (``GroupView`` / ``*View`` /
        ``MenuView`` / …) is mounted in the default layout's overlay; everything
        else (geometric entity, operator, multivector, label, or scene-graph
        group) goes to the main scene.  Returns the entity ID as a ``str`` for
        entities, or ``None`` for views.

        See the class docstring for full entity parameter documentation.
        """
        from .views import View

        if isinstance(obj, View):
            self._layout[""].overlay.add(obj)
            return None
        return self._layout.scenes[""].add_viz(
            obj=obj,
            entity_id=entity_id,
            color=color,
            opacity=opacity,
            style=style,
            label=label,
            label_style=label_style,
            tex_label=tex_label,
            tex_label_style=tex_label_style,
            parent_id=parent_id,
            attach_to=attach_to,
        )

    def new(
        self,
        obj: VizInputType | None = None,
        *,
        entity_id: str | None = None,
        color: str
        | tuple[float, float, float]
        | tuple[float, float, float, float]
        | None = None,
        opacity: float | None = None,
        style: ObjVizStyle | None = None,
        label: str | None = None,
        label_style: LabelStyle | None = None,
        tex_label: str | None = None,
        tex_label_style: "TextureLabelStyle | None" = None,
        parent_id: str | None = None,
        attach_to: str | None = None,
    ) -> "VizObjectRef":
        """Like :meth:`add`, but returns a :class:`VizObjectRef` instead of a ``str``."""
        from ._object_ref import VizObjectRef

        eid = self._layout.scenes[""].add_viz(
            obj=obj,
            entity_id=entity_id,
            color=color,
            opacity=opacity,
            style=style,
            label=label,
            label_style=label_style,
            tex_label=tex_label,
            tex_label_style=tex_label_style,
            parent_id=parent_id,
            attach_to=attach_to,
        )
        node = self._layout.scenes[""].get_node(eid)
        return VizObjectRef(VizSceneHandle(self, ""), node)

    def __call__(
        self, obj: VizInputType | None = None, **kwargs: Any
    ) -> "VizObjectRef":
        """Shorthand for :meth:`new`: ``viz(point, color=...)``.

        Adds *obj* to the main scene and returns a :class:`VizObjectRef`, just
        like :meth:`new`.  This keeps the pre-create + update animation pattern
        concise::

            p = viz(Point(3, 0, 0), color="#ff4444")
            for dt in viz.animate(fps=30):
                p.entity = Point(...)
                viz.flush()
        """
        return self.new(obj, **kwargs)

    def add_group(
        self, name: str | None = None, *, scene_name: str = ""
    ) -> "VizObjectRef":
        """Create a scene-graph group and return a :class:`VizObjectRef` for it."""
        from ._object_ref import VizObjectRef

        scene = self._layout.scenes[scene_name]
        group = scene.add_group(name)
        return VizObjectRef(VizSceneHandle(self, scene_name), group)

    def update(self, entity_id: str, **properties: Any) -> None:
        """Update rendering properties of an existing entity in the main scene.

        Accepted keyword arguments correspond to the style fields of the
        entity's kind — see :class:`~pytanga.viz.ObjVizStyle` and its
        per-entity subclasses.

        Common across all kinds:
            ``color`` (str), ``opacity`` (float), ``style`` (ObjVizStyle)

        Per-kind examples:
            Point/HPoint: ``size``
            Line: ``thickness``, ``length``
            PointPath: ``line_thickness``
            Sphere/Circle/Plane/Line: ``wireframe`` (bool)
        """
        self._layout.scenes[""].update(entity_id, **properties)

    def update_style(self, entity_id: str, style: ObjVizStyle) -> None:
        """Update rendering style of an existing entity from a style instance.

        Extracts only the explicitly set (non-``None``) fields from *style*
        and passes them as keyword properties to :meth:`update`.

        Example::

            viz.update_style(point_id, PointStyle(size=0.15, opacity=0.5))

        is equivalent to::

            viz.update(point_id, size=0.15, opacity=0.5)
        """
        from ._props import _extract_non_none

        props = _extract_non_none(style)
        self._layout.scenes[""].update(entity_id, **props)

    def update_entity(self, entity_id: str, obj: SceneEntity) -> None:
        """Replace the geometry for an existing entity in the main scene."""
        entity: SceneEntity = self._resolve(obj)
        self._layout.scenes[""].update_entity(entity_id, entity)

    def update_sdf_group_member(
        self,
        group_id: str,
        member: int | str,
        *,
        position: Vec3 = None,
        rotation: TransformRotation = None,
        scale: Triple = None,
    ) -> None:
        """Update an :class:`~pytanga.viz.sdf.SdfGroup` member's runtime transform.

        The member is addressed by *member* — either its 0-based index or its
        ``id``. Only the provided components are changed. Call :meth:`flush` to
        push the update (the member can then be animated frame-by-frame in an
        ``animate`` loop).
        """
        self._layout.scenes[""].update_sdf_group_member(
            group_id, member, position=position, rotation=rotation, scale=scale
        )

    def update_label(
        self,
        object_id: str,
        *,
        text: str | None = None,
        style: LabelStyle | None = None,
    ) -> None:
        """Update a label's text and/or style in the main scene."""
        self._layout.scenes[""].update_label(object_id, text=text, style=style)

    def get_label_ids(self, entity_id: str) -> list[str]:
        """Return the IDs of all labels attached to *entity_id* in the main scene."""
        return self._layout.scenes[""].get_label_ids(entity_id)

    def remove(self, entity_id: str) -> None:
        """Remove an entity from the main scene."""
        self._layout.scenes[""].remove(entity_id)

    def clear(self, *, add_axes: bool = False, add_grid: bool = False) -> None:
        """Remove all entities from the main scene.

        By default the scene is left empty.  Set ``add_axes`` / ``add_grid``
        to ``True`` to re-add the default coordinate axes / grid afterward
        (subject to the visualizer's ``add_default_axes`` / ``add_default_grid``
        constructor flags).
        """
        self._layout.scenes[""].clear()
        if add_axes or add_grid:
            self._default_objects_added.discard("")
            self._add_default_scene_objects("", add_axes=add_axes, add_grid=add_grid)

    def _reset_scene(self, scene_name: str) -> None:
        """Clear a scene and re-add its default axes/grid.

        Used by the context managers so ``with viz:`` / ``with viz.scene(name):``
        reset to the default scene (axes/grid present), not an empty one.
        """
        self._layout.scenes[scene_name].clear()
        self._default_objects_added.discard(scene_name)
        self._add_default_scene_objects(scene_name)

    # ── Title & annotation ──────────────────────────────────

    def set_title(self, title: str) -> None:
        """Update the viewport title overlay for the main scene."""
        self._set_scene_title("", title)

    def _set_scene_title(self, scene_name: str, title: str) -> None:
        scene = self._layout.scenes[scene_name]
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
        scene = self._layout.scenes[scene_name]
        scene.config.annotation = text

        if text is None or text == "":
            scene.remove("__annotation__")
        else:
            style_dict = _resolve_annotation_style(scene.styles.annotation, style)
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
        data = json.dumps(self._layout.scenes[scene_name].config.to_dict())
        asyncio.run_coroutine_threadsafe(self._server.push_raw(data), self._loop)

    def set_camera(
        self,
        camera: CameraConfig | View2DConfig | View3dConfig,
        *,
        scene_name: str = "",
    ) -> None:
        """Update the camera configuration for a scene at runtime.

        Args:
            camera: A :class:`CameraConfig`, or a :class:`View2DConfig` /
                :class:`View3dConfig` input spec.
            scene_name: Target scene (default ``""`` = main scene).
        """
        scene = self._layout.scenes[scene_name]
        scene.config.camera = _normalize_camera_config(camera)
        self._push_scene_config(scene_name)

    def set_space_dim(
        self,
        space_dim: int,
        *,
        scene_name: str = "",
        camera: CameraConfig | View2DConfig | View3dConfig | None = None,
    ) -> None:
        """Switch a scene's space dimension (2D/3D) at runtime.

        Updates the scene's ``space_dim`` and re-pushes its config so the
        browser switches camera mode and controls without a reload.

        Args:
            space_dim: ``2`` or ``3``.
            scene_name: Target scene (default ``""`` = main scene).
            camera: Optional camera to apply with the new dimension.  When
                omitted and the scene's current camera conflicts with
                ``space_dim``, the camera is cleared so the frontend auto-fits
                with the correct camera type.
        """
        _validate_space_dim(space_dim)
        scene = self._layout.scenes[scene_name]
        scene.config.space_dim = space_dim
        if camera is not None:
            cam = _normalize_camera_config(camera)
            cam_dim = _deduce_space_dim(cam)
            if cam_dim is not None and cam_dim != space_dim:
                raise ValueError(
                    f"camera implies space_dim={cam_dim}, but {space_dim} was requested"
                )
            scene.config.camera = cam
        else:
            cam_dim = _deduce_space_dim(scene.config.camera)
            if cam_dim is not None and cam_dim != space_dim:
                scene.config.camera = None
        self._push_scene_config(scene_name)

    def set_view_camera(
        self,
        view: SceneView,
        camera: CameraConfig | View2DConfig | View3dConfig,
    ) -> None:
        """Update the camera of a single pane (:class:`SceneView`) at runtime.

        Unlike :meth:`set_camera` (which changes a scene for **every** pane
        showing it), this targets one specific pane, identified by the
        ``SceneView`` instance.  The pane keeps its own orbit/zoom; this only
        moves the camera to the requested configuration.

        Args:
            view: The :class:`SceneView` pane to update.  It must be part of a
                registered layout (see :meth:`set_layout`).
            camera: A :class:`CameraConfig`, or a :class:`View2DConfig` /
                :class:`View3dConfig` input spec.
        """
        if not isinstance(view, SceneView):
            raise TypeError(f"view must be a SceneView, got {type(view).__name__}")
        view.camera = _normalize_camera_config(camera)
        if view.camera is None:
            return
        data = json.dumps(
            {
                "type": "view_camera",
                "view_id": view.id,
                "camera": view.camera.to_dict(),
            }
        )
        if self._server is None or self._loop is None:
            return
        asyncio.run_coroutine_threadsafe(self._server.push_raw(data), self._loop)

    def _add_default_scene_objects(
        self,
        scene_name: str,
        *,
        add_axes: bool | None = None,
        add_grid: bool | None = None,
    ) -> None:
        """Add default axes and/or grid, controlled by constructor flags.

        Each object is added independently based on ``_add_default_axes`` and
        ``_add_default_grid``.  ``add_axes`` / ``add_grid`` optionally override
        those flags for this call (ANDed with the constructor flags); ``None``
        means "use the constructor flag as-is".  Idempotent per scene (runs
        only once).  Runs eagerly at construction and when a named scene is
        created, so exports that read the scene directly (without starting the
        server) also see the defaults.
        """
        if scene_name in self._default_objects_added:
            return
        scene = self._layout.scenes[scene_name]

        want_axes = (
            self._add_default_axes
            if add_axes is None
            else (add_axes and self._add_default_axes)
        )
        want_grid = (
            self._add_default_grid
            if add_grid is None
            else (add_grid and self._add_default_grid)
        )

        from ._scene_objects import Axes2D, Axes3D, Grid
        from ._styles import Axes3DStyle, AxisStyle

        if scene.config.space_dim == 2:
            if want_axes:
                axes: Axes2D | Axes3D = Axes2D(range_u=(-5.0, 5.0), range_v=(-5.0, 5.0))
                self._layout.scenes[scene_name].add_viz(obj=axes)
            if want_grid:
                grid = Grid(range_u=(-5.0, 5.0), range_v=(-5.0, 5.0))
                self._layout.scenes[scene_name].add_viz(obj=grid)
        else:
            if want_axes:
                axes = Axes3D(
                    range_u=(0.0, 5.0),
                    range_v=(0.0, 5.0),
                    range_w=(0.0, 5.0),
                    show_value_labels=False,
                )
                self._layout.scenes[scene_name].add_viz(
                    obj=axes,
                    style=Axes3DStyle(
                        u=AxisStyle(color="#ff0000"),
                        v=AxisStyle(color="green"),
                        w=AxisStyle(color="blue"),
                    ),
                )
            if want_grid:
                grid = Grid(
                    origin=(0.0, 0.0, 0.0),
                    dir_u=(1.0, 0.0, 0.0),
                    dir_v=(0.0, 0.0, 1.0),
                    range_u=(-5.0, 5.0),
                    range_v=(-5.0, 5.0),
                )
                self._layout.scenes[scene_name].add_viz(obj=grid)

        self._default_objects_added.add(scene_name)

    def _full_state_for(
        self, scene_name: str
    ) -> tuple[list[dict[str, Any]], list[str]]:
        """Return full serialized state for a scene, adding defaults first."""
        self._add_default_scene_objects(scene_name)
        scene = self._layout.scenes.get(scene_name, self._layout.scenes[""])
        state = scene.full_state(styles_map=scene.styles.kind)
        # The full state is the authoritative snapshot the frontend just
        # received; consume the dirty flags so the next flush() doesn't re-send
        # the whole scene (which would force a rebuild and orphan CSS2D labels).
        scene.clear_dirty()
        return state, []

    def _interrupt_event(self, scene_name: str = "") -> threading.Event:
        """Return (creating if needed) the interrupt :class:`threading.Event`
        for *scene_name* (``""`` = main scene)."""
        if scene_name not in self._interrupt_events:
            self._interrupt_events[scene_name] = threading.Event()
        return self._interrupt_events[scene_name]

    def _clear_interrupt(self, scene_name: str = "") -> None:
        """Clear a previous per-scene interrupt for *scene_name*.

        Called at the start of a new :meth:`animate` loop so that re-running
        an animation after a browser ``q`` stop starts cleanly.  The global
        shutdown event (terminal Ctrl+C/SIGTERM) is intentionally left
        untouched so a terminal interrupt still ends every loop.
        """
        event = self._interrupt_events.get(scene_name)
        if event is not None:
            event.clear()

    def _normalize_stop_modifiers(
        self, stop_modifiers: Sequence[KeyModifier | str] | None
    ) -> list[KeyModifier]:
        """Normalize a stop-modifier sequence into ``KeyModifier`` members.

        Accepts ``KeyModifier`` members or raw strings matching a member value
        (e.g. ``"ctrl"``).  Unknown values raise :class:`ValueError`.
        """
        if not stop_modifiers:
            return []
        normalized: list[KeyModifier] = []
        for mod in stop_modifiers:
            if isinstance(mod, KeyModifier):
                normalized.append(mod)
                continue
            try:
                normalized.append(KeyModifier(str(mod).lower()))
            except ValueError:
                raise ValueError(
                    f"Unknown key modifier {mod!r}; expected one of "
                    f"{[m.value for m in KeyModifier]}"
                ) from None
        return normalized

    def _register_animation_stop(
        self,
        scene_name: str,
        stop_key: str | None,
        stop_modifiers: Sequence[KeyModifier | str] | None,
    ) -> None:
        """Normalize, store, and push an animation-stop binding for a scene.

        ``stop_key=None`` disables the browser binding for that scene.
        """
        modifiers = self._normalize_stop_modifiers(stop_modifiers)
        enabled = stop_key is not None
        config: dict[str, Any] = {
            "enabled": enabled,
            "key": stop_key if enabled else None,
            "modifiers": [m.value for m in modifiers],
        }
        self._scene_interrupt_configs[scene_name] = config
        self._push_animation_stop(scene_name)

    def enable_server_stop_key(
        self,
        enabled: bool = True,
        key: str = "q",
        modifiers: list[KeyModifier] = [KeyModifier.CTRL],
    ) -> None:
        """Enable or disable the browser-triggered full-server stop key.

        Configures the binding for the **main scene**.  When pressed in that
        scene's browser tab, it sets the global shutdown event so
        :meth:`wait` returns and every running :meth:`animate` loop ends —
        mirroring a terminal Ctrl+C / SIGTERM.  Server teardown still happens
        via :meth:`wait` / the ``atexit`` hook; the key only requests shutdown.

        Args:
            enabled: ``True`` activates the binding, ``False`` disables it.
            key: The key to match (case-insensitive), default ``"q"``.
            modifiers: Modifiers that must be held, default ``[KeyModifier.CTRL]``
                (i.e. Ctrl+Q).
        """
        self._set_server_stop_key("", enabled=enabled, key=key, modifiers=modifiers)

    def _set_server_stop_key(
        self,
        scene_name: str,
        *,
        enabled: bool,
        key: str,
        modifiers: list[KeyModifier],
    ) -> None:
        normalized = self._normalize_stop_modifiers(modifiers)
        self._server_stop_configs[scene_name] = {
            "enabled": enabled,
            "key": key if enabled else None,
            "modifiers": [m.value for m in normalized],
        }
        self._push_animation_stop(scene_name)

    def _push_animation_stop(self, scene_name: str = "") -> None:
        """Push the stored animation-stop config to the frontend (thread-safe)."""
        if self._server is None or self._loop is None:
            return
        asyncio.run_coroutine_threadsafe(
            self._push_animation_stop_async(scene_name), self._loop
        )

    async def _push_animation_stop_async(self, scene_name: str = "") -> None:
        """Async variant — must be called from the server's event loop."""
        if self._server is None:
            return
        config = self._scene_interrupt_configs.get(
            scene_name, {"enabled": False, "key": None, "modifiers": []}
        )
        server_config = self._server_stop_configs.get(
            scene_name, {"enabled": False, "key": None, "modifiers": []}
        )
        message: dict[str, Any] = {
            "type": "animation_stop_config",
            "scene": scene_name,
        }
        message.update(config)
        message["server_enabled"] = server_config["enabled"]
        message["server_key"] = server_config["key"]
        message["server_modifiers"] = server_config["modifiers"]
        await self._server.push_raw(json.dumps(message))

    async def _on_browser_animation_stop(
        self, scene_name: str, scope: str = "scene"
    ) -> None:
        """Handle an ``animation_stop`` message from the browser.

        With ``scope="scene"`` (the default) only the requested scene's
        interrupt event is set.  With ``scope="server"`` the global shutdown
        event is set (and every per-scene interrupt event), so :meth:`wait`
        returns and all :meth:`animate` loops end — mirroring a terminal
        Ctrl+C / SIGTERM.  Never tears the server down here: teardown is the
        job of :meth:`wait` / the ``atexit`` hook.
        """
        if scope == "server":
            logger.info("Browser requested full server stop (scene %r)", scene_name)
            shutdown = getattr(self, "_shutdown_requested", None)
            if shutdown is not None:
                shutdown.set()
            for event in self._interrupt_events.values():
                event.set()
            return
        logger.info("Browser requested animation stop for scene %r", scene_name)
        self._interrupt_event(scene_name).set()

    def sleep_ms(self, milliseconds: int, scene_name: str = "") -> bool:
        """Sleep for *milliseconds*, returning early if interrupted.

        Returns ``True`` if the full interval elapsed, or ``False`` if an
        interrupt (terminal Ctrl+C/SIGTERM, or the scene's browser stop key)
        arrived before it finished — the caller should then stop animating.

        Blocks on the scene's interrupt event with a timeout (no busy-wait).
        If the server hasn't been started (no signal handler installed), it
        sleeps the full interval and returns ``True``.
        """
        if self.interrupted(scene_name):
            return False
        shutdown = getattr(self, "_shutdown_requested", None)
        if shutdown is None:
            time.sleep(milliseconds / 1000)
            return True
        # Wait in short windows so both the global and the scene event are
        # observed without busy-spinning.
        scene_event = self._interrupt_event(scene_name)
        deadline = time.monotonic() + milliseconds / 1000
        while not self.interrupted(scene_name):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return True
            scene_event.wait(timeout=min(remaining, 0.05))
        return False

    def interrupted(self, scene_name: str = "") -> bool:
        """True once an interrupt for *scene_name* has been requested.

        An interrupt is requested either by terminal Ctrl+C / SIGTERM (global,
        applies to every scene) or by the scene's browser stop key (scoped to
        just this scene).

        Requires :meth:`start_server` (or :meth:`show` / :meth:`animate`) to
        have been called so the signal handler is installed.
        """
        shutdown = getattr(self, "_shutdown_requested", None)
        if shutdown is not None and shutdown.is_set():
            return True
        return self._interrupt_event(scene_name).is_set()

    def animate(
        self,
        *,
        fps: float = 60.0,
        stop_key: str | None = "q",
        stop_modifiers: Sequence[KeyModifier | str] | None = None,
        scene_name: str = "",
        auto_clear: bool = False,
    ) -> Iterator[float]:
        """Yield once per animation frame until interrupted.

        Each iteration yields the elapsed wall-clock time in seconds since the
        previous frame (``0.0`` on the first frame).  When *fps* is positive the
        generator sleeps between frames to hold that frame rate; pass ``fps=0``
        to disable pacing and call :meth:`sleep_ms` from inside the loop body
        instead.

        The loop stops when an interrupt for *scene_name* is requested: either
        terminal Ctrl+C / SIGTERM (global) or the scene's browser stop key.
        *stop_key* (default ``"q"``) with optional *stop_modifiers*
        (``KeyModifier`` values) configures that browser binding per scene;
        pass ``stop_key=None`` to disable it.  Starting a loop clears any
        earlier per-scene interrupt for *scene_name*, so a cell that ended via
        the browser stop key can be re-run to restart the animation.

        The server is started automatically (headless) if it isn't already
        running, and is stopped automatically at interpreter exit via the
        registered ``atexit`` hook (so a per-scene ``q`` interrupt does not
        shut the server down).  ``animate`` never makes the viewer visible —
        call :meth:`show` first (or use ``with viz:``) to open it, then drive
        the loop.

        When *auto_clear* is ``True``, each frame first flushes the scene (so the
        previous frame's changes appear), then removes every object that was
        added after the loop began — i.e. anything not present on the first
        frame.  This lets you ``add()`` fresh objects every frame without
        accumulating them::

            for dt in viz.animate(fps=30, auto_clear=True):
                viz.add(Point(math.cos(t), math.sin(t), 0), color="#ff4444")
                viz.flush()

        Objects added *before* the loop persist across frames.

        Example::

            viz = Visualizer(title="...")
            viz.show()  # make the viewer visible (inline in Jupyter)
            for dt in viz.animate(fps=60):
                ...  # update transforms / entities each frame
                viz.flush()
        """
        if self._server is None:
            self.start_server()

        # Start each loop with a clean per-scene interrupt so re-running the
        # animation after a browser "q" stop restarts instead of immediately
        # ending.  (The global Ctrl+C/SIGTERM event is left untouched.)
        self._clear_interrupt(scene_name)

        self._register_animation_stop(scene_name, stop_key, stop_modifiers)

        frame_time = 1.0 / fps if fps and fps > 0.0 else None

        baseline: set[str] | None = None
        prev = time.monotonic()
        while not self.interrupted(scene_name):
            if auto_clear:
                # Flush synchronously first so the previous frame's additions
                # are actually pushed to the browser *before* we mark them for
                # removal.  (A fire-and-forget flush races with the synchronous
                # remove() below: the flush can observe the object already
                # pending removal and send "remove" without ever sending "add",
                # so the object never appears.)
                self._flush_scene(scene_name, wait=True)
                scene = self._layout.scenes[scene_name]
                current = set(scene._objects.keys())
                if baseline is None:
                    baseline = current
                else:
                    for object_id in current - baseline:
                        scene.remove(object_id)

            now = time.monotonic()
            yield now - prev
            prev = now
            if frame_time is not None:
                remaining = frame_time - (time.monotonic() - now)
                if remaining > 0.0:
                    time.sleep(remaining)

    # ── Default style configuration ─────────────────────────

    def set_default_color(
        self,
        kind: str,
        color: str | tuple[float, float, float] | tuple[float, float, float, float],
    ) -> None:
        """Set the default color (and optionally opacity) for an entity kind.

        Targets the main scene's style defaults (``viz.styles``).
        """
        normalized = _normalize_color(color)
        key = _kind_to_key(kind)
        if key not in self.styles.kind:
            raise ValueError(f"Unknown entity kind: {kind!r}")

        if isinstance(normalized, tuple):
            self.styles.kind[key].color = normalized[0]
            self.styles.kind[key].opacity = normalized[1]
        else:
            self.styles.kind[key].color = normalized

    # ── MV resolution ──────────────────────────────────────

    def _resolve(self, obj: Any) -> SceneEntity:
        """Resolve an MV to a :class:`SceneEntity` (delegated to Scene)."""
        from .scene import _resolve_scene_entity

        return _resolve_scene_entity(obj)

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

    def start_server(self, host: str = "localhost", port: int | None = None) -> None:
        """Start serving the visualization without opening a browser.

        Parameters
        ----------
        host : str
            Bind host (default ``"localhost"``).
        port : int | None
            Port to serve on.  ``None`` (default) uses the standard Tanga
            viewer port (8765) so an already-open browser tab can reconnect
            across server restarts.  ``0`` auto-picks a free port; a positive
            integer uses that exact port.
        """
        if port is None:
            port = DEFAULT_PORT
        elif port == 0:
            port = _find_free_port(host)
        elif port < 0:
            raise ValueError(f"port must be 0 or a positive integer, got {port}")
        self._host = host
        self._port = port
        from .server import PortInUseError

        try:
            self._ensure_server_running()
        except PortInUseError as e:
            raise SystemExit(str(e))

    def _ensure_server_running(self) -> None:
        """Boot the server in a background thread if not already running."""
        if self._server is not None:
            return

        from ._themes import external_theme_dirs
        from .server import VizServer

        logger.info("Starting VizServer on %s:%d", self._host, self._port)
        self._server = VizServer(host=self._host, port=self._port)

        _boot_done = threading.Event()
        _boot_start = time.monotonic()

        async def _boot() -> None:
            await self._server.start(
                self._full_state_for,
                self._config.to_dict,
                control_callback=self._transport.dispatch,
                interaction_callback=self._transport.dispatch,
                on_connect=self._on_client_connect,
                on_disconnect=self._on_client_disconnect,
                animation_stop_callback=self._on_browser_animation_stop,
                push_animation_stop=self._push_animation_stop_async,
                scene_config_callback=self._scene_config_for,
                scene_list_callback=self.list_scenes,
                layout_callback=self._layout._layout_serialized_for,
                scene_layout_callback=self._layout._scene_layout_for,
                theme_callback=self._theme_host._theme_define_payload,
                theme_static_dirs=external_theme_dirs(),
            )
            _boot_done.set()

        self._loop = asyncio.new_event_loop()

        boot_task = self._loop.create_task(_boot())

        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()

        deadline = time.monotonic() + 5.0
        while not _boot_done.is_set():
            if boot_task.done():
                error = boot_task.exception()
                if error is not None:
                    self._cleanup_failed_boot()
                    raise error
            if time.monotonic() >= deadline:
                break
            time.sleep(0.01)

        if not _boot_done.is_set():
            self._cleanup_failed_boot()
            raise RuntimeError("Server failed to start within 5s")

        logger.debug("Server booted in %.1fs", time.monotonic() - _boot_start)

        # Graceful shutdown on interpreter exit, even if the script forgets to
        # call stop_server() — otherwise the daemon server thread is killed
        # abruptly and browsers see an abnormal 1006 reset instead of a clean
        # 1001 close.
        if not self._atexit_registered:
            import atexit

            def _atexit_stop() -> None:
                try:
                    self.stop_server(timeout=2.0)
                except Exception:
                    pass

            atexit.register(_atexit_stop)
            self._atexit_registered = True

        # Threading.Event for Ctrl+C — signal handler sets it, poll loop checks it.
        # Avoids asyncio/signal clashes on Windows.
        self._shutdown_requested = threading.Event()

        def _on_sigint(signum: int, frame: object) -> None:
            logger.info("Ctrl+C received - requesting shutdown")
            self._shutdown_requested.set()
            for event in self._interrupt_events.values():
                event.set()

        self._saved_signal_handlers = {
            signal.SIGINT: signal.getsignal(signal.SIGINT),
            signal.SIGTERM: signal.getsignal(signal.SIGTERM),
        }
        signal.signal(signal.SIGINT, _on_sigint)
        signal.signal(signal.SIGTERM, _on_sigint)

        # Print URLs
        self._print_startup_urls()

    def _cleanup_failed_boot(self) -> None:
        """Tear down a server whose boot task failed before it fully started."""
        if self._loop is not None and self._loop.is_running():
            if self._server is not None:

                async def _cleanup() -> None:
                    try:
                        await self._server.stop()
                    except Exception:
                        pass

                try:
                    asyncio.run_coroutine_threadsafe(_cleanup(), self._loop).result(
                        timeout=5.0
                    )
                except Exception:
                    pass
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread is not None:
            self._thread.join(timeout=3.0)
        self._server = None
        self._loop = None
        self._thread = None

    def _restore_signal_handlers(self) -> None:
        """Restore the SIGINT/SIGTERM handlers saved before the server started."""
        if self._saved_signal_handlers is None:
            return
        for signum, handler in self._saved_signal_handlers.items():
            try:
                signal.signal(signum, handler)
            except Exception:
                pass
        self._saved_signal_handlers = None

    def open_browser(
        self, *, wait_for_browser: bool | None = None, timeout: float | None = None
    ) -> bool:
        """Open/reconnect a browser tab for the main scene."""
        return self._open_scene_browser(
            "", wait_for_browser=wait_for_browser, timeout=timeout
        )

    def _open_scene_browser(
        self,
        scene_name: str,
        *,
        wait_for_browser: bool | None = None,
        timeout: float | None = None,
    ) -> bool:
        """Open/reconnect a browser tab for *scene_name* (``""`` for main)."""
        import secrets

        if self._server is None:
            raise RuntimeError("Server not started. Call start_server() first.")

        page_token = secrets.token_hex(4)  # 8 hex chars
        url_path = f"/{scene_name}" if scene_name else "/"
        token_url = f"{url_path}?token={page_token}"
        return self._open_browser_url(
            token_url, wait_for_browser=wait_for_browser, timeout=timeout
        )

    def _open_layout_browser(
        self,
        layout_name: str,
        *,
        wait_for_browser: bool | None = None,
        timeout: float | None = None,
    ) -> bool:
        """Open/reconnect a browser tab for the split-view layout *layout_name*."""
        import secrets

        if self._server is None:
            raise RuntimeError("Server not started. Call start_server() first.")

        page_token = secrets.token_hex(4)
        token_url = f"/?view={layout_name}&token={page_token}"
        return self._open_browser_url(
            token_url, wait_for_browser=wait_for_browser, timeout=timeout
        )

    def _open_browser_url(
        self,
        token_url: str,
        *,
        wait_for_browser: bool | None,
        timeout: float | None = None,
    ) -> bool:
        """Open *token_url* in a (possibly reused) browser tab."""
        if wait_for_browser is None:
            wait_for_browser = not self._jupyter

        if self._reuse_existing:
            # Interactive wait: user either clicks Reconnect or presses Enter
            if wait_for_browser:
                connected = self.wait_for_browser(
                    timeout=timeout if timeout is not None else 120.0,
                    path=token_url,
                )
                if not connected:
                    return False
            else:
                # wait_for_browser is False (e.g. Jupyter): just check if
                # one is already there, otherwise open tab and don't wait.
                fut = asyncio.run_coroutine_threadsafe(
                    self._server.wait_for_ws_ready(timeout=3.0), self._loop
                )
                try:
                    reconnected = fut.result(timeout=3.5)
                except (
                    concurrent.futures.TimeoutError,
                    asyncio.TimeoutError,
                ):
                    reconnected = False
                if not reconnected:
                    if self._loop is not None:
                        self._loop.call_soon_threadsafe(
                            self._server._clear_ws_ready_events
                        )
                    self._server.open_browser(token_url)
        else:
            # reuse_existing disabled — always open new tab
            if self._loop is not None:
                self._loop.call_soon_threadsafe(self._server._clear_ws_ready_events)
            self._server.open_browser(token_url)
            if wait_for_browser:
                return self.wait_for_browser(
                    timeout=timeout if timeout is not None else 30.0
                )
        return True

    def start(
        self, *, wait_for_browser: bool | None = None, timeout: float = 30.0
    ) -> bool:
        """Deprecated: use :meth:`show` (or :meth:`start_server` + :meth:`open_browser`).

        Preserved for backward compatibility — starts the server on the
        configured ``host``/``port`` and opens a browser (unless
        ``open_browser=False``).
        """
        warnings.warn(
            "start() is deprecated; use show() or start_server()",
            DeprecationWarning,
            stacklevel=2,
        )
        self.start_server(host=self._host, port=self._port)
        if self._open_browser:
            return self.open_browser(wait_for_browser=wait_for_browser)
        return True

    def _print_startup_urls(self) -> None:
        """Print the HTTP URL for the viewer."""
        http_url = f"http://{self._host}:{self._port}"
        try:
            from rich.console import Console
            from rich.text import Text

            Console().print(Text(http_url, style="bold cyan"))
        except Exception:
            print(http_url)

    def _print_connect_prompt(self, path: str | None = None) -> None:
        """Print the interactive connect prompt including the server URL.

        The URL is printed on its own line so terminals (e.g. VS Code) can
        detect it as a clickable link.
        """
        url = self.url if path is None else f"{self.url}{path}"
        try:
            from rich.console import Console
            from rich.text import Text

            Console().print(
                Text.assemble(
                    "Server: ",
                    Text(url, style="bold cyan"),
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
                f"Server: {url}\n"
                "Press Enter to open a new browser tab, "
                "or click 'Reconnect' in an existing tab..."
            )

    def _scene_config_for(self, scene_name: str) -> dict[str, Any] | None:
        """Callback: return config dict for a named scene, or None if not found."""
        scene = self._layout.scenes.get(scene_name)
        if scene is None:
            return None
        return scene.config.to_dict()

    async def wait_for_shutdown(self, poll_interval: float = 0.25) -> None:
        """Asyncio-friendly wait until shutdown is requested (e.g. Ctrl+C).

        Polls ``self._shutdown_requested`` so it works on Windows where
        ``loop.add_signal_handler`` is not available.
        """
        while not self._shutdown_requested.is_set():
            await asyncio.sleep(poll_interval)

    def stop_server(self, *, timeout: float = 5.0) -> None:
        """Stop the server and clean up."""
        self._restore_signal_handlers()
        if self._server is None:
            logger.debug("stop_server() called but server already None")
            return

        logger.info("Shutting down server...")

        async def _stop() -> None:
            # Gracefully close WebSocket connections FIRST, so browsers receive
            # a clean close frame (1001) instead of an abnormal 1006 reset.
            # Cancelling the handler tasks before this would let their finally
            # blocks discard the sockets from _ws_clients before the close
            # frame can be sent.
            await self._server.stop()

            # Cancel remaining tasks (heartbeats, handlers) that may still be
            # pending.  Don't do t.cancel() in a loop — it can recurse on child tasks.
            tasks = [
                t
                for t in asyncio.all_tasks(self._loop)
                if not t.done() and t is not asyncio.current_task(self._loop)
            ]
            if tasks:
                for t in tasks:
                    t.cancel("server shutting down")
                await asyncio.gather(*tasks, return_exceptions=True)

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
        logger.debug("Server stopped")

    def stop(self, *, timeout: float = 5.0) -> None:
        """Deprecated: use :meth:`stop_server`."""
        warnings.warn(
            "stop() is deprecated; use stop_server()",
            DeprecationWarning,
            stacklevel=2,
        )
        self.stop_server(timeout=timeout)

    def wait_for_browser(self, timeout: float = 120.0, path: str | None = None) -> bool:
        """Block until a browser connects, or the user opens one interactively.

        Prints a prompt and waits for EITHER:
          - An existing browser to reconnect, OR
          - The user to press Enter (opens a new tab with a fresh token).

        Returns True if a browser connected, False if cancelled by user
        (Ctrl+C) or on timeout after opening a tab.

        Ctrl+C is responsive throughout.
        """
        import secrets

        if self._server is None or self._loop is None:
            raise RuntimeError("Server not started. Call start() first.")

        # ── Check if already connected ──
        if self._server._any_ws_ready_thread.is_set():
            logger.info("Browser already connected")
            return True

        # ── Print interactive prompt ──
        self._print_connect_prompt(path=path)

        # ── Threading.Event for Enter press ──
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

        # ── Poll loop ──
        start_ts = time.monotonic()
        poll_interval = 0.2

        while True:
            if self._server._any_ws_ready_thread.is_set():
                elapsed = time.monotonic() - start_ts
                logger.info("Browser reconnected after %.1fs", elapsed)
                return True
            if enter_pressed.is_set():
                logger.info("User pressed Enter - opening new tab")
                break
            if shutdown.is_set():
                logger.info("Shutdown requested during wait")
                return False
            time.sleep(poll_interval)

        # ── User chose to open a new tab ──
        page_token = secrets.token_hex(4)  # 8 hex chars
        logger.info("Opening new tab with token=%s", page_token)

        # Thread-safe clear of ready events
        if self._loop is not None:
            self._loop.call_soon_threadsafe(self._server._clear_ws_ready_events)

        self._server.open_browser(path or f"/?token={page_token}")

        # Now wait for the new tab to connect
        logger.info(
            "Waiting up to %.0fs for new tab to connect at %s ...",
            timeout,
            self.url,
        )
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self._server._any_ws_ready_thread.is_set():
                elapsed = time.monotonic() - start_ts
                logger.info("New tab connected after %.1fs", elapsed)
                return True
            if shutdown.is_set():
                logger.info("Shutdown requested during tab wait")
                return False
            time.sleep(poll_interval)

        logger.warning("No browser connected within %.0fs after opening tab", timeout)
        self._print_ws_timeout_note()
        return False

    def _print_ws_timeout_note(self) -> None:
        """Print a note about WebSocket reachability when browser didn't connect."""
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

    def _print_disconnect(self, remote_addr: str) -> None:
        try:
            from rich.console import Console
            from rich.text import Text

            Console().print(
                Text(f"Browser disconnected  ({remote_addr}).", style="bold yellow")
            )
        except Exception:
            print(f"Browser disconnected ({remote_addr}).")

    async def _flush_scene_async(
        self, scene_name: str, *, fit_camera: bool = False
    ) -> None:
        """Push dirty state for a specific scene (must be called from server's event loop)."""
        if self._server is None:
            return
        scene = self._layout.scenes.get(scene_name)
        if scene is None:
            return
        patches, removed = scene.flush()
        if patches or removed or fit_camera:
            from .serializer import serialize_object_update

            message = serialize_object_update(patches, removed)
            message["scene"] = scene_name
            if fit_camera:
                message["fit_camera"] = True
            await self._server.push_raw(json.dumps(message))

    async def _flush_all_async(self, *, fit_camera: bool = False) -> None:
        """Push dirty state for every scene (must be called from the server's event loop)."""
        if self._server is None:
            return
        for name in self._layout.scenes:
            await self._flush_scene_async(name, fit_camera=fit_camera)

    def _flush_scene(
        self, scene_name: str, *, fit_camera: bool = False, wait: bool = False
    ) -> None:
        """Schedule a scene update on the server's event loop (thread-safe).

        When *wait* is ``True``, block until the flush has been processed so the
        caller can rely on the pushed state before making further changes (e.g.
        ``auto_clear`` flushes before removing objects).  This blocking wait is
        only safe from a thread other than the server's event-loop thread; if it
        is called from within that loop (e.g. an async control handler) it would
        deadlock, so a :class:`RuntimeError` is raised and the caller should
        ``await flush_async()`` instead.
        """
        if self._loop is None or self._server is None:
            return
        if wait:
            try:
                on_server_loop = asyncio.get_running_loop() is self._loop
            except RuntimeError:
                on_server_loop = False
            if on_server_loop:
                raise RuntimeError(
                    "flush(wait=True) cannot block on the server's own event "
                    "loop; await flush_async() instead (e.g. from a control "
                    "handler)."
                )
        fut = asyncio.run_coroutine_threadsafe(
            self._flush_scene_async(scene_name, fit_camera=fit_camera), self._loop
        )
        if wait:
            fut.result(timeout=10.0)

    def flush(self, *, fit_camera: bool = False, wait: bool = False) -> None:
        """Schedule all dirty scenes to be pushed to the server (thread-safe).

        If *fit_camera* is ``True``, the frontend will auto‑adjust the
        camera to encompass all entities after the flush.

        If *wait* is ``True``, block until the flush has been processed.  This
        is intended for plain synchronous scripts (their main thread is not the
        server's event-loop thread).  It must **not** be called from an async
        control/interaction handler — those run on the server loop itself and
        would deadlock; use :meth:`flush_async` there instead.
        """
        if self._loop is not None and self._server is not None:
            for name in self._layout.scenes:
                self._flush_scene(name, fit_camera=fit_camera, wait=wait)

    async def _on_server_loop(self, coro_factory: Any) -> Any:
        """Await ``coro_factory()`` on the server's event loop, from any loop.

        When already running on ``self._loop`` the coroutine executes inline;
        otherwise it is scheduled onto the loop via
        ``run_coroutine_threadsafe`` and awaited with ``wrap_future``
        (non-blocking — the caller's loop keeps running).
        """
        if self._loop is None or self._server is None:
            return None
        if asyncio.get_running_loop() is self._loop:
            return await coro_factory()
        fut = asyncio.run_coroutine_threadsafe(coro_factory(), self._loop)
        return await asyncio.wrap_future(fut)

    async def flush_async(
        self, *, fit_camera: bool = False, scene: str | None = None
    ) -> None:
        """Awaitable flush that completes once pending updates have been sent.

        Unlike :meth:`flush`, which schedules the push and returns immediately,
        this coroutine waits for the WebSocket write to finish.  Use it from an
        async control handler to guarantee a change is rendered *before* the
        handler blocks the event loop with a long synchronous computation::

            async def on_change(self, value, event):
                self.viz.set_annotation("Calculating...")
                await self.viz.flush_async()   # annotation is now on screen
                result = expensive_sync_work(value)

        Safe from any running event loop: when awaited on the server's own loop
        (control/interaction handlers) the flush runs inline; otherwise it is
        scheduled onto the server loop and awaited without blocking the caller.

        Args:
            fit_camera: Forward the camera auto‑fit flag to the frontend.
            scene: Name of a single scene to flush, or ``None`` (default) to
                flush all scenes.
        """

        async def _run() -> None:
            if scene is None:
                await self._flush_all_async(fit_camera=fit_camera)
            else:
                await self._flush_scene_async(scene, fit_camera=fit_camera)

        await self._on_server_loop(_run)

    async def run_blocking(self, fn: Any, *args: Any, **kwargs: Any) -> Any:
        """Run a blocking callable in an executor from the current loop.

        A control handler can ``await`` this to run CPU-bound work in a worker
        thread without blocking the server loop.  Works for plain synchronous
        ``Visualizer`` scripts (which have no user loop).
        """
        return await asyncio.get_running_loop().run_in_executor(
            None, fn, *args, **kwargs
        )

    def show(
        self,
        *,
        host: str | None = None,
        port: int | None = None,
        wait_for_browser: bool | None = None,
        timeout: float | None = None,
        jupyter: bool | None = None,
        viewer_name: str | None = None,
        layout: View | None = None,
        layout_name: str | None = None,
    ) -> Any:
        """Serve the visualization and show it in the current environment.

        With ``jupyter=None`` (the default) the display mode is chosen
        automatically: in a Jupyter notebook this delegates to :meth:`display`
        (inline iframe); otherwise it opens a browser tab.  Pass
        ``jupyter=True`` to force the notebook display, or ``jupyter=False`` to
        force the standard browser tab.  ``viewer_name`` is forwarded to
        :meth:`display` in Jupyter.

        Equivalent to :meth:`start_server` followed by either :meth:`display`
        or :meth:`open_browser`.  ``host``/``port`` are only used when the
        server is not already running; see :meth:`start_server` for their
        semantics.
        """
        use_jupyter = self._jupyter if jupyter is None else jupyter

        if self._server is None:
            self.start_server(host=host or "localhost", port=port)

        if layout is not None:
            self.set_layout(layout, layout_name or "")
            return self._open_layout_browser(
                layout_name or "",
                wait_for_browser=wait_for_browser,
                timeout=timeout,
            )

        if use_jupyter:
            return self.display(viewer_name=viewer_name)

        return self.open_browser(wait_for_browser=wait_for_browser, timeout=timeout)

    def __enter__(self) -> "Visualizer":
        """Reset the main scene and show it immediately on entry.

        ``show()`` here starts the server (if needed) and makes the viewer
        visible *before* the block body runs, so each ``flush()`` inside the
        block updates the live viewer (e.g. an ``animate()`` loop).
        """
        self._reset_scene("")
        self.show()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Flush the main scene on exit (any exception still propagates)."""
        self.flush()
        return None

    def wait(self) -> None:
        """Block until Ctrl+C (or SIGTERM) requests shutdown, then return.

        Requires :meth:`start_server` (or :meth:`show`) to have been called so
        the Ctrl+C handler is installed.  The server is intentionally left
        running so the scene can keep being updated afterwards; it stops
        automatically at interpreter exit (via the ``atexit`` hook) or
        explicitly with :meth:`stop_server`.
        """
        self._ensure_server_running()
        shutdown = getattr(self, "_shutdown_requested", threading.Event())
        while not shutdown.is_set():
            time.sleep(0.25)

    def run(
        self,
        *,
        wait_for_browser: bool | None = None,
        layout: View | None = None,
        layout_name: str | None = None,
    ) -> None:
        """Deprecated: use :meth:`show` then :meth:`wait`.

        Starts the server, opens a browser, and blocks until Ctrl+C.
        """
        warnings.warn(
            "run() is deprecated; use show() then wait()",
            DeprecationWarning,
            stacklevel=2,
        )
        self.show(
            wait_for_browser=wait_for_browser, layout=layout, layout_name=layout_name
        )
        self.wait()

    # ── Interactive Controls (main scene) ───────────────────

    # ── Banners (delegated to OverlayContainer) ──────────────

    @property
    def _banners(self) -> dict[str | None, dict[str, Any]]:
        """Banner storage (global under ``None``, per-scene under the scene name)."""
        return self._layout.overlay._banners

    @property
    def _banner_counter(self) -> int:
        return self._layout.overlay._banner_counter

    def show_banner(
        self,
        text: str,
        *,
        id: str | None = None,
        title: str = "",
        align_x: float = 0.5,
        align_y: float = 0.5,
        auto_hide: bool = True,
        dismissable: bool = True,
        controls: list[Any] | None = None,
        on_close: Any = None,
        scene_name: str | None = None,
    ) -> str:
        """Show a banner/dialog and return its id (see :meth:`OverlayContainer.show_banner`)."""
        return self._layout.overlay.show_banner(
            text,
            id=id,
            title=title,
            align_x=align_x,
            align_y=align_y,
            auto_hide=auto_hide,
            dismissable=dismissable,
            controls=controls,
            on_close=on_close,
            scene_name=scene_name,
        )

    def alert(
        self,
        text: str,
        *,
        title: str = "",
        ok_label: str = "OK",
        on_ok: Any = None,
        align_x: float = 0.5,
        align_y: float = 0.5,
        dismissable: bool = True,
        scene_name: str | None = None,
    ) -> str:
        """Show an acknowledge banner with a single OK button."""
        return self._layout.overlay.alert(
            text,
            title=title,
            ok_label=ok_label,
            on_ok=on_ok,
            align_x=align_x,
            align_y=align_y,
            dismissable=dismissable,
            scene_name=scene_name,
        )

    def confirm(
        self,
        text: str,
        *,
        title: str = "",
        yes_label: str = "Yes",
        no_label: str = "No",
        cancel_label: str = "Cancel",
        on_yes: Any = None,
        on_no: Any = None,
        on_cancel: Any = None,
        align_x: float = 0.5,
        align_y: float = 0.5,
        dismissable: bool = True,
        scene_name: str | None = None,
    ) -> str:
        """Show a yes/no/cancel banner."""
        return self._layout.overlay.confirm(
            text,
            title=title,
            yes_label=yes_label,
            no_label=no_label,
            cancel_label=cancel_label,
            on_yes=on_yes,
            on_no=on_no,
            on_cancel=on_cancel,
            align_x=align_x,
            align_y=align_y,
            dismissable=dismissable,
            scene_name=scene_name,
        )

    def remove_banner(self, banner_id: str, *, scene_name: str | None = None) -> None:
        """Remove a banner by id (and unregister its handlers)."""
        return self._layout.overlay.remove_banner(banner_id, scene_name=scene_name)

    def clear_banners(self, *, scene_name: str | None = None) -> None:
        """Remove all banners in a scope (or globally when ``scene_name=None``)."""
        return self._layout.overlay.clear_banners(scene_name=scene_name)

    async def show_banner_async(
        self,
        text: str,
        *,
        id: str | None = None,
        title: str = "",
        align_x: float = 0.5,
        align_y: float = 0.5,
        auto_hide: bool = True,
        dismissable: bool = True,
        controls: list[Any] | None = None,
        on_close: Any = None,
        scene_name: str | None = None,
    ) -> str:
        """Awaitable :meth:`show_banner` (see :meth:`OverlayContainer.show_banner_async`)."""
        return await self._layout.overlay.show_banner_async(
            text,
            id=id,
            title=title,
            align_x=align_x,
            align_y=align_y,
            auto_hide=auto_hide,
            dismissable=dismissable,
            controls=controls,
            on_close=on_close,
            scene_name=scene_name,
        )

    async def remove_banner_async(
        self, banner_id: str, *, scene_name: str | None = None
    ) -> None:
        """Awaitable :meth:`remove_banner`."""
        return await self._layout.overlay.remove_banner_async(
            banner_id, scene_name=scene_name
        )

    async def clear_banners_async(self, *, scene_name: str | None = None) -> None:
        """Awaitable :meth:`clear_banners`."""
        return await self._layout.overlay.clear_banners_async(scene_name=scene_name)

    # ── Dialogs (delegated to OverlayContainer) ──────────────

    @property
    def _dialogs(self) -> dict[str | None, dict[str, Any]]:
        """Dialog storage (global under ``None``, per-scene under the scene name)."""
        return self._layout.overlay._dialogs

    @property
    def _dialog_counter(self) -> int:
        return self._layout.overlay._dialog_counter

    def show_dialog(
        self,
        content: Any,
        *,
        id: str | None = None,
        title: str = "",
        align_x: float = 0.5,
        align_y: float = 0.5,
        dismissable: bool = True,
        on_close: Any = None,
        width: Any = None,
        height: Any = None,
        scene_name: str | None = None,
    ) -> str:
        """Show a dialog and return its id (see :meth:`OverlayContainer.show_dialog`)."""
        return self._layout.overlay.show_dialog(
            content,
            id=id,
            title=title,
            align_x=align_x,
            align_y=align_y,
            dismissable=dismissable,
            on_close=on_close,
            width=width,
            height=height,
            scene_name=scene_name,
        )

    def remove_dialog(self, dialog_id: str, *, scene_name: str | None = None) -> None:
        """Remove a dialog by id (and unregister its handlers)."""
        return self._layout.overlay.remove_dialog(dialog_id, scene_name=scene_name)

    def clear_dialogs(self, *, scene_name: str | None = None) -> None:
        """Remove all dialogs in a scope (or globally when ``scene_name=None``)."""
        return self._layout.overlay.clear_dialogs(scene_name=scene_name)

    async def show_dialog_async(
        self,
        content: Any,
        *,
        id: str | None = None,
        title: str = "",
        align_x: float = 0.5,
        align_y: float = 0.5,
        dismissable: bool = True,
        on_close: Any = None,
        width: Any = None,
        height: Any = None,
        scene_name: str | None = None,
    ) -> str:
        """Awaitable :meth:`show_dialog` (see :meth:`OverlayContainer.show_dialog_async`)."""
        return await self._layout.overlay.show_dialog_async(
            content,
            id=id,
            title=title,
            align_x=align_x,
            align_y=align_y,
            dismissable=dismissable,
            on_close=on_close,
            width=width,
            height=height,
            scene_name=scene_name,
        )

    async def remove_dialog_async(
        self, dialog_id: str, *, scene_name: str | None = None
    ) -> None:
        """Awaitable :meth:`remove_dialog`."""
        return await self._layout.overlay.remove_dialog_async(
            dialog_id, scene_name=scene_name
        )

    async def clear_dialogs_async(self, *, scene_name: str | None = None) -> None:
        """Awaitable :meth:`clear_dialogs`."""
        return await self._layout.overlay.clear_dialogs_async(scene_name=scene_name)

    # ── Editor (delegated to OverlayContainer) ────────────

    def open_editor(
        self,
        cid: str,
        *,
        label: str = "",
        value: str = "",
        on_close: Any = None,
    ) -> str:
        """Open a transient multi-line text editor (see :meth:`OverlayContainer.open_editor`)."""
        return self._layout.overlay.open_editor(
            cid, label=label, value=value, on_close=on_close
        )

    async def _dispatch_control_event(
        self, msg_type: str, payload: dict[str, Any]
    ) -> None:
        """Route an incoming control event via the transport (back-compat shim)."""
        await self._transport.dispatch(msg_type, payload)

    # ── Inbound routes (registered on the transport) ─────────

    def _event_for(self, payload: dict[str, Any]) -> Any:
        from ._controls import ControlEvent

        return ControlEvent(browser_id=payload.get("browser_id"))

    async def _on_banner_closed(self, msg_type: str, payload: dict[str, Any]) -> None:
        target = payload.get("id") or payload.get("control_id")
        await self._layout.overlay._on_banner_close(
            target, payload.get("value"), self._event_for(payload)
        )

    async def _on_editor_closed(self, msg_type: str, payload: dict[str, Any]) -> None:
        target = payload.get("id") or payload.get("control_id")
        await self._layout.overlay._on_editor_close(
            target, payload.get("text"), self._event_for(payload)
        )

    async def _on_dialog_close(self, msg_type: str, payload: dict[str, Any]) -> None:
        target = payload.get("id") or payload.get("control_id")
        await self._layout.overlay._on_dialog_close(
            target, payload.get("value"), self._event_for(payload)
        )

    async def _on_dialog_accept(self, msg_type: str, payload: dict[str, Any]) -> None:
        target = payload.get("id") or payload.get("control_id")
        await self._layout.overlay._on_dialog_accept(target, self._event_for(payload))

    async def _on_control_event(self, msg_type: str, payload: dict[str, Any]) -> None:
        await self._layout.dispatch_control_event(msg_type, payload)

    def _register_routes(self) -> None:
        """Register the inbound message routes on the transport (data table)."""
        self._transport.route("banner_closed", self._on_banner_closed)
        self._transport.route("editor_closed", self._on_editor_closed)
        self._transport.route("close", self._on_dialog_close)
        self._transport.route("accept", self._on_dialog_accept)
        self._transport.route("control:*", self._on_control_event)
        self._transport.route("file_browser_navigate", self._on_control_event)
        self._transport.route("file_browser_select", self._on_control_event)
        self._transport.route(
            "interaction:*", self._interaction_host._dispatch_interaction_event
        )

    async def _on_client_connect(self, remote_addr: str) -> None:
        """Handle a new client connection.

        The comprehensive connection summary (with browser_id, page_token,
        viewer_name, and IP) is printed by VizServer._print_ws_connected
        after the browser's ``ready`` WebSocket message arrives.
        """
        return None

    async def _on_client_disconnect(self, remote_addr: str) -> None:
        """Log when a client disconnects."""
        self._print_disconnect(remote_addr)

    # ── Properties ──────────────────────────────────────────

    # ── Jupyter support ─────────────────────────────────────

    def _resolve_viewer_key(self, viewer_name: str | None, scene_name: str) -> str:
        """Resolve the stable viewer key used to dedupe notebook outputs.

        Priority: an explicit *viewer_name*, otherwise the current notebook cell
        id, otherwise the scene name (``"main"`` for the main scene).
        """
        if viewer_name is not None:
            return viewer_name
        cell_id = current_cell_id()
        if cell_id:
            return cell_id
        return scene_name or "main"

    def _display_live(
        self,
        src: str,
        viewer_key: str,
        width: int | str,
        height: int | str,
    ) -> None:
        """Emit the live iframe for *viewer_key* unless already shown this run.

        The "shown" state is scoped to the current notebook cell execution: a
        fresh execution re-emits the iframe (Jupyter destroys the previous one
        when a cell is re-run), while repeated calls within the same execution
        only flush pending state into the open viewer.
        """
        if self._server is None:
            print("Visualizer server is not running. Call start_server() first.")
            return
        token = execution_token()
        if token != self._display_execution:
            self._display_pending.clear()
            self._display_execution = token
        if viewer_key in self._display_pending:
            self.flush()
            return
        self._display_pending.add(viewer_key)
        from IPython.display import IFrame
        from IPython.display import display as ipy_display

        ipy_display(
            IFrame(src, width=width, height=height), display_id=f"tanga-{viewer_key}"
        )
        self.flush()

    def display(
        self,
        *,
        viewer_name: str | None = None,
        width: int | str = "100%",
        height: int | str = 500,
    ) -> Any:
        """Display the live main scene inline (iframe) in a Jupyter notebook.

        Within a single cell execution, repeated calls for the same viewer do
        not create a new iframe — they only flush the latest scene state into
        the already-open viewer.  The viewer is identified by *viewer_name*
        (if given), otherwise by the current notebook cell id, otherwise by the
        scene name (``"main"``).
        """
        key = self._resolve_viewer_key(viewer_name, "")
        self._viewer_name = key

        src = self.url
        if self._viewer_name:
            src += f"?viewer={self._viewer_name}"

        if self._jupyter:
            self._display_live(src, key, width, height)
            return None
        return (
            f'<iframe src="{src}" width="{width}" height="{height}px" '
            f'style="border: 1px solid #444; border-radius: 4px;" '
            f'title="Tanga 3D Viewer"></iframe>'
        )

    def display_row(
        self,
        *scenes: tuple[VizSceneHandle, str | None],
        width: int | str = "100%",
        height: int | str = 500,
        gap: int = 8,
        mode: str = "live",
    ) -> Any:
        """Display multiple scenes side by side in a single flex row.

        Each element in *scenes* is a ``(handle, viewer_name)`` tuple where
        *viewer_name* may be ``None``.

        *mode* is ``"live"`` (default — embeds the server URL) or
        ``"static"`` (embeds a serverless standalone snapshot).

        Usage::

            viz.display_row((one, None), (two, None))            # live
            viz.display_row((one, None), (two, None), mode="static")

        Args:
            *scenes: One or more ``(VizSceneHandle, viewer_name | None)`` pairs.
            width: CSS width of the container (default ``"100%"``).
            height: CSS height of each iframe in pixels (default 500).
            gap: Gap between columns in pixels (default 8).
            mode: ``"live"`` or ``"static"``.
        """
        from IPython.display import HTML
        from IPython.display import display as ipy_display

        columns_html: list[str] = []
        for handle, viewer_name in scenes:
            if mode == "static":
                import base64

                snapshot = handle._viz._render_snapshot_html(handle.name)
                b64 = base64.b64encode(snapshot.encode("utf-8")).decode("ascii")
                iframe = (
                    f'<iframe src="data:text/html;charset=utf-8;base64,{b64}" '
                    f'width="100%" height="{height}px" '
                    f'style="border: 1px solid #444; border-radius: 4px;" '
                    f'title="Tanga 3D Viewer — {handle.name}"></iframe>'
                )
            else:
                src = handle.url
                if viewer_name:
                    src += f"?viewer={viewer_name}"
                iframe = (
                    f'<iframe src="{src}" width="100%" height="{height}px" '
                    f'style="border: 1px solid #444; border-radius: 4px;" '
                    f'title="Tanga 3D Viewer — {handle.name}"></iframe>'
                )
            columns_html.append(
                f'<div style="flex: 1; min-width: 0;">'
                f'<h3 style="margin: 0 0 4px 0; font-size: 14px; color: #ccc;">'
                f"Scene: {handle.name}</h3>"
                f"{iframe}"
                f"</div>"
            )

        html = '<div style="display: flex; gap: {}px; width: {};">'.format(gap, width)
        html += "".join(columns_html)
        html += "</div>"
        ipy_display(HTML(html))
        return None

    def _render_snapshot_html(
        self,
        scene_name: str,
        *,
        animation: Any = None,
        anim_style: Any = None,
        theme: str | None = None,
    ) -> str:
        theme = theme or self._theme
        scene = self._layout.scenes[scene_name]
        if animation is not None:
            from pytanga.viz.export._animated_figure import (
                render_export_animated_html,
            )

            return render_export_animated_html(
                animation.to_dict(),
                scene_config=scene.config.to_dict(),
                anim_style=anim_style.to_dict() if anim_style is not None else None,
                title=self._title,
                theme=theme,
            )
        from pytanga.viz.export._html import render_snapshot

        objects = scene.full_state(styles_map=scene.styles.kind)
        return render_snapshot(
            objects=objects, scene_config=scene.config.to_dict(), theme=theme
        )

    def _open_scene_snapshot(self, scene_name: str) -> None:
        import tempfile
        import webbrowser
        from pathlib import Path

        html = self._render_snapshot_html(scene_name)
        tmp = Path(tempfile.mktemp(suffix=".html"))
        tmp.write_text(html, encoding="utf-8")
        webbrowser.open(str(tmp))

    def _export_scene_snapshot(
        self,
        scene_name: str,
        path: Any,
        *,
        overwrite: bool = False,
        animation: Any = None,
        anim_style: Any = None,
        theme: str | None = None,
    ) -> None:
        from pathlib import Path

        html = self._render_snapshot_html(
            scene_name, animation=animation, anim_style=anim_style, theme=theme
        )
        p = Path(path).expanduser()
        if not p.suffix:
            p = p.with_suffix(".html")
        if not overwrite and p.exists():
            raise FileExistsError(
                f"File {p} already exists. Use overwrite=True to replace it."
            )
        p.write_text(html, encoding="utf-8")

    def export_snapshot(
        self,
        path: Any,
        *,
        overwrite: bool = False,
        animation: Any = None,
        anim_style: Any = None,
        theme: str | None = None,
    ) -> None:
        """Export the current scene as a self-contained HTML file.

        Pass *animation* (an ``AnimationRecording``) to export an animated
        snapshot instead of a static one.  *theme* overrides the active UI theme
        for the packed CSS (default: the active theme).
        """
        self._export_scene_snapshot(
            "",
            path,
            overwrite=overwrite,
            animation=animation,
            anim_style=anim_style,
            theme=theme,
        )

    def open_snapshot(self) -> None:
        """Open the current scene as a standalone snapshot in a browser window."""
        self._open_scene_snapshot("")

    def _render_figure_html(
        self,
        scene_name: str,
        *,
        style: Any = None,
        animation: Any = None,
        anim_style: Any = None,
        theme: str | None = None,
    ) -> str:
        from pytanga.viz._figure import FigureConfig
        from pytanga.viz._styles import FigureStyle

        theme = theme or self._theme
        scene = self._layout.scenes[scene_name]
        resolved = style if style is not None else FigureStyle()
        fig_config = FigureConfig(
            title=self._title, annotation=self._annotation, footer=self._annotation
        )
        if animation is not None:
            from pytanga.viz.export._animated_figure import (
                render_export_animated_figure,
            )

            return render_export_animated_figure(
                animation.to_dict(),
                figure_style=resolved.to_dict(),
                figure_config=fig_config.to_dict(),
                scene_config=scene.config.to_dict(),
                anim_style=anim_style.to_dict() if anim_style is not None else None,
                theme=theme,
            )
        from pytanga.viz.export._figure_html import render_figure

        objects = scene.full_state(styles_map=scene.styles.kind)
        return render_figure(
            objects,
            scene.config.to_dict(),
            resolved.to_dict(),
            fig_config.to_dict(),
            theme=theme,
        )

    def _export_scene_figure(
        self,
        scene_name: str,
        path: Any,
        *,
        style: Any = None,
        overwrite: bool = False,
        animation: Any = None,
        anim_style: Any = None,
        theme: str | None = None,
    ) -> str | None:
        from pathlib import Path

        html = self._render_figure_html(
            scene_name,
            style=style,
            animation=animation,
            anim_style=anim_style,
            theme=theme,
        )
        if path is None:
            return html
        p = Path(path).expanduser()
        if not p.suffix:
            p = p.with_suffix(".html")
        if not overwrite and p.exists():
            raise FileExistsError(
                f"File {p} already exists. Use overwrite=True to replace it."
            )
        p.write_text(html, encoding="utf-8")
        return None

    def export_figure(
        self,
        path: Any = None,
        *,
        style: Any = None,
        overwrite: bool = False,
        animation: Any = None,
        anim_style: Any = None,
        theme: str | None = None,
    ) -> str | None:
        """Export the current scene as an HTML snippet (or return the string).

        Pass *animation* (an ``AnimationRecording``) to export an animated
        figure instead of a static one.  *theme* overrides the active UI theme
        for the packed CSS (default: the active theme).
        """
        return self._export_scene_figure(
            "",
            path,
            style=style,
            overwrite=overwrite,
            animation=animation,
            anim_style=anim_style,
            theme=theme,
        )

    def _export_scene_glb(
        self, scene_name: str, path: Any, *, overwrite: bool = False
    ) -> None:
        from pathlib import Path

        from pytanga.viz.export._gltf import build_glb

        scene = self._layout.scenes[scene_name]
        all_objects = scene.full_state(styles_map=scene.styles.kind)
        entities = [o for o in all_objects if o.get("layer") != "overlay"]
        glb = build_glb(entities, scene.config)
        p = Path(path).expanduser()
        if not p.suffix:
            p = p.with_suffix(".glb")
        if not overwrite and p.exists():
            raise FileExistsError(
                f"File {p} already exists. Use overwrite=True to replace it."
            )
        p.write_bytes(glb)

    def export_glb(self, path: Any, *, overwrite: bool = False) -> None:
        """Export the current scene as a glTF 2.0 binary (``.glb``) file."""
        self._export_scene_glb("", path, overwrite=overwrite)

    def _start_scene_animation_recording(self, scene_name: str) -> Any:
        from pytanga.viz.export._animation_recording import AnimationRecording

        scene = self._layout.scenes[scene_name]
        return AnimationRecording(scene, styles_map=scene.styles.kind)

    def start_animation_recording(self) -> Any:
        """Begin recording entity state for animated export (main scene)."""
        return self._start_scene_animation_recording("")

    def display_snapshot(
        self,
        width: int | str = "100%",
        height: int | str = "500px",
        *,
        scene_name: str = "",
    ) -> Any:
        """Display a scene as standalone HTML (no server required).

        In Jupyter, returns an ``IPython.display.IFrame`` embedding the
        standalone document via a data URL (no server, no style leakage).
        Outside Jupyter, opens the snapshot in a browser window.
        """
        html = self._render_snapshot_html(scene_name)

        if self._jupyter:
            import base64

            from IPython.display import IFrame

            width_css = f"{width}px" if isinstance(width, int) else str(width)
            height_css = f"{height}px" if isinstance(height, int) else str(height)
            b64 = base64.b64encode(html.encode("utf-8")).decode("ascii")
            return IFrame(
                src=f"data:text/html;charset=utf-8;base64,{b64}",
                width=width_css,
                height=height_css,
            )

        self._open_scene_snapshot(scene_name)
        return None

    def display_static(
        self,
        width: int | str = "100%",
        height: int | str = "500px",
        *,
        scene_name: str = "",
    ) -> Any:
        """Deprecated: use :meth:`display_snapshot`."""
        warnings.warn(
            "display_static() is deprecated; use display_snapshot()",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.display_snapshot(width=width, height=height, scene_name=scene_name)

    @property
    def global_styles(self) -> "VizStyles":
        """The master :class:`VizStyles` instance (template for new scenes)."""
        return self._global_styles

    @property
    def styles(self) -> "VizStyles":
        """The main scene's :class:`VizStyles` (what gets rendered)."""
        return self._layout.scenes[""].styles

    @property
    def main_scene(self) -> Scene:
        """The underlying main :class:`Scene` instance (backward compat)."""
        return self._layout.scenes[""]

    @property
    def url(self) -> str:
        """The HTTP URL of the viewer."""
        return f"http://{self._host}:{self._port}"
