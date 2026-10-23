# Phase 7 — Docs + changelog

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md`.  This work **adds a new entity
> kind and a new granular message**, so update the developer docs here.

## Goal

Document the `depth_image` entity and its shader/uniform contract, update the
developer-doc entity recipe, and record the change in a branch changelog.

## Files

- Edit: `docs/dev/architecture/viz-architecture.md`
- New: `docs/py/viz/image/depth-image.md` (and index it in
  `docs/py/viz/image/index.md`)
- New: `docs/changelog/<YYYY>/<MM>/DD_feat-depth-image.md`
- Regenerate: `docs/py/viz/…` example pages (via `generate-example-docs.py`)

## Steps

- [x] **7.1 — Developer docs (`viz-architecture.md`).**
  - In "New entity kind", add `depth_image` to the payload-style entities
    (with `image`): a `VizDepthImage` node carrying `frame`/`depth`/`image`/
    `segmentation`/`shader`/`mesh`/`uniforms`, pixels as binary frames, and the
    `depth_image_update` granular message for live uniform/segment changes.

- [x] **7.2 — User docs (`docs/py/viz/image/depth-image.md`).**
  - Document `DepthImageData`/`DepthImage`/`DepthImageStyle` +
    `DepthImageMode`/`DepthColormap`, the `viz.add`/`viz.new` usage, the
    shader/uniform contract (always-provided varyings `vUv`/`vDepth`/`vValid`
    and uniforms `uDepth`/`uSegMask`/`uImage0`/`uDepthSize`/`uImageSize` +
    `tangaSegmentSelected`), and the segmentation-filtering workflow.
  - Link it from `docs/py/viz/image/index.md` and the mkdocs nav (if needed).

- [x] **7.3 — Example docs regeneration.**
  - `uv run python tools/generate-example-docs.py` then `--check` so the new
    example appears in the gallery.

- [x] **7.4 — Changelog.**
  - Run `uv run python tools/last-release.py`; create
    `docs/changelog/<year>/<month>/DD_feat-depth-image.md` per
    `dev/workflows/changelog.md` (branch name → `feat-depth-image`), titled
    `# Changes since version <last-stable> (<last-rc>)`, with a `## New Features`
    bullet for the `depth_image` entity.

- [x] **7.5 — Build + status.**
  - `uv run mkdocs build --strict`; mark the `README.md` `**Status:**` → `Done`.

## Validation

`uv run mkdocs build --strict && uv run python tools/generate-example-docs.py --check`

## Notes

- Changelog rename (branch → squashed-hash) happens at PR time per
  `dev/workflows/pull-request.md`; this phase only creates the branch file.
