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
from functools import singledispatchmethod
from typing import Any

from pytanga.geometry import Direction, Point

from ._controls import ControlHandlerRegistry

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
        hover_emissive: CSS colour string for emissive glow on hover
            (e.g. ``"#ffff44"``).  ``None`` = no hover highlight.
        hover_scale: Uniform scale multiplier on hover
            (e.g. ``1.5``).  ``None`` = no hover scaling.
        hover_opacity: Opacity override on hover (0..1).  ``None`` = no
            opacity change on hover.
    """

    enabled: bool = False
    triggers: list[InteractionTrigger] = field(default_factory=list)
    throttle_ms: int = 50
    hover_emissive: str | None = None
    hover_scale: float | None = None
    hover_opacity: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-ready dict."""
        result: dict[str, Any] = {
            "enabled": self.enabled,
            "triggers": [t.to_dict() for t in self.triggers],
            "throttle_ms": self.throttle_ms,
        }
        if self.hover_emissive is not None:
            result["hover_emissive"] = self.hover_emissive
        if self.hover_scale is not None:
            result["hover_scale"] = self.hover_scale
        if self.hover_opacity is not None:
            result["hover_opacity"] = self.hover_opacity
        return result


# ── Matrix helpers ─────────────────────────────────────────────


def _mat4_col(m: tuple[float, ...], col: int) -> tuple[float, float, float, float]:
    """Extract column *col* (0-3) from a 16-float column-major matrix."""
    i = col * 4
    return (m[i], m[i + 1], m[i + 2], m[i + 3])


def _mat4_mul_vec4(
    m: tuple[float, ...], v: tuple[float, float, float, float]
) -> tuple[float, float, float, float]:
    """Multiply a 16-float column-major 4×4 matrix by a 4-element vector."""
    return (
        m[0] * v[0] + m[4] * v[1] + m[8] * v[2] + m[12] * v[3],
        m[1] * v[0] + m[5] * v[1] + m[9] * v[2] + m[13] * v[3],
        m[2] * v[0] + m[6] * v[1] + m[10] * v[2] + m[14] * v[3],
        m[3] * v[0] + m[7] * v[1] + m[11] * v[2] + m[15] * v[3],
    )


def apply_delta_transform(
    delta: tuple[float, float],
    transform: tuple[float, ...],
) -> tuple[float, float, float]:
    """Apply a 4×4 column-major matrix to a 2D delta as world position.

    Treats ``delta`` as ``(dx, dy, 0, 1)``, multiplies by the 4×4
    *transform*, and returns the resulting ``(x, y, z)``.
    """
    if len(transform) != 16:
        raise ValueError(
            f"Transform must have exactly 16 elements, got {len(transform)}"
        )
    x, y, z, _w = _mat4_mul_vec4(transform, (delta[0], delta[1], 0.0, 1.0))
    return (x, y, z)


def extract_camera_directions(
    transform: tuple[float, ...],
) -> tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]:
    """Extract right, up, and forward direction vectors from a 4×4 column-major matrix.

    Returns ``(right, up, forward)``, each as a ``(x, y, z)`` tuple.
    """
    right = (transform[0], transform[1], transform[2])
    up = (transform[4], transform[5], transform[6])
    forward = (transform[8], transform[9], transform[10])
    return (right, up, forward)


# ── Camera dataclass ───────────────────────────────────────────


