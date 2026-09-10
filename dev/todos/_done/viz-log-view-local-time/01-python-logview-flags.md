# Phase 1 — `LogView` flags + serialization

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Add the `show_date` / `show_utc_offset` flags to the backend `LogView` and
serialize them into the `log_view` node.

## Files

- Edit: `py/pytanga/viz/views.py`
- Edit: `py/tests/viz/test_log_view.py`

## Steps

- [x] **1.1 — Add the flags to `LogView.__init__`**
  - Add keyword-only `show_date: bool = False` and
    `show_utc_offset: bool = False` after `max_history` (before `**kwargs`).
  - Store `self.show_date` / `self.show_utc_offset` next to `self.max_history`.
  - Update the class docstring to describe the new display options.
- [x] **1.2 — Serialize the flags**
  - In `LogView._serialize`, add `result["show_date"] = self.show_date` and
    `result["show_utc_offset"] = self.show_utc_offset`.
- [x] **1.3 — Python tests**
  - Extend `test_serialize` to assert both flags default to `False`.
  - Add a test that `LogView(id="log0", show_date=True, show_utc_offset=True)`
    serializes both flags as `True`.

## Validation

`uv run pytest py/tests/viz/test_log_view.py -q`

## Notes

- `LogView` is a display view (not a `ControlView`); its `_serialize` is a
  plain override, matching the existing `id`/`max_history`/`lines` fields.