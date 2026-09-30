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

import math
import sys
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from pytanga.geometry import Circle, Direction, Ellipse, Line, Point, Rectangle2D

from ._act_style import ActPointStyle
from ._point_path import PointPath
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
from .camera import CoordinateMapper, PlanarMapper

#: Floating-point floor used when a size/radius limit is left at ``None`` —
#: effectively "no practical minimum", guarding only against degenerate zero.
_FLOAT_EPS = sys.float_info.epsilon

if TYPE_CHECKING:
    from ._image_view import ImageView
    from ._scene_handle import VizSceneHandle
    from ._styles._entity_styles import PointStyle

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
        style: Any = None,
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
        self._body_style: Any = style
        self._viz_handle: VizSceneHandle | None = None
        self._entity_id: str = ""
        self._pixel_scale: float = 1.0

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

    def click_anchor(self, ray_origin: Point, ray_direction: Direction) -> Point | None:
        """Return the ideal anchor for a CLICK event, or ``None``.

        ``None`` keeps the frontend's raw mesh hit (``event.world_position``)
        untouched.  Defaults to :meth:`drag_anchor`, so a subclass that raises
        :class:`NotImplementedError` there also keeps the raw hit.
        """
        return self.drag_anchor(ray_origin, ray_direction)

    # ── Helpers ────────────────────────────────────────────

    @property
    def entity_id(self) -> str:
        """The scene entity ID assigned by the visualizer."""
        return self._entity_id

    @property
    def body_style(self) -> Any:
        """The body entity's visual style (from the ``style`` constructor arg)."""
        return self._body_style

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

    def remove(self) -> None:
        """Remove this object's body entity from the scene.

        Composites (:class:`_ActWithHandles`) override this to also remove their
        handle entities; a bare :class:`ActSceneObject` (e.g. :class:`ActPoint`)
        only has the body to remove.
        """
        if self._viz_handle is not None:
            self._viz_handle.remove(self._entity_id)

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

    def set_on_click(self, on_click: ActClickHandler | None) -> None:
        """Set (or clear) the body's click handler and re-register it.

        Lets a host (e.g. a labeling app) make an already-added composite
        selectable after construction, without the composite itself knowing
        about selection.
        """
        self._on_click = on_click
        self.refresh_interaction()

    def set_pixel_scale(self, pixel_scale: float) -> None:
        """Set the world-units-per-image-pixel scale of this object's scene."""
        self._pixel_scale = float(pixel_scale)

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
        style: Optional visual style for the point, applied when the point is
            added without an explicit ``style=``.
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
        drag_bindings: Optional list of :class:`DragBinding` entries firing
            for a specific button + modifier combination (mirrors
            :class:`~pytanga.viz.ActImagePlane`).
        click_bindings: Optional list of :class:`ClickBinding` entries firing
            for a specific button + modifier combination.
    """

    def __init__(
        self,
        x: float | Point,
        y: float = 0.0,
        z: float = 0.0,
        *,
        drag_mode: DragMode | None = None,
        act_style: ActPointStyle | None = None,
        style: Any = None,
        handler: ActHandler | None = None,
        on_drag_start: ActEventHandler | None = None,
        on_drag_end: ActEventHandler | None = None,
        on_click: ActClickHandler | None = None,
        cursor: str | None = None,
        drag_bindings: list[DragBinding[ActSceneObject]] | None = None,
        click_bindings: list[ClickBinding[ActSceneObject]] | None = None,
    ) -> None:
        super().__init__(
            handler=handler,
            on_drag_start=on_drag_start,
            on_drag_end=on_drag_end,
            on_click=on_click,
            drag_bindings=drag_bindings,
            click_bindings=click_bindings,
            cursor=cursor,
            style=style,
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
        binding_drag_mode = mode if mode is not None else DragMode.VIEW_PLANE
        for binding in self._drag_bindings:
            if not binding.enabled:
                continue
            triggers.append(
                InteractionTrigger(
                    event_type=InteractionEventType.DRAG,
                    mouse_button=binding.button,
                    modifiers=binding.modifiers,
                    drag_mode=binding_drag_mode,
                )
            )
        if self._click_enabled and self._on_click is not None:
            triggers.append(
                InteractionTrigger(
                    event_type=InteractionEventType.CLICK,
                    mouse_button=MouseButton.LEFT,
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
        image_view: ImageView | None = None,
        *,
        mapper: CoordinateMapper | None = None,
        entity: Any | None = None,
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
        self._entity: Any = entity if entity is not None else image_view
        self._mapper: CoordinateMapper = mapper if mapper is not None else PlanarMapper()

    # ── Properties ─────────────────────────────────────────

    @property
    def image_view(self) -> ImageView | None:
        """The underlying :class:`~pytanga.viz.ImageView` (or ``None``)."""
        return self._image_view

    @property
    def entity(self) -> Any:
        """The rendered entity (an ``ImageView`` or a transparent hit plane)."""
        return self._entity

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
                    drag_mode=DragMode.VIEW_PLANE,
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
        """Return the picking ray ↔ mapper plane intersection (world coords)."""
        point, normal = self._mapper.plane()
        denom = ray_direction.dot(normal)
        if abs(denom) < 1e-12:
            # Ray parallel to the plane: project the origin onto the plane.
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

    def click_anchor(self, ray_origin: Point, ray_direction: Direction) -> Point | None:
        """Keep the raw mesh hit for CLICK events.

        The image plane is flat at ``z = 0``, so the frontend's raycast hit is
        already the correct pixel coordinate — recomputing it from the event's
        (view-relative) ``screen_position`` would introduce an offset.
        """
        return None


# ── Composite base ───────────────────────────────────────────────


class _ActWithHandles(ActSceneObject):
    """Base for composite actives: a visual-only body plus ``ActPoint`` handles.

    Owns the shared handle bookkeeping — the ``_handle_ids`` list, the
    ``_spawn_handle`` helper, and ``remove()`` — so composites only implement
    their specific geometry and handle-refresh logic.
    """

    def __init__(
        self,
        *,
        on_click: ActClickHandler | None = None,
        handle_style: PointStyle | None = None,
        translate_handle_style: PointStyle | None = None,
        rotate_handle_style: PointStyle | None = None,
        act_style: ActPointStyle | None = None,
        style: Any = None,
    ) -> None:
        super().__init__(on_click=on_click, style=style)
        self._handle_ids: list[str] = []
        self._handle_style = handle_style
        self._translate_handle_style = translate_handle_style
        self._rotate_handle_style = rotate_handle_style
        self._act_style = act_style

    def _spawn_handle(self, handle: ActPoint, *, style: Any = None) -> str:
        """Add a child handle to the scene and record its entity id."""
        assert self._viz_handle is not None, "spawn_handle called before _init"
        eid = self._viz_handle.add(handle, style=style)
        self._handle_ids.append(eid)
        return eid

    def _resolve_handle_style(self) -> PointStyle:
        """The vertex/corner/radius handle style (a screen-space ``CirclePointStyle`` by default)."""
        from ._styles._operator_styles import CirclePointStyle

        style = self._handle_style
        if style is not None:
            return style
        return CirclePointStyle(size=6.0, screen_space=True)

    def _handle_size(self) -> float:
        """Effective control-point size in screen px (default 6.0)."""
        style = self._handle_style
        if style is None or style.size is None:
            return 6.0
        return style.size

    def _handle_world_size(self) -> float:
        """The handle size in world units (screen px × pixel scale)."""
        return self._handle_size() * self._pixel_scale

    def _resolve_translate_handle_style(self) -> PointStyle:
        """The translate handle style (a screen-space move glyph, twice the control-point size)."""
        from ._styles._operator_styles import IconPointStyle

        style = self._translate_handle_style
        if style is not None:
            return style
        return IconPointStyle(
            icon="material:open_with",
            size=self._handle_size() * 2,
            screen_space=True,
        )

    def _resolve_rotate_handle_style(self) -> PointStyle:
        """The rotate handle style (a screen-space rotate glyph, twice the control-point size)."""
        from ._styles._operator_styles import IconPointStyle

        style = self._rotate_handle_style
        if style is not None:
            return style
        return IconPointStyle(
            icon="material:rotate_right",
            size=self._handle_size() * 2,
            screen_space=True,
        )

    def _handle_click_handler(self) -> ActClickHandler:
        """Route a handle click to the body's ``on_click`` with the parent Act.

        Lets a single click on any control point select the parent object, the
        same as clicking the body.
        """

        async def on_click(event: ClickEvent, _handle: ActSceneObject) -> None:
            if self._on_click is not None:
                await self._on_click(event, self)

        return on_click

    def set_translate_handle_visible(self, visible: bool) -> None:
        """Show or hide the translation handle (no-op if it was never spawned)."""
        handle = getattr(self, "_translate_handle", None)
        if handle is not None and handle.entity_id and self._viz_handle is not None:
            self._viz_handle.set_visible(handle.entity_id, visible)
            handle.set_enabled(visible)
            self.flush()

    def set_rotate_handle_visible(self, visible: bool) -> None:
        """Show or hide the rotation handle (no-op if it was never spawned)."""
        handle = getattr(self, "_rotate_handle", None)
        if handle is not None and handle.entity_id and self._viz_handle is not None:
            self._viz_handle.set_visible(handle.entity_id, visible)
            handle.set_enabled(visible)
            self.flush()

    def _remove_handles(self) -> None:
        if self._viz_handle is None:
            return
        for eid in self._handle_ids:
            self._viz_handle.remove(eid)
        self._handle_ids.clear()

    def _on_remove(self) -> None:
        """Hook for subclasses to clear their own handle references."""

    def remove(self) -> None:
        """Remove the body and all handle entities."""
        if self._viz_handle is None:
            return
        self._remove_handles()
        self._on_remove()
        self._viz_handle.remove(self._entity_id)

    def clear(self) -> None:
        """Alias for :meth:`remove`."""
        self.remove()


# ── ActRectangle2D ───────────────────────────────────────────────


class ActRectangle2D(_ActWithHandles):
    """An interactive rectangle with corner, translation, and rotation handles.

    The body is a visual-only :class:`~pytanga.geometry.Rectangle2D`; all
    interaction happens through child :class:`ActPoint` handles (4 corners for
    resizing, one centre handle for translating, one rim handle for rotating).
    Default behaviour is implemented but overridable, mirroring :class:`ActPoint`.

    Args:
        center: Center of the rectangle (default ``(0, 0, 0)``).
        size: Full ``(width, height)`` (default ``(1, 1)``).
        angle: In-plane rotation in radians (default ``0.0`` = axis-aligned).
        min_size: Minimum width/height during corner resize (default ``None`` =
            floating-point precision).  Pass an explicit world-unit value to clamp.
        max_size: Maximum width/height during corner resize (default ``None`` =
            unbounded).
        show_translate_handle: Add a centre translation handle (default ``True``).
        show_rotate_handle: Add a rim rotation handle (default ``True``).
        handle_style: Marker style for the corner handles (default a circle marker).
        translate_handle_style: Marker style for the translation handle (default
            a move-icon glyph).
        rotate_handle_style: Marker style for the rotation handle (default a
            rotate-icon glyph).
        act_style: Hover style for the handles.
        style: Optional visual style for the body entity, applied when the
            object is added without an explicit ``style=``.
        on_corner_drag: Optional async callback overriding corner resize.
            Signature ``async def h(i, event: DragEvent, rect) -> bool``.
        on_translate: Optional async callback overriding translation.
            Signature ``async def h(event: DragEvent, rect) -> bool``.
        on_rotate: Optional async callback overriding rotation.
            Signature ``async def h(event: DragEvent, rect) -> bool``.
        on_change: Optional sync callback fired after any geometry change.
            Signature ``def h(rect: Rectangle2D) -> None``.
        on_click: Optional async callback invoked when the body is clicked.
            Providing it makes the body clickable (selectable).
    """

    def __init__(
        self,
        center: Point | None = None,
        size: tuple[float, float] | None = None,
        *,
        angle: float = 0.0,
        min_size: float | None = None,
        max_size: float | None = None,
        show_translate_handle: bool = True,
        show_rotate_handle: bool = True,
        handle_style: PointStyle | None = None,
        translate_handle_style: PointStyle | None = None,
        rotate_handle_style: PointStyle | None = None,
        act_style: ActPointStyle | None = None,
        style: Any = None,
        on_corner_drag: Callable[[int, DragEvent, "ActRectangle2D"], Awaitable[bool]]
        | None = None,
        on_translate: Callable[[DragEvent, "ActRectangle2D"], Awaitable[bool]]
        | None = None,
        on_rotate: Callable[[DragEvent, "ActRectangle2D"], Awaitable[bool]]
        | None = None,
        on_change: Callable[[Rectangle2D], None] | None = None,
        on_click: ActClickHandler | None = None,
    ) -> None:
        super().__init__(
            on_click=on_click,
            handle_style=handle_style,
            translate_handle_style=translate_handle_style,
            rotate_handle_style=rotate_handle_style,
            act_style=act_style,
            style=style,
        )
        self._rect = Rectangle2D(center=center, size=size, angle=angle)
        self._angle = float(angle)
        self._min_size = min_size
        self._max_size = max_size
        self._show_translate_handle = show_translate_handle
        self._show_rotate_handle = show_rotate_handle
        self._on_corner_drag = on_corner_drag
        self._on_translate = on_translate
        self._on_rotate = on_rotate
        self._on_change = on_change
        self._corner_handles: list[ActPoint] = []
        self._translate_handle: ActPoint | None = None
        self._rotate_handle: ActPoint | None = None

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
    def angle(self) -> float:
        """The in-plane rotation in radians."""
        return self._angle

    @property
    def interaction_config(self) -> InteractionConfig:
        """The body is visual-only unless ``on_click`` was provided.

        With ``on_click`` set, the body registers a left-button ``CLICK``
        trigger so it can be selected.
        """
        if self._on_click is None:
            return InteractionConfig(enabled=False, triggers=[])
        return InteractionConfig(
            enabled=True,
            triggers=[
                InteractionTrigger(
                    event_type=InteractionEventType.CLICK,
                    mouse_button=MouseButton.LEFT,
                )
            ],
        )

    # ── Geometry helpers ───────────────────────────────────

    def _dir_u(self) -> Direction:
        return Direction(math.cos(self._angle), math.sin(self._angle), 0.0)

    def _dir_v(self) -> Direction:
        return Direction(-math.sin(self._angle), math.cos(self._angle), 0.0)

    def _corners(self) -> list[Point]:
        cx, cy = self._rect.center.x, self._rect.center.y
        cz = self._rect.center.z
        hw, hh = self._rect.size[0] / 2.0, self._rect.size[1] / 2.0
        ux, uy = math.cos(self._angle), math.sin(self._angle)
        vx, vy = -math.sin(self._angle), math.cos(self._angle)
        return [
            Point(cx - hw * ux - hh * vx, cy - hw * uy - hh * vy, cz),
            Point(cx + hw * ux - hh * vx, cy + hw * uy - hh * vy, cz),
            Point(cx + hw * ux + hh * vx, cy + hw * uy + hh * vy, cz),
            Point(cx - hw * ux + hh * vx, cy - hw * uy + hh * vy, cz),
        ]

    def _rotate_handle_position(self) -> Point:
        hw, hh = self._rect.size[0] / 2.0, self._rect.size[1] / 2.0
        offset = max(0.25 * max(hw, hh), 2.0 * self._handle_world_size())
        d = self._dir_u()
        r = hw + offset
        return Point(
            self._rect.center.x + r * d.x,
            self._rect.center.y + r * d.y,
            self._rect.center.z,
        )

    def _spawn_handles(self) -> None:
        if self._viz_handle is None:
            return
        style = self._resolve_handle_style()
        translate_style = self._resolve_translate_handle_style()
        rotate_style = self._resolve_rotate_handle_style()
        for i, pos in enumerate(self._corners()):
            handle = ActPoint(
                pos,
                handler=self._make_corner_handler(i),
                drag_mode=DragMode.XY_PLANE,
                act_style=self._act_style,

                on_click=self._handle_click_handler(),
            )
            self._spawn_handle(handle, style=style)
            self._corner_handles.append(handle)
        if self._show_translate_handle:
            handle = ActPoint(
                self._rect.center,
                handler=self._make_translate_handler(),
                drag_mode=DragMode.XY_PLANE,
                act_style=self._act_style,

                on_click=self._handle_click_handler(),
            )
            self._spawn_handle(handle, style=translate_style)
            self._translate_handle = handle
        if self._show_rotate_handle:
            handle = ActPoint(
                self._rotate_handle_position(),
                handler=self._make_rotate_handler(),
                drag_mode=DragMode.XY_PLANE,
                act_style=self._act_style,

                on_click=self._handle_click_handler(),
            )
            self._spawn_handle(handle, style=rotate_style)
            self._rotate_handle = handle

    # ── Handler closures ───────────────────────────────────

    def _make_corner_handler(self, index: int) -> ActHandler:
        async def handler(event: DragEvent, _handle: ActSceneObject) -> bool:
            return await self._dispatch_corner_drag(index, event)

        return handler

    def _make_translate_handler(self) -> ActHandler:
        async def handler(event: DragEvent, _handle: ActSceneObject) -> bool:
            return await self._dispatch_translate(event)

        return handler

    def _make_rotate_handler(self) -> ActHandler:
        async def handler(event: DragEvent, _handle: ActSceneObject) -> bool:
            return await self._dispatch_rotate(event)

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

    async def _dispatch_rotate(self, event: DragEvent) -> bool:
        if self._on_rotate is not None:
            return await self._on_rotate(event, self)
        self._rotate_to(event.world_position)
        return True

    # ── Default geometry mutations ─────────────────────────

    def _resize_corner(self, index: int, pos: Point) -> None:
        corners = self._corners()
        opposite = corners[(index + 2) % 4]
        center = Point(
            (pos.x + opposite.x) / 2.0,
            (pos.y + opposite.y) / 2.0,
            self._rect.center.z,
        )
        dx = pos.x - center.x
        dy = pos.y - center.y
        ux, uy = math.cos(self._angle), math.sin(self._angle)
        vx, vy = -math.sin(self._angle), math.cos(self._angle)
        hw = abs(dx * ux + dy * uy)
        hh = abs(dx * vx + dy * vy)
        half_floor = (self._min_size if self._min_size is not None else _FLOAT_EPS) / 2.0
        hw = max(hw, half_floor)
        hh = max(hh, half_floor)
        if self._max_size is not None:
            half_cap = self._max_size / 2.0
            hw = min(hw, half_cap)
            hh = min(hh, half_cap)
        self._rect = Rectangle2D(
            center=center, size=(2.0 * hw, 2.0 * hh), angle=self._angle
        )
        self._commit()

    def set_size_limits(
        self, min_size: float | None, max_size: float | None
    ) -> None:
        """Set the resize clamp (world units; ``None`` = floating-point min / unbounded max)."""
        self._min_size = None if min_size is None else float(min_size)
        self._max_size = None if max_size is None else float(max_size)

    def _translate_by(self, delta: Direction) -> None:
        center = Point(
            self._rect.center.x + delta.x,
            self._rect.center.y + delta.y,
            self._rect.center.z,
        )
        self._rect = Rectangle2D(center=center, size=self._rect.size, angle=self._angle)
        self._commit()

    def _rotate_to(self, pos: Point) -> None:
        dx = pos.x - self._rect.center.x
        dy = pos.y - self._rect.center.y
        self._angle = math.atan2(dy, dx)
        # Rebuild the body with the new angle so the rendered rectangle (and the
        # on_change payload) matches the rotated handle layout.
        self._rect = Rectangle2D(
            center=self._rect.center, size=self._rect.size, angle=self._angle
        )
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
        if self._rotate_handle is not None:
            self._rotate_handle.set_position(self._rotate_handle_position())

    # ── Default movement (body never moves) ────────────────

    def _move_to(self, pos: Point) -> None:
        """The body is fixed; movement happens via the handles."""

    def drag_anchor(self, ray_origin: Point, ray_direction: Direction) -> Point:
        """Not used — the body has no interaction triggers."""
        return self._rect.center

    # ── Removal ────────────────────────────────────────────

    def _on_remove(self) -> None:
        """Clear this composite's own handle references."""
        self._corner_handles.clear()
        self._translate_handle = None
        self._rotate_handle = None

    @classmethod
    def create_from_points(
        cls, a: Point, b: Point, **kwargs: Any
    ) -> "ActRectangle2D":
        """Build a rectangle from two opposite corners."""
        rect = Rectangle2D.between(a, b)
        size = list(rect.size)
        min_s = kwargs.get("min_size")
        if min_s is not None:
            size[0] = max(size[0], float(min_s))
            size[1] = max(size[1], float(min_s))
        return cls(center=rect.center, size=size, **kwargs)


