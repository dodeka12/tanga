# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Object interaction types, handler registry, and utilities.

Defines enums, dataclasses, and an async handler registry for pointer-based
object interaction in the Tanga 3D viewer.  The frontend captures pointer
events (click, double-click, drag, scroll) on 3D entities and sends them
over WebSocket; the backend dispatches them to user-registered handlers
with drag-move coalescing.

.. note::
   This module is the Python-side data model.  The frontend counterpart is
   :file:`py/pytanga/viz/templates/interaction.js` (Phase 5).
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

_logger = logging.getLogger(__name__)


# ── Enums ──────────────────────────────────────────────────────


class InteractionEventType(Enum):
    """Types of pointer interactions the frontend can report.

    The :attr:`DRAG` member is a trigger-only umbrella — it is **not** sent
    by the frontend as an event type, but used in :class:`InteractionTrigger`
    to match all three drag phases (:attr:`DRAG_START`, :attr:`DRAG_MOVE`,
    :attr:`DRAG_END`).
    """

    CLICK = "click"
    DBLCLICK = "dblclick"
    DRAG = "drag"            # umbrella for triggers — never sent as event_type
    DRAG_START = "drag_start"
    DRAG_MOVE = "drag_move"
    DRAG_END = "drag_end"
    SCROLL = "scroll"


class MouseButton(Enum):
    """Mouse button identifiers matching Three.js button codes."""

    LEFT = "left"       # button 0 in Three.js
    MIDDLE = "middle"   # button 1 in Three.js
    RIGHT = "right"     # button 2 in Three.js

    @classmethod
    def from_js_code(cls, code: int) -> "MouseButton":
        """Convert a Three.js mouse button code (0/1/2) to enum member."""
        mapping = {0: cls.LEFT, 1: cls.MIDDLE, 2: cls.RIGHT}
        if code not in mapping:
            raise ValueError(f"Unknown mouse button code: {code}")
        return mapping[code]

    def to_js_code(self) -> int:
        """Convert enum member to Three.js mouse button code."""
        mapping = {MouseButton.LEFT: 0, MouseButton.MIDDLE: 1, MouseButton.RIGHT: 2}
        return mapping[self]


class ModifierKey(Enum):
    """Keyboard modifier keys."""

    CTRL = "ctrl"
    SHIFT = "shift"
    ALT = "alt"


class DragMode(Enum):
    """Constraint plane for ray intersection during dragging.

    Determines which plane the mouse ray is intersected with to compute
    ``world_position`` during a drag.  Stored per-trigger so different
    mouse buttons or modifier combinations can use different planes.
    """

    VIEW_PLANE = "view_plane"   # plane ⟂ camera view at initial depth
    XY_PLANE = "xy_plane"       # world XY plane at z = z₀
    XZ_PLANE = "xz_plane"       # world XZ plane at y = y₀
    YZ_PLANE = "yz_plane"       # world YZ plane at x = x₀


# ── Configuration dataclasses ──────────────────────────────────


@dataclass
class InteractionTrigger:
    """Defines one type of interaction the frontend should capture and report.

    Attributes:
        event_type: The interaction kind (click, drag, scroll, etc.).
        mouse_button: The mouse button that must be pressed, or ``None`` for
            any button (or irrelevant, e.g. scroll).
        modifiers: Set of modifier keys that must be held.  An empty set means
            no modifiers are required (the trigger fires regardless).
    """

    event_type: InteractionEventType
    mouse_button: MouseButton | None = None
    modifiers: frozenset[ModifierKey] = frozenset()
    drag_mode: DragMode = DragMode.VIEW_PLANE

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-ready dict."""
        result: dict[str, Any] = {"event_type": self.event_type.value}
        if self.mouse_button is not None:
            result["mouse_button"] = self.mouse_button.value
        if self.modifiers:
            result["modifiers"] = sorted([m.value for m in self.modifiers])
        else:
            result["modifiers"] = []
        if self.event_type == InteractionEventType.DRAG:
            result["drag_mode"] = self.drag_mode.value
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InteractionTrigger":
        """Deserialize from a JSON dict."""
        drag_mode = DragMode.VIEW_PLANE
        if "drag_mode" in data:
            drag_mode = DragMode(data["drag_mode"])
        return cls(
            event_type=InteractionEventType(data["event_type"]),
            mouse_button=MouseButton(data["mouse_button"])
            if data.get("mouse_button")
            else None,
            modifiers=frozenset(
                ModifierKey(m) for m in data.get("modifiers", [])
            ),
            drag_mode=drag_mode,
        )


@dataclass
class InteractionConfig:
    """Per-entity interaction configuration sent to the frontend.

    Attributes:
        enabled: Master switch.  When ``False``, no events are captured for
            this entity.
        triggers: List of trigger definitions.  Only event types listed here
            produce WebSocket messages.
        throttle_ms: Minimum interval in milliseconds between consecutive
            events of the same type for the same object.  ``0`` disables
            throttling entirely.
    """

    enabled: bool = False
    triggers: list[InteractionTrigger] = field(default_factory=list)
    throttle_ms: int = 50

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-ready dict."""
        return {
            "enabled": self.enabled,
            "triggers": [t.to_dict() for t in self.triggers],
            "throttle_ms": self.throttle_ms,
        }


