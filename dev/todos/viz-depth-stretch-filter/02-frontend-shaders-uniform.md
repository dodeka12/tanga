# Phase 2 — Frontend shaders + renderer uniform binding

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` (the `DepthImage` shader/renderer
> contract and the `depth_image_update` merge) and the existing
> `py/pytanga/viz/templates/renderers/depth-shader.js`.  This phase extends the
> existing vertex/fragment builders and uniform map — no new protocol or
> architecture.

## Goal

Compute `vStretch` in the vertex shader, add the `u_max_stretch` fragment
discard, and register the uniform so live `depth_image_update` patches apply.

## Files

- Edit `py/pytanga/viz/templates/renderers/depth-shader.js`
- Edit `py/pytanga/viz/templates/renderers/depth-image.js`
- Edit `js/dev/tests/depth-shader.test.mjs`

## Steps

- [x] **2.1 — Vertex varying + neighbour sampling**
  - In `buildDepthVertex`, add `varying float vStretch;` after
    `varying vec3 vWorldPosition;`.
  - After `dU`/`dV`, sample the `-u`/`-v` neighbours:
    `float dL = texture2D(uDepth, snap - du).r; float dD = texture2D(uDepth, snap - dv).r;`
    and `bool missingL = (dL == u_missing_depth); bool missingD = (dD == u_missing_depth);`.
  - Initialize `vStretch = 0.0;` before the `u_depth_kind` branch.

- [x] **2.2 — Pinhole slope**
  - In the pinhole branch, add `zCL`/`zCD` (clamp like `zCU`/`zCV`), then:
    - `float invZ = 1.0 / max(zC, 1e-6);`
    - `float sx = u_fx * uDepthSize.x / max(u_frame_size.x, 1.0);`
    - `float sy = u_fy * uDepthSize.y / max(u_frame_size.y, 1.0);`
    - for each of the four pairs (missing centre or neighbour → skip):
      `vStretch = max(vStretch, abs(zCU - zC) * sx * invZ);` (and `zCL`×`sx`,
      `zCV`×`sy`, `zCD`×`sy`).

- [x] **2.3 — Orthographic slope**
  - In the orthographic branch, add `zCL`/`zCD`, then:
    - `float invSx = 1.0 / max(uWorldStep.x, 1e-6);`
    - `float invSy = 1.0 / max(uWorldStep.y, 1e-6);`
    - `float absScale = abs(u_depth_scale);`
    - for each pair: `vStretch = max(vStretch, abs(zCU - zC) * absScale * invSx);`
      (and `zCL`×`invSx`, `zCV`×`invSy`, `zCD`×`invSy`).

- [x] **2.4 — Fragment discard**
  - In `buildDepthFragment`, add `varying float vStretch;` and
    `uniform float u_max_stretch;`.
  - Between the missing-depth and segment discards add:
    `if (u_max_stretch > 0.0 && vStretch > u_max_stretch) discard;`.

- [x] **2.5 — Renderer uniform**
  - In `depth-image.js::buildDepthUniforms`, add
    `u_max_stretch: { value: u.u_max_stretch ?? 0.0 }` next to the other scalar
    uniforms.  No change to `applyDepthImageUniforms` (generic float path).

- [x] **2.6 — JS shader tests + rebuild**
  - In `js/dev/tests/depth-shader.test.mjs`, add assertions that the vertex
    shader contains `varying float vStretch`, `snap - du`, and `snap - dv`; the
    fragment shader contains `uniform float u_max_stretch` and
    `vStretch > u_max_stretch`.
  - Rebuild the bundle with `uv run python tools/build-viewer-js.py`.

## Validation

```bash
node js/dev/tests/check-syntax.mjs && node --test js/dev/tests/depth-shader.test.mjs
uv run python tools/build-viewer-js.py && uv run python tools/build-viewer-js.py --check
```

## Notes

- `u_frame_size`/`uDepthSize` are the reference frame and the transmitted
  (downscaled) depth size; their ratio is the reference-pixel step between
  adjacent mesh samples — required because depth is decimated to the mesh.
- `applyDepthImageUniforms` already sets float uniforms via
  `uniform.value = value`, so `u_max_stretch` needs no special-case.
