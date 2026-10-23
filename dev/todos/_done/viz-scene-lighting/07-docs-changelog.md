# Phase 7 — Docs + changelog

> **Architecture note — check the developer docs.** This phase updates the
> developer docs to record the new per-scene lighting contract.  Follow
> `dev/workflows/changelog.md` for the changelog file and
> `dev/workflows/pull-request.md` for opening the PR.

## Goal

Document the scene-lighting feature (developer + user docs) and write the branch
changelog so the work is reviewable and releasable.

## Files

- **Edit** `docs/dev/architecture/viz-architecture.md` — add a short "Scene
  lighting" subsection under the scene-config part: `SceneConfig.lighting` →
  `scene_config.lighting` wire shape, the shared `shader-lighting.js` module, and
  that the standard renderer + SDF + depth surface all consume it.
- **Edit** `docs/py/viz/image/depth-image.md` — document the new `shininess` /
  `specular` style fields and the lit "plain" mode.
- **Edit** `docs/py/viz/image/index.md` — add/refresh a link to the lighting note
  if it fits the existing structure.
- **Regenerate** example docs for the new `py/examples/viz/lighting/` example
  (and any edited example) so it appears in the gallery.
- **New** `docs/changelog/<date>_<scope>-scene-lighting.md` — per the changelog
  workflow (scope/type naming from `dev/workflows/changelog.md`).

## Steps

- [x] 7.1 Update `docs/dev/architecture/viz-architecture.md` (scene lighting
  contract, both the backend field and the frontend shared module; note world
  space + "direction toward the light").
- [x] 7.2 Update `docs/py/viz/image/depth-image.md` (new `DepthImageStyle`
  fields; lit plain-mode screenshot/description if available).
- [x] 7.3 Update `docs/py/viz/image/index.md` if a cross-link is warranted.
- [x] 7.4 Regenerate example docs for the new `py/examples/viz/lighting/`
  example (`uv run python tools/generate-example-docs.py` + `--check`).
- [x] 7.5 Write the changelog file following `dev/workflows/changelog.md`.
- [x] 7.6 Confirm the new example's docstring + `Keywords:` header follow
  `dev/workflows/example-docs.md`.
- [x] 7.7 Run the docs build and the full relevant test gates.

## Validation

```bash
uv run python tools/generate-example-docs.py
uv run python tools/generate-example-docs.py --check
uv run mkdocs build --strict
uv run pytest py/tests/viz -q
node js/dev/tests/check-syntax.mjs
node --test js/dev/tests/*.test.mjs
uv run python tools/build-viewer-js.py
```
