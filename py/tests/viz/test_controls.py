# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Unit tests for pytanga.viz._controls — data model, serialization, handler registry."""

from __future__ import annotations

from pytanga.viz._controls import (
    Button,
    Checkbox,
    ColorPicker,
    ControlHandlerRegistry,
    Dispatch,
    Dropdown,
    EControlVariant,
    Label,
    Markdown,
    Slider,
    Table,
    TableCellChange,
    TableCellSelect,
    TableColumnTitleChange,
    TextArea,
    TextField,
    ValueEdit,
    _serialize_one_control,
    get_control_value,
    set_control_value,
)

# ── Test: Dispatch + Control.handle_event ────────────────────


def test_dispatch_defaults() -> None:
    d = Dispatch()
    assert (d.event, d.value, d.push) == (None, None, None)


def test_handle_event_change_is_pass_through() -> None:
    slider = Slider(id="s", value=0.25)
    d = slider.handle_event("change", {"value": 0.5})
    assert (d.event, d.value, d.push) == ("change", 0.5, None)
    assert slider.value == 0.25  # generic dispatch does not mutate the model


def test_handle_event_click_returns_no_value() -> None:
    d = Button(id="b").handle_event("click", {})
    assert (d.event, d.value, d.push) == ("click", None, None)


def test_handle_event_press_release_pass_through() -> None:
    slider = Slider(id="s")
    assert slider.handle_event("press", {"value": 0.1}).value == 0.1
    d = slider.handle_event("release", {"value": 0.9})
    assert (d.event, d.value, d.push) == ("release", 0.9, None)


def test_handle_event_unknown_falls_back_to_change() -> None:
    d = Dropdown(id="d").handle_event("unknown", {"value": "x"})
    assert (d.event, d.value) == ("change", "x")


# ── Test: Table.handle_event ─────────────────────────────────


def test_table_handle_event_cell_change_mutates_model() -> None:
    ctrl = Table(id="tbl", columns=["x"], rows=[["1"]])
    d = ctrl.handle_event("cell_change", {"value": {"row": 0, "col": 0, "value": "9"}})
    assert d.event == "cell_change"
    assert isinstance(d.value, TableCellChange)
    assert (d.value.row, d.value.col, d.value.value) == (0, 0, "9")
    assert d.push is None
    assert ctrl.rows == [["9"]]


def test_table_handle_event_row_add_mutates_model() -> None:
    ctrl = Table(id="tbl", columns=["x", "y"], rows=[["1", "2"]])
    d = ctrl.handle_event("row_add", {"value": {"row": 1, "values": ["3", "4"]}})
    assert d.event == "row_add"
    assert d.value.row == 1
    assert ctrl.rows == [["1", "2"], ["3", "4"]]


def test_table_handle_event_column_add_mutates_model() -> None:
    ctrl = Table(id="tbl", columns=["x"], rows=[["1"], ["2"]])
    d = ctrl.handle_event(
        "column_add", {"value": {"col": 1, "header": "y", "values": ["a", "b"]}}
    )
    assert d.event == "column_add"
    assert (d.value.col, d.value.header) == (1, "y")
    assert ctrl.columns == ["x", "y"]
    assert ctrl.rows == [["1", "a"], ["2", "b"]]


def test_table_handle_event_row_delete_mutates_model() -> None:
    ctrl = Table(id="tbl", columns=["x"], rows=[["1"], ["2"], ["3"]])
    d = ctrl.handle_event("row_delete", {"value": {"rows": [1]}})
    assert d.event == "row_delete"
    assert d.value.rows == [1]
    assert ctrl.rows == [["1"], ["3"]]


def test_table_handle_event_column_delete_mutates_model() -> None:
    ctrl = Table(id="tbl", columns=["x", "y"], rows=[["1", "2"], ["3", "4"]])
    d = ctrl.handle_event("column_delete", {"value": {"col": 0}})
    assert d.event == "column_delete"
    assert d.value.col == 0
    assert ctrl.columns == ["y"]
    assert ctrl.rows == [["2"], ["4"]]


def test_table_handle_event_cell_select_sets_active_cell() -> None:
    ctrl = Table(id="tbl", columns=["x", "y"], rows=[["1", "2"], ["3", "4"]])
    d = ctrl.handle_event("cell_select", {"value": {"row": 1, "col": 0}})
    assert d.event == "cell_select"
    assert isinstance(d.value, TableCellSelect)
    assert (d.value.row, d.value.col) == (1, 0)
    assert d.push is None
    assert ctrl.active_cell == (1, 0)