# ── Event dataclasses ──────────────────────────────────────────


@dataclass
class ControlEvent:
    """Base class for all interaction events.

    All events carry the current camera frame so handlers can transform
    between screen space and world space without additional round-trips.
    """

    browser_id: str | None = None
    camera_right: tuple[float, float, float] = (0.0, 0.0, 0.0)
    camera_up: tuple[float, float, float] = (0.0, 0.0, 0.0)
    camera_view: tuple[float, float, float] = (0.0, 0.0, 0.0)
    camera_distance: float = 0.0


@dataclass
class ClickEvent(ControlEvent):
    """Fired when the user clicks or double-clicks an interactive object.

    ``event_type`` will be :attr:`~InteractionEventType.CLICK` or
    :attr:`~InteractionEventType.DBLCLICK`.
    """

    object_id: str = ""
    event_type: InteractionEventType = InteractionEventType.CLICK
    mouse_button: MouseButton = MouseButton.LEFT
    modifiers: frozenset[ModifierKey] = frozenset()
    screen_position: tuple[float, float] = (0.0, 0.0)
    world_position: tuple[float, float, float] = (0.0, 0.0, 0.0)
    world_normal: tuple[float, float, float] = (0.0, 0.0, 0.0)


@dataclass
class DragEvent(ControlEvent):
    """Fired during pointer drags on an interactive object.

    ``event_type`` will be :attr:`~InteractionEventType.DRAG_START`,
    :attr:`~InteractionEventType.DRAG_MOVE`, or
    :attr:`~InteractionEventType.DRAG_END`.

    The frontend computes ``world_position`` by intersecting the
    pixel-position ray with the plane perpendicular to ``camera_view``
    at ``camera_distance`` (cached at drag start).  ``world_delta``
    is the change since the previous drag event.
    """

    object_id: str = ""
    event_type: InteractionEventType = InteractionEventType.DRAG_MOVE
    mouse_button: MouseButton = MouseButton.LEFT
    modifiers: frozenset[ModifierKey] = frozenset()
    screen_position: tuple[float, float] = (0.0, 0.0)
    delta_pixels: tuple[float, float] = (0.0, 0.0)
    world_position: tuple[float, float, float] = (0.0, 0.0, 0.0)
    world_delta: tuple[float, float, float] = (0.0, 0.0, 0.0)
    drag_mode: DragMode = DragMode.VIEW_PLANE


@dataclass
class ScrollEvent(ControlEvent):
    """Fired when the user scrolls while hovering an interactive object."""

    object_id: str = ""
    event_type: InteractionEventType = InteractionEventType.SCROLL
    modifiers: frozenset[ModifierKey] = frozenset()
    screen_position: tuple[float, float] = (0.0, 0.0)
    delta_xy: tuple[float, float] = (0.0, 0.0)  # raw scroll delta


# ── Deserialization helpers ────────────────────────────────────


def _parse_modifiers(modifiers_list: list[str]) -> frozenset[ModifierKey]:
    """Parse a list of modifier strings from JSON into a frozenset."""
    return frozenset(ModifierKey(m) for m in modifiers_list)


