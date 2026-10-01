# Phase 0 — Revert the prior `Plane` hit-surface wiring

## Goal

Revert the broken drag-to-draw wiring added in `viz-plane-drag-surface` phase 3
(a transparent `Plane` hit surface + `ActImagePlane` + toolbar in the shared
scene), restoring `calibrated_labeling_app.py` to the clean two-pane +
label-loading baseline before the surface work starts.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Files

- Edit: `py/examples/apps/calibrated_labeling_app.py`
- Edit: `py/tests/viz/test_calibrated_labeling_example.py`
- Regenerate: `docs/py/examples/…` (via `generate-example-docs.py`)

## Steps

- [x] **0.1 — Remove the `Plane` hit surface + drag-to-draw**
  - Delete `_CalibratedLabeler`, `_style_for`, and the `Plane`/`ActImagePlane`/
    toolbar/`DragPreview` wiring from `calibrated_labeling_app.py`.
- [x] **0.2 — Restore the two-pane baseline**
  - Back to `SplitView("horizontal", [left, right])` with no toolbar/surface; keep
    the `CalibratedPlaneMapper` + `LabelMeStore` label loading and the frustum.
- [x] **0.3 — Tests + docs**
  - Keep the data-validation tests green (drop the phase-3-only import test if it
    no longer applies); regenerate example docs.

## Validation

```
uv run pytest py/tests/viz/test_calibrated_labeling_example.py -q && uv run ruff check py/examples/apps/calibrated_labeling_app.py && uv run python tools/generate-example-docs.py --check
```

## Notes

- This only reverts the *wiring* (the `Plane` hit surface). The `CoordinateMapper`
  (`plane()`) and the mapper-aware `ActImagePlane` from phases 1–2 of the prior
  plan are kept and reused by the new surface.
