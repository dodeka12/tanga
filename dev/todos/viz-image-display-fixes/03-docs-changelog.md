# Phase 3 — Docs + changelog

## Goal

Document the minification behaviour for custom shaders and record the fixes in
the branch changelog.

## Files

- Edit: `docs/py/viz/image/custom-shaders.md`
- Edit: `docs/changelog/2026/09/25_fix-image-display.md`

## Steps

- [x] **3.1 — Document custom-shader minification**
  - Add a "Minification & filtering" section to `custom-shaders.md`: image
    textures are mipmapped with linear minification and nearest magnification;
    `texture2D(uImage0, vUv)` inherits it; a manual
    `(floor(vUv * uImageSize) + 0.5) / uImageSize` tap samples level 0 and opts
    out (use `textureLod(uImage0, uv, 0.0)` for an exact LOD-0 tap).
  - Note `uImageSize` is always the level-0 (full-resolution) pixel size.
- [x] **3.2 — Changelog**
  - Update `docs/changelog/2026/09/25_fix-image-display.md` Bug Fixes: correct
    the flip root cause (JPEG `ImageBitmap` path, not `DataTexture`), and add
    bullets for the value-range reset and the minification-filter fix.

## Validation

```
uv run mkdocs build --strict
```

## Notes

- Per `dev/workflows/changelog.md`, the changelog keeps its
  `# Changes since version 2.11.0` title (branch `fix/image-display`); it is
  renamed to the hash form only at PR time.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.
