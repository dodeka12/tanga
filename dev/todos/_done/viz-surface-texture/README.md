# Surface texture mapping + custom surface shaders + shader error reporting — Overview

**Created:** 2026-10-19 | **Status:** Done | **Branch:** `feat/tex-map`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` ("New entity kind", "Styles", the
> image-frame delivery notes, and the SDF/shader-lighting notes),
> `docs/dev/architecture/viz-controls-and-interactions.md` (the `client_log` /
> `sendLog` → `on_client_log` channel and the banner/overlay contract), and
> `docs/dev/architecture/viz-theme-system.md` is **not** affected. This work
> **adds** a surface-material contract to entity styles, reuses the existing
> image-frame pipeline, and surfaces shader compile errors over the existing
> `client_log` channel — the developer docs must be updated in Phase 7.

## Goal

Let solid surface entities (`Plane`, `Sphere`, `Ellipsoid`, `Disk`, `Box`,
`Cylinder`, `Cone`) be textured by an image, a custom GLSL program, or both.
Deliver (1) a Python `surface` material structure with built-in standard shaders
(checkerboard, sphere coloring, …), (2) image delivery that reuses the existing
binary frame codec (default JPEG for `uint8`), (3) a standard texture shader that
uses the recently-added global scene lighting and documents those light uniforms
for custom shaders, and (4) end-to-end shader-compile-error reporting that shows
the driver's error in a banner on the frontend.

## Architecture (short)

- **Python** — a new `py/pytanga/viz/surface/` subpackage (mirrors `pytanga.viz.sdf`):
  `SurfaceShader`, `SurfaceTexture`, `SurfaceMaterial`, `surface_material()`,
  and standard shaders in `standard.py`.  Solid-surface styles gain a
  `surface: SurfaceMaterial | None` field; the serializer emits it into
  `ent.style.surface`.
- **Image delivery** — `SurfaceTexture` wraps an existing `ImageData`; its pixels
  travel as binary frames through `encode_image_frame` (codec `None` → JPEG for
  `uint8` 1/3-channel, zlib otherwise), collected by a new
  `Scene.surface_texture_frames()` summed into `Visualizer._image_frames_for`.
- **Frontend** — new `renderers/surface-shader.js` (pure GLSL assembly using
  `shader-lighting.js`) + `renderers/surface-material.js` (material factory +
  texture binding via `makeEncodedTexture`/`image-frames.js`).  The seven solid
  renderers branch on `ent.style?.surface`.
- **Lighting** — the standard texture shader and any custom surface shader use
  the shared `shader-lighting.js` preamble (`uLightCount`/`uLightDir[]`/
  `uLightColor[]`/`uAmbientColor`); this contract is documented for user shaders.
- **Errors** — `three-view.js` sets `renderer.debug.onShaderError` →
  `sendLog('error', 'Shader compile failed', { source: 'shader', data: { error } })`;
  `Visualizer.on_shader_error(handler)` filters `ClientLogRecord.source == "shader"`
  over the existing `on_client_log` channel.

## Fixed contract (decided up front — later phases implement against this)

### Python surface material model (`py/pytanga/viz/surface/material.py`)

```python
@dataclass(frozen=True)
class SurfaceShader:
    name: str
    fragment: str                          # GLSL fragment body (no main(), no #version)
    vertex: str | None = None              # optional full/partial vertex override
    uniforms: dict[str, Any] = field(default_factory=dict)

@dataclass
class SurfaceTexture:
    image: ImageData                       # non-tiled; pixels travel as a binary frame
    uniform: str = "uTexture0"             # sampler name a custom shader declares
    repeat_u: float = 1.0
    repeat_v: float = 1.0
    offset_u: float = 0.0
    offset_v: float = 0.0
    wrap_s: str = "repeat"                 # "repeat" | "clamp" | "mirror"
    wrap_t: str = "repeat"

@dataclass
class SurfaceMaterial:
    shader: SurfaceShader | None = None
    textures: list[SurfaceTexture] = field(default_factory=list)

