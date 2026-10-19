# Phase 5 — Depth surface shading (ambient + directional + specular)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` (the `depth_image` renderer and
> custom-shader notes) and the depth-image docs
> `docs/py/viz/image/depth-image.md`.  This phase adds lighting to the depth
> shader using the shared `shader-lighting.js` module; it does not change the
> scene-config contract.

## Goal

Light the depth surface's **plain** render mode (`u_render_mode == 2`) with
Blinn-Phong shading (ambient + directional diffuse + specular) in **world
space**, using the shared scene-lighting module; colormap and image modes stay
unlit.

## Files

- **Edit** `py/pytanga/viz/templates/renderers/depth-shader.js` — vertex normals,
  fragment lighting.
- **Edit** `py/pytanga/viz/templates/renderers/depth-image.js` — light uniforms +
  `setLightUniforms`.
- **Edit** `py/pytanga/viz/_styles/_entity_styles.py` — `DepthImageStyle.shininess`
  + `.specular` + `to_dict`.
- **Edit** `py/pytanga/viz/depth_image.py` — serialize `u_shininess` / `u_specular`.
- **New/Edit** `js/dev/tests/depth-shader.test.mjs` (extend the existing test).
- **Edit** `py/examples/viz/image/depth_surface.py` — demonstrate lit plain mode.

## Steps

- [x] 5.1 Vertex shader (`buildDepthVertex`): after computing the displaced
  `p`, compute a world-space surface normal by finite differences on `uDepth`:
  - sample `d` at `snap`, `snap+du`, `snap+dv` (one sample step = `1.0 / uDepthSize`),
  - build neighbor world positions (same `position.z + (depth-offset)*scale`
    displacement) and `normalize(cross(...))`, guarding against missing depth,
  - emit `vNormal = normalize(mat3(modelMatrix) * n)` and
    `vWorldPosition = (modelMatrix * vec4(p, 1.0)).xyz` (add the varyings).
  - Keep `vValid`/`vDepth` behavior unchanged.
- [x] 5.2 Fragment shader (`buildDepthFragment`):
  - prepend the shared `lightPreamble` (import `lightPreamble` from
    `../shader-lighting.js` — same folder, so `./shader-lighting.js`) and declare
    `varying vec3 vNormal; varying vec3 vWorldPosition; uniform float u_shininess; uniform vec3 u_specular;`,
  - in `u_render_mode == 2`, replace `vec4(u_color, u_opacity)` with Blinn-Phong:
    `N = normalize(vNormal)` (flip by `u_double_sided` if present / by facing),
    `V = normalize(cameraPosition - vWorldPosition)`,
    `ambient = uAmbientColor * u_color`,
    `diffuse = Σ uLightColor[i] * u_color * max(dot(N, uLightDir[i]), 0.0)`,
    `H = normalize(uLightDir[i] + V)`,
    `specular = Σ uLightColor[i] * u_specular * pow(max(dot(N, H), 0.0), u_shininess)`,
    `gl_FragColor = vec4(ambient + diffuse + specular, u_opacity)`.
- [x] 5.3 Renderer (`depth-image.js`): in `buildDepthUniforms`, add the light
  uniform objects (`uLightCount`, `uLightDir[]`, `uLightColor[]`, `uAmbientColor`)
  plus `u_shininess` / `u_specular`; after material creation, call
  `setLightUniforms(material.uniforms, parseLighting(DEFAULT_LIGHTING))` for now
  (scene-config plumbing is optional in this phase; the shared default is enough
  to light the surface).  Add `parseLighting`/`DEFAULT_LIGHTING`/`setLightUniforms`
  imports from `./shader-lighting.js`.
- [x] 5.4 `DepthImageStyle`: add `shininess: float | None = None` (default 32 at
  resolve time) and `specular: str | None = None` (default `#ffffff`); serialize
  both in `to_dict()` when set.
- [x] 5.5 `depth_image.py::_serialize_uniforms`: add `u_shininess` (default 32.0)
  and `u_specular` (default `[1,1,1]`) from the resolved style.
- [x] 5.6 Extend `js/dev/tests/depth-shader.test.mjs`: assert the built vertex
  declares `vNormal`/`vWorldPosition` and the built fragment declares the light
  uniforms + shades plain mode (string-level assertions consistent with the
  existing test).
- [x] 5.7 Update `py/examples/viz/image/depth_surface.py` to show the lit plain
  mode (e.g. `render_mode="plain"`, a `color`, `shininess`), keeping the existing
  modes.

## Validation

```bash
node js/dev/tests/check-syntax.mjs
node --test js/dev/tests/depth-shader.test.mjs
uv run python tools/build-viewer-js.py
uv run pytest py/tests/viz/test_depth_image.py py/tests/viz/test_depth_image_example.py -q
# Manual smoke:
uv run python py/examples/viz/image/depth_surface.py
```