@dataclass
class Camera:
    """Camera state for world ↔ screen coordinate conversion.

    Stores the view and projection matrices (and their inverses) along
    with viewport dimensions and space dimensionality.  Provides
    ``project`` / ``unproject`` methods that dispatch on :class:`Point`
    vs :class:`Direction` input.

    The matrices are flat 16-float tuples in column-major order,
    matching Three.js ``Matrix4.elements``.
    """

    view: tuple[float, ...] = field(default_factory=lambda: (
        1.0, 0.0, 0.0, 0.0,
        0.0, 1.0, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        0.0, 0.0, 0.0, 1.0,
    ))
    view_inv: tuple[float, ...] = field(default_factory=lambda: (
        1.0, 0.0, 0.0, 0.0,
        0.0, 1.0, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        0.0, 0.0, 0.0, 1.0,
    ))
    proj: tuple[float, ...] = field(default_factory=lambda: (
        1.0, 0.0, 0.0, 0.0,
        0.0, 1.0, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        0.0, 0.0, 0.0, 1.0,
    ))
    proj_inv: tuple[float, ...] = field(default_factory=lambda: (
        1.0, 0.0, 0.0, 0.0,
        0.0, 1.0, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        0.0, 0.0, 0.0, 1.0,
    ))
    viewport_width: int = 800
    viewport_height: int = 600
    space_dim: int = 3

    @property
    def position(self) -> Point:
        """Camera world-space position, extracted from the inverse view matrix."""
        col3 = _mat4_col(self.view_inv, 3)
        return Point(col3[0], col3[1], col3[2])

    @property
    def right(self) -> Direction:
        """Camera right axis in world space."""
        col0 = _mat4_col(self.view_inv, 0)
        return Direction(col0[0], col0[1], col0[2])

    @property
    def up(self) -> Direction:
        """Camera up axis in world space."""
        col1 = _mat4_col(self.view_inv, 1)
        return Direction(col1[0], col1[1], col1[2])

    @property
    def view_dir(self) -> Direction:
        """Camera view direction in world space (look-at axis, forward)."""
        col2 = _mat4_col(self.view_inv, 2)
        return Direction(col2[0], col2[1], col2[2])

    @property
    def focal_length_px(self) -> float:
        """Focal length in pixel units from the projection matrix.

        For a PerspectiveCamera: ``proj[5] = 1 / tan(fov / 2)``, so
        focal_length = proj[5] * viewport_height / 2.
        """
        return self.proj[5] * self.viewport_height / 2.0

    # ── Project ─────────────────────────────────────────────

    @singledispatchmethod
    def project(self, obj) -> tuple[float, float]:
        """Project a world-space :class:`Point` or :class:`Direction` to
        screen pixel coordinates.

        Returns ``(pixel_x, pixel_y)``.
        """
        raise TypeError(
            f"project() expects Point or Direction, got {type(obj).__name__}"
        )

    @project.register(Point)
    def _(self, p: Point) -> tuple[float, float]:
        """Project a world point to screen pixel coordinates."""
        eye = _mat4_mul_vec4(self.view, (p.x, p.y, p.z, 1.0))
        clip = _mat4_mul_vec4(self.proj, eye)
        w = clip[3]
        if abs(w) < 1e-12:
            return (float("nan"), float("nan"))
        ndc_x = clip[0] / w
        ndc_y = clip[1] / w
        px = (ndc_x + 1.0) * 0.5 * self.viewport_width
        py = (1.0 - ndc_y) * 0.5 * self.viewport_height
        return (px, py)

    @project.register(Direction)
    def _(self, d: Direction) -> tuple[float, float]:
        """Project a world direction to a screen pixel displacement.

        The direction is treated as a vector (w=0) so view-matrix
        translation is ignored.
        """
        eye = _mat4_mul_vec4(self.view, (d.x, d.y, d.z, 0.0))
        clip = _mat4_mul_vec4(self.proj, eye)
        w = clip[3]
        if abs(w) < 1e-12:
            return (float("nan"), float("nan"))
        ndc_x = clip[0] / w
        ndc_y = clip[1] / w
        px = ndc_x * 0.5 * self.viewport_width
        py = -ndc_y * 0.5 * self.viewport_height
        return (px, py)

    # ── Unproject ───────────────────────────────────────────

    @singledispatchmethod
    def unproject(self, obj, depth: float = 0.0) -> Point | Direction:
        """Unproject screen-space coordinates to world space.

        When *obj* is a :class:`Point` (the first two components are
        treated as pixel coordinates), returns a world-space
        :class:`Point` at the given *depth*.

        When *obj* is a :class:`Direction` (the first two components
        are treated as pixel displacement), returns a world-space
        :class:`Direction` at the given *depth*.
        """
        raise TypeError(
            f"unproject() expects Point or Direction, got {type(obj).__name__}"
        )

    @unproject.register(Point)
    def _(self, p: Point, depth: float = 0.0) -> Point:
        """Unproject a screen-pixel point to a world :class:`Point` at *depth*."""
        px, py = p.x, p.y
        # NDC from pixel coords
        ndc_x = (px / self.viewport_width) * 2.0 - 1.0
        ndc_y = 1.0 - (py / self.viewport_height) * 2.0

        # Build two clip-space points: one at near (z=-1), one at far (z=1)
        near_clip = _mat4_mul_vec4(self.proj_inv, (ndc_x, ndc_y, -1.0, 1.0))
        far_clip = _mat4_mul_vec4(self.proj_inv, (ndc_x, ndc_y, 1.0, 1.0))

        # Perspective divide → camera-space
        if abs(near_clip[3]) < 1e-12 or abs(far_clip[3]) < 1e-12:
            return Point(float("nan"), float("nan"), float("nan"))
        near_eye = (
            near_clip[0] / near_clip[3],
            near_clip[1] / near_clip[3],
            near_clip[2] / near_clip[3],
            1.0,
        )
        far_eye = (
            far_clip[0] / far_clip[3],
            far_clip[1] / far_clip[3],
            far_clip[2] / far_clip[3],
            1.0,
        )

        # World-space
        near_world = _mat4_mul_vec4(self.view_inv, near_eye)
        far_world = _mat4_mul_vec4(self.view_inv, far_eye)

        # Ray direction in world space
        ray_dir = Direction(
            far_world[0] - near_world[0],
            far_world[1] - near_world[1],
            far_world[2] - near_world[2],
        ).normalized()

        # March along ray to the plane at distance *depth* from camera,
        # perpendicular to the camera view direction.
        cam_pos = self.position
        cam_view = self.view_dir
        plane_point = cam_pos + cam_view * depth

        # Intersect ray with plane ⟂ cam_view through plane_point
        denom = ray_dir.dot(cam_view)
        if abs(denom) < 1e-12:
            return Point(float("nan"), float("nan"), float("nan"))
        t = (plane_point - Point(near_world[0], near_world[1], near_world[2])).dot(cam_view) / denom

        result = Point(
            near_world[0] + ray_dir.x * t,
            near_world[1] + ray_dir.y * t,
            near_world[2] + ray_dir.z * t,
        )
        return result

    @unproject.register(Direction)
    def _(self, d: Direction, depth: float = 0.0) -> Direction:
        """Unproject a screen-pixel displacement to a world :class:`Direction` at *depth*."""
        dx, dy = d.x, d.y
        # Unproject two points: screen center and screen center + (dx, dy)
        cx = self.viewport_width * 0.5
        cy = self.viewport_height * 0.5
        p0 = self.unproject(Point(cx, cy), depth)
        p1 = self.unproject(Point(cx + dx, cy + dy), depth)
        return p1 - p0

    @unproject.register(type(None))
    def _(self, _obj: None, depth: float = 0.0) -> None:
        """Handle None gracefully (e.g., default event fields)."""
        raise TypeError(
            "unproject() expects Point or Direction, got None"
        )


