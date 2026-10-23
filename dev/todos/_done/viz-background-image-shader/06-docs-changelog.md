# Phase 6 — Docs + changelog

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md`.  This work **extends** the documented
> `CameraView.background_image` contract and adds the `view_background_uniforms`
> message, so update the developer docs here.

## Goal

Document the new background shader/uniform capability, update the developer-doc
contract, and record the change in a branch changelog.

## Files

- Edit: `docs/dev/architecture/viz-architecture.md`
- New: `docs/py/viz/image/background-shaders.md` (and index it)
- New: `docs/changelog/<YYYY>/<MM>/DD_<branch-name>.md`

## Steps

- [x] **6.1 — Developer docs (`viz-architecture.md`).**
  - In "Image canvas (extension recipe)", note that the shader/uniform state model
    and the default color pipeline are now shared with the background.
  - In "Camera view (extension recipe) / Image background", document:
    `background_image` carries `shader`/`uniforms`; the default background shader
    mirrors the canvas (value-range → brightness/contrast → clamp) inside the
    letterbox/crop quad; and `register_background_shader` / `register_background_uniform`
    / `set_background_uniform` drive it via a granular `view_background_uniforms`
    message (no pixel re-send, no layout re-push).

- [x] **6.2 — User docs (`docs/py/viz/image/background-shaders.md`).**
  - Mirror `docs/py/viz/image/custom-shaders.md`: the shader contract for the
    background (`uImage`, `uCrop`, `uHx`/`uHy`, `uImageAspect`/`uPaneAspect`, plus
    the seeded brightness/contrast/value-range uniforms and any custom uniforms),
    with `register_background_shader`/`register_background_uniform`/
    `set_background_uniform` examples and the ctrl+drag interaction.
  - Link it from `docs/py/viz/image/index.md`.

- [x] **6.3 — Changelog.**
  - Run `uv run python tools/last-release.py`; create
    `docs/changelog/<year>/<month>/DD_<branch-name>.md` per
    `dev/workflows/changelog.md`, titled `# Changes since version <last-stable> (<last-rc>)`.
  - Add a `## New Features` bullet: calibrated `CameraView.background_image`
    supports a brightness/contrast default shader and custom shaders/uniforms,
    adjustable via ctrl+left-drag in `calibrated_labeling_app.py`.

- [x] **6.4 — Build.**
  - `uv run mkdocs build --strict`.

## Validation

`uv run mkdocs build --strict`

## Notes

- Changelog naming/renaming (branch name → squashed-hash) is finalised at PR time
  per `dev/workflows/pull-request.md`; this phase only creates the branch file.
- Update the `README.md` `Status:` to `Done` when this phase (and the whole plan)
  is complete, per `dev/workflows/implement-plan.md`.