# ── ActEllipse ───────────────────────────────────────────────


class ActEllipse(_ActWithHandles):
    """An interactive ellipse with radius, translate, and rotate handles.

    The body is a visual-only :class:`~pytanga.geometry.Ellipse`; all
    interaction happens through child :class:`ActPoint` handles — two radius
    handles, a centre translate handle, and a rim rotate handle.  Rotation is
    encoded in ``Ellipse.dir_u`` / ``Ellipse.dir_v``.

    Args:
        center: Center of the ellipse (default ``(0, 0, 0)``).
        radius_u: Semi-axis radius along ``dir_u`` (default ``1.0``).
        radius_v: Semi-axis radius along ``dir_v`` (default ``0.5``).
        angle: In-plane rotation in radians (default ``0.0``).
        show_translate_handle: Add a centre translation handle (default ``True``).
        show_rotate_handle: Add a rim rotation handle (default ``True``).
        handle_style: Marker style for the radius handles (default a circle marker).
        translate_handle_style: Marker style for the translation handle (default
            a move-icon glyph).
        rotate_handle_style: Marker style for the rotation handle (default a
            rotate-icon glyph).
        act_style: Hover style for the handles.
        style: Optional visual style for the body entity, applied when the
            object is added without an explicit ``style=``.
        on_radius_drag: Optional async callback overriding radius resize.
        on_translate: Optional async callback overriding translation.
        on_rotate: Optional async callback overriding rotation.
        on_change: Optional sync callback fired after any geometry change.
        on_click: Optional async callback invoked when the body is clicked.
    """

    def __init__(
        self,
        center: Point | None = None,
        radius_u: float = 1.0,
        radius_v: float = 0.5,
        *,
        angle: float = 0.0,
        show_translate_handle: bool = True,
        show_rotate_handle: bool = True,
        handle_style: PointStyle | None = None,
        translate_handle_style: PointStyle | None = None,
        rotate_handle_style: PointStyle | None = None,
        min_radius: float | None = None,
        max_radius: float | None = None,
        act_style: ActPointStyle | None = None,
        style: Any = None,
        on_radius_drag: Callable[[int, DragEvent, "ActEllipse"], Awaitable[bool]]
        | None = None,
        on_translate: Callable[[DragEvent, "ActEllipse"], Awaitable[bool]]
        | None = None,
        on_rotate: Callable[[DragEvent, "ActEllipse"], Awaitable[bool]] | None = None,
        on_change: Callable[[Ellipse], None] | None = None,
        on_click: ActClickHandler | None = None,
    ) -> None:
        super().__init__(
            on_click=on_click,
            handle_style=handle_style,
            translate_handle_style=translate_handle_style,
            rotate_handle_style=rotate_handle_style,
            act_style=act_style,
            style=style,
        )
        self._center = Point(0.0, 0.0, 0.0) if center is None else center
        self._radius_u = float(radius_u)
        self._radius_v = float(radius_v)
        self._angle = float(angle)
        self._min_radius = min_radius
        self._max_radius = max_radius
        self._show_translate_handle = show_translate_handle
        self._show_rotate_handle = show_rotate_handle
        self._on_radius_drag = on_radius_drag
        self._on_translate = on_translate
        self._on_rotate = on_rotate
        self._on_change = on_change
        self._radius_handles: list[ActPoint] = []
        self._translate_handle: ActPoint | None = None
        self._rotate_handle: ActPoint | None = None

    # ── Init (called by Visualizer) ────────────────────────

    def _init(self, viz_handle: VizSceneHandle, entity_id: str) -> None:
        super()._init(viz_handle, entity_id)
        self._spawn_handles()

    # ── Properties ─────────────────────────────────────────

    @property
    def ellipse(self) -> Ellipse:
        """The current :class:`~pytanga.geometry.Ellipse`."""
        return self._build_ellipse()

    @property
    def entity(self) -> Ellipse:
        """The rendered body entity (an ``Ellipse``)."""
        return self._build_ellipse()

    @property
    def center(self) -> Point:
        """The ellipse centre."""
        return self._center

    @property
    def angle(self) -> float:
        """The in-plane rotation in radians."""
        return self._angle

    @property
    def interaction_config(self) -> InteractionConfig:
        """The body is visual-only unless ``on_click`` was provided."""
        if self._on_click is None:
            return InteractionConfig(enabled=False, triggers=[])
        return InteractionConfig(
            enabled=True,
            triggers=[
                InteractionTrigger(
                    event_type=InteractionEventType.CLICK,
                    mouse_button=MouseButton.LEFT,
                )
            ],
        )

    # ── Geometry helpers ───────────────────────────────────

    def _dir_u(self) -> Direction:
        return Direction(math.cos(self._angle), math.sin(self._angle), 0.0)

    def _dir_v(self) -> Direction:
        return Direction(-math.sin(self._angle), math.cos(self._angle), 0.0)

    def _build_ellipse(self) -> Ellipse:
        return Ellipse(
            center=self._center,
            radius_u=self._radius_u,
            radius_v=self._radius_v,
            dir_u=self._dir_u(),
            dir_v=self._dir_v(),
        )

    def _radius_handle_position(self, index: int) -> Point:
        if index == 0:
            d, r = self._dir_u(), self._radius_u
        else:
            d, r = self._dir_v(), self._radius_v
        return Point(self._center.x + r * d.x, self._center.y + r * d.y, self._center.z)

    def _rotate_handle_position(self) -> Point:
        offset = max(
            0.25 * max(self._radius_u, self._radius_v),
            2.0 * self._handle_world_size(),
        )
        d = self._dir_u()
        r = self._radius_u + offset
        return Point(self._center.x + r * d.x, self._center.y + r * d.y, self._center.z)

    def _spawn_handles(self) -> None:
        if self._viz_handle is None:
            return
        style = self._resolve_handle_style()
        translate_style = self._resolve_translate_handle_style()
        rotate_style = self._resolve_rotate_handle_style()
        for i in range(2):
            handle = ActPoint(
                self._radius_handle_position(i),
                handler=self._make_radius_handler(i),
                drag_mode=DragMode.XY_PLANE,
                act_style=self._act_style,

                on_click=self._handle_click_handler(),
            )
            self._spawn_handle(handle, style=style)
            self._radius_handles.append(handle)
        if self._show_translate_handle:
            handle = ActPoint(
                self._center,
                handler=self._make_translate_handler(),
                drag_mode=DragMode.XY_PLANE,
                act_style=self._act_style,

                on_click=self._handle_click_handler(),
            )
            self._spawn_handle(handle, style=translate_style)
            self._translate_handle = handle
        if self._show_rotate_handle:
            handle = ActPoint(
                self._rotate_handle_position(),
                handler=self._make_rotate_handler(),
                drag_mode=DragMode.XY_PLANE,
                act_style=self._act_style,

                on_click=self._handle_click_handler(),
            )
            self._spawn_handle(handle, style=rotate_style)
            self._rotate_handle = handle

    # ── Handler closures ───────────────────────────────────

    def _make_radius_handler(self, index: int) -> ActHandler:
        async def handler(event: DragEvent, _handle: ActSceneObject) -> bool:
            return await self._dispatch_radius_drag(index, event)

        return handler

    def _make_translate_handler(self) -> ActHandler:
        async def handler(event: DragEvent, _handle: ActSceneObject) -> bool:
            return await self._dispatch_translate(event)

        return handler

    def _make_rotate_handler(self) -> ActHandler:
        async def handler(event: DragEvent, _handle: ActSceneObject) -> bool:
            return await self._dispatch_rotate(event)

        return handler

    # ── Dispatch (overridable) ─────────────────────────────

    async def _dispatch_radius_drag(self, index: int, event: DragEvent) -> bool:
        if self._on_radius_drag is not None:
            return await self._on_radius_drag(index, event, self)
        self._resize_radius(index, event.world_position)
        return True

    async def _dispatch_translate(self, event: DragEvent) -> bool:
        if self._on_translate is not None:
            return await self._on_translate(event, self)
        self._translate_by(event.world_delta)
        return True

    async def _dispatch_rotate(self, event: DragEvent) -> bool:
        if self._on_rotate is not None:
            return await self._on_rotate(event, self)
        self._rotate_to(event.world_position)
        return True

    # ── Default geometry mutations ─────────────────────────

    def _resize_radius(self, index: int, pos: Point) -> None:
        dx, dy = pos.x - self._center.x, pos.y - self._center.y
        d = self._dir_u() if index == 0 else self._dir_v()
        value = dx * d.x + dy * d.y
        floor = self._min_radius if self._min_radius is not None else _FLOAT_EPS
        value = max(floor, value)
        if self._max_radius is not None:
            value = min(self._max_radius, value)
        if index == 0:
            self._radius_u = value
        else:
            self._radius_v = value
        self._commit()

    def set_radius_limits(
        self, min_radius: float | None, max_radius: float | None
    ) -> None:
        """Set the resize clamp (world units; ``None`` = floating-point min / unbounded max)."""
        self._min_radius = None if min_radius is None else float(min_radius)
        self._max_radius = None if max_radius is None else float(max_radius)

    def _translate_by(self, delta: Direction) -> None:
        self._center = Point(
            self._center.x + delta.x, self._center.y + delta.y, self._center.z
        )
        self._commit()

    def _rotate_to(self, pos: Point) -> None:
        dx, dy = pos.x - self._center.x, pos.y - self._center.y
        self._angle = math.atan2(dy, dx)
        self._commit()

    def _commit(self) -> None:
        self.update()
        self._refresh_handles()
        self.flush()
        if self._on_change is not None:
            self._on_change(self._build_ellipse())

    def _refresh_handles(self) -> None:
        for i, handle in enumerate(self._radius_handles):
            handle.set_position(self._radius_handle_position(i))
        if self._translate_handle is not None:
            self._translate_handle.set_position(self._center)
        if self._rotate_handle is not None:
            self._rotate_handle.set_position(self._rotate_handle_position())

    # ── Default movement (body never moves) ────────────────

    def _move_to(self, pos: Point) -> None:
        """The body is fixed; movement happens via the handles."""

    def drag_anchor(self, ray_origin: Point, ray_direction: Direction) -> Point:
        """Not used — the body has no interaction triggers."""
        return self._center

    # ── Removal ────────────────────────────────────────────

    def _on_remove(self) -> None:
        """Clear this composite's own handle references."""
        self._radius_handles.clear()
        self._translate_handle = None
        self._rotate_handle = None

    @classmethod
    def create_from_points(cls, a: Point, b: Point, **kwargs: Any) -> "ActEllipse":
        """Build an axis-aligned ellipse from two opposite corners."""
        center = Point((a.x + b.x) / 2.0, (a.y + b.y) / 2.0, (a.z + b.z) / 2.0)
        radius_u = abs(b.x - a.x) / 2.0
        radius_v = abs(b.y - a.y) / 2.0
        min_r = kwargs.get("min_radius")
        if min_r is not None:
            radius_u = max(radius_u, float(min_r))
            radius_v = max(radius_v, float(min_r))
        return cls(center=center, radius_u=radius_u, radius_v=radius_v, **kwargs)


