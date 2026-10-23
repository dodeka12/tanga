# Surface opacity semantics — Overview

**Created:** 2026-10-20 | **Status:** Done | **Branch:** `fix/tex`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` (the "Surface material (extension
> recipe)" section — it currently states surface materials are opaque) and
> `docs/py/viz/styling/surface.md` (the user-facing "opaque by default" note).
> This work **corrects** the surface-material opacity contract that the previous
> PR (`feat/tex-map`, #120) introduced; it does not add a new seam or protocol,
> and it updates the two docs above in Phase 5.

## Goal

Fix the surface-material opacity semantics introduced in #120.  Today
`surface-material.js` hard-codes `opacity = 1.0` (textures and custom shaders
are always opaque), the standard texture map drops the texture's alpha channel,
and the solid entities' *default* opacities are `< 1.0`.  Deliver:

1. Default opacity `1.0` for every solid-surface entity (`Plane`, `Sphere`,
   `Ellipsoid`, `Disk`, `PartialDisk`, `Box`, `Cylinder`, `Cone`).
2. The standard texture map multiplies the entity opacity by the texture's
   alpha channel.
3. Custom shaders receive the entity opacity as the `u_opacity` uniform and
   decide how to use it.

## Architecture (short)

- **Python** — `_DEFAULT_STYLE_FOR_KIND` in `py/pytanga/viz/_styles/__init__.py`
  holds the canonical per-kind defaults; the serializer merges them into
  `ent.style.opacity`, which the JS reads via `styleParam(ent, 'opacity', …)`.
- **Frontend** — `surface-material.js` builds the `ShaderMaterial` (currently
  hard-codes `opacity = 1.0`); `surface-shader.js` assembles the GLSL
  (`main()` emits `fragColor = vec4(surfaceColor(...), u_opacity)` and the
  standard map samples `texture2D(uTexture, vUv).rgb`); `utils.js::applyStyleUpdate`
  handles cheap in-place style updates; the eight solid renderers each have a
  `styleParam(ent, 'opacity', <fallback>)` fallback.

## Fixed contract (decided up front — later phases implement against this)

1. **Default opacity 1.0.** All eight solid-surface kinds default to opacity
   `1.0` in both `_DEFAULT_STYLE_FOR_KIND` and the JS renderer fallbacks.
   (Sphere is already `1.0`; `Plane` is `0.3`; Cylinder/Disk/PartialDisk/Box/
   Ellipsoid/Cone are `0.9`.)
2. **Standard texture alpha.** The standard texture map (textures, no custom
   shader) outputs `alpha = u_opacity * texture2D(uTexture, vUv).a`, where
   `u_opacity` is the entity's resolved opacity (default `1.0`).
3. **Shader `u_opacity`.** `createSurfaceMaterial` sets `u_opacity` from the
   entity opacity (not a hard-coded `1.0`); custom shaders receive it and decide
   what to do with it (the host `main()` still applies it as the fragment alpha).
4. **Transparency flags.** `transparent = opacity < 1.0 || hasAlphaTexture`;
   `depthWrite = opacity >= 0.99 && !hasAlphaTexture`.  `hasAlphaTexture` =
   `textures[0].channels === 4` for the standard map, or any bound texture with
   `channels === 4` for the shader path (1/3-channel textures decode with alpha
   1.0 via `image.js::toRgba`, so only 4-channel contributes).
5. **In-place updates.** `applyStyleUpdate` updates the `u_opacity` uniform for
   `ShaderMaterial`s (mirroring `interaction.js`); the material records
   `userData._alphaTexture` at creation so `transparent`/`depthWrite` stay
   correct on color-only updates.

## Decisions (confirmed)

- **`PartialDisk` is in scope for the default-opacity change only.** It renders a
  flat solid surface but has **no** `surface` material field (it renders via
  `makeMaterial` in `partial_disk.js`), so it gets the opacity-1.0 default but no
  texture/shader logic.
- The default-opacity change also affects **plain (untextured)** solids — e.g. a
  default `Plane` becomes opaque.  This is intended.
- No change to `ImageView`/`DepthImage` opacity compositing, SDF/ray proxy
  `uOpacity`, or the `interaction.js` hover path (already reads/writes `u_opacity`).

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-python-default-opacity.md](./01-python-default-opacity.md) | Python canonical defaults → 1.0 + contract test |
| 2 | [02-frontend-fallback-opacity.md](./02-frontend-fallback-opacity.md) | JS renderer fallback defaults → 1.0 + bundle regen |
| 3 | [03-surface-material-opacity.md](./03-surface-material-opacity.md) | `surface-material.js`/`surface-shader.js` opacity + texture alpha |
| 4 | [04-inplace-opacity-update.md](./04-inplace-opacity-update.md) | `applyStyleUpdate` updates `u_opacity` |
| 5 | [05-docs-changelog.md](./05-docs-changelog.md) | User/developer docs + changelog |

## Testing as you go

- `uv run pytest py/tests/viz -q` — Python regression.
- `uv run ruff check .` / `uv run ty check` — lint + type gates.
- `node js/dev/tests/check-syntax.mjs` — frontend syntax gate.
- `node --test js/dev/tests/*.test.mjs` — JS unit tests.
- `uv run python tools/build-viewer-js.py --check` — bundle drift gate (after template edits).
- `uv run mkdocs build --strict` — docs gate (phase 5).
- Manual smoke: `uv run python py/examples/viz/surface/texture_mapping.py` (phase 5).

## Non-goals

- No `surface` texture/shader support for `PartialDisk` (only its default opacity changes).
- No change to `ImageView`/`DepthImage` compositing or SDF/ray proxy opacity.
- No point/spot light changes.
