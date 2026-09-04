# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Interactive UI controls for the Tanga 3D viewer.

Defines Python data classes for sliders, dropdowns, buttons, and control
groups, plus serialization helpers and an async handler registry for
dispatching WebSocket events from the JS frontend.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field, fields
from enum import Enum, StrEnum
from typing import Any, ClassVar

from ._icons import Icon


# ── Control variants ─────────────────────────────────────────


class EControlVariant(StrEnum):
    """Visual variants a control can render as.

    ``DEFAULT`` renders the control with its normal panel styling; ``MENU``
    renders it flat/borderless for use inside menu rows; ``TOOLBAR`` renders it
    compactly for use inside a horizontal toolbar.
    """

    DEFAULT = "default"
    MENU = "menu"
    TOOLBAR = "toolbar"


# ── Control event dataclass ──────────────────────────────────


@dataclass
class ControlEvent:
    """Metadata passed to every control handler alongside the value.

    Only *browser_id* is populated for now; additional fields may be added
    without breaking existing handler signatures.
    """

    browser_id: str | None = None


@dataclass
class TableCellChange:
    """A single edited cell in a :class:`Table` control.

    ``row`` and ``col`` are zero-based indices; ``value`` is the new cell text.
    """

    row: int
    col: int
    value: str


@dataclass
class TableRowAdd:
    """A row added to a :class:`Table` control.

    ``row`` is the zero-based index of the inserted row; ``values`` holds its
    cell contents (column-major order, matching the table's columns).
    """

    row: int
    values: list[str]


@dataclass
class TableColumnAdd:
    """A column added to a :class:`Table` control.

    ``col`` is the zero-based index of the inserted column, ``header`` its
    title, and ``values`` the per-row cell contents for the new column.
    """

    col: int
    header: str
    values: list[str]


@dataclass
class TableRowsDelete:
    """Rows deleted from a :class:`Table` control.

    ``rows`` holds the zero-based indexes of the deleted rows, in ascending
    order.
    """

    rows: list[int]


# ── Handler type alias ──────────────────────────────────────

Handler = Callable[[Any, ControlEvent], Awaitable[None]]
"""Async callback type for control interaction handlers.

Takes a ``value`` argument (float for sliders, str for dropdowns / text /
textarea / color pickers, bool for checkboxes, ``None`` for buttons / group
toggles) and a :class:`ControlEvent`, and returns an awaitable.
"""


@dataclass
class Dispatch:
    """What the ``Visualizer`` should do after a control applied an event.

    Returned by :meth:`Control.handle_event`.  The three fields describe the
    single lookup-and-invoke tail the visualizer runs for every control event:

    - ``event`` — the ``(id, event)`` handler to fire, or ``None`` for none.
    - ``value`` — the value handed to that handler.
    - ``push`` — a value to push back to the browser as ``control_update``, or
      ``None`` to skip the push.
    """

    event: str | None = None
    value: Any = None
    push: Any = None


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

    def handle_event(self, event: str, payload: dict[str, Any]) -> Dispatch:
        """Apply an incoming frontend *event* and return the dispatch to run.

        The generic implementation is a pass-through for value-bearing
        controls: it does **not** mutate the model (only :class:`Table` keeps
        its state authoritative).  Subclasses override this to map their own
        events onto model mutations.
        """
        if event == "click":
            return Dispatch("click", None, None)
        if event in ("press", "release"):
            return Dispatch(event, payload.get("value"), None)
        return Dispatch("change", payload.get("value"), None)

    _value_type: ClassVar[type | None] = None

    def set_value(self, value: Any) -> None:
        """Coerce and set this control's value in place.

        Scalar controls coerce via their ``_value_type`` (``float`` / ``bool`` /
        ``str``); :class:`Table` replaces its grid; ``Button`` has no value and
        raises :class:`TypeError`.
        """
        if self._value_type is None:
            raise TypeError(f"{type(self).__name__} controls do not carry a value")
        self.value = self._value_type(value)

    def get_value(self) -> Any:
        """Return this control's current value (see :meth:`set_value`)."""
        if self._value_type is None:
            raise TypeError(f"{type(self).__name__} controls do not carry a value")
        return self.value

    def _fields(self) -> dict[str, Any]:
        """Return the kind-specific fields merged into :meth:`serialize`."""
        return {}

    def serialize(self) -> dict[str, Any]:
        """Return this control's JSON-ready dict form."""
        result: dict[str, Any] = {
            "id": self.id,
            "kind": self.kind,
            "label": self.label,
        }
        if self.tooltip:
            result["tooltip"] = self.tooltip
        result.update(self._fields())
        return result

    def register_handlers(self, transport: Any) -> bool:
        """Register each ``on_*`` handler under its ``(id, event)`` key.

        The naming convention maps ``on_change`` → ``"change"``, ``on_click`` →
        ``"click"``, ``on_cell_change`` → ``"cell_change"``, …  Returns whether any
        handler was registered.
        """
        registered = False
        for f in fields(self):
            if not f.name.startswith("on_"):
                continue
            handler = getattr(self, f.name)
            if handler is not None:
                transport.register(self.id, handler, event=f.name[3:])
                registered = True
        return registered


