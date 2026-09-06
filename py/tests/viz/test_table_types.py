# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for Table column-type deduction, explicit hints, and serialization."""

import pytest

from pytanga.viz import ColumnType, Table, TableColumnTypeChange, TableView, Visualizer


def _types(ctrl: Table) -> list[dict]:
    return ctrl.get_value()["column_types"]


def test_deduce_number_and_string_columns() -> None:
    t = Table(id="t", columns=["x", "y"], rows=[[1, "a"], [2, "b"]])
    assert _types(t) == [{"kind": "number"}, {"kind": "string"}]


def test_deduce_bool_column() -> None:
    t = Table(id="t", columns=["a", "b"], rows=[[True, 1], [False, 2]])
    assert _types(t) == [{"kind": "bool"}, {"kind": "number"}]


def test_deduce_mixed_is_string() -> None:
    t = Table(id="t", columns=["x"], rows=[[1], ["a"]])
    assert _types(t) == [{"kind": "string"}]


def test_deduce_bool_plus_number_is_string() -> None:
    t = Table(id="t", columns=["x"], rows=[[True], [1]])
    assert _types(t) == [{"kind": "string"}]


def test_deduce_empty_column_is_string() -> None:
    t = Table(id="t", columns=["x"], rows=[[""], [None]])
    assert _types(t) == [{"kind": "string"}]


def test_explicit_types_override_deduction() -> None:
    t = Table(
        id="t",
        columns=["a", "b", "c"],
        rows=[[1, 1, 1]],
        column_types=[None, ["x", "y"], "bool"],
    )
    assert _types(t) == [
        {"kind": "number"},
        {"kind": "enum", "values": ["x", "y"]},
        {"kind": "bool"},
    ]


def test_explicit_types_sticky_across_set_value() -> None:
    t = Table(id="t", columns=["a"], rows=[[1]], column_types=["number"])
    t.set_value({"columns": ["a"], "rows": [["hello"]]})
    # The explicit "number" hint survives a full data replace.
    assert _types(t) == [{"kind": "number"}]


def test_bool_cells_serialize_to_true_false() -> None:
    t = Table(id="t", columns=["a", "b"], rows=[[True, False]])
    assert t.get_value()["rows"] == [["true", "false"]]


def test_serialized_rows_are_strings() -> None:
    t = Table(id="t", columns=["a", "b"], rows=[[1, 2.5]])
    assert t.get_value()["rows"] == [["1", "2.5"]]


def test_add_column_with_type() -> None:
    view = TableView("tbl", columns=["a"], rows=[[1]])
    assert view.add_column("b", values=["x"], column_type=["x", "y"]) is True
    assert _types(view.control) == [{"kind": "number"}, {"kind": "enum", "values": ["x", "y"]}]


def test_delete_column_drops_its_type() -> None:
    t = Table(id="t", columns=["a", "b"], rows=[[1, "x"]])
    t.delete_column(0)
    assert _types(t) == [{"kind": "string"}]


def test_column_type_to_dict() -> None:
    assert ColumnType("number").to_dict() == {"kind": "number"}
    assert ColumnType("enum", ("a", "b")).to_dict() == {"kind": "enum", "values": ["a", "b"]}


def test_column_type_format_to_dict() -> None:
    assert ColumnType("number", format="{:.2f}m").to_dict() == {
        "kind": "number",
        "format": "{:.2f}m",
    }
    # format is omitted when absent
    assert ColumnType("number").to_dict() == {"kind": "number"}


def test_number_format_serializes() -> None:
    t = Table(
        id="t",
        columns=["x", "y"],
        rows=[[3.5, 42]],
        column_types=[{"kind": "number", "format": "{:.2f}m"}, "number"],
    )
    assert t.get_value()["rows"] == [["3.50m", "42"]]
    assert _types(t) == [{"kind": "number", "format": "{:.2f}m"}, {"kind": "number"}]


def test_set_column_format_mutates_and_persists(tmp_path) -> None:
    t = Table(id="t", columns=["x"], rows=[[3.5]], column_types=["number"])
    assert t.set_column_format(0, "{:.2f}m") is True
    assert t.get_value()["rows"] == [["3.50m"]]
    assert t.get_value()["column_types"] == [{"kind": "number", "format": "{:.2f}m"}]
    with pytest.raises(ValueError):
        t.set_column_format(0, "{")  # invalid template
    # non-number column -> False
    t2 = Table(id="t2", columns=["s"], rows=[["a"]], column_types=["string"])
    assert t2.set_column_format(0, "{:.2f}") is False
    # JSON round-trip keeps the format
    path = tmp_path / "table.json"
    t.to_json(path)
    t3 = Table(id="t3")
    t3.from_json(path)
    assert t3.get_value()["column_types"] == [{"kind": "number", "format": "{:.2f}m"}]


