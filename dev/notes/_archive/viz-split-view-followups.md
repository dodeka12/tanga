# Viz split-view follow-ups (A / B / C)

Notes from the split-view + stack/controls work. Kept for later.

## A — Wire the demo controls (done)

`py/examples/viz/demo_split_view.py` now wires its controls so they have an
effect:

- `SliderView("radius", …, on_change=…)` → `viz.update_entity("sphere", Sphere(…, radius=value))` + `viz.flush()`.
- `ButtonView("btn_fit", on_click=…)` → `viz.flush(fit_camera=True)` (auto-fit the camera to the scene contents).
- `ButtonView("btn_reset", on_click=…)` → `viz.set_camera(CameraConfig3d(position=…, target=…))` (re-apply a fixed default camera).

No dedicated `reset_camera()`/`fit_camera()` methods exist; "fit camera" is a
`fit_camera=True` flag on `flush()`/`_flush_scene`, and "reset" is
`set_camera(<config>)`.

## B — Same scene in multiple views (works, one gap) (done)

Multiple `SceneView("main")` panes already render the same scene with
**independent** orbit/zoom (each pane is its own `ThreeJsView`: own scene,
camera, renderer, controls; the router broadcasts that scene's messages to all
its panes). The server subscribes only once (scenes are deduped).

The gap is closed: `SceneView(scene, camera=…)` accepts a per-pane initial
camera (a `CameraConfig` or `View2DConfig`/`View3dConfig`), serialized as the
`scene_view` node's `camera` field and applied by `ThreeJsView` in
`_applySceneConfig` (overriding the scene's own camera).  A pane can also be
re-aimed at runtime via `Visualizer.set_view_camera(view, camera)`, routed to
the matching pane by the pane's stable `id` (a new `view_camera` message +
`view_id → ThreeJsView` map).

## C — Standalone HTML export of a split view (not yet)

`viz.export_snapshot()` only exports a **single** scene, via a separate static
figure renderer (`_figure_html.render_figure`) — not the interactive
`viewer.js`/`views/` frontend. `view_layout` + multi-scene state are
server/WebSocket-only today.

Feasible plan: embed `view_layout` + all referenced scenes' `full_state()` into
a standalone page and run the existing frontend in a "static data, no
WebSocket" mode (controls render, events no-op).