# ── Event dataclasses ──────────────────────────────────────────


@dataclass
class ControlEvent:
    """Base class for all interaction events.

    All events carry a :class:`Camera` so handlers can transform
    between screen space and world space without additional round-trips.

    The *camera* may be ``None`` on drag-move/drag-end events coming
    from the frontend (the camera is only sent on drag-start).
    The :class:`InteractionHandlerRegistry` injects the cached camera
    before the handler sees it, so handlers always receive a populated
    ``camera``.
    """

    browser_id: str | None = None
    camera: Camera | None = None


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
    world_position: Point = field(default_factory=Point)
    world_normal: Direction = field(default_factory=Direction)


@dataclass
class DragEvent(ControlEvent):
    """Fired during pointer drags on an interactive object.

    ``event_type`` will be :attr:`~InteractionEventType.DRAG_START`,
    :attr:`~InteractionEventType.DRAG_MOVE`, or
    :attr:`~InteractionEventType.DRAG_END`.

    The frontend computes ``world_position`` by intersecting the
    pixel-position ray with the constraint plane.  ``world_delta``
    is the change since the previous drag event.
    """

    object_id: str = ""
    event_type: InteractionEventType = InteractionEventType.DRAG_MOVE
    mouse_button: MouseButton = MouseButton.LEFT
    modifiers: frozenset[ModifierKey] = frozenset()
    screen_position: tuple[float, float] = (0.0, 0.0)
    delta_pixels: tuple[float, float] = (0.0, 0.0)
    delta_transform: tuple[float, ...] = ()
    world_position: Point = field(default_factory=Point)
    world_delta: Direction = field(default_factory=Direction)
    drag_mode: DragMode = DragMode.VIEW_PLANE
    ray_origin: Point = field(default_factory=Point)
    ray_direction: Direction = field(default_factory=Direction)


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


