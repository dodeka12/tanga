# Phase 3 — Persistence (JSON, CSV, auto-save)

## Goal

Save/load the full table (data + `column_types` + view state) as versioned JSON,
export/import CSV, and support auto-save to a JSON path.

## Files

- Edit: `py/pytanga/viz/_controls.py`
- Edit: `py/pytanga/viz/views.py`
- Edit: `py/tests/viz/test_table.py`

## Steps

- [x] **3.1 — format constants + dict round-trip (`_controls.py`)**
  - Add `TABLE_FORMAT_ID = "pytanga-table"`, `TABLE_FORMAT_VERSION = "1.0"`.
  - `Table.to_dict()` → `{"id", "version", "columns", "rows", "column_types",
    "column_widths", "row_height", "sort"}` (reusing the wire serialization).
  - `Table.from_dict(d)` → validate `id` and `version` (wrong id → `ValueError`;
    major mismatch → `ValueError`; `minor > current` → `ValueError`; `minor <=
    current` accepted), then load data + types + view state.

- [x] **3.2 — JSON file I/O (`_controls.py`)**
  - `to_json(path)` writes `to_dict()` via `json.dump` (indent for readability);
    `from_json(path)` reads and calls `from_dict`.

- [x] **3.3 — CSV (`_controls.py`)**
  - `to_csv(path)` writes header + rows using the `csv` module (cells via
    `_cell_to_str`). `from_csv(path)` reads header + rows and infers types from
    string content (all `"true"`/`"false"` → bool; all parse-as-number → number;
    else string) — enum is not representable and becomes `string`.

- [x] **3.4 — auto-save (`_controls.py`)**
  - Add internal `_json_path: str | None = field(default=None, repr=False,
    compare=False)` and `_save()` (atomic write-to-temp + `os.replace`).
  - Call `_save()` at the end of every mutating method (`set_value`, `set_cell`,
    `insert_row`, `insert_column`, `delete_rows`, `delete_column`, `undo`, `redo`)
    when `_json_path` is set.

- [x] **3.5 — `TableView` surface (`views.py`)**
  - Add `json_path: str | None = None` param; on construction load the file if it
    exists (file wins over args), else init from args and write it.
  - Add `save(path=None)`, `load(path=None)`, `to_csv(path)`, `from_csv(path)`
    delegating to the control (load/from_csv also push the grid).

- [x] **3.6 — tests**
  - `to_dict`/`from_dict` round-trip (types + view state); version validation
    (wrong id, major mismatch, newer minor); `to_json`/`from_json` via `tmp_path`;
    `to_csv`/`from_csv` round-trip; auto-save writes on `set_cell` and undo.

## Validation

`uv run pytest py/tests/viz/ -q`

## Notes

- File I/O is synchronous (table payloads are small); note this in the docstring
  — async write is a possible later enhancement.
