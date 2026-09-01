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
    ap = ActPoint(1, 2, 3)
    viz.add(ap, color="#ff4444", style=PointStyle(size=0.15))
    viz.run()
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from pytanga.geometry import Direction, Point

from ._act_style import ActPointStyle
from ._interaction import (
    ClickEvent,
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

ActEventHandler = Callable[[DragEvent, "ActSceneObject"], Awaitable[None]]
"""Notification handler signature for active scene objects.

Receives the drag event and the :class:`ActSceneObject` instance for the
``DRAG_START`` and ``DRAG_END`` phases.  The return value is ignored —
these handlers observe the drag lifecycle and never override the default
movement behaviour.
"""

ActClickHandler = Callable[[ClickEvent, "ActSceneObject"], Awaitable[None]]
"""Click handler signature for active scene objects.

Receives the click event and the :class:`ActSceneObject` instance.  The
return value is ignored — click handlers observe the click and never override
default behaviour.
"""


# ── Default trigger helpers ─────────────────────────────────────


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

    # ── Managed state ──────────────────────────────────────

    def __init__(
        self,
        *,
        handler: ActHandler | None = None,
        on_drag_start: ActEventHandler | None = None,
        on_drag_end: ActEventHandler | None = None,
        on_click: ActClickHandler | None = None,
    ) -> None:
        self._handler: ActHandler | None = handler
        self._on_drag_start: ActEventHandler | None = on_drag_start
        self._on_drag_end: ActEventHandler | None = on_drag_end
        self._on_click: ActClickHandler | None = on_click
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

        Registers a handler for ``DRAG_MOVE`` (the per-frame event), which
        calls :meth:`_on_drag`.  When ``on_drag_start`` / ``on_drag_end`` /
        ``on_click`` handlers were supplied, they are additionally registered
        for ``DRAG_START`` / ``DRAG_END`` / ``CLICK``.
        """
        if self._viz_handle is None:
            return
        cfg = self.interaction_config
        self._viz_handle.set_interaction(self._entity_id, cfg)
        self._viz_handle.on_interaction(
            self._entity_id, InteractionEventType.DRAG_MOVE, self._on_drag
        )
        if self._on_drag_start is not None:
            self._viz_handle.on_interaction(
                self._entity_id,
                InteractionEventType.DRAG_START,
                self._on_drag_start_event,
            )
        if self._on_drag_end is not None:
            self._viz_handle.on_interaction(
                self._entity_id,
                InteractionEventType.DRAG_END,
                self._on_drag_end_event,
            )
        if self._on_click is not None:
            self._viz_handle.on_interaction(
                self._entity_id,
                InteractionEventType.CLICK,
                self._on_click_event,
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
        if self._handler is not None:
            handled = await self._handler(event, self)
            if handled:
                return

        self._move_to(event.world_position)
        self.update()
        self.flush()

    async def _on_drag_start_event(self, event: DragEvent) -> None:
        """Dispatch a ``DRAG_START`` event to the user handler, if any."""
        if self._on_drag_start is not None:
            await self._on_drag_start(event, self)

    async def _on_drag_end_event(self, event: DragEvent) -> None:
        """Dispatch a ``DRAG_END`` event to the user handler, if any."""
        if self._on_drag_end is not None:
            await self._on_drag_end(event, self)

    async def _on_click_event(self, event: ClickEvent) -> None:
        """Dispatch a ``CLICK`` event to the user handler, if any."""
        if self._on_click is not None:
            await self._on_click(event, self)

    def _move_to(self, pos: Point) -> None:
        """Update the internal position.  Override in subclasses."""
        raise NotImplementedError

    def drag_anchor(self, ray_origin: Point, ray_direction: Direction) -> Point:
        """Return the nearest point on the ideal geometry to the picking ray."""
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

    Creates a :class:`Point` entity whose left-button drag can be constrained
    to a single plane.  Passing ``drag_mode`` replaces the default triggers
    with a single unmodified left-button trigger on that plane.  When
    ``drag_mode`` is omitted, the point uses four standard modifier-switched
    triggers in 3D, but in a 2D visualizer (``space_dim == 2``) it defaults to
    a single XY-plane trigger so dragging never changes the point's Z
    coordinate.

    The point's visual style (colour, size, opacity) is set via the
    :meth:`Visualizer.add` call, just like any other geometry entity::

        ap = ActPoint(0, 0, 2)
        viz.add(ap, color="#ff4444", style=PointStyle(size=0.15))

    Args:
        x: X coordinate or a :class:`Point` instance.  When a ``Point``
            is given, *y* and *z* are ignored.
        y: Y coordinate (default ``0.0``).  Ignored when *x* is a ``Point``.
        z: Z coordinate (default ``0.0``).  Ignored when *x* is a ``Point``.
        drag_mode: Optional :class:`DragMode` constraining the unmodified
            left-button drag.  When provided, the primary drag trigger uses
            this plane and the modifier-based alternate triggers are omitted.
            When ``None`` (default), the four standard triggers are registered
            (no modifier → view plane, Shift → XY, Ctrl → XZ, Ctrl+Shift → YZ)
            in 3D scenes; in a 2D scene (``space_dim == 2``) the unmodified
            drag instead defaults to :attr:`DragMode.XY_PLANE`.
        act_style: Optional :class:`~pytanga.viz._act_style.ActPointStyle`
            controlling hover highlighting and other interactive feedback.
        handler: Optional async callback invoked before the default
            point-movement logic.  Signature:
            ``async def handler(event: DragEvent, ap: ActPoint) -> bool``.
            Return ``True`` to fully handle the event (no default
            movement or flush), or ``False`` to let ``ActPoint`` move
            the point and flush.
        on_drag_start: Optional async callback invoked when a drag
            begins.  Signature:
            ``async def on_drag_start(event: DragEvent, ap: ActPoint) -> None``.
            The return value is ignored; this observes the start of the
            drag and does not override default movement.
        on_drag_end: Optional async callback invoked when a drag ends.
            Signature:
            ``async def on_drag_end(event: DragEvent, ap: ActPoint) -> None``.
            The return value is ignored; this observes the end of the
            drag and does not override default movement.
        on_click: Optional async callback invoked when the point is clicked.
            Signature:
            ``async def on_click(event: ClickEvent, ap: ActPoint) -> None``.
            The return value is ignored; this observes a click and does not
            override default behaviour.  Providing it also registers a
            ``CLICK`` trigger so the frontend emits ``interaction:click``.
    """

    def __init__(
        self,
        x: float | Point,
        y: float = 0.0,
        z: float = 0.0,
        *,
        drag_mode: DragMode | None = None,
        act_style: ActPointStyle | None = None,
        handler: ActHandler | None = None,
        on_drag_start: ActEventHandler | None = None,
        on_drag_end: ActEventHandler | None = None,
        on_click: ActClickHandler | None = None,
    ) -> None:
        super().__init__(
            handler=handler,
            on_drag_start=on_drag_start,
            on_drag_end=on_drag_end,
            on_click=on_click,
        )
        if isinstance(x, Point):
            self._point = x
        else:
            self._point = Point(float(x), float(y), float(z))
        self._drag_mode = drag_mode
        self._act_style = act_style
        self._resolved_style: ActPointStyle | None = None

    # ── Init (called by Visualizer) ────────────────────────

    def _init(self, viz_handle: VizSceneHandle, entity_id: str) -> None:
        """Resolve style from visualizer default, then register handlers."""
        if self._act_style is None:
            self._resolved_style = viz_handle.styles.act_point
        else:
            default = viz_handle.styles.act_point
            self._resolved_style = ActPointStyle(
                hover_emissive=self._act_style.hover_emissive
                if self._act_style.hover_emissive is not None
                else default.hover_emissive,
                hover_scale=self._act_style.hover_scale
                if self._act_style.hover_scale is not None
                else default.hover_scale,
            )
        super()._init(viz_handle, entity_id)

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
        """Drag triggers with hover highlighting.

        When ``drag_mode`` was provided at construction, or when the point
        is attached to a 2D scene (``space_dim == 2``), a single unmodified
        left-button trigger is registered for that mode (``XY_PLANE`` for the
        automatic 2D default).  Otherwise the four standard triggers (view
        plane, XY, XZ, YZ) are registered.
        """
        s = self._resolved_style or ActPointStyle()
        mode = self._effective_drag_mode
        if mode is None:
            triggers = _default_drag_triggers(MouseButton.LEFT)
        else:
            triggers = [
                InteractionTrigger(
                    event_type=InteractionEventType.DRAG,
                    mouse_button=MouseButton.LEFT,
                    drag_mode=mode,
                )
            ]
        if self._on_click is not None:
            triggers.append(
                InteractionTrigger(
                    event_type=InteractionEventType.CLICK,
                    mouse_button=MouseButton.LEFT,
                )
            )
        return InteractionConfig(
            enabled=True,
            triggers=triggers,
            throttle_ms=40,
            hover_emissive=s.hover_emissive,
            hover_scale=s.hover_scale,
        )

    # ── Drag-mode resolution ────────────────────────────────

    @property
    def _effective_drag_mode(self) -> DragMode | None:
        """Resolve the unmodified drag mode, applying the 2D default.

        Returns the explicit ``drag_mode`` if set.  Otherwise, when the point
        is attached to a scene with ``space_dim == 2``, returns
        :attr:`DragMode.XY_PLANE`.  Returns ``None`` only when no explicit
        mode is set and the scene dimension is unknown or 3D — in that case
        the four standard modifier-switched triggers are used.
        """
        if self._drag_mode is not None:
            return self._drag_mode
        if self._scene_space_dim() == 2:
            return DragMode.XY_PLANE
        return None

    def _scene_space_dim(self) -> int | None:
        """Return the owning scene's space dimension, if discoverable."""
        handle = self._viz_handle
        if handle is None:
            return None
        scene = getattr(handle, "scene", None)
        config = getattr(scene, "config", None)
        space_dim = getattr(config, "space_dim", None)
        return space_dim if isinstance(space_dim, int) else None

    # ── Default movement ───────────────────────────────────

    def _move_to(self, pos: Point) -> None:
        """Set the point position to *pos*."""
        self._point = pos

    def drag_anchor(self, ray_origin: Point, ray_direction: Direction) -> Point:
        """Return the ideal anchor — the point's centre (the ray is ignored)."""
        return self._point
