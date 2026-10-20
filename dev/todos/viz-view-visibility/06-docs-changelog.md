# Phase 6 — Developer docs + example docs + changelog

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Update the developer docs for the changed visibility contracts, regenerate the
public example docs, and add the branch changelog.

## Files

- Edit: `docs/dev/architecture/viz-architecture.md`
- Edit: `docs/dev/architecture/viz-controls-and-interactions.md`
- Generated: `docs/py/examples/**` (via `tools/generate-example-docs.py`)
- New: `docs/changelog/2026/10/DD_viz-view-visibility.md`

## Steps

- [x] **6.1 — Developer docs**
  - `viz-architecture.md`: replace the `SceneView(hide=…, show=…)` "Per-pane
    visibility" bullet with the new model — `visible_in` add-time scope,
    `SceneView.set_visible` → `view_visibility`, and `Scene.set_visible` global.
  - `viz-controls-and-interactions.md`: describe `view_visibility` next to
    `view_camera`/`view_viewport`/`view_background_image`.
- [x] **6.2 — Example docs**
  - Run `uv run python tools/generate-example-docs.py`.
- [x] **6.3 — Changelog**
  - Create the branch changelog per `dev/workflows/changelog.md` (title from
    `uv run python tools/last-release.py`).
- [x] **6.4 — Validate**
  - Example docs, bundle drift, and MkDocs build.

## Validation

`uv run python tools/generate-example-docs.py --check && uv run python tools/build-viewer-js.py --check && uv run mkdocs build --strict`
