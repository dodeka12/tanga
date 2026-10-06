# Phase 3 — Docs + changelog

## Goal

Document the float tile path and record the change.

## Files

- Edit: `docs/dev/architecture/viz-architecture.md`
- Edit: `docs/py/viz/image/tiled-images.md`
- Edit: `docs/changelog/2026/09/25_fix-image-display.md`

## Steps

- [x] **3.1 — architecture doc**
  - In `viz-architecture.md` (the image-canvas section that describes the tile
    pyramid), note that the pyramid serves `uint8` tiles as JPEG/PNG and
    `float32`/`uint16` tiles as lossless zlib-compressed raw, assembled into a
    float texture so the value range is applied in-shader.

- [x] **3.2 — user doc**
  - In `docs/py/viz/image/tiled-images.md` (the `## Display formats` section),
    note the float path: `float32`/`uint16` tiles stream lossless zlib and
    compose into a float texture, so `u_value_min`/`u_value_max` and
    brightness/contrast use the full dynamic range.

- [x] **3.3 — changelog**
  - Add a `## New Features` bullet to the branch changelog: tiled
    `float32`/`uint16` images now stream lossless zlib tiles into a float
    texture, so brightness/contrast and the value range operate on the full
    dynamic range.

## Validation

```
uv run mkdocs build --strict
```

## Notes

- Keep the changelog title `# Changes since version 2.11.0` (rename only at PR
  time, per `dev/workflows/changelog.md`).

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.
