# Phase 3 — `createSdfProxy()` (proxy box + per-object raymarch shader)

## Goal

Build a `THREE.Mesh` with a proxy `BoxGeometry` sized to the object's `bound`
and a `ShaderMaterial` whose fragment shader ray-marches the object's
**local-space** SDF and writes `gl_FragDepth`, so the standard depth buffer
handles occlusion against meshes and other SDF objects.

## Files

- New: `py/pytanga/viz/templates/renderers/sdf.js` — `createSdfProxy(ent)`,
  `updateSdfProxy(mesh, ent, prev)`, `disposeSdfProxy(mesh)`.
- New: `py/pytanga/viz/templates/renderers/sdf/proxy.glsl` — vertex +
  fragment body (local-space raymarch + `gl_FragDepth`).
- Modify: `py/pytanga/viz/templates/sdf/shaders/raymarch.glsl` — (optional)
  factor the gradient/shading core into a shared snippet so the proxy shader
  reuses it instead of duplicating it.
- Modify: `py/pytanga/viz/templates/sdf_viewer.js` — (optional) factor
  `lightPreamble`/`setLightUniforms` into `renderers/sdf/lighting.js` shared
  by both viewers.

## Steps

- [x] **3.1 — Proxy geometry**
  - `new THREE.BoxGeometry(w, h, d)` from `ent.bound` (`max - min`, inflated);
    set `mesh.position` to the bound center so the box *is* the AABB; mark
    `mesh.frustumCulled = true` (default) so off-screen proxies skip the shader.

- [x] **3.2 — Vertex shader (passthrough)**
  - Standard transform + pass the **local-space** position as a varying:
    `vLocalPos = position;  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);`
  - Use three.js built-ins (`modelViewMatrix`, `projectionMatrix`, `cameraPosition`).

- [x] **3.3 — Fragment shader (local raymarch)**
  - Ray origin = `cameraPosition` transformed into local space; direction from
    `vLocalPos` (or reconstruct via `modelMatrix` inverse). March only between
    the proxy's near/far box faces (bounded `tMin`/`tMax` from the box size).
  - `float map(vec3 p) { return <emitTree(tree)>; }` — reuse `emitTree`,
    `sdf_common.glsl`, `primitives.glsl`, `combinators.glsl`.
  - Tetrahedral normal + IQ shading + soft self-shadow (reuse the raymarch
    core), tinted by `uColor`/`uOpacity`.
  - Write `gl_FragDepth` from the hit's clip-space depth (`clip.z/clip.w`
    remapped to `[0,1]`); `discard` when no hit so the proxy back face never
    shows. Material: `depthWrite: true`, `depthTest: true`, `glslVersion: GLSL3`.

- [x] **3.4 — Uniforms**
  - `uColor` (vec3), `uOpacity` (float), `uMaxSteps` (int),
    `uLightCount/uLightDir/uLightColor/uAmbientColor` (shared lighting module),
    plus three.js auto camera/matrix uniforms.

- [x] **3.5 — Validate (static)**
  - `node --input-type=module --check` on all touched JS (green); `dev/src/sdf_proxy_smoke.mjs` + `py/tests/viz/sdf/test_proxy_shader.py` assert one `main`, `out vec4`, `gl_FragDepth`, no `#version`/`precision`. Shared lighting factored into `renderers/sdf/lighting.js` (one source of truth for both viewers); HTML export bundles the SDF renderer + inlines the GLSL.
  - `node --input-type=module --check` on `sdf.js`.
  - Confirm the assembled proxy fragment contains exactly one `main`, no
    `#version`/`precision` (GLSL3 host prepends them), and declares
    `out vec4` (mirrors the existing `raymarch.glsl` contract checks).

## Validation

`node --input-type=module --check` on all touched JS; static GLSL contract
checks mirroring `py/tests/viz/sdf/test_raymarch_shader.py`. Browser compile
deferred to Phase 5 (no headless browser in the repo).

## Notes

- The raymarch is bounded by the proxy box (enter/exit distances), so cost
  scales with the object's screen footprint, not the viewport — the key
  performance win over the fullscreen SDF viewer.
- `gl_FragDepth` must match three.js's depth range `[0,1]`; use the camera's
  projection matrix, not a linearized depth.
