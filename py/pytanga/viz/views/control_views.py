# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Concrete HTML control views (one per ``_controls.Control`` kind)."""

from __future__ import annotations

from typing import Any

from .._controls import (
    Button,
    Checkbox,
    ColorPicker,
    Dropdown,
    EControlVariant,
    EnumOptionsHandler,
    FileChooser,
    ControlHandler,
    Label,
    Markdown,
    ProgressBar,
    Slider,
    Table,
    TextArea,
    TextField,
    ValueEdit,
)
from ._helpers import _TABLE_COLUMN_MIN_PX
from .._icons import Icon
from .._size import Size, SizeSpec
from .control_view import ControlView


class SliderView(ControlView[Slider]):
    """A numeric slider control as a view."""

    _node_type = "slider_view"

    def __init__(
        self,
        cid: str,
        *,
        label: str = "",
        variant: EControlVariant = EControlVariant.DEFAULT,
        min: float = 0.0,
        max: float = 1.0,
        step: float = 0.01,
        value: float | None = None,
        on_change: ControlHandler | None = None,
        on_press: ControlHandler | None = None,
        on_release: ControlHandler | None = None,
        tooltip: str = "",
        size: SizeSpec = None,
        preferred_width: SizeSpec = None,
        preferred_height: SizeSpec = None,
        min_width: SizeSpec = Size.px(120),
        min_height: SizeSpec = Size.px(32),
        max_width: SizeSpec = None,
        max_height: SizeSpec = None,
    ) -> None:
        super().__init__(
            cid,
            label=label,
            tooltip=tooltip,
            size=size,
            preferred_width=preferred_width,
            preferred_height=preferred_height,
            min_width=min_width,
            min_height=min_height,
            max_width=max_width,
            max_height=max_height,
        )
        self.control = Slider(
            id=cid,
            label=label,
            tooltip=self.tooltip,
            variant=variant,
            min=float(min),
            max=float(max),
            step=float(step),
            value=float(min) if value is None else float(value),
            on_change=on_change,
            on_press=on_press,
            on_release=on_release,
        )


class ButtonView(ControlView[Button]):
    """A clickable button control (with optional icon) as a view."""

    _node_type = "button_view"

    def __init__(
        self,
        cid: str,
        *,
        label: str = "",
        variant: EControlVariant = EControlVariant.DEFAULT,
        icon: Icon | None = None,
        icon_only: bool = False,
        on_click: ControlHandler | None = None,
        tooltip: str = "",
        size: SizeSpec = None,
        preferred_width: SizeSpec = None,
        preferred_height: SizeSpec = None,
        min_width: SizeSpec = Size.px(120),
        min_height: SizeSpec = Size.px(32),
        max_width: SizeSpec = None,
        max_height: SizeSpec = None,
    ) -> None:
        if icon_only:
            # Icon-only buttons render as a small square tile; shrink the
            # generic control floor (120×32) to match so adjacent icons don't
            # get a large empty gap around them.  Explicit ``min_width=`` /
            # ``min_height=`` still win.
            if min_width == Size.px(120):
                min_width = Size.px(28)
            if min_height == Size.px(32):
                min_height = Size.px(28)
        super().__init__(
            cid,
            label=label,
            tooltip=tooltip,
            size=size,
            preferred_width=preferred_width,
            preferred_height=preferred_height,
            min_width=min_width,
            min_height=min_height,
            max_width=max_width,
            max_height=max_height,
        )
        self.control = Button(
            id=cid,
            label=label,
            tooltip=self.tooltip,
            variant=variant,
            icon=icon,
            icon_only=icon_only,
            on_click=on_click,
        )


class DropdownView(ControlView[Dropdown]):
    """A dropdown/select control as a view."""

    _node_type = "dropdown_view"

    def __init__(
        self,
        cid: str,
        *,
        label: str = "",
        variant: EControlVariant = EControlVariant.DEFAULT,
        options: list[str] | tuple[str, ...] = (),
        value: str = "",
        on_change: ControlHandler | None = None,
        tooltip: str = "",
        size: SizeSpec = None,
        preferred_width: SizeSpec = None,
        preferred_height: SizeSpec = None,
        min_width: SizeSpec = Size.px(120),
        min_height: SizeSpec = Size.px(32),
        max_width: SizeSpec = None,
        max_height: SizeSpec = None,
    ) -> None:
        super().__init__(
            cid,
            label=label,
            tooltip=tooltip,
            size=size,
            preferred_width=preferred_width,
            preferred_height=preferred_height,
            min_width=min_width,
            min_height=min_height,
            max_width=max_width,
            max_height=max_height,
        )
        self.control = Dropdown(
            id=cid,
            label=label,
            tooltip=self.tooltip,
            variant=variant,
            options=list(options),
            value=value,
            on_change=on_change,
        )


