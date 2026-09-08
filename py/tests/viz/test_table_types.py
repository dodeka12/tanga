# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for Table column-type deduction, explicit hints, and serialization."""

import asyncio

import pytest

from pytanga.viz import (
    ColumnType,
    ControlEvent,
    Table,
    TableColumnTypeChange,
    TableEnumOptionsRequest,
    TableView,
    Visualizer,
)
from pytanga.viz._controls import _resolve_column_type


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
    assert _types(view.control) == [
        {"kind": "number"},
        {"kind": "enum", "values": ["x", "y"]},
    ]


def test_delete_column_drops_its_type() -> None:
    t = Table(id="t", columns=["a", "b"], rows=[[1, "x"]])
    t.delete_column(0)
    assert _types(t) == [{"kind": "string"}]


def test_column_type_to_dict() -> None:
    assert ColumnType("number").to_dict() == {"kind": "number"}
    assert ColumnType("enum", ("a", "b")).to_dict() == {
        "kind": "enum",
        "values": ["a", "b"],
    }


def test_column_type_format_to_dict() -> None:
    assert ColumnType("number", format="{:.2f}m").to_dict() == {
        "kind": "number",
        "format": "{:.2f}m",
    }
    # format is omitted when absent
    assert ColumnType("number").to_dict() == {"kind": "number"}


def test_column_type_column_to_dict() -> None:
    assert ColumnType("column", source=1).to_dict() == {"kind": "column", "source": 1}


def test_column_type_custom_to_dict() -> None:
    assert ColumnType("custom").to_dict() == {"kind": "custom"}


def test_resolve_column_type_column_and_custom() -> None:
    assert _resolve_column_type({"kind": "column", "source": 2}, []) == ColumnType(
        "column", source=2
    )
    assert _resolve_column_type({"kind": "custom"}, []) == ColumnType("custom")
    assert _resolve_column_type("custom", []) == ColumnType("custom")


def test_table_serializes_column_and_custom_types() -> None:
    t = Table(
        id="t",
        columns=["names", "seat", "notes"],
        rows=[["alice", "bob", "x"], ["bob", "alice", "y"]],
        column_types=[None, {"kind": "column", "source": 0}, "custom"],
    )
    assert _types(t) == [
        {"kind": "string"},
        {"kind": "column", "source": 0},
        {"kind": "custom"},
    ]


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
    t = Table(
        id="t", columns=["s"], rows=[["a"], ["b"], ["a"]], column_types=["string"]
    )
    assert t.convert_column(0, "enum") is True
    assert _types(t)[0]["kind"] == "enum"
    t2 = Table(
        id="t2",
        columns=["s"],
        rows=[[str(i)] for i in range(20)],
        column_types=["string"],
    )
    assert t2.convert_column(0, "enum") is False
    assert _types(t2) == [{"kind": "string"}]  # unchanged


def test_convert_to_column_sets_source_and_keeps_cells() -> None:
    t = Table(
        id="t",
        columns=["names", "seat"],
        rows=[["alice", "bob"], ["bob", "alice"]],
        column_types=[None, "string"],
    )
    assert t.convert_column(1, "column", source=0) is True
    assert _types(t) == [{"kind": "string"}, {"kind": "column", "source": 0}]
    assert t.rows == [["alice", "bob"], ["bob", "alice"]]  # cells untouched


def test_convert_to_column_rejects_invalid_source() -> None:
    t = Table(
        id="t",
        columns=["a", "b"],
        rows=[["x", "y"]],
        column_types=["string", "string"],
    )
    assert t.convert_column(0, "column") is False  # missing source
    assert t.convert_column(0, "column", source=5) is False  # out of range
    assert t.convert_column(0, "column", source=0) is False  # self
    assert _types(t) == [{"kind": "string"}, {"kind": "string"}]


def test_convert_to_custom_rejected() -> None:
    t = Table(id="t", columns=["a"], rows=[["x"]], column_types=["string"])
    assert t.convert_column(0, "custom") is False
    assert _types(t) == [{"kind": "string"}]


def test_custom_column_cannot_be_converted() -> None:
    t = Table(id="t", columns=["a"], rows=[["x"]], column_types=["custom"])
    assert t.convert_column(0, "number") is False
    assert t.convert_column(0, "string") is False
    assert _types(t) == [{"kind": "custom"}]


