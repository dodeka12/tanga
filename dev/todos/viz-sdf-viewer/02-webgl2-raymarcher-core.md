# Phase 2 — WebGL2 gate + minimal raymarcher core

**Status:** Planned

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

- [ ] WebGL2 gate:
  - [ ] Probe WebGL2 (or detect `renderer.capabilities.isWebGL2` after
        creating a `WebGLRenderer`).
  - [ ] On failure: display a clear error message ("SDF viewer requires
        WebGL2") and abort initialization.
- [ ] Fullscreen-quad setup:
  - [ ] Vertex shader: pass-through of a unit quad (no per-vertex geometry);
        compute ray direction in the fragment shader from the camera inverse
        projection/view.
  - [ ] Fragment shader: derive camera ray from `cameraWorldMatrix` /
        inverse projection (IQ pattern), establish `ro`/`rd`.
- [ ] Ray-march loop:
  - [ ] Fixed (initial) iteration cap; sphere-tracing `t += d` updated via a
        user-provided SDF function (initially `sdSphere` hardcoded).
  - [ ] Adaptive stepping refinement flag + epsilon/`MAX_DIST` constants from
        Phase 1 common header.
- [ ] Normal + shading:
  - [ ] Tetrahedral gradient `normal(p)` for per-pixel surface normals.
  - [ ] IQ lighting: ambient + diffuse (key light) + soft shadow (optional in
        this phase).
  - [ ] Background color + simple fog for depth cueing.
- [ ] Opacity-transfer plug (stub the extension point now, no refactor later):
  - [ ] Reserve an `opacityOf(float d)` call site in the shading path, wired
        to a single `step` implementation (`d < 0.0 ? 1.0 : 0.0`) in this
        phase.
  - [ ] Multiplier for the resolved surface color so later transfers
        (`linear`/`sigmoid`) only replace the `opacityOf` snippet, not the
        shading/raymarch structure.
  - [ ] Keep `opacityOf` in a dedicated snippet string so Phase 12 swaps it
        in without touching the raymarch body.
- [ ] Camera uniform plumbing:
  - [ ] Camera position + inverse projection/view matrices as uniforms so the
        orbit camera (reused from the existing viewer) drives the rays.
- [ ] Hardcoded sphere smoke check: render a centered sphere and verify it
      shades correctly from all angles.

## Verification

- [ ] `sdf_viewer.js` renders a sphere-ray-marched surface in a minimal HTML
      harness (can be a temporary page before Phase 6 wires the real server).
- [ ] WebGL1 context (or a stubbed `isWebGL2 === false`) triggers the error
      banner and aborts.
- [ ] No JS console errors from shader compilation.