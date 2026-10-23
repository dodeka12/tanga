# Phase 6 — Docs + changelog

> **Architecture note — check the developer docs.** Before writing 6.1, re-check
> `docs/dev/architecture/viz-architecture.md` so the developer doc reflects what
> Phases 1–4 actually built (and update it if the architecture changed).

## Goal

Update the developer architecture doc and the user docs for the new/changed
contracts, and add the branch changelog.

## Files

- Edit: `docs/dev/architecture/viz-architecture.md`
- Edit: `docs/py/viz/image/depth-image.md`
- Edit: `docs/py/viz/image/background-shaders.md` (and/or `image-transport.md`, `image-canvas.md`)
- Edit: `docs/py/viz/ui/runtime-updates.md` (background runtime notes, if applicable)
- New: `docs/changelog/<YYYY>/<MM>/DD_feat-improve-image-views.md` (branch changelog per `dev/workflows/changelog.md`)

## Steps

- [x] **6.1 — Developer architecture doc**
  - Update `viz-architecture.md` "Image background" and "Image canvas (extension
    recipe)" sections: the background `ImageView` now binds to the layout
    transport and pushes its own `view_background_uniforms` /
    `view_background_image` updates; layers are stable-index and capped by a
    serialized `max_layers` (default 8); per-layer `u_layer{i}_colormap` exists;
    the `depth_image` mesh payload may carry `mesh.camera` +
    `mesh.camera_to_world`.

- [x] **6.2 — User docs: depth image pinhole**
  - Extend `docs/py/viz/image/depth-image.md` with a "Pinhole camera mode"
    section: `DepthImageStyle(camera=..., depth_kind=..., apply_pose=...)`, the
    vertex math, and the `CameraCalibration`/`PinholeCamera` convention; add the
    new fields to the `DepthImageStyle` table.

- [x] **6.3 — User docs: layers / colormap / self-push**
  - Note `max_layers` (8) and `ImageColormap` in the image-layer docs; document
    that a 4-channel layer is alpha-composited with `opacity` and blend mode.
  - Document the background self-push API (mutate the `ImageView` directly after
    `set_layout`; `set_layer`/`set_layer_style`/`remove_layer` push granularly).

- [x] **6.4 — Branch changelog**
  - Add `docs/changelog/<YYYY>/<MM>/DD_feat-improve-image-views.md` following
    `dev/workflows/changelog.md` (title via `uv run python tools/last-release.py`;
    `New Features` / `Breaking Changes` / `Bug Fixes` / `Refactor` sections as
    applicable).

- [x] **6.5 — Docs gate**
  - `uv run mkdocs build --strict`.

## Validation

```
uv run mkdocs build --strict
uv run python tools/generate-example-docs.py --check
```

## Notes

- If any Phase 1–4 work turns out to *change* (not just extend) a documented
  architecture contract, that contract update belongs here too — re-check
  `docs/dev/architecture/` before writing 6.1.
- The changelog is renamed to the squashed-commit hash only at PR time
  (`dev/workflows/pull-request.md`); for now use the branch-name file.
