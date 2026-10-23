# Phase 7 — Developer docs + user docs + changelog

> **Architecture note — check the developer docs.** This phase updates the
> developer docs that the earlier phases noted.  Follow `dev/workflows/changelog.md`
> for the branch changelog and `dev/workflows/pull-request.md` for the final
> rename; follow the existing `mkdocs.yml` nav and `docs/py/viz/` page style for
> the user docs.

## Goal

Document the new surface-material contract, the reusable lighting uniforms for
custom shaders, and the shader-error pathway; add a user-facing page; write the
branch changelog.

## Files

- **Edit** `docs/dev/architecture/viz-architecture.md`
- **Edit** `docs/dev/architecture/viz-controls-and-interactions.md`
- **New** `docs/py/viz/surface/index.md` (or extend `docs/py/viz/styling/…` / `entities/…` as fits the existing nav)
- **Edit** `mkdocs.yml` — nav entry
- **New** `docs/changelog/2026/10/DD_<branch-name>.md` (per `changelog.md`)

## Steps

- [x] **7.1 — developer docs**
  - `viz-architecture.md`: add an "Extension recipe — surface material" note covering the `surface` style field, `surface-shader.js`/`surface-material.js`, image-frame delivery via `surface_texture_frames()`, and the documented lighting-uniform contract.
  - `viz-controls-and-interactions.md`: extend the `client_log` bullet to note the `source: "shader"` shader-error convention and `Visualizer.on_shader_error`.

- [x] **7.2 — user docs**
  - Add a page under `docs/py/viz/` describing `SurfaceMaterial`/`SurfaceShader`/`SurfaceTexture`, the standard shaders (`checkerboard`, `sphere_coloring`, …), the texture-vs-shader-vs-both semantics, the light uniforms available to custom shaders, and the `on_shader_error` banner pattern.
  - Add the page to `mkdocs.yml` nav (match the existing `docs/py/viz/*` structure).

- [x] **7.3 — changelog**
  - Create the branch changelog per `dev/workflows/changelog.md`:
    - title from `uv run python tools/last-release.py`,
    - `## New Features` bullets for surface texture mapping + standard/custom shaders + shader-error reporting.
  - (At PR time, rename to the squashed-commit hash and update `docs/changelog/index.md` per `pull-request.md`.)

- [x] **7.4 — final validation gate**
  - Run the full gate (tests, lint, ty, JS tests, syntax, bundle `--check`, docs `--strict`).

## Validation

```bash
uv run mkdocs build --strict
uv run python tools/build-viewer-js.py --check
uv run pytest -rs
uv run ruff check .
uv run ty check
node --test js/dev/tests/*.test.mjs
node js/dev/tests/check-syntax.mjs
```

## Notes

- Bump the `README.md` `**Status:**` line as phases complete (`Planned` →
  `In progress` → `Done`); this phase marks the plan `Done`.
