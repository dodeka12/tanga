# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Interactive UI controls for the Tanga 3D viewer.

Defines Python data classes for sliders, dropdowns, buttons, and control
groups, plus serialization helpers and an async handler registry for
dispatching WebSocket events from the JS frontend.
"""

from __future__ import annotations

import logging
import numbers
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


#: Reserved control id for the backend-only client → server log sink.
CLIENT_LOG_ID = "client_log"


@dataclass
class ClientLogRecord:
    """A normalized log entry received from the browser frontend.

    ``level`` is one of ``"debug" | "info" | "warn" | "error"``; ``source`` is
    the emitting JS module (optional); ``data`` carries any extra structured
    context (optional); ``browser_id`` is the reporting client.
    """

    level: str
    message: str
    source: str | None = None
    data: dict[str, Any] | None = None
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


@dataclass
class TableColumnDelete:
    """A column deleted from a :class:`Table` control.

    ``col`` is the zero-based index of the deleted column.
    """

    col: int


@dataclass
class TableCellSelect:
    """The table's active (selected) cell changed.

    ``row`` and ``col`` are zero-based data indices; both are ``None`` when
    the selection is cleared (e.g. after a grid push replaces the DOM).
    """

    row: int | None
    col: int | None


@dataclass
class TableColumnTitleChange:
    """A column title (header) was renamed.

    ``col`` is the zero-based column index; ``title`` is the new header text.
    """

    col: int
    title: str


@dataclass
class TableColumnTypeChange:
    """A column type conversion was requested.

    ``col`` is the zero-based column index, ``target`` the requested kind
    (``"number" | "string" | "bool" | "enum"``), ``ok`` whether the base
    conversion succeeded, and ``column_type`` the resulting resolved type (or
    ``None`` when the conversion was rejected).
    """

    col: int
    target: str
    ok: bool
    column_type: ColumnType | None


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


async def _default_client_log_sink(
    record: ClientLogRecord, _event: ControlEvent
) -> None:
    """Log a client record to ``tanga.viz.client`` (the default sink).

    ``record.level`` maps to the logger method per the client-log contract;
    unknown levels fall back to ``warning``.
    """
    logger = logging.getLogger("tanga.viz.client")
    level = (record.level or "").lower()
    emit = {
        "debug": logger.debug,
        "info": logger.info,
        "warn": logger.warning,
        "error": logger.error,
    }.get(level, logger.warning)
    parts = [record.message]
    if record.source:
        parts.append(f"source={record.source}")
    if record.browser_id:
        parts.append(f"browser={record.browser_id}")
    if record.data:
        parts.append(f"data={record.data!r}")
    emit(" | ".join(parts))


@dataclass
class ClientLog(Control):
    """Backend-only sink for browser log events (never serialized)."""

    kind: str = "client_log"
    on_log: Handler = _default_client_log_sink

    def handle_event(self, event: str, payload: dict[str, Any]) -> Dispatch:
        record = ClientLogRecord(
            level=payload.get("level", "info"),
            message=str(payload.get("message", "")),
            source=payload.get("source"),
            data=payload.get("data"),
            browser_id=payload.get("browser_id"),
        )
        return Dispatch("log", record)


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
    if event == "column_delete":
        return Dispatch(
            "column_delete",
            TableColumnDelete(col=int(table_payload.get("col", 0))),
        )
    if event == "cell_select":
        row = table_payload.get("row")
        col = table_payload.get("col")
        return Dispatch(
            "cell_select",
            TableCellSelect(
                row=None if row is None else int(row),
                col=None if col is None else int(col),
            ),
        )
    if event == "column_title_change":
        return Dispatch(
            "column_title_change",
            TableColumnTitleChange(
                col=int(table_payload.get("col", 0)),
                title=str(table_payload.get("title", "")),
            ),
        )
    if event == "column_type_change":
        return Dispatch(
            "column_type_change",
            TableColumnTypeChange(
                col=int(table_payload.get("col", 0)),
                target=str(table_payload.get("type", "string")),
                ok=False,
                column_type=None,
            ),
        )
    return Dispatch()


# ── Table column types ──────────────────────────────────────

#: Table JSON/file format identifier and version (see :meth:`Table.to_dict`).
TABLE_FORMAT_ID = "pytanga-table"
TABLE_FORMAT_VERSION = "1.0"


@dataclass(frozen=True)
class ColumnType:
    """A resolved per-column type: ``kind`` + optional enum ``values`` + number
    ``format``.

    ``kind`` is one of ``"number" | "string" | "bool" | "enum"``; ``values``
    holds the allowed display strings for an ``enum`` column (empty otherwise);
    ``format`` is a Python ``str.format`` template for a ``number`` column
    (``None`` for every other kind).
    """

    kind: str
    values: tuple[str, ...] = ()
    format: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return the wire form ``{"kind", "values"?, "format"?}``."""
        out: dict[str, Any] = {"kind": self.kind}
        if self.kind == "enum":
            out["values"] = list(self.values)
        if self.kind == "number" and self.format is not None:
            out["format"] = self.format
        return out


