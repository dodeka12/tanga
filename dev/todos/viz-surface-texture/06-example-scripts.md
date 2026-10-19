# Phase 6 — Example scripts

> **Architecture note — check the developer docs.** Before implementing, check
> `dev/workflows/example-docs.md` (header/`Keywords:` contract) and the existing
> examples under `py/examples/viz/` for the control/layout patterns
> (`docs/dev/architecture/viz-controls-and-interactions.md`).

## Goal

Add two runnable examples: one that switches between standard texture mapping and
a custom texture-mapping shader using two programmatically generated textures,
and one that triggers a shader compile error and shows it in a banner round-trip.

## Files

- **New** `py/examples/viz/surface/texture_mapping.py`
- **New** `py/examples/viz/surface/shader_errors.py`

## Steps

- [x] **6.1 — `texture_mapping.py`**
  - Module docstring per `example-docs.md`: one-line description, `Run with:`, `Keywords:` (e.g. `surface, texture mapping, shader, checkerboard, image, lighting`).
  - Generate two `uint8` RGB textures with numpy (e.g. a gradient and a checker) as `ImageData(id=..., data=..., tile_max_dim=None, tile_max_bytes=None)`.
  - Add a sphere (or plane) whose `surface` is initially a standard texture map (`SurfaceTexture(image=tex0)`), plus a custom shader (`SurfaceShader`/`surface_material`) that samples `tex1` and multiplies by the documented `uAmbientColor`/`uLightDir` lighting.
  - Add a `DropdownView` (or two `ButtonView`s) wired via the unified `(id, event)` control model to switch the entity's `surface` at runtime (re-`add`/`update_entity` with the new `SurfaceMaterial`), so standard ↔ custom texture mapping is demonstrable live.
  - Optionally call `viz.set_scene_lighting(...)` to show the standard texture shader reacting to global lighting.

- [x] **6.2 — `shader_errors.py`**
  - Register `viz.on_shader_error` (or `viz.on_client_log`) with an `async def` handler that calls
    `viz.show_banner(f"**Shader compile failed**\n\n```\n{record.message}\n```", title="Shader error")`.
  - Add an entity with a deliberately invalid custom surface shader (e.g. a syntax error in `fragment`) so the round-trip — frontend `sendLog` → backend `on_shader_error` → `banner_define` — is visibly demonstrated.
  - Module docstring + `Keywords:` (e.g. `shader error, compile error, banner, client log, debug`).

- [x] **6.3 — example docs**
  - Run `uv run python tools/generate-example-docs.py` and `--check`; commit the regenerated gallery + nav.

## Validation

```bash
uv run python tools/generate-example-docs.py --check
uv run mkdocs build --strict
```

## Notes

- Use `uv run python py/examples/viz/surface/texture_mapping.py` (and `shader_errors.py`)
  for a manual browser smoke; the shader-error example must open a browser to
  trigger the compile on first render.
