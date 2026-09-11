# Phase 6 — Docs & changelog

## Goal

Document the new features, regenerate the example docs so the new example
appears in the gallery, and record everything in the branch changelog.

## Files

- Edit: `docs/py/viz/plotting/coordinate-system.md` (document `fit_view2d`)
- Edit: `docs/py/viz/visualizer/multi-scene.md` (document `scene(..., add_axes=, add_grid=)`)
- Edit: `docs/py/viz/visualizer/split-views.md` (per-pane interaction + pane-aspect 2D cameras)
- Edit: `docs/py/viz/app/layouts.md` (cross-link the new example)
- Edit: `docs/changelog/2026-08-31_fix-scene-alert.md` (branch changelog)

## Steps

- [x] **6.1 — Document `fit_view2d` in the coordinate-system docs**
  - Add a subsection showing `fit_view2d(xlim, ylim)` and the
    `SceneView(name, camera=fit_view2d(...))` + `CoordinateSystem(..., camera=False)`
    pattern for embedding an exact plot camera at layout-construction time.
- [x] **6.2 — Document per-scene grid/axes opt-out**
  - In `multi-scene.md`, document `scene(name, add_axes=False, add_grid=False)`
    and the app-level `add_default_axes`/`add_default_grid` flags for
    `CoordinateSystem`-backed plot scenes.
- [x] **6.3 — Note per-pane interaction and pane-aspect cameras**
  - In `split-views.md` (and/or `app/layouts.md`), note that interactive objects
    (`ActPoint`) now work independently in each pane, and that 2D panes use
    their own aspect ratio for camera framing.
- [x] **6.4 — Regenerate example docs**
  - Run `uv run python tools/generate-example-docs.py` so
    `py/examples/viz/app/split_view_app.py` gets a docs page + nav entry.
- [x] **6.5 — Add the branch changelog entry**
  - Append a `## New Features` / `## Bug Fixes` section to
    `docs/changelog/2026-08-31_fix-scene-alert.md` covering: per-pane
    interaction, pane-aspect 2D framing, per-scene grid/axes opt-out,
    `fit_view2d`, and the new example.

## Validation

`uv run python tools/generate-example-docs.py --check && uv run mkdocs build --strict`

## Notes

- The changelog is renamed to its hash-based form and indexed in
  `docs/changelog/index.md` only at PR time (`dev/workflows/pull-request.md`).