class FileChooserView(ControlView[FileChooser]):
    """A file-selection (directory listing) view with no path field/browse button.

    The view renders the backend-driven directory listing only; it is meant to be
    embedded in any view container (or inside a :class:`FileChooserDialog`).  A
    path display, edit field, and browse button are intentionally not part of this
    view — compose those yourself (e.g. a :class:`TextFieldView` plus a
    :class:`ButtonView` that calls ``open_file_chooser``).
    """

    _node_type = "file_chooser_view"

    def __init__(
        self,
        cid: str,
        *,
        label: str = "",
        value: str = "",
        placeholder: str = "",
        root: str | None = None,
        file_filter: str = "",
        folders_only: bool = False,
        on_change: ControlHandler | None = None,
        tooltip: str = "",
        size: SizeSpec = None,
        preferred_width: SizeSpec = Size.px(400),
        preferred_height: SizeSpec = Size.px(320),
        min_width: SizeSpec = Size.px(320),
        min_height: SizeSpec = Size.px(240),
        max_width: SizeSpec = None,
        max_height: SizeSpec = None,
    ) -> None:
        super().__init__(
            cid,
            label=label,
            tooltip=tooltip,
            size=size,
            preferred_width=preferred_width,
            preferred_height=preferred_height,
            min_width=min_width,
            min_height=min_height,
            max_width=max_width,
            max_height=max_height,
        )
        self.control = FileChooser(
            id=cid,
            label=label,
            tooltip=self.tooltip,
            value=value,
            placeholder=placeholder,
            root=root,
            file_filter=file_filter,
            folders_only=folders_only,
            on_change=on_change,
        )


class TextFieldView(ControlView[TextField]):
    """A single-line text input control as a view."""

    _node_type = "text_field_view"

    def __init__(
        self,
        cid: str,
        *,
        label: str = "",
        value: str = "",
        placeholder: str = "",
        tooltip: str = "",
        on_change: ControlHandler | None = None,
        size: SizeSpec = None,
        preferred_width: SizeSpec = None,
        preferred_height: SizeSpec = None,
        min_width: SizeSpec = Size.px(120),
        min_height: SizeSpec = Size.px(32),
        max_width: SizeSpec = None,
        max_height: SizeSpec = None,
    ) -> None:
        super().__init__(
            cid,
            label=label,
            tooltip=tooltip,
            size=size,
            preferred_width=preferred_width,
            preferred_height=preferred_height,
            min_width=min_width,
            min_height=min_height,
            max_width=max_width,
            max_height=max_height,
        )
        self.control = TextField(
            id=cid,
            label=label,
            tooltip=tooltip,
            value=value,
            placeholder=placeholder,
            on_change=on_change,
        )


class TextAreaView(ControlView[TextArea]):
    """A multi-line text input control as a view."""

    _node_type = "text_area_view"

    def __init__(
        self,
        cid: str,
        *,
        label: str = "",
        value: str = "",
        placeholder: str = "",
        rows: int = 4,
        tooltip: str = "",
        on_change: ControlHandler | None = None,
        size: SizeSpec = None,
        preferred_width: SizeSpec = None,
        preferred_height: SizeSpec = None,
        min_width: SizeSpec = Size.px(120),
        min_height: SizeSpec = Size.px(32),
        max_width: SizeSpec = None,
        max_height: SizeSpec = None,
    ) -> None:
        super().__init__(
            cid,
            label=label,
            tooltip=tooltip,
            size=size,
            preferred_width=preferred_width,
            preferred_height=preferred_height,
            min_width=min_width,
            min_height=min_height,
            max_width=max_width,
            max_height=max_height,
        )
        self.control = TextArea(
            id=cid,
            label=label,
            tooltip=tooltip,
            value=value,
            placeholder=placeholder,
            rows=rows,
            on_change=on_change,
        )


