# Phase 3 — Frontend surface material module (GLSL + texture binding)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` (custom-shader / SDF notes) and read
> `renderers/shader-lighting.js`, `renderers/depth-image.js` (`bindFrameTexture`),
> `renderers/image.js` (`makeEncodedTexture`), and `image-frames.js`.  This is a
> new renderer-side module pair; it follows the existing shader-assembly pattern.

## Goal

Add a pure GLSL assembler (`surface-shader.js`) that lights surfaces with the
global lighting preamble and documents the light uniforms, plus a material
factory (`surface-material.js`) that turns `ent.style.surface` into a
`THREE.Material` and binds textures.

## Files

- **New** `py/pytanga/viz/templates/renderers/surface-shader.js`
- **New** `py/pytanga/viz/templates/renderers/surface-material.js`
- **New** `js/dev/tests/surface-shader.test.mjs`

## Steps

- [x] **3.1 — `surface-shader.js` (pure GLSL, Node-testable, no THREE/DOM)**
  - `buildSurfaceVertex()` — varyings `vUv`, `vNormal`, `vWorldPosition`, `vLocalPos`; `vUv = uv`, `vLocalPos = position`, world normal/position from `modelMatrix`/`normalMatrix`.
  - `buildSurfaceFragment(userFragment, opts)` — assemble: header comment + `lightPreamble` (from `shader-lighting.js`) + optional `opts.textureUniforms` (`uniform sampler2D <name>;` per texture) + the injected `userFragment` + a `main()` that calls the documented `vec3 surfaceColor(vec3 baseColor, vec3 n, vec3 p)` helper, falling back to a standard `surfaceColor` using `uAmbientColor`/`uLightCount`/`uLightDir`/`uLightColor` when the user does not define it.
  - `buildStandardTextureFragment()` — `uniform sampler2D uTexture; uniform vec3 u_color;` sample `texture2D(uTexture, vUv).rgb` and shade via the shared light uniforms.
  - Document (module comment) the lighting-uniform contract and the varyings so custom shaders can rely on them.

- [x] **3.2 — `surface-material.js` (THREE)**
  - `createSurfaceMaterial(ent, { fallbackMaterial })`:
    - no `ent.style?.surface` → return `fallbackMaterial` (the existing `makeMaterial` result).
    - `surface.shader` present → `new THREE.ShaderMaterial({ vertexShader: buildSurfaceVertex(), fragmentShader: buildSurfaceFragment(shader.fragment, { textureUniforms }), uniforms: {...}, glslVersion: THREE.GLSL3 })`; seed `uniforms` from `shader.uniforms`, add light uniforms via `setLightUniforms(...parseLighting(DEFAULT_LIGHTING))`, and bind each `surface.textures[i]` to `uniforms[tex.uniform]` (default `uTexture0`…).
    - `surface.shader` absent + `textures.length` → a `MeshPhongMaterial` (via `makeMaterial`) whose `map` is the **first** texture; set `wrapS/T`, `repeat`, `offset` from the texture.
  - `applySurfaceTexture(material, tex, targetKey)` / `bindSurfaceTextures(material, textures)` — decode via `makeEncodedTexture` + `image-frames.js` (`hasImageFrame`/`takeImageFrame`/`registerImageFrameConsumer`), mirroring `depth-image.js::bindFrameTexture`.
  - `applySurfaceMaterialLighting(material, wireLighting)` — re-run `setLightUniforms` on the shader path (used by `three-view.js` on `scene_config` re-push).
  - Map `wrap_s/t` strings to `THREE.RepeatWrapping` / `ClampToEdgeWrapping` / `MirroredRepeatWrapping`.

- [x] **3.3 — JS test (`js/dev/tests/surface-shader.test.mjs`)**
  - `buildSurfaceVertex()` contains `vUv`/`vNormal`/`vWorldPosition`/`vLocalPos`.
  - `buildSurfaceFragment("vec3 c = u_color;", {...})` contains `lightPreamble` (`uLightCount`, `uAmbientColor`) and the injected body, and has exactly one `main()`.
  - `buildStandardTextureFragment()` declares `uniform sampler2D uTexture;` and references the light uniforms.

## Validation

```bash
node js/dev/tests/check-syntax.mjs
node --test js/dev/tests/surface-shader.test.mjs
```

## Notes

- Keep `surface-shader.js` free of three.js/DOM imports so it stays unit-testable,
  like `image-shader.js` / `depth-shader.js`.
- Lighting defaults come from `DEFAULT_LIGHTING`; the live per-scene override is
  plumbed in phase 4 via `three-view.js` (existing `_applyShaderLighting` path).
