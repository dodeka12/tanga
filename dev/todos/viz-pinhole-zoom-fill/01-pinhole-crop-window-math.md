# Phase 1 — Pane-shaped crop window + generalized letterbox (math)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-architecture.md`, §
> "Calibrated camera view" and "Viewport navigation").  This phase changes the
> crop-window contract in `pinhole-framing.js`; the same module stays the single
> source of truth for the sub-frustum and the background letterbox.

## Goal

Rewrite the crop-window + letterbox math in `pinhole-framing.js` so the crop
window is the **pane-shaped visible portion** of the zoomed image, and the
letterbox factor derives from that window's pixel aspect (not the fixed image
aspect).  `zoom=1` and `fit="fill"` results stay byte-for-byte identical; only
`fit` + `zoom>1` gains the grow-to-fill behaviour.

## Files

- Edit: `py/pytanga/viz/templates/pinhole-framing.js`
- Edit: `py/tests/viz/test_pinhole_math.py`

## Steps

- [x] **1.1 — Hoist `imageAspect`/`aspect` and compute the fit half-extents.**
  - Move the existing `const imageAspect = W / H;` and
    `const aspect = Number(paneAspect) || imageAspect;` above the crop block
    (they are currently just before the letterbox branches).
  - Add `const fillMode = fit === 'fill';`, `const hx0 = fillMode ? 1 :
    Math.min(1, imageAspect / aspect);`, `const hy0 = fillMode ? 1 :
    Math.min(1, aspect / imageAspect);`.

- [x] **1.2 — Replace the square crop window with the pane-shaped one.**
  - In the `if (crop) { … }` block, replace `const half = 0.5 / zoom;` and the
    two `_clamp(0.5 + pan*0.5, half, 1 - half)` calls with per-axis
    `halfU = 0.5 * Math.min(1, 1 / (hx0 * zoom))` and
    `halfV = 0.5 * Math.min(1, 1 / (hy0 * zoom))`, then
    `cxN = _clamp(0.5 + px*0.5, halfU, 1 - halfU)` /
    `cyN = _clamp(0.5 + py*0.5, halfV, 1 - halfV)`, and
    `u0 = cxN - halfU; u1 = cxN + halfU; v0 = cyN - halfV; v1 = cyN + halfV;`.

- [x] **1.3 — Generalize the letterbox to the crop window's pixel aspect.**
  - Add `const cropW = (u1 - u0) * W; const cropH = (v1 - v0) * H;` and
    `const cropAspect = cropH > 0 ? cropW / cropH : imageAspect;`.
  - In the letterbox branches, replace every use of `imageAspect` with
    `cropAspect` (the `aspect > imageAspect` / `aspect < imageAspect` tests and
    the returned `hx`/`hy` values: `hx: cropAspect / aspect`, `hy: 1` and
    `hx: 1`, `hy: aspect / cropAspect`).  Keep the `fillMode` branch returning
    `hx: 1, hy: 1` and the `else` (equal) branch unchanged.

- [x] **1.4 — Return the fit half-extents.**
  - After `result.crop = { u0, v0, u1, v1 };`, add `result.fitHx = hx0;` and
    `result.fitHy = hy0;` before `return result;`.

- [x] **1.5 — Add/adjust node tests.**
  - Keep the existing `fill`-mode and no-crop `fit` tests green (they pin the
    unchanged contract).  Add `test_pinhole_framing_fit_crop_window_grows`
    using image `640×480` in a `1.0`-aspect pane with `fit`:
    - `zoom=1`: `crop == {0,0,1,1}`, `hx == 1`, `hy ≈ 0.75`.
    - `zoom=2`: `hx == 1`, `hy == 1` (image reaches the pane edge).
    - `zoom=4`: `crop ≈ {u0:0.375, v0:1/3, u1:0.625, v1:2/3}` (pane-shaped),
      `hx == 1`, `hy == 1`, and `left/right/top/bottom` span the central
      `0.25 × 1/3` of the full frustum.
  - Also assert `fitHx == 1` / `fitHy ≈ 0.75` for this pane/image.

## Validation

`uv run pytest py/tests/viz/test_pinhole_math.py -q`

## Notes

- `pinholeFraming` stays `three`/DOM-free (node-tested) — no new imports.
- The `_clamp` helper already exists; reuse it.
- `Math.min`/`Math.max` are already used in the file; keep the same style.
- Existing tests in `test_pinhole_math.py` project known camera-space points;
  do not change their expected values — the no-crop/fill paths are unchanged.
