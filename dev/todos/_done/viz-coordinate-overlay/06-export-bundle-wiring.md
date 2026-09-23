# Phase 6 — Export + bundle wiring

## Goal

Bundle the underlay/overlay modules and wire `grid_underlay` + `axes_overlay`
into all standalone-HTML export paths (full page, figure snippet, animated
figure) so they render and update in exported HTML.

## Files

- Edit: `py/pytanga/viz/export/_bootstrap/_html.py`
- Edit: `py/pytanga/viz/export/_bootstrap/_scene.py`
- Edit: `py/pytanga/viz/export/_bootstrap/_entities.py`
- Edit: `py/pytanga/viz/export/_bootstrap/_overlays.py`
- Edit: `py/pytanga/viz/export/_html.py`
- Edit: `py/pytanga/viz/export/_figure_html.py`
- Edit: `py/pytanga/viz/export/_animated_figure.py`
- New: `py/tests/viz/test_overlay_bundle.py`

## Steps

- [x] **6.1 — bundle + bridge**
  - In `_bootstrap/_html.py`, add `nice-ticks.js`, `axes-overlay-math.js`,
    `axes-overlay.js`, then `grid-underlay.js` (order: math before renderers) to
    `_SHARED_JS_FILES` — this single list feeds `generate_library_js()`, the one
    source for **all three delivery modes**: `inline` (inlined via `_cdn.py`),
    `offline` (esbuild bundle via `_offline.py`), and `cdn` (the committed
    `js/tanga-viewer.js` served by jsDelivr).
  - In `_bootstrap/_scene.py`, add `AxesOverlay` and `GridUnderlay` to
    `_TANGA_BRIDGE_SYMBOLS` (so `window.__tanga` exposes them to the generated
    export adapters).

- [x] **6.2 — `js_scene_build` underlay branch**
  - In `_bootstrap/_entities.py`, add `else if (obj.layer === 'underlay') { /* skip
    — handled by the coordinate-frame setup */ }` so underlay objects aren't
    routed to `buildSceneObject`/`buildOverlay`.

- [x] **6.3 — `js_coordinate_overlay_setup` generator**
  - In `_bootstrap/_overlays.py`, add a generator that: creates the underlay
    container + `GridUnderlay` from `grid_underlay` objects and the `AxesOverlay`
    from `axes_overlay` objects (mounting into the export container), and defines
    `updateCoordinateOverlays(camera, w, h, dpr)` + a resize hook.

- [x] **6.4 — static + figure adapters**
  - `_html.py` and `_figure_html.py`: when scene data contains an underlay/overlay
    coordinate object, set the scene background to `"transparent"`, call
    `js_coordinate_overlay_setup(...)` after `applyCameraConfig`, and pass
    `extra_per_frame` (calling `updateCoordinateOverlays`) to `js_render_loop`.

- [x] **6.5 — animated adapter**
  - `_animated_figure.py`: same overlay setup + transparency, and add an
    overlay-update call to the animated loop (extend `js_animated_render_loop`
    with an `extra_per_frame` parameter, default `""`).

- [x] **6.6 — rebuild bundle + check**
  - `uv run python tools/build-viewer-js.py` to regenerate the committed
    `js/tanga-viewer.js` (+ manifest), then `--check`; `node --check` the new
    modules; browser-smoke an exported HTML with a 2D overlay coordinate system.
  - The rebuilt `js/tanga-viewer.js` is what `_cdn.py`
    `build_library_script_tag(delivery="cdn")` loads — commit it in this PR
    (`.github/workflows/ci.yml` / `cd.yml` gate it via
    `tools/build-viewer-js.py --check`).

- [x] **6.7 — bundle-inclusion regression test**
  - `py/tests/viz/test_overlay_bundle.py`: assert `generate_bootstrap_js("")`
    contains `niceLinearTicks`, `formatValue`, `AxesOverlay`, and `GridUnderlay`
    (mirroring `test_camera_fit_unification.py`), and that the committed
    `js/tanga-viewer.js` on disk also contains them.

## Validation

`uv run python tools/build-viewer-js.py --check && uv run pytest py/tests/viz/test_overlay_bundle.py -q && node --check py/pytanga/viz/templates/nice-ticks.js && node --check py/pytanga/viz/templates/axes-overlay-math.js && node --check py/pytanga/viz/templates/axes-overlay.js && node --check py/pytanga/viz/templates/grid-underlay.js`

## Notes

- `_strip_imports` removes `import`/`export` keywords, so the concatenated
  modules share one bundle scope; order the `_SHARED_JS_FILES` additions so math
  precedes renderers.
- Export `OrbitControls` already enables pan/zoom; only the per-frame update call
  and transparent background are needed.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