def test_convert_column_repurposes_source() -> None:
    t = Table(
        id="t",
        columns=["a", "b", "c"],
        rows=[["x", "y", "z"]],
        column_types=["string", {"kind": "column", "source": 0}, "string"],
    )
    assert t.convert_column(1, "column", source=2) is True
    assert _types(t)[1] == {"kind": "column", "source": 2}


def test_handle_event_column_type_change_carries_source() -> None:
    t = Table(
        id="t",
        columns=["names", "seat"],
        rows=[["alice", "bob"], ["bob", "alice"]],
        column_types=[None, "string"],
    )
    d = t.handle_event(
        "column_type_change",
        {"value": {"col": 1, "type": "column", "source": 0}},
    )
    assert isinstance(d.value, TableColumnTypeChange)
    assert d.value.source == 0
    assert d.value.ok is True
    assert d.push["column_types"] == [
        {"kind": "string"},
        {"kind": "column", "source": 0},
    ]


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


def test_enum_options_request_fields() -> None:
    req = TableEnumOptionsRequest(col=0, row=3, current="alice")
    assert req.col == 0
    assert req.row == 3
    assert req.current == "alice"


def test_enum_options_values_invokes_handler_and_stringifies() -> None:
    async def handler(request: TableEnumOptionsRequest, event: ControlEvent) -> list:
        assert request.col == 0
        assert request.row == 1
        assert request.current == "x"
        return ["a", "b", 3]

    t = Table(id="t", columns=["a"], rows=[["x"]], on_enum_options=handler)
    result = asyncio.run(
        t.enum_options_values(TableEnumOptionsRequest(0, 1, "x"), ControlEvent())
    )
    assert result == ["a", "b", "3"]


def test_enum_options_values_empty_when_unset() -> None:
    t = Table(id="t", columns=["a"], rows=[["x"]])
    assert (
        asyncio.run(
            t.enum_options_values(TableEnumOptionsRequest(0, 0, ""), ControlEvent())
        )
        == []
    )


def test_enum_options_not_serialized() -> None:
    t = Table(id="t", columns=["a"], rows=[["x"]], on_enum_options=lambda: None)
    assert "on_enum_options" not in t.serialize()


def test_on_enum_options_registered_as_handler() -> None:
    from pytanga.viz._controls import ControlHandlerRegistry

    async def handler(request, event) -> None:
        return None

    registry = ControlHandlerRegistry()
    ctrl = Table(id="tbl", columns=["a"], rows=[["x"]], on_enum_options=handler)
    ctrl.register_handlers(registry)
    assert registry.get("tbl", "enum_options") is handler


def test_table_view_forwards_enum_options() -> None:
    from pytanga.viz.views import control_to_view

    def handler(request, event) -> None:
        return None

    view = TableView("tv", columns=["a"], rows=[["x"]], on_enum_options=handler)
    assert view.control.on_enum_options is handler
    # control_to_view reuses the same control object.
    assert control_to_view(view.control).control.on_enum_options is handler


class _FakeLayoutTransport:
    def __init__(self) -> None:
        self.sent: list[tuple[str, dict]] = []

    def send(self, message: dict) -> None:
        return None

    async def send_to_browser(self, browser_id: str, message: dict) -> None:
        self.sent.append((browser_id, message))

    def get(self, id: str, event: str = "change"):
        return None

    def unregister(self, id: str, event: str | None = None) -> None:
        return None


