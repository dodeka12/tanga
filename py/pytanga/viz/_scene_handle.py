# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Per-scene proxy handle for the :class:`Visualizer`.

A :class:`VizSceneHandle` is created by :meth:`Visualizer.scene` and exposes
the same entity, label, control, animation, and title/annotation API as
``Visualizer``, but all operations affect only the target scene.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Iterator, Sequence

if TYPE_CHECKING:
    from ._styles import AnnotationStyle, LabelStyle, ObjVizStyle, TextureLabelStyle
    from ._viz_styles import VizStyles
    from .visualizer import Visualizer

from ._jupyter import _JupyterDisplayMixin
from ._keys import KeyModifier
from ._timeline import Timeline
from ._types import SceneEntity
from .scene import Scene


class VizSceneHandle(_JupyterDisplayMixin):
    """Proxy targeting a specific named scene within a :class:`Visualizer`.

    Exposes the same entity, label, control, animation, and title/annotation
    API as ``Visualizer``, but all operations affect only the target scene.
    Created by :meth:`Visualizer.scene`.

    Supports Jupyter inline display via :meth:`_repr_html_`, embedding an
    iframe that points to the scene's URL.
    """

    def __init__(self, visualizer: Visualizer, scene_name: str) -> None:
        self._viz = visualizer
        self._name = scene_name
        self._viewer_name: str | None = None

    # ── _JupyterDisplayMixin contract ──────────────────────

    @property
    def _server(self) -> Any:
        return self._viz._server

    # ── Scene access ────────────────────────────────────────

    def _scene(self) -> Scene:
        """Return the underlying Scene object."""
        return self._viz._layout.scene(self._name)

    @property
    def name(self) -> str:
        """The scene name (URL-path-friendly)."""
        return self._name

    @property
    def url(self) -> str:
        """The HTTP URL of this scene."""
        base = self._viz.url
        if self._name:
            return f"{base}/{self._name}"
        return base

    @property
    def scene(self) -> Scene:
        """The underlying :class:`Scene` instance."""
        return self._scene()

    @property
    def styles(self) -> "VizStyles":
        """This scene's :class:`VizStyles` holder (its own copy)."""
        return self._scene().styles

    # ── Entity management ───────────────────────────────────

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
        tex_label_style: TextureLabelStyle | None = None,
        parent_id: str | None = None,
        attach_to: str | None = None,
    ) -> str:
        """Add an entity, operator, MV, or label to this scene.

        Returns the entity ID as a ``str``.

        See :meth:`Visualizer.add` for full documentation.
        """
        return self._scene().add_viz(
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
        tex_label_style: TextureLabelStyle | None = None,
        parent_id: str | None = None,
        attach_to: str | None = None,
    ) -> Any:
        """Like :meth:`add`, but returns a :class:`VizObjectRef` for the node."""
        from ._object_ref import VizObjectRef

        eid = self._scene().add_viz(
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
        return VizObjectRef(self, self._scene().get_node(eid))

    def add_group(self, name: str | None = None) -> Any:
        """Create a scene-graph group in this scene and return a :class:`VizObjectRef`."""
        from ._object_ref import VizObjectRef

        group = self._scene().add_group(name)
        return VizObjectRef(self, group)

    def update_style(self, entity_id: str, style: ObjVizStyle) -> None:
        """Update the style of an existing entity in this scene."""
        self._scene().update(entity_id, style=style)

    def update(self, entity_id: str, **properties: Any) -> None:
        """Update rendering properties of an existing entity."""
        self._scene().update(entity_id, **properties)

    def update_entity(self, entity_id: str, obj: SceneEntity) -> None:
        """Replace the geometry for an existing entity."""
        entity = self._viz._resolve(obj)
        self._scene().update_entity(entity_id, entity)

    def update_label(
        self,
        object_id: str,
        *,
        text: str | None = None,
        style: LabelStyle | None = None,
    ) -> None:
        """Update a label's text and/or style."""
        self._scene().update_label(object_id, text=text, style=style)

    def get_label_ids(self, entity_id: str) -> list[str]:
        """Return the IDs of all labels attached to *entity_id* in this scene."""
        return self._scene().get_label_ids(entity_id)

    def remove(self, entity_id: str) -> None:
        """Remove an entity from this scene."""
        self._scene().remove(entity_id)

    def clear(self, *, add_axes: bool = False, add_grid: bool = False) -> None:
        """Remove all entities from this scene.

        By default the scene is left empty.  Set ``add_axes`` / ``add_grid``
        to ``True`` to re-add the default coordinate axes / grid afterward
        (subject to the visualizer's ``add_default_axes`` / ``add_default_grid``
        constructor flags).
        """
        self._scene().clear()
        if add_axes or add_grid:
            self._viz._default_objects_added.discard(self._name)
            self._viz._add_default_scene_objects(
                self._name, add_axes=add_axes, add_grid=add_grid
            )

    def __enter__(self) -> "VizSceneHandle":
        """Reset this scene and show it immediately on entry."""
        self._viz._reset_scene(self._name)
        self.show()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Flush this scene on exit (any exception still propagates)."""
        self.flush()
        return None

    def flush(self, *, fit_camera: bool = False, wait: bool = False) -> None:
        """Schedule a scene update on the server's event loop (thread-safe).

        If *fit_camera* is ``True``, the frontend will auto‑adjust the
        camera to encompass all entities after the flush.

        If *wait* is ``True``, block until the flush has been processed.  This
        is intended for plain synchronous scripts; see
        :meth:`~pytanga.viz.Visualizer.flush` for the caveats.
        """
        self._viz._flush_scene(self._name, fit_camera=fit_camera, wait=wait)

    async def flush_async(self, *, fit_camera: bool = False) -> None:
        """Awaitable flush for this scene (see :meth:`~pytanga.viz.Visualizer.flush_async`)."""
        await self._viz.flush_async(fit_camera=fit_camera, scene=self._name)

    # ── Title & annotation ──────────────────────────────────

    def set_title(self, title: str) -> None:
        """Update the viewport title overlay for this scene."""
        self._viz._set_scene_title(self._name, title)

    def set_camera(self, camera: Any) -> None:
        """Update the camera configuration for this scene at runtime."""
        self._viz.set_camera(camera, scene_name=self._name)

    @property
    def space_dim(self) -> int:
        """The scene's current space dimension (``2`` or ``3``)."""
        return self._scene().config.space_dim

    @space_dim.setter
    def space_dim(self, value: int) -> None:
        self._viz.set_space_dim(value, scene_name=self._name)

    def set_space_dim(self, space_dim: int, camera: Any = None) -> None:
        """Set the space dimension (and optionally the camera) for this scene."""
        self._viz.set_space_dim(space_dim, scene_name=self._name, camera=camera)

    def set_annotation(
        self, text: str | None, *, style: AnnotationStyle | None = None
    ) -> None:
        """Set or update the markdown annotation panel for this scene."""
        self._viz._set_scene_annotation(self._name, text, style=style)

    # ── Animation ───────────────────────────────────────────

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
        """Animate an entity in this scene."""
        self._viz._animate_scene_entity(
            self._name,
            entity_id,
            position=position,
            rotation=rotation,
            opacity=opacity,
            scale=scale,
            duration=duration,
            easing=easing,
        )

    def timeline(self) -> Timeline:
        """Create a :class:`Timeline` targeting this scene."""
        return self._viz._scene_timeline(self._name)

    def enable_server_stop_key(
        self,
        enabled: bool = True,
        key: str = "q",
        modifiers: list[KeyModifier] = [KeyModifier.CTRL],
    ) -> None:
        """Enable or disable a browser-triggered full-server stop key for this scene.

        When enabled and pressed in this scene's tab, it sets the global
        shutdown event so ``wait()`` returns and every ``animate()`` loop ends.
        """
        self._viz._set_server_stop_key(
            self._name, enabled=enabled, key=key, modifiers=modifiers
        )

    def animate(
        self,
        *,
        fps: float = 60.0,
        stop_key: str | None = "q",
        stop_modifiers: Sequence[KeyModifier | str] | None = None,
        auto_clear: bool = False,
    ) -> Iterator[float]:
        """Yield once per animation frame until this scene is interrupted.

        See :meth:`Visualizer.animate`; the loop is scoped to this scene.
        """
        return self._viz.animate(
            fps=fps,
            stop_key=stop_key,
            stop_modifiers=stop_modifiers,
            auto_clear=auto_clear,
            scene_name=self._name,
        )

    def interrupted(self) -> bool:
        """True once this scene has been interrupted (browser or terminal)."""
        return self._viz.interrupted(scene_name=self._name)

    def sleep_ms(self, milliseconds: int) -> bool:
        """Sleep, returning early if this scene is interrupted.

        See :meth:`Visualizer.sleep_ms`.
        """
        return self._viz.sleep_ms(milliseconds, scene_name=self._name)

    # ── Interactive Controls ─────────────────────────────────

    def open_file_chooser(self, cid: str, *, path: str | None = None) -> None:
        """Open the file browser dialog for control *cid*."""
        self._viz.open_file_chooser(cid, scene_name=self._name, path=path)

    def close_file_chooser(self, cid: str) -> None:
        """Close the file browser dialog for control *cid*."""
        self._viz.close_file_chooser(cid, scene_name=self._name)

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
        controls: Any = None,
        on_close: Any = None,
    ) -> str:
        """Show a banner scoped to this scene (see :meth:`Visualizer.show_banner`)."""
        return self._viz.show_banner(
            text,
            id=id,
            title=title,
            align_x=align_x,
            align_y=align_y,
            auto_hide=auto_hide,
            dismissable=dismissable,
            controls=controls,
            on_close=on_close,
            scene_name=self._name,
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
    ) -> str:
        """Show an acknowledge banner scoped to this scene (see :meth:`Visualizer.alert`)."""
        return self._viz.alert(
            text,
            title=title,
            ok_label=ok_label,
            on_ok=on_ok,
            align_x=align_x,
            align_y=align_y,
            dismissable=dismissable,
            scene_name=self._name,
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
    ) -> str:
        """Show a yes/no/cancel banner scoped to this scene (see :meth:`Visualizer.confirm`)."""
        return self._viz.confirm(
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
            scene_name=self._name,
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
        controls: Any = None,
        on_close: Any = None,
    ) -> str:
        """Awaitable :meth:`show_banner` scoped to this scene."""
        return await self._viz.show_banner_async(
            text,
            id=id,
            title=title,
            align_x=align_x,
            align_y=align_y,
            auto_hide=auto_hide,
            dismissable=dismissable,
            controls=controls,
            on_close=on_close,
            scene_name=self._name,
        )

    def remove_banner(self, banner_id: str) -> None:
        """Remove a banner from this scene."""
        self._viz.remove_banner(banner_id, scene_name=self._name)

    async def remove_banner_async(self, banner_id: str) -> None:
        """Awaitable :meth:`remove_banner`."""
        await self._viz.remove_banner_async(banner_id, scene_name=self._name)

    def clear_banners(self) -> None:
        """Remove all banners from this scene."""
        self._viz.clear_banners(scene_name=self._name)

    async def clear_banners_async(self) -> None:
        """Awaitable :meth:`clear_banners`."""
        await self._viz.clear_banners_async(scene_name=self._name)

    # ── Dialogs ──────────────────────────────────────────────

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
    ) -> str:
        """Show a dialog scoped to this scene (see :meth:`Visualizer.show_dialog`)."""
        return self._viz.show_dialog(
            content,
            id=id,
            title=title,
            align_x=align_x,
            align_y=align_y,
            dismissable=dismissable,
            on_close=on_close,
            width=width,
            height=height,
            scene_name=self._name,
        )

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
    ) -> str:
        """Awaitable :meth:`show_dialog` scoped to this scene."""
        return await self._viz.show_dialog_async(
            content,
            id=id,
            title=title,
            align_x=align_x,
            align_y=align_y,
            dismissable=dismissable,
            on_close=on_close,
            width=width,
            height=height,
            scene_name=self._name,
        )

    def remove_dialog(self, dialog_id: str) -> None:
        """Remove a dialog from this scene."""
        self._viz.remove_dialog(dialog_id, scene_name=self._name)

    async def remove_dialog_async(self, dialog_id: str) -> None:
        """Awaitable :meth:`remove_dialog`."""
        await self._viz.remove_dialog_async(dialog_id, scene_name=self._name)

    def clear_dialogs(self) -> None:
        """Remove all dialogs from this scene."""
        self._viz.clear_dialogs(scene_name=self._name)

    async def clear_dialogs_async(self) -> None:
        """Awaitable :meth:`clear_dialogs`."""
        await self._viz.clear_dialogs_async(scene_name=self._name)

    # ── Object Interaction ───────────────────────────────────

    def set_interaction(self, object_id: str, config: Any) -> None:
        """Set the interaction configuration for an entity in this scene."""
        self._viz.set_interaction(object_id, config, scene_name=self._name)

    def on_interaction(self, object_id: str, event_type: Any, handler: Any) -> None:
        """Register an async handler for interaction events on an entity."""
        self._viz.on_interaction(object_id, event_type, handler, scene_name=self._name)

    # ── Navigation ───────────────────────────────────────────

    def navigate_to(self, scene_name: str) -> None:
        """Navigate all browsers currently viewing *this* scene to another scene.

        Shorthand for ``viz.navigate_to(scene_name, target="scene:<this.name>")``.
        """
        self._viz.navigate_to(scene_name, target=f"scene:{self._name}")

    def open_browser(self) -> bool:
        """Open a browser tab for this scene (server must be running)."""
        return self._viz._open_scene_browser(self._name)

    def show(
        self,
        *,
        host: str | None = None,
        port: int | None = None,
        jupyter: bool | None = None,
        viewer_name: str | None = None,
    ) -> Any:
        """Serve (if needed) and show this scene in the current environment.

        With ``jupyter=None`` (the default) the display mode is chosen
        automatically: in a Jupyter notebook this delegates to :meth:`display`
        (inline iframe); otherwise it opens a browser tab.  Pass
        ``jupyter=True`` to force the notebook display, or ``jupyter=False`` to
        force the standard browser tab.  ``viewer_name`` is forwarded to
        :meth:`display` in Jupyter.

        ``host``/``port`` are forwarded to ``Visualizer.start_server`` and
        only used when the server is not already running.
        """
        use_jupyter = self._viz._jupyter if jupyter is None else jupyter

        if self._viz._server is None:
            self._viz.start_server(host=host or "localhost", port=port)

        if use_jupyter:
            return self.display(viewer_name=viewer_name)

        return self.open_browser()

    # ── Jupyter support ──────────────────────────────────────

    def display(
        self,
        *,
        viewer_name: str | None = None,
        width: int | str = "100%",
        height: int | str | None = None,
    ) -> Any:
        """Display this scene in a Jupyter notebook with an optional viewer name.

        In Jupyter, returns an :class:`IPython.display.IFrame` instance for
        reliable rendering.  Outside Jupyter, returns a raw HTML ``<iframe>``
        string.

        Repeated calls for the same viewer do not create a new iframe — they
        only flush the latest scene state into the already-open viewer.  The
        viewer is identified by *viewer_name* (if given), otherwise by the
        current notebook cell id, otherwise by the scene name.

        Args:
            viewer_name: Optional label passed via ``?viewer=`` URL param. Used
                to deduplicate notebook outputs and by ``navigate_to``.
            width: CSS width of the iframe (default ``"100%"``).
            height: CSS height of the iframe (defaults to 500px).
        """
        key = self._viz._resolve_viewer_key(viewer_name, self._name)
        self._viewer_name = key

        if height is None:
            height = 500

        src = self.url
        if self._viewer_name:
            src += f"?viewer={self._viewer_name}"

        if self._viz._jupyter:
            self._viz._display_live(src, key, width, height)
            return None
        return (
            f'<iframe src="{src}" width="{width}" height="{height}px" '
            f'style="border: 1px solid #444; border-radius: 4px;" '
            f'title="Tanga 3D Viewer — {self._name}"></iframe>'
        )

    def display_snapshot(
        self, width: int | str = "100%", height: int | str = "500px"
    ) -> Any:
        """Display this scene as standalone HTML (no server required)."""
        return self._viz.display_snapshot(
            width=width, height=height, scene_name=self._name
        )

    def display_static(
        self, width: int | str = "100%", height: int | str = "500px"
    ) -> Any:
        """Deprecated: use :meth:`display_snapshot`."""
        import warnings

        warnings.warn(
            "display_static() is deprecated; use display_snapshot()",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.display_snapshot(width=width, height=height)

    def export_snapshot(
        self,
        path: Any,
        *,
        overwrite: bool = False,
        animation: Any = None,
        anim_style: Any = None,
        theme: str | None = None,
    ) -> None:
        """Export this scene as a self-contained HTML file."""
        self._viz._export_scene_snapshot(
            self._name,
            path,
            overwrite=overwrite,
            animation=animation,
            anim_style=anim_style,
            theme=theme,
        )

    def open_snapshot(self) -> None:
        """Open this scene as a standalone snapshot in a browser window."""
        self._viz._open_scene_snapshot(self._name)

    def export_figure(
        self,
        path: Any = None,
        *,
        style: Any = None,
        overwrite: bool = False,
        animation: Any = None,
        anim_style: Any = None,
        theme: str | None = None,
    ) -> Any:
        """Export this scene as an HTML snippet (or return the string)."""
        return self._viz._export_scene_figure(
            self._name,
            path,
            style=style,
            overwrite=overwrite,
            animation=animation,
            anim_style=anim_style,
            theme=theme,
        )

    def export_glb(self, path: Any, *, overwrite: bool = False) -> None:
        """Export this scene as a glTF 2.0 binary (``.glb``) file."""
        self._viz._export_scene_glb(self._name, path, overwrite=overwrite)

    def start_animation_recording(self) -> Any:
        """Begin recording entity state for animated export (this scene)."""
        return self._viz._start_scene_animation_recording(self._name)
