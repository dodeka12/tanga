# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Serialization and tree-walking helpers for the layout view model."""

from __future__ import annotations

from typing import Any, Iterator, cast

from ._base import View
from .._controls import (
    Button,
    Checkbox,
    ColorPicker,
    Control,
    Dropdown,
    FileChooser,
    Slider,
    Table,
    TextArea,
    TextField,
    ValueEdit,
)
from .control_view import ControlView
from .control_views import (
    ButtonView,
    CheckboxView,
    ColorPickerView,
    DropdownView,
    FileChooserView,
    SliderView,
    TableView,
    TextAreaView,
    TextFieldView,
    ValueEditView,
)
from .log_view import LogView
from .scene_view import SceneView


def control_to_view(ctrl: Control) -> ControlView[Any]:
    """Wrap an existing :class:`Control` in its ``*View`` counterpart.

    The returned view reuses *ctrl* as its ``control`` (the single source of
    truth), so backend updates via ``scene._controls`` and control handlers
    registered under the control id keep working.
    """
    if isinstance(ctrl, Slider):
        view = SliderView(
            ctrl.id,
            label=ctrl.label,
            tooltip=ctrl.tooltip,
            variant=ctrl.variant,
            min=ctrl.min,
            max=ctrl.max,
            step=ctrl.step,
            value=ctrl.value,
            on_change=ctrl.on_change,
            on_press=ctrl.on_press,
            on_release=ctrl.on_release,
        )
    elif isinstance(ctrl, Dropdown):
        view = DropdownView(
            ctrl.id,
            label=ctrl.label,
            tooltip=ctrl.tooltip,
            variant=ctrl.variant,
            options=ctrl.options,
            value=ctrl.value,
            on_change=ctrl.on_change,
        )
    elif isinstance(ctrl, Button):
        view = ButtonView(
            ctrl.id,
            label=ctrl.label,
            tooltip=ctrl.tooltip,
            variant=ctrl.variant,
            icon=ctrl.icon,
            icon_only=ctrl.icon_only,
            on_click=ctrl.on_click,
        )
    elif isinstance(ctrl, Checkbox):
        view = CheckboxView(
            ctrl.id,
            label=ctrl.label,
            tooltip=ctrl.tooltip,
            variant=ctrl.variant,
            value=ctrl.value,
            on_change=ctrl.on_change,
        )
    elif isinstance(ctrl, TextField):
        view = TextFieldView(
            ctrl.id,
            label=ctrl.label,
            tooltip=ctrl.tooltip,
            value=ctrl.value,
            placeholder=ctrl.placeholder,
            on_change=ctrl.on_change,
        )
    elif isinstance(ctrl, TextArea):
        view = TextAreaView(
            ctrl.id,
            label=ctrl.label,
            tooltip=ctrl.tooltip,
            value=ctrl.value,
            placeholder=ctrl.placeholder,
            rows=ctrl.rows,
            on_change=ctrl.on_change,
        )
    elif isinstance(ctrl, ColorPicker):
        view = ColorPickerView(
            ctrl.id,
            label=ctrl.label,
            tooltip=ctrl.tooltip,
            value=ctrl.value,
            on_change=ctrl.on_change,
        )
    elif isinstance(ctrl, FileChooser):
        view = FileChooserView(
            ctrl.id,
            label=ctrl.label,
            tooltip=ctrl.tooltip,
            value=ctrl.value,
            placeholder=ctrl.placeholder,
            root=ctrl.root,
            accept=ctrl.accept,
            on_change=ctrl.on_change,
        )
    elif isinstance(ctrl, ValueEdit):
        view = ValueEditView(
            ctrl.id,
            label=ctrl.label,
            tooltip=ctrl.tooltip,
            min=ctrl.min,
            max=ctrl.max,
            step=ctrl.step,
            digits=ctrl.digits,
            value=ctrl.value,
            editable=ctrl.editable,
            on_change=ctrl.on_change,
        )
    elif isinstance(ctrl, Table):
        view = TableView(
            ctrl.id,
            label=ctrl.label,
            tooltip=ctrl.tooltip,
            columns=ctrl.columns,
            rows=ctrl.rows,
            allow_add_rows=ctrl.allow_add_rows,
            allow_add_columns=ctrl.allow_add_columns,
            allow_delete_rows=ctrl.allow_delete_rows,
            show_column_titles=ctrl.show_column_titles,
            show_row_numbers=ctrl.show_row_numbers,
            allow_delete_columns=ctrl.allow_delete_columns,
            sortable=ctrl.sortable,
            editable_titles=ctrl.editable_titles,
            max_history=ctrl.max_history,
            on_cell_change=ctrl.on_cell_change,
            on_row_add=ctrl.on_row_add,
            on_column_add=ctrl.on_column_add,
            on_row_delete=ctrl.on_row_delete,
            on_column_delete=ctrl.on_column_delete,
            on_column_title_change=ctrl.on_column_title_change,
            on_column_type_change=ctrl.on_column_type_change,
            on_cell_select=ctrl.on_cell_select,
            on_change=ctrl.on_change,
            on_enum_options=ctrl.on_enum_options,
        )
    else:
        raise TypeError(f"Unknown control kind: {type(ctrl).__name__}")
    # Each branch above builds the view whose control kind matches ``ctrl``, so
    # the base-typed ``ctrl`` is the right concrete control for ``view`` (which
    # the checker only sees as a union of view types).
    cast("Any", view).control = ctrl  # reuse the same control object
    return view


