# Phase 5 — Docs + changelog

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` (the `DepthImage` section) and
> `docs/py/viz/image/depth-image.md`.  This phase updates user docs and adds the
> changelog; it does not change architecture.

## Goal

Document the new style field and the live `u_max_stretch` uniform, and add the
branch changelog.

## Files

- Edit `docs/py/viz/image/depth-image.md`
- Edit `docs/changelog/2026/10/20_fix-image-layers.md` (append to the branch changelog)

## Steps

- [x] **5.1 — User docs**
  - In `docs/py/viz/image/depth-image.md`, add a `max_grazing_angle` row to the
    `DepthImageStyle` table (degrees, `None` = off, `u_max_stretch = tan(angle)`).
  - Add a short "Depth-jump filter" paragraph and a `ref.set_uniform("u_max_stretch", …)`
    live-update snippet under "Live uniforms and custom shaders".

- [x] **5.2 — Branch changelog**
  - Append a `## New Features` section to the existing branch changelog
    `docs/changelog/2026/10/20_fix-image-layers.md` (this plan runs on
    `fix/image-layers`, which already has a `Bug Fixes` section for this branch).
  - Bullet: `DepthImageStyle(max_grazing_angle=…)` + the live `u_max_stretch`
    uniform (self-contained, ~80-col wrapped).
  - Leave `docs/changelog/index.md` for PR time (`dev/workflows/pull-request.md`).

## Validation

```bash
uv run mkdocs build --strict
uv run ruff check .
uv run ty check
```

## Notes

- Do not hand-edit `docs/changelog/index.md` yet — that is part of the PR
  workflow (squash → hash rename → index entry).
- Because the plan runs on `fix/image-layers`, integrate into that branch's
  existing changelog file rather than creating a new one (see
  `dev/workflows/changelog.md`).
