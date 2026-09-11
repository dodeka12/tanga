# Phase 7 — Extract `viewer.js` into `ThreeJsView` (backward compatible)

## Goal

Turn the single-scene rendering logic in `viewer.js` into a reusable
`ThreeJsView extends View`, driven by a single-instance bootstrap so the
existing single-scene viewer keeps working unchanged.

## Steps

- [x] **7.1 — `templates/views/three-view.js`**
  - `ThreeJsView extends View`; constructor `(sceneName, ws)`.
  - Moved scene/camera/renderer/CSS2D/controls/`sceneObjects` map +
    `buildSceneObject`/`_upsertObject`/`_applyObjectPatch`/`_removeSceneObject`/
    `fitCamera`/per-scene `handleMessage` logic out of `viewer.js` into the
    class (plus `clearAll`, `resize`, `render`, title/annotation overlays).
  - `_onExtentChanged` → `view_mode.handleResize`; `render()` → controls.update +
    tweens + `renderer.render` + label render.

- [x] **7.2 — `viewer.js` becomes a single-view bootstrap**
  - Instantiate ONE `ThreeJsView` for `_myScene`; keep WS connect/reconnect,
    status, screenshot, animation-stop keybinding, and the single `rAF` loop
    calling `view.render()`; scene messages are routed to the view
    (single-scene `_forMyScene` filter stays in the bootstrap).
  - No behavior change yet (multi-view comes in Phase 9).

- [x] **7.3 — Regression smoke**
  - `node --input-type=module --check` passes for all touched JS files.
  - `uv run pytest py/tests/viz/ -q` → 558 passed (server + frontend-shape +
    serialization regression).
  - Manual browser check still pending (no headless browser in the repo);
    `dev/src/test_viz_smoke.py` has a pre-existing syntax error unrelated to
    this change.

- [x] **7.4 — Validate**
  - `uv run pytest py/tests/viz/ -q` (558 passed) + JS syntax check.

## Validation

`uv run pytest py/tests/viz/ -q` (558 passed) + `node --input-type=module --check`
on all touched JS files. Manual browser verification deferred (no headless
browser; the `dev/src/test_viz_smoke.py` script is pre-existing broken).

## Notes

- Pure refactor: same wire messages, same scene registry. This must land before
  Phase 9 so the multi-view bootstrap only *composes* an already-working view.