def test_set_cell_parses_formatted_number() -> None:
    t = Table(
        id="t",
        columns=["x"],
        rows=[[3.5]],
        column_types=[{"kind": "number", "format": "{:.2f}m"}],
    )
    assert t.set_cell(0, 0, "4.20m") is True
    assert t.rows == [[4.2]]
    assert t.get_value()["rows"] == [["4.20m"]]
    assert t.set_cell(0, 0, "4.2") is True
    assert t.rows == [[4.2]]
    assert t.set_cell(0, 0, "abc") is False


def test_convert_bool_to_number() -> None:
    t = Table(id="t", columns=["b"], rows=[[True], [False]], column_types=["bool"])
    assert t.convert_column(0, "number") is True
    assert t.rows == [[1], [0]]
    assert _types(t) == [{"kind": "number"}]


def test_convert_number_to_bool_only_0_1() -> None:
    t = Table(id="t", columns=["n"], rows=[[0], [1]], column_types=["number"])
    assert t.convert_column(0, "bool") is True
    assert t.rows == [[False], [True]]
    t2 = Table(id="t2", columns=["n"], rows=[[2]], column_types=["number"])
    assert t2.convert_column(0, "bool") is False
    assert t2.rows == [[2]]  # unchanged


def test_convert_to_string_always_succeeds() -> None:
    t = Table(id="t", columns=["n"], rows=[[1], [2]], column_types=["number"])
    assert t.convert_column(0, "string") is True
    assert t.rows == [["1"], ["2"]]
    assert _types(t) == [{"kind": "string"}]


def test_convert_to_enum_requires_less_than_20() -> None:
    t = Table(id="t", columns=["s"], rows=[["a"], ["b"], ["a"]], column_types=["string"])
    assert t.convert_column(0, "enum") is True
    assert _types(t)[0]["kind"] == "enum"
    t2 = Table(id="t2", columns=["s"], rows=[[str(i)] for i in range(20)], column_types=["string"])
    assert t2.convert_column(0, "enum") is False
    assert _types(t2) == [{"kind": "string"}]  # unchanged


def test_handle_event_column_type_change_push_on_success() -> None:
    t = Table(id="t", columns=["b"], rows=[[True], [False]], column_types=["bool"])
    d = t.handle_event("column_type_change", {"value": {"col": 0, "type": "number"}})
    assert d.event == "column_type_change"
    assert isinstance(d.value, TableColumnTypeChange)
    assert d.value.ok is True
    assert d.push is not None
    t2 = Table(id="t2", columns=["n"], rows=[[2]], column_types=["number"])
    d2 = t2.handle_event("column_type_change", {"value": {"col": 0, "type": "bool"}})
    assert d2.value.ok is False
    assert d2.push is None


def test_undo_restores_column_types() -> None:
    t = Table(id="t", columns=["a", "b"], rows=[[1, "x"]])
    t.delete_column(1)  # removes "b" (string) column
    assert t.columns == ["a"]
    t.undo()
    assert t.columns == ["a", "b"]
    assert _types(t) == [{"kind": "number"}, {"kind": "string"}]


# ── view state (column widths, row height, sort) ────────────


def test_default_view_state_omitted() -> None:
    t = Table(id="t", columns=["a"], rows=[[1]])
    assert "column_widths" not in t.get_value()
    assert "row_height" not in t.get_value()
    assert "sort" not in t.get_value()


def test_table_view_change_sets_view_state() -> None:
    t = Table(id="t", columns=["a"], rows=[[1]])
    d = t.handle_event(
        "table_view_change",
        {"value": {"column_widths": [0.5], "row_height": 30, "sort": {"column": 0, "order": "desc"}}},
    )
    assert d.event is None
    assert t.get_value()["column_widths"] == [0.5]
    assert t.get_value()["row_height"] == 30
    assert t.get_value()["sort"] == {"column": 0, "order": "desc"}


def test_table_view_change_partial_update_preserves_other_keys() -> None:
    t = Table(id="t", columns=["a"], rows=[[1]])
    t.handle_event("table_view_change", {"value": {"sort": {"column": 0, "order": "asc"}}})
    t.handle_event("table_view_change", {"value": {"row_height": 40}})
    assert t.get_value()["sort"] == {"column": 0, "order": "asc"}  # preserved
    assert t.get_value()["row_height"] == 40