def test_table_handle_event_cell_select_clear() -> None:
    ctrl = Table(id="tbl", columns=["x"], rows=[["1"]])
    ctrl.active_cell = (0, 0)
    d = ctrl.handle_event("cell_select", {})
    assert d.event == "cell_select"
    assert (d.value.row, d.value.col) == (None, None)
    assert ctrl.active_cell is None


def test_table_handle_event_column_title_change_mutates_model() -> None:
    ctrl = Table(id="tbl", columns=["x", "y"], rows=[["1", "2"]])
    d = ctrl.handle_event("column_title_change", {"value": {"col": 1, "title": "renamed"}})
    assert d.event == "column_title_change"
    assert isinstance(d.value, TableColumnTitleChange)
    assert (d.value.col, d.value.title) == (1, "renamed")
    assert d.push is None
    assert ctrl.columns == ["x", "renamed"]


def test_table_rename_column_bounds_and_history() -> None:
    ctrl = Table(id="tbl", columns=["x"], rows=[["1"]])
    assert ctrl.rename_column(0, "new") is True
    assert ctrl.columns == ["new"]
    assert ctrl.rename_column(5, "x") is False
    assert ctrl.undo() is True
    assert ctrl.columns == ["x"]


def test_table_registers_on_column_type_change() -> None:
    async def handler(*_args, **_kwargs) -> None:
        """No-op type-change handler."""

    registry = ControlHandlerRegistry()
    ctrl = Table(id="tbl", columns=["a"], rows=[["1"]], on_column_type_change=handler)
    ctrl.register_handlers(registry)
    assert registry.get("tbl", "column_type_change") is handler


def test_table_handle_event_undo_fires_change() -> None:
    ctrl = Table(id="tbl", columns=["x"], rows=[["1"]])
    ctrl.set_cell(0, 0, "9")
    d = ctrl.handle_event("undo", {})
    assert d.event == "change"
    assert d.value == {"columns": ["x"], "rows": [["1"]], "column_types": [{"kind": "string"}]}
    assert d.push == d.value
    assert ctrl.rows == [["1"]]


def test_table_handle_event_redo_fires_change() -> None:
    ctrl = Table(id="tbl", columns=["x"], rows=[["1"]])
    ctrl.set_cell(0, 0, "9")
    ctrl.undo()
    d = ctrl.handle_event("redo", {})
    assert d.event == "change"
    assert d.value == {"columns": ["x"], "rows": [["9"]], "column_types": [{"kind": "string"}]}
    assert ctrl.rows == [["9"]]


def test_table_handle_event_undo_empty_history_noop() -> None:
    ctrl = Table(id="tbl", columns=["x"], rows=[["1"]])
    d = ctrl.handle_event("undo", {})
    assert (d.event, d.value, d.push) == (None, None, None)


def test_table_handle_event_unknown_noop() -> None:
    ctrl = Table(id="tbl", columns=["x"], rows=[["1"]])
    d = ctrl.handle_event("click", {})
    assert (d.event, d.value, d.push) == (None, None, None)


# ── Test: Slider serialization ──────────────────────────────


def test_serialize_slider() -> None:
    ctrl = Slider(
        id="pos_x",
        label="X Position",
        min=0.0,
        max=5.0,
        step=0.1,
        value=2.0,
    )
    result = _serialize_one_control(ctrl)
    assert result == {
        "id": "pos_x",
        "kind": "slider",
        "label": "X Position",
        "variant": "default",
        "min": 0.0,
        "max": 5.0,
        "step": 0.1,
        "value": 2.0,
    }


# ── Test: Dropdown serialization ────────────────────────────


def test_serialize_dropdown() -> None:
    ctrl = Dropdown(
        id="mode",
        label="Mode",
        options=["Wireframe", "Solid", "Translucent"],
        value="Solid",
    )
    result = _serialize_one_control(ctrl)
    assert result == {
        "id": "mode",
        "kind": "dropdown",
        "label": "Mode",
        "variant": "default",
        "options": ["Wireframe", "Solid", "Translucent"],
        "value": "Solid",
    }


