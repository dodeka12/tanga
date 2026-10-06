# Phase 4 — Update the two labeling apps

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-controls-and-interactions.md`).
> Example-only change; no architecture change.

## Goal

Both example apps restrict active/visible control points to the selected shape,
using the new bulk API.

## Files

- Edit: `py/examples/apps/image_labeling_app.py`
- Edit: `py/examples/apps/calibrated_labeling_app.py`

## Steps

- [x] **4.1 — `image_labeling_app.py`.**
  - In `_set_extra_handles`, replace the two
    `hasattr(...set_translate_handle_visible / set_rotate_handle_visible)` calls with
    `if hasattr(act, "set_handles_visible"): act.set_handles_visible(visible)`.
    Keep the `_select`/`_deselect` call sites unchanged.
- [x] **4.2 — `calibrated_labeling_app.py`.**
  - Apply the same replacement in its `_set_extra_handles` (identical shape);
    keep the `_add_shape` call that starts new shapes hidden.
- [x] **4.3 — Verify selection behavior.**
  - Run both apps and confirm the selected shape shows all handles and unselected
    shapes show none.

## Validation

`uv run pytest py/tests/viz/test_calibrated_labeling_example.py -q && uv run python -m py_compile py/examples/apps/image_labeling_app.py py/examples/apps/calibrated_labeling_app.py`

## Notes

- No `Keywords:` change is needed, so no example-docs regeneration.
