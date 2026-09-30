# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Per-pane interaction surface.

An :class:`InteractionSurface` binds a :class:`~pytanga.viz.CoordinateMapper`
(which defines a plane + pixel↔world mapping) to a set of pointer handlers and
a serialized wire description.  Unlike an :class:`~pytanga.viz.ActSceneObject`,
it has **no scene entity**: the frontend emits its drag/click events when the
pointer hits *empty space* in the pane (see ``templates/interaction.js``), and
the backend resolves world positions against ``mapper.plane()``.

The surface is the shared interaction primitive behind the flat
:class:`~pytanga.viz.ImageCanvas` (``PlanarMapper``, ``z = 0``) and a calibrated
``CameraView.background_image`` (``CalibratedPlaneMapper``).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from itertools import count
from typing import TYPE_CHECKING, Any

from pytanga.geometry import Direction, Point

from ._active import ClickBinding, DragBinding
from ._interaction import (
    ClickEvent,
    DragEvent,
    DragMode,
    InteractionConfig,
    InteractionEventType,
    InteractionTrigger,
)
from .camera import CalibratedPlaneMapper, CoordinateMapper

if TYPE_CHECKING:
    from .camera import CameraCalibration
    from .visualizer import Visualizer

__all__ = ["InteractionSurface", "CalibratedSurface"]

_surface_counter = count(0)

#: Handler signatures — mirror the ``Act*`` convention ``(event, surface)``.
SurfaceDragHandler = Callable[[DragEvent, "InteractionSurface"], Awaitable[bool]]
SurfaceEventHandler = Callable[[DragEvent, "InteractionSurface"], Awaitable[None]]
SurfaceClickHandler = Callable[[ClickEvent, "InteractionSurface"], Awaitable[None]]


def _ray_plane_intersect(
    ray_origin: Point,
    ray_direction: Direction,
    point: Point,
    normal: Direction,
) -> Point:
    """Return the ray↔plane intersection, or the origin projected onto the plane."""
    denom = ray_direction.dot(normal)
    if abs(denom) < 1e-12:
        d = (
            (ray_origin.x - point.x) * normal.x
            + (ray_origin.y - point.y) * normal.y
            + (ray_origin.z - point.z) * normal.z
        )
        return Point(
            ray_origin.x - d * normal.x,
            ray_origin.y - d * normal.y,
            ray_origin.z - d * normal.z,
        )
    t = (
        (point.x - ray_origin.x) * normal.x
        + (point.y - ray_origin.y) * normal.y
        + (point.z - ray_origin.z) * normal.z
    ) / denom
    return Point(
        ray_origin.x + t * ray_direction.x,
        ray_origin.y + t * ray_direction.y,
        ray_origin.z + t * ray_direction.z,
    )


