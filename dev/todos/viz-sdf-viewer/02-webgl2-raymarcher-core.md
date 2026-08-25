# Phase 2 — WebGL2 gate + minimal raymarcher core

**Status:** Done

## Goal

Prove the SDF rendering loop works end-to-end with a hardcoded object: create a
WebGL2 three.js renderer, a fullscreen-quad `ShaderMaterial` ray-marcher, a
gradient-based normal estimate, and IQ-style shading. This is the foundation
every later phase plugs into.

## Files

- New: `py/pytanga/viz/templates/sdf/shaders/raymarch.glsl` (vertex +
  fragment body; includes the shared glass pipeline from Phase 1)
- New: `py/pytanga/viz/templates/sdf/sdf_viewer.js` (scene/render loop;
  WebGL2 gate lives here)

## Requirements

- **WebGL2 required.** On startup, detect WebGL2 via a probe context /
  `renderer.capabilities.isWebGL2`. If unavailable, render an in-page error
  banner (reusing the `viewer.html` error-banner pattern) and stop — no
  WebGL1 fallback.

## Steps

- [x] WebGL2 gate:
  - [x] Probe WebGL2 (or detect `renderer.capabilities.isWebGL2` after
        creating a `WebGLRenderer`).
  - [x] On failure: display a clear error message ("SDF viewer requires
        WebGL2") and abort initialization.
- [x] Fullscreen-quad setup:
  - [x] Vertex shader: pass-through of a unit quad (no per-vertex geometry);
        compute ray direction in the fragment shader from the camera inverse
        projection/view.
  - [x] Fragment shader: derive camera ray from `cameraWorldMatrix` /
        inverse projection (IQ pattern), establish `ro`/`rd`.
- [x] Ray-march loop:
  - [x] Fixed (initial) iteration cap; sphere-tracing `t += d` updated via a
        user-provided SDF function (initially `sdSphere` hardcoded).
  - [x] Adaptive stepping refinement flag + epsilon/`MAX_DIST` constants from
        Phase 1 common header.
- [x] Normal + shading:
  - [x] Tetrahedral gradient `normal(p)` for per-pixel surface normals.
  - [x] IQ lighting: ambient + diffuse (key light) + soft shadow (optional in
        this phase).
  - [x] Background color + simple fog for depth cueing.
- [x] Opacity-transfer plug (stub the extension point now, no refactor later):
  - [x] Reserve an `opacityOf(float d)` call site in the shading path, wired
        to a single `step` implementation (`d < 0.0 ? 1.0 : 0.0`) in this
        phase.
  - [x] Multiplier for the resolved surface color so later transfers
        (`linear`/`sigmoid`) only replace the `opacityOf` snippet, not the
        shading/raymarch structure.
  - [x] Keep `opacityOf` in a dedicated snippet string so Phase 12 swaps it
        in without touching the raymarch body.
- [x] Camera parity (identical default + custom view to the standard viewer):
  - [x] Reuse the standard viewer's `view_mode.js` `createCamera` /
        `switchToCamera` (3D branch) unchanged — do not fork a copy. Default
        camera is therefore `PerspectiveCamera(fov=50, aspect, 0.1, 1000)` at
        `position=(8, 6, 10)` looking at the origin, matching `viewer.js`.
  - [x] Reuse `controls.js` `setupControls` unchanged so the OrbitControls
        defaults (`target=(0,0,0)`, `minDistance=1`, `maxDistance=100`) match.
  - [x] Apply a custom `CameraConfig3d` exactly as `viewer.js` does
        (`fov = cc.fov || 50`; `near`/`far`/`up`/`position`/`target` applied
        only when provided; `target` also sets the controls target).
- [x] Camera uniform plumbing (feed that shared camera into the raymarcher):
  - [x] `cameraPosition` (for `ro`), `cameraWorldMatrix`,
        `cameraProjectionMatrixInverse` (inverse view-projection for `rd`),
        and `cameraNear` / `cameraFar` as uniforms, so `MAX_DIST` / the step
        range track the camera far rather than a hardcoded constant.
- [ ] Hardcoded sphere smoke check: render a centered sphere and verify it
      shades correctly from all angles.

## Verification

- [ ] `sdf_viewer.js` renders a sphere-ray-marched surface in a minimal HTML
      harness (can be a temporary page before Phase 6 wires the real server).
- [ ] WebGL1 context (or a stubbed `isWebGL2 === false`) triggers the error
      banner and aborts.
- [ ] No JS console errors from shader compilation.
- [ ] A headless GLSL compile check (e.g. `glslangValidator` / Node `three`)
      parses the assembled raymarch shader with no syntax errors. *(deferred to
      the browser — no `glslangValidator`/`glslc`/Node-`three` available
      locally; a structural Python smoke test
      `py/tests/viz/sdf/test_raymarch_shader.py` covers assembly order, single
      `main()`, brace balance, and `#version`/`precision` hygiene instead.)*