def test_table_view_change_can_clear_sort() -> None:
    t = Table(id="t", columns=["a"], rows=[[1]])
    t.handle_event("table_view_change", {"value": {"sort": {"column": 0, "order": "asc"}}})
    t.handle_event("table_view_change", {"value": {"sort": None}})
    assert "sort" not in t.get_value()


@pytest.mark.anyio
async def test_dispatch_table_view_change() -> None:
    viz = Visualizer(add_default_axes=False, add_default_grid=False)
    viz.set_layout(TableView("tbl", columns=["x"], rows=[[1]]))
    await viz._dispatch_control_event(
        "control:table_view_change",
        {
            "control_id": "tbl",
            "value": {"sort": {"column": 0, "order": "asc"}, "row_height": 30},
        },
    )
    value = viz._resolve_control("tbl").get_value()
    assert value["sort"] == {"column": 0, "order": "asc"}
    assert value["row_height"] == 30


# ── persistence (JSON / CSV / auto-save) ─────────────────────


def test_to_from_dict_round_trip() -> None:
    t = Table(
        id="t",
        columns=["x", "status", "active"],
        rows=[[1, "on", True], [2, "off", False]],
        column_types=[None, ["on", "off"], "bool"],
    )
    t.column_widths = [0.5, 0.3, 0.2]
    t.row_height = 30
    t.sort = {"column": 0, "order": "desc"}

    t2 = Table(id="t2")
    t2.from_dict(t.to_dict())
    assert t2.columns == ["x", "status", "active"]
    assert t2.get_value()["rows"] == [["1", "on", "true"], ["2", "off", "false"]]
    assert _types(t2) == [
        {"kind": "number"},
        {"kind": "enum", "values": ["on", "off"]},
        {"kind": "bool"},
    ]
    assert t2.column_widths == [0.5, 0.3, 0.2]
    assert t2.row_height == 30
    assert t2.sort == {"column": 0, "order": "desc"}


def test_from_dict_rejects_wrong_id() -> None:
    with pytest.raises(ValueError):
        Table(id="t").from_dict({"id": "nope", "version": "1.0", "columns": [], "rows": []})


def test_from_dict_rejects_major_mismatch() -> None:
    with pytest.raises(ValueError):
        Table(id="t").from_dict(
            {"id": "pytanga-table", "version": "2.0", "columns": [], "rows": []}
        )


def test_from_dict_rejects_newer_minor() -> None:
    with pytest.raises(ValueError):
        Table(id="t").from_dict(
            {"id": "pytanga-table", "version": "1.1", "columns": [], "rows": []}
        )


def test_to_from_json_round_trip(tmp_path) -> None:
    t = Table(id="t", columns=["a"], rows=[[1]], column_types=["number"])
    path = tmp_path / "table.json"
    t.to_json(path)
    t2 = Table(id="t2")
    t2.from_json(path)
    assert t2.get_value() == t.get_value()


def test_to_from_csv_round_trip(tmp_path) -> None:
    t = Table(id="t", columns=["a", "b"], rows=[[1, True], [2, False]])
    path = tmp_path / "table.csv"
    t.to_csv(path)
    t2 = Table(id="t2")
    t2.from_csv(path)
    assert t2.columns == ["a", "b"]
    assert t2.get_value()["rows"] == [["1", "true"], ["2", "false"]]
    assert _types(t2) == [{"kind": "number"}, {"kind": "bool"}]


def test_auto_save_writes_on_mutation(tmp_path) -> None:
    import json

    path = tmp_path / "autosave.json"
    t = Table(id="t", columns=["a"], rows=[[1]], _json_path=str(path))
    t.set_cell(0, 0, 42)
    assert json.loads(path.read_text())["rows"] == [["42"]]


def test_auto_save_undo_rewrites(tmp_path) -> None:
    import json

    path = tmp_path / "autosave.json"
    t = Table(id="t", columns=["a"], rows=[[1]], _json_path=str(path))
    t.set_cell(0, 0, 42)
    t.undo()
    assert json.loads(path.read_text())["rows"] == [["1"]]


def test_table_view_json_path_autosave(tmp_path) -> None:
    path = tmp_path / "tv.json"
    view = TableView("tbl", columns=["a"], rows=[[1]], json_path=str(path))
    assert path.exists()  # created with the initial data
    view.set_cell(0, 0, 9)
    reloaded = TableView("tbl2", json_path=str(path))  # loads from the file
    assert reloaded.get_value()["rows"] == [["9"]]
