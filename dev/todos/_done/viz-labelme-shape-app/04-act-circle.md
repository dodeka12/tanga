# Phase 4 — `ActCircle` (+ `ActEllipse.min_radius`)

## Goal

Add a dedicated `ActCircle` composite — a `Circle` body (center + radius, normal
`+z`), a center translate handle and a single radius handle — plus a `min_radius`
clamp (also replacing `ActEllipse`'s hard-coded `0.05`).

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-controls-and-interactions.md`
> and `viz-architecture.md`).  This reuses `_ActWithHandles` and the existing
> `Circle` entity (`circle.py`, `CircleStyle`, `circle.js`); no architecture change.

## Files

- Edit: `py/pytanga/viz/_active.py` (`ActCircle`, `ActEllipse`; import `Circle`)
- Edit: `py/pytanga/viz/__init__.py` (export `ActCircle`)
- New: `py/tests/viz/test_act_circle.py`

## Steps

- [x] **4.1 — `ActEllipse.min_radius`**
  - Add `min_radius: float | None = None`; use it in `_resize_radius` instead of
    the literal `0.05` (default clamp stays `0.05` when `None`).
- [x] **4.2 — `ActCircle` composite**
  - `class ActCircle(_ActWithHandles)` with `center`, `radius`, `min_radius`,
    `show_translate_handle`, `handle_style`, `translate_handle_style`,
    `act_style`, `on_radius_drag`, `on_translate`, `on_change`, `on_click`.
  - `entity`/`circle` property returns `Circle(center, radius,
    normal=Direction(0,0,1))`; body `on_click` mirrors `ActEllipse`.
- [x] **4.3 — Handles**
  - Spawn a center translate handle (`translate_handle_style`) and one radius
    handle (`handle_style`) at `center + (radius, 0)`; no rotate handle.
- [x] **4.4 — Radius resize**
  - `_dispatch_radius_drag`/`_resize_radius(pos)`: `radius = clamp(distance(center,
    pos), min_radius, …)`; `_translate_by(delta)` moves the center; both call
    `_commit()` (update body + refresh handles + flush + `on_change`).
- [x] **4.5 — `create_from_points(center, rim)`**
  - Classmethod building a circle from center + rim point (radius = distance),
    forwarding `min_radius`/handle args.
- [x] **4.6 — Export + tests**
  - Export `ActCircle` from `pytanga.viz`; test defaults, `entity` is a `Circle`
    with the correct radius, radius resize clamp, translate, and
    `create_from_points`.

## Validation

```
uv run pytest py/tests/viz -q
```

## Notes

- labelme `circle` is center + one rim point; `ActCircle`'s single radius handle
  matches that exactly (see Phase 8).  The body renders via the existing
  `circle.js` with `CircleStyle` (a thick screen-space line).

