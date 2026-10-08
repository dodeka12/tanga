# Phase 2 — Background letterbox shader (`uHx`/`uHy`)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-architecture.md`, § "Image
> background").  This phase adds an explicit letterbox uniform to the background
> quad shader; it refines the existing `image-background.js` seam (no new host
> protocol).

## Goal

Let the background quad's letterbox be driven explicitly by the `pinholeFraming`
result (zoom-scaled `hx`/`hy`) instead of only the aspect fit, while keeping the
existing aspect-fit path as a fallback for the non-pinhole `background_image`
case.

## Files

- Edit: `py/pytanga/viz/templates/renderers/image-background.js`

## Steps

- [x] **2.1 — Add `uHx`/`uHy` uniforms to the fragment shader.**
  - Add `uniform float uHx;` and `uniform float uHy;` to `_BG_FRAGMENT`.
  - Replace the two hard-coded fit lines with an override:
    `float hx = uHx > 0.0 ? uHx : (uFit > 0.5 ? 1.0 : min(1.0, uImageAspect / uPaneAspect));`
    and the symmetric `hy` line using `uPaneAspect / uImageAspect`.  Keep the
    rest of the shader (`q`, the `abs(q)>1` black test, the crop sampling) as-is.

- [x] **2.2 — Initialize the new uniforms in `_buildMaterial`.**
  - Add `uHx: { value: 0.0 },` and `uHy: { value: 0.0 },` to the `uniforms`
    object (default `0` → fallback fit path, so existing callers are unchanged).

- [x] **2.3 — Add `setBackgroundLetterbox(mesh, hx, hy)`.**
  - Export a function that sets `mat.uniforms.uHx.value = Number(hx) || 0;` and
    `mat.uniforms.uHy.value = Number(hy) || 0;`, mirroring the guard style of
    `setBackgroundCrop`.  Add a short JSDoc (NDC display half-extents; pass `0`
    to revert to the aspect-fit fallback).

## Validation

`node js/dev/tests/check-syntax.mjs`

## Notes

- `updateImageBackground` still sets `uImageAspect`; `setBackgroundAspect` still
  sets `uPaneAspect` — both remain as the fallback path and must not be removed.
- The shader is not exercised by node math tests; the definitive check is the
  manual browser run after Phase 3.
- Do not change the `uFit` / `uImageAspect` / `uPaneAspect` defaults (Phase 1's
  no-crop/fill behaviour and the non-pinhole case depend on them).
