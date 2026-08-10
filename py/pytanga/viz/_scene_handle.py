# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Per-scene proxy handle for the :class:`Visualizer`.

A :class:`VizSceneHandle` is created by :meth:`Visualizer.scene` and exposes
the same entity, label, control, animation, and title/annotation API as
``Visualizer``, but all operations affect only the target scene.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ._styles import AnnotationStyle, LabelStyle, ObjVizStyle
    from .visualizer import Visualizer

from pytanga.geometry.entities import Entity as GeoEntity

from ._jupyter import _JupyterDisplayMixin
from ._timeline import Timeline
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

    @property
    def _space_extent(self) -> float:
        return self._scene().config.space_extent

    # ── Scene access ────────────────────────────────────────

    def _scene(self) -> Scene:
        """Return the underlying Scene object."""
        return self._viz._scenes[self._name]

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
    def default_styles(self) -> Any:
        """Per-kind style instances (shared across all scenes)."""
        return self._viz.default_styles

    @property
    def default_label_style(self) -> LabelStyle:
        """The global default ``LabelStyle`` instance (shared across scenes)."""
        return self._viz.default_label_style

    @property
    def default_label_styles(self) -> dict[str, Any]:
        """Per-kind default label style overrides (shared across scenes)."""
        return self._viz.default_label_styles

    @property
    def default_annotation_style(self) -> AnnotationStyle:
        """The global default ``AnnotationStyle`` instance (shared across scenes)."""
        return self._viz.default_annotation_style

    # ── Entity management ───────────────────────────────────

    def add(
        self,
        obj: Any = None,
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
        """Add an entity, operator, MV, or label to this scene.

        See :meth:`Visualizer.add` for full documentation.
        """
        return self._viz._add_to_scene(
            self._name,
            obj=obj,
            entity_id=entity_id,
            opns=opns,
            color=color,
            opacity=opacity,
            style=style,
            label=label,
            label_style=label_style,
        )

    def update(self, entity_id: str, **properties: Any) -> None:
        """Update rendering properties of an existing entity."""
        self._scene().update(entity_id, **properties)

    def update_entity(
        self, entity_id: str, obj: GeoEntity | Any, *, opns: bool | None = None
    ) -> None:
        """Replace the geometry for an existing entity."""
        from ._point_path import PointPath

        if isinstance(obj, PointPath):
            self._scene().update_entity(entity_id, obj)
            return

        if opns is None:
            opns = self._viz._opns
        entity = self._viz._resolve(obj, opns=opns)
        if isinstance(entity, list):
            raise ValueError(
                f"update_entity expects a single entity, but the MV resolved to "
                f"{len(entity)} entities. Use the first one explicitly."
            )
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

    def remove(self, entity_id: str) -> None:
        """Remove an entity from this scene."""
        self._scene().remove(entity_id)

    def clear(self) -> None:
        """Remove all entities from this scene."""
        self._scene().clear()

    def flush(self) -> None:
        """Schedule a scene update on the server's event loop (thread-safe)."""
        self._viz._flush_scene(self._name)

    # ── Title & annotation ──────────────────────────────────

    def set_title(self, title: str) -> None:
        """Update the viewport title overlay for this scene."""
        self._viz._set_scene_title(self._name, title)

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

    # ── Interactive Controls ─────────────────────────────────

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
        """Add a slider control to this scene."""
        return self._viz._add_scene_slider(
            self._name,
            cid,
            label=label,
            min=min,
            max=max,
            step=step,
            default=default,
            on_change=on_change,
            parent_id=parent_id,
        )

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
        """Add a dropdown control to this scene."""
        return self._viz._add_scene_dropdown(
            self._name,
            cid,
            label=label,
            options=options,
            default=default,
            on_change=on_change,
            parent_id=parent_id,
        )

    def add_button(
        self,
        cid: str,
        *,
        label: str = "",
        on_click: Any = None,
        parent_id: str | None = None,
    ) -> str:
        """Add a button control to this scene."""
        return self._viz._add_scene_button(
            self._name,
            cid,
            label=label,
            on_click=on_click,
            parent_id=parent_id,
        )

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
        """Create a control group in this scene."""
        return self._viz._add_scene_group(
            self._name,
            gid,
            title=title,
            controls=controls,
            position=position,
            collapsed=collapsed,
            parent_id=parent_id,
            on_toggle=on_toggle,
        )

    def remove_control(self, cid: str) -> None:
        """Remove a control from this scene."""
        self._viz._remove_scene_control(self._name, cid)

    def remove_group(self, gid: str) -> None:
        """Remove a control group from this scene."""
        self._viz._remove_scene_group(self._name, gid)

    def clear_controls(self) -> None:
        """Remove all controls and groups from this scene."""
        self._viz._clear_scene_controls(self._name)

    # ── Navigation ───────────────────────────────────────────

    def navigate_to(self, scene_name: str) -> None:
        """Navigate all browsers currently viewing *this* scene to another scene.

        Shorthand for ``viz.navigate_to(scene_name, target="scene:<this.name>")``.
        """
        self._viz.navigate_to(scene_name, target=f"scene:{self._name}")

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

        Args:
            viewer_name: Optional friendly label passed via ``?viewer=`` URL param.
                Used by ``list_browsers()`` and ``navigate_to(target="viewer:...")``.
            width: CSS width of the iframe (default ``"100%"``).
            height: CSS height of the iframe (auto-computed from ``space_extent``
                when *None*, defaulting to a minimum of 400px).
        """
        if viewer_name is not None:
            self._viewer_name = viewer_name

        if height is None:
            height = max(400, int(self._scene().config.space_extent * 50))

        src = self.url
        if self._viewer_name:
            src += f"?viewer={self._viewer_name}"

        if self._viz._jupyter:
            from IPython.display import IFrame
            from IPython.display import display as ipy_display

            iframe = IFrame(src, width=width, height=height)
            ipy_display(iframe)
            return None
        else:
            return (
                f'<iframe src="{src}" width="{width}" height="{height}px" '
                f'style="border: 1px solid #444; border-radius: 4px;" '
                f'title="Tanga 3D Viewer — {self._name}"></iframe>'
            )

    def display_static(
        self, width: int | str = "100%", height: int | str = "500px"
    ) -> Any:
        """Display this scene as standalone HTML (no server required)."""
        return self._viz.display_static(
            width=width, height=height, scene_name=self._name
        )