def serialize_layout(
    root: View, name: str = "", overlay: list[View] | None = None
) -> dict[str, Any]:
    """Serialize a view tree to the ``view_layout`` message.

    ``overlay`` lists extra views (e.g. global menus) mounted into the global
    overlay container; they are serialized after the root with the same id
    generator so node ids stay unique across root and overlay.
    """
    result = {
        "type": "view_layout",
        "name": name,
        "scenes": iter_scene_names(root),
        "root": root._serialize(),
    }
    if overlay:
        result["overlay"] = [view._serialize() for view in overlay]
    return result


def iter_scene_names(root: View) -> list[str]:
    """Return the deduplicated scene names referenced by *root* (DFS order)."""
    names: list[str] = []
    seen: set[str] = set()

    def _visit(view: View) -> None:
        scene = getattr(view, "scene", None)
        if isinstance(scene, str) and scene not in seen:
            seen.add(scene)
            names.append(scene)
        for child in getattr(view, "children", None) or ():
            _visit(child)
        for child in getattr(view, "overlay", None) or ():
            _visit(child)

    _visit(root)
    return names


def iter_scene_views(root: View) -> Iterator[SceneView]:
    """Yield every :class:`SceneView` in the tree (DFS order)."""

    def _visit(view: View) -> Iterator[SceneView]:
        if isinstance(view, SceneView):
            yield view
        for child in getattr(view, "children", None) or ():
            yield from _visit(child)
        for child in getattr(view, "overlay", None) or ():
            yield from _visit(child)

    yield from _visit(root)


def iter_control_views(root: View) -> Iterator[ControlView[Any]]:
    """Yield every control view in the tree (DFS order)."""

    def _visit(view: View) -> Iterator[ControlView[Any]]:
        if isinstance(view, ControlView):
            yield view
        for child in getattr(view, "children", None) or ():
            yield from _visit(child)
        for child in getattr(view, "overlay", None) or ():
            yield from _visit(child)

    yield from _visit(root)


def iter_log_views(root: View) -> Iterator[LogView]:
    """Yield every :class:`LogView` in the tree (DFS order)."""

    def _visit(view: View) -> Iterator[LogView]:
        if isinstance(view, LogView):
            yield view
        for child in getattr(view, "children", None) or ():
            yield from _visit(child)
        for child in getattr(view, "overlay", None) or ():
            yield from _visit(child)

    yield from _visit(root)
