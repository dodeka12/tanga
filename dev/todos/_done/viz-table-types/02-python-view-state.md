# Phase 2 — View state (widths, row height, sort)

## Goal

Let the backend hold, serialize, and receive the table's presentation state:
relative column widths, row height, and sort column/order.

## Files

- Edit: `py/pytanga/viz/_controls.py`
- Edit: `py/pytanga/viz/server.py`
- Edit: `py/tests/viz/test_table.py`

## Steps

- [x] **2.1 — `Table` view-state fields (`_controls.py`)**
  - Add `column_widths: list[float] | None = None`, `row_height: int = 24`,
    `sort: dict[str, Any] | None = None` (internal, `repr=False, compare=False`
    where appropriate).
  - Serialize them in `_fields()`/`get_value()`: `column_widths` (relative
    weights, omitted when `None`/empty), `row_height`, `sort` (`{column, order}`
    or `null`). These are presentation state — excluded from undo history.

- [x] **2.2 — `table_view_change` handling (`_controls.py`)**
  - In `parse_table_event`/`Table.handle_event`, add a `table_view_change` branch
    that merges `{column_widths?, row_height?, sort?}` into the model and calls
    `_save()` (auto-save hook from Phase 3, if configured) — no `Dispatch`
    payload, no handler, no push back (the frontend is the origin).

- [x] **2.3 — server routing (`server.py`)**
  - Add `"table_view_change": "control:table_view_change"` to `_EVENT_MSG_MAP` and
    `"control:table_view_change"` to the inbound control-message tuple, matching
    the existing `control:cell_change` pattern.

- [x] **2.4 — tests**
  - `control:table_view_change` mutates `column_widths`/`row_height`/`sort` and
    they appear in `get_value()`; unchanged keys are preserved on a partial update;
    no undo history is recorded.

## Validation

`uv run pytest py/tests/viz/ -q`

## Notes

- The frontend reporting side (sending `control:table_view_change`) lands in
  Phase 5; this phase only makes the backend accept + serialize it.
