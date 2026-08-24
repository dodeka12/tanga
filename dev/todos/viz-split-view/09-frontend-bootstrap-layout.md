# Phase 9 — Multi-view bootstrap + scene routing

## Goal

Build the `View` tree from `view_layout`, route scene-tagged WS messages to the
matching pane, and run one render loop over all `ThreeJsView`s. Scene URLs keep
working via the single-view path.

## Steps

- [x] **9.1 — `viewer.js` mode detection**
  - `?view=<name>` (param present) → layout mode; otherwise single-scene mode
    (existing path unchanged).

- [x] **9.2 — Tree materialization**
  - `views/build.js` maps `view_layout` node types →
    `SplitView`/`ThreeJsView`/`ControlGroupView`/`SpacerView`; `collectSceneRoutes`
    builds `{ scene → {sceneViews, controlViews} }`.

- [x] **9.3 — WS routing**
  - `ready` sends `{type: "ready", layout: name}` in layout mode.
  - `_routeToScene` routes scene-tagged messages to the bound view(s);
    `controls_define`/`controls_clear` go to the scene's `ControlGroupView`s
    (falling back to its `SceneView`); `clear_all` broadcasts to every pane.

- [x] **9.4 — Single render loop**
  - One `rAF` loop renders the single view (single-scene) or iterates all
    `ThreeJsView`s (layout).

- [x] **9.5 — `viewer.html` loads the `views/` modules**
  - No change needed: `viewer.js` imports `views/*` transitively; the importmap
    already maps `three`/`three/addons/`.

- [x] **9.6 — End-to-end**
  - WS-level check (aiohttp client): `ready {layout:"demo"}` → server sends
    `view_layout` + `scene_config`/`scene_update` for both scenes, then
    `scene_list` (verified). Browser rendering itself deferred (no headless
    browser).

- [x] **9.7 — Validate**
  - `uv run pytest py/tests/viz/ -q` (558 passed) + `node --test
    'dev/src/js-tests/*.test.mjs'` (18 passed) + JS syntax check. Manual
    drag/nest/fixed checks deferred.

## Validation

`uv run pytest py/tests/viz/ -q` (558 passed) + `node --test 'dev/src/js-tests/*.test.mjs'`
(18 passed) + `node --input-type=module --check` on all touched JS files + a
WS-level layout handshake check. Manual browser verification deferred.

## Notes

- `scene_synced` is acked per-scene by each `ThreeJsView`; the server's
  `_signal_ws_ready` is idempotent, so the first ack unblocks `start()`.
