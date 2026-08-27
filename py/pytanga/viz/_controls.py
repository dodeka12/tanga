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
from typing import Any

from ._icons import Icon


# ── Control event dataclass ──────────────────────────────────


@dataclass
class ControlEvent:
    """Metadata passed to every control handler alongside the value.

    Only *browser_id* is populated for now; additional fields may be added
    without breaking existing handler signatures.
    """

    browser_id: str | None = None


# ── Handler type alias ──────────────────────────────────────

Handler = Callable[[Any, ControlEvent], Awaitable[None]]
"""Async callback type for control interaction handlers.

Takes a ``value`` argument (float for sliders, str for dropdowns / text /
textarea / color pickers, bool for checkboxes, ``None`` for buttons / group
toggles) and a :class:`ControlEvent`, and returns an awaitable.
"""


# ── Control dataclasses ──────────────────────────────────────


@dataclass
class Control:
    """Base class for interactive UI controls overlaid on the 3D viewer."""

    id: str
    """Unique control identifier.  Used as the WebSocket event key."""

    label: str = ""
    """Human-readable label displayed next to the control."""

    tooltip: str = ""
    """Optional hover tooltip text (rendered via the native ``title`` attr)."""

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
    value: float = 0.5
    on_change: Handler | None = None
    on_press: Handler | None = None
    on_release: Handler | None = None


@dataclass
class Dropdown(Control):
    """A dropdown / select control with a fixed set of string options."""

    kind: str = "dropdown"
    options: list[str] = field(default_factory=list)
    value: str = ""
    on_change: Handler | None = None


@dataclass
class Button(Control):
    """A clickable button with an optional icon and an async callback."""

    kind: str = "button"
    icon: Icon | None = None
    """Optional icon id (``family:name``); rendered before the label."""

    icon_only: bool = False
    """If ``True``, render only the icon as a small square button."""

    on_click: Handler | None = None


@dataclass
class FileChooser(Control):
    """A file-path control: a text field plus a backend-driven file browser."""

    kind: str = "file_chooser"
    value: str = ""
    placeholder: str = ""
    root: str | None = None
    accept: str = ""
    on_change: Handler | None = None


@dataclass
class TextField(Control):
    """A single-line text input control."""

    kind: str = "text"
    value: str = ""
    placeholder: str = ""
    on_change: Handler | None = None


@dataclass
class TextArea(Control):
    """A multi-line text input control."""

    kind: str = "textarea"
    value: str = ""
    placeholder: str = ""
    rows: int = 4
    on_change: Handler | None = None


@dataclass
class ColorPicker(Control):
    """A color chooser control (native color input, hex value)."""

    kind: str = "color"
    value: str = "#ffffff"
    on_change: Handler | None = None


@dataclass
class Checkbox(Control):
    """A boolean checkbox control."""

    kind: str = "checkbox"
    value: bool = False
    on_change: Handler | None = None


@dataclass
class ValueEdit(Control):
    """A numeric stepper control with up/down buttons and keyboard/wheel steps."""

    kind: str = "value_edit"
    min: float = 0.0
    max: float = 1.0
    step: float = 0.1
    digits: int = 2
    value: float = 0.0
    editable: bool = True
    on_change: Handler | None = None


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

    icon: Icon | None = None
    """Optional icon id (``family:name``) rendered in the title bar."""

    tooltip: str = ""
    """Optional hover tooltip text for the title bar."""

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
    if ctrl.tooltip:
        base["tooltip"] = ctrl.tooltip

    if isinstance(ctrl, Slider):
        base.update(
            {
                "min": ctrl.min,
                "max": ctrl.max,
                "step": ctrl.step,
                "value": ctrl.value,
            }
        )
    elif isinstance(ctrl, Dropdown):
        base.update(
            {
                "options": list(ctrl.options),
                "value": ctrl.value,
            }
        )
    elif isinstance(ctrl, Button):
        if ctrl.icon is not None:
            base["icon"] = str(ctrl.icon)
        base["icon_only"] = ctrl.icon_only
    elif isinstance(ctrl, TextField):
        base.update(
            {
                "value": ctrl.value,
                "placeholder": ctrl.placeholder,
            }
        )
    elif isinstance(ctrl, TextArea):
        base.update(
            {
                "value": ctrl.value,
                "placeholder": ctrl.placeholder,
                "rows": ctrl.rows,
            }
        )
    elif isinstance(ctrl, ColorPicker):
        base.update({"value": ctrl.value})
    elif isinstance(ctrl, Checkbox):
        base.update({"value": ctrl.value})
    elif isinstance(ctrl, FileChooser):
        base.update(
            {
                "value": ctrl.value,
                "placeholder": ctrl.placeholder,
                "root": ctrl.root,
                "accept": ctrl.accept,
            }
        )
    elif isinstance(ctrl, ValueEdit):
        base.update(
            {
                "min": ctrl.min,
                "max": ctrl.max,
                "step": ctrl.step,
                "digits": ctrl.digits,
                "value": ctrl.value,
                "editable": ctrl.editable,
            }
        )
    else:
        raise TypeError(f"Unknown control kind: {type(ctrl).__name__}")

    return base


def serialize_control_defs(controls: list[Control]) -> list[dict[str, Any]]:
    """Serialize a flat list of :class:`Control` objects to their dict forms.

    Reuses :func:`_serialize_one_control`; banners and other consumers use this
    to embed the same control shapes as ``controls_define``.
    """
    return [_serialize_one_control(ctrl) for ctrl in controls]


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
        group_entry: dict[str, Any] = {
            "id": group.id,
            "title": group.title,
            "controls": group_control_ids,
            "position": group.position,
            "collapsed": group.collapsed,
            "parentId": group.parent_id,
        }
        if group.icon is not None:
            group_entry["icon"] = str(group.icon)
        if group.tooltip:
            group_entry["tooltip"] = group.tooltip
        group_list.append(group_entry)

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


def get_control_value(ctrl: Control) -> Any:
    """Return the current value of a value-bearing control.

    ``Button`` controls have no value and raise :class:`TypeError`.
    """
    if isinstance(ctrl, Button):
        raise TypeError("Button controls do not carry a value")
    if isinstance(
        ctrl,
        (
            Slider,
            Dropdown,
            ColorPicker,
            Checkbox,
            TextField,
            TextArea,
            FileChooser,
            ValueEdit,
        ),
    ):
        return ctrl.value
    raise TypeError(f"Unknown control kind: {type(ctrl).__name__}")


def set_control_value(ctrl: Control, value: Any) -> None:
    """Coerce and set *value* on a value-bearing control.

    Sliders and value edits coerce to ``float``, checkboxes to ``bool``, and the
    string-valued controls (dropdown, color, text, textarea, file chooser) to
    ``str``.  ``Button`` controls have no value and raise :class:`TypeError`.
    """
    if isinstance(ctrl, (Slider, ValueEdit)):
        ctrl.value = float(value)
    elif isinstance(ctrl, Checkbox):
        ctrl.value = bool(value)
    elif isinstance(ctrl, (Dropdown, ColorPicker, TextField, TextArea, FileChooser)):
        ctrl.value = str(value)
    elif isinstance(ctrl, Button):
        raise TypeError("Button controls do not carry a value")
    else:
        raise TypeError(f"Unknown control kind: {type(ctrl).__name__}")