def _cell_to_str(value: Any, column_type: ColumnType | None = None) -> str:
    """Serialize a cell value to its wire string form.

    ``bool`` becomes ``"true"``/``"false"`` (matching the frontend checkbox);
    a numeric value in a column carrying a ``format`` is rendered with
    ``column_type.format.format(value)``; every other value uses ``str``.
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    if (
        column_type is not None
        and column_type.format is not None
        and _is_number_value(value)
    ):
        try:
            return column_type.format.format(value)
        except (ValueError, TypeError, KeyError, IndexError):
            pass
    return str(value)


def _is_bool_value(value: Any) -> bool:
    """Return whether *value* counts as a boolean cell for type deduction."""
    return isinstance(value, bool)


def _is_number_value(value: Any) -> bool:
    """Return whether *value* counts as a number cell for type deduction."""
    return isinstance(value, numbers.Number) and not isinstance(value, bool)


def _deduce_column_type(values: list[Any]) -> ColumnType:
    """Deduce a column's type from its (non-empty) cell values."""
    nonempty = [
        v
        for v in values
        if v is not None and not (isinstance(v, str) and v.strip() == "")
    ]
    if not nonempty:
        return ColumnType("string")
    if all(_is_bool_value(v) for v in nonempty):
        return ColumnType("bool")
    if all(_is_number_value(v) for v in nonempty):
        return ColumnType("number")
    return ColumnType("string")


def _resolve_column_type(hint: Any, values: list[Any]) -> ColumnType:
    """Resolve a ``column_types`` hint (plus data) into a :class:`ColumnType`.

    ``None`` deduces from *values*; a scalar string selects ``number`` /
    ``string`` / ``bool``; an iterable of strings selects ``enum``.
    """
    if hint is None:
        return _deduce_column_type(values)
    if isinstance(hint, ColumnType):
        return hint
    if isinstance(hint, str):
        name = hint.strip().lower()
        if name in ("number", "float", "int"):
            return ColumnType("number")
        if name in ("string", "text", "str"):
            return ColumnType("string")
        if name in ("bool", "boolean"):
            return ColumnType("bool")
        raise ValueError(f"unknown column type {hint!r}")
    if isinstance(hint, dict):
        kind = str(hint.get("kind", "string"))
        if kind == "enum":
            return ColumnType("enum", tuple(str(v) for v in hint.get("values", [])))
        if kind == "number":
            fmt = hint.get("format")
            return ColumnType("number", format=None if fmt is None else str(fmt))
        return ColumnType(kind)
    if isinstance(hint, (list, tuple, set, frozenset)):
        return ColumnType("enum", tuple(str(v) for v in hint))
    raise ValueError(f"unsupported column type hint {hint!r}")


