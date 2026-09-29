# Phase 2 — Refactor `ImageCanvas` onto the surface

## Goal

Make `ImageCanvas` use an `InteractionSurface` (flat `PlanarMapper`, `z = 0`) for
its drag/click, so the image-labeling app exercises the same surface path as the
calibrated case.  The `ImageView` stays as the visual only.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Files

- Edit: `py/pytanga/viz/_image_view.py`
- Edit: `py/pytanga/viz/_active.py` (only to slim `ActImagePlane`, if needed)
- Edit: `py/examples/apps/image_labeling_app.py` (only if its API changes)

## Steps

- [ ] **2.1 — Surface-backed drag in `ImageCanvas`**
  - Build an `InteractionSurface(PlanarMapper(), on_drag_start=…, on_drag=…,
    on_drag_end=…, on_click=…)` and route the existing `ImageCanvas` drag/click
    callbacks through it, instead of the `ActImagePlane` entity.
- [ ] **2.2 — Keep the `ImageView` visual**
  - `ImageView` remains the rendered image; it is no longer the hit surface.
- [ ] **2.3 — Backward compatibility**
  - Preserve the public `ImageCanvas(...)` constructor signature and behavior;
    existing callers (image-labeling app, tests) must not change.
- [ ] **2.4 — Tests**
  - Full `py/tests/viz` still passes; manual smoke: `uv run python
    py/examples/apps/image_labeling_app.py` still pan/zooms/draws.

## Validation

```
uv run pytest py/tests/viz -q && uv run ruff check . && uv run ty check
```

## Notes

- This is the riskiest refactor (touches the flat path); keep `ActImagePlane`
  for backward-compat if removing it would ripple, and note the deprecation.
