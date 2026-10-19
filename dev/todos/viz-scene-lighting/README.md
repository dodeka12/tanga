# Scene lighting (ambient + directional + specular) — Overview

**Created:** 2026-10-19 | **Status:** Done | **Branch:** `feat/scene-lighting`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-architecture.md` — "Scene
> config", "New entity kind", and the SDF renderer notes) and the SDF lighting
> module `py/pytanga/viz/templates/renderers/sdf/lighting.js`.  This work
> **adds a per-scene lighting contract** to `scene_config` and unifies the
> standard + shader lighting, so the developer docs must be updated in Phase 7.

## Goal

Introduce one **per-scene lighting configuration** (ambient + directional lights)
that drives *both* the standard three.js renderer (the existing `MeshPhongMaterial`
entities) *and* custom shaders (the SDF renderer and the new `depth_image`
surface).  Then use it to light the depth surface's **plain** render mode with
**ambient + directional + specular (Blinn-Phong)** shading in **world space**,
while its colormap and image modes stay unlit.

## Architecture (short)

- **Python** — a `SceneLighting` value object (ambient `LightSpec` + directional
  `DirectionalLightSpec` list) + `SceneConfig.lighting`.  `None` → frontend
  default (which mirrors today's hardcoded lights).
- **Backend API** — `Visualizer.set_scene_lighting(lighting, scene_name=…)` sets
  `scene.config.lighting` and pushes `scene_config` (mirrors `set_camera`).
- **Frontend standard path** — `three-view.js` replaces `_addDefaultLights()`
  with `_applyLighting(config.lighting)`, creating `AmbientLight` +
  `DirectionalLight`s from the config (init + reset + `scene_config`).
- **Frontend shader path** — promote `renderers/sdf/lighting.js` to a shared
  `renderers/shader-lighting.js` (pure module: `lightPreamble`, `parseLighting`,
  `setLightUniforms`, `DEFAULT_LIGHTING`); SDF and `depth-image` both import it.
- **Depth surface** — vertex shader computes a world-space surface normal by
  finite differences on the depth field; the fragment shader shades the plain
  mode with Blinn-Phong using the shared light uniforms; `DepthImageStyle` gains
  `shininess`/`specular`.

## Fixed contract (decided up front — later phases implement against this)

### Python data model + API

```python
@dataclass(frozen=True)
class LightSpec:
    color: str = "#ffffff"
    intensity: float = 1.0

@dataclass(frozen=True)
class DirectionalLightSpec(LightSpec):
    # Unit vector pointing *toward* the light (NdotL = dot(N, dir)).
    direction: tuple[float, float, float] = (0.0, 0.0, 1.0)

@dataclass(frozen=True)
class SceneLighting:
    ambient: LightSpec = ...        # default: #ffffff @ 0.5
    lights: tuple[DirectionalLightSpec, ...] = ...  # default: two directionals

# SceneConfig gains:
lighting: SceneLighting | None = None

viz.set_scene_lighting(SceneLighting(...), scene_name="")
```

Default `SceneLighting` (mirrors today's `_addDefaultLights`):

- ambient: `#ffffff` @ `0.5`
- directional 1: direction `normalize((10, 20, 10)) ≈ (0.2673, 0.5345, 0.8018)`, `#ffffff` @ `0.8`
- directional 2: direction `normalize((-5, -2, -8)) ≈ (-0.5195, -0.2078, -0.8312)`, `#ffffff` @ `0.3`

### Wire (`scene_config` gains an optional `lighting` block)

```json
"lighting": {
  "ambient": { "color": "#ffffff", "intensity": 0.5 },
  "lights": [
    { "direction": [0.2673, 0.5345, 0.8018], "color": "#ffffff", "intensity": 0.8 },
    { "direction": [-0.5195, -0.2078, -0.8312], "color": "#ffffff", "intensity": 0.3 }
  ]
}
```

### Shared shader-lighting module (`renderers/shader-lighting.js`)

- `MAX_LIGHTS` (8), `DEFAULT_LIGHTING`, `lightPreamble` (GLSL
  `uLightCount`/`uLightDir[]`/`uLightColor[]`/`uAmbientColor`), `parseLighting(wire)`,
  `setLightUniforms(u, lighting)`, `parseHexColor`/`parseAmbient`/`parseLight`.
- `direction` = unit vector **toward the light**; lighting is in **world space**.

### Depth surface shading

- Vertex varyings: `vNormal` (world-space), `vWorldPosition`.
- Fragment (plain mode, `u_render_mode == 2`):
  `gl_FragColor = vec4(u_color * (ambient + Σ dir·max(N·L,0)) + specular·Σ pow(max(N·H,0), shininess), u_opacity)`.
- `DepthImageStyle` gains `shininess: float | None` (default 32) and
  `specular: str | None` (default `#ffffff`).

## Decisions (confirmed)

- **Lighting model:** ambient + directional diffuse + Blinn-Phong specular.
- **Space:** world space.
- **Direction convention:** unit vector toward the light.
- **Scope:** ambient + directional only (no point/spot), matching the current scene.
- **Specular** is a material property (`DepthImageStyle`), not a scene-light property.
- **SDF** is re-wired onto the shared module so shader/scene lights share one default.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-python-lighting-model.md](./01-python-lighting-model.md) | `SceneLighting`/`LightSpec`/`DirectionalLightSpec` + `SceneConfig.lighting` + default + serialization |
| 2 | [02-backend-set-scene-lighting.md](./02-backend-set-scene-lighting.md) | `Visualizer.set_scene_lighting` + `scene_config` push |
| 3 | [03-shared-shader-lighting-module.md](./03-shared-shader-lighting-module.md) | Generalize `sdf/lighting.js` → `renderers/shader-lighting.js`; SDF import |
| 4 | [04-standard-renderer-lighting.md](./04-standard-renderer-lighting.md) | `_applyLighting(config.lighting)` replacing `_addDefaultLights` |
| 5 | [05-depth-surface-shading.md](./05-depth-surface-shading.md) | Depth vertex normals + fragment Blinn-Phong + `DepthImageStyle.shininess`/`specular` |
| 6 | [06-unified-lighting-example.md](./06-unified-lighting-example.md) | Example: change lighting + mesh sphere + SDF cylinder + depth sin-wave, all lit the same |
| 7 | [07-docs-changelog.md](./07-docs-changelog.md) | Developer docs + user docs + changelog |

## Testing as you go

- `uv run pytest py/tests/viz -q` — Python regression.
- `node js/dev/tests/check-syntax.mjs` — frontend syntax gate.
- `node --test js/dev/tests/*.test.mjs` — JS unit tests.
- `uv run python tools/build-viewer-js.py` — rebuild the committed viewer bundle after template edits.
- `uv run mkdocs build --strict` — docs gate (phase 7).
- Manual smoke: `uv run python py/examples/viz/image/depth_surface.py` (phase 5).
- Manual smoke: `uv run python py/examples/viz/lighting/scene_lighting.py` (phase 6).

## Non-goals

- No point/spot lights or shadows (ambient + directional only, for now).
- No per-entity light override on `DepthImage` (a style-level `lights`/`ambient`
  override, like SDF, can be added later).
- No change to the `MeshPhongMaterial` used by standard entities — they keep
  three.js lighting; the scene just now drives which lights exist.