@dataclass
class Slider(Control):
    """A numeric slider control with min/max/step bounds."""

    kind: str = "slider"
    _value_type: ClassVar[type | None] = float

    def _fields(self) -> dict[str, Any]:
        return {
            "variant": str(self.variant),
            "min": self.min,
            "max": self.max,
            "step": self.step,
            "value": self.value,
        }

    variant: EControlVariant = EControlVariant.DEFAULT
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
    _value_type: ClassVar[type | None] = str

    def _fields(self) -> dict[str, Any]:
        return {
            "variant": str(self.variant),
            "options": list(self.options),
            "value": self.value,
        }

    variant: EControlVariant = EControlVariant.DEFAULT
    options: list[str] = field(default_factory=list)
    value: str = ""
    on_change: Handler | None = None


@dataclass
class Button(Control):
    """A clickable button with an optional icon and an async callback."""

    kind: str = "button"

    def _fields(self) -> dict[str, Any]:
        d = {"variant": str(self.variant), "icon_only": self.icon_only}
        if self.icon is not None:
            d["icon"] = str(self.icon)
        return d

    variant: EControlVariant = EControlVariant.DEFAULT
    icon: Icon | None = None
    """Optional icon id (``family:name``); rendered before the label."""

    icon_only: bool = False
    """If ``True``, render only the icon as a small square button."""

    on_click: Handler | None = None


@dataclass
class FileChooser(Control):
    """A file-path control: a text field plus a backend-driven file browser."""

    kind: str = "file_chooser"
    _value_type: ClassVar[type | None] = str

    def _fields(self) -> dict[str, Any]:
        return {
            "value": self.value,
            "placeholder": self.placeholder,
            "root": self.root,
            "accept": self.accept,
        }

    value: str = ""
    placeholder: str = ""
    root: str | None = None
    accept: str = ""
    on_change: Handler | None = None


@dataclass
class TextField(Control):
    """A single-line text input control."""

    kind: str = "text"
    _value_type: ClassVar[type | None] = str

    def _fields(self) -> dict[str, Any]:
        return {"value": self.value, "placeholder": self.placeholder}

    value: str = ""
    placeholder: str = ""
    on_change: Handler | None = None


@dataclass
class TextArea(Control):
    """A multi-line text input control."""

    kind: str = "textarea"
    _value_type: ClassVar[type | None] = str

    def _fields(self) -> dict[str, Any]:
        return {"value": self.value, "placeholder": self.placeholder, "rows": self.rows}

    value: str = ""
    placeholder: str = ""
    rows: int = 4
    on_change: Handler | None = None


@dataclass
class ColorPicker(Control):
    """A color chooser control (native color input, hex value)."""

    kind: str = "color"
    _value_type: ClassVar[type | None] = str

    def _fields(self) -> dict[str, Any]:
        return {"value": self.value}

    value: str = "#ffffff"
    on_change: Handler | None = None


@dataclass
class Checkbox(Control):
    """A boolean checkbox control."""

    kind: str = "checkbox"
    _value_type: ClassVar[type | None] = bool

    def _fields(self) -> dict[str, Any]:
        return {"variant": str(self.variant), "value": self.value}

    variant: EControlVariant = EControlVariant.DEFAULT
    value: bool = False
    on_change: Handler | None = None


