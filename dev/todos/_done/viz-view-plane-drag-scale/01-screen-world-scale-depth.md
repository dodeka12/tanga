# Phase 1 — Depth-based `screenWorldScale` + regression tests

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-controls-and-interactions.md`
> and `viz-architecture.md`).  This fixes the behaviour of the existing
> `screenWorldScale` helper documented in `viz-architecture.md`; it does not
> introduce new architecture.

## Goal

Change the perspective branch of `screenWorldScale` to use depth along the view
axis instead of Euclidean distance, and pin the new behaviour with Node-executed
tests in `py/tests/viz/test_camera_fit_math.py`.

## Files

- Edit: `py/pytanga/viz/templates/camera-fit.js`
- Edit: `py/tests/viz/test_camera_fit_math.py`

## Steps

- [x] **1.1 — Add the `forward` parameter and depth computation.**
  - Change the signature to `screenWorldScale(camera, viewportPx, worldPos, forward)`.
  - In the perspective branch, keep `dx/dy/dz` and compute:
    - `let depth = Math.sqrt(dx * dx + dy * dy + dz * dz);`
    - if `forward` is non-zero, `depth = Math.abs((fx*dx + fy*dy + fz*dz) / fl)`
      where `fl = Math.sqrt(fx*fx + fy*fy + fz*fz)`.
  - Use `depth` in place of `dist` in both `(span / near) * depth` and
    `2 * depth * tan(fov / 2)`.

- [x] **1.2 — Update the JSDoc.**
  - Document the new optional `forward` param and that the perspective branch
    uses depth-along-view-axis (Euclidean fallback when omitted).

- [x] **1.3 — Keep existing tests green.**
  - The current `test_screen_world_scale` / `test_screen_world_scale_pinhole_frustum`
    pass no `forward`, so they must still return the Euclidean-based values
    (`0.02` / `0.1`).  No change to them.

- [x] **1.4 — Add depth regression tests.**
  - New test `test_screen_world_scale_uses_depth_not_distance`:
    - pinhole branch: camera at origin, `forward {x:0,y:0,z:-1}`,
      `_pinholeFrustum {top:5,bottom:-5,near:1}`, worldPos `{x:3,y:4,z:-10}`
      → expect `0.1` (depth 10), not the Euclidean `~0.1118`.
    - fov branch: camera at origin, `fov:90`, same `forward`, worldPos
      `{x:6,y:8,z:-10}` → expect `0.02` (depth 10), not Euclidean `~0.0283`.

## Validation

`uv run pytest py/tests/viz/test_camera_fit_math.py -q`

## Notes

- `camera-fit.js` is `three`/DOM-free and is unit-tested by Node via
  `test_camera_fit_math.py`; keep the new code dependency-free.
