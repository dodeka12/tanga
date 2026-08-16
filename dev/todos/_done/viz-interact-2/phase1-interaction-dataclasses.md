# Phase 1 — Interaction Dataclasses, Enums & Handler Registry

**Prerequisites:** None (new file, no dependencies on other phases)

**Goal:** Create `py/pytanga/viz/_interaction.py` containing all enums, dataclasses,
the handler registry, drag-move coalescing logic, and utility functions.
Export from `py/pytanga/viz/__init__.py`.

---

## 1. Motivation

The existing `_controls.py` provides `ControlEvent`, `ControlHandlerRegistry` and UI
control dataclasses (sliders, dropdowns, buttons) for fixed DOM panel controls.
Object interaction is fundamentally different: events originate from pointer
interaction on 3D meshes, carry spatial context (world position, pixel-to-world
transforms), and need throttled, coalesced delivery.

This phase defines the Python-side data model. The frontend counterpart is Phase 5.

---

## 2. New File: `py/pytanga/viz/_interaction.py`

### 2.1 Enums

```python
from enum import Enum


class InteractionEventType(Enum):
    """Types of pointer interactions the frontend can report."""
    CLICK = "click"
    DBLCLICK = "dblclick"
    DRAG_START = "drag_start"
    DRAG_MOVE = "drag_move"
    DRAG_END = "drag_end"
    SCROLL = "scroll"


class MouseButton(Enum):
    """Mouse button identifiers matching Three.js button codes."""
    LEFT = "left"     # button 0 in Three.js
    MIDDLE = "middle" # button 1 in Three.js
    RIGHT = "right"   # button 2 in Three.js

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
```

### 2.2 Dataclasses

```python
@dataclass
class InteractionTrigger:
    """Defines one type of interaction the frontend should capture and report.

    Attributes:
        event_type: The interaction kind (click, drag, scroll, etc.).
        mouse_button: The mouse button that must be pressed, or ``None`` for any
            button.  Scroll triggers typically leave this as ``None``.
        modifiers: Set of modifier keys that must be held.  Empty frozenset
            means no modifiers required.
    """
    event_type: InteractionEventType
    mouse_button: MouseButton | None = None
    modifiers: frozenset[ModifierKey] = frozenset()

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-ready dict."""
        result: dict[str, Any] = {"event_type": self.event_type.value}
        if self.mouse_button is not None:
            result["mouse_button"] = self.mouse_button.value
        if self.modifiers:
            result["modifiers"] = [m.value for m in sorted(self.modifiers, key=lambda m: m.value)]
        else:
            result["modifiers"] = []
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InteractionTrigger":
        """Deserialize from JSON dict."""
        return cls(
            event_type=InteractionEventType(data["event_type"]),
            mouse_button=MouseButton(data["mouse_button"]) if data.get("mouse_button") else None,
            modifiers=frozenset(ModifierKey(m) for m in data.get("modifiers", [])),
        )


@dataclass
class InteractionConfig:
    """Per-entity interaction configuration sent to the frontend.

    Attributes:
        enabled: Master switch.  When ``False``, no events are captured.
        triggers: List of trigger definitions.  Only event types listed here
            are sent to the backend.
        throttle_ms: Minimum interval between consecutive events of the same
            type for the same object.  ``0`` disables throttling.
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
```

### 2.3 Event Dataclasses

```python
@dataclass
class ControlEvent:
    """Base class for all interaction events."""
    browser_id: str | None = None


@dataclass
class ClickEvent(ControlEvent):
    """Fired when the user clicks or double-clicks an interactive object.

    ``event_type`` will be ``InteractionEventType.CLICK`` or
    ``InteractionEventType.DBLCLICK``.
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

    ``event_type`` will be ``InteractionEventType.DRAG_START``,
    ``InteractionEventType.DRAG_MOVE``, or ``InteractionEventType.DRAG_END``.

    ``delta_pixels`` is the screen-space change since the last event.
    ``delta_transform`` is a 4×4 row-major matrix mapping pixel deltas to
    world-space deltas at the object's depth (see :func:`apply_delta_transform`).
    """
    object_id: str = ""
    event_type: InteractionEventType = InteractionEventType.DRAG_MOVE
    mouse_button: MouseButton = MouseButton.LEFT
    modifiers: frozenset[ModifierKey] = frozenset()
    screen_position: tuple[float, float] = (0.0, 0.0)
    delta_pixels: tuple[float, float] = (0.0, 0.0)
    world_position: tuple[float, float, float] = (0.0, 0.0, 0.0)
    delta_transform: tuple[float, ...] = ()  # 16 floats


@dataclass
class ScrollEvent(ControlEvent):
    """Fired when the user scrolls while hovering an interactive object."""
    object_id: str = ""
    event_type: InteractionEventType = InteractionEventType.SCROLL
    modifiers: frozenset[ModifierKey] = frozenset()
    screen_position: tuple[float, float] = (0.0, 0.0)
    delta_xy: tuple[float, float] = (0.0, 0.0)  # raw scroll delta
```