def _parse_camera_frame(data: dict[str, Any]) -> dict[str, Any]:
    """Extract camera frame fields from a JSON dict."""
    return dict(
        camera_right=tuple(data.get("camera_right", [0.0, 0.0, 0.0])),
        camera_up=tuple(data.get("camera_up", [0.0, 0.0, 0.0])),
        camera_view=tuple(data.get("camera_view", [0.0, 0.0, 0.0])),
        camera_distance=float(data.get("camera_distance", 0.0)),
    )


def _parse_event(data: dict[str, Any]) -> ControlEvent:
    """Parse a JSON dict into the appropriate event dataclass.

    Dispatches on ``data["event_type"]``.
    """
    event_type_str = data.get("event_type", "")
    try:
        event_type = InteractionEventType(event_type_str)
    except ValueError:
        raise ValueError(
            f"Unknown interaction event type: {event_type_str!r}"
        ) from None

    modifiers = _parse_modifiers(data.get("modifiers", []))
    browser_id = data.get("browser_id")
    cam = _parse_camera_frame(data)

    if event_type in (InteractionEventType.CLICK, InteractionEventType.DBLCLICK):
        return ClickEvent(
            browser_id=browser_id,
            object_id=data.get("object_id", ""),
            event_type=event_type,
            mouse_button=MouseButton(data.get("mouse_button", "left")),
            modifiers=modifiers,
            screen_position=tuple(data.get("screen_position", [0.0, 0.0])),
            world_position=tuple(data.get("world_position", [0.0, 0.0, 0.0])),
            world_normal=tuple(data.get("world_normal", [0.0, 0.0, 0.0])),
            **cam,
        )

    if event_type in (
        InteractionEventType.DRAG_START,
        InteractionEventType.DRAG_MOVE,
        InteractionEventType.DRAG_END,
    ):
        drag_mode = DragMode.VIEW_PLANE
        if "drag_mode" in data:
            try:
                drag_mode = DragMode(data["drag_mode"])
            except ValueError:
                pass
        return DragEvent(
            browser_id=browser_id,
            object_id=data.get("object_id", ""),
            event_type=event_type,
            mouse_button=MouseButton(data.get("mouse_button", "left")),
            modifiers=modifiers,
            screen_position=tuple(data.get("screen_position", [0.0, 0.0])),
            delta_pixels=tuple(data.get("delta_pixels", [0.0, 0.0])),
            world_position=tuple(data.get("world_position", [0.0, 0.0, 0.0])),
            world_delta=tuple(data.get("world_delta", [0.0, 0.0, 0.0])),
            drag_mode=drag_mode,
            **cam,
        )

    if event_type == InteractionEventType.SCROLL:
        return ScrollEvent(
            browser_id=browser_id,
            object_id=data.get("object_id", ""),
            event_type=event_type,
            modifiers=modifiers,
            screen_position=tuple(data.get("screen_position", [0.0, 0.0])),
            delta_xy=tuple(data.get("delta_xy", [0.0, 0.0])),
            **cam,
        )

    raise ValueError(f"Unhandled interaction event type: {event_type!r}")


# ── Drag move coalescing ───────────────────────────────────────


def _coalesce_drag_events(events: list[DragEvent]) -> DragEvent:
    """Merge multiple drag_move events into one by accumulating deltas.

    All events must have the same ``object_id`` and ``event_type``.  The
    result uses the latest ``screen_position``, ``world_position``,
    ``world_delta``, ``modifiers``, and camera frame.

    ``delta_pixels`` and ``world_delta`` are summed across events.

    Returns:
        The single event unchanged if *events* has length 1.
    """
    if not events:
        raise ValueError("Cannot coalesce empty event list")
    if len(events) == 1:
        return events[0]

    first = events[0]
    total_delta_x = sum(e.delta_pixels[0] for e in events)
    total_delta_y = sum(e.delta_pixels[1] for e in events)
    total_wx = sum(e.world_delta[0] for e in events)
    total_wy = sum(e.world_delta[1] for e in events)
    total_wz = sum(e.world_delta[2] for e in events)
    last = events[-1]

    return DragEvent(
        browser_id=last.browser_id,
        object_id=first.object_id,
        event_type=first.event_type,
        mouse_button=first.mouse_button,
        modifiers=last.modifiers,
        screen_position=last.screen_position,
        delta_pixels=(total_delta_x, total_delta_y),
        world_position=last.world_position,
        world_delta=(total_wx, total_wy, total_wz),
        camera_right=last.camera_right,
        camera_up=last.camera_up,
        camera_view=last.camera_view,
        camera_distance=last.camera_distance,
    )


