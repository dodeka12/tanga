# Changes since version 2.10.0 (2.11.0-rc1)

## New Features

- **Layout reconciliation (no full teardown on re-push)** — the frontend now
  reconciles the whole `view_layout` tree by stable view id against a single
  live-view orphan registry (`_viewRegistry`), reusing unchanged scene panes and
  controls and only creating/removing the diff, so reordering a layout re-attaches
  the expensive WebGL panes instead of tearing the whole UI down.
- **Granular background-image update** — `Visualizer.set_background_image(view,
  image)` streams a new `CameraView.background_image` (a binary pixel frame plus a
  `view_background_image` message) without re-pushing the layout, leaving other
  panes untouched.
- **Streaming camera-view example** — `pinhole_calibrated_streaming.py` streams
  random noise at 4 fps into a calibrated 2D pane and swaps the left/right panes
  at runtime via a toolbar button.
- **Enable/disable/hide for entities and controls** — entities can be hidden or
  shown at runtime (`Visualizer.set_visible`/`hide`, `VizSceneHandle.set_visible`/
  `hide`, `VizObjectRef.visible`), action objects can be enabled/disabled
  (`ActSceneObject.set_enabled/enable/disable`), and UI controls can be hidden,
  shown, or greyed out (`ControlView.set_enabled/set_visible` and
  `Visualizer.set_control_enabled/set_control_visible`) — each pushed as a
  granular message (a `visible` aspect patch, an `interaction` re-push, or a
  `control_state` message) with no layout re-push.  See `hide_sphere.py`.

## Bug Fixes

- **Multiple panes of the same scene** — a `view_layout` re-push now reuses every
  scene pane by its stable id (previously keyed by scene name), so two panes of
  the same scene no longer tear down and rebuild an unrelated pane on every
  re-push.

## Refactor

- **JS dev toolchain under `js/dev/`** — `package.json` (esbuild + playwright),
  `node --test` unit tests for the reconciliation/orphan-map core (extracted into
  the pure `views/reconcile.js`), a node syntax gate, and a headless Playwright
  smoke; wired into pre-commit and the PR checklist. JS tests/esbuild/playwright
  do **not** run in GitHub Actions.
