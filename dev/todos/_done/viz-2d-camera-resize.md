# 2D Viewer — Robust Camera Framing on Resize (ResizeObserver)

**Created:** 2026-08-20 | **Status:** Planned

## Goal

Make the live 2D viewer's camera framing robust so that:

1. A fresh browser window never shows a "completely wrong and distorted" 2D
   camera that only corrects when the user clicks into the window.
2. Resizing the window — including while the server is disconnected — keeps the
   2D view at its internal aspect ratio (letterbox), exactly like the 3D view
   already does.

The change replaces the fragile `window.resize`-only handling with a
`ResizeObserver` on the actual render container, and makes the 2D orthographic
frustum recompute from a canonical stored fit instead of the current (possibly
corrupted) frustum.

## Background (current behaviour & root cause)

All dimension-specific logic lives in `py/pytanga/viz/templates/view_mode.js`,
driven from `py/pytanga/viz/templates/viewer.js`. The 2D path is far more
fragile than 3D:

- **3D (perspective)** projection depends only on `aspect`, recomputed fresh
  every resize → self-correcting, no distortion.
- **2D (orthographic)** projection depends on `left/right/top/bottom`, which
  must be recomputed correctly on every viewport change. If they are ever
  derived from a stale/wrong viewport size, the result is a non-uniform stretch.

Five code paths touch the camera (the "different update handlers"):

1. `view_mode.js createCamera()` — always creates a 3D `PerspectiveCamera`;
   `spaceDim` is ignored. 2D is switched in later via `switchToCamera()`.
2. `view_mode.js switchToCamera()` "default 2D" branch — builds the ortho
   camera with `aspect = window.innerWidth/innerHeight` at config-arrival time,
   sets the frustum, but **does not call `updateProjectionMatrix()`** (the
   explicit-2D branch, `fitCamera`, and `handleResize` all do).
3. `view_mode.js fitCamera()` (2D) — auto-fits from entity bounds, but **does
   not record `camera.userData._view2d`**, so later resizes cannot recompute
   from the original fit.
4. `viewer.js onResize()` → `view_mode.js handleResize()` — the window-resize
   handler. Its 2D fallback derives the new frustum from the **current**
   `camera.left/right/top/bottom` (fragile).
5. `viewer.js handleScreenshot()` — inline resize that only sets
   `camera.aspect`, never the ortho frustum (latent 2D screenshot bug).

Root causes of the two symptoms:

- **Startup distortion (fixed by clicking):** the ortho frustum is computed
  from `window.innerWidth/innerHeight` at the instant `scene_config` arrives. If
  the window is not yet laid out (background tab, `0`/`NaN` inner size), the
  frustum gets `NaN`/`Infinity` and/or the projection matrix stays stale.
  Clicking focuses the window → a `resize` event (or a visibility-triggered
  reconnect) recomputes it.
- **Resize distortion while disconnected:** the default 2D view never records
  `_view2d`, so `handleResize` falls back to re-deriving from the current
  frustum. Because `Math.max(NaN, …)` returns `NaN` (and `Infinity` likewise),
  a bad initial frustum is **propagated**, never corrected — and with no
  reconnect there is no re-fit to recover.

## Design decisions

1. **`ResizeObserver` is the source of truth** for the render size, observing
   `#viewer-container` (the element the canvas actually fills). This catches
   initial layout settling, container/iframe resizes (Jupyter, DevTools,
   split panes), and recovers from an initial `0`/`NaN` size once the container
   gets real dimensions — none of which `window.resize` reliably reports.
2. **Keep `window.resize` as a fallback**, routed through the same idempotent
   handler, for older/odd environments.
3. **Store the 2D auto-fit** on `camera.userData._view2d` (reusing the existing
   `_orthoFrustum` path) so resize recomputes from the original fit, not the
   current extents.
4. **Guard all non-finite sizes/aspects**; never write `NaN`/`Infinity` into a
   frustum, and reset to a sane default when a corrupt frustum is detected.
5. **Consistent `updateProjectionMatrix()`** everywhere the frustum is mutated.

## Files

- Modify: `py/pytanga/viz/templates/view_mode.js`
- Modify: `py/pytanga/viz/templates/viewer.js`