# ── ActCircle ─────────────────────────────────────────────────


class ActCircle(_ActWithHandles):
    """An interactive circle with center translate and radius handles.

    The body is a visual-only :class:`~pytanga.geometry.Circle`; interaction
    happens through a centre translate handle and a single radius handle.

    Args:
        center: Center of the circle (default ``(0, 0, 0)``).
        radius: Circle radius (default ``1.0``).
        min_radius: Minimum radius during resize (default ``None`` =
            floating-point precision).  Pass an explicit world-unit value to clamp.
        max_radius: Maximum radius during resize (default ``None`` = unbounded).
        show_translate_handle: Add a centre translation handle (default ``True``).
        handle_style: Marker style for the radius handle (default a circle marker).
        translate_handle_style: Marker style for the translation handle (default
            a move-icon glyph).
        act_style: Hover style for the handles.
        style: Optional visual style for the body entity, applied when the
            object is added without an explicit ``style=``.
        on_radius_drag: Optional async callback overriding radius resize.
            Signature ``async def h(event: DragEvent, circle) -> bool``.
        on_translate: Optional async callback overriding translation.
            Signature ``async def h(event: DragEvent, circle) -> bool``.
        on_change: Optional sync callback fired after any geometry change.
            Signature ``def h(circle: Circle) -> None``.
        on_click: Optional async callback invoked when the body is clicked.
            Providing it makes the body clickable (selectable).
    """

    def __init__(
        self,
        center: Point | None = None,
        radius: float = 1.0,
        *,
        min_radius: float | None = None,
        max_radius: float | None = None,
        show_translate_handle: bool = True,
        handle_style: PointStyle | None = None,
        translate_handle_style: PointStyle | None = None,
        act_style: ActPointStyle | None = None,
        style: Any = None,
        on_radius_drag: Callable[[DragEvent, "ActCircle"], Awaitable[bool]]
        | None = None,
        on_translate: Callable[[DragEvent, "ActCircle"], Awaitable[bool]]
        | None = None,
        on_change: Callable[[Circle], None] | None = None,
        on_click: ActClickHandler | None = None,
    ) -> None:
        super().__init__(
            on_click=on_click,
            handle_style=handle_style,
            translate_handle_style=translate_handle_style,
            act_style=act_style,
            style=style,
        )
        self._center = Point(0.0, 0.0, 0.0) if center is None else center
        self._radius = float(radius)
        self._min_radius = min_radius
        self._max_radius = max_radius
        self._show_translate_handle = show_translate_handle
        self._on_radius_drag = on_radius_drag
        self._on_translate = on_translate
        self._on_change = on_change
        self._radius_handle: ActPoint | None = None
        self._translate_handle: ActPoint | None = None

    # ── Init (called by Visualizer) ────────────────────────

    def _init(self, viz_handle: VizSceneHandle, entity_id: str) -> None:
        super()._init(viz_handle, entity_id)
        self._spawn_handles()

    # ── Properties ─────────────────────────────────────────

    @property
    def circle(self) -> Circle:
        """The current :class:`~pytanga.geometry.Circle`."""
        return self._build_circle()

    @property
    def entity(self) -> Circle:
        """The rendered body entity (a ``Circle``)."""
        return self._build_circle()

    @property
    def center(self) -> Point:
        """The circle centre."""
        return self._center

    @property
    def radius(self) -> float:
        """The circle radius."""
        return self._radius

    @property
    def interaction_config(self) -> InteractionConfig:
        """The body is visual-only unless ``on_click`` was provided."""
        if self._on_click is None:
            return InteractionConfig(enabled=False, triggers=[])
        return InteractionConfig(
            enabled=True,
            triggers=[
                InteractionTrigger(
                    event_type=InteractionEventType.CLICK,
                    mouse_button=MouseButton.LEFT,
                )
            ],
        )

    # ── Geometry helpers ───────────────────────────────────

    def _build_circle(self) -> Circle:
        return Circle(center=self._center, radius=self._radius)

    def _radius_handle_position(self) -> Point:
        return Point(self._center.x + self._radius, self._center.y, self._center.z)

    def _spawn_handles(self) -> None:
        if self._viz_handle is None:
            return
        style = self._resolve_handle_style()
        translate_style = self._resolve_translate_handle_style()
        handle = ActPoint(
            self._radius_handle_position(),
            handler=self._make_radius_handler(),
            drag_mode=DragMode.XY_PLANE,
            act_style=self._act_style,

            on_click=self._handle_click_handler(),
        )
        self._spawn_handle(handle, style=style)
        self._radius_handle = handle
        if self._show_translate_handle:
            handle = ActPoint(
                self._center,
                handler=self._make_translate_handler(),
                drag_mode=DragMode.XY_PLANE,
                act_style=self._act_style,

                on_click=self._handle_click_handler(),
            )
            self._spawn_handle(handle, style=translate_style)
            self._translate_handle = handle


    # ── Handler closures ───────────────────────────────────

    def _make_radius_handler(self) -> ActHandler:
        async def handler(event: DragEvent, _handle: ActSceneObject) -> bool:
            return await self._dispatch_radius_drag(event)

        return handler

    def _make_translate_handler(self) -> ActHandler:
        async def handler(event: DragEvent, _handle: ActSceneObject) -> bool:
            return await self._dispatch_translate(event)

        return handler

    # ── Dispatch (overridable) ─────────────────────────────

    async def _dispatch_radius_drag(self, event: DragEvent) -> bool:
        if self._on_radius_drag is not None:
            return await self._on_radius_drag(event, self)
        self._resize_radius(event.world_position)
        return True

    async def _dispatch_translate(self, event: DragEvent) -> bool:
        if self._on_translate is not None:
            return await self._on_translate(event, self)
        self._translate_by(event.world_delta)
        return True

    # ── Default geometry mutations ─────────────────────────

    def _resize_radius(self, pos: Point) -> None:
        dx = pos.x - self._center.x
        dy = pos.y - self._center.y
        radius = math.hypot(dx, dy)
        floor = self._min_radius if self._min_radius is not None else _FLOAT_EPS
        radius = max(floor, radius)
        if self._max_radius is not None:
            radius = min(self._max_radius, radius)
        self._radius = radius
        self._commit()

    def set_radius_limits(
        self, min_radius: float | None, max_radius: float | None
    ) -> None:
        """Set the resize clamp (world units; ``None`` = floating-point min / unbounded max)."""
        self._min_radius = None if min_radius is None else float(min_radius)
        self._max_radius = None if max_radius is None else float(max_radius)

    def _translate_by(self, delta: Direction) -> None:
        self._center = Point(
            self._center.x + delta.x, self._center.y + delta.y, self._center.z
        )
        self._commit()

    def _commit(self) -> None:
        self.update()
        self._refresh_handles()
        self.flush()
        if self._on_change is not None:
            self._on_change(self._build_circle())

    def _refresh_handles(self) -> None:
        if self._radius_handle is not None:
            self._radius_handle.set_position(self._radius_handle_position())
        if self._translate_handle is not None:
            self._translate_handle.set_position(self._center)

    # ── Default movement (body never moves) ────────────────

    def _move_to(self, pos: Point) -> None:
        """The body is fixed; movement happens via the handles."""

    def drag_anchor(self, ray_origin: Point, ray_direction: Direction) -> Point:
        """Not used — the body has no interaction triggers."""
        return self._center

    # ── Removal ────────────────────────────────────────────

    def _on_remove(self) -> None:
        """Clear this composite's own handle references."""
        self._radius_handle = None
        self._translate_handle = None

    @classmethod
    def create_from_points(cls, a: Point, b: Point, **kwargs: Any) -> "ActCircle":
        """Build a circle from a center point and a rim point."""
        radius = math.hypot(b.x - a.x, b.y - a.y)
        min_r = kwargs.get("min_radius")
        if min_r is not None:
            radius = max(radius, float(min_r))
        return cls(center=a, radius=radius, **kwargs)


