# Table column types, editors & persistence — Overview

**Created:** 2026-09-06 | **Status:** Done | **Branch:** `fix/examples`

## Goal

Give `TableView` / `Table` a real data model and persistence story:

- Per-column **types** (`number`, `string`, `bool`, `enum(values)`), deduced from
  data or set explicitly, and rendered/enforced in the frontend.
- **Type-driven editors**: text input (`number`/`string`, with number
  validation), `<select>` (`enum`), always-visible checkbox (`bool`).
- **Type-driven alignment**: `number` → right, `string`/`enum` → left,
  `bool` → center.
- **Fit-to-content** column sizing + **icon zoom buttons** (`arrow_left` /
  `arrow_right`, `arrow_drop_up` / `arrow_drop_down`, `fit_screen`).
- **JSON** save/load (with `id` + `version`), **CSV** export/import, and an
  **auto-save** mode (`json_path=…`) that persists on every change.
- **View state** (relative column widths, row height, sort column + order)
  round-tripped through the wire and saved to JSON.

## Architecture (short)

- `Table` (`py/pytanga/viz/_controls.py`) is the single source of truth: data
  (`columns`/`rows`), `column_types`, view state (`column_widths`, `row_height`,
  `sort`), and persistence (`to_json`/`from_json`/`to_csv`/`from_csv`) + auto-save.
- `TableView` (`py/pytanga/viz/views.py`) exposes the public API and delegates to
  the wrapped control.
- `createTable` moves into `py/pytanga/viz/templates/controls/table.js` (see
  Phase 4 step 4.0) so the table DOM factory doesn't bloat `controls-panel.js`;
  it renders/edits per column type and reports view-state changes back via a new
  `control:table_view_change` event.
- Wire payload and JSON file share one serialization shape; the JSON file adds
  `id` + `version`.

## Contract (fixed)

Wire payload — `Table.get_value()` and `Table._fields()`:

```json
{
  "columns": ["x", "status", "active", "note"],
  "rows": [["1", "on", "true", "hi"], ["2", "off", "false", "there"]],
  "column_types": [
    {"kind": "number"},
    {"kind": "enum", "values": ["on", "off"]},
    {"kind": "bool"},
    {"kind": "string"}
  ],
  "column_widths": [1.0, 0.6, 0.5, 1.2],
  "row_height": 28,
  "sort": {"column": 0, "order": "asc"}
}
```

- `rows` are **always strings**; bool cells serialize to `"true"`/`"false"`.
- `column_types[i]` is `{"kind": "number"|"string"|"bool"|"enum", "values": [...]}`
  (`values` only for `enum`). Omitted/empty means "deduce from data".
- `column_widths` are **relative weights** (floats `> 0`, ~sum 1); omitted → equal.
- `row_height` is px (int); omitted → `24`.
- `sort` is `{"column": int, "order": "asc"|"desc"}` or `null`.

JSON file (v1.0) = the wire payload plus a header:

```json
{ "id": "pytanga-table", "version": "1.0", "...": "…" }
```

- `TABLE_FORMAT_ID = "pytanga-table"`, `TABLE_FORMAT_VERSION = "1.0"`.
- Load rejects a wrong `id` or a different **major**; accepts `minor <= current`
  (ignoring unknown fields); errors on `minor > current`. Non-breaking format
  changes bump minor (1.1), breaking changes bump major (2.0) — documented
  convention, not enforced programmatically beyond the major/minor check.

View-state event (frontend → backend): `control:table_view_change` with payload
`{column_widths?, row_height?, sort?}` (partial; backend merges and persists —
no undo history, no push back).

## Decisions (confirmed)

- **Deduction** (only when a column has no explicit type, from Python types at
  ingest time; cell edits are strings and never re-derive a type):
  all-`bool` → `bool`; else all-numeric (bool excluded) → `number`; else
  `string` (so mixed string/number → string). Deduction never yields `enum`.
- **Explicit types** via `column_types=[None | "number"|"float"|"int" |
  "string"|"text" | "bool"|"boolean" | ["a","b",…]]`; `None` deduces; explicit
  types are sticky across `set_value` and add/delete column/row.
- **Bool** = always-visible checkbox; single click toggles and commits
  `"true"`/`"false"`.
- **Alignment** derived from `kind` (`number`→right, `string`/`enum`→left,
  `bool`→center); no separate alignment field.
- **CSV** = data only (header + rows, `"true"`/`"false"` for bool); import
  infers `number`/`bool` from string content, `enum` degrades to `string`.
- **Auto-save**: `TableView(json_path=…)`; the file is authoritative over the
  `columns`/`rows`/`column_types` args when it exists; otherwise init from args
  and write the file; every mutation re-writes atomically.
- **Zoom** (`column_scale`) is **not** persisted (resets to 1.0 on load).

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-python-column-types.md](./01-python-column-types.md) | `ColumnType` + deduction + `column_types` serialization |
| 2 | [02-python-view-state.md](./02-python-view-state.md) | view state + `table_view_change` event |
| 3 | [03-python-persistence.md](./03-python-persistence.md) | JSON (id/version) + CSV + auto-save |
| 4 | [04-frontend-types-editors.md](./04-frontend-types-editors.md) | per-type editors + alignment + apply state |
| 5 | [05-frontend-zoom-fit-report.md](./05-frontend-zoom-fit-report.md) | zoom/fit icons + report view state |
| 6 | [06-docs-changelog.md](./06-docs-changelog.md) | docs + changelog + example |

## Testing as you go

- `uv run pytest py/tests/viz/ -q`
- `node --test 'dev/src/js-tests/*.test.mjs'`
- `uv run mkdocs build --strict`
- browser smoke via a temporary Playwright probe (the `dev/src/diagnose_*.mjs`
  pattern; delete after use)

## Non-goals

- Numeric parsing/formatting of edited cells (deferred — the "future formatting"
  hook the backend leaves open).
- Persisting the column zoom scale (`column_scale`).
- Multi-client live sync of view state (persistence only).
- Per-cell alignment (alignment is type-derived, per column).
