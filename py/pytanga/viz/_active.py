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
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from pytanga.geometry import Direction, Point, Rectangle2D

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
    from ._image_view import ImageView
    from ._scene_handle import VizSceneHandle
    from ._styles._operator_styles import SquarePointStyle

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


# ── Handler bindings ─────────────────────────────────────────────

_ContextT = TypeVar("_ContextT")


@dataclass
class DragBinding(Generic[_ContextT]):
    """Bind a drag handler to a mouse button and optional modifier keys.

    The most specific matching binding (greatest number of required modifiers)
    wins over less specific bindings and over the general ``on_drag`` handler.

    Args:
        button: Mouse button that starts the drag.
        handler: Async callback invoked for matching drags.  Signature:
            ``async def handler(event: DragEvent, obj) -> bool`` — ``obj`` is the
            interaction context (an ``ActSceneObject``, or the ``ImageCanvas``
            when bound through :class:`~pytanga.viz.ImageCanvas`).
        modifiers: Modifier keys that must all be held (varargs).  None means
            the binding fires regardless of modifier state.
    """

    button: MouseButton
    handler: Callable[[DragEvent, _ContextT], Awaitable[bool]]
    modifiers: frozenset[ModifierKey]
    enabled: bool = True

    def __init__(
        self,
        button: MouseButton,
        handler: Callable[[DragEvent, _ContextT], Awaitable[bool]],
        *modifiers: ModifierKey,
        enabled: bool = True,
    ) -> None:
        self.button = button
        self.handler = handler
        self.modifiers = frozenset(modifiers)
        self.enabled = enabled


@dataclass
class ClickBinding(Generic[_ContextT]):
    """Bind a click handler to a mouse button and optional modifier keys.

    Args:
        button: Mouse button that triggers the click.
        handler: Async callback invoked for matching clicks.  Signature:
            ``async def handler(event: ClickEvent, obj) -> None`` — ``obj`` is the
            interaction context (an ``ActSceneObject``, or the ``ImageCanvas``
            when bound through :class:`~pytanga.viz.ImageCanvas`).
        modifiers: Modifier keys that must all be held (varargs).  None means
            the binding fires regardless of modifier state.
    """

    button: MouseButton
    handler: Callable[[ClickEvent, _ContextT], Awaitable[None]]
    modifiers: frozenset[ModifierKey]
    enabled: bool = True

    def __init__(
        self,
        button: MouseButton,
        handler: Callable[[ClickEvent, _ContextT], Awaitable[None]],
        *modifiers: ModifierKey,
        enabled: bool = True,
    ) -> None:
        self.button = button
        self.handler = handler
        self.modifiers = frozenset(modifiers)
        self.enabled = enabled


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
        drag_bindings: list[DragBinding[ActSceneObject]] | None = None,
        click_bindings: list[ClickBinding[ActSceneObject]] | None = None,
        cursor: str | None = None,
    ) -> None:
        self._handler: ActHandler | None = handler
        self._on_drag_start: ActEventHandler | None = on_drag_start
        self._on_drag_end: ActEventHandler | None = on_drag_end
        self._on_click: ActClickHandler | None = on_click
        self._drag_bindings: list[DragBinding[ActSceneObject]] = list(
            drag_bindings or ()
        )
        self._click_bindings: list[ClickBinding[ActSceneObject]] = list(
            click_bindings or ()
        )
        self._handler_enabled = True
        self._click_enabled = True
        self._enabled = True
        self._cursor: str | None = cursor
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
        cfg.enabled = self._enabled
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
        if self._on_click is not None or self._click_bindings:
            self._viz_handle.on_interaction(
                self._entity_id,
                InteractionEventType.CLICK,
                self._on_click_event,
            )

    # ── Default drag handler ───────────────────────────────

    def _resolve_drag_handler(self, event: DragEvent) -> ActHandler | None:
        """Return the most specific drag binding matching *event*, else the general handler."""
        best: ActHandler | None = self._handler if self._handler_enabled else None
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

    def _resolve_click_handler(self, event: ClickEvent) -> ActClickHandler | None:
        """Return the most specific click binding matching *event*, else the general handler."""
        best: ActClickHandler | None = self._on_click if self._click_enabled else None
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

    async def _on_drag(self, event: DragEvent) -> None:
        """Default drag handler.

        1. Resolve the most specific matching binding (or the general handler)
           and, if one exists, call it.
           * Returns ``True`` → nothing more (handler did its own flush).
           * Returns ``False`` → continue with default behaviour.
        2. Replace the position of the geometry entity with
           ``event.world_position``.
        3. Call :meth:`update` to push the change to the scene.
        4. Call :meth:`flush` to send the update to the frontend.
        """
        handler = self._resolve_drag_handler(event)
        if handler is not None:
            handled = await handler(event, self)
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
        """Dispatch a ``CLICK`` event to the matching binding or general handler."""
        handler = self._resolve_click_handler(event)
        if handler is not None:
            await handler(event, self)

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

    # ── Enable / disable individual handlers ───────────────

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable all interaction on this object.

        When disabled the frontend captures no hover/drag/click/scroll events
        for this object (``InteractionConfig.enabled=False``).
        """
        self._enabled = enabled
        self.refresh_interaction()

    def enable(self) -> None:
        """Re-enable interaction on this object."""
        self.set_enabled(True)

    def disable(self) -> None:
        """Disable interaction on this object."""
        self.set_enabled(False)

    def set_handler_enabled(self, enabled: bool) -> None:
        """Enable or disable the general drag handler (re-registers triggers)."""
        self._handler_enabled = enabled
        self.refresh_interaction()

    def set_click_enabled(self, enabled: bool) -> None:
        """Enable or disable the general click handler (re-registers triggers)."""
        self._click_enabled = enabled
        self.refresh_interaction()

    def refresh_interaction(self) -> None:
        """Re-register this object's interaction config and flush it.

        Call after mutating a :class:`DragBinding` / :class:`ClickBinding`
        ``enabled`` flag so the new trigger set reaches the frontend.
        """
        if self._viz_handle is None:
            return
        self._register_interaction()
        self.flush()


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
        cursor: str | None = None,
    ) -> None:
        super().__init__(
            handler=handler,
            on_drag_start=on_drag_start,
            on_drag_end=on_drag_end,
            on_click=on_click,
            cursor=cursor,
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
        if self._click_enabled and self._on_click is not None:
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
            hover_cursor=self._cursor,
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

    def set_position(self, pos: Point) -> None:
        """Set the point position and push the entity (without flushing).

        Lets a coordinator (e.g. :class:`ActRectangle2D`) reposition several
        handles programmatically and flush once at the end.
        """
        self._move_to(pos)
        self.update()

    def drag_anchor(self, ray_origin: Point, ray_direction: Direction) -> Point:
        """Return the ideal anchor — the point's centre (the ray is ignored)."""
        return self._point


