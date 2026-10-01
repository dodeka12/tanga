# Phase 3 — Explicit `value` on dialog accept

## Goal

Let the `accept` event carry an explicit full path, so the typed filename
reaches `on_accept` without relying solely on `ctrl.get_value()`.

## Files

- Edit: `py/pytanga/viz/visualizer.py` (`_on_dialog_accept`)
- Edit: `py/pytanga/viz/_layout.py` (`OverlayContainer._on_dialog_accept`)
- Edit: `py/tests/viz/test_file_chooser.py`

## Steps

- [x] **3.1 — `visualizer._on_dialog_accept`**
  - Pass `payload.get("value")` through to
    `self._layout.overlay._on_dialog_accept(target, event, value=...)`.
- [x] **3.2 — `_on_dialog_accept(target, event, value=None)`**
  - Accept an optional `value`; when it is not `None`, use it instead of
    resolving `ctrl.get_value()` from `dialog.control_id` (keep the fallback).
- [x] **3.3 — Test**
  - Add a test that dispatching `accept` with `{"id": did, "value": "/typed.json"}`
    reaches `on_accept` with `"/typed.json"`, and that omitting `value` still
    falls back to the control value (existing behavior).

## Validation

```
uv run pytest py/tests/viz/test_file_chooser.py -q
```

## Notes

- Generic (non-file-chooser) dialogs have `control_id=None`, so the fallback
  path already yields `None`; the explicit-value branch does not change them.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.