def _parse_version(version: Any) -> tuple[int, int]:
    """Parse a ``"major.minor"`` version string into ``(major, minor)``."""
    if isinstance(version, str):
        parts = version.split(".")
        major = int(parts[0]) if parts and parts[0] else 0
        minor = int(parts[1]) if len(parts) > 1 and parts[1] else 0
        return major, minor
    if isinstance(version, (int, float)):
        return int(version), 0
    return 0, 0


def _validate_table_file(data: dict[str, Any]) -> None:
    """Validate the ``id``/``version`` header of a table file dict."""
    if data.get("id") != TABLE_FORMAT_ID:
        raise ValueError(f"not a pytanga table file (id={data.get('id')!r})")
    current = _parse_version(TABLE_FORMAT_VERSION)
    version = _parse_version(data.get("version"))
    if version[0] != current[0]:
        raise ValueError(f"unsupported table version {data.get('version')!r}")
    if version[1] > current[1]:
        raise ValueError(
            f"table version {data.get('version')!r} is newer than this library supports"
        )


def _infer_column_type_from_strings(values: list[Any]) -> ColumnType:
    """Infer a column type from string content (used by CSV import)."""
    nonempty = [str(v).strip() for v in values if v is not None and str(v).strip() != ""]
    if not nonempty:
        return ColumnType("string")
    if all(v.lower() in ("true", "false") for v in nonempty):
        return ColumnType("bool")
    if all(_parse_number(v) is not None for v in nonempty):
        return ColumnType("number")
    return ColumnType("string")


def _parse_number(text: str) -> float | None:
    """Return ``float(text)`` or ``None`` when *text* is not numeric."""
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def _split_format_template(fmt: str) -> tuple[str, str, str] | None:
    """Split a single-placeholder ``str.format`` template into prefix/spec/suffix.

    Supports ``{}``, ``{0}``, ``{:spec}`` and ``{0:spec}``; returns ``None`` for
    anything else (no placeholder, multiple placeholders, or a named field).
    """
    start = fmt.find("{")
    if start < 0:
        return None
    end = fmt.find("}", start + 1)
    if end < 0:
        return None
    if fmt.find("{", end + 1) >= 0:
        return None
    inner = fmt[start + 1 : end]
    if ":" in inner:
        field, spec = inner.split(":", 1)
    else:
        field, spec = inner, ""
    if field not in ("", "0"):
        return None
    return fmt[:start], spec, fmt[end + 1 :]


def _coerce_number_cell(text: str, column_type: ColumnType | None) -> int | float | None:
    """Parse *text* back into a number for a ``number`` column.

    Accepts a plain int/float, or — when the column has a ``format`` — the
    formatted form (the template's literal text is stripped and the numeric core
    parsed with the spec's conversion).  Returns ``None`` when unparseable.
    """
    s = str(text).strip()
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    if column_type is None or column_type.format is None:
        return None
    parts = _split_format_template(column_type.format)
    if parts is None:
        return None
    prefix, spec, suffix = parts
    core = s
    if prefix and core.startswith(prefix):
        core = core[len(prefix) :]
    if suffix and core.endswith(suffix):
        core = core[: -len(suffix)]
    core = core.strip()
    if not core:
        return None
    if spec and spec[-1] in "dboxX":
        base = {"d": 10, "b": 2, "o": 8, "x": 16, "X": 16}[spec[-1]]
        try:
            return int(core, base)
        except ValueError:
            return None
    try:
        return float(core)
    except ValueError:
        return None


def _to_number(value: Any) -> int | float | None:
    """Coerce a cell to a number for column conversion (bool → 0/1)."""
    if isinstance(value, bool):
        return 1 if value else 0
    if _is_number_value(value):
        return value
    if isinstance(value, str):
        return _coerce_number_cell(value, None)
    return None


def _to_bool(value: Any) -> bool | None:
    """Coerce a cell to a bool for column conversion; ``None`` on failure."""
    if isinstance(value, bool):
        return value
    if _is_number_value(value):
        if value == 0:
            return False
        if value == 1:
            return True
        return None
    if isinstance(value, str):
        s = value.strip().lower()
        if s in ("true", "1"):
            return True
        if s in ("false", "0"):
            return False
        return None
    return None


