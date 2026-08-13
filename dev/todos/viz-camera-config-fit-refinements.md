# Viz: Camera Config Fit Refinements — 2D Stretch Borders + Exact 3D Contain Fit

**Date:** 13 August 2026

**Status:** Implemented

**Depends on / cross-references:** [`viz-camera-config-restructure.md`](viz-camera-config-restructure.md),
which introduced the typed `CameraConfig` base class, `CameraConfig2d` /
`CameraConfig3d` subclasses, the `View2DConfig` / `ViewPlaneConfig` input specs,
and the `get_camera*` builders.  This document builds on top of that work and
assumes its schema is already in place.

## Goal

Two refinements to the camera-fitting behaviour introduced by the initial plan:

- **A — `border_px` in 2D stretch mode (`uniform=False`).**  The pixel border
  must also be honoured when the 2D view stretches to fill the viewport, not
  only when letterboxing.
- **B — exact 3D contain fit.**  The perspective camera produced by
  `get_camera_view3d()` must perfectly contain the requested plane for the
  **actual browser aspect ratio**, instead of the current aspect-agnostic
  `max(extent_u, extent_v)` approximation.

## A — `border_px` in 2D Stretch Mode

### Current behaviour

`CameraConfig2d.uniform=False` maps the rectangle directly onto the full
viewport with symmetric half-extents (`left=-extX/2`, `right=extX/2`,
`top=extY/2`, `bottom=-extY/2`).  `border_px` is ignored.

### Required behaviour

The rectangle should fill only the **content area** inset by the border, not the
whole window.  Let `W × H` be the window, `bp = border_px`, `cw = W - 2bp`,
`ch = H - 2bp`.  Because the symmetric frustum half-extent `hw` maps to `W/2`
pixels while the rectangle half-extent `extX/2` must map to `cw/2` pixels:

```
hw = (extX/2) · (W / cw)
hh = (extY/2) · (H / ch)
```

The stretch branch of `_orthoFrustum()` in `py/pytanga/viz/templates/view_mode.js`
becomes:

```js
const fX = (cw > 0) ? w / cw : 1;
const fY = (ch > 0) ? h / ch : 1;
return {
    left:  -(extX / 2) * fX,
    right:  (extX / 2) * fX,
    top:    (extY / 2) * fY,
    bottom:-(extY / 2) * fY,
};
```

With `bp = 0` this reduces to the current behaviour (`hw = extX/2`,
`hh = extY/2`), so it is a strict generalization.  Because `handleResize()`
already reruns `_orthoFrustum(...)` with the stored rectangle + `uniform` +
`border_px`, updating the helper covers both initial placement and resizing —
no other JS change is needed for part A.

## B — Exact 3D Contain Fit

### The math

At camera distance `d` with vertical FOV `θ`, a point at lateral offset `r`
subtends `atan(r/d)`.  To contain the plane extents on the **vertical** axis:

```
extent_v / 2  ≤  d · tan(θ/2)
```

and on the **horizontal** axis (whose half-FOV is `tan⁻¹(aspect·tan(θ/2))`):

```
extent_u / 2  ≤  d · (aspect · tan(θ/2))
```

Solving for the smallest `d` that satisfies both:

```
d = max(extent_v, extent_u / aspect) / (2 · tan(θ/2))
```

This is the 2D letterbox formula `fit = max(extent_x/aspect, extent_y)`
generalized to perspective — the only difference is the `/(2·tan(θ/2))`
conversion from world size to distance.

### Why this must be computed in the frontend

`d` (and therefore `position`) depends on the browser aspect ratio, which the
Python backend does not know.  This is the same reason the 2D frustum is
derived in the frontend.  The plane geometry must therefore be carried as raw
parameters and finished in the browser, recomputed on `resize`.

### `CameraConfig3d` schema change

Add plane-fit raw parameters to `py/pytanga/viz/camera.py`:

```python
@dataclass(kw_only=True)
class CameraConfig3d(CameraConfig):
    type: Literal["3d"] = "3d"
    fov: float = 50.0

    # Plane-fit mode — when set, the frontend derives the distance (and thus
    # position/near/far) from the live aspect ratio, anchoring at ``target``
    # with the optical-axis direction normalize(position - target).
    extent_u: float | None = None
    extent_v: float | None = None
```

The **anchor point is `target`** and the **optical axis direction is
`normalize(position - target)`** — both already present in the inherited base
class, so no `normal` or `point` field is needed.

