# Pinhole zoom fill — Overview

**Created:** 2026-10-08 | **Status:** Done | **Branch:** `fix/background-image-scale`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-architecture.md`, §
> "Calibrated camera view" and "Viewport navigation") for the subsystem this work
> touches, so the new code aligns with the documented architecture.  This work
> refines the existing crop-window contract in `pinhole-framing.js` (it does not
> add a new seam or message type); update the developer docs accordingly.

## Goal

When a calibrated camera pane (`CameraView(cam, navigation="2d",
background_image=…)`) is zoomed in, the visible image currently stays pinned at
its initial **fit** letterbox size — zoom magnifies the pixels inside that
fixed region but the region's borders (and the surrounding black bars) never
move.  This plan makes zooming **scale the image up to fill the pane**, so the
letterbox bars shrink as you zoom and disappear once the image reaches the pane
edge, after which the pane crops it — the standard image-viewer zoom behaviour.
The 3D overlay (shapes, frustum) must stay pixel-locked to the image.

## Architecture (short)

- **`pinhole-framing.js`** (pure, node-tested) is the single source of truth for
  both the off-center sub-frustum and the background letterbox.  Today it
  computes a *square* crop window (`half = 0.5/zoom` in both axes — always the
  image's aspect) and letterboxes it with a **fixed** `aspect/imageAspect`
  factor, so the fit region is zoom-independent.  The fix makes the crop window
  **pane-shaped** (the portion of the zoomed image visible in the pane) and
  letterboxes *that* window, so the letterbox `{hx, hy}` grow toward `1` as zoom
  increases.
- **`image-background.js`** (background quad shader) currently derives its
  letterbox from `uImageAspect`/`uPaneAspect` alone (no zoom).  It gains explicit
  `uHx`/`uHy` uniforms (zoom-scaled letterbox) with a fallback to the existing
  fit path so the non-pinhole `background_image` case is unchanged.
- **`view_mode.js` `applyPinhole`** already returns the framing result internally;
  it will additionally retain the zoom-scaled letterbox and the base fit
  half-extents on `camera.userData` for `three-view.js`.
- **`three-view.js`** passes the retained letterbox to the background quad
  (`setBackgroundLetterbox`) and clamps pan per-axis against the fit half-extents.

## Decisions (confirmed)

- Zoom semantics: scale the image by `zoom` around the pan anchor and clip at the
  pane (the crop window is the pane-shaped visible portion).  At `zoom=1` the
  behaviour is byte-for-byte today's `fit`; `fit="fill"` is unchanged.
- The crop window stays the single source of truth for both the sub-frustum and
  the background (same invariant as today); only its *shape* and the letterbox
  factor change.
- `pinholeFraming` returns two new fields, `fitHx`/`fitHy`, so `three-view.js`
  can clamp pan without duplicating the aspect math.
- The shader keeps the old `uImageAspect`/`uPaneAspect`/`uFit` fit path as a
  fallback for the non-pinhole `background_image` case (no regression there).
- Pan stays clamped so the image is never panned past its edge (no "pan into the
  black bars"); the clamp range now depends on the fit factors and zoom.

## Contract (fixed)

`pinholeFraming(fx, fy, cx, cy, width, height, near, far, paneAspect, fit, crop)`
returns:

```js
{
  left, right, top, bottom, near, far,   // off-center sub-frustum (shape unchanged)
  hx, hy,         // zoom-scaled display letterbox half-extents (NDC, ≤ 1)
  fitHx, fitHy,   // NEW: base fit half-extents at zoom=1 (for pan clamping)
  crop: { u0, v0, u1, v1 },   // visible crop window (pane-shaped when zoomed)
}
```

Crop-window math (normalized image coords, `v=0` at top):

```
imageAspect = W/H;  aspect = paneAspect
hx0 = min(1, imageAspect/aspect);  hy0 = min(1, aspect/imageAspect)   // fit; fill → (1, 1)
z   = max(1, zoom)
halfU = 0.5 · min(1, 1/(hx0·z));   halfV = 0.5 · min(1, 1/(hy0·z))
centerU = clamp(0.5 + pan.x·0.5, halfU, 1 − halfU);   centerV = clamp(0.5 + pan.y·0.5, halfV, 1 − halfV)
u0 = centerU − halfU;  u1 = centerU + halfU;  v0 = centerV − halfV;  v1 = centerV + halfV
cropAspect = ((u1 − u0)·W) / ((v1 − v0)·H)
# letterbox the crop window into the pane using cropAspect (replacing the fixed imageAspect)
```

`image-background.js`:

```js
// shader: hx = uHx > 0 ? uHx : (uFit > 0.5 ? 1 : min(1, uImageAspect/uPaneAspect));
//         hy = uHy > 0 ? uHy : (uFit > 0.5 ? 1 : min(1, uPaneAspect/uImageAspect));
export function setBackgroundLetterbox(mesh, hx, hy);  // sets uHx/uHy
```

`view_mode.js applyPinhole` retains on `camera.userData`:

```js
_pinholeLetterbox = { hx: f.hx, hy: f.hy };   // zoom-scaled
_pinholeFit       = { hx: f.fitHx, hy: f.fitHy };  // base fit
```

`three-view.js` pan clamp (per-axis):

```
limit = max(0, 1 − 1/(fit·zoom))   // fit = _pinholeFit.hx / .hy for x / y
pan   ∈ [−limit, limit]
```

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-pinhole-crop-window-math.md](./01-pinhole-crop-window-math.md) | Pane-shaped crop window + generalized letterbox in `pinhole-framing.js` + node tests |
| 2 | [02-background-letterbox-shader.md](./02-background-letterbox-shader.md) | `uHx`/`uHy` uniforms + `setBackgroundLetterbox` in `image-background.js` |
| 3 | [03-viewport-plumbing.md](./03-viewport-plumbing.md) | Retain letterbox/fit in `applyPinhole`; pass to background + per-axis pan clamp in `three-view.js`; rebuild bundle |
| 4 | [04-docs-changelog.md](./04-docs-changelog.md) | Update `viz-architecture.md` + branch changelog |

## Testing as you go

- Node framing math: `uv run pytest py/tests/viz/test_pinhole_math.py -q`
- JS syntax gate: `node js/dev/tests/check-syntax.mjs`
- Bundle in sync: `uv run python tools/build-viewer-js.py --check`
- Backend regressions: `uv run pytest py/tests/viz -q`
- Docs: `uv run mkdocs build --strict`
- Manual: `uv run python py/examples/apps/calibrated_labeling_app.py`

## Non-goals

- No new message type, event registry, or binary transport.
- No change to the non-pinhole `background_image` path (no pinhole camera).
- No change to `fit="fill"` (stretch) behaviour.
- No orbit/rotate in `"2d"` mode (unchanged).
- No change to `ImageData` / frame transport / reconnect logic.