def test_serialize_dropdown_toolbar_variant() -> None:
    ctrl = Dropdown(
        id="mode",
        variant=EControlVariant.TOOLBAR,
        options=["A", "B"],
        value="A",
    )
    assert _serialize_one_control(ctrl)["variant"] == "toolbar"


# ── Test: Button serialization ──────────────────────────────


def test_serialize_button() -> None:
    ctrl = Button(id="reset_btn", label="Reset")
    result = _serialize_one_control(ctrl)
    assert result == {
        "id": "reset_btn",
        "kind": "button",
        "label": "Reset",
        "variant": "default",
        "icon_only": False,
    }


# ── Test: ControlHandlerRegistry ────────────────────────────


def test_handler_registry_register_and_get() -> None:
    registry = ControlHandlerRegistry()

    async def my_handler(value: float) -> None:
        pass

    registry.register("pos_x", my_handler)
    assert registry.get("pos_x") is my_handler
    assert registry.get("nonexistent") is None


def test_handler_registry_unregister() -> None:
    registry = ControlHandlerRegistry()

    async def my_handler(value: float) -> None:
        pass

    registry.register("pos_x", my_handler)
    registry.unregister("pos_x")
    assert registry.get("pos_x") is None
    # Unregistering again should not raise
    registry.unregister("pos_x")


def test_handler_registry_clear() -> None:
    registry = ControlHandlerRegistry()

    async def handler_a(value: float) -> None:
        pass

    async def handler_b(value: str) -> None:
        pass

    registry.register("a", handler_a)
    registry.register("b", handler_b)
    registry.clear()
    assert registry.get("a") is None
    assert registry.get("b") is None


def test_handler_registry_event_keyed_round_trip() -> None:
    registry = ControlHandlerRegistry()

    async def on_change(value):
        pass

    async def on_row(value):
        pass

    registry.register("t", on_change)
    registry.register("t", on_row, event="row_add")
    assert registry.get("t") is on_change
    assert registry.get("t", "row_add") is on_row
    assert registry.get("t", "column_add") is None


def test_handler_registry_unregister_all_events() -> None:
    registry = ControlHandlerRegistry()

    async def h1(value):
        pass

    async def h2(value):
        pass

    registry.register("t", h1)
    registry.register("t", h2, event="row_add")
    registry.unregister("t")
    assert registry.get("t") is None
    assert registry.get("t", "row_add") is None


# ── Test: new control serialization ──────────────────────────


def test_serialize_text_field() -> None:
    ctrl = TextField(id="name", label="Name", value="a", placeholder="…")
    result = _serialize_one_control(ctrl)
    assert result == {
        "id": "name",
        "kind": "text",
        "label": "Name",
        "value": "a",
        "placeholder": "…",
    }


def test_serialize_text_area() -> None:
    ctrl = TextArea(id="notes", label="Notes", value="", rows=6)
    result = _serialize_one_control(ctrl)
    assert result == {
        "id": "notes",
        "kind": "textarea",
        "label": "Notes",
        "value": "",
        "placeholder": "",
        "rows": 6,
    }


def test_serialize_color_picker() -> None:
    ctrl = ColorPicker(id="col", label="Color", value="#ff0000")
    result = _serialize_one_control(ctrl)
    assert result == {
        "id": "col",
        "kind": "color",
        "label": "Color",
        "value": "#ff0000",
    }


def test_serialize_checkbox() -> None:
    ctrl = Checkbox(id="wire", label="Wireframe", value=True)
    result = _serialize_one_control(ctrl)
    assert result == {
        "id": "wire",
        "kind": "checkbox",
        "label": "Wireframe",
        "variant": "default",
        "value": True,
    }


def test_serialize_value_edit() -> None:
    ctrl = ValueEdit(
        id="zoom",
        label="Zoom",
        min=0.5,
        max=4.0,
        step=0.25,
        digits=2,
        value=1.5,
    )
    result = _serialize_one_control(ctrl)
    assert result == {
        "id": "zoom",
        "kind": "value_edit",
        "label": "Zoom",
        "min": 0.5,
        "max": 4.0,
        "step": 0.25,
        "digits": 2,
        "value": 1.5,
        "editable": True,
    }


def test_serialize_value_edit_not_editable() -> None:
    ctrl = ValueEdit(id="zoom", editable=False)
    assert _serialize_one_control(ctrl)["editable"] is False


