# Phase 3 — CPU reference test

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` (the pinhole vertex math in
> `compute_pinhole_positions`) — this phase is a pure-Python mirror of the shader
> slope, using the already-canonical reference function; no architecture change.

## Goal

Add a CPU reference test proving the angle→discard semantics on synthetic
scenes: border triangles at a box/plane depth jump are flagged, plane/box
interiors and a moderately tilted plane are kept.

## Files

- New `py/tests/viz/test_depth_image_stretch.py`

## Steps

- [x] **3.1 — Per-vertex stretch helper**
  - Add a local `_vertex_stretch(depth, fx, fy, cx, cy) -> np.ndarray` that:
    - calls `compute_pinhole_positions(...)` to get `(positions, u, v)` (camera
      frame, ref-pixel centres), reshapes to `(H, W, 3)` / `(H, W)`;
    - for each interior vertex computes the max over its four neighbours of
      `|zN − zC| · f / (zC · Δref)` (u uses `fx`/`|Δu|`, v uses `fy`/`|Δv|`,
      with `Δu`/`Δv` the reference-pixel spacing from the returned `u`/`v`);
    - treats out-of-range neighbours as `0` (no jump).

- [x] **3.2 — Box-in-front-of-plane scene**
  - Build a depth map (e.g. 64×64, no image so `frame == depth`) where a central
    box region is `Z = 1.5` and the surrounding plane is `Z = 3.0`, intrinsics
    `fx = fy = 400`, `cx/cy` centred.
  - Assert border vertices have `stretch > tan(radians(80))` and interior
    plane/box vertices have `stretch < tan(radians(80))` (≈ 0).

- [x] **3.3 — Tilted plane stays complete**
  - Build a depth map that unprojects to a plane tilted ~30° from the viewing
    ray (e.g. `z = d / (cos(60°) + sin(60°) · xnorm)`, `xnorm = (u−cx)/fx`) and
    assert **every** vertex `stretch < tan(radians(80))`.

## Validation

```bash
uv run pytest py/tests/viz/test_depth_image_stretch.py -q
```

## Notes

- The helper mirrors the shader's slope with the general reference-pixel step,
  so it also documents why the `u_frame_size/uDepthSize` factor is needed.
- Values stay within range, so the unclamped `compute_pinhole_positions` output
  is sufficient (no `depth_min`/`depth_max` clamp needed here).
