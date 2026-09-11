# Changes in version 0.5.2

## New Features

- **`ControlEvent` dataclass** — extensible metadata passed to all control
  handlers. Currently carries `browser_id`; additional fields can be added
  without breaking existing handler signatures.  Import from `pytanga.viz`.

- **`get_label_ids(entity_id) → list[str]`** — new method on `Scene`,
  `Visualizer`, and `VizSceneHandle` to look up label IDs attached to an
  entity.  Replaces the removed `(entity_id, label_id)` tuple return from
  `add()`.

- **`flush(fit_camera=True)`** — explicit camera auto-fit.  Call
  `viz.flush(fit_camera=True)` after all entities are added to have the
  frontend adjust the camera to encompass them.  Disabled by default;
  the camera no longer auto-fits on first entity arrival.

## Bug Fixes

- **Unified browser connection detection** across `start()`, `run()`, and
  `VisualizerApp.run()`.  All three now wait for the frontend `"ready"`
  WebSocket round-trip, proving both HTTP page load and WebSocket
  connectivity before proceeding.

- **Fixed browser timeout when GPU crashes** during WebGL initialization.
  `initScene()` is now fault-tolerant: if the WebGL renderer fails, the
  WebSocket still connects and sends the `"ready"` message.

- **Fixed orbit target drifting away from world origin** when entities
  arrived via WebSocket.  The camera orbit point now stays at `(0,0,0)`
  regardless of entity placement.

- **Fixed sphere flickering in animations** caused by floating-point epsilon
  changes in `radius`/`extent` triggering full mesh rebuilds every frame.
  Both live streaming (`inPlaceUpdate`) and animated HTML exports
  (`applyFrameUpdate`) now use tolerance-based comparison (ε = 10⁻⁹).

- **Added missing `reflection_point.js` renderer** for the `ReflectionPoint`
  operator.  Removed stale reference to the non-existent `reflection_origin.js`
  from the export bootstrap renderer list.

- **`add()` return type** is `str` (never `list[str]`).  The
  `(entity_id, label_id)` tuple is no longer returned.  Use
  `get_label_ids(entity_id)` instead.

- Fixed missing comma in `demo_title_annotation.py` and redundant `import math`
  in `two_body_gravity.py`.

## Doc Changes

- Updated `add()` return type and documented `get_label_ids()` in
  `visualizer.md`.
- Updated all control handler signatures in `interactive.md` to use
  the new `(value, event: ControlEvent)` signature.
- Documented `flush(fit_camera=False)` in `visualizer.md`.
- Replaced bare style parameters (`size=0.15`, `wireframe=True`) with
  style classes (`PointStyle(size=0.15)`, `SphereStyle(wireframe=True)`)
  in all example scripts.
- Replaced unicode subscripts with KaTeX math expression strings
  (`$P_1$`, `$\pi$`, etc.) in example labels.