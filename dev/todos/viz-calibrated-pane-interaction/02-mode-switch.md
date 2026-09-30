# Phase 2 — Complete the drawing mode-switch

## Goal

Make the calibrated labeler's `set_mode` mirror the `ImageLabeler`: arm/disarm the
surface and set the cursor so navigation yields and the cursor signals drawing.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Files

- Edit: `py/examples/apps/calibrated_labeling_app.py`

## Steps

- [ ] **2.1 — `set_mode` arms the surface + cursor**
  - `set_mode(mode)`: `self._drag_binding.enabled = mode is not None`,
    `self.surface.set_enabled(mode is not None)`, and set the cursor
    (`"crosshair"` when armed, `None` otherwise) via the scene handle.
- [ ] **2.2 — Verify navigation yields**
  - Confirm arming a tool disables the viewport pan (phase 1 predicate) and the
    cursor changes; disarm restores both.

## Validation

```
uv run pytest py/tests/viz/test_calibrated_labeling_example.py -q && uv run ruff check py/examples/apps/calibrated_labeling_app.py
```

Manual smoke: arm/disarm tools — cursor toggles and panning stops while armed.

## Notes

- The cursor is the **scene** cursor (per the README decision), so it shows on
  both panes; a per-pane cursor is deferred.
