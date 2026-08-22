# Phase 6 — `SdfVisualizer` facade + HTML bootstrap (reuse `server.py`)

**Status:** Planned

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

- [ ] `SdfVisualizer` class:
  - [ ] Mirrors `Visualizer`'s `add()` / scene-handle API, serializing entities
        and operators via `sdf/serializer.py` and MVs via
        `sdf/algebra_embedding.py` (Phase 7).
  - [ ] Holds the viewer-level `distance` setting (default `"magnitude"`),
        exposed via a setter that emits the recompile message.
  - [ ] Reuses the existing server runtime (start/stop/port/static serving),
        switching the served entry page to `sdf_viewer.html`.
- [ ] `sdf_viewer.html`:
  - [ ] Reuse the `viewer.html` `<head>` + loading/error/fallback/status
        bootstrap.
  - [ ] Load `sdf/sdf_viewer.js` (+ `sdf/` modules) instead of
        `viewer.js`/`renderers/`.
  - [ ] Add an early WebGL2 capability notice.
- [ ] `sdf_viewer.js`:
  - [ ] Port the WebSocket client (connect/reconnect/ready/scene messages)
        from `viewer.js`, delegating message handling to the SDF
        scene-builder and the distance-function recompile hook.
- [ ] `server.py` integration: register `sdf_viewer.html` + `sdf/` static
      assets with the existing content-hash versioning.

## Verification

- [ ] `SdfVisualizer().add(Point(...))` opens the SDF viewer in a browser and
      renders via the ray-marcher.
- [ ] Changing the distance function through the facade triggers a recompile in
      the connected browser.
- [ ] Existing (non-SDF) `Visualizer` continues to work unchanged.