### 2.4 Deserialization Helpers

```python
def _parse_modifiers(modifiers_list: list[str]) -> frozenset[ModifierKey]:
    """Parse a list of modifier strings from JSON into a frozenset."""
    return frozenset(ModifierKey(m) for m in modifiers_list)


def _parse_event(data: dict[str, Any]) -> ControlEvent:
    """Parse a JSON dict into the appropriate event dataclass.

    Dispatches on ``data["event_type"]``.
    """
    msg_type = data.get("type", "")
    event_type_str = data.get("event_type", "")
    try:
        event_type = InteractionEventType(event_type_str)
    except ValueError:
        raise ValueError(f"Unknown interaction event type: {event_type_str!r}") from None

    modifiers = _parse_modifiers(data.get("modifiers", []))
    browser_id = data.get("browser_id")

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
        )
    elif event_type in (InteractionEventType.DRAG_START, InteractionEventType.DRAG_MOVE, InteractionEventType.DRAG_END):
        return DragEvent(
            browser_id=browser_id,
            object_id=data.get("object_id", ""),
            event_type=event_type,
            mouse_button=MouseButton(data.get("mouse_button", "left")),
            modifiers=modifiers,
            screen_position=tuple(data.get("screen_position", [0.0, 0.0])),
            delta_pixels=tuple(data.get("delta_pixels", [0.0, 0.0])),
            world_position=tuple(data.get("world_position", [0.0, 0.0, 0.0])),
            delta_transform=tuple(data.get("delta_transform", [])),
        )
    elif event_type == InteractionEventType.SCROLL:
        return ScrollEvent(
            browser_id=browser_id,
            object_id=data.get("object_id", ""),
            event_type=event_type,
            modifiers=modifiers,
            screen_position=tuple(data.get("screen_position", [0.0, 0.0])),
            delta_xy=tuple(data.get("delta_xy", [0.0, 0.0])),
        )
    else:
        raise ValueError(f"Unhandled interaction event type: {event_type!r}")
```

### 2.5 Drag Move Coalescing

```python
def _coalesce_drag_events(events: list[DragEvent]) -> DragEvent:
    """Merge multiple drag_move events into one by accumulating deltas.

    All events must have the same ``object_id`` and ``event_type``.  The
    result uses the latest ``screen_position``, ``world_position``,
    ``delta_transform``, and ``modifiers``.

    Returns the single event unchanged if the list has length 1.
    """
    if not events:
        raise ValueError("Cannot coalesce empty event list")
    if len(events) == 1:
        return events[0]

    first = events[0]
    total_delta_x = sum(e.delta_pixels[0] for e in events)
    total_delta_y = sum(e.delta_pixels[1] for e in events)
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
        delta_transform=last.delta_transform,
    )
```

### 2.6 Handler Registry with Coalescing

