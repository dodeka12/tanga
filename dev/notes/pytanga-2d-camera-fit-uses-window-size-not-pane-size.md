# 2D `fit_camera=True` fits against `window.innerWidth`/`innerHeight`, not the pane's size

## Goal

`Visualizer.flush(fit_camera=True)` (2D scenes) should fit the orthographic
camera to the actual `SceneView` pane's rendered size, so the fit is correct
in any split-view layout, not just when the scene fills the whole browser
window.

Observed with `tanga-py==1.14.0`.

## User-visible symptom

In a split-view layout where a `SceneView` pane doesn't fill the whole
browser window (e.g. a sidebar next to the scene, as in
`src/examples/floating_interactive_v3.py`), the 2D view looks squashed/
stretched horizontally on first paint. If the split-view divider is dragged
by hand afterward (or the browser window itself is resized), the view
immediately snaps to the correct aspect ratio. Calling
`viz.flush(fit_camera=True)` again later -- even after a delay meant to let
the layout "settle" -- does **not** fix it; the squash is identical every
time.

## Cause

The 2D branch of `fitCamera()` computes the frustum's aspect ratio from
`window.innerWidth`/`window.innerHeight` instead of the pane's own measured
size:

```js
// pytanga/viz/templates/fit_camera.js
export function fitCamera(sceneObjects, camera, controls, spaceDim) {
    if (spaceDim === 2) {
        ...
        const aspect = _finiteAspect(window.innerWidth, window.innerHeight);
        const safeAspect = Number.isFinite(aspect) ? aspect : 1.0;
        camera.left = frustumSize * safeAspect / -2;
        camera.right = frustumSize * safeAspect / 2;
        ...
        camera.userData._view2d = {
            xmin: center.x - frustumSize * safeAspect / 2,
            xmax: center.x + frustumSize * safeAspect / 2,
            ymin: center.y - frustumSize / 2,
            ymax: center.y + frustumSize / 2,
            uniform: true,
            border_px: 0,
        };
        return;
    }
    ...
}
```

`_orthoFrustum()` -- used both by this fit path indirectly (via the stored
`_view2d` rect) and by explicit `CameraConfig2d`/`View2DConfig` cameras --
has the same problem: it reads `window.innerWidth`/`window.innerHeight`
directly for its border/aspect-content calculations, only falling back to
its `aspect` *parameter* for the final `left`/`right`/`top`/`bottom` scale in
the `uniform` branch:

```js
// pytanga/viz/templates/view_mode.js
function _orthoFrustum(xmin, xmax, ymin, ymax, uniform, borderPx, aspect) {
    ...
    // Undistorted letterboxing: ...
    const w = window.innerWidth;
    const h = window.innerHeight;
    const bp = borderPx || 0;
    const cw = w - 2 * bp;
    const ch = h - 2 * bp;
    const aspectContent = (cw > 0 && ch > 0) ? (cw / ch) : aspect;

    const fit = Math.max(extX / aspectContent, extY);
    ...
}
```

The three-view wrapper's own `fitCamera()` method doesn't pass its pane's
measured size in at all -- unlike its `resize()` method, which does:

```js
// pytanga/viz/templates/views/three-view.js
resize() {
    const width = this.width || window.innerWidth;
    const height = this.height || window.innerHeight;
    if (this.camera) {
        handleResize(this.camera, this.renderer, this.labelRenderer,
            this.sceneConfig?.space_dim || 3, width, height);
    }
    ...
}

fitCamera() {
    if (!this.camera) return;
    fitCamera(this.sceneObjects, this.camera, this.controls,
        this.sceneConfig?.space_dim || 3);   // no width/height passed
}
```