class ColorPickerView(ControlView[ColorPicker]):
    """A color picker control as a view."""

    _node_type = "color_picker_view"

    def __init__(
        self,
        cid: str,
        *,
        label: str = "",
        value: str = "#ffffff",
        tooltip: str = "",
        on_change: ControlHandler | None = None,
        size: SizeSpec = None,
        preferred_width: SizeSpec = None,
        preferred_height: SizeSpec = None,
        min_width: SizeSpec = Size.px(120),
        min_height: SizeSpec = Size.px(32),
        max_width: SizeSpec = None,
        max_height: SizeSpec = None,
    ) -> None:
        super().__init__(
            cid,
            label=label,
            tooltip=tooltip,
            size=size,
            preferred_width=preferred_width,
            preferred_height=preferred_height,
            min_width=min_width,
            min_height=min_height,
            max_width=max_width,
            max_height=max_height,
        )
        self.control = ColorPicker(
            id=cid,
            label=label,
            tooltip=tooltip,
            value=value,
            on_change=on_change,
        )


class CheckboxView(ControlView[Checkbox]):
    """A boolean checkbox control as a view."""

    _node_type = "checkbox_view"

    def __init__(
        self,
        cid: str,
        *,
        label: str = "",
        variant: EControlVariant = EControlVariant.DEFAULT,
        value: bool = False,
        tooltip: str = "",
        on_change: ControlHandler | None = None,
        size: SizeSpec = None,
        preferred_width: SizeSpec = None,
        preferred_height: SizeSpec = None,
        min_width: SizeSpec = Size.px(120),
        min_height: SizeSpec = Size.px(32),
        max_width: SizeSpec = None,
        max_height: SizeSpec = None,
    ) -> None:
        super().__init__(
            cid,
            label=label,
            tooltip=tooltip,
            size=size,
            preferred_width=preferred_width,
            preferred_height=preferred_height,
            min_width=min_width,
            min_height=min_height,
            max_width=max_width,
            max_height=max_height,
        )
        self.control = Checkbox(
            id=cid,
            label=label,
            tooltip=tooltip,
            variant=variant,
            value=value,
            on_change=on_change,
        )


class ValueEditView(ControlView[ValueEdit]):
    """A numeric stepper control as a view."""

    _node_type = "value_edit_view"

    def __init__(
        self,
        cid: str,
        *,
        label: str = "",
        min: float = 0.0,
        max: float = 1.0,
        step: float = 0.1,
        digits: int = 2,
        value: float = 0.0,
        editable: bool = True,
        tooltip: str = "",
        on_change: ControlHandler | None = None,
        size: SizeSpec = None,
        preferred_width: SizeSpec = None,
        preferred_height: SizeSpec = None,
        min_width: SizeSpec = Size.px(120),
        min_height: SizeSpec = Size.px(32),
        max_width: SizeSpec = None,
        max_height: SizeSpec = None,
    ) -> None:
        super().__init__(
            cid,
            label=label,
            tooltip=tooltip,
            size=size,
            preferred_width=preferred_width,
            preferred_height=preferred_height,
            min_width=min_width,
            min_height=min_height,
            max_width=max_width,
            max_height=max_height,
        )
        self.control = ValueEdit(
            id=cid,
            label=label,
            tooltip=tooltip,
            min=float(min),
            max=float(max),
            step=float(step),
            digits=int(digits),
            value=float(value),
            editable=editable,
            on_change=on_change,
        )


class LabelView(ControlView[Label]):
    """A read-only text label control (configurable font size) as a view."""

    _node_type = "label_view"

    def __init__(
        self,
        cid: str,
        *,
        value: str = "",
        font_size: float = 14,
        tooltip: str = "",
        size: SizeSpec = None,
        preferred_width: SizeSpec = None,
        preferred_height: SizeSpec = None,
        min_width: SizeSpec = Size.px(120),
        min_height: SizeSpec = Size.px(32),
        max_width: SizeSpec = None,
        max_height: SizeSpec = None,
    ) -> None:
        super().__init__(
            cid,
            tooltip=tooltip,
            size=size,
            preferred_width=preferred_width,
            preferred_height=preferred_height,
            min_width=min_width,
            min_height=min_height,
            max_width=max_width,
            max_height=max_height,
        )
        self.control = Label(
            id=cid,
            label="",
            tooltip=self.tooltip,
            value=value,
            font_size=float(font_size),
        )


