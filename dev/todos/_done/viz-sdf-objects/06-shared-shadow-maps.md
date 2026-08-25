# Phase 6 — *(deferred)* Mutual shading via shared shadow maps

> **Status:** deferred / optional. The vertical slice (Phases 1–5) ships without
> this; SDF objects still get soft *self*-shadowing, but do not cast/receive
> shadows onto *other* objects.

## Goal

Make SDF objects cast and receive shadows with **other SDF objects and standard
meshes**, using three.js rasterized shadow maps — the one mechanism that unifies
SDF↔SDF and SDF↔mesh shading in a single pass.

## Files (indicative)

- Modify: `py/pytanga/viz/templates/views/three-view.js` — enable
  `renderer.shadowMap` and add a shadow-casting directional light.
- Modify: `py/pytanga/viz/templates/renderers/sdf.js` — a shadow-pass material
  variant that ray-marches the object's SDF in the light's view to write depth
  into the shadow map.
- Modify: `py/pytanga/viz/templates/renderers/sdf/proxy.glsl` — sample the
  shadow map in the shade path (`shadowMap` uniforms) and modulate the diffuse
  term.

## Steps

- [ ] **6.1** Enable shadow maps on the standard renderer + cast light; mark
  mesh objects `castShadow`/`receiveShadow` as appropriate.
- [ ] **6.2** Add an SDF shadow-depth pass: render the proxy with a
  light-space raymarch that writes `gl_FragDepth`, so the SDF surface depth
  lands in the shadow map (bounds the march by the proxy in light space).
- [ ] **6.3** In the forward SDF shade path, sample the shadow map (three.js
  `#include <shadowmap_pars_fragment>` / `getShadow()` or explicit sampler) and
  multiply the directional contribution.
- [ ] **6.4** Validate with the mixed example (an SDF sphere shadowing a mesh
  plane and vice-versa) + regression.

## Notes

- This is the only way to get SDF↔mesh shadows without a global SDF field; it
  is a standard three.js technique but adds a shadow pass + shadow-map uniforms,
  hence deferred. Kept as a separate phase so it never blocks the base feature.