@dataclass
class ValueEdit(Control):
    """A numeric stepper control with up/down buttons and keyboard/wheel steps."""

    kind: str = "value_edit"
    _value_type: ClassVar[type | None] = float

    def _fields(self) -> dict[str, Any]:
        return {
            "min": self.min,
            "max": self.max,
            "step": self.step,
            "digits": self.digits,
            "value": self.value,
            "editable": self.editable,
        }

    min: float = 0.0
    max: float = 1.0
    step: float = 0.1
    digits: int = 2
    value: float = 0.0
    editable: bool = True
    on_change: Handler | None = None


def parse_table_event(event: str, payload: dict[str, Any]) -> Dispatch:
    """Parse a table event's payload into its handler payload (no mutation).

    Shared by :meth:`Table.handle_event` (which also mutates the model) and the
    visualizer's dispatch fallback, which still fires a handler when a table
    control id is not resolvable but a handler is registered.
    """
    nested = payload.get("value")
    table_payload = nested if isinstance(nested, dict) else payload

    if event == "cell_change":
        return Dispatch(
            "cell_change",
            TableCellChange(
                row=int(table_payload.get("row", 0)),
                col=int(table_payload.get("col", 0)),
                value=str(table_payload.get("value", "")),
            ),
        )
    if event == "row_add":
        return Dispatch(
            "row_add",
            TableRowAdd(
                row=int(table_payload.get("row", 0)),
                values=[str(v) for v in (table_payload.get("values") or [])],
            ),
        )
    if event == "column_add":
        return Dispatch(
            "column_add",
            TableColumnAdd(
                col=int(table_payload.get("col", 0)),
                header=str(table_payload.get("header", "")),
                values=[str(v) for v in (table_payload.get("values") or [])],
            ),
        )
    if event == "row_delete":
        return Dispatch(
            "row_delete",
            TableRowsDelete(rows=[int(r) for r in (table_payload.get("rows") or [])]),
        )
    return Dispatch()