class MarkdownView(ControlView[Markdown]):
    """A read-only rendered-markdown control (with KaTeX math) as a view."""

    _node_type = "markdown_view"

    def __init__(
        self,
        cid: str,
        *,
        value: str = "",
        tooltip: str = "",
        size: SizeSpec = None,
        preferred_width: SizeSpec = None,
        preferred_height: SizeSpec = None,
        min_width: SizeSpec = Size.px(120),
        min_height: SizeSpec = Size.px(32),
        max_width: SizeSpec = None,
        max_height: SizeSpec = None,
    ) -> None:
        super().__init__(
            cid,
            tooltip=tooltip,
            size=size,
            preferred_width=preferred_width,
            preferred_height=preferred_height,
            min_width=min_width,
            min_height=min_height,
            max_width=max_width,
            max_height=max_height,
        )
        self.control = Markdown(
            id=cid,
            label="",
            tooltip=self.tooltip,
            value=value,
        )


class ProgressBarView(ControlView[ProgressBar]):
    """A determinate/indeterminate progress bar control as a view.

    ``indeterminate=True`` renders an animated bar; otherwise the determinate
    bar fills to ``value / total`` (empty when ``total <= 0``).  ``title`` is
    shown above the bar and ``text`` (when non-empty) below it.
    """

    _node_type = "progress_bar_view"

    def __init__(
        self,
        cid: str,
        *,
        title: str = "",
        value: float = 0.0,
        total: int = 0,
        indeterminate: bool = False,
        text: str = "",
        tooltip: str = "",
        size: SizeSpec = None,
        preferred_width: SizeSpec = Size.px(220),
        preferred_height: SizeSpec = None,
        min_width: SizeSpec = Size.px(160),
        min_height: SizeSpec = Size.px(40),
        max_width: SizeSpec = None,
        max_height: SizeSpec = None,
    ) -> None:
        super().__init__(
            cid,
            tooltip=tooltip,
            size=size,
            preferred_width=preferred_width,
            preferred_height=preferred_height,
            min_width=min_width,
            min_height=min_height,
            max_width=max_width,
            max_height=max_height,
        )
        self.control = ProgressBar(
            id=cid,
            label="",
            tooltip=self.tooltip,
            title=title,
            value=float(value),
            total=int(total),
            indeterminate=bool(indeterminate),
            text=text,
        )

    def _push_value(self) -> None:
        """Push the full progress state to the browser (if mounted)."""
        if self._push is not None:
            self._push(self.id, self.control.get_value())

    def set_text(self, text: str) -> None:
        """Set the status line below the bar and push it."""
        self.control.text = str(text)
        self._push_value()

    def set_total(self, total: int) -> None:
        """Set the total step count and push it."""
        self.control.total = int(total)
        self._push_value()

    def set_indeterminate(self, on: bool = True) -> None:
        """Toggle the indeterminate animation and push it."""
        self.control.indeterminate = bool(on)
        self._push_value()

    def set_progress(self, value: float, text: str | None = None) -> None:
        """Set the progress value (and optionally the status text) and push."""
        self.control.value = float(value)
        if text is not None:
            self.control.text = str(text)
        self._push_value()

    def start(self) -> None:
        """Switch to the indeterminate animation."""
        self.set_indeterminate(True)

    def stop(self) -> None:
        """Stop the indeterminate animation."""
        self.set_indeterminate(False)

    def reset(self) -> None:
        """Reset progress to zero and push it."""
        self.control.value = 0.0
        self._push_value()


