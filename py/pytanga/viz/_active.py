# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Active scene objects — self-registering interactive entities.

Provides :class:`ActSceneObject` (base class) and :class:`ActPoint`
for creating interactive 3D objects that register their own interaction
handlers with the visualizer.

Usage::

    from pytanga.viz import Visualizer
    from pytanga.viz._active import ActPoint
    from pytanga.geometry import Point

    viz = Visualizer()
    ap = ActPoint(Point(1, 2, 3), color="#ff4444")
    viz.add(ap)
    viz.run()
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from pytanga.geometry import Direction, Point

from ._interaction import (
    DragEvent,
    DragMode,
    InteractionConfig,
    InteractionEventType,
    InteractionTrigger,
    ModifierKey,
    MouseButton,
)

if TYPE_CHECKING:
    from ._scene_handle import VizSceneHandle

# ── Handler type ───────────────────────────────────────────────

ActHandler = Callable[[DragEvent, "ActSceneObject"], Awaitable[bool]]
"""Custom handler signature for active scene objects.

Receives the drag event and the :class:`ActSceneObject` instance.  Must
return ``True`` if it fully handled the event (including flush), or
``False`` to let the default behaviour run (move & flush).
"""


# ── Default triggers ───────────────────────────────────────────

def _default_drag_triggers(button: MouseButton) -> list[InteractionTrigger]:
    """Standard four drag-mode triggers for a single mouse button.

    * No modifier → view plane
    * Shift → XY plane
    * Ctrl → XZ plane
    * Ctrl+Shift → YZ plane
    """
    return [
        InteractionTrigger(
            event_type=InteractionEventType.DRAG,
            mouse_button=button,
            drag_mode=DragMode.VIEW_PLANE,
        ),
        InteractionTrigger(
            event_type=InteractionEventType.DRAG,
            mouse_button=button,
            modifiers=frozenset({ModifierKey.SHIFT}),
            drag_mode=DragMode.XY_PLANE,
        ),
        InteractionTrigger(
            event_type=InteractionEventType.DRAG,
            mouse_button=button,
            modifiers=frozenset({ModifierKey.CTRL}),
            drag_mode=DragMode.XZ_PLANE,
        ),
        InteractionTrigger(
            event_type=InteractionEventType.DRAG,
            mouse_button=button,
            modifiers=frozenset({ModifierKey.CTRL, ModifierKey.SHIFT}),
            drag_mode=DragMode.YZ_PLANE,
        ),
    ]


# ── ActSceneObject ─────────────────────────────────────────────