def surface_material(
    obj: SurfaceMaterial | SurfaceShader | SurfaceTexture
       | list[SurfaceTexture] | tuple[SurfaceTexture, ...] | None = None,
) -> SurfaceMaterial: ...                  # normalizes convenience inputs
```

`SurfaceTexture.to_dict()` emits `{id, uniform, width, height, channels, dtype,
source, repeat_u, repeat_v, offset_u, offset_v, wrap_s, wrap_t}` (image meta from
`ImageData`; `codec` stays in the binary frame header, not here).

### Semantics (exact)

| Inputs | Behavior |
|--------|----------|
| no `surface` | existing standard `MeshPhongMaterial` (unchanged) |
| `textures` only (≥1) | **first texture only** → standard texture map (`material.map` + UV wrap/repeat/offset) |
| `shader` only | shader replaces the standard shader (no textures) |
| `shader` + `textures` | shader replaces the standard shader; each texture bound to its `uniform` sampler |

### Wire (`ent.style.surface`)

```json
{
  "shader": null | { "name": "...", "fragment": "...", "vertex": null | "...",
                     "uniforms": { "u_scale": 8.0 } },
  "textures": [
    { "id": "e3.surface.0", "uniform": "uTexture0",
      "width": 512, "height": 512, "channels": 3, "dtype": 0, "source": "data",
      "repeat_u": 1.0, "repeat_v": 1.0, "offset_u": 0.0, "offset_v": 0.0,
      "wrap_s": "repeat", "wrap_t": "repeat" }
  ]
}
```

### Standard texture shader lighting (documented, reusable)

- The surface fragment host always injects `shader-lighting.js::lightPreamble`,
  which declares `MAX_LIGHTS`, `uniform int uLightCount;`,
  `uniform vec3 uLightDir[MAX_LIGHTS];`, `uniform vec3 uLightColor[MAX_LIGHTS];`,
  `uniform vec3 uAmbientColor;` and is populated by `setLightUniforms(...)` from
  the scene's global lighting.
- The standard texture shader shades `texture2D(uTexture, vUv).rgb` with ambient
  + directional diffuse (`u_color * (uAmbientColor + Σ uLightColor·max(N·L,0))`).
- Custom surface shaders may reference the same light uniforms directly; the host
  supplies them.  `vUv`, `vNormal`, `vWorldPosition`, `vLocalPos` are provided.

### Shader error pathway

- `three-view.js` installs `renderer.debug.onShaderError` →
  `sendLog('error', 'Shader compile failed', { source: 'shader', data: { error } })`.
- `Visualizer.on_shader_error(handler)` = `on_client_log` filtered to
  `record.source == "shader"`.

## Decisions (confirmed)

- **Scope of "surface entities":** `Plane`, `Sphere`, `Ellipsoid`, `Disk`, `Box`,
  `Cylinder`, `Cone` (confirmed with the user).  `PartialDisk`/`RegularPolygon`
  are out of scope (non-goal).
- **Image delivery:** reuse the binary frame pipeline (`ImageData` +
  `encode_image_frame`); codec optional, default JPEG for `uint8` 1/3-channel.
- **Multiple textures + no shader:** only the first texture is used.
- **Shader + textures:** the user is responsible for matching sampler `uniform`
  names in the shader to the supplied `SurfaceTexture.uniform`s.
- **Lighting:** standard + custom surface shaders share `shader-lighting.js`.
- **Errors:** reuse `sendLog` → `on_client_log` → `show_banner` (no new wire channel).

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-python-surface-material-model.md](./01-python-surface-material-model.md) | `surface/` subpackage, standard shaders, style `surface` field, serializer/export |
| 2 | [02-frame-delivery-and-add-api.md](./02-frame-delivery-and-add-api.md) | `Scene.surface_texture_frames()` + `viz.add(surface=…)` convenience + frame wiring |
| 3 | [03-frontend-surface-material.md](./03-frontend-surface-material.md) | `surface-shader.js` + `surface-material.js` (GLSL + texture binding) |
| 4 | [04-renderer-integration.md](./04-renderer-integration.md) | Seven solid renderers branch on `ent.style.surface`; bundle regen |
| 5 | [05-shader-error-reporting.md](./05-shader-error-reporting.md) | `shader-error.js` + `debug.onShaderError` → `sendLog` + `viz.on_shader_error` |
| 6 | [06-example-scripts.md](./06-example-scripts.md) | Texture-switch example + shader-error banner example |
| 7 | [07-docs-changelog.md](./07-docs-changelog.md) | Developer docs + user docs + changelog |

## Testing as you go

- `uv run pytest py/tests/viz -q` — Python regression.
- `uv run ruff check .` / `uv run ty check` — lint + type gates.
- `node js/dev/tests/check-syntax.mjs` — frontend syntax gate.
- `node --test js/dev/tests/*.test.mjs` — JS unit tests.
- `uv run python tools/build-viewer-js.py --check` — bundle drift gate (after template edits).
- `uv run mkdocs build --strict` — docs gate (phase 7).
- Manual smoke: `uv run python py/examples/viz/surface/texture_mapping.py` (phase 6).
- Manual smoke: `uv run python py/examples/viz/surface/shader_errors.py` (phase 6).

## Non-goals

- No tiled-pyramid surface textures (single binary frame only in v1).
- No `PartialDisk`/`RegularPolygon`/`Space`/`Arc` surface mapping.
- No point/spot light changes — global lighting is already in place; we only consume it.
- No change to the analytic ray (`ray.js`) or SDF proxy shaders beyond the existing
  global error hook catching their compile failures.