def test_serialize_button_with_icon() -> None:
    ctrl = Button(id="reset", label="Reset", icon="material:refresh", icon_only=True)
    result = _serialize_one_control(ctrl)
    assert result == {
        "id": "reset",
        "kind": "button",
        "label": "Reset",
        "variant": "default",
        "icon": "material:refresh",
        "icon_only": True,
    }


def test_serialize_button_without_icon_has_no_icon_key() -> None:
    ctrl = Button(id="reset", label="Reset")
    result = _serialize_one_control(ctrl)
    assert "icon" not in result
    assert result["icon_only"] is False


def test_serialize_control_tooltip_present_when_set() -> None:
    ctrl = Slider(id="s", label="S", tooltip="hover text")
    assert _serialize_one_control(ctrl)["tooltip"] == "hover text"


def test_serialize_control_tooltip_absent_when_empty() -> None:
    ctrl = Slider(id="s", label="S")
    assert "tooltip" not in _serialize_one_control(ctrl)


# ── Test: Table control ──────────────────────────────────────


def test_serialize_table() -> None:
    ctrl = Table(
        id="tbl",
        label="Data",
        columns=["x", "y", "z"],
        rows=[["1", "2", "3"], ["4", "5", "6"]],
    )
    result = _serialize_one_control(ctrl)
    assert result == {
        "id": "tbl",
        "kind": "table",
        "label": "Data",
        "columns": ["x", "y", "z"],
        "rows": [["1", "2", "3"], ["4", "5", "6"]],
        "column_types": [{"kind": "string"}, {"kind": "string"}, {"kind": "string"}],
        "allow_add_rows": True,
        "allow_add_columns": True,
        "allow_delete_rows": True,
        "show_column_titles": True,
        "show_row_numbers": False,
        "allow_delete_columns": True,
        "sortable": True,
        "editable_titles": True,
    }


def test_serialize_table_disallows_adds() -> None:
    ctrl = Table(id="tbl", columns=["a"], allow_add_rows=False, allow_add_columns=False)
    result = _serialize_one_control(ctrl)
    assert result["allow_add_rows"] is False
    assert result["allow_add_columns"] is False


def test_serialize_table_flags_custom() -> None:
    ctrl = Table(
        id="tbl",
        columns=["a"],
        show_column_titles=False,
        show_row_numbers=True,
        allow_delete_columns=False,
        sortable=False,
    )
    result = _serialize_one_control(ctrl)
    assert result["show_column_titles"] is False
    assert result["show_row_numbers"] is True
    assert result["allow_delete_columns"] is False
    assert result["sortable"] is False


def test_table_sortable_defaults_true() -> None:
    assert Table(id="tbl").sortable is True
    assert _serialize_one_control(Table(id="tbl"))["sortable"] is True


def test_table_get_control_value() -> None:
    ctrl = Table(id="tbl", columns=["x"], rows=[["1"]])
    assert get_control_value(ctrl) == {
        "columns": ["x"],
        "rows": [["1"]],
        "column_types": [{"kind": "string"}],
    }


def test_table_set_control_value() -> None:
    ctrl = Table(id="tbl", columns=["x"], rows=[["1"]])
    set_control_value(ctrl, {"columns": ["y", "z"], "rows": [[2], [3]]})
    assert ctrl.columns == ["y", "z"]
    assert ctrl.rows == [[2], [3]]


def test_table_get_cell() -> None:
    ctrl = Table(id="tbl", columns=["x", "y"], rows=[["1", "2"], ["3", "4"]])
    assert ctrl.get_cell(0, 0) == "1"
    assert ctrl.get_cell(1, 1) == "4"


def test_label_get_control_value() -> None:
    ctrl = Label(id="lbl", value="hello")
    assert get_control_value(ctrl) == "hello"


def test_label_set_control_value_coerces_to_str() -> None:
    ctrl = Label(id="lbl")
    set_control_value(ctrl, 123)
    assert ctrl.value == "123"


def test_markdown_get_control_value() -> None:
    ctrl = Markdown(id="md", value="# Title")
    assert get_control_value(ctrl) == "# Title"


def test_markdown_set_control_value_coerces_to_str() -> None:
    ctrl = Markdown(id="md")
    set_control_value(ctrl, 99)
    assert ctrl.value == "99"


# ── Test: Table undo/redo history ────────────────────────────