class ActSceneObject:
    """Base class for interactive scene objects.

    Subclasses must define the :attr:`entity` property (the geometry
    entity rendered in the scene) and :attr:`interaction_config`
    (the triggers that activate interaction).

    The visualizer calls :meth:`_init` after the entity is added to
    the scene, giving the object access to its :class:`VizSceneHandle`
    and generated entity ID.
    """

    # ── Subclass contract ──────────────────────────────────

    @property
    def entity(self) -> Any:
        """The geometry entity rendered in the scene (Point, Sphere, …)."""
        raise NotImplementedError

    @property
    def interaction_config(self) -> InteractionConfig:
        """Triggers that make this entity interactive."""
        raise NotImplementedError

    # Override in subclasses if the default drag handler needs
    # to be replaced entirely
    _custom_handler: ActHandler | None = None

    # ── Managed state ──────────────────────────────────────

    def __init__(self, *, custom_handler: ActHandler | None = None) -> None:
        self._custom_handler = custom_handler
        self._viz_handle: VizSceneHandle | None = None
        self._entity_id: str = ""

    # ── Initialization (called by Visualizer) ──────────────

    def _init(self, viz_handle: VizSceneHandle, entity_id: str) -> None:
        """Bind this active object to a scene handle and entity ID.

        Called automatically by :meth:`Visualizer.add` after the
        underlying entity is added to the scene.
        """
        self._viz_handle = viz_handle
        self._entity_id = entity_id
        self._register_interaction()

    # ── Interaction registration ───────────────────────────

    def _register_interaction(self) -> None:
        """Register interaction config and handlers with the scene.

        Iterates over :attr:`interaction_config.triggers` and registers
        a handler for ``DRAG_MOVE`` (the per-frame event).  Calls
        :meth:`_on_drag` for each drag-move event.
        """
        if self._viz_handle is None:
            return
        cfg = self.interaction_config
        self._viz_handle.set_interaction(self._entity_id, cfg)
        self._viz_handle.on_interaction(
            self._entity_id, InteractionEventType.DRAG_MOVE, self._on_drag
        )

    # ── Default drag handler ───────────────────────────────

    async def _on_drag(self, event: DragEvent) -> None:
        """Default drag handler.

        1. If a custom handler is set → call it.
           * Returns ``True`` → nothing more (handler did its own flush).
           * Returns ``False`` → continue with default behaviour.
        2. Replace the position of the geometry entity with
           ``event.world_position``.
        3. Call :meth:`update` to push the change to the scene.
        4. Call :meth:`flush` to send the update to the frontend.
        """
        if self._custom_handler is not None:
            handled = await self._custom_handler(event, self)
            if handled:
                return

        self._move_to(event.world_position)
        self.update()
        self.flush()

    def _move_to(self, pos: Point) -> None:
        """Update the internal position.  Override in subclasses."""
        raise NotImplementedError

    # ── Helpers ────────────────────────────────────────────

    @property
    def entity_id(self) -> str:
        """The scene entity ID assigned by the visualizer."""
        return self._entity_id

    @property
    def viz_handle(self) -> VizSceneHandle | None:
        """The :class:`VizSceneHandle` that owns this object."""
        return self._viz_handle

    def update(self) -> None:
        """Push current :attr:`entity` geometry to the scene."""
        if self._viz_handle is not None:
            self._viz_handle.update_entity(self._entity_id, self.entity)

    def flush(self) -> None:
        """Flush scene updates to the frontend."""
        if self._viz_handle is not None:
            self._viz_handle.flush()


# ── ActPoint ───────────────────────────────────────────────────


class ActPoint(ActSceneObject):
    """An interactive draggable point.

    Creates a :class:`Point` entity with four standard drag-mode triggers
    (view-plane, XY, XZ, YZ) on the left mouse button.

    Args:
        point: The initial position.
        color: CSS colour string for the point (default ``"#ff4444"``).
        size: Point size in world units (default ``0.2``).
        opacity: Opacity (0–1, default ``1.0``).
        custom_handler: Optional async callback invoked before the
            default point-movement logic.  Signature:
            ``async def handler(event: DragEvent, ap: ActPoint) -> bool``.
            Return ``True`` to fully handle the event (no default
            movement or flush), or ``False`` to let ``ActPoint`` move
            the point and flush.
    """

    def __init__(
        self,
        point: Point,
        *,
        color: str | None = None,
        size: float | None = None,
        opacity: float | None = None,
        custom_handler: ActHandler | None = None,
    ) -> None:
        super().__init__(custom_handler=custom_handler)
        self._point = point
        self._color = color
        self._size = size
        self._opacity = opacity

    # ── Properties ─────────────────────────────────────────

    @property
    def point(self) -> Point:
        """Current position."""
        return self._point

    @property
    def entity(self) -> Point:
        """The underlying :class:`Point` geometry entity."""
        return self._point

    @property
    def interaction_config(self) -> InteractionConfig:
        """Standard drag triggers for a draggable point."""
        return InteractionConfig(
            enabled=True,
            triggers=_default_drag_triggers(MouseButton.LEFT),
            throttle_ms=40,
        )

    # ── Default movement ───────────────────────────────────

    def _move_to(self, pos: Point) -> None:
        """Set the point position to *pos*."""
        self._point = pos

    # ── Convenience properties for add() ────────────────────

    @property
    def _add_kwargs(self) -> dict[str, Any]:
        """Keyword arguments to pass to ``scene.add()``."""
        kwargs: dict[str, Any] = {}
        if self._color is not None:
            kwargs["color"] = self._color
        if self._size is not None:
            kwargs["size"] = self._size
        if self._opacity is not None:
            kwargs["opacity"] = self._opacity
        return kwargs