### `get_camera_view3d()` change

Update the builder to emit the plane-fit params instead of a precomputed
`position` / `near` / `far`:

```python
def get_camera_view3d(config: ViewPlaneConfig) -> CameraConfig3d:
    n = _normalize(config.normal)
    center = config.center if config.center is not None else config.point
    # ... orthogonalize span_u / compute vv = n × u (unchanged) ...
    return CameraConfig3d(
        fov=fov,
        target=center,          # plane anchor / view centre
        up=vv,                  # v̂ = n̂ × û
        position=position,      # direction source (normalize(position - target))
        near=..., far=...,      # static/glTF fallback at default distance
        extent_u=abs(ext_u),
        extent_v=abs(ext_v),
    )
```

The builder keeps `position` / `near` / `far` computed at the legacy default
distance so explicit direction and static/glTF export still work. The live
frontend treats `extent_u`/`extent_v` as the discriminator and rescales the
distance along `normalize(position - target)`.

Manual/explicit `CameraConfig3d(position=..., target=..., fov=...)` has
`extent_u=None` and `extent_v=None`, so the frontend applies `position` /
`target` directly — fully backward compatible.

### Frontend (`view_mode.js`)

In the `type === "3d"` branch:

- If `extent_u` / `extent_v` are present (plane-fit mode):
  - `n = normalize(position - target)` (direction from the existing values)
  - `d = max(extent_v, extent_u / aspect) / (2 · tan(fov/2))`
  - `position = target + n · d`
  - `near = max(0.01, d · 1e-3)`, `far = d · 10`
  - cache `{ target, dir: n, extent_u, extent_v, fov }` on `camera.userData`
    so `handleResize()` can recompute on window resize.
- Otherwise (explicit placement): apply `position` / `target` / `up` / `fov`
  directly (current behaviour).

`handleResize()` gains a 3D branch that, when plane-fit data is cached,
recomputes `d` / `position` / `near` / `far` from the new aspect and calls
`camera.updateProjectionMatrix()`.

### glTF exporter (`_gltf.py`)

glTF is static with no live aspect, so plane-fit keeps the **16:9** ratio (the
same ratio already used for glTF `aspectRatio`):

- If plane-fit params are present, compute `d` at `aspect = 16/9` and set
  `position` / `target` / camera accordingly.
- Explicit-placement behaviour is unchanged.
- Document this as the static-export approximation.

## Files Touched

| File | Change |
|------|--------|
| `py/pytanga/viz/camera.py` | Add `extent_u` / `extent_v` to `CameraConfig3d`; update `get_camera_view3d`. |
| `py/pytanga/viz/templates/view_mode.js` | `border_px` in `_orthoFrustum` stretch branch; exact 3D plane fit in `switchToCamera` + `handleResize`. |
| `py/pytanga/viz/export/_gltf.py` | Handle plane-fit fields at 16:9. |
| `py/tests/viz/test_scene_session.py` | Update `test_view3d_builder` to assert `extent_u`/`extent_v` set (and `position`/`target`/`up` still populated); add explicit-placement discimination test. |
| `docs/py/viz/camera.md` | Document `border_px` in stretch mode and exact 3D contain fit. |

## Implementation Order

- [x] 1. `py/pytanga/viz/camera.py` — add `extent_u`/`extent_v` to `CameraConfig3d`; update `get_camera_view3d`.
- [x] 2. `py/pytanga/viz/templates/view_mode.js` — `border_px` stretch + exact 3D fit.
- [x] 3. `py/pytanga/viz/export/_gltf.py` — plane-fit at 16:9.
- [x] 4. `py/tests/viz/test_scene_session.py` — update tests.
- [x] 5. `docs/py/viz/camera.md` — update docs.
- [x] 6. Run full test suite.

## Open Questions / Assumptions

- **Optical axis direction** — not stored as an explicit field; it is derived
  in the frontend as `normalize(position - target)`.  This matches the existing
  `ViewPlaneConfig.normal` semantics (normal points from plane toward camera).
- **`border_px` semantics in stretch mode** — the rectangle fills the inset
  content area (same meaning as letterbox mode): the border appears as extra
  margin on all four sides.
- **glTF plane-fit** — fixed 16:9 aspect (static export approximation), same
  ratio the glTF `perspective.aspectRatio` already assumes.