```python
Handler = Callable[[Any], Awaitable[None]]
"""Async callback receiving a :class:`ClickEvent`, :class:`DragEvent`, or :class:`ScrollEvent`."""


class InteractionHandlerRegistry:
    """Maps ``(object_id, event_type)`` pairs to async handler callables.

    Provides drag_move coalescing: when multiple ``DRAG_MOVE`` events arrive
    for the same object while a handler is still processing, they are merged
    into a single event before the next handler invocation.
    """

    def __init__(self) -> None:
        self._handlers: dict[tuple[str, InteractionEventType], Handler] = {}
        # Per-object state for coalescing
        self._pending: dict[str, list[DragEvent]] = {}  # object_id → queued DRAG_MOVE events
        self._running: dict[str, bool] = {}  # object_id → True if handler currently running

    def register(self, object_id: str, event_type: InteractionEventType, handler: Handler) -> None:
        """Register an async handler for a specific object + event type."""
        self._handlers[(object_id, event_type)] = handler

    def unregister(self, object_id: str, event_type: InteractionEventType | None = None) -> None:
        """Remove handler(s). If ``event_type`` is ``None``, remove all for that object."""
        if event_type is None:
            keys = [k for k in self._handlers if k[0] == object_id]
            for k in keys:
                del self._handlers[k]
        else:
            self._handlers.pop((object_id, event_type), None)

    def get(self, object_id: str, event_type: InteractionEventType) -> Handler | None:
        """Look up a handler, or ``None``."""
        return self._handlers.get((object_id, event_type))

    def clear(self) -> None:
        """Remove all handlers and pending queues."""
        self._handlers.clear()
        self._pending.clear()
        self._running.clear()

    async def dispatch(self, event: ControlEvent) -> None:
        """Fire-and-forget dispatch with drag_move coalescing.

        * ``DRAG_START`` / ``DRAG_END``: flush pending queue, dispatch immediately.
        * ``DRAG_MOVE``: if handler is running, queue the event for later coalescing.
          Otherwise dispatch immediately.
        * Other event types: dispatch immediately (no coalescing needed).
        """
        if isinstance(event, DragEvent):
            handler = self.get(event.object_id, event.event_type)
            if handler is None:
                return

            if event.event_type in (InteractionEventType.DRAG_START, InteractionEventType.DRAG_END):
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
        """Run a drag handler and process any coalesced pending events after."""
        import asyncio
        import logging

        _logger = logging.getLogger(__name__)

        try:
            await handler(event)
        except Exception:
            _logger.exception("Interaction handler raised an exception for object %s", event.object_id)
        finally:
            obj_id = event.object_id
            # Check for coalesced pending events
            pending = self._pending.get(obj_id, [])
            if pending:
                self._pending.pop(obj_id, None)
                coalesced = _coalesce_drag_events(pending)
                next_handler = self.get(obj_id, InteractionEventType.DRAG_MOVE)
                if next_handler is not None:
                    self._running[obj_id] = True
                    asyncio.create_task(self._run_handler(next_handler, coalesced))
                    return  # _run_handler will clear _running when done
            self._running[obj_id] = False
```

### 2.7 Utility Functions

```python
def apply_delta_transform(
    delta_pixels: tuple[float, float],
    transform: tuple[float, ...],
) -> tuple[float, float, float]:
    """Convert a pixel delta to a world-space delta using the transform matrix.

    The transform is a 4×4 row-major matrix as produced by the frontend.
    Only the first two rows are used for screen-parallel movement; the
    third row (depth) is ignored unless the delta has a non-zero Z component
    (e.g., from scroll).

    Args:
        delta_pixels: (dx, dy) in screen pixels.
        transform: 16 floats in row-major 4×4 order.

    Returns:
        (dx, dy, dz) in world coordinates.
    """
    if len(transform) != 16:
        raise ValueError(f"Transform must be 16 floats (4×4 row-major), got {len(transform)}")

    dx, dy = delta_pixels
    # Row 0: screen +X → world (columns 0,1,2)
    wx = dx * transform[0] + dy * transform[4]
    wy = dx * transform[1] + dy * transform[5]
    wz = dx * transform[2] + dy * transform[6]
    return (wx, wy, wz)


def extract_camera_directions(
    transform: tuple[float, ...],
) -> tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]:
    """Extract the unit camera frame directions from the delta transform.

    Since each row of the transform is the camera basis vector scaled by
    ``screen_scale``, normalizing each row recovers the unit directions.

    Args:
        transform: 16 floats in row-major 4×4 order.

    Returns:
        ``(right, up, forward)`` — each a ``(x, y, z)`` unit vector tuple.
    """
    import math

    if len(transform) != 16:
        raise ValueError(f"Transform must be 16 floats (4×4 row-major), got {len(transform)}")

    def _normalize(v: tuple[float, float, float]) -> tuple[float, float, float]:
        length = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
        if length < 1e-12:
            return (0.0, 0.0, 0.0)
        return (v[0] / length, v[1] / length, v[2] / length)

    right = (transform[0], transform[1], transform[2])
    up = (transform[4], transform[5], transform[6])
    forward = (transform[8], transform[9], transform[10])

    return (_normalize(right), _normalize(up), _normalize(forward))
```