@dataclass
class Table(Control):
    """An editable tabular-data control rendered as a native grid.

    ``columns`` lists the column headers (its length is the column count),
    ``rows`` is the row-major grid of cell values (strings, numbers, or bools),
    and ``column_types`` optionally fixes each column's type (``"number"`` /
    ``"string"`` / ``"bool"`` / a list of allowed strings for an enum).  Columns
    without an explicit type deduce one from their data.
    """

    kind: str = "table"

    def set_value(self, value: Any) -> None:
        self.columns = [str(c) for c in value["columns"]]
        self.rows = [list(row) for row in value["rows"]]
        if value.get("column_types") is not None:
            self.column_types = list(value["column_types"])
        self._normalize_column_type_hints()
        self._resolve_column_types()
        self.clear_history()
        self._save()

    def get_value(self) -> dict[str, Any]:
        rows, types = self._serialize_cells()
        return {
            "columns": list(self.columns),
            "rows": rows,
            "column_types": types,
            **self._view_state(),
        }

    def _fields(self) -> dict[str, Any]:
        rows, types = self._serialize_cells()
        return {
            "columns": list(self.columns),
            "rows": rows,
            "column_types": types,
            **self._view_state(),
            "allow_add_rows": self.allow_add_rows,
            "allow_add_columns": self.allow_add_columns,
            "allow_delete_rows": self.allow_delete_rows,
            "show_column_titles": self.show_column_titles,
            "show_row_numbers": self.show_row_numbers,
            "allow_delete_columns": self.allow_delete_columns,
            "sortable": self.sortable,
            "editable_titles": self.editable_titles,
        }

    columns: list[str] = field(default_factory=list)
    rows: list[list[Any]] = field(default_factory=list)
    column_types: list[Any] | None = field(default=None)
    _column_types: list[ColumnType] = field(default_factory=list, repr=False, compare=False)
    allow_add_rows: bool = True
    allow_add_columns: bool = True
    allow_delete_rows: bool = True
    show_column_titles: bool = True
    show_row_numbers: bool = False
    allow_delete_columns: bool = True
    sortable: bool = True
    editable_titles: bool = True
    column_widths: list[float] | None = field(default=None)
    row_height: int = 24
    sort: dict[str, Any] | None = field(default=None)
    _json_path: str | None = field(default=None, repr=False, compare=False)
    max_history: int = 100
    on_cell_change: Handler | None = None
    on_row_add: Handler | None = None
    on_column_add: Handler | None = None
    on_row_delete: Handler | None = None
    on_column_delete: Handler | None = None
    on_column_title_change: Handler | None = None
    on_column_type_change: Handler | None = None
    on_cell_select: Handler | None = None
    on_change: Handler | None = None
    active_cell: tuple[int, int] | None = field(default=None, repr=False, compare=False)
    _undo: list[dict[str, Any]] = field(default_factory=list, repr=False, compare=False)
    _redo: list[dict[str, Any]] = field(default_factory=list, repr=False, compare=False)

    def __post_init__(self) -> None:
        self._normalize_column_type_hints()
        self._resolve_column_types()

    def _normalize_column_type_hints(self) -> None:
        n = len(self.columns)
        hints = list(self.column_types) if self.column_types is not None else []
        if len(hints) < n:
            hints.extend([None] * (n - len(hints)))
        self.column_types = hints[:n]

    def _resolve_column_types(self) -> None:
        hints = self.column_types or []
        self._column_types = [
            _resolve_column_type(
                hints[c] if c < len(hints) else None,
                [row[c] for row in self.rows if c < len(row)],
            )
            for c in range(len(self.columns))
        ]

    def _serialize_cells(self) -> tuple[list[list[str]], list[dict[str, Any]]]:
        types = self._column_types
        rows = [
            [_cell_to_str(v, types[c] if c < len(types) else None) for c, v in enumerate(row)]
            for row in self.rows
        ]
        return rows, [t.to_dict() for t in types]

    def _view_state(self) -> dict[str, Any]:
        """Return the non-default presentation state (omitted keys = defaults)."""
        out: dict[str, Any] = {}
        if self.column_widths is not None:
            out["column_widths"] = list(self.column_widths)
        if self.row_height != 24:
            out["row_height"] = self.row_height
        if self.sort is not None:
            out["sort"] = self.sort
        return out

    def _apply_view_state(self, view: dict[str, Any]) -> None:
        """Merge a partial view-state payload (from ``table_view_change``)."""
        if "column_widths" in view:
            widths = view["column_widths"]
            self.column_widths = [float(w) for w in widths] if widths is not None else None
        if "row_height" in view:
            self.row_height = int(view["row_height"])
        if "sort" in view:
            sort = view["sort"]
            self.sort = (
                None
                if sort is None
                else {"column": int(sort.get("column", 0)), "order": str(sort.get("order", "asc"))}
            )
        self._save()

    def to_dict(self) -> dict[str, Any]:
        """Return the full file format (id + version + data + types + view state)."""
        rows, types = self._serialize_cells()
        return {
            "id": TABLE_FORMAT_ID,
            "version": TABLE_FORMAT_VERSION,
            "columns": list(self.columns),
            "rows": rows,
            "column_types": types,
            **self._view_state(),
        }

    def from_dict(self, data: dict[str, Any]) -> None:
        """Load from a ``to_dict`` dict, validating the format id and version."""
        _validate_table_file(data)
        self.columns = [str(c) for c in data.get("columns", [])]
        self.rows = [list(row) for row in data.get("rows", [])]
        self.column_types = (
            list(data["column_types"]) if data.get("column_types") is not None else None
        )
        self.column_widths = (
            [float(w) for w in data["column_widths"]]
            if data.get("column_widths") is not None
            else None
        )
        self.row_height = int(data.get("row_height", 24))
        sort = data.get("sort")
        self.sort = (
            None
            if sort is None
            else {"column": int(sort["column"]), "order": str(sort["order"])}
        )
        self._normalize_column_type_hints()
        self._resolve_column_types()
        self.clear_history()

    def to_json(self, path: Any) -> None:
        import json
        from pathlib import Path

        Path(path).write_text(json.dumps(self.to_dict(), indent=2) + "\n", encoding="utf-8")

    def from_json(self, path: Any) -> None:
        import json
        from pathlib import Path

        self.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    def to_csv(self, path: Any) -> None:
        import csv

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(self.columns)
            for row in self.rows:
                writer.writerow([_cell_to_str(v) for v in row])

    def from_csv(self, path: Any) -> None:
        import csv

        with open(path, newline="", encoding="utf-8") as f:
            data = list(csv.reader(f))
        self.columns = [str(c) for c in data[0]] if data else []
        self.rows = [list(row) for row in data[1:]] if data else []
        hints = []
        for c in range(len(self.columns)):
            col_values = [row[c] for row in self.rows if c < len(row)]
            hints.append(_infer_column_type_from_strings(col_values))
        self.column_types = hints
        self.column_widths = None
        self.row_height = 24
        self.sort = None
        self._normalize_column_type_hints()
        self._resolve_column_types()
        self.clear_history()

    def _save(self) -> None:
        """Persist to ``_json_path`` (atomic) when auto-save is enabled."""
        if self._json_path is None:
            return
        import json
        import os
        import tempfile

        path = os.fspath(self._json_path)
        directory = os.path.dirname(path) or "."
        fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, indent=2)
                f.write("\n")
            os.replace(tmp, path)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

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
        if event == "table_view_change":
            nested = payload.get("value")
            view = nested if isinstance(nested, dict) else payload
            self._apply_view_state(view)
            return Dispatch()

        if event == "column_type_change":
            change = parse_table_event(event, payload).value
            ok = self.convert_column(change.col, change.target)
            return Dispatch(
                "column_type_change",
                TableColumnTypeChange(
                    change.col,
                    change.target,
                    ok,
                    self._column_types[change.col] if ok else None,
                ),
                push=(self.get_value() if ok else None),
            )

        if event in ("undo", "redo"):
            changed = self.undo() if event == "undo" else self.redo()
            if changed:
                value = self.get_value()
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
        elif event == "row_delete":
            self.delete_rows(change.rows)
        elif event == "column_delete":
            self.delete_column(change.col)
        elif event == "cell_select":
            self.active_cell = (
                None if change.row is None or change.col is None else (change.row, change.col)
            )
        elif event == "column_title_change":
            self.rename_column(change.col, change.title)
        return d

    def _snapshot(self) -> dict[str, Any]:
        """Return a deep copy of the current grid state (data + type hints)."""
        return {
            "columns": list(self.columns),
            "rows": [list(row) for row in self.rows],
            "column_types": list(self.column_types) if self.column_types is not None else None,
        }

    def _push_undo(self) -> None:
        """Record the current state on the undo stack and clear the redo stack."""
        self._undo.append(self._snapshot())
        if self.max_history is not None and len(self._undo) > self.max_history:
            del self._undo[0]
        self._redo.clear()

    def _restore(self, snap: dict[str, Any]) -> None:
        """Restore columns/rows and type hints from a snapshot."""
        self.columns = list(snap["columns"])
        self.rows = [list(row) for row in snap["rows"]]
        self.column_types = list(snap["column_types"]) if snap.get("column_types") is not None else None
        self._normalize_column_type_hints()
        self._resolve_column_types()

    def set_cell(self, row: int, col: int, value: str) -> bool:
        """Record history and set a single cell's value.

        For a ``number`` column the entered text is coerced back to a number
        (rejecting unparseable input); other columns store the value as-is.
        """
        if not (0 <= row < len(self.rows)) or not (0 <= col < len(self.columns)):
            return False
        column_type = self._column_types[col] if col < len(self._column_types) else None
        if column_type is not None and column_type.kind == "number":
            parsed = _coerce_number_cell(str(value), column_type)
            if parsed is None:
                return False
            stored: Any = parsed
        else:
            stored = value
        self._push_undo()
        self.rows[row][col] = stored
        self._save()
        return True

    def get_cell(self, row: int, col: int) -> str:
        """Return the cell at *row*/*col* (zero-based).

        Raises ``IndexError`` when *row* or *col* is out of range (matching
        :meth:`set_cell`, which rejects the same out-of-range positions).
        """
        if not (0 <= row < len(self.rows)) or not (0 <= col < len(self.columns)):
            raise IndexError(f"cell ({row}, {col}) out of range")
        return self.rows[row][col]

    def insert_row(self, row: int, values: list[str]) -> bool:
        """Record history and insert a row at *row* (zero-based)."""
        if not 0 <= row <= len(self.rows):
            return False
        self._push_undo()
        vals = list(values)
        while len(vals) < len(self.columns):
            vals.append("")
        self.rows.insert(row, vals)
        self._save()
        return True

    def insert_column(
        self, col: int, header: str, values: list[Any], column_type: Any = None
    ) -> bool:
        """Record history and insert a column at *col* (zero-based)."""
        if not 0 <= col <= len(self.columns):
            return False
        self._push_undo()
        self.columns.insert(col, str(header))
        vals = list(values)
        while len(vals) < len(self.rows):
            vals.append("")
        for r, val in enumerate(vals[: len(self.rows)]):
            self.rows[r].insert(col, val)
        hints = list(self.column_types) if self.column_types is not None else []
        while len(hints) < len(self.columns) - 1:
            hints.append(None)
        hints.insert(col, column_type)
        self.column_types = hints
        self._resolve_column_types()
        self._save()
        return True

    def delete_rows(self, rows: list[int]) -> bool:
        """Record history and delete the given rows (zero-based indexes)."""
        valid = sorted({r for r in rows if 0 <= r < len(self.rows)}, reverse=True)
        if not valid:
            return False
        self._push_undo()
        for r in valid:
            del self.rows[r]
        self._save()
        return True

    def delete_column(self, col: int) -> bool:
        """Record history and delete the column at *col* (zero-based)."""
        if not 0 <= col < len(self.columns):
            return False
        self._push_undo()
        del self.columns[col]
        for row in self.rows:
            del row[col]
        if self.column_types is not None and col < len(self.column_types):
            del self.column_types[col]
        self._resolve_column_types()
        self._save()
        return True

    def set_column_format(self, col: int, fmt: str | None) -> bool:
        """Set the ``format`` template of a ``number`` column (``None`` clears it).

        Validates the template with a dry-run (raising :class:`ValueError` on a
        bad template) and returns ``False`` when the column is not a ``number``
        column.  The format is mirrored into the ``column_types`` hint list so
        re-resolution (e.g. after ``insert_column``) keeps it.
        """
        if not 0 <= col < len(self.columns):
            return False
        if self._column_types[col].kind != "number":
            return False
        if fmt is not None:
            try:
                fmt.format(0)
            except (ValueError, TypeError, KeyError, IndexError):
                raise ValueError(f"invalid number format template {fmt!r}")
        self._push_undo()
        self._column_types[col] = ColumnType("number", format=fmt)
        hints = (
            list(self.column_types)
            if self.column_types is not None
            else [None] * len(self.columns)
        )
        hints[col] = {"kind": "number", "format": fmt} if fmt is not None else "number"
        self.column_types = hints
        self._save()
        return True

    def rename_column(self, col: int, title: str) -> bool:
        """Record history and rename the column at *col* (zero-based)."""
        if not 0 <= col < len(self.columns):
            return False
        self._push_undo()
        self.columns[col] = str(title)
        self._save()
        return True

    def convert_column(self, col: int, target: str) -> bool:
        """Convert the column at *col* to *target* type; return whether applied.

        ``string`` always works; ``number`` (bool → 1/0, string → parse, else
        fail); ``bool`` (number 0/1 only, else fail; string
        ``"true"``/``"1"``/``"false"``/``"0"``); ``enum`` (distinct non-empty
        values, only when ``0 < len < 20``).  On success records undo, rewrites
        the column cells, sets the resolved type and saves; otherwise leaves the
        model untouched and returns ``False``.
        """
        target = str(target).strip().lower()
        if target not in ("number", "string", "bool", "enum"):
            return False
        if not 0 <= col < len(self.columns):
            return False
        if self._column_types[col].kind == target:
            return True

        values = [row[col] if col < len(row) else "" for row in self.rows]
        if target == "string":
            converted = [str(v) for v in values]
        elif target == "number":
            converted = []
            for v in values:
                n = _to_number(v)
                if n is None:
                    return False
                converted.append(n)
        elif target == "bool":
            converted = []
            for v in values:
                b = _to_bool(v)
                if b is None:
                    return False
                converted.append(b)
        else:  # enum
            strings = [_cell_to_str(v) for v in values]
            distinct = sorted({s for s in strings if s.strip() != ""})
            if not distinct or len(distinct) >= 20:
                return False
            converted = strings

        self._push_undo()
        for r, row in enumerate(self.rows):
            while len(row) <= col:
                row.append("")
            row[col] = converted[r]

        if target == "enum":
            new_type = ColumnType("enum", tuple(distinct))
        elif target == "number":
            new_type = ColumnType("number")
        else:
            new_type = ColumnType(target)
        self._column_types[col] = new_type
        hints = (
            list(self.column_types)
            if self.column_types is not None
            else [None] * len(self.columns)
        )
        while len(hints) <= col:
            hints.append(None)
        hints[col] = new_type.to_dict()
        self.column_types = hints
        self._save()
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
        self._save()
        return True

    def redo(self) -> bool:
        """Restore the next grid state; return whether anything was redone."""
        if not self._redo:
            return False
        self._undo.append(self._snapshot())
        self._restore(self._redo.pop())
        self._save()
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