## Steps

### Step 1 — Robust size/frustum helpers in `view_mode.js`

- [x] Add a private `_finiteAspect(width, height)` returning
      `width / height` for positive finite inputs, else `NaN`.
- [x] Add a private `_applyOrthoFrustum(camera, aspect)` that sets
      `left/right/top/bottom` for a 2D ortho camera:
      - if `camera.userData._view2d` is present and finite, recompute via the
        existing `_orthoFrustum(...)`;
      - else, preserve the current full height: `fit = max(extX/aspect, extY)`;
      - if any current extent is non-finite or `<= 0`, reset to a sane default
        box (full height 10, width `10 * aspect`) instead of propagating
        `NaN`/`Infinity`.
- [x] Refactor `handleResize` to accept an explicit `{width, height}` (or two
      args) rather than reading `window.innerWidth/innerHeight` itself, and
      **return early** when the size is non-finite.

### Step 2 — Persist the 2D auto-fit in `fitCamera`

- [x] In the 2D branch of `fitCamera`, after computing `frustumSize` and
      `center`, record the fitted world rectangle on
      `camera.userData._view2d` (centered on `center`, extents from
      `frustumSize` and the current `aspect`, `uniform: true`,
      `border_px: 0`), so `_applyOrthoFrustum`/`_orthoFrustum` can recompute it
      on every resize.
- [x] Keep the existing frustum set + `updateProjectionMatrix()` behaviour.

### Step 3 — Harden `switchToCamera` default-2D branch

- [x] Guard `aspect` with `_finiteAspect` (fall back to `1.0`).
- [x] Call `newCam.updateProjectionMatrix()` after setting `left/right/top/bottom`.
- [x] (Optional) record the default 20-unit box in `_view2d` so resize stays
      consistent before the first auto-fit.

### Step 4 — Ensure the 2D camera is sized after the config arrives

- [x] Call `onResize()` at the end of `applySceneConfig()` (after
      `switchToCamera`/`configureControls`), so the just-switched 2D camera is
      immediately recomputed from the real container size instead of the
      possibly-stale `window.innerWidth/innerHeight` used during the switch.

### Step 5 — Wire up the `ResizeObserver` in `viewer.js`

- [x] In `initScene`, create a `ResizeObserver` on `#viewer-container` that
      calls `onResize()` with the observed entry's content size
      (`entry.contentRect.width/height`, or `target.clientWidth/clientHeight`).
- [x] Store the observer (e.g. `window._viewerResizeObserver`) and disconnect it
      on teardown if any such path exists.
- [x] Update `onResize()` to read size from the container first
      (`clientWidth/clientHeight`), falling back to
      `window.innerWidth/innerHeight`, then pass it into `handleResize`.
- [x] Keep `window.addEventListener('resize', onResize)` as a fallback; both
      routes are idempotent.

### Step 6 — Share one resize path (fix the screenshot handler)

- [x] Update `handleScreenshot` to reuse `_applyOrthoFrustum`/`handleResize`
      for 2D instead of only setting `camera.aspect`, so screenshots of a 2D
      scene capture the correct ortho framing.

### Step 7 — Verification

- [ ] Manual: `Visualizer(space_dim=2)` + a few entities (no explicit camera),
      then resize the window → no distortion, letterboxing preserved.
- [ ] Manual: stop the server, resize again → still no distortion.
- [ ] Manual: open the 2D view in a background tab / resize during load →
      camera self-corrects without clicking.
- [ ] Manual: `py/examples/viz/demo_camera_2d.py` (explicit `View2DConfig`) →
      resize letterboxes correctly.
- [x] `uv run pytest py/tests/viz` stays green (backend regression guard;
      frontend JS is not pytest-covered).

## Notes / edge cases

- The `Math.max(NaN, x) === NaN` gotcha is the reason a bad initial size is
  permanent today; the guards in Steps 1–3 must never let a non-finite value
  reach the frustum.
- Resize must not change what the camera is centered on: `_orthoFrustum` only
  uses extents, so panning (camera position/target shift) is preserved across
  resizes as long as we recompute from the stored fit, not the pan position.