class TableView(ControlView[Table]):
    """An editable tabular-data control rendered as a view."""

    _node_type = "table_view"

    def __init__(
        self,
        cid: str,
        *,
        label: str = "",
        columns: list[str] | tuple[str, ...] = (),
        rows: list[list[Any]] | tuple[tuple[Any, ...], ...] = (),
        column_types: list[Any] | tuple[Any, ...] | None = None,
        allow_add_rows: bool = True,
        allow_add_columns: bool = True,
        allow_delete_rows: bool = True,
        show_column_titles: bool = True,
        show_row_numbers: bool = False,
        allow_delete_columns: bool = True,
        sortable: bool = True,
        editable_titles: bool = True,
        max_history: int = 100,
        tooltip: str = "",
        json_path: str | None = None,
        on_cell_change: ControlHandler | None = None,
        on_row_add: ControlHandler | None = None,
        on_column_add: ControlHandler | None = None,
        on_row_delete: ControlHandler | None = None,
        on_column_delete: ControlHandler | None = None,
        on_column_title_change: ControlHandler | None = None,
        on_column_type_change: ControlHandler | None = None,
        on_cell_select: ControlHandler | None = None,
        on_change: ControlHandler | None = None,
        on_enum_options: EnumOptionsHandler | None = None,
        size: SizeSpec = None,
        preferred_width: SizeSpec = None,
        preferred_height: SizeSpec = None,
        min_width: SizeSpec = None,
        min_height: SizeSpec = None,
        max_width: SizeSpec = None,
        max_height: SizeSpec = None,
    ) -> None:
        # A native grid needs horizontal room for every column; default the min
        # width to a per-column estimate so an auto-sized overlay panel doesn't
        # clip the last column.  Default a natural preferred size so flow
        # containers bound the grid and it scrolls internally instead of growing
        # with content.  Explicit ``min_width=``/``preferred_*`` still win.
        ncols = max(1, len(columns))
        if min_width is None:
            min_width = Size.px(max(120, ncols * _TABLE_COLUMN_MIN_PX))
        if preferred_width is None:
            preferred_width = Size.px(480)
        if preferred_height is None:
            preferred_height = Size.px(320)
        super().__init__(
            cid,
            label=label,
            tooltip=tooltip,
            size=size,
            preferred_width=preferred_width,
            preferred_height=preferred_height,
            min_width=min_width,
            min_height=min_height,
            max_width=max_width,
            max_height=max_height,
        )
        self.control = Table(
            id=cid,
            label=label,
            tooltip=tooltip,
            columns=list(columns),
            rows=[list(row) for row in rows],
            column_types=list(column_types) if column_types is not None else None,
            allow_add_rows=allow_add_rows,
            allow_add_columns=allow_add_columns,
            allow_delete_rows=allow_delete_rows,
            show_column_titles=show_column_titles,
            show_row_numbers=show_row_numbers,
            allow_delete_columns=allow_delete_columns,
            sortable=sortable,
            editable_titles=editable_titles,
            max_history=max_history,
            on_cell_change=on_cell_change,
            on_row_add=on_row_add,
            on_column_add=on_column_add,
            on_row_delete=on_row_delete,
            on_column_delete=on_column_delete,
            on_column_title_change=on_column_title_change,
            on_column_type_change=on_column_type_change,
            on_cell_select=on_cell_select,
            on_change=on_change,
            on_enum_options=on_enum_options,
            _json_path=json_path,
        )
        if json_path is not None:
            import os

            if os.path.exists(json_path):
                self.control.from_json(json_path)
            else:
                self.control._save()

    def undo(self) -> bool:
        """Undo the last edit of the wrapped ``Table`` and push the grid."""
        changed = self.control.undo()
        if changed:
            self._push_value()
        return changed

    def redo(self) -> bool:
        """Redo the last undone edit of the wrapped ``Table`` and push the grid."""
        changed = self.control.redo()
        if changed:
            self._push_value()
        return changed

    def get_value(self) -> dict[str, Any]:
        """Return the wrapped ``Table``'s current grid (``{columns, rows}``)."""
        return self.control.get_value()

    def get_cell(self, row: int, col: int) -> str:
        """Return the cell at *row*/*col* from the wrapped ``Table``."""
        return self.control.get_cell(row, col)

    def set_cell(self, row: int, col: int, value: str) -> bool:
        """Set a single cell (recording history) and push the grid."""
        changed = self.control.set_cell(row, col, value)
        if changed:
            self._push_value()
        return changed

    def clear_history(self) -> None:
        """Clear the wrapped ``Table``'s undo and redo stacks."""
        self.control.clear_history()

    def add_row(self, values: list[str] | None = None) -> bool:
        """Append a row (blank by default) and push the grid to the browser."""
        vals = list(values) if values is not None else []
        changed = self.control.insert_row(len(self.control.rows), vals)
        if changed:
            self._push_value()
        return changed

    def add_column(
        self,
        header: str = "",
        values: list[Any] | None = None,
        column_type: Any = None,
    ) -> bool:
        """Append a column (blank cells by default) and push the grid."""
        vals = list(values) if values is not None else []
        changed = self.control.insert_column(
            len(self.control.columns), header, vals, column_type
        )
        if changed:
            self._push_value()
        return changed

    def delete_row(self, index: int) -> bool:
        """Delete the row at *index* (zero-based) and push the grid."""
        changed = self.control.delete_rows([index])
        if changed:
            self._push_value()
        return changed

    def delete_column(self, index: int) -> bool:
        """Delete the column at *index* (zero-based) and push the grid."""
        changed = self.control.delete_column(index)
        if changed:
            self._push_value()
        return changed

    def insert_row(self, index: int, values: list[str] | None = None) -> bool:
        """Insert a row at *index* (zero-based) and push the grid."""
        vals = list(values) if values is not None else []
        changed = self.control.insert_row(index, vals)
        if changed:
            self._push_value()
        return changed

    def insert_column(
        self,
        index: int,
        header: str = "",
        values: list[Any] | None = None,
        column_type: Any = None,
    ) -> bool:
        """Insert a column at *index* (zero-based) and push the grid."""
        vals = list(values) if values is not None else []
        changed = self.control.insert_column(index, header, vals, column_type)
        if changed:
            self._push_value()
        return changed

    def set_column_format(self, col: int, fmt: str | None) -> bool:
        """Set the ``format`` template of a ``number`` column and push the grid."""
        changed = self.control.set_column_format(col, fmt)
        if changed:
            self._push_value()
        return changed

    def rename_column(self, col: int, title: str) -> bool:
        """Rename the column at *col* (zero-based) without a full-grid push."""
        return self.control.rename_column(col, title)

    def convert_column(self, col: int, target: str) -> bool:
        """Convert the column at *col* to *target* type and push the grid."""
        changed = self.control.convert_column(col, target)
        if changed:
            self._push_value()
        return changed

    @property
    def active_cell(self) -> tuple[int, int] | None:
        """The currently selected cell (``(row, col)``), or ``None``."""
        return self.control.active_cell

    def _push_value(self) -> None:
        """Push the wrapped ``Table``'s grid to the browser (if mounted)."""
        if self._push is not None:
            self._push(self.id, self.control.get_value())

    def save(self, path: str | None = None) -> None:
        """Write the table to JSON (defaults to the auto-save ``json_path``)."""
        target = path if path is not None else self.control._json_path
        if target is None:
            raise ValueError("no path: pass path= or construct with json_path=")
        self.control.to_json(target)

    def load(self, path: str | None = None) -> None:
        """Load the table from JSON (defaults to the auto-save ``json_path``)."""
        target = path if path is not None else self.control._json_path
        if target is None:
            raise ValueError("no path: pass path= or construct with json_path=")
        self.control.from_json(target)
        self._push_value()

    def to_csv(
        self, path: str, delimiter: str = ",", decimal_separator: str = "."
    ) -> None:
        """Export the table data to CSV (no column types).

        ``delimiter`` and ``decimal_separator`` control the CSV dialect; use
        ``delimiter=";"`` / ``decimal_separator=","`` for European locales.
        """
        self.control.to_csv(
            path, delimiter=delimiter, decimal_separator=decimal_separator
        )

    def from_csv(
        self,
        path: str,
        delimiter: str | None = None,
        decimal_separator: str | None = None,
    ) -> None:
        """Import table data from CSV and push the grid.

        ``delimiter`` / ``decimal_separator`` default to ``None`` (auto-detect
        from file content); pass explicit values to override.
        """
        self.control.from_csv(
            path, delimiter=delimiter, decimal_separator=decimal_separator
        )
        self._push_value()

    @property
    def can_undo(self) -> bool:
        """Whether the wrapped ``Table`` can be undone."""
        return self.control.can_undo

    @property
    def can_redo(self) -> bool:
        """Whether the wrapped ``Table`` can be redone."""
        return self.control.can_redo
