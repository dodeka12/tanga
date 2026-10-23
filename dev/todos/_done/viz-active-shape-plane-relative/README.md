# Active-shape plane-relative geometry & view-plane editing — Overview

**Created:** 2026-10-07 | **Status:** Done | **Branch:** `fix/act-plane-relative`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-controls-and-interactions.md`
> and `viz-architecture.md`) for the subsystem(s) this work touches, so the new
> code aligns with the documented architecture.  If this work introduces or
> changes architecture, update the developer docs.

## Goal

Make every `Act*` active shape lie on — and be edited in — its plane (the
view/depth plane of a calibrated `CalibratedSurface`, or the XY plane in flat
2D scenes) instead of silently assuming the world-XY plane.  Resolves
`_input/pytanga-act-ellipse-world-xy-plane-only.md` for **all** shapes, not just
`ActEllipse`.

## Background / root cause

Every composite `Act*` in `py/pytanga/viz/_active.py` hardcodes the world-XY
plane in two independent ways:

1. **Geometry** — `_dir_u`/`_dir_v` fix `z = 0`; `entity`/`_build_*` never sets
   the entity's `normal`, so `Ellipse`/`Rectangle2D`/`Circle` silently flatten
   to `normal = +z`; resize/rotate/translate math drops or ignores `z`.  A
   tilted-plane shape is reconstructed in the XY plane.
2. **Interaction** — `_spawn_handles()` builds every child `ActPoint` with
   `drag_mode=DragMode.XY_PLANE`, so dragging moves handles in world-XY, not in
   the surface/view plane (which the enclosing `InteractionSurface` already
   resolves via `DragMode.VIEW_PLANE` + `mapper.plane()`).

The backing entities already support arbitrary planes (`Ellipse.normal/dir_u/
dir_v`, `Rectangle2D.normal`, `Circle.normal`); the `Act*` wrappers just don't
expose or honor them.  The existing `TestPlaneZ` suites already encode the
intended invariant — "handles stay on the body's plane" — but only test the
flat `z = const` case.

## Architecture (short)

- **Python only** (`py/pytanga/viz/_active.py`).  No new interaction model, no
  new `DragMode`, no wire/schema change: we reuse the existing
  `DragMode.VIEW_PLANE` (already used by `ActPoint` and `InteractionSurface`) and
  add an optional `normal` constructor parameter to the three shapes whose
  entities carry a `normal`.
- A single private helper `_plane_basis(normal) -> (u0, v0)` derives an
  orthonormal in-plane basis; `ActEllipse`/`ActRectangle2D` express their
  internal `angle` in that basis, `ActCircle` picks `u0` as its radius-handle
  direction.
- Point-based shapes (`ActPoint`, `ActLine`, `ActPolygon`) are already fully 3D
  for vertex/endpoint/point motion; they only need the `VIEW_PLANE` handle
  switch and a full-3D `_translate_by`.

## Decisions (confirmed)

- New kw-only constructor parameter `normal: Direction | None = None` on
  `ActRectangle2D`, `ActEllipse`, `ActCircle` (default `+z` → unchanged
  behaviour).
- `ActRectangle2D` and `ActEllipse` are symmetric **rotating** shapes — both
  store an internal `angle` and rotate in the plane via `_dir_u`/`_dir_v`.
  `ActCircle` is the **non-rotating** shape (a `normal` + one in-plane radius
  direction).  The only rectangle↔ellipse difference is the wrapped entity's
  data model (`Rectangle2D.angle` vs `Ellipse.dir_u`/`dir_v`), which surfaces
  only in the example round-trip (Phase 5), never in the `Act*` geometry.
- Handles switch to `drag_mode=DragMode.VIEW_PLANE` (single, unmodified
  trigger) — matching `InteractionSurface`.  In 2D scenes `VIEW_PLANE` ≡
  `XY_PLANE`, so flat labelling is unaffected.
- Point-based shapes get **no** `normal` param (their entities are free 3D
  points); their fix is drag-mode + full-3D translate only.
- `_translate_by` becomes full 3D everywhere (adds `delta.z`).  The existing
  `test_translate_preserves_z` tests keep passing because their `world_delta`
  has `z = 0`.

## Contract (fixed)

```python
# _active.py — private helper (near _default_drag_triggers)
def _plane_basis(normal: Direction) -> tuple[Direction, Direction]:
    """Orthonormal in-plane axes (u0, v0) with u0 × v0 = normalized normal.

    For normal=+z: u0 = (1, 0, 0), v0 = (0, 1, 0).
    """

# ActRectangle2D / ActEllipse / ActCircle — new kw-only arg
normal: Direction | None = None   # plane normal; default +z

# entity reconstruction sets the stored normal
Rectangle2D(center, size, normal=self._normal, angle=self._angle)
Ellipse(center, radius_u, radius_v, normal=self._normal, dir_u=..., dir_v=...)
Circle(center, radius, normal=self._normal)

# in-plane axes (ActRectangle2D / ActEllipse)
_dir_u() = cos(angle)·u0 + sin(angle)·v0
_dir_v() = -sin(angle)·u0 + cos(angle)·v0

# handle drag plane (all five _spawn_handles)
drag_mode=DragMode.VIEW_PLANE
```

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-plane-basis-and-ellipse.md](./01-plane-basis-and-ellipse.md) | `_plane_basis` helper + `ActEllipse` (rotating shape; the reported bug) |
| 2 | [02-rectangle.md](./02-rectangle.md) | `ActRectangle2D` (rotating shape — mirrors Phase 1) |
| 3 | [03-circle.md](./03-circle.md) | `ActCircle` (non-rotating: `normal` + radius direction) |
| 4 | [04-handle-drag-plane.md](./04-handle-drag-plane.md) | `VIEW_PLANE` handles + full-3D translate for point-based shapes |
| 5 | [05-example-apps.md](./05-example-apps.md) | Round-trip `normal`/rotation in both labelling apps |
| 6 | [06-docs-changelog.md](./06-docs-changelog.md) | Active-element docs + changelog |

## Testing as you go

- `uv run pytest py/tests/viz -q`
- `uv run ruff check .` + `uv run ty check`
- `uv run mkdocs build --strict` (phase 5)

## Non-goals

- No new `DragMode` / arbitrary-plane drag mode; no `mapper.plane()`-coupled
  handle anchoring (out of scope — `VIEW_PLANE` is sufficient for the calibrated
  case, matching `InteractionSurface`).
- No change to `ActPoint`'s standalone behaviour (already plane-correct).
- No change to the frontend (`templates/*`) or the wire protocol.
- No removal of the `TestPlaneZ` "stay on the plane" contract — only its
  generalisation from `z = const` to a `normal`-defined plane.