# ── Handler type alias ─────────────────────────────────────────

Handler = Callable[[Any], Awaitable[None]]
"""Async callback receiving a :class:`ClickEvent`, :class:`DragEvent`, or
:class:`ScrollEvent`."""


# ── Handler registry ───────────────────────────────────────────


class InteractionHandlerRegistry:
    """Maps ``(object_id, event_type)`` pairs to async handler callables.

    Provides drag_move coalescing: when multiple ``DRAG_MOVE`` events arrive
    for the same object while a handler is still processing, they are merged
    into a single event before the next handler invocation.  This prevents
    unbounded queue growth and reduces handler calls during rapid dragging.
    """

    def __init__(self) -> None:
        self._handlers: dict[tuple[str, InteractionEventType], Handler] = {}
        # Per-object state for coalescing
        self._pending: dict[str, list[DragEvent]] = {}
        self._running: dict[str, bool] = {}

    # ── Registration ───────────────────────────────────────────

    def register(
        self,
        object_id: str,
        event_type: InteractionEventType,
        handler: Handler,
    ) -> None:
        """Register an async handler for a specific object + event type."""
        self._handlers[(object_id, event_type)] = handler

    def unregister(
        self,
        object_id: str,
        event_type: InteractionEventType | None = None,
    ) -> None:
        """Remove handler(s).

        If *event_type* is ``None``, remove all handlers for *object_id*.
        """
        if event_type is None:
            keys = [k for k in self._handlers if k[0] == object_id]
            for k in keys:
                del self._handlers[k]
        else:
            self._handlers.pop((object_id, event_type), None)

    def get(
        self, object_id: str, event_type: InteractionEventType
    ) -> Handler | None:
        """Look up a handler, or ``None``."""
        return self._handlers.get((object_id, event_type))

    def clear(self) -> None:
        """Remove all handlers and pending queues."""
        self._handlers.clear()
        self._pending.clear()
        self._running.clear()

    # ── Dispatch ───────────────────────────────────────────────

    async def dispatch(self, event: ControlEvent) -> None:
        """Fire-and-forget dispatch with drag_move coalescing.

        * ``DRAG_START`` / ``DRAG_END``: flush pending queue, dispatch
          immediately.
        * ``DRAG_MOVE``: if handler is running, queue the event for later
          coalescing.  Otherwise dispatch immediately.
        * Other event types: dispatch immediately (no coalescing needed).
        """
        if isinstance(event, DragEvent):
            handler = self.get(event.object_id, event.event_type)
            if handler is None:
                return

            if event.event_type in (
                InteractionEventType.DRAG_START,
                InteractionEventType.DRAG_END,
            ):
                # Flush pending before dispatching start/end
                self._pending.pop(event.object_id, None)
                self._running[event.object_id] = True
                asyncio.create_task(self._run_handler(handler, event))

            elif event.event_type == InteractionEventType.DRAG_MOVE:
                if self._running.get(event.object_id, False):
                    # Handler is busy — queue
                    self._pending.setdefault(event.object_id, []).append(event)
                else:
                    self._running[event.object_id] = True
                    asyncio.create_task(self._run_handler(handler, event))
        else:
            handler = self.get(event.object_id, event.event_type)
            if handler is not None:
                asyncio.create_task(handler(event))

    async def _run_handler(self, handler: Handler, event: DragEvent) -> None:
        """Run a drag handler and process any coalesced pending events."""
        try:
            await handler(event)
        except Exception:
            _logger.exception(
                "Interaction handler raised an exception for object %s",
                event.object_id,
            )
        finally:
            obj_id = event.object_id
            # Check for coalesced pending events
            pending = self._pending.get(obj_id, [])
            if pending:
                self._pending.pop(obj_id, None)
                coalesced = _coalesce_drag_events(pending)
                next_handler = self.get(
                    obj_id, InteractionEventType.DRAG_MOVE
                )
                if next_handler is not None:
                    self._running[obj_id] = True
                    asyncio.create_task(
                        self._run_handler(next_handler, coalesced)
                    )
                    return  # _run_handler will clear _running when done
            self._running[obj_id] = False