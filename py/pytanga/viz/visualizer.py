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
from typing import TYPE_CHECKING, Any, Iterator, NamedTuple, Sequence

if TYPE_CHECKING:
    from ._object_ref import VizObjectRef
    from ._styles import AnnotationStyle, LabelStyle, ObjVizStyle, TextureLabelStyle
    from ._viz_styles import VizStyles

from pytanga.geometry.entities import Entity as GeoEntity

from ._anchor import EAnchor
from ._icons import Icon
from ._jupyter import _JupyterDisplayMixin
from ._keys import KeyModifier
from ._notebook_cell import current_cell_id, execution_token
from ._props import _normalize_color
from ._scene_handle import VizSceneHandle
from ._style_dict import (
    _kind_to_key,
    _resolve_annotation_style,
    _resolve_label_style,
    _resolve_tex_label_style,
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
    ControlView,
    SceneView,
    View,
    serialize_layout,
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


class ControlRef(NamedTuple):
    """A control resolved by id, regardless of placement.

    ``placement`` is ``"panel"`` (a :class:`~pytanga.viz._controls.Control`
    stored in a scene) or ``"view"`` (a layout ``ControlView``).  ``scene`` is
    the owning scene name (``""`` for layout views, which are global).
    """

    placement: str
    control: Any
    scene: str


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
        background_color: str = "#1a1a2e",
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
        self._server = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._theme = "dark"
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
        from ._controls import ControlHandlerRegistry

        self._handler_registry = ControlHandlerRegistry()

        # Banner storage: global banners under ``None``, per-scene under the
        # scene name.  Banner ids are unique across scopes (auto-generated).
        self._banners: dict[str | None, dict[str, Any]] = {}
        self._banner_counter = 0
        # Banner/editor/dialog ``on_close`` handlers live in ``_handler_registry``
        # under ``(id, "close")``.

        # Dialog storage: global dialogs under ``None``, per-scene under the
        # scene name.  Dialog ids are unique across scopes (auto-generated).
        self._dialogs: dict[str | None, dict[str, Any]] = {}
        self._dialog_counter = 0

        # Interaction handler registry (shared across all scenes)
        from ._interaction import InteractionHandlerRegistry

        self._interaction_registry = InteractionHandlerRegistry(self._handler_registry)
        self._interaction_configs: dict[str, dict[str, Any]] = {}
        self._act_objects: dict[str, Any] = {}

        # ── Multi-scene storage ──
        # Key "" is the main scene (backward compatible).
        self._scenes: dict[str, Scene] = {}
        self._scenes[""] = Scene(
            self._config, name="", styles=self._global_styles.copy()
        )
        # ── Split-view layouts ──
        # Key "" is the default layout (shown at "/?view=").
        self._layouts: dict[str, View] = {}
        self._layouts_serialized: dict[str, dict[str, Any]] = {}
        # Single-scene layouts (one ``SceneView`` stack per named scene), cached
        # for the unified view mode.  The base scene reuses ``_layouts[""]``.
        self._scene_layouts_serialized: dict[str, dict[str, Any]] = {}
        # Control ids registered by the currently-registered layout, so they can
        # be unregistered cleanly when the layout is overwritten.
        self._layout_control_ids: set[str] = set()

        # Global overlay views (e.g. global menus) mounted into the browser's
        # full-screen overlay container and serialized alongside every layout.
        self._global_overlay: list[View] = []
        self._menus: dict[str, View] = {}
        self._menu_counter = 0

        # Control groups unified onto `GroupView`: per-scene overlay views
        # (injected into each layout's matching `SceneView` pane), the id → view
        # registry, and the set of injected view ids so re-sync can strip and
        # re-append them idempotently.
        self._scene_overlays: dict[str, list[View]] = {}
        self._scene_groups: dict[str, dict[str, View]] = {}
        self._injected_overlay_ids: set[int] = set()

        self._default_objects_added: set[str] = set()

        # Seed default axes/grid immediately — independent of server start.
        self._add_default_scene_objects("")

        # Opt-in browser-triggered server stop for the main scene.
        if enable_server_stop_key:
            self.enable_server_stop_key()

    # ── Scene access ─────────────────────────────────────────

    def scene(
        self,
        name: str,
        *,
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
        if name not in self._scenes:
            cfg = SceneConfig(
                background_color=self._config.background_color,
                camera=None,
                title=name or self._config.title,
                name=name,
                space_dim=self._config.space_dim,
            )
            self._scenes[name] = Scene(
                cfg, name=name, styles=self._global_styles.copy()
            )
            self._add_default_scene_objects(name, add_axes=add_axes, add_grid=add_grid)
        if enable_server_stop_key:
            self._set_server_stop_key(
                name, enabled=True, key="q", modifiers=[KeyModifier.CTRL]
            )
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

    def set_layout(self, root: View, name: str = "") -> str:
        """Register a split-view layout and return its name.

        The layout is validated, serialized once, and served (plus subscribed
        to) as the ``view_layout`` message when a browser opens
        ``/?view=<name>``.
        """
        if not isinstance(root, View):
            raise TypeError(f"layout must be a View, got {type(root).__name__}")
        self._layouts[name] = root
        self._register_control_handlers(root)
        self._sync_overlays()
        return name

    def _register_view_handlers(self, root: View) -> set[str]:
        """Register control-view handlers in *root*'s subtree; return their ids."""
        from .views import iter_control_views

        registered: set[str] = set()
        for view in iter_control_views(root):
            entries: list[tuple[str, Any]] = []
            if getattr(view, "on_change", None) is not None:
                entries.append(("change", view.on_change))
            elif getattr(view, "on_click", None) is not None:
                entries.append(("click", view.on_click))
            if getattr(view, "on_cell_change", None) is not None:
                entries.append(("cell_change", view.on_cell_change))
            if getattr(view, "on_row_add", None) is not None:
                entries.append(("row_add", view.on_row_add))
            if getattr(view, "on_column_add", None) is not None:
                entries.append(("column_add", view.on_column_add))
            if getattr(view, "on_row_delete", None) is not None:
                entries.append(("row_delete", view.on_row_delete))
            for event, h in entries:
                self._handler_registry.register(view.id, h, event=event)
            if entries:
                registered.add(view.id)
        return registered

    def _register_control_handlers(self, root: View) -> None:
        """Register control-view handlers into the control handler registry."""
        for cid in self._layout_control_ids:
            self._handler_registry.unregister(cid)
        self._layout_control_ids = self._register_view_handlers(root)

    def _sync_overlays(self) -> None:
        """Re-serialize every registered layout with global + scene overlays."""
        from .views import SceneView, StackView

        if (self._global_overlay or self._scene_overlays) and not self._layouts:
            # No-layout case: create a minimal default layout so overlays have a
            # root (and a matching ``SceneView`` pane) to attach to.
            self._layouts[""] = StackView("vertical", [SceneView("")])
        overlay = self._global_overlay or None
        for name, root in self._layouts.items():
            self._inject_scene_overlays(root)
            self._layouts_serialized[name] = serialize_layout(
                root, name=name, overlay=overlay
            )
        # Rebuild cached single-scene layouts for named scenes (their per-scene
        # overlays may have changed).  The base scene is covered by the loop above.
        for name in list(self._scene_layouts_serialized):
            root = StackView("vertical", [SceneView(name)])
            self._inject_scene_overlays(root)
            self._scene_layouts_serialized[name] = serialize_layout(root, name=name)
        # Live re-push (unified view mode): connected browsers see overlay changes.
        self._push_layout_updates_threadsafe()

    def _inject_scene_overlays(self, root: View) -> None:
        """Merge per-scene overlay views into each matching ``SceneView`` pane."""
        from .views import iter_scene_views

        for scene_view in iter_scene_views(root):
            base = [
                v for v in scene_view.overlay if id(v) not in self._injected_overlay_ids
            ]
            scene_view.overlay = base + list(
                self._scene_overlays.get(scene_view.scene, [])
            )

    def add_menu(
        self,
        mid: str | None = None,
        *,
        label: str = "",
        trigger_icon: Icon | None = None,
        mode: str = "dropdown",
        direction: str = "vertical",
        position: EAnchor | None = None,
        override_variant: bool = True,
        children: list[View] | None = None,
        scene_name: str | None = None,
    ) -> str:
        """Add a menu to the global overlay and return its id.

        ``scene_name=None`` (or the base scene ``""``) adds a **global** menu,
        mounted in the browser's full-screen overlay.  Per-pane menus are
        declared declaratively via ``SceneView(overlay=[MenuView(...)])``;
        per-scene-name menus are out of scope and raise ``NotImplementedError``.
        """
        from .views import MenuView

        if scene_name not in (None, ""):
            raise NotImplementedError(
                "Per-scene-name menus are out of scope; declare per-pane menus "
                "with SceneView(overlay=[MenuView(...)])"
            )
        if mid is None:
            mid = f"menu_{self._menu_counter}"
            self._menu_counter += 1
        menu = MenuView(
            label=label,
            trigger_icon=trigger_icon,
            mode=mode,
            direction=direction,
            position=position,
            override_variant=override_variant,
            children=list(children or []),
        )
        self._menus[mid] = menu
        self._global_overlay.append(menu)
        self._register_view_handlers(menu)
        self._sync_overlays()
        return mid

    def _layout_serialized_for(self, layout_name: str) -> dict[str, Any] | None:
        """Callback: return the serialized layout for *layout_name*, or None."""
        return self._layouts_serialized.get(layout_name)

    def _scene_layout_for(self, scene_name: str) -> dict[str, Any] | None:
        """Return the serialized single-scene layout for *scene_name*.

        A single scene is served as a one-``SceneView`` stack merged with the
        global overlay (base scene only) and any per-scene overlays.  This is
        the model the server uses to always serve a ``view_layout``.
        """
        from .views import SceneView, StackView

        if scene_name == "":
            if "" not in self._layouts:
                self._layouts[""] = StackView("vertical", [SceneView("")])
            if "" not in self._layouts_serialized:
                self._inject_scene_overlays(self._layouts[""])
                self._layouts_serialized[""] = serialize_layout(
                    self._layouts[""], name="", overlay=self._global_overlay or None
                )
            return self._layouts_serialized.get("")

        layout = self._scene_layouts_serialized.get(scene_name)
        if layout is None:
            root = StackView("vertical", [SceneView(scene_name)])
            self._inject_scene_overlays(root)
            layout = serialize_layout(root, name=scene_name)
            self._scene_layouts_serialized[scene_name] = layout
        return layout

    async def _push_layout_updates(self) -> None:
        """Re-push each connected session's ``view_layout`` after overlays change.

        A layout tab gets its named layout; a single-scene tab gets its scene's
        auto-derived single-scene layout.  Runs on the server event loop.
        """
        if self._server is None:
            return
        for session in self._server.get_browser_sessions():
            layout_name = session.get("layout")
            if layout_name is not None:
                payload = self._layout_serialized_for(layout_name)
            else:
                payload = self._scene_layout_for(session["scene"])
            if payload is not None:
                await self._server.push_layout_to_session(session["id"], payload)

    def _push_layout_updates_threadsafe(self) -> None:
        """Schedule :meth:`_push_layout_updates` onto the server loop (no-op pre-server)."""
        if self._server is None or self._loop is None:
            return
        asyncio.run_coroutine_threadsafe(self._push_layout_updates(), self._loop)

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
    ) -> str:
        """Add a geometric entity, operator, multivector, or label to the main scene.

        Returns the entity ID as a ``str``.  If *label* is provided the
        label is created alongside the entity and the entity ID is returned.

        See the class docstring for full parameter documentation.
        """
        return self._add_to_scene(
            "",
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

        eid = self._add_to_scene(
            "",
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
        node = self._scenes[""].get_node(eid)
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

        scene = self._scenes[scene_name]
        group = scene.add_group(name)
        return VizObjectRef(VizSceneHandle(self, scene_name), group)

    def _add_to_scene(
        self,
        scene_name: str,
        *,
        obj: VizInputType | None = None,
        entity_id: str | None = None,
        color: Any = None,
        opacity: float | None = None,
        style: ObjVizStyle | None = None,
        label: str | None = None,
        label_style: LabelStyle | None = None,
        tex_label: str | None = None,
        tex_label_style: "TextureLabelStyle | None" = None,
        parent_id: str | None = None,
        attach_to: str | None = None,
    ) -> str:
        """Add an entity to a specific scene.

        ``parent_id`` parents the new scene node under an existing scene node;
        ``attach_to`` sets the scene-node reference for a label created here.
        """
        from ._active import ActSceneObject
        from ._label import Label
        from ._nodes import VizGroup, VizSceneObject
        from ._styles import TextureLabelStyle as _TLS

        scene = self._scenes[scene_name]

        if isinstance(obj, VizGroup):
            from .scene import _generate_id

            gid = entity_id or obj.id or _generate_id()
            obj.id = gid
            scene.add_node(obj, object_id=gid)
            if parent_id is not None:
                parent = scene.get_node(parent_id)
                if isinstance(parent, VizSceneObject):
                    parent.add_child(obj)
            return gid

        if isinstance(obj, ActSceneObject):
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
            eid = scene.add(obj.entity, entity_id=entity_id, **properties)
            obj._init(VizSceneHandle(self, scene_name), eid)
            self._act_objects[eid] = obj
            self._attach_to_parent(scene, eid, parent_id)
            self._add_label_for_entity(
                scene,
                obj.entity,
                eid,
                label=label,
                label_style=label_style,
                attach_to=attach_to,
                properties=properties,
            )
            return eid

        if isinstance(obj, Label):
            if attach_to is not None:
                obj.parent_id = attach_to
            return scene.add_label(obj)

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

        # Build texture label convenience style if tex_label is set
        _tex_label_merged: _TLS | None = None
        if tex_label is not None:
            entity_for_kind = self._resolve(obj)
            kind = type(entity_for_kind).__name__
            _tex_label_merged = _resolve_tex_label_style(
                scene.styles.tex_label_base,
                scene.styles.tex_label_kind.get(kind),
                tex_label_style,
            )
            _tex_label_merged.text = tex_label

        # Merge texture label into style if the user didn't provide
        # texture_label explicitly via style
        if _tex_label_merged is not None:
            if style is not None:
                from ._styles import PlaneStyle, SphereStyle

                style_for_check = style
                if isinstance(style_for_check, (SphereStyle, PlaneStyle)):
                    if style_for_check.texture_label is None:
                        style_for_check.texture_label = _tex_label_merged
                # Otherwise leave the user's explicit style alone
            else:
                kind_for_style = None
                entity_for_style = self._resolve(obj)
                if entity_for_style is not None:
                    kind_for_style = type(entity_for_style).__name__
                if kind_for_style == "Sphere":
                    from ._styles import SphereStyle as SS

                    style = SS(
                        texture_label=_tex_label_merged,
                        wireframe=False,
                        # double_sided=True,
                    )
                elif kind_for_style == "Plane":
                    from ._styles import PlaneStyle as PS

                    style = PS(texture_label=_tex_label_merged, wireframe=False)

        if style is not None:
            properties["style"] = style

        entity = self._resolve(obj)

        # Viz-level drawables (PointPath, etc.) go through add_object
        from pytanga.geometry.entities import Entity as GeoEntity
        from pytanga.geometry.operators import Operator as GeoOperator

        if not isinstance(entity, (GeoEntity, GeoOperator)):
            kind = type(entity).__name__
            oid = scene.add_object(
                SceneObject(
                    id=entity_id or "",
                    layer="scene",
                    kind=kind,
                    data=entity,
                    properties=properties,
                    dirty=True,
                ),
                object_id=entity_id,
            )
            self._attach_to_parent(scene, oid, parent_id)
            self._add_label_for_entity(
                scene,
                entity,
                oid,
                label=label,
                label_style=label_style,
                attach_to=attach_to,
                properties=properties,
            )
            return oid

        eid = scene.add(entity, entity_id=entity_id, **properties)
        self._attach_to_parent(scene, eid, parent_id)

        self._add_label_for_entity(
            scene,
            entity,
            eid,
            label=label,
            label_style=label_style,
            attach_to=attach_to,
            properties=properties,
        )
        return eid

    @staticmethod
    def _attach_to_parent(scene: Any, oid: str, parent_id: str | None) -> None:
        """Attach a scene node to a parent scene node (no-op when ``parent_id`` is ``None``)."""
        if parent_id is None:
            return
        from ._nodes import VizSceneObject

        child = scene.get_node(oid)
        parent = scene.get_node(parent_id)
        if isinstance(child, VizSceneObject) and isinstance(parent, VizSceneObject):
            parent.add_child(child)

    def _add_label_for_entity(
        self,
        scene: Any,
        entity: Any,
        eid: str,
        *,
        label: str | None,
        label_style: LabelStyle | None,
        attach_to: str | None,
        properties: dict[str, Any],
    ) -> None:
        """Create a label for *entity* attached to *eid*.

        No-op when *label* is ``None``.  Shared by the regular entity path and
        the :class:`ActSceneObject` path so active objects support ``label=``.
        """
        if label is None:
            return
        from ._label import Label
        from ._label_frame import compute_label_position
        from .serializer import resolve_line_length

        from pytanga.geometry.entities import Line
        from pytanga.geometry.operators import ReflectionLine

        kind = type(entity).__name__
        resolved_ls = _resolve_label_style(
            scene.styles.label_base,
            scene.styles.label_kind.get(kind),
            label_style,
        )

        line_length = None
        if isinstance(entity, Line):
            line_length = resolve_line_length(
                entity, styles_map=scene.styles.kind, props=properties
            )
        elif isinstance(entity, ReflectionLine):
            line_length = resolve_line_length(
                entity.line, styles_map=scene.styles.kind, props=properties
            )

        position = compute_label_position(
            entity,
            resolved_ls.offset_local,
            along=resolved_ls.along,
            line_length=line_length,
        )
        lbl = Label(
            text=label,
            position=position,
            parent_id=attach_to if attach_to is not None else eid,
            style=resolved_ls,
        )
        scene.add_label(lbl)

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
        self._scenes[""].update(entity_id, **properties)

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
        self._scenes[""].update(entity_id, **props)

    def update_entity(self, entity_id: str, obj: SceneEntity) -> None:
        """Replace the geometry for an existing entity in the main scene."""
        entity: SceneEntity = self._resolve(obj)
        self._scenes[""].update_entity(entity_id, entity)

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
        self._scenes[""].update_sdf_group_member(
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
        self._scenes[""].update_label(object_id, text=text, style=style)

    def get_label_ids(self, entity_id: str) -> list[str]:
        """Return the IDs of all labels attached to *entity_id* in the main scene."""
        return self._scenes[""].get_label_ids(entity_id)

    def remove(self, entity_id: str) -> None:
        """Remove an entity from the main scene."""
        self._scenes[""].remove(entity_id)

    def clear(self, *, add_axes: bool = False, add_grid: bool = False) -> None:
        """Remove all entities from the main scene.

        By default the scene is left empty.  Set ``add_axes`` / ``add_grid``
        to ``True`` to re-add the default coordinate axes / grid afterward
        (subject to the visualizer's ``add_default_axes`` / ``add_default_grid``
        constructor flags).
        """
        self._scenes[""].clear()
        if add_axes or add_grid:
            self._default_objects_added.discard("")
            self._add_default_scene_objects("", add_axes=add_axes, add_grid=add_grid)

    def _reset_scene(self, scene_name: str) -> None:
        """Clear a scene and re-add its default axes/grid.

        Used by the context managers so ``with viz:`` / ``with viz.scene(name):``
        reset to the default scene (axes/grid present), not an empty one.
        """
        self._scenes[scene_name].clear()
        self._default_objects_added.discard(scene_name)
        self._add_default_scene_objects(scene_name)

    # ── Theme selection ─────────────────────────────────────────

    @property
    def theme(self) -> str:
        """The active UI theme id (default ``"dark"``)."""
        return self._theme

    def set_theme(self, theme_id: str) -> None:
        """Select the active UI theme and push it to all connected clients.

        Validates *theme_id* against the theme registry (raising on unknown
        themes), records it as the active theme, and pushes a ``theme_define``
        message so connected viewers restyle without a page reload.
        """
        from ._themes import theme_css_files

        theme_css_files(theme_id)  # raises KeyError on unknown theme
        self._theme = theme_id
        self._push_theme()

    async def set_theme_async(self, theme_id: str) -> None:
        """Async variant of :meth:`set_theme` — call from the server's event loop."""
        from ._themes import theme_css_files

        theme_css_files(theme_id)  # raises KeyError on unknown theme
        self._theme = theme_id
        if self._server is not None:
            await self._server.push_raw(json.dumps(self._theme_message()))

    def _theme_message(self) -> dict[str, Any]:
        """Return the full ``theme_define`` message for the active theme."""
        return {"type": "theme_define", **self._theme_define_payload()}

    def _push_theme(self) -> None:
        """Push the active theme to all connected clients (thread-safe)."""
        if self._server is None or self._loop is None:
            return
        asyncio.run_coroutine_threadsafe(
            self._server.push_raw(json.dumps(self._theme_message())), self._loop
        )

    def _theme_define_payload(self) -> dict[str, Any]:
        """Return the active theme's ``theme_define``-shaped payload (no ``type``)."""
        from ._themes import theme_css_files, theme_label

        return {
            "theme": self._theme,
            "label": theme_label(self._theme),
            "css": theme_css_files(self._theme),
        }

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
        data = json.dumps(self._scenes[scene_name].config.to_dict())
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
        scene = self._scenes[scene_name]
        scene.config.camera = _normalize_camera_config(camera)
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

    def set_control_view_value(self, view: ControlView, value: Any) -> None:
        """Update a layout control view's value in place and push ``control_update``.

        Mirrors :meth:`set_view_camera`: the view must be a :class:`ControlView`
        and the update is keyed by ``view.id``.
        """
        from ._controls import (
            get_control_value,
            set_control_value as _set_control_value,
        )

        _set_control_value(view.control, value)
        self._push_control_update("", view.id, get_control_value(view.control))

    def set_control(self, cid: str, value: Any) -> None:
        """Set a control's value in place and push ``control_update``.

        Resolves *cid* across panel controls (any scene) and layout view
        controls, so this is the single value-update entry point regardless of
        placement.

        Args:
            cid: The control id (panel or layout view).
            value: The new value (coerced to the control kind's type).
        """
        from ._controls import (
            get_control_value,
            set_control_value as _set_control_value,
        )

        ref = self._resolve_control(cid)
        if ref is None:
            raise KeyError(f"Control {cid!r} not found")
        _set_control_value(ref.control, value)
        self._push_control_update(ref.scene, cid, get_control_value(ref.control))

    def get_control(self, cid: str) -> Any:
        """Return the current value of the control/view with id *cid*."""
        from ._controls import get_control_value

        ref = self._resolve_control(cid)
        if ref is None:
            raise KeyError(f"Control {cid!r} not found")
        return get_control_value(ref.control)

    # ── Default scene objects ───────────────────────────────

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
        scene = self._scenes[scene_name]

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
                self._add_to_scene(scene_name, obj=axes)
            if want_grid:
                grid = Grid(range_u=(-5.0, 5.0), range_v=(-5.0, 5.0))
                self._add_to_scene(scene_name, obj=grid)
        else:
            if want_axes:
                axes = Axes3D(
                    range_u=(0.0, 5.0),
                    range_v=(0.0, 5.0),
                    range_w=(0.0, 5.0),
                    show_value_labels=False,
                )
                self._add_to_scene(
                    scene_name,
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
                self._add_to_scene(scene_name, obj=grid)

        self._default_objects_added.add(scene_name)

    def _full_state_for(
        self, scene_name: str
    ) -> tuple[list[dict[str, Any]], list[str]]:
        """Return full serialized state for a scene, adding defaults first."""
        self._add_default_scene_objects(scene_name)
        scene = self._scenes.get(scene_name, self._scenes[""])
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
                scene = self._scenes[scene_name]
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
        """Resolve an MV to a :class:`SceneEntity`.

        Viz-level drawables (PointPath, …) are passed through unchanged.
        GeoEntities and Operators are returned as-is.
        MVs are resolved via :func:`pytanga.geometry.analyze`, reading the
        MV's ``algebra.opns`` flag.
        """
        from pytanga.geometry.operators import Operator as GeoOperator

        # Viz-level drawables — pass through
        if isinstance(obj, SceneEntity):
            return obj  # type: ignore[return-value]

        # SDF drawables (SdfElement / SdfNode) — pass through unchanged; they
        # are serialized by the SDF path (SdfElements carry their own style).
        from .sdf._compose import SdfElement as _SdfElement
        from .sdf.primitives import SdfNode as _SdfNode

        if isinstance(obj, (_SdfElement, _SdfNode)):
            return obj  # type: ignore[return-value]

        # Geo entities and operators — pass through
        if isinstance(obj, (GeoEntity, GeoOperator)):
            return obj  # type: ignore[return-value]

        try:
            from pytanga.geometry import analyze

            result = analyze(obj)
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

        from .server import VizServer

        logger.info("Starting VizServer on %s:%d", self._host, self._port)
        self._server = VizServer(host=self._host, port=self._port)

        _boot_done = threading.Event()
        _boot_start = time.monotonic()

        async def _boot() -> None:
            await self._server.start(
                self._full_state_for,
                self._config.to_dict,
                control_callback=self._dispatch_control_event,
                interaction_callback=self._dispatch_interaction_event,
                on_connect=self._on_client_connect,
                on_disconnect=self._on_client_disconnect,
                push_controls=self._push_controls_async,
                animation_stop_callback=self._on_browser_animation_stop,
                push_animation_stop=self._push_animation_stop_async,
                scene_config_callback=self._scene_config_for,
                scene_list_callback=self.list_scenes,
                layout_callback=self._layout_serialized_for,
                scene_layout_callback=self._scene_layout_for,
                theme_callback=self._theme_define_payload,
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
        scene = self._scenes.get(scene_name)
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
        scene = self._scenes.get(scene_name)
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
        for name in self._scenes:
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
            for name in self._scenes:
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

    # ── Object Interaction ─────────────────────────────────

    def set_interaction(
        self,
        object_id: str,
        config: Any,
        *,
        scene_name: str = "",
    ) -> None:
        """Set the interaction configuration for an entity.

        The config is sent to the frontend with the next scene flush.
        """
        self._interaction_configs.setdefault(scene_name, {})[object_id] = config
        scene = self._scenes[scene_name]
        scene.set_interaction(object_id, config)

    def on_interaction(
        self,
        object_id: str,
        event_type: Any,
        handler: Any,
        *,
        scene_name: str = "",
    ) -> None:
        """Register an async handler for interaction events on an entity.

        Args:
            object_id: The entity ID.
            event_type: An :class:`~pytanga.viz._interaction.InteractionEventType`
                value.
            handler: Async callable receiving a :class:`ClickEvent`,
                :class:`DragEvent`, or :class:`ScrollEvent`.
            scene_name: Target scene (default ``""`` = main scene).
        """
        from ._controls import HandlerOrigin

        self._handler_registry.register(
            object_id,
            handler,
            event=event_type.value,
            origin=HandlerOrigin.INTERACTION,
        )

    async def _send_drag_anchor(self, event: Any) -> None:
        """Resolve the ideal drag anchor and rebase the event on it.

        On ``DRAG_START`` the frontend reports ``world_position`` at the
        raycast hit point on the rendered mesh (e.g. a point's sphere surface),
        which can carry an off-plane component in a 2D scene.  The ideal anchor
        is computed here and written back into ``event.world_position`` so the
        ``DRAG_START`` handler observes the ideal point, before the anchor is
        also replied to the originating browser for the frontend's rebasing.
        """
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
        # Use the ideal point as the drag-start position for handlers.
        event.world_position = anchor
        if self._server is not None:
            await self._server.push_raw_to_browser(
                event.browser_id,
                json.dumps(
                    {
                        "type": "interaction:drag_anchor",
                        "object_id": event.object_id,
                        "world_position": [anchor.x, anchor.y, anchor.z],
                    }
                ),
            )

    async def _resolve_click_anchor(self, event: Any) -> None:
        """Overwrite a CLICK event's world_position with the ideal anchor.

        The frontend reports ``world_position`` at the raycast hit on the
        rendered mesh (e.g. a point's sphere surface), which can carry an
        off-plane component in a 2D scene.  Rebuild the picking ray from the
        event's camera + screen position and replace ``world_position`` with
        the ideal point from :meth:`drag_anchor`.
        """
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
        """Callback invoked by the server for incoming interaction events.

        Parses the raw JSON dict into the appropriate event dataclass and
        dispatches to the :class:`InteractionHandlerRegistry`.
        """
        from ._interaction import _parse_event

        try:
            event = _parse_event(data)
        except (ValueError, KeyError):
            return
        await self._send_drag_anchor(event)
        await self._resolve_click_anchor(event)
        await self._interaction_registry.dispatch(event)

    # ── Interactive Controls (main scene) ───────────────────

    def add_slider(
        self,
        cid: str,
        *,
        label: str = "",
        tooltip: str = "",
        min: float = 0.0,
        max: float = 1.0,
        step: float = 0.01,
        value: float | None = None,
        on_change: Any = None,
        on_press: Any = None,
        on_release: Any = None,
        parent_id: str | None = None,
    ) -> str:
        return self._add_scene_slider(
            "",
            cid,
            label=label,
            tooltip=tooltip,
            min=min,
            max=max,
            step=step,
            value=value,
            on_change=on_change,
            on_press=on_press,
            on_release=on_release,
            parent_id=parent_id,
        )

    def _add_scene_slider(
        self,
        scene_name: str,
        cid: str,
        *,
        label: str = "",
        tooltip: str = "",
        min: float = 0.0,
        max: float = 1.0,
        step: float = 0.01,
        value: float | None = None,
        on_change: Any = None,
        on_press: Any = None,
        on_release: Any = None,
        parent_id: str | None = None,
    ) -> str:
        from ._controls import Slider

        ctrl = Slider(
            id=cid,
            label=label,
            tooltip=tooltip,
            min=min,
            max=max,
            step=step,
            value=value if value is not None else min,
            on_change=on_change,
            on_press=on_press,
            on_release=on_release,
            parent_id=parent_id,
        )
        self._scenes[scene_name].add_control(ctrl)
        if on_change is not None:
            self._handler_registry.register(cid, on_change)
        if on_press is not None:
            self._handler_registry.register(cid, on_press, event="press")
        if on_release is not None:
            self._handler_registry.register(cid, on_release, event="release")
        self._push_controls(scene_name)
        return cid

    def update_control(
        self, ctrl_id: str, *, scene_name: str = "", **fields: Any
    ) -> None:
        """Mutate fields of a stored control and re-push ``controls_define``.

        A ``value=`` field is routed through :meth:`set_control_value` so the
        frontend updates the control in place instead of rebuilding the panel.
        """
        scene = self._scenes[scene_name]
        ctrl = scene._controls.get(ctrl_id)
        if ctrl is None:
            raise KeyError(f"Control {ctrl_id!r} not found")
        if "value" in fields:
            self.set_control_value(ctrl_id, fields.pop("value"), scene_name=scene_name)
        for key, value in fields.items():
            setattr(ctrl, key, value)
        if fields:
            self._push_controls(scene_name)

    def set_control_value(self, cid: str, value: Any, *, scene_name: str = "") -> None:
        """Update a control's value in place and push ``control_update``.

        Args:
            cid: The control id.
            value: The new value (coerced to the control kind's type).
            scene_name: Target scene (default ``""`` = main scene).
        """
        from ._controls import (
            get_control_value,
            set_control_value as _set_control_value,
        )

        scene = self._scenes[scene_name]
        ctrl = scene._controls.get(cid)
        if ctrl is None:
            raise KeyError(f"Control {cid!r} not found")
        _set_control_value(ctrl, value)
        self._push_control_update(scene_name, cid, get_control_value(ctrl))

    def add_dropdown(
        self,
        cid: str,
        *,
        label: str = "",
        tooltip: str = "",
        options: list[str] | None = None,
        value: str = "",
        on_change: Any = None,
        parent_id: str | None = None,
    ) -> str:
        return self._add_scene_dropdown(
            "",
            cid,
            label=label,
            tooltip=tooltip,
            options=options,
            value=value,
            on_change=on_change,
            parent_id=parent_id,
        )

    def _add_scene_dropdown(
        self,
        scene_name: str,
        cid: str,
        *,
        label: str = "",
        tooltip: str = "",
        options: list[str] | None = None,
        value: str = "",
        on_change: Any = None,
        parent_id: str | None = None,
    ) -> str:
        from ._controls import Dropdown

        ctrl = Dropdown(
            id=cid,
            label=label,
            tooltip=tooltip,
            options=options or [],
            value=value,
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
        icon: Icon | None = None,
        icon_only: bool = False,
        tooltip: str = "",
        on_click: Any = None,
        parent_id: str | None = None,
    ) -> str:
        return self._add_scene_button(
            "",
            cid,
            label=label,
            icon=icon,
            icon_only=icon_only,
            tooltip=tooltip,
            on_click=on_click,
            parent_id=parent_id,
        )

    def _add_scene_button(
        self,
        scene_name: str,
        cid: str,
        *,
        label: str = "",
        icon: Icon | None = None,
        icon_only: bool = False,
        tooltip: str = "",
        on_click: Any = None,
        parent_id: str | None = None,
    ) -> str:
        from ._controls import Button

        ctrl = Button(
            id=cid,
            label=label,
            icon=icon,
            icon_only=icon_only,
            tooltip=tooltip,
            on_click=on_click,
            parent_id=parent_id,
        )
        self._scenes[scene_name].add_control(ctrl)
        if on_click is not None:
            self._handler_registry.register(cid, on_click, event="click")
        self._push_controls(scene_name)
        return cid

    def add_file_chooser(
        self,
        cid: str,
        *,
        label: str = "",
        tooltip: str = "",
        value: str = "",
        placeholder: str = "",
        root: str | None = None,
        accept: str = "",
        on_change: Any = None,
        parent_id: str | None = None,
    ) -> str:
        """Add a file chooser control (text field + backend file browser)."""
        return self._add_scene_file_chooser(
            "",
            cid,
            label=label,
            tooltip=tooltip,
            value=value,
            placeholder=placeholder,
            root=root,
            accept=accept,
            on_change=on_change,
            parent_id=parent_id,
        )

    def _add_scene_file_chooser(
        self,
        scene_name: str,
        cid: str,
        *,
        label: str = "",
        tooltip: str = "",
        value: str = "",
        placeholder: str = "",
        root: str | None = None,
        accept: str = "",
        on_change: Any = None,
        parent_id: str | None = None,
    ) -> str:
        from ._controls import FileChooser

        ctrl = FileChooser(
            id=cid,
            label=label,
            tooltip=tooltip,
            value=value,
            placeholder=placeholder,
            root=root,
            accept=accept,
            on_change=on_change,
            parent_id=parent_id,
        )
        self._scenes[scene_name].add_control(ctrl)
        if on_change is not None:
            self._handler_registry.register(cid, on_change)
        self._push_controls(scene_name)
        return cid

    def add_text_field(
        self,
        cid: str,
        *,
        label: str = "",
        value: str = "",
        placeholder: str = "",
        tooltip: str = "",
        on_change: Any = None,
        parent_id: str | None = None,
    ) -> str:
        """Add a single-line text input control."""
        return self._add_scene_text_field(
            "",
            cid,
            label=label,
            value=value,
            placeholder=placeholder,
            tooltip=tooltip,
            on_change=on_change,
            parent_id=parent_id,
        )

    def _add_scene_text_field(
        self,
        scene_name: str,
        cid: str,
        *,
        label: str = "",
        value: str = "",
        placeholder: str = "",
        tooltip: str = "",
        on_change: Any = None,
        parent_id: str | None = None,
    ) -> str:
        from ._controls import TextField

        ctrl = TextField(
            id=cid,
            label=label,
            value=value,
            placeholder=placeholder,
            tooltip=tooltip,
            on_change=on_change,
            parent_id=parent_id,
        )
        self._scenes[scene_name].add_control(ctrl)
        if on_change is not None:
            self._handler_registry.register(cid, on_change)
        self._push_controls(scene_name)
        return cid

    def add_text_area(
        self,
        cid: str,
        *,
        label: str = "",
        value: str = "",
        placeholder: str = "",
        rows: int = 4,
        tooltip: str = "",
        on_change: Any = None,
        parent_id: str | None = None,
    ) -> str:
        """Add a multi-line text input control."""
        return self._add_scene_text_area(
            "",
            cid,
            label=label,
            value=value,
            placeholder=placeholder,
            rows=rows,
            tooltip=tooltip,
            on_change=on_change,
            parent_id=parent_id,
        )

    def _add_scene_text_area(
        self,
        scene_name: str,
        cid: str,
        *,
        label: str = "",
        value: str = "",
        placeholder: str = "",
        rows: int = 4,
        tooltip: str = "",
        on_change: Any = None,
        parent_id: str | None = None,
    ) -> str:
        from ._controls import TextArea

        ctrl = TextArea(
            id=cid,
            label=label,
            value=value,
            placeholder=placeholder,
            rows=rows,
            tooltip=tooltip,
            on_change=on_change,
            parent_id=parent_id,
        )
        self._scenes[scene_name].add_control(ctrl)
        if on_change is not None:
            self._handler_registry.register(cid, on_change)
        self._push_controls(scene_name)
        return cid

    def add_table(
        self,
        cid: str,
        *,
        label: str = "",
        columns: list[str] | None = None,
        rows: list[list[str]] | None = None,
        allow_add_rows: bool = True,
        allow_add_columns: bool = True,
        allow_delete_rows: bool = True,
        tooltip: str = "",
        on_cell_change: Any = None,
        on_row_add: Any = None,
        on_column_add: Any = None,
        on_row_delete: Any = None,
        parent_id: str | None = None,
    ) -> str:
        """Add an editable table (tabular data) control."""
        return self._add_scene_table(
            "",
            cid,
            label=label,
            columns=columns,
            rows=rows,
            allow_add_rows=allow_add_rows,
            allow_add_columns=allow_add_columns,
            allow_delete_rows=allow_delete_rows,
            tooltip=tooltip,
            on_cell_change=on_cell_change,
            on_row_add=on_row_add,
            on_column_add=on_column_add,
            on_row_delete=on_row_delete,
            parent_id=parent_id,
        )

    def _add_scene_table(
        self,
        scene_name: str,
        cid: str,
        *,
        label: str = "",
        columns: list[str] | None = None,
        rows: list[list[str]] | None = None,
        allow_add_rows: bool = True,
        allow_add_columns: bool = True,
        allow_delete_rows: bool = True,
        tooltip: str = "",
        on_cell_change: Any = None,
        on_row_add: Any = None,
        on_column_add: Any = None,
        on_row_delete: Any = None,
        parent_id: str | None = None,
    ) -> str:
        from ._controls import Table

        ctrl = Table(
            id=cid,
            label=label,
            columns=columns or [],
            rows=rows or [],
            allow_add_rows=allow_add_rows,
            allow_add_columns=allow_add_columns,
            allow_delete_rows=allow_delete_rows,
            tooltip=tooltip,
            on_cell_change=on_cell_change,
            on_row_add=on_row_add,
            on_column_add=on_column_add,
            on_row_delete=on_row_delete,
            parent_id=parent_id,
        )
        self._scenes[scene_name].add_control(ctrl)
        if on_cell_change is not None:
            self._handler_registry.register(cid, on_cell_change, event="cell_change")
        if on_row_add is not None:
            self._handler_registry.register(cid, on_row_add, event="row_add")
        if on_column_add is not None:
            self._handler_registry.register(cid, on_column_add, event="column_add")
        if on_row_delete is not None:
            self._handler_registry.register(cid, on_row_delete, event="row_delete")
        self._push_controls(scene_name)
        return cid

    def add_color_picker(
        self,
        cid: str,
        *,
        label: str = "",
        value: str = "#ffffff",
        tooltip: str = "",
        on_change: Any = None,
        parent_id: str | None = None,
    ) -> str:
        """Add a color picker control (native color input)."""
        return self._add_scene_color_picker(
            "",
            cid,
            label=label,
            value=value,
            tooltip=tooltip,
            on_change=on_change,
            parent_id=parent_id,
        )

    def _add_scene_color_picker(
        self,
        scene_name: str,
        cid: str,
        *,
        label: str = "",
        value: str = "#ffffff",
        tooltip: str = "",
        on_change: Any = None,
        parent_id: str | None = None,
    ) -> str:
        from ._controls import ColorPicker

        ctrl = ColorPicker(
            id=cid,
            label=label,
            value=value,
            tooltip=tooltip,
            on_change=on_change,
            parent_id=parent_id,
        )
        self._scenes[scene_name].add_control(ctrl)
        if on_change is not None:
            self._handler_registry.register(cid, on_change)
        self._push_controls(scene_name)
        return cid

    def add_checkbox(
        self,
        cid: str,
        *,
        label: str = "",
        value: bool = False,
        tooltip: str = "",
        on_change: Any = None,
        parent_id: str | None = None,
    ) -> str:
        """Add a checkbox control."""
        return self._add_scene_checkbox(
            "",
            cid,
            label=label,
            value=value,
            tooltip=tooltip,
            on_change=on_change,
            parent_id=parent_id,
        )

    def _add_scene_checkbox(
        self,
        scene_name: str,
        cid: str,
        *,
        label: str = "",
        value: bool = False,
        tooltip: str = "",
        on_change: Any = None,
        parent_id: str | None = None,
    ) -> str:
        from ._controls import Checkbox

        ctrl = Checkbox(
            id=cid,
            label=label,
            value=value,
            tooltip=tooltip,
            on_change=on_change,
            parent_id=parent_id,
        )
        self._scenes[scene_name].add_control(ctrl)
        if on_change is not None:
            self._handler_registry.register(cid, on_change)
        self._push_controls(scene_name)
        return cid

    def add_value_edit(
        self,
        cid: str,
        *,
        label: str = "",
        tooltip: str = "",
        min: float = 0.0,
        max: float = 1.0,
        step: float = 0.1,
        digits: int = 2,
        editable: bool = True,
        value: float | None = None,
        on_change: Any = None,
        parent_id: str | None = None,
    ) -> str:
        """Add a numeric value-edit (stepper) control."""
        return self._add_scene_value_edit(
            "",
            cid,
            label=label,
            tooltip=tooltip,
            min=min,
            max=max,
            step=step,
            digits=digits,
            editable=editable,
            value=value,
            on_change=on_change,
            parent_id=parent_id,
        )

    def _add_scene_value_edit(
        self,
        scene_name: str,
        cid: str,
        *,
        label: str = "",
        tooltip: str = "",
        min: float = 0.0,
        max: float = 1.0,
        step: float = 0.1,
        digits: int = 2,
        editable: bool = True,
        value: float | None = None,
        on_change: Any = None,
        parent_id: str | None = None,
    ) -> str:
        from ._controls import ValueEdit

        ctrl = ValueEdit(
            id=cid,
            label=label,
            tooltip=tooltip,
            min=min,
            max=max,
            step=step,
            digits=digits,
            editable=editable,
            value=value if value is not None else min,
            on_change=on_change,
            parent_id=parent_id,
        )
        self._scenes[scene_name].add_control(ctrl)
        if on_change is not None:
            self._handler_registry.register(cid, on_change)
        self._push_controls(scene_name)
        return cid

    def open_file_chooser(
        self, cid: str, *, scene_name: str = "", path: str | None = None
    ) -> None:
        """Open the file browser dialog for control *cid* (from the backend)."""
        if self._server is None or self._loop is None:
            return
        ctrl = self._scenes[scene_name]._controls.get(cid)
        if ctrl is None:
            return
        start = path if path is not None else (ctrl.value or ctrl.root or "")
        asyncio.run_coroutine_threadsafe(
            self._server.push_raw(
                json.dumps(
                    {
                        "type": "file_browser_show",
                        "scene": scene_name,
                        "control_id": cid,
                        "path": start,
                    }
                )
            ),
            self._loop,
        )

    def close_file_chooser(self, cid: str, *, scene_name: str = "") -> None:
        """Close the file browser dialog for control *cid*."""
        if self._server is None or self._loop is None:
            return
        asyncio.run_coroutine_threadsafe(
            self._server.push_raw(
                json.dumps({"type": "file_browser_close", "control_id": cid})
            ),
            self._loop,
        )

    def _resolve_control(self, cid: str) -> ControlRef | None:
        """Return the panel control or layout view with id *cid*, or ``None``.

        Searches panel controls across all scenes first, then layout view
        controls registered via :meth:`set_layout`.  The result carries the
        owning scene (``""`` for layout views).
        """
        for name, scene in self._scenes.items():
            ctrl = scene._controls.get(cid)
            if ctrl is not None:
                return ControlRef("panel", ctrl, name)
        from .views import iter_control_views

        for layout in self._layouts.values():
            for view in iter_control_views(layout):
                if view.id == cid:
                    return ControlRef("view", view.control, "")
        return None

    async def _handle_file_browser_navigate(self, payload: dict[str, Any]) -> None:
        from ._file_browser import list_directory

        if self._server is None:
            return
        cid = payload.get("control_id")
        path = payload.get("path") or ""
        ref = self._resolve_control(cid) if cid else None
        root = getattr(ref.control, "root", None) if ref is not None else None
        message = list_directory(path, root=root)
        message.update({"type": "file_browser_listing", "control_id": cid})
        await self._server.push_raw(json.dumps(message))

    async def _handle_file_browser_select(
        self, payload: dict[str, Any], event: Any
    ) -> None:
        cid = payload.get("control_id")
        path = payload.get("path") or ""
        if cid and self._resolve_control(cid) is not None:
            self.set_control(cid, path)
        handler = self._handler_registry.get(cid) if cid else None
        if handler is not None:
            try:
                await handler(path, event)
            except Exception:
                import logging

                logging.getLogger(__name__).exception(
                    "Error in file chooser handler for %r", cid
                )

    def add_control_group(
        self,
        gid: str,
        *,
        title: str = "",
        icon: Icon | None = None,
        tooltip: str = "",
        controls: list[str] | None = None,
        position: EAnchor = EAnchor.BOTTOM_RIGHT,
        collapsed: bool = False,
        parent_id: str | None = None,
        on_toggle: Any = None,
    ) -> str:
        """Create a UI control group (sliders/buttons) in the main scene."""
        return self._add_scene_group(
            "",
            gid,
            title=title,
            icon=icon,
            tooltip=tooltip,
            controls=controls,
            position=position,
            collapsed=collapsed,
            parent_id=parent_id,
            on_toggle=on_toggle,
        )

    def _grouped_control_ids(self, scene_name: str) -> set[str]:
        """Return the control ids currently owned by groups in *scene_name*."""
        ids: set[str] = set()
        for group in self._scene_groups.get(scene_name, {}).values():
            for child in getattr(group, "children", ()):
                cid = getattr(child, "id", None)
                if cid is not None:
                    ids.add(cid)
        return ids

    def _remove_group_view(self, scene_name: str, group: View) -> None:
        """Unmount a group view from the global or per-scene overlay."""
        if group in self._global_overlay:
            self._global_overlay.remove(group)
        else:
            overlays = self._scene_overlays.get(scene_name)
            if overlays and group in overlays:
                overlays.remove(group)
        self._injected_overlay_ids.discard(id(group))

    def _add_scene_group(
        self,
        scene_name: str,
        gid: str,
        *,
        title: str = "",
        icon: Icon | None = None,
        tooltip: str = "",
        controls: list[str] | None = None,
        position: EAnchor = EAnchor.BOTTOM_RIGHT,
        collapsed: bool = False,
        parent_id: str | None = None,
        on_toggle: Any = None,
    ) -> str:
        """Create a UI control group as a ``GroupView`` overlay.

        Referenced control ids are resolved to their ``*View`` wrappers (reusing
        the stored ``Control`` objects) and mounted as the group's children.  The
        group is anchored in the overlay — the global overlay for the base scene,
        or the matching ``SceneView`` pane for a named scene — unless
        ``parent_id`` is set, in which case the frontend attaches it to that 3D
        entity.
        """
        from .views import GroupView, control_to_view

        scene = self._scenes[scene_name]
        children: list[View] = []
        for cid in controls or []:
            ctrl = scene._controls.get(cid)
            if ctrl is None:
                continue
            children.append(control_to_view(ctrl))

        group = GroupView(
            title,
            children,
            position=position,
            collapsed=collapsed,
            icon=icon,
            parent_id=parent_id,
        )
        if on_toggle is not None:
            self._handler_registry.register(gid, on_toggle, event="toggle")
        self._scene_groups.setdefault(scene_name, {})[gid] = group

        if parent_id is not None or scene_name != "":
            self._scene_overlays.setdefault(scene_name, []).append(group)
            self._injected_overlay_ids.add(id(group))
        else:
            self._global_overlay.append(group)

        self._sync_overlays()
        self._push_controls(scene_name)
        return gid

    def remove_control(self, cid: str) -> None:
        self._remove_scene_control("", cid)

    def _remove_scene_control(self, scene_name: str, cid: str) -> None:
        self._handler_registry.unregister(cid)
        self._scenes[scene_name].remove_control(cid)
        self._push_controls(scene_name)

    def remove_control_group(self, gid: str) -> None:
        """Remove a UI control group from the main scene."""
        self._remove_scene_group("", gid)

    def _remove_scene_group(self, scene_name: str, gid: str) -> None:
        groups = self._scene_groups.get(scene_name, {})
        group = groups.pop(gid, None)
        if group is None:
            return
        self._handler_registry.unregister(gid)
        self._remove_group_view(scene_name, group)
        self._sync_overlays()
        self._push_controls(scene_name)

    def clear_controls(self) -> None:
        """Remove all UI panel controls (and their handlers) from the main scene.

        Only panel controls are removed; entity object-interaction handlers
        (``on_interaction`` / ``ActPoint``) are left intact.
        """
        self._clear_scene_controls("")

    def _clear_scene_controls(self, scene_name: str) -> None:
        from ._controls import HandlerOrigin

        self._handler_registry.clear(origin=HandlerOrigin.CONTROL)
        self._scenes[scene_name].clear_controls()
        for group in list(self._scene_groups.pop(scene_name, {}).values()):
            self._remove_group_view(scene_name, group)
        self._scene_overlays.pop(scene_name, None)
        self._sync_overlays()
        self._push_controls_clear(scene_name)

    # ── Banners ─────────────────────────────────────────────

    def _next_banner_id(self) -> str:
        """Return a fresh, unique banner id."""
        self._banner_counter += 1
        return f"banner_{self._banner_counter}"

    def _register_banner(
        self,
        text: str,
        *,
        id: str | None,
        title: str,
        align_x: float,
        align_y: float,
        auto_hide: bool,
        dismissable: bool,
        controls: list[Any] | None,
        on_close: Any,
        scene_name: str | None,
    ) -> Any:
        """Create, store, and register a banner; return it (un-pushed)."""
        from ._banner import Banner

        if id is None:
            id = self._next_banner_id()
        else:
            for scoped in self._banners.values():
                if id in scoped:
                    raise ValueError(f"Banner id {id!r} is already in use")

        ctrl_list = list(controls or [])
        banner = Banner(
            id=id,
            text=text,
            title=title,
            align_x=align_x,
            align_y=align_y,
            auto_hide=auto_hide,
            dismissable=dismissable,
            controls=ctrl_list,
            on_close=on_close,
        )
        for ctrl in ctrl_list:
            if getattr(ctrl, "on_click", None) is not None:
                self._handler_registry.register(ctrl.id, ctrl.on_click, event="click")
            elif getattr(ctrl, "on_change", None) is not None:
                self._handler_registry.register(ctrl.id, ctrl.on_change, event="change")
        if on_close is not None:
            self._handler_registry.register(id, on_close, event="close")
        self._banners.setdefault(scene_name, {})[id] = banner
        return banner

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
        """Show a banner/dialog and return its id.

        A global banner (``scene_name=None``) spans the whole viewport; a
        per-scene banner (``scene_name="<name>"``) is shown inside every pane
        displaying that scene.  ``controls`` is a list of :class:`Button` /
        :class:`Slider` / :class:`Dropdown` objects (the same controls usable
        in a control group) rendered as the banner's options; their
        ``on_click`` / ``on_change`` handlers are registered automatically.
        """
        banner = self._register_banner(
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
        self._push_banner(banner, scene_name)
        return banner.id

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
        from ._controls import Button

        bid = self._next_banner_id()
        buttons = [Button(id=f"{bid}_ok", label=ok_label, on_click=on_ok)]
        return self.show_banner(
            text,
            id=bid,
            title=title,
            align_x=align_x,
            align_y=align_y,
            auto_hide=True,
            dismissable=dismissable,
            controls=buttons,
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
        from ._controls import Button

        bid = self._next_banner_id()
        buttons = [
            Button(id=f"{bid}_yes", label=yes_label, on_click=on_yes),
            Button(id=f"{bid}_no", label=no_label, on_click=on_no),
            Button(id=f"{bid}_cancel", label=cancel_label, on_click=on_cancel),
        ]
        return self.show_banner(
            text,
            id=bid,
            title=title,
            align_x=align_x,
            align_y=align_y,
            auto_hide=True,
            dismissable=dismissable,
            controls=buttons,
            scene_name=scene_name,
        )

    def _unregister_banner(self, banner: Any) -> None:
        """Unregister a banner's control handlers and ``on_close`` handler."""
        for ctrl in banner.controls:
            self._handler_registry.unregister(ctrl.id)
        self._handler_registry.unregister(banner.id, "close")

    def remove_banner(self, banner_id: str, *, scene_name: str | None = None) -> None:
        """Remove a banner by id (and unregister its handlers)."""
        scoped = self._banners.get(scene_name, {})
        banner = scoped.get(banner_id)
        if banner is None:
            return
        self._unregister_banner(banner)
        del scoped[banner_id]
        self._push_banner_remove(banner_id, scene_name)

    def clear_banners(self, *, scene_name: str | None = None) -> None:
        """Remove all banners in a scope (or globally when ``scene_name=None``)."""
        scoped = self._banners.pop(scene_name, {})
        for banner in scoped.values():
            self._unregister_banner(banner)
        self._push_banner_clear(scene_name)

    def _push_banner(self, banner: Any, scene_name: str | None) -> None:
        from ._banner import serialize_banner

        if self._server is None or self._loop is None:
            return
        asyncio.run_coroutine_threadsafe(
            self._server.push_raw(
                json.dumps(serialize_banner(banner, scene=scene_name))
            ),
            self._loop,
        )

    def _push_banner_remove(self, banner_id: str, scene_name: str | None) -> None:
        from ._banner import serialize_banner_remove

        if self._server is None or self._loop is None:
            return
        asyncio.run_coroutine_threadsafe(
            self._server.push_raw(
                json.dumps(serialize_banner_remove(banner_id, scene=scene_name))
            ),
            self._loop,
        )

    def _push_banner_clear(self, scene_name: str | None) -> None:
        from ._banner import serialize_banner_clear

        if self._server is None or self._loop is None:
            return
        asyncio.run_coroutine_threadsafe(
            self._server.push_raw(json.dumps(serialize_banner_clear(scene=scene_name))),
            self._loop,
        )

    async def _push_banner_async(self, banner: Any, scene_name: str | None) -> None:
        from ._banner import serialize_banner

        if self._server is None:
            return
        await self._server.push_raw(
            json.dumps(serialize_banner(banner, scene=scene_name))
        )

    async def _push_banner_remove_async(
        self, banner_id: str, scene_name: str | None
    ) -> None:
        from ._banner import serialize_banner_remove

        if self._server is None:
            return
        await self._server.push_raw(
            json.dumps(serialize_banner_remove(banner_id, scene=scene_name))
        )

    async def _push_banner_clear_async(self, scene_name: str | None) -> None:
        from ._banner import serialize_banner_clear

        if self._server is None:
            return
        await self._server.push_raw(
            json.dumps(serialize_banner_clear(scene=scene_name))
        )

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
        """Awaitable :meth:`show_banner` (see its docs).

        Awaits the ``banner_define`` push so the banner is visible before the
        caller proceeds; safe from a handler (on ``self._loop``) or from
        ``init()`` / ``cleanup()`` (user loop).
        """
        banner = self._register_banner(
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
        await self._on_server_loop(lambda: self._push_banner_async(banner, scene_name))
        return banner.id

    async def remove_banner_async(
        self, banner_id: str, *, scene_name: str | None = None
    ) -> None:
        """Awaitable :meth:`remove_banner`."""
        scoped = self._banners.get(scene_name, {})
        banner = scoped.get(banner_id)
        if banner is None:
            return
        self._unregister_banner(banner)
        del scoped[banner_id]
        await self._on_server_loop(
            lambda: self._push_banner_remove_async(banner_id, scene_name)
        )

    async def clear_banners_async(self, *, scene_name: str | None = None) -> None:
        """Awaitable :meth:`clear_banners`."""
        scoped = self._banners.pop(scene_name, {})
        for banner in scoped.values():
            self._unregister_banner(banner)
        await self._on_server_loop(lambda: self._push_banner_clear_async(scene_name))

    # ── Dialogs ─────────────────────────────────────────────

    def _next_dialog_id(self) -> str:
        """Return a fresh, unique dialog id."""
        self._dialog_counter += 1
        return f"dialog_{self._dialog_counter}"

    def _register_dialog(
        self,
        content: View,
        *,
        id: str | None,
        title: str,
        align_x: float,
        align_y: float,
        dismissable: bool,
        on_close: Any,
        scene_name: str | None,
    ) -> Any:
        """Create, store, and register a dialog; return it (un-pushed)."""
        from ._dialog import Dialog

        if not isinstance(content, View):
            raise TypeError(f"content must be a View, got {type(content).__name__}")

        if id is None:
            id = self._next_dialog_id()
        else:
            for scoped in self._dialogs.values():
                if id in scoped:
                    raise ValueError(f"Dialog id {id!r} is already in use")

        dialog = Dialog(
            id=id,
            content=content,
            title=title,
            align_x=align_x,
            align_y=align_y,
            dismissable=dismissable,
            on_close=on_close,
        )
        # Register the content's control-view handlers, then the close callback.
        self._register_view_handlers(content)
        if on_close is not None:
            self._handler_registry.register(id, on_close, event="close")
        self._dialogs.setdefault(scene_name, {})[id] = dialog
        return dialog

    def show_dialog(
        self,
        content: View,
        *,
        id: str | None = None,
        title: str = "",
        align_x: float = 0.5,
        align_y: float = 0.5,
        dismissable: bool = True,
        on_close: Any = None,
        scene_name: str | None = None,
    ) -> str:
        """Show a dialog and return its id.

        A global dialog (``scene_name=None``) spans the whole viewport; a
        per-scene dialog (``scene_name="<name>"``) is shown inside every pane
        displaying that scene.  ``content`` is any :class:`View` (e.g. a
        :class:`StackView` of ``*View`` control wrappers) rendered inside the
        dialog body; its control-view handlers are registered automatically.
        Closing the dialog (the ✕, or a backend ``remove_dialog``) fires
        ``on_close`` on the server loop.  With ``dismissable=False`` the dialog
        is modal — a dimmed backdrop blocks the scene and there is no ✕ (close
        it via a control in ``content`` or ``remove_dialog``).
        """
        dialog = self._register_dialog(
            content,
            id=id,
            title=title,
            align_x=align_x,
            align_y=align_y,
            dismissable=dismissable,
            on_close=on_close,
            scene_name=scene_name,
        )
        self._push_dialog(dialog, scene_name)
        return dialog.id

    def _unregister_dialog(self, dialog: Any) -> None:
        """Unregister a dialog's content control handlers and ``on_close``."""
        from .views import iter_control_views

        for view in iter_control_views(dialog.content):
            self._handler_registry.unregister(view.id)
        self._handler_registry.unregister(dialog.id, "close")

    def remove_dialog(self, dialog_id: str, *, scene_name: str | None = None) -> None:
        """Remove a dialog by id (and unregister its handlers)."""
        scoped = self._dialogs.get(scene_name, {})
        dialog = scoped.get(dialog_id)
        if dialog is None:
            return
        self._unregister_dialog(dialog)
        del scoped[dialog_id]
        self._push_dialog_remove(dialog_id, scene_name)

    def clear_dialogs(self, *, scene_name: str | None = None) -> None:
        """Remove all dialogs in a scope (or globally when ``scene_name=None``)."""
        scoped = self._dialogs.pop(scene_name, {})
        for dialog in scoped.values():
            self._unregister_dialog(dialog)
        self._push_dialog_clear(scene_name)

    def _push_dialog(self, dialog: Any, scene_name: str | None) -> None:
        from ._dialog import serialize_dialog

        if self._server is None or self._loop is None:
            return
        asyncio.run_coroutine_threadsafe(
            self._server.push_raw(
                json.dumps(serialize_dialog(dialog, scene=scene_name))
            ),
            self._loop,
        )

    def _push_dialog_remove(self, dialog_id: str, scene_name: str | None) -> None:
        from ._dialog import serialize_dialog_remove

        if self._server is None or self._loop is None:
            return
        asyncio.run_coroutine_threadsafe(
            self._server.push_raw(
                json.dumps(serialize_dialog_remove(dialog_id, scene=scene_name))
            ),
            self._loop,
        )

    def _push_dialog_clear(self, scene_name: str | None) -> None:
        from ._dialog import serialize_dialog_clear

        if self._server is None or self._loop is None:
            return
        asyncio.run_coroutine_threadsafe(
            self._server.push_raw(json.dumps(serialize_dialog_clear(scene=scene_name))),
            self._loop,
        )

    async def _push_dialog_async(self, dialog: Any, scene_name: str | None) -> None:
        from ._dialog import serialize_dialog

        if self._server is None:
            return
        await self._server.push_raw(
            json.dumps(serialize_dialog(dialog, scene=scene_name))
        )

    async def _push_dialog_remove_async(
        self, dialog_id: str, scene_name: str | None
    ) -> None:
        from ._dialog import serialize_dialog_remove

        if self._server is None:
            return
        await self._server.push_raw(
            json.dumps(serialize_dialog_remove(dialog_id, scene=scene_name))
        )

    async def _push_dialog_clear_async(self, scene_name: str | None) -> None:
        from ._dialog import serialize_dialog_clear

        if self._server is None:
            return
        await self._server.push_raw(
            json.dumps(serialize_dialog_clear(scene=scene_name))
        )

    async def show_dialog_async(
        self,
        content: View,
        *,
        id: str | None = None,
        title: str = "",
        align_x: float = 0.5,
        align_y: float = 0.5,
        dismissable: bool = True,
        on_close: Any = None,
        scene_name: str | None = None,
    ) -> str:
        """Awaitable :meth:`show_dialog` (see its docs).

        Awaits the ``dialog_define`` push so the dialog is visible before the
        caller proceeds; safe from a handler (on ``self._loop``) or from
        ``init()`` / ``cleanup()`` (user loop).
        """
        dialog = self._register_dialog(
            content,
            id=id,
            title=title,
            align_x=align_x,
            align_y=align_y,
            dismissable=dismissable,
            on_close=on_close,
            scene_name=scene_name,
        )
        await self._on_server_loop(lambda: self._push_dialog_async(dialog, scene_name))
        return dialog.id

    async def remove_dialog_async(
        self, dialog_id: str, *, scene_name: str | None = None
    ) -> None:
        """Awaitable :meth:`remove_dialog`."""
        scoped = self._dialogs.get(scene_name, {})
        dialog = scoped.get(dialog_id)
        if dialog is None:
            return
        self._unregister_dialog(dialog)
        del scoped[dialog_id]
        await self._on_server_loop(
            lambda: self._push_dialog_remove_async(dialog_id, scene_name)
        )

    async def clear_dialogs_async(self, *, scene_name: str | None = None) -> None:
        """Awaitable :meth:`clear_dialogs`."""
        scoped = self._dialogs.pop(scene_name, {})
        for dialog in scoped.values():
            self._unregister_dialog(dialog)
        await self._on_server_loop(lambda: self._push_dialog_clear_async(scene_name))

    # ── Editor ─────────────────────────────────────────────

    def open_editor(
        self,
        cid: str,
        *,
        label: str = "",
        value: str = "",
        on_close: Any = None,
    ) -> str:
        """Open a transient multi-line text editor in the viewer overlay.

        When the editor is closed, *on_close* (an async ``(text, event)``
        callable) is invoked on the server loop with the edited text, or
        ``None`` when the edit is discarded (✕).  The editor is one-shot: the
        handler is consumed after it runs.
        """
        self._handler_registry.register(cid, on_close, event="close")
        self._push_editor_define(cid, label=label, value=value)
        return cid

    def _push_editor_define(self, cid: str, *, label: str, value: str) -> None:
        """Push the ``editor_define`` message that opens the editor."""
        if self._server is None or self._loop is None:
            return
        message = {
            "type": "editor_define",
            "id": cid,
            "label": label,
            "value": value,
        }
        asyncio.run_coroutine_threadsafe(
            self._server.push_raw(json.dumps(message)), self._loop
        )

    def _push_controls(self, scene_name: str = "") -> None:
        """Push the scene's orphan controls (grouped controls ride the overlay)."""
        if self._server is None or self._loop is None:
            return
        from ._controls import serialize_controls

        scene = self._scenes[scene_name]
        grouped = self._grouped_control_ids(scene_name)
        orphan_map = {
            cid: c for cid, c in scene._controls.items() if cid not in grouped
        }
        message = serialize_controls([], orphan_map)
        message["scene"] = scene_name
        asyncio.run_coroutine_threadsafe(
            self._server.push_raw(json.dumps(message)), self._loop
        )

    def _push_control_update(self, scene_name: str, cid: str, value: Any) -> None:
        """Push a lightweight ``control_update`` message for one control."""
        if self._server is None or self._loop is None:
            return
        message = {
            "type": "control_update",
            "scene": scene_name,
            "id": cid,
            "value": value,
        }
        asyncio.run_coroutine_threadsafe(
            self._server.push_raw(json.dumps(message)), self._loop
        )

    async def _push_controls_async(self, scene_name: str = "") -> None:
        """Async variant — must be called from the server's event loop."""
        if self._server is None:
            return
        from ._controls import serialize_controls

        scene = self._scenes.get(scene_name, self._scenes[""])
        grouped = self._grouped_control_ids(scene_name)
        orphan_map = {
            cid: c for cid, c in scene._controls.items() if cid not in grouped
        }
        message = serialize_controls([], orphan_map)
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

    async def _dispatch_event(
        self, target: str | None, event: str, data: Any, browser_id: Any
    ) -> None:
        """Dispatch ``(target, event)`` to its handler with ``data``.

        The single lookup-and-invoke tail shared by control, banner, and editor
        events: the handler is awaited as ``handler(data, ControlEvent)`` and
        any exception is logged without propagating.
        """
        from ._controls import ControlEvent

        handler = self._handler_registry.get(target, event) if target else None
        if handler is None:
            return
        try:
            await handler(data, ControlEvent(browser_id=browser_id))
        except Exception:
            import logging

            logging.getLogger(__name__).exception(
                "Error in %r handler for %r", event, target
            )

    async def _dispatch_control_event(
        self, msg_type: str, payload: dict[str, Any]
    ) -> None:
        """Handle an incoming control event from the frontend."""
        from ._controls import (
            ControlEvent,
            TableCellChange,
            TableColumnAdd,
            TableRowAdd,
            TableRowsDelete,
        )

        browser_id = payload.get("browser_id")
        event = ControlEvent(browser_id=browser_id)
        if msg_type in ("banner_closed", "editor_closed", "close"):
            target = payload.get("id") or payload.get("control_id")
            value = payload.get("value")
            if msg_type == "editor_closed":
                value = payload.get("text")
            handler = self._handler_registry.get(target, "close") if target else None
            if handler is not None:
                self._handler_registry.unregister(target, "close")
                try:
                    await handler(value, event)
                except Exception:
                    import logging

                    logging.getLogger(__name__).exception(
                        "Error in close handler for %r", target
                    )
            return

        if msg_type == "file_browser_navigate":
            await self._handle_file_browser_navigate(payload)
            return
        if msg_type == "file_browser_select":
            await self._handle_file_browser_select(payload, event)
            return

        if msg_type == "control:cell_change":
            cid = payload.get("control_id")
            handler = self._handler_registry.get(cid, "cell_change") if cid else None
            if handler is not None:
                try:
                    nested = payload.get("value")
                    table_payload = nested if isinstance(nested, dict) else payload
                    await handler(
                        TableCellChange(
                            row=int(table_payload.get("row", 0)),
                            col=int(table_payload.get("col", 0)),
                            value=str(table_payload.get("value", "")),
                        ),
                        event,
                    )
                except Exception:
                    import logging

                    logging.getLogger(__name__).exception(
                        "Error in table cell handler for %r", cid
                    )
            return

        if msg_type == "control:row_add":
            cid = payload.get("control_id")
            handler = self._handler_registry.get(cid, "row_add") if cid else None
            if handler is not None:
                try:
                    nested = payload.get("value")
                    table_payload = nested if isinstance(nested, dict) else payload
                    await handler(
                        TableRowAdd(
                            row=int(table_payload.get("row", 0)),
                            values=[
                                str(v) for v in (table_payload.get("values") or [])
                            ],
                        ),
                        event,
                    )
                except Exception:
                    import logging

                    logging.getLogger(__name__).exception(
                        "Error in table row handler for %r", cid
                    )
            return

        if msg_type == "control:column_add":
            cid = payload.get("control_id")
            handler = self._handler_registry.get(cid, "column_add") if cid else None
            if handler is not None:
                try:
                    nested = payload.get("value")
                    table_payload = nested if isinstance(nested, dict) else payload
                    await handler(
                        TableColumnAdd(
                            col=int(table_payload.get("col", 0)),
                            header=str(table_payload.get("header", "")),
                            values=[
                                str(v) for v in (table_payload.get("values") or [])
                            ],
                        ),
                        event,
                    )
                except Exception:
                    import logging

                    logging.getLogger(__name__).exception(
                        "Error in table column handler for %r", cid
                    )
            return

        if msg_type == "control:row_delete":
            cid = payload.get("control_id")
            handler = self._handler_registry.get(cid, "row_delete") if cid else None
            if handler is not None:
                try:
                    nested = payload.get("value")
                    table_payload = nested if isinstance(nested, dict) else payload
                    await handler(
                        TableRowsDelete(
                            rows=[int(r) for r in (table_payload.get("rows") or [])],
                        ),
                        event,
                    )
                except Exception:
                    import logging

                    logging.getLogger(__name__).exception(
                        "Error in table row delete handler for %r", cid
                    )
            return

        cid = payload.get("control_id")
        if msg_type == "control:press":
            event_name, data = "press", payload.get("value")
        elif msg_type == "control:release":
            event_name, data = "release", payload.get("value")
        elif msg_type == "control:click":
            event_name, data = "click", None
        elif msg_type == "control:group_toggle":
            event_name, data = "toggle", payload.get("value")
        else:
            event_name, data = "change", payload.get("value")
        await self._dispatch_event(cid, event_name, data, browser_id)

    async def _on_client_connect(self, remote_addr: str) -> None:
        """Push controls state when a new client connects.

        The comprehensive connection summary (with browser_id, page_token,
        viewer_name, and IP) is printed by VizServer._print_ws_connected
        after the browser's ``ready`` WebSocket message arrives.
        """
        # Push controls for the main scene initially (scene-specific push happens
        # after the ready message tells us which scene the client wants)
        await self._push_controls_async("")

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
    ) -> str:
        scene = self._scenes[scene_name]
        if animation is not None:
            from pytanga.viz.export._animated_figure import (
                render_export_animated_html,
            )

            return render_export_animated_html(
                animation.to_dict(),
                scene_config=scene.config.to_dict(),
                anim_style=anim_style.to_dict() if anim_style is not None else None,
                title=self._title,
            )
        from pytanga.viz.export._html import render_snapshot

        objects = scene.full_state(styles_map=scene.styles.kind)
        return render_snapshot(objects=objects, scene_config=scene.config.to_dict())

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
    ) -> None:
        from pathlib import Path

        html = self._render_snapshot_html(
            scene_name, animation=animation, anim_style=anim_style
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
    ) -> None:
        """Export the current scene as a self-contained HTML file.

        Pass *animation* (an ``AnimationRecording``) to export an animated
        snapshot instead of a static one.
        """
        self._export_scene_snapshot(
            "", path, overwrite=overwrite, animation=animation, anim_style=anim_style
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
    ) -> str:
        from pytanga.viz._figure import FigureConfig
        from pytanga.viz._styles import FigureStyle

        scene = self._scenes[scene_name]
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
            )
        from pytanga.viz.export._figure_html import render_figure

        objects = scene.full_state(styles_map=scene.styles.kind)
        return render_figure(
            objects,
            scene.config.to_dict(),
            resolved.to_dict(),
            fig_config.to_dict(),
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
    ) -> str | None:
        from pathlib import Path

        html = self._render_figure_html(
            scene_name, style=style, animation=animation, anim_style=anim_style
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
    ) -> str | None:
        """Export the current scene as an HTML snippet (or return the string).

        Pass *animation* (an ``AnimationRecording``) to export an animated
        figure instead of a static one.
        """
        return self._export_scene_figure(
            "",
            path,
            style=style,
            overwrite=overwrite,
            animation=animation,
            anim_style=anim_style,
        )

    def _export_scene_glb(
        self, scene_name: str, path: Any, *, overwrite: bool = False
    ) -> None:
        from pathlib import Path

        from pytanga.viz.export._gltf import build_glb

        scene = self._scenes[scene_name]
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

        scene = self._scenes[scene_name]
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
        return self._scenes[""].styles

    @property
    def main_scene(self) -> Scene:
        """The underlying main :class:`Scene` instance (backward compat)."""
        return self._scenes[""]

    @property
    def url(self) -> str:
        """The HTTP URL of the viewer."""
        return f"http://{self._host}:{self._port}"
