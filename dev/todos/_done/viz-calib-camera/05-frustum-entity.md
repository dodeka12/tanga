# Phase 5 — `Frustum` geometry entity + `FrustumStyle`

## Goal

Add the visualization-only `Frustum` entity (frozen dataclass, **no** multivector
representation) with a `Frustum.from_camera(camera)` classmethod, and its
`FrustumStyle`. This mirrors the existing `Rectangle2D` viz-only entity pattern.

## Files

- New: `py/pytanga/geometry/entities/frustum.py`
- Edit: `py/pytanga/geometry/entities/__init__.py` (export `Frustum`)
- Edit: `py/pytanga/geometry/__init__.py` (export `Frustum`)
- Edit: `py/pytanga/viz/_styles/_entity_styles.py` (add `FrustumStyle`)
- Edit: `py/pytanga/viz/__init__.py` (export `FrustumStyle`)
- New: `py/tests/geometry/test_frustum.py`
- New: `py/tests/viz/test_frustum_style.py`

## Steps

- [x] **5.1 — `Frustum` frozen dataclass (viz-only)**
  - `near` / `far`, each a `Point` (apex) or a `Rectangle2D`, or a 4-corner
    sequence of `Point`s. Coerce with the `_coerce` helpers (`to_point`, …).
  - Expose an `apex` property (True when the near end is a single point) and a
    `__repr__` like `Box`/`Rectangle2D`. Document that it cannot be passed to
    `pytanga.geometry.create` / `analyze`.

- [x] **5.2 — `Frustum.from_camera(camera, *, near=None, far=None)`**
  - Lazy-import `pytanga.viz.camera.CameraConfig3d` for the type check; read
    `position` / `target` / `up` / `fov` / `near` / `far` / `intrinsics`
    duck-typed (no hard geometry→viz import at module load).
  - Compute the near/far rectangles in the camera frame (optical axis = normal,
    right/up = in-plane axes). Use `intrinsics` (`fx,fy,cx,cy,width,height`) when
    present, else `fov` + a default aspect. When `near <= 0`, return the apex
    form (`near = Point(position)`).

- [x] **5.3 — `FrustumStyle(VizStyle)`**
  - `color: str | None`, `opacity: float | None`, `fill: bool = False`,
    `fill_opacity: float | None`, `thickness: float | None`.
  - `to_dict()` emits `style_type: "FrustumStyle"` and omits `None`s (mirror
    `Rectangle2DStyle`).

- [x] **5.4 — exports**
  - Export `Frustum` from `pytanga.geometry`; `FrustumStyle` from `pytanga.viz`.

- [x] **5.5 — tests**
  - Entity coercion + `apex` detection; `from_camera` corner correctness for an
    axis-aligned camera; `FrustumStyle.to_dict` round-trip.

## Validation

`uv run pytest py/tests/geometry/test_frustum.py py/tests/viz/test_frustum_style.py -q`

## Notes

- `Frustum` is a **visualization-only** entity — it is not an `MV`, is not
  analyzable, and is not convertible to a multivector (same contract as
  `Rectangle2D`).
- Two parallel planes with a separation and different sizes = two `Rectangle2D`
  ends; the point form = `near = Point(...)` (apex).

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