class InteractionSurface:
    """A per-pane interaction plane (pane + mapper + pointer handlers).

    Args:
        mapper: The :class:`~pytanga.viz.CoordinateMapper` that defines the
            interaction plane (via :meth:`~pytanga.viz.CoordinateMapper.plane`)
            and the pixel↔world mapping.
        id: Optional stable surface id (auto-generated as ``"surfaceN"`` when
            omitted).  This id is the ``object_id`` carried by the surface's
            pointer events.
        on_drag_start: Optional async handler ``async def h(event, surface)``
            fired when a surface drag starts.
        on_drag: Optional async handler ``async def h(event, surface) -> bool``
            fired on each drag move (the ``bool`` return is ignored, mirroring
            the ``Act*`` convention).
        on_drag_end: Optional async handler ``async def h(event, surface)``
            fired when a surface drag ends.
        on_click: Optional async handler ``async def h(event, surface)`` fired
            when the surface is clicked.
    """

    def __init__(
        self,
        mapper: CoordinateMapper,
        *,
        id: str | None = None,
        on_drag_start: SurfaceEventHandler | None = None,
        on_drag: SurfaceDragHandler | None = None,
        on_drag_end: SurfaceEventHandler | None = None,
        on_click: SurfaceClickHandler | None = None,
        drag_bindings: list[DragBinding[InteractionSurface]] | None = None,
        click_bindings: list[ClickBinding[InteractionSurface]] | None = None,
        cursor: str | None = None,
    ) -> None:
        self.id = id if id is not None else f"surface{next(_surface_counter)}"
        self.mapper = mapper
        self._on_drag_start = on_drag_start
        self._on_drag = on_drag
        self._on_drag_end = on_drag_end
        self._on_click = on_click
        self._drag_bindings: list[DragBinding[InteractionSurface]] = list(
            drag_bindings or ()
        )
        self._click_bindings: list[ClickBinding[InteractionSurface]] = list(
            click_bindings or ()
        )
        self._cursor = cursor
        self._enabled = True
        self._handler_enabled = True
        self._click_enabled = True
        self._viz: Visualizer | None = None
        self._view_id: str | None = None

    # ── Wire description ──────────────────────────────────────

    def serialize(self) -> dict[str, Any]:
        """Serialize the surface for the frontend's ``scene_view`` node."""
        point, normal = self.mapper.plane()
        return {
            "id": self.id,
            "point": [point.x, point.y, point.z],
            "normal": [normal.x, normal.y, normal.z],
            "interaction": self._interaction_config().to_dict(),
        }

    def _interaction_config(self) -> InteractionConfig:
        """The trigger set (bindings + general handlers + cursor).

        Mirrors :meth:`~pytanga.viz.ActImagePlane.interaction_config`: each
        enabled drag/click binding yields a trigger for its button + modifiers,
        and a general handler (with no bindings) adds a catch-all trigger.
        """
        triggers: list[InteractionTrigger] = []
        for binding in self._drag_bindings:
            if not binding.enabled:
                continue
            triggers.append(
                InteractionTrigger(
                    event_type=InteractionEventType.DRAG,
                    mouse_button=binding.button,
                    modifiers=binding.modifiers,
                    drag_mode=DragMode.VIEW_PLANE,
                )
            )
        if self._handler_enabled and (
            self._on_drag is not None
            or (
                (self._on_drag_start is not None or self._on_drag_end is not None)
                and not self._drag_bindings
            )
        ):
            triggers.append(
                InteractionTrigger(
                    event_type=InteractionEventType.DRAG,
                    mouse_button=None,
                    drag_mode=DragMode.VIEW_PLANE,
                )
            )
        for binding in self._click_bindings:
            if not binding.enabled:
                continue
            triggers.append(
                InteractionTrigger(
                    event_type=InteractionEventType.CLICK,
                    mouse_button=binding.button,
                    modifiers=binding.modifiers,
                )
            )
        if self._click_enabled and self._on_click is not None:
            triggers.append(
                InteractionTrigger(
                    event_type=InteractionEventType.CLICK,
                    mouse_button=None,
                )
            )
        return InteractionConfig(
            enabled=self._enabled,
            triggers=triggers,
            throttle_ms=40,
            hover_cursor=self._cursor,
        )

    # ── Anchor resolution (mirrors ActSceneObject) ────────────

    def drag_anchor(self, ray_origin: Point, ray_direction: Direction) -> Point:
        """Return the picking-ray ↔ mapper-plane intersection (world coords)."""
        point, normal = self.mapper.plane()
        return _ray_plane_intersect(ray_origin, ray_direction, point, normal)

    def click_anchor(self, ray_origin: Point, ray_direction: Direction) -> Point | None:
        """Return the picking-ray ↔ mapper-plane intersection for a CLICK."""
        return self.drag_anchor(ray_origin, ray_direction)

    # ── Binding (called by Visualizer when the layout is pushed) ──

    def _bind(self, viz: Visualizer, view_id: str | None = None) -> None:
        """Register handlers + the surface itself with the visualizer (idempotent)."""
        if self._viz is viz:
            if view_id is not None:
                self._view_id = view_id
            return
        self._viz = viz
        self._view_id = view_id
        viz._act_objects[self.id] = self  # noqa: SLF001
        if (
            self._on_drag is not None
            or self._on_drag_start is not None
            or self._on_drag_end is not None
            or self._drag_bindings
        ):
            viz.on_interaction(
                self.id, InteractionEventType.DRAG_MOVE, self._dispatch_drag
            )
        if self._on_drag_start is not None:
            viz.on_interaction(
                self.id, InteractionEventType.DRAG_START, self._dispatch_drag_start
            )
        if self._on_drag_end is not None:
            viz.on_interaction(
                self.id, InteractionEventType.DRAG_END, self._dispatch_drag_end
            )
        if self._on_click is not None or self._click_bindings:
            viz.on_interaction(
                self.id, InteractionEventType.CLICK, self._dispatch_click
            )

    # ── Handler resolution (mirrors ActSceneObject) ───────────

    def _resolve_drag_handler(self, event: DragEvent) -> SurfaceDragHandler | None:
        """Return the most specific matching drag binding, else the general handler."""
        best: SurfaceDragHandler | None = self._on_drag if self._handler_enabled else None
        best_mods = -1
        for binding in self._drag_bindings:
            if not binding.enabled:
                continue
            if binding.button is not event.mouse_button:
                continue
            if not binding.modifiers <= event.modifiers:
                continue
            if len(binding.modifiers) > best_mods:
                best = binding.handler
                best_mods = len(binding.modifiers)
        return best

    def _resolve_click_handler(self, event: ClickEvent) -> SurfaceClickHandler | None:
        """Return the most specific matching click binding, else the general handler."""
        best: SurfaceClickHandler | None = self._on_click if self._click_enabled else None
        best_mods = -1
        for binding in self._click_bindings:
            if not binding.enabled:
                continue
            if binding.button is not event.mouse_button:
                continue
            if not binding.modifiers <= event.modifiers:
                continue
            if len(binding.modifiers) > best_mods:
                best = binding.handler
                best_mods = len(binding.modifiers)
        return best

    # ── Dispatch wrappers (registered as single-arg async handlers) ──

    async def _dispatch_drag_start(self, event: DragEvent) -> None:
        if self._on_drag_start is not None:
            await self._on_drag_start(event, self)

    async def _dispatch_drag(self, event: DragEvent) -> None:
        handler = self._resolve_drag_handler(event)
        if handler is not None:
            await handler(event, self)

    async def _dispatch_drag_end(self, event: DragEvent) -> None:
        if self._on_drag_end is not None:
            await self._on_drag_end(event, self)

    async def _dispatch_click(self, event: ClickEvent) -> None:
        handler = self._resolve_click_handler(event)
        if handler is not None:
            await handler(event, self)

    # ── Enable / disable ──────────────────────────────────────

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable all interaction on the surface."""
        self._enabled = enabled
        self.refresh_interaction()

    def set_handler_enabled(self, enabled: bool) -> None:
        """Enable or disable the general drag handler (re-pushes triggers)."""
        self._handler_enabled = enabled
        self.refresh_interaction()

    def set_click_enabled(self, enabled: bool) -> None:
        """Enable or disable the general click handler (re-pushes triggers)."""
        self._click_enabled = enabled
        self.refresh_interaction()

    def refresh_interaction(self) -> None:
        """Re-push the surface's interaction config to the bound pane."""
        self._push_surface()

    def _push_surface(self) -> None:
        if self._viz is None or self._view_id is None:
            return
        transport = getattr(self._viz, "_transport", None)
        if transport is None:
            return
        transport.send(
            {
                "type": "view_surface",
                "view_id": self._view_id,
                "surface": self.serialize(),
            }
        )


def CalibratedSurface(
    camera: CameraCalibration,
    depth: float,
    *,
    id: str | None = None,
    on_drag_start: SurfaceEventHandler | None = None,
    on_drag: SurfaceDragHandler | None = None,
    on_drag_end: SurfaceEventHandler | None = None,
    on_click: SurfaceClickHandler | None = None,
    drag_bindings: list[DragBinding[InteractionSurface]] | None = None,
    click_bindings: list[ClickBinding[InteractionSurface]] | None = None,
    cursor: str | None = None,
) -> InteractionSurface:
    """Build an :class:`InteractionSurface` on the ⟂-optical-axis plane.

    Convenience for the calibrated ``CameraView.background_image`` case: the
    mapper is a :class:`~pytanga.viz.CalibratedPlaneMapper`, whose plane is the
    principal point at ``depth`` with the optical axis as its normal.
    """
    return InteractionSurface(
        CalibratedPlaneMapper(camera, depth),
        id=id,
        on_drag_start=on_drag_start,
        on_drag=on_drag,
        on_drag_end=on_drag_end,
        on_click=on_click,
        drag_bindings=drag_bindings,
        click_bindings=click_bindings,
        cursor=cursor,
    )
