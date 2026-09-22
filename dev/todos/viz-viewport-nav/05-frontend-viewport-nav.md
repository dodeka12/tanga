# Phase 5 — Frontend viewport navigation

## Goal

Wire the frontend: handle the `view_viewport` message in the existing
`viewer.js` dispatcher, add `ThreeJsView.setViewport(...)`, and implement the
`"2d"` navigation mode (disable rotate, cursor-anchored zoom, per-pane button
mapping) so the viewport is a general per-pane capability.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Files

- Edit: `py/pytanga/viz/templates/viewer.js`
- Edit: `py/pytanga/viz/templates/views/three-view.js`
- Edit: `py/pytanga/viz/templates/view_mode.js`

## Steps

- [x] **5.1 — `view_viewport` dispatch in `viewer.js`**
  - Add `if (msg.type === 'view_viewport') { const t = _viewById.get(msg.view_id);
    if (t) t.setViewport(msg.viewport); return; }` next to the existing
    `view_camera` branch.
- [x] **5.2 — `ThreeJsView.setViewport(viewport)`**
  - Merge the partial `{zoom?, pan?}` into the pane's viewport state and
    re-apply it (clamp via the pane's `min_zoom`/`max_zoom`/`pan_*` limits).
  - Reuse the same apply path as the interaction (below) so interaction and
    programmatic set share one function.
- [x] **5.3 — `"2d"` navigation mode in `view_mode.js`**
  - In `configureControls`, read the pane's `navigation` (from the `scene_view`
    node): when `"2d"`, set `enableRotate = false`, `enablePan = true`,
    `enableZoom = true`, `zoomToCursor = true`, and apply the per-pane `controls`
    button mapping (falling back to the scene `controls`).
  - Compose with the existing `applyCameraLock` (lock still disables the named
    action).
- [x] **5.4 — apply viewport to camera**
  - For 2D/3D/pinhole, fold `{zoom, pan}` into the camera: 2D via the existing
    `_view2d`/`clampOrthoView` path; 3D via `camera.zoom` + an off-center
    frustum shift (`setViewOffset` or a frustum-center shift); pinhole via the
    crop window wired in Phase 6.
  - Reapply on resize (recompute the shifted frustum for the new aspect).
- [x] **5.5 — interaction gesture**
  - In `"2d"` mode, wheel = zoom (cursor-anchored), drag = screen-space pan,
    updating the same viewport state and re-applying via the shared path from
    `5.2`/`5.4`.  No new event registry — this is OrbitControls-driven, matching
    the existing 2D pan/zoom.

## Validation

```
uv run python tools/build-viewer-js.py --check && uv run pytest py/tests/viz -q
```

## Notes

- `setViewport` is the only new frontend entry point; everything else reuses
  `configureControls` / `applyCameraLock` / `handleResize`.
- Keep the viewport apply function pure/`three`-only so it can be unit-tested
  (mirror `camera-fit.js`).
