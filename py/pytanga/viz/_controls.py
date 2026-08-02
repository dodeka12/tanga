# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Interactive UI controls for the Tanga 3D viewer.

Defines Python data classes for sliders, dropdowns, buttons, and control
groups, plus serialization helpers and an async handler registry for
dispatching WebSocket events from the JS frontend.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# ── Handler type alias ──────────────────────────────────────

Handler = Callable[[Any], Awaitable[None]]
"""Async callback type for control interaction handlers.

Takes a single ``value`` argument (float for sliders, str for dropdowns,
``None`` for buttons / group toggles) and returns an awaitable.
"""


# ── Control dataclasses ──────────────────────────────────────


@dataclass
class Control:
    """Base class for interactive UI controls overlaid on the 3D viewer."""

    id: str
    """Unique control identifier.  Used as the WebSocket event key."""

    label: str = ""
    """Human-readable label displayed next to the control."""

    parent_id: str | None = None
    """If set, attach this control (via CSS2DRenderer) to the 3D entity
    with this ID.  ``None`` means the control lives in a fixed DOM panel."""


@dataclass
class Slider(Control):
    """A numeric slider control with min/max/step bounds."""

    kind: str = "slider"
    min: float = 0.0
    max: float = 1.0
    step: float = 0.01
    default: float = 0.5
    on_change: Handler | None = None


@dataclass
class Dropdown(Control):
    """A dropdown / select control with a fixed set of string options."""

    kind: str = "dropdown"
    options: list[str] = field(default_factory=list)
    default: str = ""
    on_change: Handler | None = None


@dataclass
class Button(Control):
    """A clickable button with an async callback."""

    kind: str = "button"
    on_click: Handler | None = None


# ── Control group ────────────────────────────────────────────


@dataclass
class ControlGroup:
    """A visual group of related controls with a title bar.

    Can either be a **fixed-position** DOM panel (``parent_id=None``)
    or **attached** to a 3D entity via CSS2DRenderer (``parent_id`` set).
    """

    id: str
    """Unique group identifier."""

    title: str = ""
    """Title displayed in the group's title bar.

    When the group is attached to a 3D object (``parent_id`` is set),
    this title doubles as a persistent label rendered alongside the object.
    """

    controls: list[Control] = field(default_factory=list)
    """The list of :class:`Control` instances belonging to this group."""

    position: str = "bottom-right"
    """Viewport anchor for fixed-position panels.

    One of ``"top-left"``, ``"top-right"``, ``"bottom-left"``,
    ``"bottom-right"``.  Ignored when ``parent_id`` is set.
    """

    collapsed: bool = False
    """If ``True``, the group starts collapsed (controls hidden)."""

    parent_id: str | None = None
    """If set, the group is rendered as a CSS2DObject attached to the
    3D entity with this ID.  The title bar serves as a persistent label.
    When ``None``, the group is a fixed-position DOM panel."""

    on_toggle: Handler | None = None
    """Optional callback invoked when the group is expanded or collapsed.
    Receives a ``bool`` (``True`` = collapsed)."""


# ── Handler registry ─────────────────────────────────────────


class ControlHandlerRegistry:
    """Maps ``control_id`` strings to async handler callables.

    The server's WebSocket handler uses this registry to dispatch
    incoming ``control:change`` and ``control:click`` messages.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, Handler] = {}

    def register(self, control_id: str, handler: Handler) -> None:
        """Register an async handler for a control.

        Args:
            control_id: The ``id`` of the :class:`Control`.
            handler: An ``async def`` callable that receives the control's
                value (float for sliders, str for dropdowns).
        """
        self._handlers[control_id] = handler

    def unregister(self, control_id: str) -> None:
        """Remove a previously registered handler (no-op if not found)."""
        self._handlers.pop(control_id, None)

    def get(self, control_id: str) -> Handler | None:
        """Look up the handler for *control_id*, or ``None``."""
        return self._handlers.get(control_id)

    def clear(self) -> None:
        """Remove all registered handlers."""
        self._handlers.clear()


# ── Serialization ────────────────────────────────────────────


def _serialize_one_control(ctrl: Control) -> dict[str, Any]:
    """Serialize a single :class:`Control` to its JSON-ready dict form."""
    base: dict[str, Any] = {
        "id": ctrl.id,
        "kind": ctrl.kind,
        "label": ctrl.label,
    }

    if isinstance(ctrl, Slider):
        base.update(
            {
                "min": ctrl.min,
                "max": ctrl.max,
                "step": ctrl.step,
                "default": ctrl.default,
            }
        )
    elif isinstance(ctrl, Dropdown):
        base.update(
            {
                "options": list(ctrl.options),
                "default": ctrl.default,
            }
        )
    elif isinstance(ctrl, Button):
        pass  # No extra fields for buttons
    else:
        raise TypeError(f"Unknown control kind: {type(ctrl).__name__}")

    return base


def serialize_controls(
    groups: list[ControlGroup],
    controls_map: dict[str, Control] | None = None,
) -> dict[str, Any]:
    """Build the ``controls_define`` JSON message from group definitions.

    Args:
        groups: A (possibly empty) list of :class:`ControlGroup` instances.
        controls_map: Optional dict of ``control_id`` → :class:`Control` for
            resolving group control ID references to full control objects.
            When ``None``, groups must store :class:`Control` objects directly.

    Returns:
        A dict ready for ``json.dumps`` with ``"type": "controls_define"``
        and ``"controls"``, ``"groups"``, ``"orphanControls"`` fields.
    """
    all_controls: dict[str, dict[str, Any]] = {}
    group_list: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for group in groups:
        group_control_ids: list[str] = []
        for ctrl in group.controls:
            # Resolve control: either it's already a Control object or
            # it's a string ID that needs lookup in controls_map
            if isinstance(ctrl, Control):
                ctrl_obj = ctrl
            elif controls_map is not None:
                ctrl_obj = controls_map.get(ctrl)
                if ctrl_obj is None:
                    continue  # skip orphaned IDs
            else:
                continue
            group_control_ids.append(ctrl_obj.id)
            seen_ids.add(ctrl_obj.id)
            all_controls[ctrl_obj.id] = _serialize_one_control(ctrl_obj)
        group_list.append(
            {
                "id": group.id,
                "title": group.title,
                "controls": group_control_ids,
                "position": group.position,
                "collapsed": group.collapsed,
                "parentId": group.parent_id,
            }
        )

    # Collect orphan controls: all registered controls not in any group
    orphan_ids: list[str] = []
    if controls_map is not None:
        for cid in controls_map:
            if cid not in seen_ids:
                orphan_ids.append(cid)
                all_controls[cid] = _serialize_one_control(controls_map[cid])
    return {
        "type": "controls_define",
        "controls": list(all_controls.values()),
        "groups": group_list,
        "orphanControls": orphan_ids,
    }
