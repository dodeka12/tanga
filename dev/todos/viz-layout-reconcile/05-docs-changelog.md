# Phase 5 — Docs + changelog

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Update the developer + API docs for the new reconciliation behavior and the
`set_background_image` API, and record the change in the branch changelog.

## Files

- Edit: `docs/dev/architecture/viz-architecture.md`
- Edit: `docs/dev/architecture/viz-controls-and-interactions.md`
- Edit: `docs/py/viz/ui/layouts.md` (or `control-views.md`) — API reference
- New: `docs/changelog/2026/09/<DD>_feat-ui-layout-update.md` (per
  `dev/workflows/changelog.md`; `<DD>` = branch start day)
- Edit: `docs/changelog/index.md` (entry added at PR time)

## Steps

- [x] **5.1 — `viz-architecture.md`**
  - Rewrite the "Layout re-push" bullet (currently "reuses existing `ThreeJsView`
    scene panes (keyed by scene name)… only the DOM chrome rebuilds") to describe
    **full reconciliation by stable view id** (all views reused/created/removed by
    diff; `_viewRegistry`; `scene_sync_request` only for newly-introduced scenes).
  - Note the `view_background_image` message next to the "Image background"
    bullet (bytes first, then JSON; no layout re-push).

- [x] **5.2 — `viz-controls-and-interactions.md`**
  - Extend the "Per-pane camera view & visibility" section with
    `Visualizer.set_background_image(view, image)` → `view_background_image`
    (mirroring `view_camera`/`view_viewport`), and note the
    single-`_viewRegistry` reconciliation invariant (identity = `View.id`).

- [x] **5.3 — API reference**
  - Document `set_background_image` alongside `set_view_camera`/`set_viewport`.

- [x] **5.4 — Changelog**
  - Create `docs/changelog/2026/09/24_feat-ui-layout-update.md` with the
    since-version title from `uv run python tools/last-release.py`, and bullets:
    - New feature: layout reconciliation (no full teardown on re-push).
    - New feature: `Visualizer.set_background_image` granular update.
    - New example: `pinhole_calibrated_streaming.py`.
    - Bug fix: multiple panes of the same scene no longer tear down on re-push.

- [x] **5.5 — Regenerate + verify docs**
  - `mkdocs build --strict`, bundle drift check, and example-docs `--check`.

## Validation

```
uv run python tools/last-release.py
uv run python tools/generate-example-docs.py --check
uv run python tools/build-viewer-js.py --check
uv run mkdocs build --strict
uv run pytest py/tests/viz -q
```

## Notes

- The `docs/changelog/index.md` entry is finalized at PR time
  (`dev/workflows/pull-request.md`); the branch changelog filename is
  `DD_feat-ui-layout-update.md` (branch `/` → `-`).