So in a single, full-window scene this bug is invisible (`window.innerWidth`
happens to equal the pane's width). In any split-view layout it is not: the
fit is computed against the *browser window's* aspect ratio, not the pane's,
which is deterministically wrong whenever they differ (e.g. a sidebar pane
next to the scene).

This is why a client-side "wait and re-flush" workaround from application
code can't fix it: `fitCamera()`'s 2D branch reads `window.innerWidth`/
`window.innerHeight` every time it runs, and the browser window's size
doesn't change just because the split-view layout finished settling, so
re-requesting `fit_camera=True` after a delay recomputes the exact same
wrong result.

It only self-corrects when the pane's own `ResizeObserver` fires from a
*genuine* resize (dragging the split divider, or resizing the browser
window itself), because that runs a different, correctly pane-size-aware
path:

```js
// pytanga/viz/templates/views/three-view.js
_onExtentChanged() { this.resize(); }
```

```js
// pytanga/viz/templates/view_mode.js
export function handleResize(camera, renderer, labelRenderer, spaceDim, width, height) {
    const aspect = _finiteAspect(width, height);   // real pane width/height
    if (!Number.isFinite(aspect)) return;
    if (spaceDim === 2 && camera.isOrthographicCamera) {
        _applyOrthoFrustum(camera, aspect);   // uses the real aspect param
    }
    ...
}
```

There is no public pytanga API or event that lets server-side (Python)
application code trigger this correct `handleResize()` path directly -- only
the buggy `fitCamera()` path is reachable via `Visualizer.flush(fit_camera=
True)`.

## Proposed fix

Thread the pane's real measured width/height into `fitCamera()`/
`_orthoFrustum()` the same way `handleResize()` already receives them,
instead of reading `window.innerWidth`/`window.innerHeight`:

1. `three-view.js`'s `fitCamera()` method should pass `this.width`/
   `this.height` (with the same `|| window.innerWidth`/`|| window.innerHeight`
   fallback `resize()` already uses) into the shared `fitCamera()` function.
2. The shared `fitCamera()` (in `fit_camera.js`) and `_orthoFrustum()` (in
   `view_mode.js`) should accept `width`/`height` parameters and use them
   wherever they currently read `window.innerWidth`/`window.innerHeight`,
   rather than reading the global window size directly.
3. `export/_animated_figure.py` and `export/_html.py`'s static/standalone
   HTML export bootstraps (`js_autofit_camera`/`js_resize_handler`) likely
   need the same treatment if they embed a viewer inside a non-full-window
   container -- worth checking as part of the same fix, since they
   concatenate the same shared JS.

## Regression tests

- [ ] A 2D scene rendered inside a `SplitView` pane narrower than the full
      viewport, with `fit_camera=True` requested once at startup (no
      subsequent resize), should end up with `camera.left`/`right`/`top`/
      `bottom` matching the pane's own aspect ratio, not the window's.
- [ ] The same scenario for a 3D `PerspectiveCamera` fit should be
      unaffected (the 3D fit path doesn't depend on aspect, only radius/fov,
      so it isn't expected to reproduce this bug -- worth a test asserting
      that explicitly so a future refactor doesn't introduce it there too).

## Downstream workaround (applied)

None viable from application code alone -- confirmed there is no public
pytanga API/event to trigger the correct (`handleResize`) code path from the
server side. `src/examples/floating_interactive_v3.py` previously attempted
a delayed re-`flush(fit_camera=True)` after `init()`; this has been removed
(commit `afcd211`) since it never actually corrected the squash -- it just
re-ran the same buggy, window-size-based computation. The only current
workaround is for the end user to resize the browser window or drag the
split divider once after the app starts, either of which fires the pane's
own `ResizeObserver` and self-corrects the aspect via `handleResize()`. This
is documented in that file's module docstring and in
`/memories/repo/fpk-viz-workflow-prefs.md`.

## Acceptance criteria

- `fit_camera=True` on a 2D scene produces a correctly-aspected frustum on
  the very first request, regardless of how the containing pane's size
  relates to the browser window's size.
- No change in behavior for the common case of a scene that fills the whole
  browser window.
- Covered by a regression test asserting the fitted frustum's aspect matches
  the pane's aspect, not the window's, in a narrower-than-window pane.