def _parse_camera(data: dict[str, Any]) -> Camera | None:
    """Parse a camera sub-object from a JSON dict, or return None."""
    cam_data = data.get("camera")
    if cam_data is None:
        return None
    return Camera(
        view=tuple(cam_data.get("view", [])),
        view_inv=tuple(cam_data.get("view_inv", [])),
        proj=tuple(cam_data.get("proj", [])),
        proj_inv=tuple(cam_data.get("proj_inv", [])),
        viewport_width=int(cam_data.get("viewport_width", 800)),
        viewport_height=int(cam_data.get("viewport_height", 600)),
        space_dim=int(cam_data.get("space_dim", 3)),
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
    camera = _parse_camera(data)

    if event_type in (InteractionEventType.CLICK, InteractionEventType.DBLCLICK):
        wp = data.get("world_position", [0.0, 0.0, 0.0])
        wn = data.get("world_normal", [0.0, 0.0, 0.0])
        return ClickEvent(
            browser_id=browser_id,
            camera=camera,
            object_id=data.get("object_id", ""),
            event_type=event_type,
            mouse_button=MouseButton(data.get("mouse_button", "left")),
            modifiers=modifiers,
            screen_position=tuple(data.get("screen_position", [0.0, 0.0])),
            world_position=Point(float(wp[0]), float(wp[1]), float(wp[2])),
            world_normal=Direction(float(wn[0]), float(wn[1]), float(wn[2])),
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
        wp = data.get("world_position", [0.0, 0.0, 0.0])
        wd = data.get("world_delta", [0.0, 0.0, 0.0])
        dt = data.get("delta_transform", [])
        ro = data.get("ray_origin", [0.0, 0.0, 0.0])
        rd = data.get("ray_direction", [0.0, 0.0, 0.0])
        return DragEvent(
            browser_id=browser_id,
            camera=camera,
            object_id=data.get("object_id", ""),
            event_type=event_type,
            mouse_button=MouseButton(data.get("mouse_button", "left")),
            modifiers=modifiers,
            screen_position=tuple(data.get("screen_position", [0.0, 0.0])),
            delta_pixels=tuple(data.get("delta_pixels", [0.0, 0.0])),
            delta_transform=tuple(dt),
            world_position=Point(float(wp[0]), float(wp[1]), float(wp[2])),
            world_delta=Direction(float(wd[0]), float(wd[1]), float(wd[2])),
            drag_mode=drag_mode,
            ray_origin=Point(float(ro[0]), float(ro[1]), float(ro[2])),
            ray_direction=Direction(float(rd[0]), float(rd[1]), float(rd[2])),
        )

    if event_type == InteractionEventType.SCROLL:
        return ScrollEvent(
            browser_id=browser_id,
            camera=camera,
            object_id=data.get("object_id", ""),
            event_type=event_type,
            modifiers=modifiers,
            screen_position=tuple(data.get("screen_position", [0.0, 0.0])),
            delta_xy=tuple(data.get("delta_xy", [0.0, 0.0])),
        )

    raise ValueError(f"Unhandled interaction event type: {event_type!r}")


# ── Drag move coalescing ───────────────────────────────────────


def _coalesce_drag_events(events: list[DragEvent]) -> DragEvent:
    """Merge multiple drag_move events into one by accumulating deltas.

    All events must have the same ``object_id`` and ``event_type``.  The
    result uses the latest ``screen_position``, ``world_position``,
    ``world_delta``, ``modifiers``, and camera.

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
    total_world_delta = first.world_delta
    for e in events[1:]:
        total_world_delta = total_world_delta + e.world_delta
    last = events[-1]

    return DragEvent(
        browser_id=last.browser_id,
        camera=last.camera,
        object_id=first.object_id,
        event_type=first.event_type,
        mouse_button=first.mouse_button,
        modifiers=last.modifiers,
        screen_position=last.screen_position,
        delta_pixels=(total_delta_x, total_delta_y),
        world_position=last.world_position,
        world_delta=total_world_delta,
        drag_mode=last.drag_mode,
        ray_origin=first.ray_origin,
        ray_direction=first.ray_direction,
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

    Also caches the camera from ``DRAG_START`` and injects it into
    ``DRAG_MOVE`` / ``DRAG_END`` events that arrive without a camera,
    so handlers always receive a fully populated ``camera`` field.
    """

    def __init__(self, handlers: ControlHandlerRegistry | None = None) -> None:
        # Handler storage: when a shared ``(id, event)`` registry is supplied,
        # registration delegates to it so interactions and controls share one
        # namespace; otherwise a private dict is used (unit tests / standalone).
        self._handlers_registry = handlers
        self._own_handlers: dict[tuple[str, InteractionEventType], Handler] = {}
        # Per-object state for coalescing
        self._pending: dict[str, list[DragEvent]] = {}
        self._running: dict[str, bool] = {}
        # Camera cache: stored on drag_start / click / scroll,
        # injected into drag_move / drag_end when missing
        self._camera_store: dict[str, Camera] = {}

    # ── Registration ───────────────────────────────────────────

    def register(
        self,
        object_id: str,
        event_type: InteractionEventType,
        handler: Handler,
    ) -> None:
        """Register an async handler for a specific object + event type."""
        if self._handlers_registry is not None:
            self._handlers_registry.register(
                object_id, handler, event=event_type.value
            )
        else:
            self._own_handlers[(object_id, event_type)] = handler

    def unregister(
        self,
        object_id: str,
        event_type: InteractionEventType | None = None,
    ) -> None:
        """Remove handler(s).

        If *event_type* is ``None``, remove all handlers for *object_id*.
        """
        if self._handlers_registry is not None:
            self._handlers_registry.unregister(
                object_id, None if event_type is None else event_type.value
            )
        elif event_type is None:
            keys = [k for k in self._own_handlers if k[0] == object_id]
            for k in keys:
                del self._own_handlers[k]
        else:
            self._own_handlers.pop((object_id, event_type), None)

    def get(
        self, object_id: str, event_type: InteractionEventType
    ) -> Handler | None:
        """Look up a handler, or ``None``."""
        if self._handlers_registry is not None:
            return self._handlers_registry.get(object_id, event_type.value)
        return self._own_handlers.get((object_id, event_type))

    def clear(self) -> None:
        """Remove all handlers and pending queues.

        With a shared registry the handlers are owned by that registry, so only
        the interaction coalescing state is reset here.
        """
        if self._handlers_registry is None:
            self._own_handlers.clear()
        self._pending.clear()
        self._running.clear()
        self._camera_store.clear()

    # ── Dispatch ───────────────────────────────────────────────

    async def dispatch(self, event: ControlEvent) -> None:
        """Fire-and-forget dispatch with drag_move coalescing.

        * ``DRAG_START``: cache camera, flush pending queue, dispatch
          immediately.
        * ``DRAG_MOVE``: inject cached camera if missing; if handler is
          running, queue the event for later coalescing. Otherwise
          dispatch immediately.
        * ``DRAG_END``: inject cached camera if missing, flush pending
          queue, dispatch immediately.
        * Other event types: cache camera, dispatch immediately (no
          coalescing needed).
        """
        # ── Cache camera on any event that has one ──────────
        if event.camera is not None:
            oid = getattr(event, "object_id", None)
            if oid:
                self._camera_store[oid] = event.camera

        if isinstance(event, DragEvent):
            handler = self.get(event.object_id, event.event_type)
            if handler is None:
                return

            # Inject camera from cache if the frontend didn't send one
            if event.camera is None:
                cached = self._camera_store.get(event.object_id)
                if cached is not None:
                    event.camera = cached

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
                # Inject camera from cache for click/scroll events too
                if event.camera is None:
                    cached = self._camera_store.get(event.object_id)
                    if cached is not None:
                        event.camera = cached
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