@dataclass
class Table(Control):
    """An editable tabular-data control rendered as a Tabulator grid.

    ``columns`` lists the column headers (its length is the column count) and
    ``rows`` is the row-major grid of cell strings.  ``allow_add_rows`` /
    ``allow_add_columns`` gate the frontend's "+ Row" / "+ Column" buttons;
    ``allow_delete_rows`` gates the "− Selected" row-delete button.
    """

    kind: str = "table"

    def set_value(self, value: Any) -> None:
        self.columns = [str(c) for c in value["columns"]]
        self.rows = [[str(cell) for cell in row] for row in value["rows"]]
        self.clear_history()

    def get_value(self) -> dict[str, Any]:
        return {"columns": list(self.columns), "rows": [list(r) for r in self.rows]}

    def _fields(self) -> dict[str, Any]:
        return {
            "columns": list(self.columns),
            "rows": [list(row) for row in self.rows],
            "allow_add_rows": self.allow_add_rows,
            "allow_add_columns": self.allow_add_columns,
            "allow_delete_rows": self.allow_delete_rows,
        }

    columns: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
    allow_add_rows: bool = True
    allow_add_columns: bool = True
    allow_delete_rows: bool = True
    max_history: int = 100
    on_cell_change: Handler | None = None
    on_row_add: Handler | None = None
    on_column_add: Handler | None = None
    on_row_delete: Handler | None = None
    on_change: Handler | None = None
    _undo: list[dict[str, Any]] = field(default_factory=list, repr=False, compare=False)
    _redo: list[dict[str, Any]] = field(default_factory=list, repr=False, compare=False)

    def handle_event(self, event: str, payload: dict[str, Any]) -> Dispatch:
        """Apply a table event, mutating the model and recording history.

        Overrides :meth:`Control.handle_event` so the table stays authoritative:
        each frontend event maps to a mutation method and reports the matching
        payload dataclass to the registered handler.  The per-event mutation is
        best-effort (bounds-checked); the handler fires with the reported payload
        regardless, matching the legacy dispatch.  ``undo``/``redo`` restore a
        whole snapshot and report the bulk ``on_change`` handler (registered
        under ``"change"``) with the full ``{columns, rows}`` value, pushing the
        same value back to the browser.
        """
        if event in ("undo", "redo"):
            changed = self.undo() if event == "undo" else self.redo()
            if changed:
                value = self._snapshot()
                return Dispatch("change", value, push=value)
            return Dispatch()

        d = parse_table_event(event, payload)
        if d.event is None:
            return Dispatch()

        change = d.value
        if event == "cell_change":
            self.set_cell(change.row, change.col, change.value)
        elif event == "row_add":
            self.insert_row(change.row, change.values)
        elif event == "column_add":
            self.insert_column(change.col, change.header, change.values)
        else:  # row_delete
            self.delete_rows(change.rows)
        return d

    def _snapshot(self) -> dict[str, Any]:
        """Return a deep copy of the current grid state."""
        return {
            "columns": list(self.columns),
            "rows": [list(row) for row in self.rows],
        }

    def _push_undo(self) -> None:
        """Record the current state on the undo stack and clear the redo stack."""
        self._undo.append(self._snapshot())
        if self.max_history is not None and len(self._undo) > self.max_history:
            del self._undo[0]
        self._redo.clear()

    def _restore(self, snap: dict[str, Any]) -> None:
        """Restore columns/rows from a snapshot."""
        self.columns = list(snap["columns"])
        self.rows = [list(row) for row in snap["rows"]]

    def set_cell(self, row: int, col: int, value: str) -> bool:
        """Record history and set a single cell's value."""
        if not (0 <= row < len(self.rows)) or not (0 <= col < len(self.columns)):
            return False
        self._push_undo()
        self.rows[row][col] = str(value)
        return True

    def insert_row(self, row: int, values: list[str]) -> bool:
        """Record history and insert a row at *row* (zero-based)."""
        if not 0 <= row <= len(self.rows):
            return False
        self._push_undo()
        vals = [str(v) for v in values]
        while len(vals) < len(self.columns):
            vals.append("")
        self.rows.insert(row, vals)
        return True

    def insert_column(self, col: int, header: str, values: list[str]) -> bool:
        """Record history and insert a column at *col* (zero-based)."""
        if not 0 <= col <= len(self.columns):
            return False
        self._push_undo()
        self.columns.insert(col, str(header))
        vals = [str(v) for v in values]
        while len(vals) < len(self.rows):
            vals.append("")
        for r, val in enumerate(vals[: len(self.rows)]):
            self.rows[r].insert(col, val)
        return True

    def delete_rows(self, rows: list[int]) -> bool:
        """Record history and delete the given rows (zero-based indexes)."""
        valid = sorted({r for r in rows if 0 <= r < len(self.rows)}, reverse=True)
        if not valid:
            return False
        self._push_undo()
        for r in valid:
            del self.rows[r]
        return True

    def clear_history(self) -> None:
        """Clear both the undo and redo stacks."""
        self._undo.clear()
        self._redo.clear()

    @property
    def can_undo(self) -> bool:
        """True when there is history to undo."""
        return bool(self._undo)

    @property
    def can_redo(self) -> bool:
        """True when there is history to redo."""
        return bool(self._redo)

    def undo(self) -> bool:
        """Restore the previous grid state; return whether anything was undone."""
        if not self._undo:
            return False
        self._redo.append(self._snapshot())
        self._restore(self._undo.pop())
        return True

    def redo(self) -> bool:
        """Restore the next grid state; return whether anything was redone."""
        if not self._redo:
            return False
        self._undo.append(self._snapshot())
        self._restore(self._redo.pop())
        return True


@dataclass
class Label(Control):
    """A read-only display label control (text with an optional font size)."""

    kind: str = "label"
    _value_type: ClassVar[type | None] = str

    def _fields(self) -> dict[str, Any]:
        return {"value": self.value, "font_size": self.font_size}

    value: str = ""
    font_size: float = 14


@dataclass
class Markdown(Control):
    """A read-only display markdown control (rendered with optional KaTeX math)."""

    kind: str = "markdown"
    _value_type: ClassVar[type | None] = str

    def _fields(self) -> dict[str, Any]:
        return {"value": self.value}

    value: str = ""


