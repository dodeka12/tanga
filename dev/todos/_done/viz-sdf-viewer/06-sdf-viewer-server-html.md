# Phase 6 — `SdfVisualizer` facade + HTML bootstrap (reuse `server.py`)

**Status:** Done

## Goal

Expose the SDF viewer through the existing visualizer infrastructure: a
`SdfVisualizer` facade on the Python side and an `sdf_viewer.html` that reuses
the existing `viewer.html` bootstrap (CDN import map, status, loading,
error/fallback, reconnect). `server.py` and the WebSocket protocol are shared
unchanged.

## Files

- New: `py/pytanga/viz/sdf/visualizer.py` (`SdfVisualizer`)
- New: `py/pytanga/viz/sdf/__init__.py` (exports)
- New: `py/pytanga/viz/templates/sdf_viewer.html`
- Modify: `py/pytanga/viz/server.py` (route/static-serving registration only —
  behavior unchanged)

## Reuse strategy

- **`server.py`**: reuse the existing `Visualizer` server plumbing. `SdfVisualizer`
  adapts the same scene/update/serialize flow but emits SDF objects (analytic
  trees + `mv_sdf` objects) and a `sdf_viewer_config` message carrying the
  active distance function.
- **HTML**: copy the `viewer.html` head/loading/error/fallback/CDN-probe
  boilerplate verbatim into `sdf_viewer.html`; the only differences are the
  module entry-point scripts (`sdf/sdf_viewer.js` etc.) and a WebGL2
  pre-check.
- **WS protocol**: keep `scene_update` / `object_update` shapes; SDF objects
  are additional `kind`s and the distance function is a new small
  `sdf_viewer_config` message.

## Steps

- [x] `SdfVisualizer` class:
  - [x] Mirrors `Visualizer`'s `add()` / scene-handle API, serializing the six
        supported entities via `sdf/serializer.py` and MVs via
        `sdf/algebra_embedding.py` (Phase 7).
  - [x] Holds the viewer-level `distance` setting (default `"scalar_pseudo"`),
        and `opacity` (default `"step"`), exposed via setters that emit the
        recompile message (distance/opacity are wired only in later phases;
        the facade just exposes the hook in this phase).
  - [x] Reuses the existing server runtime (start/stop/port/static serving),
        switching the served entry page to `sdf_viewer.html`.
- [x] `sdf_viewer.html`:
  - [x] Reuse the `viewer.html` `<head>` + loading/error/fallback/status
        bootstrap.
  - [x] Load `sdf/sdf_viewer.js` (+ `sdf/` modules) instead of
        `viewer.js`/`renderers/`.
  - [x] Add an early WebGL2 capability notice.
- [x] `sdf_viewer.js`:
  - [x] Port the WebSocket client (connect/reconnect/ready/scene messages)
        from `viewer.js`, delegating message handling to the SDF
        scene-builder and the distance-function recompile hook.
- [x] Camera parity (shared `scene_config.camera`, identical to the standard
      viewer):
  - [x] Emit the camera through the same `scene_config.camera` field used by
        `scene.py` / `camera.py` (`CameraConfig3d`), so `sdf_viewer.js` applies
        it via the shared `view_mode.js` `switchToCamera` (3D branch) — no SDF
        fork.
  - [x] `fit_camera` auto-fit is **not** handled here: the standard viewer
        computes a bounding box from meshes the SDF path does not have. This is
        a known gap, tackled in a later phase with an SDF-specific bounds
        computation.
- [x] `server.py` integration: serve `sdf_viewer.html` + `sdf/` static assets
      via the configurable `entry_page` (existing catch-all static routing +
      content-hash versioning already cover the `sdf/` assets).

## Unit tests

File: `py/tests/viz/sdf/test_visualizer.py`

- [x] `test_add_serializes_sdf_object` — `SdfVisualizer.add(Sphere(...))`
      produces an SDF scene object of the expected kind/structure.
- [x] `test_distance_setter_emits_config` — setting `distance` / `opacity`
      emits the `sdf_viewer_config` message with the right value.
- [ ] `test_serve_sdf_viewer_html` — the server serves `sdf_viewer.html` and
      the `sdf/` static assets (mock transport, no real browser). *(deferred —
      exercised by the Phase 6a browser slice via the real `VizServer`)*
- [x] `test_camera_config_parity` — the `scene_config.camera` dict emitted by
      `SdfVisualizer` equals the one emitted by the standard `Visualizer` for an
      identical `CameraConfig3d`.

## Verification

- [ ] `SdfVisualizer().add(Point(...))` opens the SDF viewer in a browser and
      renders via the ray-marcher. *(Phase 6a manual user confirmation)*
- [ ] Changing the distance function through the facade triggers a recompile in
      the connected browser. *(deferred — Phase 8 wires `distOf`)*
- [ ] Existing (non-SDF) `Visualizer` continues to work unchanged. *(the
      `entry_page` server param is opt-in; the default remains `viewer.html`)*
- [x] `uv run pytest py/tests/viz/sdf/test_visualizer.py` passes.
