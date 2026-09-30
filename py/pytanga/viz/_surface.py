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

from ._interaction import (
    ClickEvent,
    DragEvent,
    DragMode,
    InteractionConfig,
    InteractionEventType,
    InteractionTrigger,
    MouseButton,
)
from .camera import CoordinateMapper

if TYPE_CHECKING:
    from .visualizer import Visualizer

__all__ = ["InteractionSurface"]

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
    ) -> None:
        self.id = id if id is not None else f"surface{next(_surface_counter)}"
        self.mapper = mapper
        self._on_drag_start = on_drag_start
        self._on_drag = on_drag
        self._on_drag_end = on_drag_end
        self._on_click = on_click
        self._viz: Visualizer | None = None

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
        """The trigger set for this surface (left-button drag + click)."""
        triggers: list[InteractionTrigger] = []
        if (
            self._on_drag is not None
            or self._on_drag_start is not None
            or self._on_drag_end is not None
        ):
            triggers.append(
                InteractionTrigger(
                    event_type=InteractionEventType.DRAG,
                    mouse_button=MouseButton.LEFT,
                    drag_mode=DragMode.VIEW_PLANE,
                )
            )
        if self._on_click is not None:
            triggers.append(
                InteractionTrigger(
                    event_type=InteractionEventType.CLICK,
                    mouse_button=MouseButton.LEFT,
                )
            )
        return InteractionConfig(enabled=True, triggers=triggers, throttle_ms=40)

    # ── Anchor resolution (mirrors ActSceneObject) ────────────

    def drag_anchor(self, ray_origin: Point, ray_direction: Direction) -> Point:
        """Return the picking-ray ↔ mapper-plane intersection (world coords)."""
        point, normal = self.mapper.plane()
        return _ray_plane_intersect(ray_origin, ray_direction, point, normal)

    def click_anchor(self, ray_origin: Point, ray_direction: Direction) -> Point | None:
        """Return the picking-ray ↔ mapper-plane intersection for a CLICK."""
        return self.drag_anchor(ray_origin, ray_direction)

    # ── Binding (called by Visualizer when the layout is pushed) ──

    def _bind(self, viz: Visualizer) -> None:
        """Register handlers + the surface itself with the visualizer (idempotent)."""
        if self._viz is viz:
            return
        self._viz = viz
        viz._act_objects[self.id] = self  # noqa: SLF001
        if (
            self._on_drag is not None
            or self._on_drag_start is not None
            or self._on_drag_end is not None
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
        if self._on_click is not None:
            viz.on_interaction(
                self.id, InteractionEventType.CLICK, self._dispatch_click
            )

    # ── Dispatch wrappers (registered as single-arg async handlers) ──

    async def _dispatch_drag_start(self, event: DragEvent) -> None:
        if self._on_drag_start is not None:
            await self._on_drag_start(event, self)

    async def _dispatch_drag(self, event: DragEvent) -> None:
        if self._on_drag is not None:
            await self._on_drag(event, self)

    async def _dispatch_drag_end(self, event: DragEvent) -> None:
        if self._on_drag_end is not None:
            await self._on_drag_end(event, self)

    async def _dispatch_click(self, event: ClickEvent) -> None:
        if self._on_click is not None:
            await self._on_click(event, self)