def test_dispatch_enum_options_replies_to_browser(monkeypatch) -> None:
    from pytanga.viz._layout import LayoutHostImpl

    async def handler(request: TableEnumOptionsRequest, event: ControlEvent) -> list:
        assert request.col == 0
        assert request.row == 1
        assert request.current == "x"
        return ["a", "b"]

    ctrl = Table(id="tbl", columns=["a"], rows=[["x"]], on_enum_options=handler)
    transport = _FakeLayoutTransport()
    layout = LayoutHostImpl(
        None, scene_factory=lambda name: None, transport=transport, client_log=None
    )
    monkeypatch.setattr(layout, "resolve_control", lambda cid: ctrl)

    asyncio.run(
        layout.dispatch_control_event(
            "control:enum_options",
            {
                "control_id": "tbl",
                "browser_id": "b1",
                "value": {"col": 0, "row": 1, "current": "x", "request_id": 7},
            },
        )
    )

    assert transport.sent == [
        (
            "b1",
            {
                "type": "enum_options",
                "id": "tbl",
                "request_id": 7,
                "values": ["a", "b"],
            },
        )
    ]


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
        {
            "value": {
                "column_widths": [0.5],
                "row_height": 30,
                "sort": {"column": 0, "order": "desc"},
            }
        },
    )
    assert d.event is None
    assert t.get_value()["column_widths"] == [0.5]
    assert t.get_value()["row_height"] == 30
    assert t.get_value()["sort"] == {"column": 0, "order": "desc"}


def test_table_view_change_partial_update_preserves_other_keys() -> None:
    t = Table(id="t", columns=["a"], rows=[[1]])
    t.handle_event(
        "table_view_change", {"value": {"sort": {"column": 0, "order": "asc"}}}
    )
    t.handle_event("table_view_change", {"value": {"row_height": 40}})
    assert t.get_value()["sort"] == {"column": 0, "order": "asc"}  # preserved
    assert t.get_value()["row_height"] == 40


def test_table_view_change_can_clear_sort() -> None:
    t = Table(id="t", columns=["a"], rows=[[1]])
    t.handle_event(
        "table_view_change", {"value": {"sort": {"column": 0, "order": "asc"}}}
    )
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
        Table(id="t").from_dict(
            {"id": "nope", "version": "1.0", "columns": [], "rows": []}
        )


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


def test_to_from_csv_european_round_trip(tmp_path) -> None:
    t = Table(id="t", columns=["x", "active"], rows=[[1.5, True], [2.25, False]])
    path = tmp_path / "european.csv"
    t.to_csv(path, delimiter=";", decimal_separator=",")
    t2 = Table(id="t2")
    t2.from_csv(path, delimiter=";", decimal_separator=",")
    assert t2.columns == ["x", "active"]
    assert t2.get_value()["rows"] == [["1.5", "true"], ["2.25", "false"]]
    assert _types(t2) == [{"kind": "number"}, {"kind": "bool"}]


def test_to_csv_semicolon_writes_expected_bytes(tmp_path) -> None:
    t = Table(id="t", columns=["x", "active"], rows=[[1.5, True]])
    path = tmp_path / "t.csv"
    t.to_csv(path, delimiter=";", decimal_separator=",")
    assert path.read_bytes() == b"x;active\r\n1,5;true\r\n"


def test_from_csv_auto_detects_semicolon_and_comma_decimal(tmp_path) -> None:
    path = tmp_path / "german.csv"
    path.write_text("preis;menge\n1,5;2\n3,25;4\n", encoding="utf-8")
    t = Table(id="t")
    t.from_csv(path)
    assert t.columns == ["preis", "menge"]
    assert t.get_value()["rows"] == [["1.5", "2"], ["3.25", "4"]]
    assert _types(t) == [{"kind": "number"}, {"kind": "number"}]


def test_from_csv_auto_detects_comma_and_dot_decimal(tmp_path) -> None:
    path = tmp_path / "us.csv"
    path.write_text("x,y\n1.5,2\n3.25,4\n", encoding="utf-8")
    t = Table(id="t")
    t.from_csv(path)
    assert t.columns == ["x", "y"]
    assert t.get_value()["rows"] == [["1.5", "2"], ["3.25", "4"]]
    assert _types(t) == [{"kind": "number"}, {"kind": "number"}]


def test_from_csv_explicit_delimiter_overrides_detection(tmp_path) -> None:
    path = tmp_path / "t.csv"
    path.write_text("x;y\n1;2\n", encoding="utf-8")
    t = Table(id="t")
    # Forcing a comma delimiter makes each line a single column, proving the
    # explicit value wins over the `;` that auto-detection would have chosen.
    t.from_csv(path, delimiter=",")
    assert t.columns == ["x;y"]
    assert t.get_value()["rows"] == [["1;2"]]


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
