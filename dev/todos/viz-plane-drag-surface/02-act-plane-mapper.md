# Phase 2 — Generalize `ActImagePlane`

## Goal

Make `ActImagePlane` mapper-aware so its drag anchor and drag mode come from the
mapper's plane, and decouple its rendered entity so a non-image hit plane works.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Files

- Edit: `py/pytanga/viz/_active.py`
- Edit: `py/pytanga/viz/_image_view.py` (only if the constructor signature moves)
- Edit: `py/tests/viz/test_labelme.py` (or a new `test_act_plane.py`)

## Steps

- [ ] **2.1 — `mapper` + `entity` parameters**
  - `ActImagePlane(image_view: ImageView | None = None, *, mapper=None,
    entity=None, ...)`; `mapper` defaults to `PlanarMapper()`; `entity` defaults
    to `image_view`.
- [ ] **2.2 — Generic `drag_anchor`**
  - Replace the `z = 0` intersection with a ray↔`mapper.plane()` intersection:
    `t = (point − ray_origin)·n / (ray_dir·n)`, then `ray_origin + t·ray_dir`.
- [ ] **2.3 — `interaction_config` uses `VIEW_PLANE`**
  - Swap both `DragMode.XY_PLANE` literals for `DragMode.VIEW_PLANE`.
- [ ] **2.4 — Entity decoupling**
  - The `entity` property returns `image_view` (flat) or the provided hit-plane
    entity (calibrated). `ImageCanvas` keeps passing the `ImageView`.
- [ ] **2.5 — Tests**
  - Flat regression: existing `ImageCanvas`/`ImageLabeler` drag tests still pass.
  - Unit: `drag_anchor` for a `CalibratedPlaneMapper` returns the plane point on
    the optical axis at `depth` (mirror the mapper round-trip tests).

## Validation

```
uv run pytest py/tests/viz -q && uv run ruff check . && uv run ty check
```

## Notes

- Keep `click_anchor` returning `None` (the raw frontend hit) for now; only drag
  needs the plane. If calibrated CLICK anchoring turns out to be wrong, revisit
  in phase 3 rather than expanding this phase.