---

## 3. Export from `py/pytanga/viz/__init__.py`

```python
from ._interaction import (
    InteractionConfig,
    InteractionTrigger,
    InteractionEventType,
    MouseButton,
    ModifierKey,
    ClickEvent,
    DragEvent,
    ScrollEvent,
    ControlEvent,
    InteractionHandlerRegistry,
    apply_delta_transform,
    extract_camera_directions,
    Handler,
)
```

Add these to the module's `__all__` if one exists.

---

## 4. Design Decisions

### 4.1 Enums for Type Safety

All event types, mouse buttons, and modifier keys are Python enums rather than
plain strings or ints. This provides IDE autocompletion, prevents typos, and
makes the API self-documenting. The `value` of each enum is the lowercase
string used in JSON serialization.

### 4.2 `frozenset` for Modifiers

Using `frozenset[ModifierKey]` (rather than a regular set) makes instances
hashable and immutable, which is consistent with dataclass semantics and
prevents accidental mutation.

### 4.3 Coalescing in Registry, not Server

The coalescing logic lives in `InteractionHandlerRegistry.dispatch()` rather
than the server or visualizer. This keeps the coalescing close to the handler
lifecycle and avoids leaking implementation details into the transport layer.

### 4.4 Fire-and-Forget

Handlers are invoked via `asyncio.create_task()` — the dispatch returns
immediately. This matches the existing `_controls.py` pattern and prevents
backpressure from a slow handler blocking event delivery for other objects.

### 4.5 `delta_transform` as Flat Tuple

A flat 16-element tuple is simple to serialize over JSON (array of 16 floats)
and avoids introducing a numpy dependency. Utility functions
`apply_delta_transform()` and `extract_camera_directions()` provide the
ergonomic API.

---

## 5. Implementation Checklist

- [x] Create `py/pytanga/viz/_interaction.py`
- [x] Define `InteractionEventType` enum
- [x] Define `MouseButton` enum with `from_js_code` / `to_js_code` helpers
- [x] Define `ModifierKey` enum
- [x] Define `InteractionTrigger` dataclass with `to_dict` / `from_dict`
- [x] Define `InteractionConfig` dataclass with `to_dict`
- [x] Define `ControlEvent` base dataclass
- [x] Define `ClickEvent`, `DragEvent`, `ScrollEvent` dataclasses
- [x] Implement `_parse_modifiers()` helper
- [x] Implement `_parse_event()` deserialization
- [x] Implement `_coalesce_drag_events()`
- [x] Implement `InteractionHandlerRegistry` with `dispatch()` method
- [x] Implement `apply_delta_transform()` utility
- [x] Implement `extract_camera_directions()` utility
- [x] Add `Handler` type alias
- [x] Import and re-export from `py/pytanga/viz/__init__.py`

---

## 6. Verification

- [x] `InteractionTrigger(event_type=InteractionEventType.DRAG, mouse_button=MouseButton.LEFT).to_dict()` → `{"event_type": "drag", "mouse_button": "left", "modifiers": []}`
- [x] `InteractionConfig(enabled=True, throttle_ms=30).to_dict()` → `{"enabled": true, "triggers": [], "throttle_ms": 30}`
- [x] `_parse_event({"type": "interaction:click", "event_type": "click", "object_id": "x", "mouse_button": "left", ...})` → `ClickEvent` instance
- [x] `_coalesce_drag_events([DragEvent(delta_pixels=(1,0)), DragEvent(delta_pixels=(2,3))])` → `DragEvent(delta_pixels=(3,3))`
- [x] `apply_delta_transform((100, 0), [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1])` → `(100.0, 0.0, 0.0)`
- [x] `extract_camera_directions([1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1])` → `((1,0,0), (0,1,0), (0,0,1))`
- [x] `from pytanga.viz import InteractionConfig, InteractionEventType, DragEvent` works
