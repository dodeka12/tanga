# Phase 3 — Surface material opacity + texture alpha

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` ("Surface material (extension
> recipe)") and the GLSL contract in `py/pytanga/viz/surface/material.py` and
> `renderers/surface-shader.js`.  This phase corrects the documented contract
> (surfaces are no longer always opaque); the docs are updated in Phase 5.

## Goal

Make `createSurfaceMaterial` use the entity's real opacity, multiply the
standard texture map's alpha by the texture alpha channel, set the transparency
flags accordingly, and document the `u_opacity` contract.

## Files

- Edit `py/pytanga/viz/templates/renderers/surface-material.js`
- Edit `py/pytanga/viz/templates/renderers/surface-shader.js`
- Edit `py/pytanga/viz/surface/material.py` (docstring only)
- Edit `js/dev/tests/surface-shader.test.mjs`
- Regenerate `js/tanga-viewer.js` + `js/tanga-viewer.manifest.json`

## Steps

- [x] **3.1 — Read the entity opacity**
  - In `surface-material.js`, import `styleParam` from `./utils.js` and replace
    `const opacity = 1.0;` with `const opacity = styleParam(ent, 'opacity', 1.0);`.
  - Delete the now-wrong "Surface materials are opaque…" comment (lines ~142-144).

- [x] **3.2 — Transparency flags + alpha-texture marker**
  - Compute `hasAlphaTexture`:
    - texture-only path: `textures[0] && textures[0].channels === 4`
    - shader path: `textures.some((t) => t && t.channels === 4)`
  - In both `ShaderMaterial` constructions set
    `transparent: opacity < 1.0 || hasAlphaTexture` and
    `depthWrite: opacity >= 0.99 && !hasAlphaTexture`.
  - Set `material.userData._alphaTexture = hasAlphaTexture` on both materials
    (consumed by Phase 4).

- [x] **3.3 — Standard-map alpha in the GLSL**
  - In `surface-shader.js::buildSurfaceFragment`, when `sampleTexture` is set,
    emit the fragment alpha as `u_opacity * texture2D(${sampleTexture}, vUv).a`;
    otherwise keep `u_opacity`.  (Add a small `alphaExpr` template variable so
    `main()` stays shared between the standard map and custom shaders.)
  - Update the header comment to state that the standard map multiplies
    `u_opacity` by the texture alpha and that `u_opacity` carries the entity
    opacity.

- [x] **3.4 — Clarify the Python shader docstring**
  - In `py/pytanga/viz/surface/material.py`, update the `SurfaceShader` docstring
    to say `u_opacity` is the **entity's opacity** (the shader decides how to use
    it).

- [x] **3.5 — Extend the JS shader test**
  - In `js/dev/tests/surface-shader.test.mjs`, assert the standard-map fragment
    contains `u_opacity * texture2D(uTexture, vUv).a`, and a custom-shader
    fragment emits a plain `u_opacity` alpha (no texture alpha term).

- [x] **3.6 — Regenerate the bundle**
  - `uv run python tools/build-viewer-js.py`

## Validation

```bash
node --test js/dev/tests/surface-shader.test.mjs
node js/dev/tests/check-syntax.mjs
uv run python tools/build-viewer-js.py --check
uv run ruff check py/pytanga/viz/surface/material.py
uv run ty check
```

## Notes

- 1/3-channel textures already decode with alpha `1.0` (`image.js::toRgba`), so
  the `* .a` term is a no-op for them; only 4-channel (RGBA/PNG) textures carry
  real alpha.
- The shader path still uses `sampleTexture: null` (the custom shader samples its
  own samplers), so its alpha stays `u_opacity` — the shader decides.