# ── ActPolygon ───────────────────────────────────────────────


class ActPolygon(_ActWithHandles):
    """An editable open/closed polygon rendered as a ``PointPath``.

    The body is a visual-only :class:`~pytanga.viz.PointPath`; all interaction
    happens through child :class:`ActPoint` handles — one per vertex plus a
    centroid translate handle.  Ctrl+dragging any vertex inserts a new vertex
    after it; Ctrl+right-clicking any vertex deletes it (keeping a closed
    polygon closed while at least three vertices remain); Alt+right-click also
    opens a closed polygon.

    Args:
        points: Initial vertex positions.
        closed: When ``True``, the rendered path is closed (default ``True``).
        show_translate_handle: Add a centroid translation handle (default ``True``).
        handle_style: Marker style for the vertex handles (default a circle marker).
        translate_handle_style: Marker style for the translation handle (default
            a move-icon glyph).
        end_handle_style: Marker style for the start/end vertices (defaults to
            ``handle_style``).
        auto_close: When ``True``, dragging an endpoint onto the other endpoint
            fuses the two endpoints into one and closes the path (default
            ``False``).  The resulting closed polygon has no distinct endpoints.
        close_tolerance: Distance (world units) within which the two endpoints
            count as coincident for auto-close.  ``None`` derives it from the
            handle ``size`` (the full handle width).
        act_style: Hover style for the handles.
        style: Optional visual style for the body entity, applied when the
            object is added without an explicit ``style=``.
        on_vertex_drag: Optional async callback overriding vertex drag.
        on_translate: Optional async callback overriding translation.
        on_change: Optional sync callback fired after any geometry change.
        on_removed: Optional sync callback fired when the whole polygon is
            removed (vertex deletion down to one vertex).
        on_click: Optional async callback invoked when the body is clicked.
    """

    def __init__(
        self,
        points: list[Point],
        *,
        closed: bool = True,
        show_translate_handle: bool = True,
        handle_style: PointStyle | None = None,
        translate_handle_style: PointStyle | None = None,
        end_handle_style: PointStyle | None = None,
        auto_close: bool = False,
        close_tolerance: float | None = None,
        act_style: ActPointStyle | None = None,
        style: Any = None,
        on_vertex_drag: Callable[[int, DragEvent, "ActPolygon"], Awaitable[bool]]
        | None = None,
        on_translate: Callable[[DragEvent, "ActPolygon"], Awaitable[bool]]
        | None = None,
        on_change: Callable[[list[Point]], None] | None = None,
        on_removed: Callable[[], None] | None = None,
        on_click: ActClickHandler | None = None,
    ) -> None:
        super().__init__(
            on_click=on_click,
            handle_style=handle_style,
            translate_handle_style=translate_handle_style,
            act_style=act_style,
            style=style,
        )
        self._points = [Point(p.x, p.y, p.z) for p in points]
        self._closed = closed
        self._show_translate_handle = show_translate_handle
        self._end_handle_style = end_handle_style
        self._auto_close = auto_close
        self._close_tolerance = close_tolerance
        self._on_vertex_drag = on_vertex_drag
        self._on_translate = on_translate
        self._on_change = on_change
        self._on_removed = on_removed
        self._vertex_handles: list[ActPoint] = []
        self._translate_handle: ActPoint | None = None
        # Index of the endpoint inserted by the in-flight Ctrl+drag, if any.
        self._insert_drag_index: int | None = None

    # ── Init (called by Visualizer) ────────────────────────

    def _init(self, viz_handle: VizSceneHandle, entity_id: str) -> None:
        super()._init(viz_handle, entity_id)
        self._spawn_handles()

    # ── Properties ─────────────────────────────────────────

    @property
    def points(self) -> list[Point]:
        """A copy of the current vertex positions."""
        return list(self._points)

    @property
    def closed(self) -> bool:
        """Whether the polygon is closed."""
        return self._closed

    @property
    def entity(self) -> PointPath:
        """The rendered body entity (a ``PointPath``)."""
        return self._build_path()

    @property
    def interaction_config(self) -> InteractionConfig:
        """The body is visual-only unless ``on_click`` was provided."""
        if self._on_click is None:
            return InteractionConfig(enabled=False, triggers=[])
        return InteractionConfig(
            enabled=True,
            triggers=[
                InteractionTrigger(
                    event_type=InteractionEventType.CLICK,
                    mouse_button=MouseButton.LEFT,
                )
            ],
        )

    # ── Geometry helpers ───────────────────────────────────

    def _build_path(self) -> PointPath:
        path = PointPath()
        for p in self._points:
            path.add((p.x, p.y, p.z))
        if self._closed and len(self._points) > 1:
            first = self._points[0]
            path.add((first.x, first.y, first.z))
        return path

    def _centroid(self) -> Point:
        if not self._points:
            return Point(0.0, 0.0, 0.0)
        n = len(self._points)
        return Point(
            sum(p.x for p in self._points) / n,
            sum(p.y for p in self._points) / n,
            sum(p.z for p in self._points) / n,
        )

    def _is_endpoint(self, index: int) -> bool:
        if self._closed:
            return False  # a closed polygon has no endpoints
        return index == 0 or index == len(self._points) - 1

    def _maybe_auto_close(self, index: int) -> bool:
        """Fuse the endpoints and close the path when they overlap.

        With ``auto_close``, dragging an endpoint within ``close_tolerance`` of
        the other endpoint merges the two endpoints into one and closes the
        path.  Returns ``True`` when the fusion happened.
        """
        if not self._auto_close:
            return False
        if len(self._points) < 3 or not self._is_endpoint(index):
            return False
        start = self._points[0]
        end = self._points[-1]
        dx = end.x - start.x
        dy = end.y - start.y
        tol = self._effective_close_tolerance()
        if (dx * dx + dy * dy) > tol * tol:
            return False
        self._fuse_endpoints()
        return True

    def _fuse_endpoints(self) -> None:
        """Merge the two endpoints into one and close the polygon."""
        self._points.pop(-1)  # the start vertex becomes the joint
        self._closed = True
        self._auto_close = False
        self._rebuild_handles()
        self._commit()

    def _effective_close_tolerance(self) -> float:
        """The auto-close distance (world units).

        An explicit ``close_tolerance`` wins; otherwise it is derived from the
        handle size (the full handle width = ``2 * size``).
        """
        if self._close_tolerance is not None:
            return float(self._close_tolerance)
        return 2.0 * self._handle_world_size()

    def _spawn_handles(self) -> None:
        if self._viz_handle is None:
            return
        style = self._resolve_handle_style()
        translate_style = self._resolve_translate_handle_style()
        end_style = self._end_handle_style or style
        for i, p in enumerate(self._points):
            handle = ActPoint(
                p,
                handler=self._make_vertex_handler(i),
                on_drag_end=self._make_vertex_drag_end(),
                drag_mode=DragMode.XY_PLANE,
                act_style=self._act_style,

                on_click=self._handle_click_handler(),
                click_bindings=self._make_delete_bindings(i),
            )
            self._spawn_handle(
                handle, style=end_style if self._is_endpoint(i) else style
            )
            self._vertex_handles.append(handle)
        if self._show_translate_handle:
            handle = ActPoint(
                self._centroid(),
                handler=self._make_translate_handler(),
                drag_mode=DragMode.XY_PLANE,
                act_style=self._act_style,

                on_click=self._handle_click_handler(),
            )
            self._spawn_handle(handle, style=translate_style)
            self._translate_handle = handle

    def _rebuild_handles(self) -> None:
        """Re-spawn all handles after the vertex count changes."""
        self._remove_handles()
        self._vertex_handles.clear()
        self._translate_handle = None
        self._spawn_handles()

    # ── Handler closures ───────────────────────────────────

    def _make_vertex_handler(self, index: int) -> ActHandler:
        async def handler(event: DragEvent, _handle: ActSceneObject) -> bool:
            return await self._dispatch_vertex_drag(index, event)

        return handler

    def _make_vertex_drag_end(self) -> ActEventHandler:
        async def handler(event: DragEvent, _handle: ActSceneObject) -> None:
            self._finish_vertex_drag()

        return handler

    def _make_translate_handler(self) -> ActHandler:
        async def handler(event: DragEvent, _handle: ActSceneObject) -> bool:
            return await self._dispatch_translate(event)

        return handler

    def _make_delete_bindings(
        self, index: int
    ) -> list[ClickBinding[ActSceneObject]] | None:
        async def delete_handler(event: ClickEvent, _handle: ActSceneObject) -> None:
            self._delete_vertex(index, open=False)

        async def delete_open_handler(
            event: ClickEvent, _handle: ActSceneObject
        ) -> None:
            self._delete_vertex(index, open=True)

        return [
            ClickBinding(MouseButton.RIGHT, delete_handler, ModifierKey.CTRL),
            ClickBinding(
                MouseButton.RIGHT,
                delete_open_handler,
                ModifierKey.ALT,
            ),
        ]

    # ── Dispatch (overridable) ─────────────────────────────

    async def _dispatch_vertex_drag(self, index: int, event: DragEvent) -> bool:
        if self._on_vertex_drag is not None:
            return await self._on_vertex_drag(index, event, self)
        if self._insert_drag_index is not None:
            # Continuation of a Ctrl+drag insert: move the newly-inserted
            # endpoint (the original endpoint's index is now stale).
            self._set_vertex_body(self._insert_drag_index, event.world_position)
            return True
        if ModifierKey.CTRL in event.modifiers:
            # First Ctrl+drag move on a vertex: insert a new vertex after it and
            # remember it so the rest of this drag moves the new vertex.
            self._insert_drag_index = self._insert_after(index, event.world_position)
            return True
        self._move_vertex(index, event.world_position)
        return True

    async def _dispatch_translate(self, event: DragEvent) -> bool:
        if self._on_translate is not None:
            return await self._on_translate(event, self)
        self._translate_by(event.world_delta)
        return True

    # ── Default geometry mutations ─────────────────────────

    def _move_vertex(self, index: int, pos: Point) -> None:
        self._points[index] = Point(pos.x, pos.y, pos.z)
        if self._maybe_auto_close(index):
            return  # the endpoints fused: the polygon is now closed
        self._commit()

    def _insert_after(self, index: int, pos: Point) -> int:
        """Insert a new vertex after *index* and return its index.

        The handle set is *not* rebuilt here — the caller defers that to drag
        end, so an in-flight Ctrl+drag isn't cancelled by removing the handle
        being dragged.
        """
        p = Point(pos.x, pos.y, pos.z)
        # The start vertex is the one exception to the insert-after rule: a
        # Ctrl+drag on it prepends so the new point becomes the new start.
        new_index = 0 if index == 0 else index + 1
        self._points.insert(new_index, p)
        self._update_body()
        return new_index

    def _set_vertex_body(self, index: int, pos: Point) -> None:
        """Move a vertex and update the body without refreshing handles."""
        self._points[index] = Point(pos.x, pos.y, pos.z)
        self._update_body()

    def _finish_vertex_drag(self) -> None:
        """End a vertex drag: rebuild handles if an insert is pending."""
        if self._insert_drag_index is not None:
            self._insert_drag_index = None
            self._rebuild_handles()
            self._commit()

    def _delete_vertex(self, index: int, *, open: bool = False) -> None:
        if len(self._points) <= 2:
            # Deleting would leave a single vertex → remove the whole composite.
            self.remove()
            if self._on_removed is not None:
                self._on_removed()
            return
        self._points.pop(index)
        if open:
            self._closed = False
            self._auto_close = True  # re-enable so the endpoints can be re-fused
        elif self._closed and len(self._points) < 3:
            self._closed = False
        self._rebuild_handles()
        self._commit()

    def _translate_by(self, delta: Direction) -> None:
        self._points = [
            Point(p.x + delta.x, p.y + delta.y, p.z) for p in self._points
        ]
        self._commit()

    def _update_body(self) -> None:
        """Update the body entity + flush, without touching the handles."""
        self.update()
        self.flush()
        if self._on_change is not None:
            self._on_change(list(self._points))

    def _commit(self) -> None:
        self.update()
        self._refresh_handles()
        self.flush()
        if self._on_change is not None:
            self._on_change(list(self._points))

    def _refresh_handles(self) -> None:
        for i, handle in enumerate(self._vertex_handles):
            handle.set_position(self._points[i])
        if self._translate_handle is not None:
            self._translate_handle.set_position(self._centroid())

    # ── Default movement (body never moves) ────────────────

    def _move_to(self, pos: Point) -> None:
        """The body is fixed; movement happens via the handles."""

    def drag_anchor(self, ray_origin: Point, ray_direction: Direction) -> Point:
        """Not used — the body has no interaction triggers."""
        return self._centroid()

    # ── Removal ────────────────────────────────────────────

    def _on_remove(self) -> None:
        """Clear this composite's own handle references."""
        self._vertex_handles.clear()
        self._translate_handle = None

    @classmethod
    def create_from_points(cls, a: Point, b: Point, **kwargs: Any) -> "ActPolygon":
        """Build a 2-vertex open polygon from two anchor points."""
        kwargs.setdefault("closed", False)
        kwargs.setdefault("auto_close", True)
        return cls([Point(a.x, a.y, a.z), Point(b.x, b.y, b.z)], **kwargs)