# ── ActImagePlane ───────────────────────────────────────────────


class ActImagePlane(ActSceneObject):
    """An interactive image plane.

    Captures pointer hits and drags on an image and reports them in the image's
    pixel coordinates (the image plane is ``z = 0`` in the pixel frame).  The
    plane itself never moves, so there is no default drag behaviour and the
    user's handlers read ``event.world_position`` as ``(px, py)``.

    Handlers may be supplied as a single general ``handler`` / ``on_click``
    (firing for any button + modifier) or as a list of :class:`DragBinding` /
    :class:`ClickBinding` entries (firing for a specific button + modifiers).
    """

    def __init__(
        self,
        image_view: ImageView,
        *,
        handler: ActHandler | None = None,
        on_drag_start: ActEventHandler | None = None,
        on_drag_end: ActEventHandler | None = None,
        on_click: ActClickHandler | None = None,
        drag_bindings: list[DragBinding[ActSceneObject]] | None = None,
        click_bindings: list[ClickBinding[ActSceneObject]] | None = None,
        cursor: str | None = None,
    ) -> None:
        super().__init__(
            handler=handler,
            on_drag_start=on_drag_start,
            on_drag_end=on_drag_end,
            on_click=on_click,
            drag_bindings=drag_bindings,
            click_bindings=click_bindings,
            cursor=cursor,
        )
        self._image_view = image_view

    # ── Properties ─────────────────────────────────────────

    @property
    def image_view(self) -> ImageView:
        """The underlying :class:`~pytanga.viz.ImageView`."""
        return self._image_view

    @property
    def entity(self) -> ImageView:
        """The rendered image-plane entity (an ``ImageView``)."""
        return self._image_view

    @property
    def interaction_config(self) -> InteractionConfig:
        """One ``XY_PLANE`` drag trigger per drag binding, plus a catch-all.

        Each :class:`DragBinding` yields a DRAG trigger on the image's own plane
        for its button + modifiers.  A general ``handler`` (or lifecycle
        observers without bindings) adds a catch-all DRAG trigger (any button).
        Click bindings and a general ``on_click`` handler similarly yield CLICK
        triggers; clicks are not reported unless requested.
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
                    drag_mode=DragMode.XY_PLANE,
                )
            )
        if self._handler_enabled and (
            self._handler is not None
            or (
                (self._on_drag_start is not None or self._on_drag_end is not None)
                and not self._drag_bindings
            )
        ):
            triggers.append(
                InteractionTrigger(
                    event_type=InteractionEventType.DRAG,
                    mouse_button=None,
                    drag_mode=DragMode.XY_PLANE,
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
            enabled=True,
            triggers=triggers,
            throttle_ms=40,
            hover_cursor=self._cursor,
        )

    async def _on_drag(self, event: DragEvent) -> None:
        """Dispatch a drag to the matching binding or general handler.

        The image plane is fixed, so there is no default movement to apply —
        the handler's ``bool`` return is simply ignored here.
        """
        handler = self._resolve_drag_handler(event)
        if handler is not None:
            await handler(event, self)

    # ── Default movement ───────────────────────────────────

    def _move_to(self, pos: Point) -> None:
        """The image plane is fixed — no movement."""

    def drag_anchor(self, ray_origin: Point, ray_direction: Direction) -> Point:
        """Return the ray ↔ ``z = 0`` (image plane) intersection.

        The result is in world coordinates, which are the image's pixel
        coordinates (``x`` right, ``y`` down) in the dedicated 2D scene.
        """
        denom = ray_direction.z
        if denom == 0.0:
            return Point(ray_origin.x, ray_origin.y, 0.0)
        t = -ray_origin.z / denom
        return Point(
            ray_origin.x + t * ray_direction.x,
            ray_origin.y + t * ray_direction.y,
            0.0,
        )


# ── ActRectangle2D ───────────────────────────────────────────────


class ActRectangle2D(ActSceneObject):
    """An interactive axis-aligned rectangle with corner + translation handles.

    The body is a visual-only :class:`~pytanga.geometry.Rectangle2D`; all
    interaction happens through child :class:`ActPoint` handles (4 corners for
    resizing, one centre handle for translating).  Default behaviour is
    implemented but overridable, mirroring :class:`ActPoint`.

    Args:
        center: Center of the rectangle (default ``(0, 0, 0)``).
        size: Full ``(width, height)`` (default ``(1, 1)``).
        show_translate_handle: Add a centre translation handle (default ``True``).
        handle_style: Marker style for the handles (default a square marker).
        act_style: Hover style for the handles.
        on_corner_drag: Optional async callback overriding corner resize.
            Signature ``async def h(i, event: DragEvent, rect) -> bool``.
        on_translate: Optional async callback overriding translation.
            Signature ``async def h(event: DragEvent, rect) -> bool``.
        on_change: Optional sync callback fired after any geometry change.
            Signature ``def h(rect: Rectangle2D) -> None``.
    """

    def __init__(
        self,
        center: Point | None = None,
        size: tuple[float, float] | None = None,
        *,
        show_translate_handle: bool = True,
        handle_style: SquarePointStyle | None = None,
        act_style: ActPointStyle | None = None,
        on_corner_drag: Callable[[int, DragEvent, "ActRectangle2D"], Awaitable[bool]]
        | None = None,
        on_translate: Callable[[DragEvent, "ActRectangle2D"], Awaitable[bool]]
        | None = None,
        on_change: Callable[[Rectangle2D], None] | None = None,
    ) -> None:
        super().__init__()
        self._rect = Rectangle2D(center=center, size=size)
        self._show_translate_handle = show_translate_handle
        self._handle_style = handle_style
        self._act_style = act_style
        self._on_corner_drag = on_corner_drag
        self._on_translate = on_translate
        self._on_change = on_change
        self._corner_handles: list[ActPoint] = []
        self._translate_handle: ActPoint | None = None
        self._handle_ids: list[str] = []

    # ── Init (called by Visualizer) ────────────────────────

    def _init(self, viz_handle: VizSceneHandle, entity_id: str) -> None:
        super()._init(viz_handle, entity_id)
        self._spawn_handles()

    # ── Properties ─────────────────────────────────────────

    @property
    def rectangle(self) -> Rectangle2D:
        """The current :class:`~pytanga.geometry.Rectangle2D`."""
        return self._rect

    @property
    def entity(self) -> Rectangle2D:
        """The rendered body entity (a ``Rectangle2D``)."""
        return self._rect

    @property
    def interaction_config(self) -> InteractionConfig:
        """The body is visual-only — no interaction triggers."""
        return InteractionConfig(enabled=False, triggers=[])

    # ── Geometry helpers ───────────────────────────────────

    def _corners(self) -> list[Point]:
        cx, cy = self._rect.center.x, self._rect.center.y
        hw, hh = self._rect.size[0] / 2.0, self._rect.size[1] / 2.0
        return [
            Point(cx - hw, cy - hh, 0.0),
            Point(cx + hw, cy - hh, 0.0),
            Point(cx + hw, cy + hh, 0.0),
            Point(cx - hw, cy + hh, 0.0),
        ]

    def _spawn_handles(self) -> None:
        if self._viz_handle is None:
            return
        from ._styles._operator_styles import SquarePointStyle

        style = self._handle_style or SquarePointStyle()
        for i, pos in enumerate(self._corners()):
            handle = ActPoint(
                pos,
                handler=self._make_corner_handler(i),
                drag_mode=DragMode.XY_PLANE,
                act_style=self._act_style,
            )
            eid = self._viz_handle.add(handle, style=style)
            self._corner_handles.append(handle)
            self._handle_ids.append(eid)
        if self._show_translate_handle:
            handle = ActPoint(
                self._rect.center,
                handler=self._make_translate_handler(),
                drag_mode=DragMode.XY_PLANE,
                act_style=self._act_style,
            )
            eid = self._viz_handle.add(handle, style=style)
            self._translate_handle = handle
            self._handle_ids.append(eid)

    # ── Handler closures ───────────────────────────────────

    def _make_corner_handler(self, index: int) -> ActHandler:
        async def handler(event: DragEvent, _handle: ActSceneObject) -> bool:
            return await self._dispatch_corner_drag(index, event)

        return handler

    def _make_translate_handler(self) -> ActHandler:
        async def handler(event: DragEvent, _handle: ActSceneObject) -> bool:
            return await self._dispatch_translate(event)

        return handler

    # ── Dispatch (overridable) ─────────────────────────────

    async def _dispatch_corner_drag(self, index: int, event: DragEvent) -> bool:
        if self._on_corner_drag is not None:
            return await self._on_corner_drag(index, event, self)
        self._resize_corner(index, event.world_position)
        return True

    async def _dispatch_translate(self, event: DragEvent) -> bool:
        if self._on_translate is not None:
            return await self._on_translate(event, self)
        self._translate_by(event.world_delta)
        return True

    # ── Default geometry mutations ─────────────────────────

    def _resize_corner(self, index: int, pos: Point) -> None:
        corners = self._corners()
        opposite = corners[(index + 2) % 4]
        center = Point((pos.x + opposite.x) / 2.0, (pos.y + opposite.y) / 2.0, 0.0)
        size = (abs(pos.x - opposite.x), abs(pos.y - opposite.y))
        self._rect = Rectangle2D(center=center, size=size)
        self._commit()

    def _translate_by(self, delta: Direction) -> None:
        center = Point(
            self._rect.center.x + delta.x,
            self._rect.center.y + delta.y,
            0.0,
        )
        self._rect = Rectangle2D(center=center, size=self._rect.size)
        self._commit()

    def _commit(self) -> None:
        self.update()
        self._refresh_handles()
        self.flush()
        if self._on_change is not None:
            self._on_change(self._rect)

    def _refresh_handles(self) -> None:
        corners = self._corners()
        for i, handle in enumerate(self._corner_handles):
            handle.set_position(corners[i])
        if self._translate_handle is not None:
            self._translate_handle.set_position(self._rect.center)

    # ── Default movement (body never moves) ────────────────

    def _move_to(self, pos: Point) -> None:
        """The body is fixed; movement happens via the handles."""

    def drag_anchor(self, ray_origin: Point, ray_direction: Direction) -> Point:
        """Not used — the body has no interaction triggers."""
        return self._rect.center

    # ── Removal ────────────────────────────────────────────

    def remove(self) -> None:
        """Remove the body and all handle entities."""
        if self._viz_handle is None:
            return
        for eid in self._handle_ids:
            self._viz_handle.remove(eid)
        self._handle_ids.clear()
        self._corner_handles.clear()
        self._translate_handle = None
        self._viz_handle.remove(self._entity_id)

    def clear(self) -> None:
        """Alias for :meth:`remove`."""
        self.remove()
