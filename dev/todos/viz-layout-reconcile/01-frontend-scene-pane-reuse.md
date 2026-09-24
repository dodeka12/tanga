# Phase 1 — Reuse scene panes by view id (A)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Make a `view_layout` re-push reuse **every** `ThreeJsView` scene pane (not just
the first per scene name) by keying reuse on the pane's stable `id`
(`sv0`/`sv1`…). This is the minimal fix for the reported "right pane vanishes
then reappears" glitch, which happens when two `SceneView("world")` panes share
a scene name and the scene-name-keyed map only keeps the first one.

## Files

- Edit: `py/pytanga/viz/templates/viewer.js`
- Edit: `py/pytanga/viz/templates/views/build.js`

## Steps

- [x] **1.1 — Build the reuse map from `_viewById` (`viewer.js`)**
  - In `_buildLayout`, replace the scene-name-keyed loop (currently
    `for (const [scene, route] of _sceneRoutes) for (const v of route.sceneViews)
    if (!reuse.has(scene)) reuse.set(scene, v)`) with a view-id-keyed map built
    from the *previous* `_viewById`:
    `const reuse = new Map(); if (_layoutRoot) { for (const [id, v] of _viewById) reuse.set(id, v); }`
  - `skip` stays `new Set(reuse.values())`. (`_viewById` still holds the prior
    panes at this point — it is reset a few lines later.)

- [x] **1.2 — Look up reuse by `node.id` (`build.js`)**
  - In the `scene_view` branch, change
    `let view = (reuse && reuse.get(sceneName)) || null` →
    `let view = (reuse && reuse.get(node.id)) || null`.
  - Change `reuse.delete(sceneName)` → `reuse.delete(node.id)`.
  - Keep the existing reuse body (clearOverlays + setLock/setNavigation/
    setControls/setViewport/setBackgroundImage/setVisibilityFilter +
    applySizeSpecs) unchanged.

- [x] **1.3 — Rebuild + validate**
  - Run the validation command; confirm the viz suite passes.

## Validation

```
uv run pytest py/tests/viz -q
```

## Notes

- This phase is a stepping stone: Phase 3 generalizes this ad-hoc `reuse` map
  into the persistent `_viewRegistry` and reconciles all view types.
- `collectViewByIds` (`build.js`) already keys `view_id → ThreeJsView` with
  `view.viewId = node.id`, so the ids line up.
- Reusing by `id` only preserves a pane if the app reuses the same `SceneView`
  object across `set_layout`; that is the intended contract.
- **Live frontend, not the bundle.** `templates/viewer.js` + `templates/views/`
  are served directly by the server (static ES modules) and are **not** part of
  `js/tanga-viewer.js` (which bundles only the export renderer library via
  `build-viewer-js.py`). So the gate here is `pytest py/tests/viz`; use
  `node --input-type=module --check <file>` for a syntax check where node is
  available.