def test_table_undo_redo_cell() -> None:
    ctrl = Table(id="tbl", columns=["x"], rows=[["1"]])
    assert ctrl.set_cell(0, 0, "9") is True
    assert ctrl.rows == [["9"]]
    assert ctrl.undo() is True
    assert ctrl.rows == [["1"]]
    assert ctrl.redo() is True
    assert ctrl.rows == [["9"]]


def test_table_undo_row_add_and_delete() -> None:
    ctrl = Table(id="tbl", columns=["x", "y"], rows=[["1", "2"], ["3", "4"]])
    ctrl.insert_row(1, ["a", "b"])
    assert ctrl.rows == [["1", "2"], ["a", "b"], ["3", "4"]]
    assert ctrl.undo() is True
    assert ctrl.rows == [["1", "2"], ["3", "4"]]
    ctrl.delete_rows([0, 1])
    assert ctrl.rows == []
    assert ctrl.undo() is True
    assert ctrl.rows == [["1", "2"], ["3", "4"]]


def test_table_undo_column_add() -> None:
    ctrl = Table(id="tbl", columns=["x"], rows=[["1"], ["2"]])
    ctrl.insert_column(1, "y", ["a", "b"])
    assert ctrl.columns == ["x", "y"]
    assert ctrl.rows == [["1", "a"], ["2", "b"]]
    assert ctrl.undo() is True
    assert ctrl.columns == ["x"]
    assert ctrl.rows == [["1"], ["2"]]


def test_table_undo_column_delete() -> None:
    ctrl = Table(id="tbl", columns=["x", "y"], rows=[["1", "2"], ["3", "4"]])
    assert ctrl.delete_column(1) is True
    assert ctrl.columns == ["x"]
    assert ctrl.rows == [["1"], ["3"]]
    assert ctrl.undo() is True
    assert ctrl.columns == ["x", "y"]
    assert ctrl.rows == [["1", "2"], ["3", "4"]]


def test_table_new_edit_clears_redo() -> None:
    ctrl = Table(id="tbl", columns=["x"], rows=[["1"]])
    ctrl.set_cell(0, 0, "9")
    assert ctrl.undo() is True
    assert ctrl.can_redo is True
    ctrl.set_cell(0, 0, "5")
    assert ctrl.can_redo is False


def test_table_max_history_caps_undo() -> None:
    ctrl = Table(id="tbl", columns=["x"], rows=[["0"]], max_history=2)
    for i in range(1, 5):
        ctrl.set_cell(0, 0, str(i))
    assert len(ctrl._undo) == 2
    assert ctrl.rows == [["4"]]


def test_table_out_of_range_no_history() -> None:
    ctrl = Table(id="tbl", columns=["x"], rows=[["1"]])
    assert ctrl.set_cell(5, 0, "9") is False
    assert ctrl.set_cell(0, 5, "9") is False
    assert ctrl.insert_row(5, [""]) is False
    assert ctrl.insert_column(5, "y", [""]) is False
    assert ctrl.delete_column(1) is False
    assert ctrl.delete_column(-1) is False
    assert ctrl.can_undo is False


def test_table_set_control_value_clears_history() -> None:
    ctrl = Table(id="tbl", columns=["x"], rows=[["1"]])
    ctrl.set_cell(0, 0, "9")
    assert ctrl.can_undo is True
    set_control_value(ctrl, {"columns": ["x"], "rows": [["2"]]})
    assert ctrl.can_undo is False
    assert ctrl.can_redo is False


# ── Test: control variants ───────────────────────────────────


def test_serialize_variant_defaults_to_default() -> None:
    for ctrl in (
        Button(id="b", label="B"),
        Checkbox(id="c", label="C"),
        Slider(id="s", label="S"),
    ):
        assert _serialize_one_control(ctrl)["variant"] == "default"


def test_serialize_menu_variant() -> None:
    assert (
        _serialize_one_control(Button(id="b", label="B", variant=EControlVariant.MENU))[
            "variant"
        ]
        == "menu"
    )
    assert (
        _serialize_one_control(
            Checkbox(id="c", label="C", variant=EControlVariant.MENU)
        )["variant"]
        == "menu"
    )
    assert (
        _serialize_one_control(Slider(id="s", label="S", variant=EControlVariant.MENU))[
            "variant"
        ]
        == "menu"
    )