# ── ActLine ──────────────────────────────────────────────────


class ActLine(_ActWithHandles):
    """An interactive 2-point line segment rendered as a ``Line``.

    The body is a visual-only :class:`~pytanga.geometry.Line` (via
    ``Line.from_points``); interaction happens through two endpoint handles and
    a midpoint translate handle.  A line always has exactly two points and is
    never closed.

    Args:
        start: Start point (default ``(0, 0, 0)``).
        end: End point (default ``(1, 0, 0)``).
        show_translate_handle: Add a midpoint translation handle (default ``True``).
        handle_style: Marker style for the endpoint handles (default a circle
            marker).
        translate_handle_style: Marker style for the translation handle (default
            a move-icon glyph).
        act_style: Hover style for the handles.
        style: Optional visual style for the body entity, applied when the
            object is added without an explicit ``style=``.
        on_endpoint_drag: Optional async callback overriding endpoint drag.
            Signature ``async def h(i, event: DragEvent, line) -> bool``.
        on_translate: Optional async callback overriding translation.
            Signature ``async def h(event: DragEvent, line) -> bool``.
        on_change: Optional sync callback fired after any geometry change.
            Signature ``def h(line: Line) -> None``.
        on_click: Optional async callback invoked when the body is clicked.
            Providing it makes the body clickable (selectable).
    """

    def __init__(
        self,
        start: Point | None = None,
        end: Point | None = None,
        *,
        show_translate_handle: bool = True,
        handle_style: PointStyle | None = None,
        translate_handle_style: PointStyle | None = None,
        act_style: ActPointStyle | None = None,
        style: Any = None,
        on_endpoint_drag: Callable[[int, DragEvent, "ActLine"], Awaitable[bool]]
        | None = None,
        on_translate: Callable[[DragEvent, "ActLine"], Awaitable[bool]] | None = None,
        on_change: Callable[[Line], None] | None = None,
        on_click: ActClickHandler | None = None,
    ) -> None:
        super().__init__(
            on_click=on_click,
            handle_style=handle_style,
            translate_handle_style=translate_handle_style,
            act_style=act_style,
            style=style,
        )
        self._start = Point(0.0, 0.0, 0.0) if start is None else start
        self._end = Point(1.0, 0.0, 0.0) if end is None else end
        self._show_translate_handle = show_translate_handle
        self._on_endpoint_drag = on_endpoint_drag
        self._on_translate = on_translate
        self._on_change = on_change
        self._endpoint_handles: list[ActPoint] = []
        self._translate_handle: ActPoint | None = None

    # ── Init (called by Visualizer) ────────────────────────

    def _init(self, viz_handle: VizSceneHandle, entity_id: str) -> None:
        super()._init(viz_handle, entity_id)
        self._spawn_handles()

    # ── Properties ─────────────────────────────────────────

    @property
    def line(self) -> Line:
        """The current :class:`~pytanga.geometry.Line`."""
        return self._build_line()

    @property
    def entity(self) -> Line:
        """The rendered body entity (a ``Line``)."""
        return self._build_line()

    @property
    def start(self) -> Point:
        """The start point."""
        return self._start

    @property
    def end(self) -> Point:
        """The end point."""
        return self._end

    @property
    def interaction_config(self) -> InteractionConfig:
        """The body is visual-only unless ``on_click`` was provided."""
        if self._on_click is None:
            return InteractionConfig(enabled=False, triggers=[])
        return InteractionConfig(
            enabled=True,
            triggers=[
                InteractionTrigger(
                    event_type=InteractionEventType.CLICK,
                    mouse_button=MouseButton.LEFT,
                )
            ],
        )

    # ── Geometry helpers ───────────────────────────────────

    def _build_line(self) -> Line:
        return Line.from_points(self._start, self._end)

    def _endpoint_positions(self) -> list[Point]:
        return [self._start, self._end]

    def _midpoint(self) -> Point:
        return Point(
            (self._start.x + self._end.x) / 2.0,
            (self._start.y + self._end.y) / 2.0,
            (self._start.z + self._end.z) / 2.0,
        )

    def _spawn_handles(self) -> None:
        if self._viz_handle is None:
            return
        style = self._resolve_handle_style()
        translate_style = self._resolve_translate_handle_style()
        for i, pos in enumerate(self._endpoint_positions()):
            handle = ActPoint(
                pos,
                handler=self._make_endpoint_handler(i),
                drag_mode=DragMode.XY_PLANE,
                act_style=self._act_style,

                on_click=self._handle_click_handler(),
            )
            self._spawn_handle(handle, style=style)
            self._endpoint_handles.append(handle)
        if self._show_translate_handle:
            handle = ActPoint(
                self._midpoint(),
                handler=self._make_translate_handler(),
                drag_mode=DragMode.XY_PLANE,
                act_style=self._act_style,

                on_click=self._handle_click_handler(),
            )
            self._spawn_handle(handle, style=translate_style)
            self._translate_handle = handle

    # ── Handler closures ───────────────────────────────────

    def _make_endpoint_handler(self, index: int) -> ActHandler:
        async def handler(event: DragEvent, _handle: ActSceneObject) -> bool:
            return await self._dispatch_endpoint_drag(index, event)

        return handler

    def _make_translate_handler(self) -> ActHandler:
        async def handler(event: DragEvent, _handle: ActSceneObject) -> bool:
            return await self._dispatch_translate(event)

        return handler

    # ── Dispatch (overridable) ─────────────────────────────

    async def _dispatch_endpoint_drag(self, index: int, event: DragEvent) -> bool:
        if self._on_endpoint_drag is not None:
            return await self._on_endpoint_drag(index, event, self)
        self._move_endpoint(index, event.world_position)
        return True

    async def _dispatch_translate(self, event: DragEvent) -> bool:
        if self._on_translate is not None:
            return await self._on_translate(event, self)
        self._translate_by(event.world_delta)
        return True

    # ── Default geometry mutations ─────────────────────────

    def _move_endpoint(self, index: int, pos: Point) -> None:
        p = Point(pos.x, pos.y, pos.z)
        if index == 0:
            self._start = p
        else:
            self._end = p
        self._commit()

    def _translate_by(self, delta: Direction) -> None:
        self._start = Point(self._start.x + delta.x, self._start.y + delta.y, self._start.z)
        self._end = Point(self._end.x + delta.x, self._end.y + delta.y, self._end.z)
        self._commit()

    def _commit(self) -> None:
        self.update()
        self._refresh_handles()
        self.flush()
        if self._on_change is not None:
            self._on_change(self._build_line())

    def _refresh_handles(self) -> None:
        positions = self._endpoint_positions()
        for i, handle in enumerate(self._endpoint_handles):
            handle.set_position(positions[i])
        if self._translate_handle is not None:
            self._translate_handle.set_position(self._midpoint())

    # ── Default movement (body never moves) ────────────────

    def _move_to(self, pos: Point) -> None:
        """The body is fixed; movement happens via the handles."""

    def drag_anchor(self, ray_origin: Point, ray_direction: Direction) -> Point:
        """Not used — the body has no interaction triggers."""
        return self._midpoint()

    # ── Removal ────────────────────────────────────────────

    def _on_remove(self) -> None:
        """Clear this composite's own handle references."""
        self._endpoint_handles.clear()
        self._translate_handle = None

    @classmethod
    def create_from_points(cls, a: Point, b: Point, **kwargs: Any) -> "ActLine":
        """Build a line segment from two points."""
        return cls(start=a, end=b, **kwargs)

