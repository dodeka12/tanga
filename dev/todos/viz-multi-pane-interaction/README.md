# Viz Multi-Pane Interaction, Plot Scaling & Example — Overview

**Created:** 2026-08-31 | **Status:** Done | **Branch:** `fix/scene-alert`

## Goal

1. Make pointer interaction (draggable `ActPoint`s, hover, click, scroll) work
   **independently in every `SplitView` pane**, instead of the current
   frontend singleton that leaves only one pane interactive.
2. Make 2D `CoordinateSystem` panes render at the correct scale inside a
   `SplitView` (the 2D orthographic frustum must use the pane's aspect ratio,
   not the whole window's).
3. Let a named scene opt out of the generic default `Axes2D`/`Grid` so a
   `CoordinateSystem` pane does not draw a duplicate grid/axes underneath its
   own, correctly-scaled ones.
4. Expose the `xlim`/`ylim` → `View2DConfig` fit computation as a reusable
   helper so an app can embed an exact per-pane camera at layout-construction
   time (before `run()`).
5. Add a runnable `VisualizerApp` example (`py/examples/viz/app/`) that
   exercises all of the above and doubles as a manual test bed.

## Background

Three reference sources:

- The requested example: a horizontal `SplitView` whose left pane is a vertical
  `SplitView` of two 2D plots (`sin`/`cos`) and whose right pane is a 2D view
  with four `ActPoint`s connected by lines (dragging a point updates the
  adjacent lines). One graph pane additionally carries an `ActPoint` that
  specifies the `sin` amplitude.
- `dev/todos/pytanga-splitview-scene-init-camera-grid.md` — the same use case,
  reporting (a) a duplicate grid/axes under each `CoordinateSystem` and (b) a 2D
  camera that does not auto-fit to `xlim`/`ylim`.
- Root-cause analysis: `templates/interaction.js` is a module singleton
  (`camera`, `rendererDomElement`, `controls`, `ws`, `_spaceDim`, and one
  `interactiveObjects` map) that `ThreeJsView._initScene()` re-initialises per
  pane (`views/three-view.js:194`); `templates/view_mode.js` `switchToCamera()`
  computes the 2D frustum from `window.innerWidth / window.innerHeight`.

## Architecture (short)

- **Frontend interaction:** convert `interaction.js` into an
  `InteractionController` class; each `ThreeJsView` owns one instance so
  `camera`/`domElement`/`controls`/`ws`/`spaceDim`/object registry/drag state
  are all per-pane. `viewer.js` single-scene mode reuses the same controller
  through `view.setWebSocket(ws)`.
- **Frontend camera:** `switchToCamera` takes an optional pane aspect; the 2D
  orthographic frustum is computed from it (window aspect only as a fallback).
- **Python defaults:** `Visualizer.scene(name, *, add_axes, add_grid)` passes a
  per-scene override to the existing `_add_default_scene_objects`.
- **Python fit helper:** a module-level `fit_view2d(...)` in
  `_coordinate_system.py` becomes the single source of truth for the 2D fit
  camera; `CoordinateSystem._apply_camera` calls it.

## Decisions (confirmed)

- **Interaction state becomes per-pane.** `InteractionController` public surface
  is fixed as:

  ```js
  export class InteractionController {
    constructor(camera, rendererDomElement, controls, websocket)
    setSpaceDim(dim)
    setCamera(camera)
    setWebSocket(websocket)
    registerInteractive(objectId, mesh, config)
    unregisterInteractive(objectId)
    clearAllInteractive()
  }
  ```

  No module-level interaction state remains; `viewer.js` drops its
  `setInteractionWebSocket` import. JSON payload shapes are unchanged.
- **`switchToCamera(camera, controls, spaceDim, cameraConfig, viewAspect = null)`**
  uses `viewAspect` when it is a finite positive number, else
  `window.innerWidth / window.innerHeight`. `ThreeJsView._applyCamera` passes
  `this.width / this.height` when both are measured (`> 0`).
- **`Visualizer.scene(name, *, enable_server_stop_key=False, add_axes=True, add_grid=True)`.**
  Defaults `True` preserve current behaviour (use the constructor flags);
  `False` suppresses that default object for a *newly created* scene. The main
  scene `""` is created in `__init__` and keeps using the constructor flags.
- **`fit_view2d(xlim, ylim, *, xscale="linear", yscale="linear", base=10.0, border_world=0.0, border_px=0.0, uniform=True) -> View2DConfig`**
  returns `View2DConfig(xmin=-span_x/2, xmax=span_x/2, ymin=-span_y/2, ymax=span_y/2, ...)`
  where `span = make_scale(s, base).to_world(hi) - make_scale(s, base).to_world(lo)`.
  `xscale`/`yscale` are `Scale | str`. `CoordinateSystem._apply_camera` calls
  `fit_view2d` so the two never drift. Exported from `pytanga.viz`.
- **Example layout is fixed:**
  `SplitView("horizontal", [SplitView("vertical", [SceneView("sin"), SceneView("cos")]), SceneView("")])`,
  `space_dim=2`, `add_default_axes=False`, `add_default_grid=False`. The `sin`
  pane additionally holds an amplitude `ActPoint` whose Y coordinate drives the
  `sin` amplitude and re-plots the curve.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-interaction-per-pane-controller.md](./01-interaction-per-pane-controller.md) | Refactor `interaction.js` into a per-view `InteractionController` |
| 2 | [02-view2d-pane-aspect.md](./02-view2d-pane-aspect.md) | Use the pane aspect for 2D frusta in `switchToCamera` |
| 3 | [03-scene-defaults-opt-out.md](./03-scene-defaults-opt-out.md) | Per-scene `add_axes`/`add_grid` on `Visualizer.scene()` |
| 4 | [04-fit-view2d-helper.md](./04-fit-view2d-helper.md) | `fit_view2d` helper + reuse in `CoordinateSystem._apply_camera` |
| 5 | [05-example-split-view-app.md](./05-example-split-view-app.md) | The `py/examples/viz/app` reproduction/test-bed example |
| 6 | [06-docs-changelog.md](./06-docs-changelog.md) | Docs for the new features + example docs + changelog |

## Testing as you go

- `uv run pytest py/tests/viz -q` (every Python phase)
- `uv run ruff check py/pytanga/viz/ py/examples/viz/ py/tests/viz/`
- `node --check py/pytanga/viz/templates/interaction.js` (also `view_mode.js`,
  `views/three-view.js`, `viewer.js`) — JS syntax gate for phases 1–2.
- `uv run python tools/generate-example-docs.py --check` +
  `uv run mkdocs build --strict` (phases 5–6).

## Non-goals

- No wire-protocol change (JSON shapes for interaction/config/camera unchanged).
- No change to the other singleton modules (`controls-panel.js`, `banner.js`,
  `file-browser.js`, `editor.js`) unless a phase explicitly says so.
- No new JS test framework; JS validation is `node --check` plus the runnable
  example plus the existing Python export/viz tests.
- No behavioural change to the `reuse_existing`/server lifecycle.