# ── Handler registry ─────────────────────────────────────────


class HandlerOrigin(str, Enum):
    """Owner of an entry in :class:`ControlHandlerRegistry`.

    ``CONTROL`` entries belong to UI panel controls (sliders/buttons/…);
    ``INTERACTION`` entries belong to entity object-interaction handlers
    (``on_interaction`` / ``ActPoint`` drag & click handlers).  Both share one
    ``(id, event)`` registry; the origin lets ``clear_controls()`` remove only
    the control entries.
    """

    CONTROL = "control"
    INTERACTION = "interaction"


class ControlHandlerRegistry:
    """Maps ``(control_id, event)`` pairs to async handler callables.

    ``event`` is a short string (``"change"``, ``"click"``, ``"press"``,
    ``"release"``, ``"cell_change"``, ``"row_add"``, ``"column_add"``,
    ``"toggle"``).  ``register(control_id, handler)`` is a convenience that
    registers under ``"change"`` for the common single-handler case.

    Each entry is tagged with a :class:`HandlerOrigin` so callers can clear
    only one class of handler (see :meth:`clear`).
    """

    def __init__(self) -> None:
        self._handlers: dict[tuple[str, str], tuple[HandlerOrigin, Handler]] = {}

    def register(
        self,
        control_id: str,
        handler: Handler,
        *,
        event: str = "change",
        origin: HandlerOrigin = HandlerOrigin.CONTROL,
    ) -> None:
        """Register an async handler for a control event.

        Args:
            control_id: The ``id`` of the :class:`Control` (or entity).
            handler: An ``async def`` callable that receives the control's
                value (float for sliders, str for dropdowns).
            event: The event name (default ``"change"``).
            origin: Which class of handler this entry belongs to.
        """
        self._handlers[(control_id, event)] = (origin, handler)

    def unregister(self, control_id: str, event: str | None = None) -> None:
        """Remove a handler (no-op if not found).

        With ``event=None`` removes every handler registered under
        *control_id*.
        """
        if event is None:
            for key in [k for k in self._handlers if k[0] == control_id]:
                del self._handlers[key]
        else:
            self._handlers.pop((control_id, event), None)

    def get(self, control_id: str, event: str = "change") -> Handler | None:
        """Look up the handler for ``(control_id, event)``, or ``None``."""
        entry = self._handlers.get((control_id, event))
        return entry[1] if entry is not None else None

    def clear(self, origin: HandlerOrigin | None = None) -> None:
        """Remove registered handlers.

        With ``origin=None`` removes every handler.  Otherwise only handlers
        tagged with *origin* are removed.
        """
        if origin is None:
            self._handlers.clear()
        else:
            for key in [k for k, v in self._handlers.items() if v[0] == origin]:
                del self._handlers[key]


# ── Serialization ────────────────────────────────────────────


def _serialize_one_control(ctrl: Control) -> dict[str, Any]:
    """Serialize a single :class:`Control` to its JSON-ready dict form.

    Thin delegate over :meth:`Control.serialize` (kept for backward
    compatibility); the per-kind logic lives on each control class.
    """
    return ctrl.serialize()


def serialize_control_defs(controls: list[Control]) -> list[dict[str, Any]]:
    """Serialize a flat list of :class:`Control` objects to their dict forms.

    Reuses :meth:`Control.serialize`; banners and other consumers use this to
    embed the same control shapes.
    """
    return [ctrl.serialize() for ctrl in controls]


def get_control_value(ctrl: Control) -> Any:
    """Return the current value of a value-bearing control.

    ``Button`` controls have no value and raise :class:`TypeError`.  Thin
    delegate over :meth:`Control.get_value`.
    """
    return ctrl.get_value()


def set_control_value(ctrl: Control, value: Any) -> None:
    """Coerce and set *value* on a value-bearing control.

    Sliders/value-edits coerce to ``float``, checkboxes to ``bool``, string
    controls to ``str``, and :class:`Table` replaces its grid.  ``Button``
    controls have no value and raise :class:`TypeError`.  Thin delegate over
    :meth:`Control.set_value`.
    """
    ctrl.set_value(value)
